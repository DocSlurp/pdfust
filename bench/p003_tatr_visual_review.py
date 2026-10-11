"""Render actual matched CPU TATR postprocessing diagnostics from verified artifacts."""

# ruff: noqa: EM101, EM102, TRY003, PLR2004, C901, PLR0912
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from bench.generalization_scoring import score_page
from bench.p003_visual_review import (
    COLORS,
    FONT,
    LATIN_FONT,
    RENDER_SETTINGS,
    difference_image,
    differences,
    digest,
    lines,
    output_grid,
    read,
    regional_views,
    render_page,
    verdicts,
)
from bench.silver import guard_path

IDS = ["p6ef5d3c5c2edb1c109c4", "p98d10ef50dee4b24506a", "pf012d6adb9592dab9a13"]


def verify_page(target: dict[str, Any], tables: list[dict[str, Any]], retained: dict[str, Any]) -> dict[str, Any]:
    """Replay retained structural matches and strict cell credit before drawing."""
    replay = score_page(target, tables, status="error" if retained["error"] else "ok")
    if any(replay[k] != v for k, v in retained.items() if k in replay):
        raise ValueError("Independent structural score differs from actual retained tables")
    marks = verdicts(target, tables, retained)
    exact = sum(v == "success" for cells in marks["output_cells"].values() for v in cells.values())
    if exact != retained["strict_exact_cells"]:
        raise ValueError("Independent strict cell score differs from actual retained tables")
    return marks


def source_word_verdicts(tables: list[dict[str, Any]], marks: dict[str, Any]) -> dict[str, str]:
    """Map only explicit cell-owned IDs; conflicting assignments remain unscored."""
    assignments: dict[str, set[str]] = {}
    for index, table in enumerate(tables):
        cells = table.get("cells", [])
        if len(cells) != table["row_count"] * table["col_count"]:
            raise ValueError("Source ownership cells are not an explicit row-major matrix")
        for key, state in marks["output_cells"][index].items():
            row, col, _, _ = key
            for identifier in cells[row * table["col_count"] + col].get("source_ids", []):
                assignments.setdefault(identifier, set()).add(state)
    return {
        identifier: next(iter(states)) if len(states) == 1 else "unscored" for identifier, states in assignments.items()
    }


def source_projection(
    directory: Path, source: dict[str, Any], tables: list[dict[str, Any]], marks: dict[str, Any]
) -> None:
    """Overlay retained approximate word projections, never inferred cell geometry."""
    assignments = source_word_verdicts(tables, marks)
    with Image.open(directory / "original.png") as image:
        original = image.convert("RGBA")
    overlay = Image.new("RGBA", original.size)
    draw = ImageDraw.Draw(overlay)
    x0, y0, x1, _ = source["page_size"]
    scale = original.width / (x1 - x0)
    for word in source["words"]:
        bbox = word.get("bbox")
        if bbox is None:
            continue
        color = COLORS[assignments.get(word["id"], "unscored")]
        box = ((bbox[0] - x0) * scale, (bbox[1] - y0) * scale, (bbox[2] - x0) * scale, (bbox[3] - y0) * scale)
        draw.rectangle(box, fill=(*color, 35), outline=(*color, 140), width=1)
    marked = Image.alpha_composite(original, overlay).convert("RGB")
    panel = Image.new("RGB", (marked.width, marked.height + 125), "white")
    lines(
        ImageDraw.Draw(panel),
        (20, 8),
        "Approximate retained OCR word projections, NOT physical cell/recognized word boxes. "
        "Green/red follows exact cell-owner verdict; amber unassigned or ambiguous.",
        marked.width - 40,
        20,
    )
    panel.paste(marked, (0, 125))
    panel.save(directory / "source-word-projections.png")
    (directory / "source-word-verdicts.json").write_text(json.dumps(assignments, indent=2) + "\n")


