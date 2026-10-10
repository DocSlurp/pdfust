"""Offline DEV attribution of retained table misses and source-only proposal ceilings."""

# Frozen experimental dictionaries are validated at their explicit artifact boundaries.
# ruff: noqa: EM101, TRY003, PLC0415, C901
from __future__ import annotations

import argparse
import io
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.generalization_scoring import _cells
from bench.p003_report import strict_scores, verify_archive
from bench.silver import canonical, guard_path, sha, write_json

DENSE_IDS = frozenset({"p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"})
IOU_THRESHOLDS = (0.25, 0.50, 0.75)
INCLUSION_THRESHOLDS = (0.90, 0.95, 1.00)
DEFAULT_CAP = 32
SCREEN_PAGES = 16


def _read(path: Path) -> dict[str, Any]:
    return json.loads(guard_path(path).read_bytes())


def overlap(reference: list[float], proposal: list[float]) -> tuple[float, float]:
    """Return IoU and fraction of target area visible within one complete crop."""
    intersection = max(0, min(reference[2], proposal[2]) - max(reference[0], proposal[0])) * max(
        0, min(reference[3], proposal[3]) - max(reference[1], proposal[1])
    )
    a = (reference[2] - reference[0]) * (reference[3] - reference[1])
    b = (proposal[2] - proposal[0]) * (proposal[3] - proposal[1])
    if min(a, b) <= 0:
        raise ValueError("Coverage boxes must have positive area")
    return intersection / (a + b - intersection), intersection / a


def coverage(reference: list[float], proposals: list[list[float]]) -> dict[str, float]:
    """Maxima describe geometric opportunities, never model acceptance or correctness."""
    comparisons = [overlap(reference, proposal) for proposal in proposals]
    return {
        "maximum_iou": max((a for a, _b in comparisons), default=0),
        "maximum_target_inclusion": max((b for _a, b in comparisons), default=0),
    }


def proposal_boxes(page: dict[str, Any], arm: str) -> list[list[float]]:
    """Raw union retains overlapping opportunities, without selecting or joining crops."""
    yolo = [crop["viewport"] for crop in page["yolo"]]
    if arm == "yolo":
        return yolo
    fixed = "tracks_fixed2" if arm == "yolo_union_fixed2" else arm
    boxes = [proposal["bbox"] for proposal in page["arms"][fixed]["candidates"]]
    return yolo + boxes if arm == "yolo_union_fixed2" else boxes


