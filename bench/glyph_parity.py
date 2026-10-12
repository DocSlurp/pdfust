"""Glyph-to-Unicode parity: unmapped-glyph rate and text F1 on the DEV wild corpora.

Measures, per page, the share of glyphs pdfust cannot map to Unicode (``Page.scan`` stats) and the
word-multiset F1 of its text against the authored ``truth.json`` and against MuPDF. MuPDF is a
reference decoder, not ground truth: where a font carries no usable mapping it emits control
characters, so agreement with it is secondary to the authored truth.

Only the wild-v1 and wild-v2 DEV variants and the wild-v1 quirks are read; never the held-out
silver sets. Usage: ``.venv/bin/python -m bench.glyph_parity OUT.json``.
"""

from __future__ import annotations

import json
import re
import sys
import warnings
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import pymupdf

import pdfust

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "bench/results/pdf-master-artifacts"
TEXT_LEVELS = ("L0_tagged", "L1_untagged", "L2_stripped", "L8_mixed", "L9_broken_tounicode")
MAX_PAGES_PER_FILE = 12
UNMAPPED_SUSPECT = 0.03
F1_GOOD = 0.9
_UNSPACED_SCRIPTS_FROM = 0x2E80
_WORD = re.compile(r"\w+", re.UNICODE)
_TRUTH_KEYS = {"text", "items", "values", "caption", "title", "cells"}


def _tokens(text: str) -> Counter[str]:
    """Count words; scripts written without spaces count per character."""
    out: Counter[str] = Counter()
    for word in _WORD.findall(text.lower()):
        if all(ord(c) < _UNSPACED_SCRIPTS_FROM for c in word):
            out[word] += 1
        else:
            out.update(word)
    return out


def f1(a: str, b: str) -> float:
    """Word-multiset F1 between two texts."""
    ca, cb = _tokens(a), _tokens(b)
    if not ca and not cb:
        return 1.0
    inter = sum((ca & cb).values())
    if not inter:
        return 0.0
    precision, recall = inter / sum(ca.values()), inter / sum(cb.values())
    return 2 * precision * recall / (precision + recall)


def _strings(node: object, out: list[str]) -> None:
    """Collect the text strings of one truth block."""
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for item in node:
            _strings(item, out)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key in _TRUTH_KEYS:
                _strings(value, out)


def truth_pages(variant: Path) -> dict[int, str]:
    """Return authored text per page from the truth.json of this variant's source document."""
    doc = variant.parent.name
    for candidate in (ART / "wild-v2/docs" / doc / "truth.json", ART / "wild-v1/docs" / doc / "truth.json"):
        if candidate.exists():
            pages: dict[int, list[str]] = {}
            for block in json.loads(candidate.read_text()).get("blocks", []):
                _strings(block, pages.setdefault(int(block.get("page", 1)) - 1, []))
            return {k: " ".join(v) for k, v in pages.items()}
    return {}


def recall_f1(text: str, truth: str) -> tuple[float, float]:
    """Return ``(F1, recall)`` of a page's words against the authored truth."""
    ct, cx = _tokens(truth), _tokens(text)
    if not ct:
        return 1.0, 1.0
    inter = sum((ct & cx).values())
    recall = inter / sum(ct.values())
    precision = inter / sum(cx.values()) if cx else 0.0
    return (2 * precision * recall / (precision + recall) if inter else 0.0), recall


def corpus() -> list[tuple[str, str, Path]]:
    """List ``(dataset, id, pdf)`` for every text-bearing variant that exists."""
    items: list[tuple[str, str, Path]] = []
    for ds in ("wild-v1", "wild-v2"):
        for d in sorted((ART / ds / "variants").glob("*")):
            items.extend((ds, f"{d.name}-{lv}", d / f"{lv}.pdf") for lv in TEXT_LEVELS if (d / f"{lv}.pdf").exists())
    for d in sorted(x for x in (ART / "wild-v1/quirks").glob("*") if not x.name.startswith("encrypt")):
        items.extend(("wild-v1-quirks", f"{d.name}/{p.stem}", p) for p in sorted(d.glob("*.pdf")))
    return items


def run_one(item: tuple[str, str, Path]) -> list[dict[str, Any]]:
    """Measure the leading pages of one PDF."""
    ds, name, path = item
    warnings.simplefilter("ignore")
    try:
        d = pdfust.open(str(path))
        m = pymupdf.open(str(path))
        n = min(len(d), len(m), MAX_PAGES_PER_FILE)
    except Exception as exc:
        return [{"ds": ds, "id": name, "error": str(exc)[:80]}]
    truth = truth_pages(path) if ds != "wild-v1-quirks" else {}
    rows: list[dict[str, Any]] = []
    for i in range(n):
        try:
            s = d[i].scan(images=False)["stats"]
            pt, mt = d[i].get_text(), m[i].get_text()
            row: dict[str, Any] = {
                "ds": ds,
                "id": name,
                "page": i,
                "glyphs": s["glyphs"],
                "unmapped": s["unmapped"],
                "f1": f1(pt, mt),
                "pdfust_chars": len(pt),
                "mupdf_chars": len(mt),
            }
            if truth.get(i):
                row["truth_f1"], row["truth_recall"] = recall_f1(pt, truth[i])
                row["mupdf_truth_f1"] = recall_f1(mt, truth[i])[0]
            rows.append(row)
        except Exception as exc:
            rows.append({"ds": ds, "id": name, "page": i, "error": str(exc)[:80]})
    return rows


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [r[key] for r in rows if key in r]
    return sum(values) / max(1, len(values))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate page rows into rates and means."""
    ok = [r for r in rows if "error" not in r]
    glyphs = sum(r["glyphs"] for r in ok)
    unmapped = sum(r["unmapped"] for r in ok)
    with_text = [r for r in ok if r["mupdf_chars"] > 0]
    return {
        "pages": len(ok),
        "errors": len(rows) - len(ok),
        "glyphs": glyphs,
        "unmapped": unmapped,
        "unmapped_rate": unmapped / glyphs if glyphs else 0.0,
        "pages_unmapped_gt3pct": sum(1 for r in ok if r["glyphs"] and r["unmapped"] / r["glyphs"] > UNMAPPED_SUSPECT),
        "mean_f1_vs_mupdf": _mean(with_text, "f1"),
        "truth_pages": sum(1 for r in ok if "truth_f1" in r),
        "mean_truth_f1": _mean(ok, "truth_f1"),
        "mean_truth_recall": _mean(ok, "truth_recall"),
        "mean_mupdf_truth_f1": _mean(ok, "mupdf_truth_f1"),
        "pages_f1_lt_0.9": sum(1 for r in with_text if r["f1"] < F1_GOOD),
    }


def main() -> None:
    """Run the corpus in parallel and write the JSON report named on the command line."""
    out = Path(sys.argv[1])
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(8) as pool:
        for part in pool.map(run_one, corpus(), chunksize=2):
            rows.extend(part)
    by_set: dict[str, list[dict[str, Any]]] = {}
    by_level: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_set.setdefault(r["ds"], []).append(r)
        level = "quirk" if r["ds"] == "wild-v1-quirks" else r["id"].rsplit("-", 1)[-1]
        by_level.setdefault(level, []).append(r)
    report = {
        "all": summarize(rows),
        "by_set": {k: summarize(v) for k, v in by_set.items()},
        "by_level": {k: summarize(v) for k, v in by_level.items()},
        "rows": rows,
    }
    out.write_text(json.dumps(report))
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
