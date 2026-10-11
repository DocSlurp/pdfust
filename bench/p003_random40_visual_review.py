"""Explicit adapter for independently scored authored random40 DEV source/output views."""

# ruff: noqa: EM101, TRY003, PLC0415
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from PIL import Image, ImageDraw

from bench.p003_visual_review import digest, lines, output_grid, read, run
from bench.silver import guard_path

IDS = ("r4fa2f36b57caf506679ba995", "r536e002b19beb540f99f33e9", "r46eb52c32e5e171d556ba38a")


def form_audit(batch: Path, run_dir: Path, output: Path) -> Path:
    """Show a separately labelled qualitative source review, preserving original strict FP."""
    import pylopdf

    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    frozen = read(run_dir / "frozen.json", receipts)
    result = read(run_dir / (IDS[2] + "-result.json"), receipts)
    provenance = read(batch / "provenance.json", receipts)
    record = next(p for p in frozen["records"] if p["id"] == IDS[2])
    pdf = guard_path(Path(record["pdf_path"]).resolve())
    receipts[str(pdf)] = digest(pdf.read_bytes())
    if receipts[str(pdf)] != record["pdf_sha256"]:
        raise ValueError("Frozen source PDF changed")
    original_path = batch / IDS[2] / "original.png"
    receipts[str(original_path)] = digest(original_path.read_bytes())
    receipts[str(Path(__file__).resolve())] = digest(Path(__file__).read_bytes())
    identity = digest(json.dumps(receipts, sort_keys=True).encode())
    destination = guard_path(output.resolve()) / ("random40-form-" + identity[:20])
    if (destination / "source-review.json").exists():
        return destination
    destination.mkdir(parents=True, exist_ok=False)
    with Image.open(original_path) as image:
        original = image.convert("RGB")
    original.save(destination / "original.png")
    with pylopdf.Document(record["pdf_path"]) as document:
        scale = original.width / document[record["page_number"]].rect.width
    table = result["tables"][0]
    crop = original.crop(tuple(round(v * scale) for v in table["bbox"]))
    factor = min(760 / crop.width, 1400 / crop.height)
    crop = crop.resize((round(crop.width * factor), round(crop.height * factor)))
    grid = output_grid(
        [table],
        {
            "output_cells": {
                0: dict.fromkeys(
                    ((r, c, 1, 1) for r in range(table["row_count"]) for c in range(table["col_count"])), "unscored"
                )
            }
        },
    )
    panel = Image.new("RGB", (1800, max(crop.height, grid.height) + 235), "#f5f7fa")
    draw = ImageDraw.Draw(panel)
    lines(draw, (20, 10), "Reference audit: actual irregular key-value form and actual 8 x 2 output", 1760, 24)
    lines(draw, (20, 52), "Authored random40 DEV | Sonnet detector 640, crop 1024 | " + IDS[2], 1760, 18)
    lines(
        draw,
        (20, 86),
        "Gold defines zero tables: original strict false-positive count stays one. "
        "AMBER: source-reviewed plausible form interpretation, no secondary correctness score.",
        1760,
        18,
    )
    lines(
        draw,
        (20, 132),
        "Visual source review finds all eight form labels/values preserved, including blank Review. "
        "Title/footer lie outside table scope. No automatic relabeling or model tuning.",
        1760,
        18,
    )
    lines(
        draw,
        (20, 180),
        "Source is an actual crop at retained prediction bbox, with no cell masks. "
        "Full unmodified input is retained as original.png; strict-red view remains in the original batch.",
        1760,
        18,
    )
    panel.paste(crop, (20, 225))
    panel.paste(grid, (810, 225))
    panel.save(destination / "form-reference-audit.png")
    for path, expected in receipts.items():
        if digest(Path(path).read_bytes()) != expected:
            raise ValueError("Source-review dependency changed")
    (destination / "source-review.json").write_text(
        json.dumps(
            {
                "source_id": IDS[2],
                "scope": "Qualitative visual form-body preservation review; no secondary score",
                "original_strict_false_positive_tables": 1,
                "source_review": "Plausible key-value form interpretation; all eight displayed label/value pairs "
                "preserved, including blank Review",
                "actual_values": table["values"],
                "base_batch": str(batch),
                "receipts": receipts,
                "base_provenance": provenance,
                "resources": {
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": time.process_time() - cpu,
                    "lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                    "scope": "Single CPU adapter; wall/CPU for additional form view, RSS lifetime includes base render",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    return destination


def main() -> None:
    """Show two fixed source-reviewed pages and the retained Sonnet640 negative FP."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    batch = run(args.run, args.corpus, args.output, list(IDS), supplemental_random40=True)
    print(batch)
    print(form_audit(batch, args.run, args.output))


if __name__ == "__main__":
    main()
