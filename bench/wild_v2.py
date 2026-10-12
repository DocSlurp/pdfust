"""Build the wild-v2 DEV corpus: 64 realistic multi-page documents from four producers.

wild-v2 extends wild-v1 (``bench/WILD_CORPUS.md``) with longer documents
(3-15 pages), tables that continue across pages with repeated headers,
real AcroForm fields, equations, code blocks and nested lists. Every document
is authored with explicit pages in ``bench/wild_v2_templates/docs_*.py`` and
produced by one of:

* ``chromium``: headless Chromium (``--disable-gpu``) prints tagged PDF from
  HTML; MathML equations; pypdf then writes Info, XMP and ``/Lang``.
* ``libreoffice``: Writer converts flat ODF (tagged or untagged export);
  equations are LibreOffice Math objects.
* ``reportlab``: platypus, untagged; Standard 14 Type 1, embedded TrueType or
  non-embedded CID fonts; native vector charts; AcroForm widgets that pylopdf
  fills with ``Document.set_form_field``.
* ``pylopdf``: ``insert_textbox`` with krilla-subset Noto fonts, vector rules
  through ``show_pdf_page`` and ``insert_image``.

Renderers break pages explicitly and shrink a document uniformly until every
authored page fits, so every truth block carries an exact ``page``. A build
fails when the produced page count differs from the authored one.

truth.json extends the wild-v1 schema (``"version": 2``): every block has a
one-based ``page``; table segments after the first carry ``continues_from``,
``logical_id`` and ``repeated_header``; new kinds are ``code`` (text,
language), ``equation`` (id, text, number, mathml) and ``form_field`` (name,
label, field_type, value, options); list items may be nested objects
``{"text", "ordered", "items"}``; ``continued_tables`` summarizes
continuations, ``producer_detail`` records engine facts and ``links`` carry
``page``.

Usage::

    python -m bench.wild_v2 --directory bench/results/pdf-master-artifacts/wild-v2

The directory then holds ``docs/{doc_id}/{source.*, source.pdf, truth.json,
assets/}``, ``docs/build-report.json`` and, through ``bench.wild_flatten``,
``variants/{doc_id}/{L0..L9}.pdf``. CPU only; no hosted models or network.
"""

# Fixed local tools run from PATH with argument lists; heavy imports stay lazy.
# ruff: noqa: S603, S607, PLC0415, E501, C901, PLR0912, TRY003, EM102, ANN401, ERA001, PLR2004, FBT001, D401
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bench.silver import guard_path, write_json
from bench.wild_documents import CHROMIUM_FLAGS, _delta, _usage, inspect_pdf, rewrite_metadata, screenshot
from bench.wild_templates import media
from bench.wild_v2_templates import core

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/wild-v2"
PHOTO_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
TESSDATA = PHOTO_DIRECTORY / "tessdata"
SEED = "wild-v2-documents-20261011"
SCALES = (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7)
LO_EXPORT = ('pdf:writer_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"%s"},'
             '"ExportBookmarks":{"type":"boolean","value":"true"},"ExportFormFields":{"type":"boolean","value":"false"}}')
DOC_MODULES = ("docs_finance", "docs_commerce", "docs_science", "docs_office", "docs_events")


# ------------------------------------------------------------------ composition (pure and deterministic)


def registry() -> list[tuple[str, str, Any]]:
    """``(doc_id, producer, builder)`` for every authored document, in corpus order."""
    import importlib

    entries: list[tuple[str, str, Any]] = []
    for name in DOC_MODULES:
        try:
            module = importlib.import_module(f"bench.wild_v2_templates.{name}")
        except ModuleNotFoundError as error:
            if error.name != f"bench.wild_v2_templates.{name}":
                raise
            continue
        entries += list(module.DOCS)
    return entries


def compose(only: list[str] | None = None) -> list[dict[str, Any]]:
    """Build every authored document dictionary without touching files or tools."""
    docs = []
    seen: set[str] = set()
    for doc_id, producer, builder in registry():
        if doc_id in seen:
            raise ValueError(f"duplicate doc id {doc_id}")
        seen.add(doc_id)
        if only and doc_id not in only:
            continue
        doc = builder()
        doc.setdefault("dir", "ltr")
        doc.setdefault("tagged", producer in {"chromium", "libreoffice"})
        doc.update(doc_id=doc_id, producer=producer)
        if producer not in core.PRODUCERS:
            raise ValueError(f"{doc_id}: unknown producer {producer}")
        if not 3 <= len(doc["pages"]) <= 15:
            raise ValueError(f"{doc_id}: {len(doc['pages'])} pages")
        docs.append(doc)
    return docs


