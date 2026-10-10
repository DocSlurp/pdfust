"""Independent offline replay and DEV scoring of frozen source-owned geometry placements."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.generalization_report import load_corpus
from bench.p003_gate_run import authenticate
from bench.p003_report import strict_scores
from bench.silver import guard_path, sha, write_json

SOURCE_MANIFEST_SHA256 = "416da241084e8685600a75ff4fa4bab62fdc1d5d5953da0fe612282c567ac0a8"
GEOMETRY_REPORT_SHA256 = "55c44a6c4e2e0f99233e1704fd12436db5ec723ed06aa57a4747f511a99bedac"


def read(path: Path) -> dict[str, Any]:
    """Read a guarded explicit JSON artifact."""
    return json.loads(guard_path(path).read_bytes())


def placement_inventory(
    report: dict[str, Any], ids: list[str], thresholds: list[float], policies: list[str]
) -> dict[tuple[str, float, str], dict[str, Any]]:
    """Require every predeclared treatment on every page, including empty outputs."""
    expected = {
        (identifier, threshold, policy) for identifier in ids for threshold in thresholds for policy in policies
    }
    rows = {(row["id"], row["threshold"], row["policy"]): row for row in report["rows"]}
    if len(rows) != len(report["rows"]) or set(rows) != expected:
        raise ValueError("Incomplete or duplicate frozen placement inventory")
    return rows


def verify_placements(
    directory: Path,
    geometry_directory: Path,
    baseline_trusted_code: dict[str, str],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Replay source ownership, all raw geometry projections and complete frozen placements."""
    from bench import p003_structure_geometry as geometry
    from bench import p003_structure_place as placement

    directory, geometry_directory = guard_path(directory), guard_path(geometry_directory)
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    helper_name = "p003_structure_place.py"
    if "p003_structure_qualifiers.py" in frozen["code_sha256"]:
        from bench import p003_structure_qualifiers as placement

        helper_name = "p003_structure_qualifiers.py"
    required = {helper_name, "p003_structure_geometry.py", "pipeline_assembly.py", "pipeline_repair.py"}
    if set(frozen["code_sha256"]) != required:
        raise ValueError("Incomplete trusted placement helper inventory")
    for name, digest in frozen["code_sha256"].items():
        if sha(Path(__file__).with_name(name).read_bytes()) != digest:
            raise ValueError("Frozen placement helper differs from trusted working source")
    source_path = geometry_directory / "source/manifest.json"
    geometry_path = geometry_directory / "geometry/report.json"
    if (
        sha(source_path.read_bytes()) != SOURCE_MANIFEST_SHA256
        or sha(geometry_path.read_bytes()) != GEOMETRY_REPORT_SHA256
    ):
        raise ValueError("Independently announced source geometry freeze changed")
    if (
        frozen["source_manifest_sha256"] != SOURCE_MANIFEST_SHA256
        or frozen["geometry_report_sha256"] != GEOMETRY_REPORT_SHA256
    ):
        raise ValueError("Placement names different source geometry evidence")
    manifest, raw_report = read(source_path), read(geometry_path)
    baseline = guard_path(Path(manifest["baseline"]))
    original_frozen, _ = authenticate(baseline, baseline_trusted_code)
    ids = [page["id"] for page in manifest["pages"]]
    if ids != [page["id"] for page in original_frozen["records"]] or ids != [
        page["id"] for page in raw_report["pages"]
    ]:
        raise ValueError("Source geometry inventory differs from independently authenticated baseline")
    if frozen["thresholds"] != list(geometry.THRESHOLDS) or frozen["policies"] != list(placement.POLICIES):
        raise ValueError("Frozen placement treatment inventory differs")
    rows = placement_inventory(report, ids, frozen["thresholds"], frozen["policies"])
    treatments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page, measured in zip(manifest["pages"], raw_report["pages"], strict=True):
        source_file = geometry_directory / "source" / page["source_path"]
        if sha(source_file.read_bytes()) != page["source_sha256"]:
            raise ValueError("Frozen extracted source changed")
        source = read(source_file)
        original_path = baseline / (page["id"] + "-result.json")
        if sha(original_path.read_bytes()) != page["baseline_result_sha256"] or read(original_path)["source"] != source:
            raise ValueError("Source geometry extraction differs from authenticated original")
        if len(page["crops"]) != len(measured["crops"]):
            raise ValueError("Incomplete raw crop geometry")
        candidates: dict[float, list[dict[str, Any]]] = {threshold: [] for threshold in geometry.THRESHOLDS}
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            path = geometry_directory / "geometry" / receipt["path"]
            if sha(path.read_bytes()) != receipt["sha256"]:
                raise ValueError("Frozen raw geometry receipt changed")
            prediction = read(path)
            if prediction["crop"] != crop or len(prediction["views"]) != len(geometry.THRESHOLDS):
                raise ValueError("Raw structure crop provenance differs")
            for threshold, view in zip(geometry.THRESHOLDS, prediction["views"], strict=True):
                projected = geometry.project(prediction["queries"], crop["bbox"], raw_report["labels"], threshold)
                projected["topology"] = geometry.topology(projected)
                if view != projected:
                    raise ValueError("Retained structure geometry differs from raw-query projection")
                candidates[threshold].append(
                    {
                        "region_id": crop["region_id"],
                        "source_ids": crop["source_ids"],
                        "topology": projected["topology"],
                    }
                )
        for threshold, shapes in candidates.items():
            for policy in placement.POLICIES:
                row = rows[(page["id"], threshold, policy)]
                path = directory / row["path"]
                if sha(path.read_bytes()) != row["sha256"]:
                    raise ValueError("Frozen placement output changed")
                actual = read(path)
                rebuilt = {
                    "id": page["id"],
                    "source": source,
                    "threshold": threshold,
                    **placement.place(source, shapes, policy),
                }
                if actual != rebuilt:
                    raise ValueError("Source-owned placement differs from deterministic replay")
                treatments[f"t{threshold}-{policy}"].append(
                    {"id": page["id"], "status": "ok", "tables": actual["state"]["tables"]}
                )
    return report, dict(treatments)


def analyze(directory: Path, geometry_directory: Path, corpus: Path, trusted_code: dict[str, str]) -> dict[str, Any]:
    """Load scoring references only after every frozen treatment passes source-only replay."""
    report, predictions = verify_placements(directory, geometry_directory, trusted_code)
    manifest, targets = load_corpus(corpus)
    intended = {page["id"] for page in manifest["pages"]}
    if any({page["id"] for page in pages} != intended for pages in predictions.values()):
        raise ValueError("Scoring corpus differs from complete source-frozen cohort")
    return {
        "scope": "Source-only CPU geometry placements, conditional on frozen ordinal detector crops",
        "new_api_calls": 0,
        "generated_fallback_tables": 0,
        "original_ocr_detection_and_generation_cost": "retained separately; excluded from placement resources",
        "report_sha256": sha((directory / "report.json").read_bytes()),
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "geometry_report_sha256": GEOMETRY_REPORT_SHA256,
        "resources": report["resources"],
        "treatments": {name: strict_scores(targets["pages"], pages) for name, pages in predictions.items()},
    }


def main() -> None:
    """Verify and score explicitly named frozen CPU placement artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--geometry-directory", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--baseline-trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.directory, args.geometry_directory, args.corpus, read(args.baseline_trusted_code))
    write_json(guard_path(args.output), result)
    for name, quality in result["treatments"].items():
        print(name, quality["totals"]["strict_exact_cells"], quality["totals"]["complete_tables"])


if __name__ == "__main__":
    main()