def freeze_proposals(
    source: Path, baselines: list[Path], trusts: list[Path], output: Path, *, cap: int = DEFAULT_CAP
) -> dict[str, Any]:
    """Authenticate source evidence, derive bounded proposals, then persist before reference scoring."""
    import resource

    from PIL import Image

    import pylopdf
    from bench import p003_region_candidates as helper
    from bench.generalization_report import verify_output

    started = time.perf_counter()
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    cpu_before = usage_before.ru_utime + usage_before.ru_stime
    if output.exists():
        raise ValueError("Proposal freeze must be new; do not overwrite retained evidence")
    source_frozen, source_report = _read(source / "frozen.json"), _read(source / "report.json")
    if source_frozen["config"] != source_report["config"]:
        raise ValueError("Source configuration changed")
    verify_archive(source, source_frozen, _read(trusts[0]))
    records = source_frozen["records"]
    source_pages = {p["id"]: p for p in source_report["results"]}
    if len(records) != SCREEN_PAGES or set(source_pages) != {r["id"] for r in records}:
        raise ValueError("Source ceiling requires complete frozen natural16 inventory")
    retained_reports = []
    for directory, trust in zip(baselines, trusts[1:], strict=True):
        frozen, report = _read(directory / "frozen.json"), _read(directory / "report.json")
        if (
            frozen["records"] != records
            or frozen["manifest_sha256"] != source_frozen["manifest_sha256"]
            or frozen["config"] != report["config"]
        ):
            raise ValueError("Model/source inventories or frozen configurations differ")
        verify_archive(directory, frozen, _read(trust))
        for page in report["results"]:
            verify_output(directory, page, processor="vision_regions")
        retained_reports.append(report)
    maps = [{p["id"]: p for p in report["results"]} for report in retained_reports]
    pages = []
    for record in records:
        ident = record["id"]
        source_page = source_pages[ident]
        if not verify_output(
            source, source_page, processor="regions", source_order=source_report["config"].get("source_order", "legacy")
        )["operational"]:
            raise ValueError("Native/OCR source prerequisite failed")
        native = {key: source_page["source"][key] for key in ("page_size", "words")}
        data = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Source PDF changed")
        with pylopdf.open(stream=data) as document:
            page = document[record["page_number"]]
            pixels = page.render(scale=1536 / max(page.rect.width, page.rect.height), background=(255, 255, 255))
        with Image.open(io.BytesIO(pixels)) as rendered:
            image = rendered.convert("RGB")
        arms = {
            name: helper.propose(native, image=image, max_candidates=cap, raster_grid=grid)
            for name, grid in (("tracks_whole", 0), ("tracks_fixed2", 2))
        }
        proposed = [
            {key: crop[key] for key in ("index", "request_index", "viewport", "detector_box")}
            for crop in maps[0][ident]["transcription_regions"]
        ]
        if any(
            [
                {key: crop[key] for key in ("index", "request_index", "viewport", "detector_box")}
                for crop in mapping[ident]["transcription_regions"]
            ]
            != proposed
            for mapping in maps[1:]
        ):
            raise ValueError("Retained model proposal inventories differ")
        pages.append(
            {
                "id": ident,
                "source_sha256": sha(canonical(native)),
                "raster_sha256": sha(pixels),
                "arms": arms,
                "yolo": proposed,
            }
        )
    frozen = {
        "schema": 1,
        "source_only": True,
        "candidate_cap": cap,
        "manifest_sha256": source_frozen["manifest_sha256"],
        "records": records,
        "helper_sha256": {
            name: sha((Path(__file__).parent / name).read_bytes())
            for name in ("p003_region_candidates.py", "pipeline_regions.py", "pipeline_dense_candidates.py")
        },
        "source_report_sha256": sha((source / "report.json").read_bytes()),
        "baseline_reports": [
            {"directory": str(directory), "report_sha256": sha((directory / "report.json").read_bytes())}
            for directory in baselines
        ],
        "pages": pages,
        "proposal_generation_wall_seconds": time.perf_counter() - started,
        "resources": {
            "cpu_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_utime
            + resource.getrusage(resource.RUSAGE_SELF).ru_stime
            - cpu_before,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": (
                "Single CPU process source authentication plus proposal construction; "
                "getrusage process CPU and lifetime peak RSS; no OCR/inference/GPU"
            ),
        },
        "analysis_code_sha256": sha(Path(__file__).read_bytes()),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, frozen)
    return frozen


def attribute_page(reference: dict[str, Any], prediction: dict[str, Any], *, inclusion: float = 0.95) -> dict[str, Any]:
    """Partition strict missed anchors without attributing unrequested pixels to transcription."""
    score = strict_scores([reference], [prediction])["pages"][0]
    correct = Counter()
    if prediction["status"] == "ok":
        for pair in score["matches"]:
            gold, actual = _cells(reference["tables"][pair["target"]]), _cells(prediction["tables"][pair["prediction"]])
            correct[pair["target"]] = sum(gold[key] == actual[key] for key in gold.keys() & actual.keys())
    proposed = [crop["viewport"] for crop in prediction.get("transcription_regions", [])]
    requested = [crop["viewport"] for crop in prediction.get("transcription_regions", []) if "request" in crop]
    accepted = [crop["viewport"] for crop in prediction.get("transcription_regions", []) if crop.get("status") == "ok"]
    misses = Counter()
    tables = []
    for index, table in enumerate(reference["tables"]):
        expected = len(_cells(table))
        lost = expected - correct[index]
        possibilities = {
            name: coverage(table["bbox"], boxes)
            for name, boxes in (("proposed", proposed), ("requested", requested), ("accepted", accepted))
        }
        if prediction["status"] != "ok":
            category = "whole_page_rollback"
        elif possibilities["proposed"]["maximum_target_inclusion"] + 1e-12 < inclusion:
            category = "proposal_coverage_failure"
        elif possibilities["requested"]["maximum_target_inclusion"] + 1e-12 < inclusion:
            category = "request_admission_or_selection_failure"
        else:
            category = "accepted_crop_transcription_or_structure_failure"
        misses[category] += lost
        tables.append(
            {
                "target_index": index,
                "expected_cells": expected,
                "strict_correct_cells": correct[index],
                "strict_missed_cells": lost,
                "category": category,
                "geometry": possibilities,
            }
        )
    if sum(misses.values()) + score["strict_exact_cells"] != score["expected_cells"]:
        raise ValueError("Miss partition does not reproduce the strict denominator")
    return {
        "id": prediction["id"],
        "group": "dense2" if prediction["id"] in DENSE_IDS else "other14",
        "score": score,
        "misses": dict(misses),
        "tables": tables,
        "rollback_error": prediction.get("error") if prediction["status"] != "ok" else None,
    }