def assign_photos(docs: list[dict[str, Any]], photos: list[dict[str, Any]]) -> None:
    """Choose photos per document (deterministic and independent of build order or parallelism).

    Photos may repeat across documents but not inside one document.
    """
    for doc in docs:
        used: set[str] = set()
        for block in _figures(doc):
            if block["figure_kind"] != "photo":
                continue
            want = block["photo"]
            chosen = media.choose_photo(photos, want["prefer"], want["tags"], used)
            if chosen:
                used.add(chosen["id"])
                block["photo_id"] = chosen["id"]
                block["photo_path"] = chosen["path"]
                block["caption"] = want["captions"].get(chosen["id"].split("-", 1)[-1], want["fallback"])
                block["alt"] = chosen.get("subject", "")
            else:
                block["photo_id"] = None
                block["caption"] = want["fallback"]


def _figures(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [b for page in doc["pages"] for b in core.leaves(page) if b["kind"] == "figure"]


# ------------------------------------------------------------------ media


def _chart_font(lang: str) -> str:
    special = {"ja": "Noto Sans CJK JP", "zh-CN": "Noto Sans CJK SC", "zh-TW": "Noto Sans CJK TC", "ko": "Noto Sans CJK KR",
               "hi": "Noto Sans Devanagari", "th": "Noto Sans Thai", "ar": "Noto Naskh Arabic", "he": "Noto Sans Hebrew"}
    key = lang if lang in special else lang.split("-", maxsplit=1)[0]
    return f"{special[key]}, Noto Sans" if key in special else "Noto Sans"


def resolve_media(doc: dict[str, Any], assets: Path, profile: Path) -> list[dict[str, Any]]:
    """Copy photos, render screenshots/charts and fill ``src``/``svg``/``text_in_image`` in place."""
    records = []
    for block in _figures(doc):
        kind = block["figure_kind"]
        if kind == "photo":
            if block.get("photo_id"):
                source = guard_path(PHOTO_DIRECTORY / block["photo_path"])
                block["src"] = block["photo_id"] + source.suffix.lower()
                shutil.copyfile(source, assets / block["src"])
                records.append({"figure": block["id"], "photo_id": block["photo_id"]})
            else:
                block["src"] = f"placeholder-{block['id']}.jpg"
                media.placeholder_photo(assets / block["src"], f"{SEED}|{doc['doc_id']}|{block['id']}")
                records.append({"figure": block["id"], "photo_id": None, "placeholder": block["src"]})
            block["text_in_image"] = []
        elif kind == "screenshot":
            render = block["render"]
            page, size, text = media.MOCKUPS[render["mockup"]](render["spec"])
            block["src"] = f"{block['id']}-{render['mockup']}.png"
            screenshot(page, size, assets / f"{block['id']}-{render['mockup']}.html", assets / block["src"], profile)
            block["text_in_image"] = text
            records.append({"figure": block["id"], "screenshot": render["mockup"]})
        else:
            spec = block["chart"]
            producer = doc["producer"]
            vector = not spec["raster"] and producer in {"chromium", "reportlab"}
            if vector and producer == "chromium":
                draw = media.bar_chart_svg if spec["type"] == "bar" else media.line_chart_svg
                width, height = spec["size"]
                svg = draw(spec["spec"], width=width, height=height, font=_chart_font(doc["metadata"]["lang"]))
                block["svg"] = svg.replace("<svg ", "<svg style='direction:ltr' ", 1)  # charts stay LTR inside RTL pages
                block["text_in_image"] = []
            elif vector:
                block["rl_vector"] = True
                block["text_in_image"] = []
            else:
                draw = media.bar_chart_svg if spec["type"] == "bar" else media.line_chart_svg
                width, height = spec["size"]
                svg = draw(spec["spec"], width=width, height=height, font=_chart_font(doc["metadata"]["lang"]))
                page, size = media.raster_chart_page(svg)
                block["src"] = f"{block['id']}-chart.png"
                screenshot(page, size, assets / f"{block['id']}-chart.html", assets / block["src"], profile)
                block["text_in_image"] = media.chart_labels(spec["spec"])
            records.append({"figure": block["id"], "chart": spec["type"], "vector": vector})
    return records


# ------------------------------------------------------------------ producers


def _page_count(path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(path).pages)


def _chromium_pdf(html_path: Path, out: Path, profile: Path) -> None:
    subprocess.run(["chromium", *CHROMIUM_FLAGS, f"--user-data-dir={profile}", "--no-pdf-header-footer",
                    "--generate-pdf-document-outline", f"--print-to-pdf={out}", html_path.as_uri()],
                   check=True, capture_output=True, timeout=240)


def _soffice(source: Path, out_dir: Path, lo_profile: Path, tagged: bool) -> Path:
    subprocess.run(["soffice", f"-env:UserInstallation={lo_profile.as_uri()}", "--headless", "--norestore", "--convert-to",
                    LO_EXPORT % ("true" if tagged else "false"), "--outdir", str(out_dir), str(source)],
                   check=True, capture_output=True, timeout=300, env={**os.environ, "TZ": "UTC"})
    return out_dir / (source.stem + ".pdf")


def produce(doc: dict[str, Any], folder: Path, profile: Path, lo_profile: Path, versions: dict[str, str]) -> dict[str, Any]:
    """Produce ``source.pdf`` (shrinking uniformly until the authored pages fit) and return producer facts."""
    assets = folder / "assets"
    pdf = folder / "source.pdf"
    expected = len(doc["pages"])
    producer = doc["producer"]
    attempts = []
    for scale in SCALES:
        if producer == "chromium":
            from bench.wild_v2_templates.render_html import document_html

            source = folder / "source.html"
            source.write_text(document_html(doc, scale), encoding="utf-8")
            raw = folder / "chromium-raw.pdf"
            _chromium_pdf(source, raw, profile)
            pages = _page_count(raw)
        elif producer == "libreoffice":
            from bench.wild_v2_templates.render_fodt import document_fodt

            source = folder / "source.fodt"
            source.write_text(document_fodt(doc, assets, scale), encoding="utf-8")
            with tempfile.TemporaryDirectory(prefix="wild2-lo-out-") as out:
                produced = _soffice(source, Path(out), lo_profile, doc["tagged"])
                shutil.move(produced, pdf)
            pages = _page_count(pdf)
        elif producer == "reportlab":
            from bench.wild_v2_templates.render_reportlab import render

            pages = render(doc, assets, pdf, scale)
        else:
            from bench.wild_v2_templates.render_pylopdf import Overflow, render

            try:
                pages = render(doc, assets, pdf, scale)
            except Overflow as error:
                attempts.append({"scale": scale, "overflow": str(error)})
                continue
        attempts.append({"scale": scale, "pages": pages})
        if pages == expected:
            break
    else:
        raise RuntimeError(f"{doc['doc_id']}: authored {expected} pages do not fit: {attempts}")
    detail: dict[str, Any] = {"engine": producer, "fit_scale": scale, "fit_attempts": attempts}
    if producer == "chromium":
        creator = f"wild-v2 HTML template ({doc['template']}) printed by {versions.get('chromium') or 'Chromium'}"
        rewrite_metadata(folder / "chromium-raw.pdf", pdf, doc, creator)
        (folder / "chromium-raw.pdf").unlink()
        detail["source"] = "source.html"
    elif producer == "libreoffice":
        detail.update(source="source.fodt", tagged_export=doc["tagged"])
    else:
        source = folder / "source.json"
        write_json(source, _authored_json(doc))
        detail["source"] = "source.json"
    if producer == "reportlab":
        from bench.wild_v2_templates.render_reportlab import font_policy

        detail["font_policy"] = font_policy(doc)["kind"]
    if any(b["kind"] == "form" for page in doc["pages"] for b in core.leaves(page)):
        detail["form_fill"] = fill_form(doc, pdf)
    return detail


def _authored_json(doc: dict[str, Any]) -> dict[str, Any]:
    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if not callable(v) and k != "svg"}
        if isinstance(value, list | tuple):
            return [clean(v) for v in value]
        return value

    return clean(deepcopy(doc))


