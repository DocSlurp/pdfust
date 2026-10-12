"""Build the wild-v1 DEV corpus and audit native extraction across flattening levels.

See ``bench/WILD_CORPUS.md``. Scores are language-agnostic character-bigram
multiset F1 for text, best-match cell recall for tables, and per-script and
per-Unicode-feature survival reported both exactly and after NFKC
normalization. These are DEV diagnostics on synthetic documents, not
real-world quality claims.
"""

# Fixed local tools (pdftoppm, our own bench modules) run with argument lists.
# ruff: noqa: PLR2004, S603
from __future__ import annotations

import argparse
import html
import json
import os
import resource
import subprocess
import sys
import time
import unicodedata
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import jev_pdf
from bench.silver import guard_path, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
TEXT_BLOCKS = {"heading", "paragraph", "sidebar", "callout", "footnote", "header", "footer"}
NATIVE_TABLES = {"ruled", "borderless"}
# Probe characters per declared feature; survival is counted over truth occurrences.
FEATURE_PROBES: dict[str, str] = {
    "ligature": "\ufb00\ufb01\ufb02\ufb03\ufb04",
    "nbsp": "\u00a0",
    "narrow_nbsp": "\u202f",
    "zero_width": "\u200b\u200c\u200d\u2060",
    "soft_hyphen": "\u00ad",
    "unicode_minus": "\u2212",
    "dashes": "\u2013\u2014\u2012",
    "smart_quotes": "\u2018\u2019\u201c\u201d\u00ab\u00bb\u201e",
    "currency": "\u20ac\u00a3\u00a5\u20b9\u20a9\u20aa\u0e3f\u20ab",
    "math_symbols": "\u00b1\u00d7\u00f7\u2264\u2265\u00b5\u00b0\u2030",
    "superscripts": "\u00b2\u00b3\u00b9\u2070\u2074\u2075\u2076\u2077\u2078\u2079",
    "bidi_controls": "\u200e\u200f\u2066\u2067\u2068\u2069\u202a\u202b\u202c",
}


def _measure() -> dict[str, float]:
    own = resource.getrusage(resource.RUSAGE_SELF)
    kids = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "wall": time.perf_counter(),
        "cpu_self": own.ru_utime + own.ru_stime,
        "cpu_children": kids.ru_utime + kids.ru_stime,
        "peak_rss_kib_self": own.ru_maxrss,
        "peak_rss_kib_children": kids.ru_maxrss,
    }


def _delta(start: dict[str, float]) -> dict[str, Any]:
    end = _measure()
    return {
        "wall_seconds": end["wall"] - start["wall"],
        "cpu_seconds_self": end["cpu_self"] - start["cpu_self"],
        "cpu_seconds_children": end["cpu_children"] - start["cpu_children"],
        "peak_rss_kib_self": end["peak_rss_kib_self"],
        "peak_rss_kib_children": end["peak_rss_kib_children"],
        "measurement": "getrusage self and waited children; lifetime peaks; no sampling",
    }


# ---------------------------------------------------------------- truth helpers


def truth_text(truth: dict[str, Any]) -> str:
    """Return text a native text layer should carry: prose, lists and native tables."""
    parts: list[str] = []
    for block in truth["blocks"]:
        kind = block["kind"]
        if kind in TEXT_BLOCKS:
            parts.append(block.get("text", ""))
        elif kind == "list":
            parts.extend(block.get("items", []))
        elif kind == "table" and block.get("rendering") in NATIVE_TABLES:
            parts.extend(cell for row in block["values"] for cell in row if cell)
            if block.get("caption"):
                parts.append(block["caption"])
        elif kind == "figure" and block.get("caption"):
            parts.append(block["caption"])
    return "\n".join(parts)


def image_text(truth: dict[str, Any]) -> str:
    """Return text that exists only as pixels in the born-digital document."""
    parts: list[str] = []
    for block in truth["blocks"]:
        if block["kind"] == "figure":
            parts.extend(block.get("text_in_image", []))
        elif block["kind"] == "table" and block.get("rendering") not in NATIVE_TABLES:
            parts.extend(cell for row in block["values"] for cell in row if cell)
    return "\n".join(parts)