def analyze(frozen_path: Path, corpus: Path) -> dict[str, Any]:
    """Read DEV references only for offline scoring after proposal bytes have frozen."""
    from bench.generalization_report import load_corpus

    frozen = _read(frozen_path)
    manifest, targets = load_corpus(corpus)
    if sha((corpus / "manifest.json").read_bytes()) != frozen["manifest_sha256"]:
        raise ValueError("Coverage references must identify the same frozen source manifest")
    references = {p["id"]: p for p in targets["pages"]}
    summaries = []
    for baseline in frozen["baseline_reports"]:
        path = guard_path(Path(baseline["directory"]) / "report.json")
        if sha(path.read_bytes()) != baseline["report_sha256"]:
            raise ValueError("Frozen model report changed before offline attribution")
        report = _read(path)
        attributed = [attribute_page(references[p["id"]], p) for p in report["results"]]
        groups = {}
        for group in ("all16", "dense2", "other14"):
            subset = [p for p in attributed if group == "all16" or p["group"] == group]
            missed = Counter()
            for page in subset:
                missed.update(page["misses"])
            scores = {
                key: sum(page["score"][key] for page in subset)
                for key in (
                    "strict_exact_cells",
                    "expected_cells",
                    "complete_tables",
                    "expected_tables",
                    "correct_text_cells",
                    "correct_structure_cells",
                    "missing_tables",
                    "false_positive_tables",
                    "false_positive_page",
                    "error",
                )
            }
            groups[group] = {"pages": len(subset), "scores": scores, "misses": dict(missed)}
        summaries.append({"name": Path(baseline["directory"]).name, "groups": groups, "pages": attributed})
    sensitivity = []
    for arm in ("yolo", "tracks_whole", "tracks_fixed2", "yolo_union_fixed2"):
        for group in ("all16", "dense2", "other14"):
            comparisons = []
            for page in frozen["pages"]:
                if group != "all16" and ((page["id"] in DENSE_IDS) != (group == "dense2")):
                    continue
                boxes = proposal_boxes(page, arm)
                comparisons.extend(
                    {**coverage(table["bbox"], boxes), "cells": len(_cells(table))}
                    for table in references[page["id"]]["tables"]
                )
            for measure, thresholds in (
                ("maximum_iou", IOU_THRESHOLDS),
                ("maximum_target_inclusion", INCLUSION_THRESHOLDS),
            ):
                for threshold in thresholds:
                    covered = [row for row in comparisons if row[measure] + 1e-12 >= threshold]
                    sensitivity.append(
                        {
                            "arm": arm,
                            "group": group,
                            "measure": measure,
                            "threshold": threshold,
                            "covered_tables": len(covered),
                            "expected_tables": len(comparisons),
                            "anchors_in_geometrically_covered_tables": sum(row["cells"] for row in covered),
                            "expected_cells": sum(row["cells"] for row in comparisons),
                        }
                    )
    return {
        "schema": 1,
        "dev_only": True,
        "dataset_sha256": manifest["dataset_sha256"],
        "proposal_freeze_sha256": sha(frozen_path.read_bytes()),
        "candidate_cap": frozen["candidate_cap"],
        "miss_inclusion_threshold": 0.95,
        "model_attribution": summaries,
        "proposal_coverage_sensitivity": sensitivity,
        "scope": "Geometric opportunities only; no gate/transcription success inferred; distinct model-run evidence",
    }


def main() -> None:
    """Freeze source-only proposals before optional offline reference scoring."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, action="append", required=True)
    parser.add_argument(
        "--trusted-code", type=Path, action="append", required=True, help="Source snapshot first, then each baseline"
    )
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-cap", type=int, default=DEFAULT_CAP)
    args = parser.parse_args()
    if len(args.trusted_code) != len(args.baseline) + 1:
        parser.error("Require one independent source snapshot followed by each baseline snapshot")
    freeze_proposals(args.source, args.baseline, args.trusted_code, guard_path(args.freeze), cap=args.candidate_cap)
    write_json(guard_path(args.output), analyze(args.freeze, args.corpus))


if __name__ == "__main__":
    main()
