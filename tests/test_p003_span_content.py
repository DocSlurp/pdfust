"""Merged anchors retain text once; topology is distinct from tolerant content."""

from __future__ import annotations

from copy import deepcopy

import pytest
from bench.p003_span_content import compare_table_content


def table(values: list, spans: list | None = None) -> dict:
    return {"row_count": len(values), "col_count": len(values[0]), "values": values, "spans": spans or []}


HORIZONTAL = table([["Merged heading", None], ["A", "B"]], [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}])
VERTICAL = table([["Same value", "A"], [None, "B"]], [{"row": 0, "column": 0, "row_span": 2, "column_span": 1}])


@pytest.mark.parametrize("source", [HORIZONTAL, VERTICAL])
def test_unchanged_horizontal_vertical_span_content_once(source: dict) -> None:
    original = deepcopy(source)
    result = compare_table_content(source, source)
    assert result["supported"]
    assert result["span_topology_equal"]
    assert result["content_recovered_with_row_order"]
    assert result["precision"] == result["recall"] == 1
    assert result["schema_correctness"] is None
    assert result["span_coverage"]["reference"]["anchor_count"] == 3
    assert result["span_coverage"]["reference"]["covered_slot_count"] == 1
    assert result["span_coverage"]["reference"]["merged_anchor_count"] == 1
    assert result["span_coverage"]["reference"]["literal_characters"] == sum(
        len(v) for row in source["values"] for v in row if v is not None
    )
    assert source == original


@pytest.mark.parametrize("source", [HORIZONTAL, VERTICAL])
def test_wrong_span_same_anchor_literals_content_survives_but_schema_unknown(source: dict) -> None:
    prediction = table([["" if v is None else v for v in row] for row in source["values"]])
    result = compare_table_content(source, prediction)
    assert result["content_recovered_with_row_order"]
    assert result["span_topology_equal"] is False
    assert result["schema_correctness"] is None
    assert result["span_coverage"]["prediction"]["covered_slot_count"] == 0


def test_missing_anchor_text_lowers_recall_without_expanding_merged_value() -> None:
    prediction = deepcopy(HORIZONTAL)
    prediction["values"][0][0] = "heading"
    result = compare_table_content(HORIZONTAL, prediction)
    assert result["span_topology_equal"]
    assert result["counts"]["missing"] == len("Merged ")
    assert result["recall"] < 1
    assert not result["content_recovered_with_row_order"]
    assert result["span_coverage"]["reference"]["anchors"][0]["literal"] == "Merged heading"


def test_relocated_anchor_row_is_not_complete_and_receipts_preserve_extents() -> None:
    prediction = table([["", "A"], ["Same value", "B"]])
    result = compare_table_content(VERTICAL, prediction)
    assert not result["content_recovered_with_row_order"]
    assert not result["span_topology_equal"]
    assert result["span_coverage"]["reference"]["anchors"][0]["covered_slots"] == [[1, 0]]


def test_duplicate_literals_remain_distinct_anchors_and_omissions_penalized() -> None:
    reference = table([["same", None], ["same", "same"]], [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}])
    result = compare_table_content(reference, reference)
    assert result["counts"]["matched"] == 12
    assert len([a for a in result["span_coverage"]["reference"]["anchors"] if a["literal"] == "same"]) == 3
    prediction = deepcopy(reference)
    prediction["values"][1][0] = ""
    missing = compare_table_content(reference, prediction)
    assert missing["counts"]["matched"] == 8
    assert missing["counts"]["missing"] == 4
    assert missing["recall"] == 2 / 3


@pytest.mark.parametrize(
    "invalid",
    [
        table([["A", None]], []),
        table([["A", "copied"]], [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}]),
        table(
            [["A", None], [None, "B"]],
            [
                {"row": 0, "column": 0, "row_span": 1, "column_span": 2},
                {"row": 0, "column": 1, "row_span": 2, "column_span": 1},
            ],
        ),
        table([["A"]], [{"row": 0, "column": 0, "row_span": 2, "column_span": 1}]),
        table([["A"]], [{"row": 0, "column": 0, "row_span": True, "column_span": 1}]),
    ],
)
def test_malformed_overlap_none_bounds_types_refused_not_quality_zero(invalid: dict) -> None:
    result = compare_table_content(invalid, HORIZONTAL)
    assert result["supported"] is False
    assert result["precision"] is result["recall"] is result["counts"] is None
    assert result["span_topology_equal"] is None
    assert result["unsupported_reason"].startswith("reference span validation")


def test_explicit_unit_records_and_implicit_units_have_same_topology_and_unicode_normalization() -> None:
    reference = table([["Café\nNorth", ""]])
    prediction = table(
        [["Cafe\u0301 North", ""]],
        [
            {"row": 0, "column": 0, "row_span": 1, "column_span": 1},
            {"row": 0, "column": 1, "row_span": 1, "column_span": 1},
        ],
    )
    result = compare_table_content(reference, prediction)
    assert result["span_topology_equal"]
    assert result["content_recovered_with_row_order"]
    assert result["span_coverage"]["reference"]["anchors"][0]["literal"] == "Café\nNorth"


def test_swap_invariance_with_merged_spans_preserves_original_receipt_roles() -> None:
    a = compare_table_content(HORIZONTAL, VERTICAL)
    b = compare_table_content(VERTICAL, HORIZONTAL)
    assert a["counts"]["matched"] == b["counts"]["matched"]
    assert a["counts"]["missing"] == b["counts"]["extra"]
    assert a["precision"] == b["recall"]
    assert a["span_coverage"]["reference"] == b["span_coverage"]["prediction"]
    assert not a["span_topology_equal"]


def test_relocated_horizontal_anchor_and_changed_row_extent_have_no_schema_acceptance() -> None:
    prediction = table([["", "Merged heading"], ["A", "B"]])
    relocated = compare_table_content(HORIZONTAL, prediction)
    assert not relocated["span_topology_equal"]
    assert relocated["schema_correctness"] is None
    assert relocated["span_coverage"]["prediction"]["anchors"][1]["column"] == 1
    extended = table([["A"], [None], [None]], [{"row": 0, "column": 0, "row_span": 3, "column_span": 1}])
    shorter = table([["A"], [None], [""]], [{"row": 0, "column": 0, "row_span": 2, "column_span": 1}])
    changed = compare_table_content(extended, shorter)
    assert changed["content_recovered_with_row_order"]
    assert changed["span_topology_equal"] is False
    assert changed["span_coverage"]["reference"]["covered_slot_count"] == 2
    assert changed["span_coverage"]["prediction"]["covered_slot_count"] == 1


def test_anchor_admission_refuses_oversize_without_quality_zero() -> None:
    result = compare_table_content(table([["X" * 1025]]), HORIZONTAL)
    assert not result["supported"]
    assert "over-limit raw anchor literal" in result["unsupported_reason"]
    assert result["counts"] is result["precision"] is None
