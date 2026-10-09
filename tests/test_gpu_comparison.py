"""Verify cohort-isolated presence scoring and CPU/GPU tolerance reporting."""

import pytest
from bench.gpu_comparison import compare_predictions, confusion


def test_confusion_keeps_false_positives_and_misses() -> None:
    assert confusion([True, True, False, False], [True, False, True, False]) == {
        "tp": 1,
        "fn": 1,
        "fp": 1,
        "tn": 1,
    }
    with pytest.raises(ValueError, match="counts"):
        confusion([True], [])


def test_comparison_exposes_topology_and_numeric_difference() -> None:
    left = [{"id": "one", "boxes": [{"class": "Table", "confidence": 0.7, "xyxy": [1.0, 2.0, 3.0, 4.0]}]}]
    close = [{"id": "one", "boxes": [{"class": "Table", "confidence": 0.7001, "xyxy": [1.01, 2.0, 3.0, 4.0]}]}]
    result = compare_predictions(left, close)
    assert result["bit_exact_pages"] == 0
    assert result["within_tolerance_pages"] == 1
    result = compare_predictions(left, [{"id": "one", "boxes": []}])
    assert result["ordered_topology_equal_pages"] == 0
    assert result["within_tolerance_pages"] == 0
    with pytest.raises(ValueError, match="cohorts"):
        compare_predictions(left, [{"id": "different", "boxes": []}])


def test_box_comparison_matches_geometry_after_confidence_rank_swap() -> None:
    first = {"class": "Table", "confidence": 0.7, "xyxy": [0, 0, 10, 10]}
    second = {"class": "Table", "confidence": 0.7, "xyxy": [20, 20, 30, 30]}
    result = compare_predictions(
        [{"id": "one", "boxes": [first, second]}],
        [{"id": "one", "boxes": [second, first]}],
    )
    assert result["within_tolerance_pages"] == 1
    assert result["max_box_delta_on_equal_topology"] == 0
