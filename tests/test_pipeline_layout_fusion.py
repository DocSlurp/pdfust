"""Source-only proposal fusion preserves evidence, ownership, and boundary uncertainty."""

from collections import Counter
from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_layout_fusion import ARMS, fuse, fusion_regions
from bench.pipeline_layout_tiles import class_nms


def box(
    bbox: list[float], confidence: float, *, label: str = "Table", call: str = "whole", edge: bool = False
) -> dict[str, Any]:
    return {
        "bbox": bbox,
        "confidence": confidence,
        "label": label,
        "call_id": call,
        "tile_viewport": [0, 0, 100, 100],
        "tile_boundary_risk": edge,
    }


def source() -> dict[str, Any]:
    return {
        "page_size": [100, 100],
        "vector_candidates": [],
        "words": [
            {"id": "global0", "text": "A", "bbox": [10, 10, 20, 20]},
            {"id": "global1", "text": "B", "bbox": [60, 60, 70, 70]},
            {"id": "global2", "text": "prose", "bbox": [5, 90, 30, 99]},
        ],
    }


@pytest.mark.parametrize("arm", ARMS)
def test_every_raw_member_preserved_with_deterministic_ids_and_exact_partition(arm: str) -> None:
    raw = [box([0, 0, 80, 80], 0.4), box([5, 5, 40, 40], 0.95, call="g2-t0", edge=True)]
    before = deepcopy(raw)
    evidence = fuse(raw, [0, 0, 100, 100], arm=arm)
    assert raw == before
    assert evidence["raw_boxes"] == raw
    assert evidence == fuse(raw, [0, 0, 100, 100], arm=arm)
    members = [i for proposal in evidence["boxes"] for i in proposal["member_ids"]]
    assert Counter(members) == Counter(["b00000", "b00001"])
    plan = fusion_regions(source(), evidence)
    assert Counter(i for region in plan["regions"] for i in region["source_ids"]) == Counter(
        ["global0", "global1", "global2"]
    )
    assert all(
        region["detector"]["physical_table_completeness"] == "unknown"
        for region in plan["regions"]
        if "detector" in region
    )


def test_larger_context_prevents_contained_confident_fragment_stealing_words() -> None:
    raw = [box([0, 0, 80, 80], 0.4), box([5, 5, 40, 40], 0.95, call="g2-t0", edge=True)]
    baseline = fuse(raw, [0, 0, 100, 100], arm="nms")
    assert len(baseline["boxes"]) == 2
    larger = fuse(raw, [0, 0, 100, 100], arm="larger_containment")
    assert len(larger["boxes"]) == 1
    assert larger["boxes"][0]["bbox"] == [0, 0, 80, 80]
    assert larger["boxes"][0]["confidence"] == 0.95
    plan = fusion_regions(source(), larger)
    proposed = next(region for region in plan["regions"] if "detector" in region)
    assert proposed["source_ids"] == ["global0", "global1"]
    assert proposed["context_complete"]
    assert proposed["detector"]["source_context_complete"]
    assert proposed["detector"]["cross_tile_boundary_risk"]
    assert proposed["detector"]["detector_partial_context"]


def test_union_uses_compatible_overlaps_without_joining_classes_or_disjoint_boxes() -> None:
    raw = [
        box([0, 0, 60, 60], 0.8),
        box([0, 20, 60, 80], 0.9, call="g2-t2", edge=True),
        box([80, 80, 100, 100], 0.7),
        box([0, 0, 60, 60], 0.99, label="Picture"),
    ]
    evidence = fuse(raw, [0, 0, 100, 100], arm="overlap_union")
    assert len(evidence["boxes"]) == 3
    assert evidence["boxes"][0]["bbox"] == [0, 0, 60, 80]
    assert len(evidence["boxes"][0]["members"]) == 2
    assert evidence["boxes"][0]["cross_tile_boundary_risk"]
    assert [proposal["label"] for proposal in evidence["boxes"]] == ["Table", "Table", "Picture"]


def test_baseline_nms_geometry_and_priority_match_existing_implementation() -> None:
    raw = [box([0, 0, 60, 60], 0.8), box([0, 10, 60, 70], 0.9), box([70, 70, 100, 100], 0.7)]
    expected = class_nms(raw)
    actual = fuse(raw, [0, 0, 100, 100], arm="nms")["boxes"]
    assert [(b["bbox"], b["confidence"]) for b in actual] == [(b["bbox"], b["confidence"]) for b in expected]


def test_capacity_cuts_still_abstain_even_when_full_source_is_available() -> None:
    evidence = fuse([box([0, 0, 80, 80], 0.9)], [0, 0, 100, 100], arm="larger_containment")
    plan = fusion_regions(source(), evidence, max_words=1)
    proposed = [region for region in plan["regions"] if "detector" in region]
    assert len(proposed) == 2
    assert all(not region["context_complete"] for region in proposed)
    assert all(not region["detector"]["source_context_complete"] for region in proposed)


def test_invalid_page_geometry_and_unbounded_pair_work_refuse_complete_fusion() -> None:
    with pytest.raises(ValueError, match="outside full-page"):
        fuse([box([0, 0, 101, 100], 0.9)], [0, 0, 100, 100])
    with pytest.raises(ValueError, match="confidence"):
        fuse([box([0, 0, 100, 100], float("nan"))], [0, 0, 100, 100])
    with pytest.raises(ValueError, match="pair work"):
        fuse([box([0, 0, 100, 100], 0.9) for _ in range(1500)], [0, 0, 100, 100])
    with pytest.raises(ValueError, match="Unknown"):
        fuse([], [0, 0, 100, 100], arm="unregistered")
