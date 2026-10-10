"""Handcrafted canonical-schema refusals, independent of benchmark references."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from bench.generalization_scoring import score_page


def table() -> dict[str, Any]:
    return {"row_count": 1, "col_count": 2, "values": [["A", "B"]], "spans": []}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("values", ["AB"]),
        ("values", (["A", "B"],)),
        ("values", [("A", "B")]),
        ("spans", {}),
        ("spans", ""),
        ("spans", ()),
        ("spans", ["not-a-dictionary"]),
        ("spans", [[0, 0, 1, 2]]),
    ],
)
def test_noncanonical_prediction_is_atomic_failure(field: str, value: object) -> None:
    bad = {**table(), field: value}
    result = score_page({"tables": [table()]}, [bad])
    assert result["malformed"]
    assert result["error"]
    assert result["complete_tables"] == 0
    assert result["correct_text_cells"] == 0
    assert result["missing_tables"] == 1
    assert result["expected_cells"] == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [("values", ["AB"]), ("values", "AB"), ("spans", {}), ("spans", ["not-a-dictionary"])],
)
def test_noncanonical_reference_is_annotation_refusal(field: str, value: object) -> None:
    bad = {**table(), field: value}
    result = score_page({"tables": [bad]}, [table()])
    assert not result["structural_scored"]
    assert result["annotation_errors"] == ["invalid_reference_matrix"]


def test_blank_tables_without_geometry_keep_frozen_matching_protocol() -> None:
    # Without geometry or normalized text, multiple blank tables have no cue.
    # A future matching protocol can consider this separately; schema validation
    # must not alter the current campaign's admission/matching definition.
    blank = {"row_count": 1, "col_count": 1, "values": [[""]], "spans": []}
    result = score_page({"tables": [blank, deepcopy(blank)]}, [blank, deepcopy(blank)])
    assert result["matched_tables"] == result["complete_tables"] == 0
    assert result["missing_tables"] == result["false_positive_tables"] == 2
    assert not result["exact_page"]