def _bigrams(text: str) -> Counter[str]:
    """Bigrams within whitespace tokens; unspaced scripts form long tokens naturally."""
    counts: Counter[str] = Counter()
    for token in text.split():
        if len(token) == 1:
            counts[token] += 1
        else:
            counts.update(token[i : i + 2] for i in range(len(token) - 1))
    return counts


def bigram_f1(reference: str, prediction: str) -> dict[str, float | None]:
    """Language-agnostic content overlap; order-insensitive by design."""
    ref, pred = _bigrams(reference), _bigrams(prediction)
    if not ref:
        return {"precision": None, "recall": None, "f1": None}
    overlap = sum((ref & pred).values())
    precision = overlap / sum(pred.values()) if pred else 0.0
    recall = overlap / sum(ref.values())
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def _script(char: str) -> str | None:
    """Coarse script label from the Unicode name; ASCII and non-letters are ignored."""
    if char.isascii() or unicodedata.category(char) not in {"Lu", "Ll", "Lt", "Lm", "Lo", "Mn", "Mc"}:
        return None
    word = unicodedata.name(char, "OTHER").split()[0]
    return word if word in {"CJK", "HIRAGANA", "KATAKANA", "HANGUL", "ARABIC", "HEBREW", "DEVANAGARI", "THAI",
                            "CYRILLIC", "GREEK", "LATIN", "COMBINING"} else "OTHER"


def script_recall(reference: str, prediction: str) -> dict[str, dict[str, float | int]]:
    """Per-script codepoint multiset recall, exact and after NFKC on both sides."""
    result: dict[str, dict[str, float | int]] = {}
    for label, ref, pred in (
        ("exact", reference, prediction),
        ("nfkc", unicodedata.normalize("NFKC", reference), unicodedata.normalize("NFKC", prediction)),
    ):
        ref_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for char in ref:
            script = _script(char)
            if script:
                ref_counts[script][char] += 1
        pred_counts = Counter(pred)
        for script, counts in ref_counts.items():
            total = sum(counts.values())
            kept = sum(min(n, pred_counts[c]) for c, n in counts.items())
            entry = result.setdefault(script, {"chars": total})
            entry[label] = kept / total
    return result


def feature_survival(reference: str, prediction: str) -> dict[str, dict[str, int]]:
    """Count probe characters that appear in truth and in extraction."""
    result = {}
    pred = Counter(prediction)
    for feature, probes in FEATURE_PROBES.items():
        expected = sum(reference.count(c) for c in probes)
        if expected:
            kept = sum(min(reference.count(c), pred[c]) for c in probes)
            result[feature] = {"expected": expected, "exact_kept": kept}
    marks = sum(1 for c in reference if unicodedata.category(c) == "Mn")
    if marks:
        result["combining_marks"] = {
            "expected": marks,
            "exact_kept": min(marks, sum(1 for c in prediction if unicodedata.category(c) == "Mn")),
        }
    if any(unicodedata.east_asian_width(c) == "F" for c in reference):
        expected = sum(1 for c in reference if unicodedata.east_asian_width(c) == "F")
        result["fullwidth"] = {
            "expected": expected,
            "exact_kept": min(expected, sum(1 for c in prediction if unicodedata.east_asian_width(c) == "F")),
        }
    emoji = sum(1 for c in reference if ord(c) >= 0x1F000)
    if emoji:
        result["emoji"] = {"expected": emoji, "exact_kept": min(emoji, sum(1 for c in prediction if ord(c) >= 0x1F000))}
    return result


def _cells(values: list[list[str | None]]) -> Counter[str]:
    return Counter(" ".join((cell or "").split()) for row in values for cell in row if cell and cell.strip())


