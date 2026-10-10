"""Geometric attribution distinguishes pixels, localization and strict atomic outcomes."""

from __future__ import annotations

from typing import Any

import pytest
from bench.p003_failure_analysis import attribute_page, color_boxes, coverage, overlap, proposal_boxes


def table(value: str = "A") -> dict[str, Any]:
    return {"bbox": [10, 10, 20, 20], "row_count": 1, "col_count": 1, "values": [[value]], "spans": []}


def test_whole_page_covers_pixels_without_localizing_table() -> None:
    result = coverage([10, 10, 20, 20], [[0, 0, 100, 100]])
    assert result["maximum_target_inclusion"] == 1
    assert result["maximum_iou"] == pytest.approx(0.01)
    assert overlap([10, 10, 20, 20], [50, 50, 60, 60]) == (0, 0)


def test_raw_union_preserves_overlaps_without_joining_partial_crops() -> None:
    page = {
        "yolo": [{"viewport": [0, 0, 5, 10]}],
        "arms": {"tracks_fixed2": {"candidates": [{"bbox": [5, 0, 10, 10]}]}},
    }
    boxes = proposal_boxes(page, "yolo_union_fixed2")
    assert boxes == [[0, 0, 5, 10], [5, 0, 10, 10]]
    assert coverage([0, 0, 10, 10], boxes)["maximum_target_inclusion"] == 0.5


def test_color_pixel_mapping_keeps_complete_refusals_empty() -> None:
    row = {
        "status": "ok",
        "viewport": [10, 20, 210, 120],
        "image_size": [100, 50],
        "components": [{"bbox": [25, 10, 50, 30]}],
    }
    assert color_boxes(row) == [[60, 40, 110, 80]]
    row["status"] = "error"
    assert color_boxes(row) == []


@pytest.mark.parametrize("case", ["missing_proposal", "unrequested", "transcription", "rollback"])
def test_strict_miss_partition_keeps_error_denominator(case: str) -> None:
    reference = {"id": "p", "tables": [table()]}
    crop = {"viewport": [0, 0, 30, 30], "status": "ok", "request": {}}
    prediction = {"id": "p", "status": "ok", "tables": [table("wrong")], "transcription_regions": [crop]}
    category = "accepted_crop_transcription_or_structure_failure"
    if case == "missing_proposal":
        prediction["transcription_regions"] = []
        prediction["tables"] = []
        category = "proposal_coverage_failure"
    elif case == "unrequested":
        crop.pop("request")
        category = "request_admission_or_selection_failure"
    elif case == "rollback":
        prediction.update(status="error", error="Malformed image bounds", tables=[table()])
        category = "whole_page_rollback"
    result = attribute_page(reference, prediction)
    assert result["misses"][category] == 1
    assert result["score"]["strict_exact_cells"] == 0
    assert result["score"]["expected_cells"] == 1
