"""Build the realistic born-digital (L0) documents of the wild-v1 DEV corpus.

Each document derives from one ``bench.p003_extension_cases.plans()`` entry and
keeps its structure (table shapes, merged spans, blank header rows, wrapped
descriptions, two tables for column pairs, no tables for negatives) while
replacing word salad with coherent authored content in many languages. See
``bench/WILD_CORPUS.md`` for the shared contract.

Producers: headless Chromium (``--disable-gpu``, private profile) prints
authored HTML to tagged PDF with an outline, after which pypdf rewrites Info,
XMP and ``/Lang`` without touching the structure tree. LibreOffice converts
authored flat ODF (FODT) with tagged-PDF and bookmark export under a private
user installation. Screenshots and raster charts are rendered by Chromium from
small local HTML pages. Everything runs on CPU without network access or
hosted models; photos come from ``photos/photos.json`` when present, with
deterministic generated placeholders otherwise.

Usage::

    python -m bench.wild_documents --directory bench/results/pdf-master-artifacts/wild-v1
"""

# Fixed local tools (chromium, soffice) run from PATH with argument lists; heavy imports stay lazy and
# the private LibreOffice profile path is part of the corpus contract.
# ruff: noqa: S603, S607, S108, PLC0415, E501, C901, PLR0912, PLR0913, PLR0917, TRY003, EM102, ANN401
from __future__ import annotations

import argparse
import html
import json
import os
import resource
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bench.silver import guard_path, write_json
from bench.wild_templates import docs_a, docs_b, docs_c, media, model
from bench.wild_templates.fodt_render import document_fodt
from bench.wild_templates.html_render import document_html

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
SEED = "wild-v1-documents-20261011"
FAMILIES = ("ruled", "borderless", "wrapped", "unnamed", "merged_headers", "mixed", "column_pairs", "negative")