def table_scores(truth: dict[str, Any], tables: list[list[list[str | None]]]) -> list[dict[str, Any]]:
    """Best-match each native truth table against extracted tables by cell multiset overlap."""
    results = []
    for block in truth["blocks"]:
        if block["kind"] != "table" or block.get("rendering") not in NATIVE_TABLES:
            continue
        ref = _cells(block["values"])
        best: dict[str, Any] = {"cell_recall": 0.0, "shape_exact": False, "matched": False}
        for candidate in tables:
            got = _cells(candidate)
            if not ref:
                continue
            recall = sum((ref & got).values()) / sum(ref.values())
            if recall > best["cell_recall"]:
                rows = len(candidate)
                cols = max((len(r) for r in candidate), default=0)
                best = {
                    "cell_recall": recall,
                    "shape_exact": rows == len(block["values"]) and cols == max(len(r) for r in block["values"]),
                    "matched": recall >= 0.5,
                    "exact": recall == 1.0 and rows == len(block["values"]),
                }
        results.append({"id": block.get("id"), "rendering": block["rendering"], **best})
    return results


# ---------------------------------------------------------------- extraction audit


def audit_pdf(path: Path, truth: dict[str, Any], password: str | None = None) -> dict[str, Any]:
    """Run native extraction once per variant and score it against truth."""
    start = _measure()
    record: dict[str, Any] = {"path": str(path)}
    try:
        doc = jev_pdf.open(str(guard_path(path)), password=password) if password else jev_pdf.open(
            str(guard_path(path))
        )
    except Exception as error:
        return {**record, "error": f"{type(error).__name__}: {error}", "resources": _delta(start)}
    with doc:
        text = doc.get_text()
        try:
            markdown = doc.to_markdown(table_strategy="text")
        except Exception as error:
            markdown, record["markdown_error"] = "", f"{type(error).__name__}: {error}"
        tables: list[list[list[str | None]]] = []
        for page in doc:
            for strategy in ("lines", "text"):
                try:
                    tables.extend(t.extract() for t in page.find_tables(strategy=strategy))
                except Exception as error:
                    record.setdefault("table_errors", []).append(f"{strategy}: {type(error).__name__}")
        meta = doc.metadata
        toc = doc.get_toc()
        page_count = len(doc)
    reference = truth_text(truth)
    record.update(
        page_count=page_count,
        text_chars=len(text.strip()),
        text=bigram_f1(reference, text),
        text_nfkc=bigram_f1(unicodedata.normalize("NFKC", reference), unicodedata.normalize("NFKC", text)),
        markdown=bigram_f1(reference, markdown),
        image_only_text_recovered=bigram_f1(image_text(truth), text)["recall"] if image_text(truth) else None,
        scripts=script_recall(reference, text),
        features=feature_survival(reference, text),
        tables=table_scores(truth, tables),
        metadata={
            "title_match": bool(meta.get("title")) and meta.get("title") == truth["metadata"].get("title"),
            "author_match": bool(meta.get("author")) and meta.get("author") == truth["metadata"].get("author"),
        },
        outline={"expected": len(truth.get("outline", [])), "found": len(toc)},
        resources=_delta(start),
    )
    return record


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(audits: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per level; failed opens count as zero text and table recall."""
    by_level: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audits:
        by_level[row["level"]].append(row)
    summary = {}
    for level, rows in sorted(by_level.items()):
        tables = [t for r in rows for t in r.get("tables", [])]
        summary[level] = {
            "documents": len(rows),
            "errors": sum("error" in r for r in rows),
            "text_f1": _mean([(r.get("text") or {}).get("f1") or 0.0 for r in rows]),
            "text_nfkc_f1": _mean([(r.get("text_nfkc") or {}).get("f1") or 0.0 for r in rows]),
            "markdown_f1": _mean([(r.get("markdown") or {}).get("f1") or 0.0 for r in rows]),
            "tables": len(tables),
            "table_matched": sum(bool(t.get("matched")) for t in tables),
            "table_exact": sum(bool(t.get("exact")) for t in tables),
            "table_cell_recall": _mean([t["cell_recall"] for t in tables]),
            "title_match": sum(r.get("metadata", {}).get("title_match", False) for r in rows),
            "outline_found": sum(bool(r.get("outline", {}).get("found")) for r in rows),
        }
    return summary


def summarize_unicode(audits: list[dict[str, Any]], level: str) -> dict[str, Any]:
    """Per-script and per-feature survival for one level."""
    scripts: dict[str, list[float]] = defaultdict(list)
    scripts_nfkc: dict[str, list[float]] = defaultdict(list)
    features: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in audits:
        if row["level"] != level or "error" in row:
            continue
        for script, entry in row["scripts"].items():
            # A script may exist on only one side of NFKC (e.g. ligatures fold to ASCII).
            if "exact" in entry:
                scripts[script].append(entry["exact"])
            if "nfkc" in entry:
                scripts_nfkc[script].append(entry["nfkc"])
        for feature, entry in row["features"].items():
            features[feature][0] += entry["expected"]
            features[feature][1] += entry["exact_kept"]
    return {
        "scripts": {
            s: {
                "docs": max(len(scripts[s]), len(scripts_nfkc[s])),
                "exact": _mean(scripts[s]),
                "nfkc": _mean(scripts_nfkc[s]),
            }
            for s in sorted(set(scripts) | set(scripts_nfkc))
        },
        "features": {f: {"expected": e, "kept": k, "rate": k / e if e else None} for f, (e, k) in features.items()},
    }


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def report_markdown(summary: dict[str, Any], unicode_l0: dict[str, Any], manifest: dict[str, Any]) -> str:
    """Render the per-level and L0 Unicode tables as Markdown."""
    lines = [
        "# Wild-v1 native extraction baseline",
        "",
        (
            f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} from {manifest['documents']} base "
            f"documents × {manifest['levels']} levels. Synthetic DEV documents; not a real-world quality claim."
        ),
        "Text F1 is character-bigram multiset overlap against the native text truth (order-insensitive).",
        "",
        (
            "| Level | Docs | Errors | Text F1 | Text F1 (NFKC) | Markdown F1 | Tables matched / exact / total | "
            "Cell recall | Title | Outline |"
        ),
        "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for level, s in summary.items():
        lines.append(
            f"| {level} | {s['documents']} | {s['errors']} | {_fmt(s['text_f1'])} | {_fmt(s['text_nfkc_f1'])} | "
            f"{_fmt(s['markdown_f1'])} | {s['table_matched']} / {s['table_exact']} / {s['tables']} | "
            f"{_fmt(s['table_cell_recall'])} | {s['title_match']} | {s['outline_found']} |"
        )
    lines += ["", "## Unicode survival at L0 (born-digital)", "", "| Script | Docs | Exact recall | NFKC recall |",
              "|---|---:|---:|---:|"]
    for script, s in sorted(unicode_l0["scripts"].items()):
        lines.append(f"| {script} | {s['docs']} | {_fmt(s['exact'])} | {_fmt(s['nfkc'])} |")
    lines += ["", "| Feature | Expected chars | Kept exactly | Rate |", "|---|---:|---:|---:|"]
    for feature, s in sorted(unicode_l0["features"].items()):
        lines.append(f"| {feature} | {s['expected']} | {s['kept']} | {_fmt(s['rate'])} |")
    return "\n".join(lines) + "\n"


def gallery(directory: Path, docs: list[str], levels: list[str]) -> None:
    """Write a contact-sheet HTML of page-1 thumbnails for every doc and level."""
    thumbs = directory / "gallery"
    thumbs.mkdir(exist_ok=True)
    rows = []
    for doc_id in docs:
        cells = []
        for level in levels:
            pdf = directory / "variants" / doc_id / f"{level}.pdf"
            if not pdf.exists():
                cells.append("<td>missing</td>")
                continue
            stem = thumbs / f"{doc_id}-{level}"
            if not stem.with_suffix(".png").exists():
                command = ["pdftoppm", "-r", "40", "-png", "-f", "1", "-l", "1", "-singlefile", str(pdf), str(stem)]
                subprocess.run(command, check=False, capture_output=True, timeout=120)
            cells.append(f"<td><img src='{html.escape(stem.name)}.png' loading='lazy'><br>{html.escape(level)}</td>")
        rows.append(f"<tr><th>{html.escape(doc_id)}</th>{''.join(cells)}</tr>")
    page = ("<!doctype html><meta charset='utf-8'><title>wild-v1</title><style>body{font-family:system-ui}"
            "img{width:150px;border:1px solid #ccc}td,th{vertical-align:top;font-size:11px}</style>"
            f"<table>{''.join(rows)}</table>")
    (thumbs / "index.html").write_text(page, encoding="utf-8")


OCR_LEVELS = ("L3_outlined", "L4_raster", "L6_phone_scan", "L7_photocopy", "L8_mixed", "L9_broken_tounicode")


def ocr_fallback(directory: Path, *, dpi: float = 200, threads: int = 4) -> dict[str, Any]:
    """Write `{level}+ocr.pdf` variants with pylopdf's native OCR on textless pages.

    Pages that already have extractable text are skipped by `apply_ocr`'s
    default, so mixed documents keep their native layer. CPU only.
    """
    directory = guard_path(directory)
    start = _measure()
    engine = jev_pdf.OcrEngine(threads=threads)
    report: dict[str, Any] = {"dpi": dpi, "threads": threads, "documents": {}}
    for variant_dir in sorted((directory / "variants").iterdir()):
        for level in OCR_LEVELS:
            source = variant_dir / f"{level}.pdf"
            target = variant_dir / f"{level}+ocr.pdf"
            if not source.exists() or target.exists():
                continue
            page_start = _measure()
            words = 0
            with jev_pdf.open(str(source)) as doc:
                for page in doc:
                    words += len(page.apply_ocr(dpi=dpi, engine=engine))
                doc.save(str(target))
            report["documents"][f"{variant_dir.name}/{level}"] = {"words": words, "resources": _delta(page_start)}
    report["resources"] = _delta(start)
    write_json(directory / "ocr-report.json", report)
    return report


ADAPTIVE_OCR_LEVELS = ("L0_tagged", "L1_untagged", "L8_mixed", "L9_broken_tounicode")
MIN_NATIVE_CHARS = 20
MIN_IMAGE_AREA = 0.02


def _page_needs_full_ocr(page: jev_pdf.Page) -> bool:
    """Full-page OCR when native text is nearly absent or glyphs lacked Unicode."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        text = page.get_text()
    unmapped = any("no Unicode mapping" in str(item.message) for item in caught)
    return unmapped or len(text.strip()) < MIN_NATIVE_CHARS


def adaptive_ocr(directory: Path, *, dpi: float = 200, threads: int = 4) -> dict[str, Any]:
    """Write `{level}+ocr-adaptive.pdf` variants with layer-aware OCR.

    Pages whose text layer is unusable get full-page OCR; other pages get OCR
    clipped to raster placements covering at least 2% of the page. Clipped OCR
    keeps the default skip, so native text inside a region wins.
    """
    directory = guard_path(directory)
    start = _measure()
    engine = jev_pdf.OcrEngine(threads=threads)
    report: dict[str, Any] = {"dpi": dpi, "threads": threads, "documents": {}}
    for variant_dir in sorted((directory / "variants").iterdir()):
        for level in ADAPTIVE_OCR_LEVELS:
            source = variant_dir / f"{level}.pdf"
            target = variant_dir / f"{level}+ocr-adaptive.pdf"
            if not source.exists() or target.exists():
                continue
            item_start = _measure()
            counts = {"full_pages": 0, "regions": 0, "words": 0}
            with jev_pdf.open(str(source)) as doc:
                for page in doc:
                    if _page_needs_full_ocr(page):
                        counts["full_pages"] += 1
                        counts["words"] += len(page.apply_ocr(dpi=dpi, engine=engine, skip_existing=False))
                        continue
                    width, height = page.rect.width, page.rect.height
                    for image in page.get_images():
                        box = image["bbox"]
                        if (box.x1 - box.x0) * (box.y1 - box.y0) < MIN_IMAGE_AREA * width * height:
                            continue
                        counts["regions"] += 1
                        clip = [box.x0, box.y0, box.x1, box.y1]
                        counts["words"] += len(page.apply_ocr(dpi=dpi, engine=engine, clip=clip))
                doc.save(str(target))
            report["documents"][f"{variant_dir.name}/{level}"] = {**counts, "resources": _delta(item_start)}
    report["resources"] = _delta(start)
    write_json(directory / "ocr-adaptive-report.json", report)
    return report


FILL_OCR_LEVELS = ADAPTIVE_OCR_LEVELS
FILL_MIN_CONFIDENCE = 0.7
FILL_UNRELIABLE_RATIO = 0.5


def _center_inside(native: tuple[float, float, float, float], box: Any, slack: float = 2.0) -> bool:  # noqa: ANN401
    """Whether a native word's centre lies inside an OCR box widened by `slack` points."""
    x0, y0, x1, y1 = box
    cx, cy = (native[0] + native[2]) / 2, (native[1] + native[3]) / 2
    return x0 - slack <= cx <= x1 + slack and y0 - slack <= cy <= y1 + slack


def fill_ocr(directory: Path, *, dpi: float = 200, threads: int = 4) -> dict[str, Any]:
    """Write `{level}+ocr-fill.pdf`: add OCR words only where no native word exists.

    Each page is recognized without modification; OCR boxes containing the
    centre of any native word are dropped, and the rest are inserted as an
    invisible layer, so native text is not duplicated. When glyphs lacked
    Unicode and native text is under half of the OCR text, the native layer is
    treated as unreliable and every OCR box is inserted.
    """
    directory = guard_path(directory)
    start = _measure()
    engine = jev_pdf.OcrEngine(threads=threads)
    report: dict[str, Any] = {"dpi": dpi, "threads": threads, "min_confidence": FILL_MIN_CONFIDENCE,
                              "documents": {}}
    for variant_dir in sorted((directory / "variants").iterdir()):
        raster = sorted(p.stem for p in variant_dir.glob("R[0-9][0-9]_*.pdf") if "+" not in p.stem)
        for level in (*FILL_OCR_LEVELS, *raster):
            source = variant_dir / f"{level}.pdf"
            target = variant_dir / f"{level}+ocr-fill.pdf"
            if not source.exists() or target.exists():
                continue
            item_start = _measure()
            counts = {"recognized": 0, "inserted": 0}
            with jev_pdf.open(str(source)) as doc:
                for page in doc:
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        native_words = page.get_text("words")
                    unmapped = any("no Unicode mapping" in str(item.message) for item in caught)
                    native = [tuple(w[:4]) for w in native_words]
                    words = engine.recognize(page, dpi=dpi, min_confidence=FILL_MIN_CONFIDENCE)
                    counts["recognized"] += len(words)
                    native_chars = sum(len(w[4]) for w in native_words)
                    ocr_chars = sum(len(word["text"].replace(" ", "")) for word in words)
                    if unmapped and native_chars < FILL_UNRELIABLE_RATIO * ocr_chars:
                        # Most glyphs lack Unicode: the native layer cannot gate OCR.
                        page.insert_ocr_text_layer([(*word["bbox"], word["text"]) for word in words])
                        counts["inserted"] += len(words)
                        counts["replaced_pages"] = counts.get("replaced_pages", 0) + 1
                        continue
                    # OCR boxes are usually whole lines and native boxes approximate the
                    # glyph body, so test whether any native word centre falls inside.
                    fresh = [
                        (*word["bbox"], word["text"]) for word in words
                        if not any(_center_inside(box, word["bbox"]) for box in native)
                    ]
                    if fresh:
                        page.insert_ocr_text_layer(fresh)
                        counts["inserted"] += len(fresh)
                doc.save(str(target))
            report["documents"][f"{variant_dir.name}/{level}"] = {**counts, "resources": _delta(item_start)}
    report["resources"] = _delta(start)
    write_json(directory / "ocr-fill-report.json", report)
    return report


def build(directory: Path, *, steps: list[str], workers: int) -> None:
    """Run the requested pipeline steps as fresh subprocesses, then audit."""
    directory = guard_path(directory)
    py = sys.executable
    commands = {
        "photos": [py, "-m", "bench.wild_photos", "--directory", str(directory)],
        "documents": [py, "-m", "bench.wild_documents", "--directory", str(directory)],
        "flatten": [py, "-m", "bench.wild_flatten", "--directory", str(directory), "--workers", str(workers)],
    }
    env = dict(os.environ)
    tessdata = directory / "tessdata"
    if (tessdata / "eng.traineddata").exists():
        # Local tessdata_fast models (Apache-2.0) cover every corpus language without system packages.
        env["TESSDATA_PREFIX"] = str(tessdata)
    for step in steps:
        if step in commands:
            subprocess.run(commands[step], check=True, cwd=ROOT, env=env)
        elif step == "ocr":
            ocr_fallback(directory)
        elif step == "ocr-adaptive":
            adaptive_ocr(directory)
        elif step == "ocr-fill":
            fill_ocr(directory)
    if "audit" in steps:
        audit(directory)


def audit_quirks(directory: Path) -> list[dict[str, Any]]:
    """Score quirk cases: document-based ones against their truth, raw ones against expected text."""
    manifest_path = directory / "quirks" / "manifest.json"
    if not manifest_path.exists():
        return []
    rows = []
    for case in json.loads(manifest_path.read_text(encoding="utf-8"))["cases"]:
        doc_id = case.get("doc_id")
        if doc_id:
            truth = json.loads((directory / "docs" / doc_id / "truth.json").read_text(encoding="utf-8"))
        else:
            truth = {"metadata": {}, "blocks": [{"kind": "paragraph", "text": case.get("expected_text", "")}]}
        row = audit_pdf(directory / case["path"], truth, password=case.get("password"))
        row.update(doc_id=doc_id or case.get("source_doc_id"), level=f"Q:{case['quirk_id']}",
                   quirk_family=case["family"], family=truth.get("family"),
                   producer=truth.get("producer"), languages=truth.get("languages", []))
        rows.append(row)
    return rows


def audit(directory: Path) -> dict[str, Any]:
    """Score every variant against its truth and write audit.json, audit.md and the gallery."""
    start = _measure()
    audits = []
    docs = sorted(p.name for p in (directory / "docs").iterdir() if (p / "truth.json").exists())
    levels: set[str] = set()
    for doc_id in docs:
        truth = json.loads((directory / "docs" / doc_id / "truth.json").read_text(encoding="utf-8"))
        for pdf in sorted((directory / "variants" / doc_id).glob("*.pdf")):
            levels.add(pdf.stem)
            row = audit_pdf(pdf, truth)
            row.update(doc_id=doc_id, level=pdf.stem, family=truth.get("family"),
                       producer=truth.get("producer"), languages=truth.get("languages", []))
            audits.append(row)
    audits.extend(audit_quirks(directory))
    levels.update(row["level"] for row in audits if row["level"].startswith("Q:"))
    summary = summarize(audits)
    unicode_by_level = {level: summarize_unicode(audits, level) for level in sorted(levels)}
    manifest = {"version": 1, "documents": len(docs), "levels": len(levels), "level_names": sorted(levels),
                "doc_ids": docs, "audit_resources": _delta(start)}
    write_json(directory / "manifest.json", manifest)
    write_json(directory / "audit.json", {"manifest": manifest, "summary": summary,
                                          "unicode": unicode_by_level, "audits": audits})
    report = report_markdown(summary, unicode_by_level.get("L0_tagged", {"scripts": {}, "features": {}}), manifest)
    (directory / "audit.md").write_text(report, encoding="utf-8")
    gallery(directory, docs, sorted(level for level in levels if not level.startswith("Q:")))
    return summary


def main() -> None:
    """Parse arguments and run the requested steps."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--steps", nargs="+", default=["photos", "documents", "flatten", "audit"],
                        choices=["photos", "documents", "flatten", "ocr", "ocr-adaptive", "ocr-fill", "audit"])
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    build(args.directory, steps=args.steps, workers=args.workers)
    print((guard_path(args.directory) / "audit.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
