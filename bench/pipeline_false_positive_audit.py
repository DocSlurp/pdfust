"""Offline source observations for every fixed page; no classification or tuning."""

# Heterogeneous retained experiment dictionaries and bounded JSON observations.
# ruff: noqa: EM101, TRY003, PLC0415, PLR2004
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import defaultdict
from itertools import pairwise
from pathlib import Path
from statistics import mean, median, pstdev
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

from bench.silver import guard_path, sha, write_json

FEATURE_SPEC = {
    "version": 1,
    "row_bins": "round((word vertical center - page top)/(median positive word height*0.5))",
    "x_occupancy": "8 equal page-width bins, word center; per source row bin",
    "sentence_terminal": "word final character in .!?。！？",
    "numeric_word": "at least one digit; all remaining characters in +-.,%:/()",
    "scope": "All complete source words and detector Table boxes; never prediction text or reference cell content",
    "purpose": "Descriptive features only; no fitted thresholds, gate, confidence, or prompt selection",
}


def _cv(values: Sequence[float]) -> float | None:
    return pstdev(values) / mean(values) if values and mean(values) > 0 else None


def source_features(source: dict[str, Any] | None, detection: dict[str, Any] | None) -> dict[str, Any]:
    """Compute identical predeclared observations without outcome or case metadata."""
    from bench.generalization_run import sanitize_vectors
    from bench.pipeline_regions import _source

    if source is None:
        return {"source_available": False}
    clean = _source(source)
    words = clean["words"]
    size = clean["page_size"]
    page = [0, 0, *size] if len(size) == 2 else size
    width, height = page[2] - page[0], page[3] - page[1]
    heights = [w["bbox"][3] - w["bbox"][1] for w in words if w["bbox"][3] > w["bbox"][1]]
    unit = median(heights) if heights else None
    rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    lines: dict[str, list[str]] = defaultdict(list)
    for original, word in zip(source["words"], words, strict=True):
        if unit:
            rows[round(((word["bbox"][1] + word["bbox"][3]) / 2 - page[1]) / (unit * 0.5))].append(word)
        if "line" in original:
            lines[json.dumps(original["line"], sort_keys=True)].append(word["text"])
    occupancies: list[int] = []
    gaps: list[float] = []
    for row in rows.values():
        occupancies.append(
            len({min(7, max(0, int(((w["bbox"][0] + w["bbox"][2]) / 2 - page[0]) / width * 8))) for w in row})
        )
        ordered = sorted(row, key=lambda word: word["bbox"][0])
        gaps.extend((b["bbox"][0] - a["bbox"][2]) / unit for a, b in pairwise(ordered) if b["bbox"][0] > a["bbox"][2])
    centers = sorted(median((w["bbox"][1] + w["bbox"][3]) / 2 for w in row) for row in rows.values())
    row_gaps = [(b - a) / unit for a, b in pairwise(centers)] if unit else []
    vectors, warnings = sanitize_vectors(source)
    tables = [box for box in (detection or {}).get("boxes", []) if box.get("label") == "Table"]
    areas = [(b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1]) / (width * height) for b in tables]
    aspects = [
        (b["bbox"][2] - b["bbox"][0]) / (b["bbox"][3] - b["bbox"][1]) for b in tables if b["bbox"][3] > b["bbox"][1]
    ]
    count = len(words)
    return {
        "source_available": True,
        "words": count,
        "characters": sum(len(w["text"]) for w in words),
        "median_word_characters": median([len(w["text"]) for w in words]) if words else None,
        "sentence_terminal_fraction": sum(bool(w["text"]) and w["text"][-1] in ".!?。！？" for w in words) / count
        if count
        else None,
        "numeric_word_fraction": sum(
            any(c.isdigit() for c in w["text"]) and all(c.isdigit() or c in "+-.,%:/()" for c in w["text"])
            for w in words
        )
        / count
        if count
        else None,
        "source_line_id_count": len(lines),
        "median_line_words": median([len(line) for line in lines.values()]) if lines else None,
        "median_line_characters": median([sum(map(len, line)) for line in lines.values()]) if lines else None,
        "median_word_height": unit,
        "row_bin_count": len(rows),
        "row_gap_cv": _cv(row_gaps),
        "positive_horizontal_gap_cv": _cv(gaps),
        "median_row_x_occupancy": median(occupancies) if occupancies else None,
        "row_x_occupancy_cv": _cv(occupancies),
        "raw_native_grids": len(source.get("vector_candidates", [])),
        "valid_native_grids": len(vectors["vector_candidates"]),
        "quarantined_native_grids": len(warnings),
        "detector_available": detection is not None,
        "detector_table_boxes": len(tables) if detection is not None else None,
        "detector_median_area_fraction": median(areas) if areas else None,
        "detector_max_area_fraction": max(areas) if areas else None,
        "detector_median_aspect_ratio": median(aspects) if aspects else None,
        "detector_median_confidence": median([b["confidence"] for b in tables]) if tables else None,
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = {key for row in rows for key in row["features"]}
    result: dict[str, Any] = {
        "pages": len(rows),
        "source_available_pages": sum(row["features"]["source_available"] for row in rows),
    }
    for key in sorted(keys):
        values = sorted(row["features"][key] for row in rows if type(row["features"].get(key)) in (int, float))
        if values:
            result[key] = {
                "observed_pages": len(values),
                "median": median(values),
                "minimum": min(values),
                "maximum": max(values),
            }
    return result


def audit(run: Path, manifest_path: Path, evaluation_path: Path, output: Path) -> dict[str, Any]:
    """Audit all manifest pages, retaining negatives and positive family comparisons."""
    began, cpu = time.perf_counter(), time.process_time()
    manifest = json.loads(guard_path(manifest_path).read_bytes())
    evaluation = json.loads(guard_path(evaluation_path).read_bytes())
    if manifest.get("split") != "DEV" or evaluation.get("dataset_sha256") != manifest.get("dataset_sha256"):
        raise ValueError("Audit requires matching frozen DEV manifest and verified evaluation")
    scores = {page["id"]: page for page in evaluation["page_scores"]}
    records = manifest["pages"]
    if set(scores) != {row["id"] for row in records}:
        raise ValueError("Complete all-page outcomes are required; no selected subset")
    rows = []
    hashes = {}
    for record in records:
        path = guard_path(run / f"{record['id']}-result.json")
        payload = path.read_bytes()
        retained = json.loads(payload)
        if retained["id"] != record["id"]:
            raise ValueError("Retained source result ID mismatch")
        hashes[record["id"]] = sha(payload)
        # Feature extraction receives neither score nor family and observes all pages first.
        features = source_features(retained.get("source"), retained.get("layout_detector"))
        rows.append(
            {
                "id": record["id"],
                "cohort": record["cohort"],
                "family": record["family"],
                "status": retained["status"],
                "features": features,
            }
        )
    for row in rows:
        score = scores[row["id"]]
        row["negative"] = score.get("negative_page", False)
        row["positive"] = score.get("positive_page", False)
        row["false_positive"] = score.get("false_positive_page", False)
        row["detected_tables"] = score.get("detected_tables")
        row["false_positive_tables"] = score.get("false_positive_tables")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        label = "negative" if row["negative"] else "positive" if row["positive"] else "unscored"
        groups[f"{label}/{row['family']}"].append(row)
    result = {
        "feature_spec": FEATURE_SPEC,
        "run": str(run),
        "manifest_sha256": sha(manifest_path.read_bytes()),
        "evaluation_sha256": sha(evaluation_path.read_bytes()),
        "input_result_sha256": hashes,
        "pages": rows,
        "groups": {key: _aggregate(value) for key, value in sorted(groups.items())},
        "metrics": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": "single CPU Python process, no subprocesses; "
            "Linux getrusage high-water RSS; utilization unsampled",
        },
    }
    write_json(output, result)
    return result


def main() -> None:
    """Accept only explicit artifact inputs; never discover benchmark directories."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.manifest, args.evaluation, args.output)
    print(json.dumps({"pages": len(result["pages"]), "metrics": result["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
