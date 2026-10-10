"""Predefined source-only detector box fusion; geometry never establishes table semantics."""

# Explicit experimental evidence/measurement dictionaries are heterogeneous.
# ruff: noqa: EM101, TRY003, PLR2004, PLC0415, C901, PLR0912
from __future__ import annotations

import argparse
import json
import math
import resource
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.pipeline_layout_detector import MAX_BOXES, _box, detector_regions
from bench.pipeline_layout_tiles import MAX_CALLS, class_nms

ARMS = ("nms", "larger_containment", "overlap_union")
THRESHOLDS = {
    "nms_iou": 0.5,
    "containment_min_area": 0.8,
    "union_iou": 0.35,
    "union_axis_overlap": 0.8,
    "union_axis_size_ratio": 0.5,
}
MAX_PAIR_COMPARISONS = 1_000_000


def _area(box: list[float]) -> float:
    return (box[2] - box[0]) * (box[3] - box[1])


def _overlap(a: list[float], b: list[float]) -> tuple[float, float]:
    return max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))


def _iou(a: list[float], b: list[float]) -> float:
    x, y = _overlap(a, b)
    intersection = x * y
    return intersection / (_area(a) + _area(b) - intersection)


def _compatible(a: list[float], b: list[float]) -> bool:
    """Require strong box overlap and one aligned, comparably sized axis projection."""
    if _iou(a, b) < THRESHOLDS["union_iou"]:
        return False
    overlap = _overlap(a, b)
    for axis in (0, 1):
        lengths = (a[axis + 2] - a[axis], b[axis + 2] - b[axis])
        if (
            overlap[axis] / min(lengths) >= THRESHOLDS["union_axis_overlap"]
            and min(lengths) / max(lengths) >= THRESHOLDS["union_axis_size_ratio"]
        ):
            return True
    return False


