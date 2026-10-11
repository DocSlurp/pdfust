"""Preserve the trusted alignment scope rather than synthesizing cell confidence."""

import pytest
from bench.p003_alignment_visual_review import group_score, span_warning


def test_group_score_uses_retained_character_denominators() -> None:
    """A missing row is red, a blank group is unscored, and extra characters reduce precision."""
    assert group_score({"matched": 8, "reference_units": 8, "prediction_units": 10}) == pytest.approx(8 / 9)
    assert group_score({"matched": 0, "reference_units": 30, "prediction_units": 0}) == 0
    assert group_score({"matched": 0, "reference_units": 0, "prediction_units": 0}) is None
    with pytest.raises(ValueError, match="denominator"):
        group_score({"matched": 10, "reference_units": 8, "prediction_units": 10})


def test_merged_membership_warning_covers_the_covered_row() -> None:
    """Equal literal content cannot hide loss of a two-row merged anchor."""
    reference = {"spans": [{"row": 1, "column": 4, "row_span": 2, "column_span": 1}]}
    actual: dict[str, list[dict[str, int]]] = {"spans": []}
    cell = {"reference_columns": [4, 5], "prediction_columns": [4, 5]}
    for index in (1, 2):
        assert span_warning({"reference_row": index, "prediction_row": index}, cell, reference, actual)
    assert not span_warning({"reference_row": 3, "prediction_row": 3}, cell, reference, actual)
