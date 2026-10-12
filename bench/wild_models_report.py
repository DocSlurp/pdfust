"""Render the wild-v1 page-transcription model comparison from retained outputs.

    python -m bench.wild_models_report [--output bench/results/wild-v1-models.md]

Scores every arm in the hosted (`vision-v1`, `vision-raster-v1`) and open
GPU (`vision-open-v1`) experiment directories with `bench.wild_vision.evaluate`,
then reports three views: the ten scan levels every open model ran, the full
21-level hard-raster set, and native pylopdf extraction from `audit.json`.
Costs are summed from per-page ledger entries; open-model GPU rental is
billed separately and listed by hand in the report notes. DEV data only.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from bench import wild_vision
from bench.silver import guard_path

WILD = wild_vision.WILD
DIRECTORIES = ("vision-v1", "vision-raster-v1", "vision-open-v1")
OPEN_LEVELS = (
    "L4_raster", "L6_phone_scan", "L7_photocopy", "R07_gray_jpeg_q35", "R11_fax_204x98", "R12_skew_3deg",
    "R13_rotated_90_scan", "R15_halftone_moire", "R16_low_contrast_faded", "R19_mobile_pdf_compression",
)
THREE_LEVELS = ("L4_raster", "L6_phone_scan", "L7_photocopy")
NATIVE_LEVELS = ("L0_tagged", "L1_untagged", "L2_stripped", "L3_outlined+ocr", "L8_mixed+ocr-fill",
                 "L9_broken_tounicode+ocr-fill")
# Native OCR on the same ten scan levels: legacy L levels use the full-page OCR policy, R levels OCR fill.
NATIVE_OCR_LEVELS = tuple(f"{level}+ocr" if level.startswith("L") else f"{level}+ocr-fill" for level in OPEN_LEVELS)


def label(arm: str) -> str:
    """Model label shared by replicate arms (``-r1`` reruns join their original)."""
    return arm.removesuffix("-r1")


def collect() -> dict[str, dict[str, dict[str, Any]]]:
    """Per label and level: the most complete arm's level score plus page-record cost and latency."""
    best: dict[str, dict[str, dict[str, Any]]] = {}
    for name in DIRECTORIES:
        directory = guard_path(WILD / name)
        if not directory.is_dir():
            continue
        for arm, result in wild_vision.evaluate(directory).items():
            pages: dict[str, list[dict[str, Any]]] = {}
            for path in (directory / arm).glob("*--p*.json"):
                record = json.loads(path.read_text(encoding="utf-8"))
                pages.setdefault(record["level"], []).append(record)
            for level, values in result["levels"].items():
                records = pages.get(level, [])
                ok = [r for r in records if r.get("status") == "ok"]
                row = {
                    **values, "arm": arm, "directory": name, "pages": len(records), "ok_pages": len(ok),
                    "usd": sum(float((r.get("entry") or {}).get("accounted_usd") or 0) for r in ok),
                    "seconds": [r["client_seconds"] for r in ok if r.get("client_seconds") is not None],
                }
                current = best.setdefault(label(arm), {}).get(level)
                if current is None or (row["ok_pages"], -row["failed_pages"]) > (current["ok_pages"],
                                                                                  -current["failed_pages"]):
                    best[label(arm)][level] = row
    return best


def summarize(levels: dict[str, dict[str, Any]], wanted: tuple[str, ...] | None) -> dict[str, Any] | None:
    """Aggregate selected levels; None when any wanted level is missing."""
    keys = wanted or tuple(sorted(levels))
    if any(key not in levels for key in keys):
        return None
    rows = [levels[key] for key in keys]
    seconds = [s for row in rows for s in row["seconds"]]
    return {
        "levels": len(rows), "pages": sum(r["pages"] for r in rows), "ok": sum(r["ok_pages"] for r in rows),
        "text_f1": statistics.fmean(r["text_f1"] for r in rows),
        "exact": sum(r["table_exact"] for r in rows), "tables": sum(r["tables"] for r in rows),
        "cell": statistics.fmean(r["table_cell_recall"] for r in rows),
        "image": statistics.fmean(r["image_text_recall"] for r in rows if r.get("image_text_recall") is not None),
        "usd": sum(r["usd"] for r in rows), "median_s": statistics.median(seconds) if seconds else None,
        "arms": sorted({f"{r['directory']}/{r['arm']}" for r in rows}),
    }


