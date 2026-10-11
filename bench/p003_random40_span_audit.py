"""Bounded source review of three content-preserved Haiku DEV structural differences."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from PIL import Image, ImageDraw

from bench.p003_report import _cells
from bench.p003_visual_review import FONT, LATIN_FONT, digest, lines, output_grid, read
from bench.silver import guard_path

NAME = "random40-haiku-matrix-yolo640-crop1024-r0-c3"
CASES = {
    "r91200ef88804e8e21a9f4c15": "Actual source has four columns. Prediction adds a wholly empty fifth column: "
    "21 extra blank slots. No observed body-token loss; no physical evidence for that added column.",
    "r51d78e79b8eaa0ebb788d94b": "Source has one right-aligned Amount column. Prediction splits it into a blank "
    "subcolumn and a value subcolumn under a two-column Amount header. Values remain associated; "
    "the extra physical division is unsupported by source pixels.",
    "r838a65ca30bafa563b7e10d4": "Source Description cell 'coral amber' visibly spans body rows 1 and 2: "
    "the row boundary is absent there. Prediction loses that span and gives row 2 an independent blank. "
    "Literal content survives, but merged-cell membership is wrong.",
}
PLAN_SHA = "79de964dfeff948b6e6ee597738001c21008c1a4bf6545e35dc0887686860abe"


def build(root: Path, base: Path, output: Path) -> Path:
    """Preserve actual source/output and display declared span evidence without relabeling."""
    root, base, output = (guard_path(p.resolve()) for p in (root, base, output))
    started, cpu = time.monotonic(), time.process_time()
    receipts: dict[str, str] = {}
    plan_path = root / "plans/random40-dual-score-v1.json"
    plan = read(plan_path, receipts)
    if receipts[str(plan_path.resolve())] != PLAN_SHA:
        raise ValueError("Authorized plan changed")
    runtime_path = root / "trusted-code/random40-dual-score-v1.json"
    read(runtime_path, receipts)
    if receipts[str(runtime_path.resolve())] != "ba780586eccd8552566b29233c6ead74ea21df45d482474e992b9d82f67b8081":
        raise ValueError("Trusted runtime receipt changed")
    entry = next(e for e in plan["entries"] if e["name"] == NAME)
    audit = read(root / "random40-dual-score-v1" / (NAME + ".json"), receipts)
    if audit["entry"] != entry:
        raise ValueError("Audit declaration differs")
    authorities = {}
    for key in ("report", "evaluation", "frozen"):
        authorities[key] = read(Path(entry[key]), receipts)
        if receipts[str(Path(entry[key]).resolve())] != entry[key + "_sha256"]:
            raise ValueError("Frozen authority changed")
    targets_path = Path(entry["corpus"]) / "private-targets.json"
    targets = read(targets_path, receipts)
    if receipts[str(targets_path.resolve())] != entry["targets_sha256"]:
        raise ValueError("Frozen reference changed")
    provenance = read(base / "provenance.json", receipts)
    for path in (FONT, LATIN_FONT, Path(__file__), Path(__file__).with_name("p003_visual_review.py")):
        receipts[str(path.resolve())] = digest(path.read_bytes())
    cases = []
    for identifier, observation in CASES.items():
        reference = next(p for p in targets["pages"] if p["id"] == identifier)["tables"][0]
        actual = next(p for p in authorities["report"]["results"] if p["id"] == identifier)["tables"][0]
        pair = next(p for p in audit["secondary"]["pages"] if p["id"] == identifier)["pairs"][0]
        if pair["content"]["recall"] != 1 or pair["content"]["precision"] != 1:
            raise ValueError("Requested full-content case changed")
        original = base / identifier / "original.png"
        receipts[str(original.resolve())] = digest(original.read_bytes())
        cases.append((identifier, observation, reference, actual, pair, original))
    identity = digest(json.dumps(receipts, sort_keys=True).encode())
    destination = output / ("random40-span-" + identity[:20])
    if (destination / "provenance.json").exists():
        return destination
    destination.mkdir(parents=True, exist_ok=False)
    evidence = []
    for identifier, observation, reference, actual, pair, original in cases:
        panel = Image.new("RGB", (2000, 1450), "#f5f7fa")
        draw = ImageDraw.Draw(panel)
        lines(draw, (20, 15), identifier + " | Haiku matrix detector 640, crop 1024 | authored DEV", 1960, 23)
        lines(draw, (20, 60), "AMBER: qualitative structural source audit. Content P/R 1/1 does not certify "
              "physical spans. Original strict scores and gold remain unchanged.", 1960, 20)
        lines(draw, (20, 118), observation, 1960, 20)
        with Image.open(original) as image:
            source = image.convert("RGB")
        record = next(r for r in authorities["frozen"]["records"] if r["id"] == identifier)
        pdf = Path(record["pdf_path"])
        receipts[str(pdf.resolve())] = digest(pdf.read_bytes())
        if receipts[str(pdf.resolve())] != record["pdf_sha256"]:
            raise ValueError("Frozen source PDF changed")
        # The retained source page and reference bbox use display coordinates; no invented cell boxes.
        import pylopdf
        with pylopdf.Document(record["pdf_path"]) as document:
            scale = source.width / document[record["page_number"]].rect.width
        crop = source.crop(tuple(round(v * scale) for v in reference["bbox"]))
        crop.thumbnail((630, 1100))
        witness = {"gold": [x for x in reference["spans"] if x["row_span"] > 1 or x["column_span"] > 1],
                   "actual": [x for x in actual["spans"] if x["row_span"] > 1 or x["column_span"] > 1]}
        lines(draw, (20, 215), "Declared merged spans (zero-based anchors): " + json.dumps(witness), 1960, 17)
        panel.paste(crop, (20, 350))
        for x, table, title in ((680, reference, "Frozen gold matrix / declared spans"),
                                (1340, actual, "Actual output matrix / declared spans")):
            lines(draw, (x, 290), title, 640, 18)
            grid = output_grid([table], {"output_cells": {0: dict.fromkeys(_cells(table), "unscored")}})
            grid.thumbnail((640, 1100))
            panel.paste(grid, (x, 350))
        panel.save(destination / (identifier + "-span-audit.png"))
        source.save(destination / (identifier + "-original.png"))
        evidence.append({"id": identifier, "observation": observation, "gold": reference,
                         "actual": actual, "secondary_pair": pair,
                         "scope": "Qualitative source audit, not automatic schema acceptance"})
    for receipt_path, expected in receipts.items():
        if digest(Path(receipt_path).read_bytes()) != expected:
            raise ValueError("Dependency changed during rendering")
    (destination / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    (destination / "provenance.json").write_text(json.dumps({"receipts": receipts, "base": provenance,
        "resources": {"wall_seconds": time.monotonic() - started, "cpu_seconds": time.process_time() - cpu,
                      "lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                      "scope": "Single CPU diagnostic process, lifetime RSS"}}, indent=2) + "\n")
    return destination


def main() -> None:
    """Render this explicit bounded source audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("root", "base", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = parser.parse_args()
    print(build(args.root, args.base, args.output))


if __name__ == "__main__":
    main()
