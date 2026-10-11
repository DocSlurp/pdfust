"""Render pinned table-level character quality separately from physical structure."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

import argparse
import json
import math
import resource
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from bench.generalization_scoring import _cells, score_page
from bench.p003_visual_review import FONT, LATIN_FONT, RENDER_SETTINGS, digest, lines, output_grid, read
from bench.silver import guard_path

CASES = (
    ("natural", "acquisition-sonnet-yolo1024-crop1024-r0-c3", "p1bfa52a41a5e15015698", 0),
    ("natural", "acquisition-sonnet-yolo1024-crop1024-r0-c3", "p1bfa52a41a5e15015698", 8),
    ("random", "random40-haiku-matrix-yolo640-crop1024-r0-c3", "r838a65ca30bafa563b7e10d4", 0),
    ("random", "random40-luna-yolo1280-crop1024-r0-c3", "r536e002b19beb540f99f33e9", 0),
    ("random", "random40-luna-yolo1280-crop1024-r0-c3", "r91200ef88804e8e21a9f4c15", 0),
)
PARTIAL_NEWSPAPER_TARGET = 8
AUTHORITIES = {
    "natural": (
        "scoring-audit26-v2",
        "scoring-audit26-v1",
        "scoring-audit26-v2",
        "333ca142f623837c724276be383ac8006f8ae504ca632ec489c5ff3417bdf743",
        "da48f3a34238fe11f1a57827628b3208e7e2ce9b28893393a5c226a311e7b956",
    ),
    "random": (
        "random40-dual-score-v1",
        "random40-dual-score-v1",
        "random40-dual-score-v1",
        "79de964dfeff948b6e6ee597738001c21008c1a4bf6545e35dc0887686860abe",
        "ba780586eccd8552566b29233c6ead74ea21df45d482474e992b9d82f67b8081",
    ),
}


def quality_color(score: float) -> tuple[int, int, int]:
    """Interpolate red at zero, yellow at one half, and green at one."""
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("Quality score must be finite and between zero and one")
    red, yellow, green = (205, 46, 48), (230, 180, 25), (28, 145, 74)
    midpoint = 0.5
    start, end, fraction = (red, yellow, score * 2) if score <= midpoint else (yellow, green, (score - midpoint) * 2)
    values = [round(a + (b - a) * fraction) for a, b in zip(start, end, strict=True)]
    return values[0], values[1], values[2]


def content_f1(precision: float, recall: float) -> float:
    """Preserve separate P/R evidence; harmonic mean is a display summary only."""
    quality_color(precision)
    quality_color(recall)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def build(root: Path, output: Path) -> Path:
    """Render only five declared cases from frozen independently audited evidence."""
    import pylopdf

    root, output = guard_path(root.resolve()), guard_path(output.resolve())
    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    admitted = []
    for scope, name, identifier, index in CASES:
        audit_dir, plan_name, runtime_name, plan_sha, runtime_sha = AUTHORITIES[scope]
        plan_path, runtime_path = (
            root / "plans" / (plan_name + ".json"),
            root / "trusted-code" / (runtime_name + ".json"),
        )
        plan = read(plan_path, receipts)
        read(runtime_path, receipts)
        if receipts[str(plan_path)] != plan_sha or receipts[str(runtime_path)] != runtime_sha:
            raise ValueError("Pinned declaration or trusted runtime changed")
        entry = next(e for e in plan["entries"] if e["name"] == name)
        audit = read(root / audit_dir / (name + ".json"), receipts)
        if audit["entry"] != entry:
            raise ValueError("Audit declaration changed")
        objects: dict[str, Any] = {}
        for key in ("report", "evaluation", "frozen"):
            path = Path(entry[key])
            objects[key] = read(path, receipts)
            if receipts[str(path.resolve())] != entry[key + "_sha256"]:
                raise ValueError("Frozen run authority changed")
        target_path = Path(entry["corpus"]) / "private-targets.json"
        targets = read(target_path, receipts)
        if receipts[str(target_path)] != entry["targets_sha256"]:
            raise ValueError("Reference changed")
        reference = next(p for p in targets["pages"] if p["id"] == identifier)
        result = next(p for p in objects["report"]["results"] if p["id"] == identifier)
        evaluated = next(r for r in objects["evaluation"]["runs"] if r["name"] == name)
        strict = next(p for p in evaluated["page_scores"] if p["id"] == identifier)
        tables = result["tables"] if not strict["error"] else []
        replay = score_page(reference, tables, status=result["status"])
        if any(replay[k] != v for k, v in strict.items() if k in replay):
            raise ValueError("Strict score does not reproduce")
        page = next(p for p in audit["secondary"]["pages"] if p["id"] == identifier)
        pair = next((p for p in page["pairs"] if p["target"] == index), None)
        record = next(r for r in objects["frozen"]["records"] if r["id"] == identifier)
        pdf = guard_path(Path(record["pdf_path"]).resolve())
        receipts[str(pdf)] = digest(pdf.read_bytes())
        if receipts[str(pdf)] != record["pdf_sha256"]:
            raise ValueError("Source PDF changed")
        admitted.append((scope, name, identifier, index, reference["tables"][index], tables, pair, record, strict))
    for path in (FONT, LATIN_FONT, Path(__file__), Path(__file__).with_name("p003_visual_review.py")):
        receipts[str(path.resolve())] = digest(path.read_bytes())
    identity = digest(json.dumps(receipts, sort_keys=True).encode())
    destination = output / ("content-gradient-" + identity[:20])
    if (destination / "provenance.json").exists():
        return destination
    destination.mkdir(parents=True, exist_ok=False)
    evidence = []
    for scope, name, identifier, index, reference_table, tables, pair, record, strict in admitted:
        with pylopdf.Document(record["pdf_path"]) as document:
            source_page = document[record["page_number"]]
            scale = 2400 / source_page.rect.width
            pixmap = source_page.get_pixmap(scale=scale, background=(255, 255, 255))
            source = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples).convert("RGB")
        source.save(destination / (identifier + "-original.png"))
        actual = [tables[pair["prediction"]]] if pair else []
        if pair:
            content = pair["content"]
            if not content["supported"]:
                raise ValueError("This bounded display requires supported character evidence")
            precision, recall = content["precision"], content["recall"]
            structure_ok = pair["strict_complete"] or pair["schema"]["schema_equivalent"]
        else:
            precision, recall, structure_ok = 0.0, 0.0, False
        score = content_f1(precision, recall)
        color = quality_color(score)
        marks = {"output_cells": {0: dict.fromkeys(_cells(actual[0]), "success")}} if actual else {"output_cells": {}}
        grid = output_grid(
            actual, marks, table_indexes=[pair["prediction"]] if pair else [], palette={"success": color}
        )
        crop = source.crop(tuple(round(v * scale) for v in reference_table["bbox"]))
        zoom = min(900 / crop.width, 1400 / crop.height)
        crop = crop.resize((round(crop.width * zoom), round(crop.height * zoom)))
        grid.thumbnail((980, 1400))
        panel = Image.new("RGB", (2000, max(crop.height, grid.height) + 340), "#f5f7fa")
        draw = ImageDraw.Draw(panel)
        lines(draw, (20, 12), f"{identifier} T{index} | {name} | {scope} frozen evaluation", 1960, 22)
        lines(
            draw,
            (20, 65),
            f"Table-level CHARACTER CONTENT: P {precision:.4f}, R {recall:.4f}, "
            f"F1 {score:.4f}. Uniform content tint is NOT a cell-level verdict or physical-structure score.",
            1960,
            20,
        )
        for x in range(500):
            draw.line((20 + x, 135, 20 + x, 160), fill=quality_color(x / 499))
        lines(draw, (540, 130), "0 red: absent | 0.5 yellow: partial | 1 green: complete literal recovery", 1420, 19)
        structural_label = (
            "Accepted by pinned strict/schema policy"
            if structure_ok
            else "AMBER structural warning: "
            "schema/span acceptance not established; content recovery does not certify membership"
        )
        if identifier == "r838a65ca30bafa563b7e10d4":
            structural_label = (
                "AMBER: source-verified lost vertical merge at row1, column4, rowspan2. "
                "Literal content1 does not preserve row membership."
            )
        elif identifier == "r536e002b19beb540f99f33e9":
            structural_label = (
                "AMBER: two final source rows absent (pearl paper / pine folder). "
                "High aggregate content recovery does not make this complete."
            )
        elif not pair:
            structural_label = (
                "AMBER: no accepted table output; retained pipeline error/missing-table result. "
                "P/R/F1 zero is an explicit absence-display convention."
            )
        draw.rectangle((20, 185, 1980, 225), fill="#f5e9cd" if not structure_ok else "#e0f0e5")
        lines(draw, (28, 190), structural_label, 1940, 18)
        lines(
            draw,
            (20, 250),
            "Original strict score unchanged. Actual source pixels left; actual extracted matrix right. "
            "Whole-table source outline only; output cell boxes are schematic.",
            1960,
            18,
        )
        detail = "Character metric includes retained spaces and decoration; it is not semantic business-value quality."
        if scope == "natural" and index == PARTIAL_NEWSPAPER_TARGET:
            detail += (
                " Source review: Motor City missing; Grand Rapids values changed. "
                "Dot leaders/fraction encoding also count."
            )
        lines(draw, (20, 285), detail, 1960, 16)
        panel.paste(crop, (20, 330))
        draw.rectangle((20, 330, 20 + crop.width, 330 + crop.height), outline=color, width=4)
        panel.paste(grid, (1010, 330))
        panel.save(destination / (identifier + f"-T{index}-gradient.png"))
        evidence.append(
            {
                "id": identifier,
                "target": index,
                "run": name,
                "precision": precision,
                "recall": recall,
                "display_f1": score,
                "structure_accepted": structure_ok,
                "pair": pair,
                "strict": strict,
            }
        )
    for receipt_path, expected in receipts.items():
        if digest(Path(receipt_path).read_bytes()) != expected:
            raise ValueError("Dependency changed while rendering")
    (destination / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    (destination / "provenance.json").write_text(
        json.dumps(
            {
                "receipts": receipts,
                "settings": RENDER_SETTINGS,
                "scope": "Table-level character F1 display, not semantic or physical-cell correctness",
                "resources": {
                    "wall_seconds": time.monotonic() - started,
                    "cpu_seconds": time.process_time() - cpu,
                    "lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                },
            },
            indent=2,
        )
        + "\n"
    )
    return destination


def main() -> None:
    """Generate bounded diagnostic artifacts only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root, args.output))


if __name__ == "__main__":
    main()