def run(official: Path, corpus: Path, output: Path, identifiers: list[str]) -> Path:
    """Create one immutable matched comparison; use no inference or source mutation."""
    started, cpu = time.monotonic(), time.process_time()
    if corpus.name != "natural16" or not 1 <= len(identifiers) <= 3 or len(set(identifiers)) != len(identifiers):
        raise ValueError("Select one through three explicit natural16 DEV pages")
    receipts: dict[str, str] = {}
    frozen = read(official / "frozen.json", receipts)
    baseline = guard_path(Path(frozen["input_directory"]).resolve())
    evaluation = read(official / "independent-evaluation.json", receipts)
    report = read(official / "report.json", receipts)
    base_eval = read(baseline / "independent-evaluation.json", receipts)
    base_report = read(baseline / "placement/report.json", receipts)
    read(baseline / "geometry/report.json", receipts)
    read(baseline / "source/manifest.json", receipts)
    targets = read(corpus / "private-targets.json", receipts)
    read(corpus / "manifest.json", receipts)
    for path, expected in (
        (official / "frozen.json", evaluation["frozen_sha256"]),
        (official / "report.json", evaluation["report_sha256"]),
        (baseline / "placement/report.json", base_eval["placement_report_sha256"]),
        (baseline / "geometry/report.json", base_eval["geometry_report_sha256"]),
        (baseline / "source/manifest.json", base_eval["source_manifest_sha256"]),
    ):
        if receipts[str(path.resolve())] != expected:
            raise ValueError(f"Independent receipt changed: {path}")
    for key in ("source_manifest_sha256", "geometry_report_sha256", "placement_report_sha256"):
        if evaluation["source_verification"][key] != base_eval[key]:
            raise ValueError("Matched postprocessors do not share the same verified inputs")
    records = {r["id"]: r for r in frozen["records"]}
    references = {r["id"]: r for r in targets["pages"]}
    treatment = evaluation["treatments"]["s1280-t0.5"]
    base_treatment = base_eval["treatments"]["s1280-t0.5-max_overlap"]
    scores = {r["id"]: r for r in treatment["pages"]}
    base_scores = {r["id"]: r for r in base_treatment["pages"]}
    pages = []
    for identifier in identifiers:
        record, target = records[identifier], references[identifier]
        pdf = guard_path(Path(record["pdf_path"]).resolve())
        receipts[str(pdf)] = digest(pdf.read_bytes())
        if receipts[str(pdf)] != record["pdf_sha256"]:
            raise ValueError("Input PDF changed")
        arms = []
        sources = []
        for name, root, rows, filename, retained in (
            (
                "baseline",
                baseline / "placement",
                base_report["rows"],
                f"{identifier}-s1280-t0.5-max_overlap.json",
                base_scores[identifier],
            ),
            ("official", official, report["rows"], f"{identifier}-s1280-t0.5.json", scores[identifier]),
        ):
            path = root / filename
            payload = read(path, receipts)
            row = next(r for r in rows if Path(r["path"]).name == filename)
            if receipts[str(path.resolve())] != row["sha256"]:
                raise ValueError("Verified prediction payload changed")
            sources.append(payload["source"])
            tables = [] if retained["error"] else payload["state"]["tables"]
            arms.append((name, tables, retained, verify_page(target, tables, retained)))
        if sources[0] != sources[1]:
            raise ValueError("Matched arms have different owned source words")
        pages.append((identifier, record, target, sources[0], arms))
    for path in (FONT, LATIN_FONT, Path(__file__), Path(__file__).with_name("p003_visual_review.py")):
        receipts[str(path.resolve())] = digest(path.read_bytes())
    identity = digest(
        json.dumps({"receipts": receipts, "ids": identifiers, "settings": RENDER_SETTINGS}, sort_keys=True).encode()
    )
    batch = guard_path(output.resolve()) / identity[:20]
    if (batch / "provenance.json").exists():
        return batch
    batch.mkdir(parents=True, exist_ok=False)
    findings = []
    for identifier, record, target, source, arms in pages:
        directory = batch / identifier
        directory.mkdir()
        grids = []
        for name, tables, score, marks in arms:
            arm_dir = directory / name
            arm_dir.mkdir()
            render_page(record, target, marks, arm_dir)
            source_projection(arm_dir, source, tables, marks)
            grid = output_grid(tables, marks)
            grid.save(arm_dir / "extracted-tables.png")
            grids.append(grid)
            diffs = differences(target, tables, score)
            (arm_dir / "differences.json").write_text(json.dumps(diffs, indent=2) + "\n")
            difference_image(diffs).save(arm_dir / "strict-differences.png")
            label = f"DEV {identifier} | detector inference 1280 | object threshold 0.5 | {name} CPU postprocessor"
            regional_views(arm_dir, tables, score, marks, label)
        with Image.open(directory / "official/original.png") as image:
            original = image.convert("RGB")
        original.thumbnail((900, 1800))
        height = max(original.height, *(g.height for g in grids)) + 180
        panel = Image.new("RGB", (2860, height), "#f5f7fa")
        draw = ImageDraw.Draw(panel)
        a, b = [arm[2]["strict_exact_cells"] for arm in arms]
        lines(
            draw,
            (20, 12),
            f"DEV {identifier} | matched retained objects and source-owned words | strict exact cells {a} -> {b}",
            2820,
            26,
        )
        lines(
            draw, (20, 54), "Original PDF | local max-overlap placement | pinned official TATR postprocessing", 2820, 24
        )
        lines(
            draw,
            (20, 92),
            "Detector inference 1280; object threshold 0.5. Green = exact reference match; "
            "red = strict reference disagreement; amber = unscored.",
            2820,
            20,
        )
        lines(
            draw,
            (20, 126),
            "Source word positions are approximate OCR whitespace projections. "
            "No physical cell boxes are invented; output grids are schematic.",
            2820,
            20,
        )
        panel.paste(original, (20, 180))
        panel.paste(grids[0], (950, 180))
        panel.paste(grids[1], (1910, 180))
        panel.save(directory / "matched-comparison.png")
        # Pair regional views without changing any original source pixels.
        for index in range(3):
            paths = [directory / name / f"regional-T{index}.png" for name, *_ in arms]
            if not all(p.exists() for p in paths):
                continue
            with Image.open(paths[0]) as left, Image.open(paths[1]) as right:
                paired = Image.new("RGB", (left.width + right.width, max(left.height, right.height) + 45), "white")
                lines(
                    ImageDraw.Draw(paired),
                    (20, 8),
                    f"Baseline left; official right | {identifier} | same source table T{index}",
                    3560,
                    24,
                )
                paired.paste(left, (0, 45))
                paired.paste(right, (left.width, 45))
                paired.save(directory / f"matched-regional-T{index}.png")
        (directory / "retained-source-words.json").write_text(json.dumps(source["words"], indent=2) + "\n")
        findings.append({"id": identifier, "scores": {name: score for name, _, score, _ in arms}})
    provenance = {
        "batch_sha256": identity,
        "inputs": receipts,
        "pages": findings,
        "scope": evaluation["scope"],
        "new_inference_calls": 0,
        "local_gpu_used": False,
        "all_dev_strict_cells": {
            "baseline": base_treatment["totals"]["strict_exact_cells"],
            "official": treatment["totals"]["strict_exact_cells"],
        },
        "source_geometry": "retained approximate uniform character advance; not recognized word/cell boxes",
        "renderer_settings": RENDER_SETTINGS,
        "resources": {
            "wall_seconds": time.monotonic() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "tool": "monotonic/process_time/getrusage Linux lifetime peak RSS",
            "scope": "single CPU renderer; concurrency one; sampled utilization unmeasured",
        },
    }
    (batch / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return batch


def main() -> None:
    """Render a bounded diagnostic batch once; no background timer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", nargs="+", default=IDS)
    args = parser.parse_args()
    print(run(args.official, args.corpus, args.output, args.ids))


if __name__ == "__main__":
    main()