def fill_form(doc: dict[str, Any], pdf: Path) -> dict[str, Any]:
    """Fill every AcroForm field with pylopdf ``set_form_field`` and verify the stored values."""
    import pylopdf
    from bench.wild_v2_templates.fonts import stack

    fields = [spec for page in doc["pages"] for b in core.leaves(page) if b["kind"] == "form" for row in b["rows"] for spec in row]
    document = pylopdf.Document(str(pdf))
    embedded = 0
    for spec in fields:
        value = spec["value"]
        if spec["field_type"] == "checkbox":
            document.set_form_field(spec["name"], bool(value))
            continue
        try:
            value.encode("cp1252")
            document.set_form_field(spec["name"], value)
        except UnicodeEncodeError:
            last: Exception | None = None
            for path, index in stack(doc["metadata"]["lang"]):
                try:
                    document.set_form_field(spec["name"], value, fontfile=str(path), fontindex=index)
                    embedded += 1
                    break
                except pylopdf.PdfError as error:
                    last = error
            else:
                raise RuntimeError(f"{doc['doc_id']}: cannot fill {spec['name']}: {last}")
    stored = {f["name"]: f for f in document.get_form_fields()}
    mismatches = []
    for spec in fields:
        got = stored.get(spec["name"], {}).get("value")
        want = spec["value"]
        ok = (got not in {None, "", "Off"}) == bool(want) if spec["field_type"] == "checkbox" else got == want
        if not ok:
            mismatches.append({"name": spec["name"], "want": want, "got": got})
    filled = pdf.with_name("source-filled.pdf")
    document.save(str(filled), garbage=True, deflate=True)
    document.close()
    filled.replace(pdf)
    if mismatches:
        raise RuntimeError(f"{doc['doc_id']}: form values not stored: {mismatches}")
    return {"filled_by": f"pylopdf set_form_field {pylopdf.__version__}", "fields": len(fields), "embedded_font_values": embedded}


