"""Retained-witness projection never drops literals or negative-page penalties."""

from __future__ import annotations

from typing import Any

import pytest
from bench.p003_wrap_audit import anchor_matrix, residual_counts


def test_anchor_projection_retains_empty_slots_without_expanding_merged_text() -> None:
    receipt: dict[str, Any] = {
        "row_count": 2,
        "col_count": 2,
        "literal_characters": 5,
        "anchors": [{"row": 0, "column": 0, "literal": "North"}, {"row": 1, "column": 1, "literal": ""}],
    }
    assert anchor_matrix(receipt) == [["North", ""], ["", ""]]
    receipt["anchors"].append({"row": 0, "column": 0, "literal": "North"})
    with pytest.raises(ValueError, match="Unique"):
        anchor_matrix(receipt)


def test_unmatched_negative_table_content_remains_in_precision_denominator() -> None:
    pair = {"matched": 4, "substituted": 0, "missing": 0, "extra": 0, "reference_units": 4, "prediction_units": 4}
    total = {**pair, "extra": 9, "prediction_units": 13}
    result = residual_counts(total, [{"counts": pair}])
    assert result == {**dict.fromkeys(pair, 0), "extra": 9, "prediction_units": 9}


def test_residual_refuses_lost_reference_content() -> None:
    with pytest.raises(ValueError, match="Reference residual"):
        residual_counts({"reference_units": 9}, [])


def test_residual_refuses_reused_pair_content() -> None:
    pair = {"matched": 4, "substituted": 0, "missing": 0, "extra": 0, "reference_units": 4, "prediction_units": 4}
    with pytest.raises(ValueError, match="exceed"):
        residual_counts(pair, [{"counts": pair}, {"counts": pair}])