def table(title: str, best: dict[str, dict[str, dict[str, Any]]], wanted: tuple[str, ...] | None,
          include: set[str] | None = None) -> list[str]:
    """One Markdown comparison table sorted by text F1."""
    rows = []
    for name, levels in best.items():
        selected = levels if include is None else {k: v for k, v in levels.items() if k in include}
        summary = summarize(selected, wanted)
        if summary:
            rows.append((name, summary))
    rows.sort(key=lambda item: -item[1]["text_f1"])
    header = ("| Arm | Pages ok | Text F1 | Exact tables | Cell recall | Image-text recall | "
              "Ledger USD | USD/page | Median request s |")
    out = [f"### {title}", "", header, "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, s in rows:
        per_page = f"{s['usd'] / s['ok']:.5f}" if s["ok"] and s["usd"] else "GPU rental"
        median = f"{s['median_s']:.1f}" if s["median_s"] is not None else "—"
        out.append(f"| {name} | {s['ok']}/{s['pages']} | {s['text_f1']:.3f} | {s['exact']}/{s['tables']} | "
                   f"{s['cell']:.3f} | {s['image']:.3f} | {s['usd']:.2f} | {per_page} | {median} |")
    return [*out, ""]


def level_matrix(best: dict[str, dict[str, dict[str, Any]]], levels: tuple[str, ...]) -> list[str]:
    """Text F1 per arm and level for arms covering every listed level."""
    names = sorted((n for n, v in best.items() if all(level in v for level in levels)),
                   key=lambda n: -statistics.fmean(best[n][level]["text_f1"] for level in levels))
    out = ["| Level | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
    out.extend(f"| {level} | " + " | ".join(f"{best[n][level]['text_f1']:.3f}" for n in names) + " |"
               for level in levels)
    return [*out, ""]


def native() -> list[str]:
    """Native pylopdf extraction and OCR-fill reference rows from the audit."""
    summary = json.loads((WILD / "audit.json").read_text(encoding="utf-8"))["summary"]
    header = "| Level | Documents | Text F1 | Exact tables | Cell recall |"
    out = ["### Native pylopdf extraction (no model)", "", header, "|---|---:|---:|---:|---:|"]
    for level in NATIVE_LEVELS:
        if level in summary:
            s = summary[level]
            out.append(f"| {level} | {s['documents']} | {s['text_f1']:.3f} | {s['table_exact']}/{s['tables']} | "
                       f"{s['table_cell_recall']:.3f} |")
    rows = [summary[level] for level in NATIVE_OCR_LEVELS if level in summary]
    if len(rows) == len(NATIVE_OCR_LEVELS):
        out.append(
            f"| Ten matched scan levels + native OCR | {sum(r['documents'] for r in rows)} | "
            f"{statistics.fmean(r['text_f1'] for r in rows):.3f} | {sum(r['table_exact'] for r in rows)}/"
            f"{sum(r['tables'] for r in rows)} | {statistics.fmean(r['table_cell_recall'] for r in rows):.3f} |"
        )
    return [*out, ""]


def main() -> None:
    """Write the generated sections between markers, keeping hand-written notes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("bench/results/wild-v1-models.md"))
    args = parser.parse_args()
    best = collect()
    raster = tuple(sorted(level for levels in best.values() for level in levels if level.startswith("R")))
    raster = tuple(dict.fromkeys(raster))
    generated = [
        "<!-- generated by bench.wild_models_report; edit notes outside these markers -->", "",
        *table("Ten matched scan levels (24 documents, 32 pages per level, 320 pages)", best, OPEN_LEVELS,
               set(OPEN_LEVELS)),
        *table("Three-level set (L4/L6/L7, 96 pages) including smaller hosted models", best, THREE_LEVELS,
               set(THREE_LEVELS)),
        *table(f"Hard-raster set ({len(raster)} levels, 672 pages)", best, raster, set(raster)),
        "### Text F1 by level (ten matched levels)", "", *level_matrix(best, OPEN_LEVELS),
        *native(), "<!-- end generated -->",
    ]
    text = args.output.read_text(encoding="utf-8") if args.output.exists() else "<!-- generated -->\n"
    head, _, rest = text.partition("<!-- generated")
    _, found, tail = rest.partition("<!-- end generated -->")
    if not found:  # first render: only the bare placeholder marker exists
        tail = rest.partition("-->")[2]
    args.output.write_text(head + "\n".join(generated) + tail, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