# ------------------------------------------------------------------ verification


def _norm(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKC", text) if not ch.isspace() and unicodedata.category(ch)[0] in "LN")


def page_check(pdf: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Probe each native text block on its assigned page with pylopdf extraction.

    A probe is the first 10 normalized letters/digits of the block's longest native
    string. ``elsewhere`` counts probes found only on another page (a pagination
    error); ``missing`` counts probes found nowhere (often an extraction gap such as
    visual-order RTL or shaped scripts, not a truth error).
    """
    import warnings

    import pylopdf

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        document = pylopdf.Document(str(pdf))
        pages = [_norm(page.get_text()) for page in document]
        document.close()
    counts: Counter[str] = Counter()
    problems = []
    for block in record["blocks"]:
        if block["kind"] in {"figure", "header", "footer"} or (block["kind"] == "table" and block["rendering"] not in {"ruled", "borderless"}):
            continue
        strings = [_norm(s) for s in core.native_strings(block) if s]
        strings = [s for s in strings if len(s) >= 6]
        if not strings:
            continue
        probe = max(strings, key=len)[:10]
        page = block["page"]
        if probe in pages[page - 1]:
            counts["on_page"] += 1
        elif any(probe in text for text in pages):
            counts["elsewhere"] += 1
            problems.append({"page": page, "kind": block["kind"], "probe": probe})
        else:
            counts["missing"] += 1
    return {"probes": sum(counts.values()), **counts, "elsewhere_examples": problems[:5]}


def pdf_fonts(pdf: Path) -> dict[str, int]:
    """Count font dictionaries by subtype and embedding across all pages."""
    from pypdf import PdfReader

    reader = PdfReader(pdf)
    seen: dict[int, str] = {}

    def visit(resources: Any) -> None:
        fonts = (resources or {}).get("/Font") if resources else None
        for ref in (fonts.get_object().values() if fonts else []):
            font = ref.get_object()
            key = id(font) if not hasattr(ref, "idnum") else ref.idnum
            subtype = str(font.get("/Subtype"))
            descriptor = font.get("/FontDescriptor")
            if subtype == "/Type0":
                descriptor = font["/DescendantFonts"][0].get_object().get("/FontDescriptor")
            embedded = bool(descriptor) and any(k in descriptor.get_object() for k in ("/FontFile", "/FontFile2", "/FontFile3"))
            seen[key] = f"{subtype.lstrip('/')}{'-embedded' if embedded else ''}"
        for ref in ((resources or {}).get("/XObject") or {}).values() if resources else []:
            xobject = ref.get_object()
            if xobject.get("/Subtype") == "/Form" and "/Resources" in xobject:
                visit(xobject["/Resources"].get_object())

    for page in reader.pages:
        visit(page.get("/Resources").get_object() if page.get("/Resources") else None)
    return dict(Counter(seen.values()))


# ------------------------------------------------------------------ build


def tool_versions() -> dict[str, str]:
    """Producer tool and library versions."""
    import PIL
    import pypdf
    import reportlab

    import pylopdf

    versions = {}
    for name, command in (("chromium", ["chromium", "--version"]), ("soffice", ["soffice", "--version"])):
        try:
            versions[name] = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            versions[name] = ""
    versions.update(reportlab=reportlab.Version, pylopdf=pylopdf.__version__, pypdf=pypdf.__version__, pillow=PIL.__version__,
                    python=sys.version.split()[0])
    return versions


def build_one(doc: dict[str, Any], docs_dir: Path, versions: dict[str, str]) -> dict[str, Any]:
    """Produce one document (own Chromium and LibreOffice profiles) and return its report entry."""
    start = _usage()
    folder = guard_path(docs_dir / doc["doc_id"])
    if folder.exists():
        shutil.rmtree(folder)
    (folder / "assets").mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="wild2-chromium-") as chrome, tempfile.TemporaryDirectory(prefix="wild2-lo-") as lo:
        media_records = resolve_media(doc, folder / "assets", Path(chrome))
        detail = produce(doc, folder, Path(chrome), Path(lo), versions)
    pdf = folder / "source.pdf"
    facts = inspect_pdf(pdf)
    facts["producer_detail"] = detail
    record = core.truth(doc, page_count=facts["page_count"], outline=facts["outline"], pdf_facts=facts)
    problems = core.validate(record) + core.check_arithmetic(record)
    if problems:
        raise ValueError(f"{doc['doc_id']}: invalid truth {problems}")
    write_json(folder / "truth.json", record)
    checks = page_check(pdf, record)
    tables = [b for b in record["blocks"] if b["kind"] == "table"]
    return {
        "doc_id": doc["doc_id"], "template": doc["template"], "producer": doc["producer"], "tagged_pdf": facts["tagged"],
        "languages": doc["languages"], "dir": doc["dir"], "page_size": doc["page_size"], "page_count": facts["page_count"],
        "unicode_features": record["unicode_features"], "media": media_records,
        "tables": len({t.get("logical_id", t["id"]) for t in tables if t["rendering"] != "chart_data"}),
        "continued_tables": record["continued_tables"],
        "form_fields": sum(1 for b in record["blocks"] if b["kind"] == "form_field"),
        "equations": sum(1 for b in record["blocks"] if b["kind"] == "equation"),
        "code_blocks": sum(1 for b in record["blocks"] if b["kind"] == "code"),
        "producer_detail": detail, "fonts": pdf_fonts(pdf),
        "pdf": {k: v for k, v in facts.items() if k not in {"outline", "producer_detail"}}, "outline_entries": len(facts["outline"]),
        "page_check": checks, "resources": _delta(start),
    }


def _build_worker(arguments: tuple[str, str, dict[str, str]]) -> dict[str, Any] | str:
    # Documents hold formatting callables, so each worker composes its own copy (composition is pure).
    doc_id, docs_dir, versions = arguments
    try:
        (doc,) = compose([doc_id])
        assign_photos([doc], media.load_photos(PHOTO_DIRECTORY))
        return build_one(doc, Path(docs_dir), versions)
    except Exception as error:
        return f"{doc_id}: {type(error).__name__}: {error}"


def build(directory: Path, *, only: list[str] | None = None, workers: int = 4) -> dict[str, Any]:
    """Build the selected documents under ``directory/docs`` and write ``docs/build-report.json``."""
    directory = guard_path(directory)
    docs_dir = directory / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    started = _usage()
    versions = tool_versions()
    photos = media.load_photos(PHOTO_DIRECTORY)
    order_ids = [doc_id for doc_id, _, _ in registry()]
    selected = [doc_id for doc_id in order_ids if not only or doc_id in only]
    reports, failures = [], []
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        for result in pool.map(_build_worker, [(doc_id, str(docs_dir), versions) for doc_id in selected]):
            if isinstance(result, str):
                failures.append(result)
                print("FAILED " + result, file=sys.stderr, flush=True)
                continue
            reports.append(result)
            print(json.dumps({"doc_id": result["doc_id"], "pages": result["page_count"], "scale": result["producer_detail"]["fit_scale"],
                              "page_check": {k: v for k, v in result["page_check"].items() if k != "elsewhere_examples"}},
                             ensure_ascii=False), flush=True)
    previous = docs_dir / "build-report.json"
    if only and previous.is_file():
        kept = [r for r in json.loads(previous.read_text())["documents"] if r["doc_id"] not in {x["doc_id"] for x in reports}]
        reports = kept + reports
    order = {doc_id: i for i, doc_id in enumerate(order_ids)}
    reports.sort(key=lambda r: order.get(r["doc_id"], 10**6))
    report = {
        "version": 2, "corpus": "wild-v2", "seed": SEED, "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool_versions": versions, "photos_available": len(photos), "documents": reports, "failures": failures,
        "summary": summarize(reports),
        "resources": {"total": _delta(started), "documents": document_resources(reports), "workers": workers,
                      "host_cpus": os.cpu_count(),
                      "measurement": "resource.getrusage deltas, no sampling. 'total' covers the coordinating process only "
                                     "(worker processes come from the multiprocessing forkserver and are not its children). "
                                     "Per-document entries are measured inside each worker: self CPU plus waited children "
                                     "(Chromium, LibreOffice); RSS values are lifetime peaks of that worker and of its largest "
                                     "child. 'documents' sums CPU over documents and takes the maximum peaks."},
        "hosted_calls": 0, "gpu": "disabled (--disable-gpu); CPU only",
    }
    write_json(docs_dir / "build-report.json", report)
    return report


def document_resources(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-document worker measurements (CPU summed, peak RSS maximum)."""
    items = [r["resources"] for r in reports]
    return {"cpu_seconds_self": round(sum(i["cpu_seconds_self"] for i in items), 3),
            "cpu_seconds_children": round(sum(i["cpu_seconds_children"] for i in items), 3),
            "wall_seconds_sum": round(sum(i["wall_seconds"] for i in items), 3),
            "peak_rss_kib_worker": max((i["lifetime_peak_rss_kib_self"] for i in items), default=0),
            "peak_rss_kib_child": max((i["lifetime_peak_rss_kib_children"] for i in items), default=0)}


def summarize(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Corpus-level counts for the build report."""
    pages = sorted(r["page_count"] for r in reports)
    return {
        "documents": len(reports), "pages": sum(pages), "median_pages": pages[len(pages) // 2] if pages else 0,
        "producers": dict(Counter(r["producer"] for r in reports)),
        "tagged": sum(1 for r in reports if r["tagged_pdf"]),
        "templates": dict(Counter(r["template"] for r in reports)),
        "languages": dict(Counter(r["languages"][0] for r in reports)),
        "all_language_tags": sorted({tag for r in reports for tag in r["languages"]}),
        "continued_table_segments": sum(len(r["continued_tables"]) for r in reports),
        "form_fields": sum(r["form_fields"] for r in reports), "equations": sum(r["equations"] for r in reports),
        "code_blocks": sum(r["code_blocks"] for r in reports),
        "unicode_features": sorted({f for r in reports for f in r["unicode_features"]}),
        "page_check": dict(sum((Counter({k: v for k, v in r["page_check"].items() if isinstance(v, int)}) for r in reports), Counter())),
        "fonts": dict(sum((Counter(r["fonts"]) for r in reports), Counter())),
    }


def flatten(directory: Path, workers: int, docs: list[str] | None = None) -> int:
    """Derive L0-L9 variants with ``bench.wild_flatten`` (wild-v1 tessdata when present)."""
    if TESSDATA.is_dir():
        os.environ["TESSDATA_PREFIX"] = str(TESSDATA)
    from bench import wild_flatten

    argv = ["--directory", str(directory), "--workers", str(workers), "--seed", "wild-v2"]
    if docs:
        argv += ["--docs", *docs]
    return wild_flatten.main(argv)


def main() -> None:
    """Build wild-v2 L0 documents, truth and (optionally) flattened variants."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--only", nargs="*", help="build only these doc ids")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--no-flatten", action="store_true", help="skip bench.wild_flatten variants")
    parser.add_argument("--flatten-workers", type=int, default=4)
    args = parser.parse_args()
    report = build(args.directory, only=args.only, workers=args.workers)
    print(json.dumps({"summary": report["summary"], "failures": report["failures"], "resources": report["resources"]["total"]},
                     indent=2, ensure_ascii=False))
    status = 1 if report["failures"] else 0
    if not args.no_flatten:
        status |= flatten(guard_path(args.directory), args.flatten_workers, args.only)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