def fuse(boxes: list[dict[str, Any]], viewport: list[float], *, arm: str = "nms") -> dict[str, Any]:
    """Fuse a complete bounded proposal set while retaining every original member."""
    if arm not in ARMS or not isinstance(boxes, list) or len(boxes) > MAX_CALLS * MAX_BOXES:
        raise ValueError("Unknown fusion arm or raw box admission exceeded")
    page = _box(viewport)
    if not math.isfinite(_area(page)):
        raise ValueError("Full-page area must be finite")
    clean = []
    for index, box in enumerate(boxes):
        geometry = _box(box["bbox"])
        if not math.isfinite(_area(geometry)):
            raise ValueError("Detector area must be finite")
        label, confidence = box["label"], box["confidence"]
        if not isinstance(label, str) or not label or len(label) > 128 or type(confidence) not in (int, float):
            raise ValueError("Invalid fusion class or confidence")
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Invalid fusion confidence")
        if geometry[0] < page[0] or geometry[1] < page[1] or geometry[2] > page[2] or geometry[3] > page[3]:
            raise ValueError("Detector geometry extends outside full-page viewport")
        clean.append({**box, "bbox": geometry, "_raw_index": index})
    counts = Counter(box["label"].casefold() for box in clean)
    if sum(count * (count - 1) // 2 for count in counts.values()) > MAX_PAIR_COMPARISONS:
        raise ValueError("Complete fusion pair work exceeds admission")
    groups: list[tuple[dict[str, Any], list[int]]] = []
    if arm == "nms":
        selected = class_nms(clean, threshold=THRESHOLDS["nms_iou"])
        groups = [(box, []) for box in selected]
        for box in clean:
            for winner, members in groups:
                if box["_raw_index"] == winner["_raw_index"] or (
                    box["label"].casefold() == winner["label"].casefold()
                    and _iou(box["bbox"], winner["bbox"]) > THRESHOLDS["nms_iou"]
                ):
                    members.append(box["_raw_index"])
                    break
    elif arm == "larger_containment":
        ordered = sorted(clean, key=lambda box: (-_area(box["bbox"]), -box["confidence"], box["_raw_index"]))
        for box in ordered:
            for winner, members in groups:
                x, y = _overlap(box["bbox"], winner["bbox"])
                if box["label"].casefold() == winner["label"].casefold() and (
                    x * y / min(_area(box["bbox"]), _area(winner["bbox"])) >= THRESHOLDS["containment_min_area"]
                ):
                    members.append(box["_raw_index"])
                    break
            else:
                groups.append((box, [box["_raw_index"]]))
    else:
        parents = list(range(len(clean)))

        def find(index: int) -> int:
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        for index, box in enumerate(clean):
            for other_index in range(index):
                other = clean[other_index]
                if box["label"].casefold() == other["label"].casefold() and _compatible(box["bbox"], other["bbox"]):
                    first, second = find(index), find(other_index)
                    parents[max(first, second)] = min(first, second)
        components: dict[int, list[int]] = {}
        for index in range(len(clean)):
            components.setdefault(find(index), []).append(index)
        for members in components.values():
            winner = max((clean[index] for index in members), key=lambda box: (box["confidence"], -box["_raw_index"]))
            geometry = [
                min(clean[index]["bbox"][0] for index in members),
                min(clean[index]["bbox"][1] for index in members),
                max(clean[index]["bbox"][2] for index in members),
                max(clean[index]["bbox"][3] for index in members),
            ]
            groups.append(({**winner, "bbox": geometry}, members))
    if len(groups) > MAX_BOXES:
        raise ValueError("Complete fused box count exceeds admission")
    selected = []
    for ordinal, (winner, members) in enumerate(groups):
        original = [deepcopy(boxes[index]) for index in sorted(members)]
        call_ids = sorted({str(member.get("call_id", "whole")) for member in original})
        boundary = any(member.get("tile_boundary_risk", False) for member in original)
        selected.append(
            {
                "label": winner["label"],
                "confidence": max(member["confidence"] for member in original),
                "confidence_scope": "Maximum original member confidence; not fused-box semantic confidence",
                "bbox": winner["bbox"],
                "fusion_id": f"f{ordinal:04d}",
                "member_ids": [f"b{index:05d}" for index in sorted(members)],
                "members": original,
                "call_ids": call_ids,
                "detector_partial_context": any(call != "whole" for call in call_ids),
                "detector_full_page_member": "whole" in call_ids,
                "cross_tile_boundary_risk": boundary,
                "context_scope": (
                    "Full source within proposal bbox is available; physical table completeness is unknown"
                ),
                "semantic_status": "proposal_only",
                "fusion_arm": arm,
                "warnings": [
                    text
                    for condition, text in (
                        (len(call_ids) > 1, "Members come from multiple detector crops"),
                        (boundary, "Original member touches an interior tile boundary"),
                        (len(members) > 1, "Combined evidence may include multiple semantic objects"),
                    )
                    if condition
                ],
            }
        )
    return {
        "arm": arm,
        "thresholds": dict(THRESHOLDS),
        "raw_boxes": deepcopy(boxes),
        "boxes": selected,
        "full_page_viewport": page,
        "semantic_status": "Source-only geometry proposals, not table labels or topology",
    }


def fusion_regions(
    page: dict[str, Any], evidence: dict[str, Any], *, max_words: int = 256, max_characters: int = 16000
) -> dict[str, Any]:
    """Partition full-page source once; distinguish source context from detector crop risk."""
    plan = detector_regions(page, evidence["boxes"], max_words=max_words, max_characters=max_characters)
    for region in plan["regions"]:
        if "detector" not in region:
            continue
        proposal = evidence["boxes"][region["detector"]["index"]]
        region["detector"].update(
            {
                key: deepcopy(proposal[key])
                for key in (
                    "fusion_id",
                    "fusion_arm",
                    "member_ids",
                    "call_ids",
                    "cross_tile_boundary_risk",
                    "detector_partial_context",
                    "detector_full_page_member",
                    "warnings",
                    "context_scope",
                )
            }
        )
        region["detector"]["source_context_complete"] = region["context_complete"]
        region["detector"]["physical_table_completeness"] = "unknown"
    return plan


def benchmark(manifest_path: Path, sources_directory: Path, tiles_directory: Path, output: Path) -> dict[str, Any]:
    """Compare three frozen source-only arms on every page; no references or inference."""
    from bench.silver import guard_path, sha, write_json

    began, cpu = time.perf_counter(), time.process_time()
    manifest = json.loads(guard_path(manifest_path).read_bytes())
    if manifest.get("split") != "DEV":
        raise ValueError("Fusion diagnostic requires explicit DEV sources")
    manifest_digest = sha(manifest_path.read_bytes())
    tile_report = json.loads(guard_path(tiles_directory / "report.json").read_bytes())
    if tile_report["manifest_sha256"] != manifest_digest:
        raise ValueError("Retained detector manifest differs from fixed screen")
    source_frozen = json.loads(guard_path(sources_directory / "frozen.json").read_bytes())
    source_records = {row["id"]: row for row in source_frozen["records"]}
    fields = ("id", "pdf_path", "pdf_sha256", "page_number")
    if any(
        {key: source_records.get(row["id"], {}).get(key) for key in fields} != {key: row[key] for key in fields}
        for row in manifest["pages"]
    ):
        raise ValueError("Cached source records differ from fixed screen")
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for record in manifest["pages"]:
        source_file = guard_path(sources_directory / f"{record['id']}-result.json")
        tile_file = guard_path(tiles_directory / f"{record['id']}-tiles.json")
        cached, tiles = json.loads(source_file.read_bytes()), json.loads(tile_file.read_bytes())
        if cached["id"] != record["id"] or tiles["id"] != record["id"] or tiles["status"] != "ok":
            raise ValueError("Frozen retained source or tiles do not match page")
        source = cached["source"]
        size = source["page_size"]
        viewport = [0, 0, *size] if len(size) == 2 else size
        for calls in ("whole_2x2", "whole_2x2_3x3"):
            raw = [
                box
                for call in tiles["detection"]["calls"]
                if calls != "whole_2x2" or not call["call_id"].startswith("g3-")
                for box in call["boxes"]
            ]
            for arm in ARMS:
                fusion = fuse(raw, viewport, arm=arm)
                for budget in (256, 1024):
                    plan = fusion_regions(source, fusion, max_words=budget)
                    regions = [region for region in plan["regions"] if "detector" in region]
                    row = {
                        "id": record["id"],
                        "calls": calls,
                        "arm": arm,
                        "word_budget": budget,
                        "raw_boxes": len(raw),
                        "fused_boxes": len(fusion["boxes"]),
                        "table_proposals": sum(box["label"].casefold() == "table" for box in fusion["boxes"]),
                        "source_words": len(source["words"]),
                        "owned_words": sum(len(region["source_ids"]) for region in regions),
                        "detector_regions": len(regions),
                        "residual_regions": sum(region["kind"] == "residual" for region in plan["regions"]),
                        "boundary_risk_regions": sum(
                            region["detector"]["cross_tile_boundary_risk"] for region in regions
                        ),
                        "capacity_regions": sum(not region["context_complete"] for region in regions),
                        "empty_table_proposals": plan["detector_diagnostics"]["empty_table_proposals"],
                        "overlapping_word_candidates": plan["detector_diagnostics"]["overlapping_word_candidates"],
                        "source_file_sha256": sha(source_file.read_bytes()),
                        "tiles_file_sha256": sha(tile_file.read_bytes()),
                    }
                    rows.append(row)
                    write_json(
                        output / f"{record['id']}-{calls}-{arm}-w{budget}.json",
                        {
                            "summary": row,
                            "fusion": fusion,
                            "partition": {k: v for k, v in plan.items() if k != "words"},
                        },
                    )
    report = {
        "source_only": True,
        "arms": list(ARMS),
        "thresholds": dict(THRESHOLDS),
        "rows": rows,
        "manifest_sha256": manifest_digest,
        "code_sha256": {
            name: sha((Path(__file__).parent / name).read_bytes())
            for name in ("pipeline_layout_fusion.py", "pipeline_layout_detector.py", "pipeline_layout_tiles.py")
        },
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Own-process CPU process_time; Linux getrusage lifetime peak RSS, no RSS sampling",
        },
        "scope": (
            "Fusion/partition and retained output serialization; cached OCR/detector costs excluded; "
            "no model quality claim"
        ),
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run the fixed-arm local retained-source diagnostic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sources-directory", type=Path, required=True)
    parser.add_argument("--tiles-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    benchmark(args.manifest, args.sources_directory, args.tiles_directory, args.output)


if __name__ == "__main__":
    main()