Builder = Callable[[dict[str, Any]], dict[str, Any]]
# Each entry: document id, family, plan index within that family, producer and builder.
DOCS: tuple[tuple[str, str, int, str, Builder], ...] = (
    ("w-ruled-invoice-01", "ruled", 0, "chromium", docs_a.invoice_en),
    ("w-ruled-quarterly-02", "ruled", 4, "chromium", docs_a.quarterly_de),
    ("w-ruled-facture-03", "ruled", 7, "libreoffice", docs_a.facture_fr),
    ("w-borderless-specsheet-04", "borderless", 0, "chromium", docs_a.spec_sheet_ja),
    ("w-borderless-agenda-05", "borderless", 2, "chromium", docs_a.agenda_en_gb),
    ("w-borderless-jornadas-06", "borderless", 7, "libreoffice", docs_a.jornadas_es),
    ("w-wrapped-expense-07", "wrapped", 0, "chromium", docs_a.expense_en),
    ("w-wrapped-itinerary-08", "wrapped", 4, "chromium", docs_a.itinerary_vi),
    ("w-wrapped-delegacja-09", "wrapped", 2, "libreoffice", docs_a.delegacja_pl),
    ("w-unnamed-labappendix-10", "unnamed", 0, "chromium", docs_b.lab_appendix_en),
    ("w-unnamed-labappendix-11", "unnamed", 5, "chromium", docs_b.lab_appendix_zh),
    ("w-unnamed-journal-12", "unnamed", 1, "libreoffice", docs_b.lab_journal_ru),
    ("w-merged-grant-13", "merged_headers", 0, "chromium", docs_b.grant_en),
    ("w-merged-grant-14", "merged_headers", 4, "chromium", docs_b.grant_ko),
    ("w-merged-budget-15", "merged_headers", 5, "libreoffice", docs_b.butce_tr),
    ("w-mixed-research-16", "mixed", 1, "chromium", docs_b.research_en),
    ("w-mixed-research-17", "mixed", 7, "chromium", docs_b.research_hi),
    ("w-mixed-research-18", "mixed", 5, "libreoffice", docs_b.research_en_gb_lo),
    ("w-pairs-plans-19", "column_pairs", 0, "chromium", docs_c.plans_zh_tw),
    ("w-pairs-plans-20", "column_pairs", 4, "chromium", docs_c.plans_en),
    ("w-pairs-catering-21", "column_pairs", 1, "libreoffice", docs_c.catering_th),
    ("w-negative-memo-22", "negative", 0, "chromium", docs_c.memo_ar),
    ("w-negative-newsletter-23", "negative", 3, "chromium", docs_c.newsletter_en),
    ("w-negative-intake-24", "negative", 1, "libreoffice", docs_c.intake_he),
)
CHROMIUM_FLAGS = ("--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                  "--disable-background-networking", "--disable-sync", "--disable-component-update", "--hide-scrollbars")
LO_EXPORT = ('pdf:writer_pdf_Export:{"UseTaggedPDF":{"type":"boolean","value":"true"},'
             '"ExportBookmarks":{"type":"boolean","value":"true"}}')


# ------------------------------------------------------------------ composition: pure and deterministic


def load_plans() -> list[dict[str, Any]]:
    """Return the P003 extension plans (imported lazily: it pulls in the native extension)."""
    from bench.p003_extension_cases import plans

    return plans()


def compose(plans: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Compose every document from its plan without touching files, tools or photos."""
    plans = load_plans() if plans is None else plans
    by_family: dict[str, list[dict[str, Any]]] = {f: [p for p in plans if p["family"] == f] for f in FAMILIES}
    docs = []
    for doc_id, family, index, producer, builder in DOCS:
        plan = by_family[family][index]
        doc = builder(deepcopy(plan))
        doc.update(doc_id=doc_id, family=family, producer=producer, base_plan_id=plan["id"], plan_index=index)
        doc.setdefault("dir", "ltr")
        docs.append(doc)
    return docs


def _all_markup(blocks: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for block in blocks:
        if block["kind"] in {"columns", "pair", "group"}:
            out += _all_markup(block["blocks"])
            continue
        out += [block[key] for key in ("text", "title", "caption") if isinstance(block.get(key), str)]
        out += list(block.get("items", [])) if block["kind"] == "list" else []
    return out


def truth(doc: dict[str, Any], *, page_count: int, outline: list[dict[str, Any]]) -> dict[str, Any]:
    """Project an authored (and media-resolved) document onto the truth schema."""
    blocks = [model.truth_block(b) for b in model.flatten(doc["blocks"])]
    pages = range(1, page_count + 1)
    if doc.get("running_header"):
        blocks = [{"kind": "header", "text": doc["running_header"].format(page=p, pages=page_count)} for p in pages] + blocks
    if doc.get("running_footer"):
        blocks += [{"kind": "footer", "text": doc["running_footer"].format(page=p, pages=page_count)} for p in pages]
    links: list[dict[str, str]] = []
    for markup in _all_markup(doc["blocks"]):
        links += model.links(markup)
    native = [s for block in blocks for s in model.native_strings(block)]
    return {"version": 1, "doc_id": doc["doc_id"], "template": doc["template"], "producer": doc["producer"],
            "base_plan_id": doc["base_plan_id"], "family": doc["family"], "page_count": page_count,
            "metadata": doc["metadata"], "outline": outline, "links": links, "blocks": blocks,
            "languages": doc["languages"], "unicode_features": model.detect_features(native)}


def media_summary(doc: dict[str, Any]) -> list[str]:
    """Mixed-media elements present in one authored document."""
    found = set()
    for block in model.flatten(doc["blocks"]):
        kind = block["kind"]
        if kind == "figure":
            if block["figure_kind"] == "photo":
                found.add(f"photo_wrap_{block['wrap']}" if block["wrap"] != "none" else "photo")
            elif block["figure_kind"] == "screenshot":
                found.add("screenshot_" + block["render"]["mockup"])
            else:
                found.add("raster_chart" if block["chart"]["raster"] else "vector_chart")
        elif kind == "table" and block["rendering"] == "screenshot":
            found.add("screenshot_table")
        elif kind in {"sidebar", "callout", "footnote"}:
            found.add(kind)
        elif kind == "list":
            found.add("ordered_list" if block["ordered"] else "unordered_list")
        elif kind == "fields":
            found.add("form_fields")
    for markup in _all_markup(doc["blocks"]):
        if model.links(markup):
            found.add("hyperlinks")
        if "**" in markup or "*" in markup.replace("**", ""):
            found.add("emphasis")
    if any(b["kind"] == "columns" for b in doc["blocks"]):
        found.add("multi_column")
    if any(b["kind"] == "pair" for b in doc["blocks"]):
        found.add("side_by_side_tables")
    if doc.get("running_header") or doc.get("running_footer"):
        found.add("running_header_footer")
    if doc.get("dir") == "rtl":
        found.add("rtl")
    return sorted(found)


# ------------------------------------------------------------------ tools


def tool_versions() -> dict[str, str]:
    """Return producer tool versions (empty string when unavailable)."""
    versions = {}
    for name, command in (("chromium", ["chromium", "--version"]), ("soffice", ["soffice", "--version"])):
        try:
            versions[name] = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            versions[name] = ""
    import pypdf

    versions["pypdf"] = pypdf.__version__
    return versions


def _chromium(args: list[str], profile: Path) -> None:
    subprocess.run(["chromium", *CHROMIUM_FLAGS, f"--user-data-dir={profile}", *args], check=True, capture_output=True, timeout=180)


def screenshot(page_html: str, size: tuple[int, int], html_path: Path, png_path: Path, profile: Path) -> None:
    """Render one local HTML page to PNG at 2x device scale."""
    html_path.write_text(page_html, encoding="utf-8")
    _chromium(["--force-device-scale-factor=2", f"--window-size={size[0]},{size[1]}", f"--screenshot={png_path}",
               html_path.as_uri()], profile)
    if not png_path.is_file():
        raise RuntimeError(f"Chromium did not write {png_path}")
    _trim(png_path)


def _trim(png_path: Path, margin: int = 8) -> None:
    """Crop surplus white window area so generous window sizes never clip or pad the mockup."""
    from PIL import Image, ImageChops

    with Image.open(png_path) as image:
        rgb = image.convert("RGB")
    box = ImageChops.difference(rgb, Image.new("RGB", rgb.size, (255, 255, 255))).getbbox()
    if box:
        left, top, right, bottom = box
        rgb.crop((max(left - margin, 0), max(top - margin, 0), min(right + margin, rgb.width),
                  min(bottom + margin, rgb.height))).save(png_path, optimize=True)


def resolve_media(doc: dict[str, Any], assets: Path, photos: list[dict[str, Any]], photo_root: Path, profile: Path,
                  used: set[str]) -> list[dict[str, Any]]:
    """Render screenshots/charts, copy photos and fill ``src``/``svg``/``photo_id``/``text_in_image`` in place."""
    records = []
    for block in model.flatten(doc["blocks"]):
        if block["kind"] != "figure":
            continue
        if block["figure_kind"] == "photo":
            want = block["photo"]
            chosen = media.choose_photo(photos, want["prefer"], want["tags"], used)
            if chosen:
                used.add(chosen["id"])
                source = guard_path(photo_root / chosen["path"])
                block["src"] = chosen["id"] + source.suffix.lower()
                shutil.copyfile(source, assets / block["src"])
                block["photo_id"] = chosen["id"]
                block["caption"] = want["captions"].get(chosen["id"].split("-", 1)[-1], want["fallback"])
                block["alt"] = chosen.get("subject", "")
                records.append({"figure": block["id"], "photo_id": chosen["id"], "license": chosen.get("license")})
            else:
                block["src"] = f"placeholder-{block['id']}.jpg"
                media.placeholder_photo(assets / block["src"], f"{SEED}|{doc['doc_id']}|{block['id']}")
                block["photo_id"] = None
                block["caption"] = want["fallback"]
                records.append({"figure": block["id"], "photo_id": None, "placeholder": block["src"]})
            block["text_in_image"] = []
        elif block["figure_kind"] == "screenshot":
            render = block["render"]
            page, size, text = media.MOCKUPS[render["mockup"]](render["spec"])
            block["src"] = f"{block['id']}-{render['mockup']}.png"
            screenshot(page, size, assets / f"{block['id']}-{render['mockup']}.html", assets / block["src"], profile)
            block["text_in_image"] = text
            records.append({"figure": block["id"], "screenshot": render["mockup"], "window": list(size)})
        else:
            spec = block["chart"]
            draw = media.bar_chart_svg if spec["type"] == "bar" else media.line_chart_svg
            width, height = spec["size"]
            svg = draw(spec["spec"], width=width, height=height, font=_chart_font(doc))
            if spec["raster"] or doc["producer"] == "libreoffice":
                page, size = media.raster_chart_page(svg)
                block["src"] = f"{block['id']}-chart.png"
                screenshot(page, size, assets / f"{block['id']}-chart.html", assets / block["src"], profile)
                block["text_in_image"] = media.chart_labels(spec["spec"])
            else:
                block["svg"] = svg
                block["text_in_image"] = []
            records.append({"figure": block["id"], "chart": spec["type"], "raster": bool(spec["raster"])})
    return records


def _chart_font(doc: dict[str, Any]) -> str:
    lang = doc["metadata"]["lang"]
    special = {"ja": "Noto Sans CJK JP", "zh-CN": "Noto Sans CJK SC", "zh-TW": "Noto Sans CJK TC", "ko-KR": "Noto Sans CJK KR",
               "hi-IN": "Noto Sans Devanagari"}
    return f"{special[lang]}, Noto Sans" if lang in special else "Noto Sans"


# ------------------------------------------------------------------ metadata and verification


def _pdf_date(stamp: str) -> str:
    moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    return moment.strftime("D:%Y%m%d%H%M%S+00'00'")


def xmp_packet(meta: dict[str, Any], producer: str, creator_tool: str) -> bytes:
    """Return a complete XMP packet with dc, pdf and xmp properties."""
    e = html.escape
    keywords = ", ".join(meta["keywords"])
    body = (
        '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:pdf="http://ns.adobe.com/pdf/1.3/" '
        'xmlns:xmp="http://ns.adobe.com/xap/1.0/">'
        '<dc:format>application/pdf</dc:format>'
        f'<dc:title><rdf:Alt><rdf:li xml:lang="x-default">{e(meta["title"])}</rdf:li></rdf:Alt></dc:title>'
        f'<dc:creator><rdf:Seq><rdf:li>{e(meta["author"])}</rdf:li></rdf:Seq></dc:creator>'
        f'<dc:description><rdf:Alt><rdf:li xml:lang="x-default">{e(meta["subject"])}</rdf:li></rdf:Alt></dc:description>'
        f'<dc:language><rdf:Bag><rdf:li>{e(meta["lang"])}</rdf:li></rdf:Bag></dc:language>'
        f'<dc:subject><rdf:Bag>{"".join(f"<rdf:li>{e(k)}</rdf:li>" for k in meta["keywords"])}</rdf:Bag></dc:subject>'
        f'<pdf:Keywords>{e(keywords)}</pdf:Keywords><pdf:Producer>{e(producer)}</pdf:Producer>'
        f'<xmp:CreateDate>{meta["created"]}</xmp:CreateDate><xmp:ModifyDate>{meta["created"]}</xmp:ModifyDate>'
        f'<xmp:MetadataDate>{meta["created"]}</xmp:MetadataDate><xmp:CreatorTool>{e(creator_tool)}</xmp:CreatorTool>'
        "</rdf:Description></rdf:RDF></x:xmpmeta>\n" + " " * 1024 + '\n<?xpacket end="w"?>'
    )
    return body.encode("utf-8")


def rewrite_metadata(source: Path, target: Path, doc: dict[str, Any], creator_tool: str) -> None:
    """Set Info, XMP and ``/Lang`` on a Chromium PDF while preserving the structure tree."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject, TextStringObject

    meta = doc["metadata"]
    reader = PdfReader(source)
    producer = str((reader.metadata or {}).get("/Producer", ""))
    writer = PdfWriter(clone_from=reader)
    writer.add_metadata({"/Title": meta["title"], "/Author": meta["author"], "/Subject": meta["subject"],
                         "/Keywords": ", ".join(meta["keywords"]), "/Creator": creator_tool, "/Producer": producer,
                         "/CreationDate": _pdf_date(meta["created"]), "/ModDate": _pdf_date(meta["created"])})
    stream = DecodedStreamObject()
    stream.set_data(xmp_packet(meta, producer, creator_tool))
    stream[NameObject("/Type")] = NameObject("/Metadata")
    stream[NameObject("/Subtype")] = NameObject("/XML")
    root = writer._root_object  # noqa: SLF001 - pypdf has no public catalog setter for /Metadata
    root[NameObject("/Metadata")] = writer._add_object(stream)  # noqa: SLF001
    root[NameObject("/Lang")] = TextStringObject(meta["lang"])
    with target.open("wb") as handle:
        writer.write(handle)


def _outline(reader: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def walk(items: list[Any], level: int) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, level + 1)
            else:
                page = reader.get_destination_page_number(item)
                result.append({"level": level, "title": str(item.title), "page": page + 1 if page is not None else None})

    walk(reader.outline, 1)
    return result


def inspect_pdf(path: Path) -> dict[str, Any]:
    """Report tagging, outline, links, language, Info and XMP facts for a produced PDF."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    root = reader.trailer["/Root"]
    tree = root.get("/StructTreeRoot")
    kids = tree.get_object().get("/K") if tree is not None else None
    info = reader.metadata or {}
    xmp_raw = b""
    if "/Metadata" in root:
        xmp_raw = root["/Metadata"].get_object().get_data()
    links = sum(1 for page in reader.pages for annot in (page.get("/Annots") or [])
                if annot.get_object().get("/Subtype") == "/Link")
    return {
        "page_count": len(reader.pages),
        "tagged": tree is not None and kids is not None and "/MarkInfo" in root,
        "struct_tree_root": tree is not None, "mark_info": "/MarkInfo" in root,
        "marked": bool(root.get("/MarkInfo", {}).get("/Marked")) if "/MarkInfo" in root else False,
        "lang": str(root.get("/Lang", "")),
        "outline": _outline(reader), "link_annotations": links,
        "info": {k.lstrip("/"): str(v) for k, v in info.items()},
        "xmp": {"present": bool(xmp_raw), "dc_title": b"<dc:title>" in xmp_raw, "dc_creator": b"<dc:creator>" in xmp_raw,
                "dc_language": b"<dc:language>" in xmp_raw, "pdf_keywords": b"Keywords" in xmp_raw},
        "page_size_pt": [round(float(v), 1) for v in reader.pages[0].mediabox[2:]],
    }


# ------------------------------------------------------------------ build


def _usage() -> dict[str, float]:
    own, kids = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"wall": time.perf_counter(), "cpu_self": own.ru_utime + own.ru_stime, "cpu_children": kids.ru_utime + kids.ru_stime,
            "rss_self": own.ru_maxrss, "rss_children": kids.ru_maxrss}


def _delta(start: dict[str, float]) -> dict[str, Any]:
    end = _usage()
    return {"wall_seconds": round(end["wall"] - start["wall"], 3),
            "cpu_seconds_self": round(end["cpu_self"] - start["cpu_self"], 3),
            "cpu_seconds_children": round(end["cpu_children"] - start["cpu_children"], 3),
            "lifetime_peak_rss_kib_self": end["rss_self"], "lifetime_peak_rss_kib_children": end["rss_children"]}


def produce(doc: dict[str, Any], folder: Path, profile: Path, lo_profile: Path, versions: dict[str, str]) -> dict[str, Any]:
    """Write the source and produce ``source.pdf`` with the document's producer; return PDF facts."""
    assets = folder / "assets"
    pdf = folder / "source.pdf"
    if doc["producer"] == "chromium":
        source = folder / "source.html"
        source.write_text(document_html(doc), encoding="utf-8")
        raw = folder / "chromium-raw.pdf"
        _chromium(["--no-pdf-header-footer", "--generate-pdf-document-outline", f"--print-to-pdf={raw}", source.as_uri()], profile)
        creator = f"wild-v1 HTML template ({doc['template']}) printed by {versions.get('chromium') or 'Chromium'}"
        rewrite_metadata(raw, pdf, doc, creator)
        raw.unlink()
    else:
        source = folder / "source.fodt"
        source.write_text(document_fodt(doc, assets), encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="wild-lo-out-") as out:
            subprocess.run(["soffice", f"-env:UserInstallation={lo_profile.as_uri()}", "--headless", "--norestore",
                            "--convert-to", LO_EXPORT, "--outdir", out, str(source)], check=True, capture_output=True, timeout=300,
                           env={**os.environ, "TZ": "UTC"})
            shutil.move(Path(out) / "source.pdf", pdf)
    return inspect_pdf(pdf)


def build(directory: Path, *, only: list[str] | None = None) -> dict[str, Any]:
    """Build all (or selected) documents under ``directory/docs`` and write ``docs/build-report.json``."""
    directory = guard_path(directory)
    docs_dir = directory / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    started = _usage()
    versions = tool_versions()
    photos = media.load_photos(directory)
    plans_start = _usage()
    documents = compose()
    plan_usage = _delta(plans_start)
    used: set[str] = set()
    reports = []
    with tempfile.TemporaryDirectory(prefix="wild-chromium-profile-") as chrome_profile:
        lo_profile = Path("/tmp/wild-lo-profile")
        for doc in documents:
            if only and doc["doc_id"] not in only:
                continue
            start = _usage()
            folder = guard_path(docs_dir / doc["doc_id"])
            if folder.exists():
                shutil.rmtree(folder)
            (folder / "assets").mkdir(parents=True)
            media_records = resolve_media(doc, folder / "assets", photos, directory, Path(chrome_profile), used)
            facts = produce(doc, folder, Path(chrome_profile), lo_profile, versions)
            record = truth(doc, page_count=facts["page_count"], outline=facts["outline"])
            problems = model.validate_truth(record)
            if problems:
                raise ValueError(f"{doc['doc_id']}: invalid truth {problems}")
            write_json(folder / "truth.json", record)
            headings = sum(1 for b in record["blocks"] if b["kind"] == "heading")
            reports.append({
                "doc_id": doc["doc_id"], "template": doc["template"], "family": doc["family"], "producer": doc["producer"],
                "base_plan_id": doc["base_plan_id"], "plan_index_in_family": doc["plan_index"], "languages": doc["languages"],
                "page_size": doc["page_size"], "page_count": facts["page_count"], "media": media_summary(doc),
                "media_records": media_records, "unicode_features": record["unicode_features"],
                "tables": [{"id": b["id"], "rendering": b["rendering"], "rows": len(b["values"]), "cols": len(b["values"][0]),
                            "header_rows": b["header_rows"], "plan_table": b.get("plan_table")}
                           for b in model.flatten(doc["blocks"]) if b["kind"] == "table"],
                "pdf": {k: v for k, v in facts.items() if k != "outline"}, "outline_entries": len(facts["outline"]),
                "headings": headings, "checks": {
                    "tagged": facts["tagged"], "outline_present": bool(facts["outline"]) or not headings,
                    "title_matches": facts["info"].get("Title") == doc["metadata"]["title"],
                    "author_matches": facts["info"].get("Author") == doc["metadata"]["author"],
                    "lang_matches": facts["lang"] == doc["metadata"]["lang"],
                    "links_annotated": facts["link_annotations"] >= len(record["links"])},
                "resources": _delta(start),
            })
            print(json.dumps({"doc_id": doc["doc_id"], "pages": facts["page_count"], **reports[-1]["checks"]}, ensure_ascii=False), flush=True)
    report = {
        "version": 1, "seed": SEED, "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "tool_versions": versions,
        "photos_available": len(photos), "documents": reports,
        "corpus_unicode_features": sorted({f for r in reports for f in r["unicode_features"]}),
        "missing_unicode_features": sorted(set(model.UNICODE_FEATURES) - {f for r in reports for f in r["unicode_features"]}),
        "resources": {"compose": plan_usage, "total": _delta(started),
                      "measurement": "resource.getrusage self plus waited children (Chromium, LibreOffice); lifetime peaks, "
                                     "not per-document; no sampling; single process, sequential documents"},
        "hosted_calls": 0, "gpu": "disabled (--disable-gpu); CPU only",
    }
    write_json(docs_dir / "build-report.json", report)
    return report


def main() -> None:
    """Build the wild-v1 L0 documents."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--only", nargs="*", help="Build only these doc ids")
    args = parser.parse_args()
    report = build(args.directory, only=args.only)
    print(json.dumps({"documents": len(report["documents"]), "missing_unicode_features": report["missing_unicode_features"],
                      "resources": report["resources"]["total"]}, indent=2))


if __name__ == "__main__":
    main()
