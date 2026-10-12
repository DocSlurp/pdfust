"""Source-only routing priority, ambiguity vetoes and paint evidence boundaries."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from bench.corpus_routes import RULES, compact_numeric, overlaps, paint_support, route_tables, totals
from bench.silver_structure import authored_table

import pdfust


def candidate() -> dict[str, Any]:
    return {
        "bbox": [0, 0, 100, 60],
        "row_count": 3,
        "col_count": 2,
        "values": [["Name", "Year"], ["East 10", "West 20"], ["East 30", "West 40"]],
    }


def stroke(y: float, length: float = 100) -> dict[str, Any]:
    return {"type": "s", "items": [("l", pdfust.Point(0, y), pdfust.Point(length, y))]}


def test_vector_priority_preserves_merged_cells_and_ownership() -> None:
    grid = authored_table(0)
    partial = candidate()
    partial["bbox"] = [50, 120, 400, 260]
    for route in ("vector", "vector-veto", "vector-paint"):
        assert route_tables(route, [grid], [partial], []) == [grid]
        assert grid["values"][0][1] is None
        assert grid["spans"][0]["column_span"] == 2
    assert route_tables("none", [grid], [partial], []) == []
    assert route_tables("raw-text", [grid], [partial], []) == [partial]


def test_numeric_prose_is_ambiguous_without_paint() -> None:
    table = candidate()
    assert compact_numeric(table)
    assert route_tables("vector-veto", [], [table], []) == [table]
    assert route_tables("vector-paint", [], [table], []) == []
    assert route_tables("vector-paint", [], [table], [stroke(0), stroke(60)]) == [table]


@pytest.mark.parametrize("value", ["A sentence ends here.", "word " * 9, "x" * 73])
def test_prose_veto(value: str) -> None:
    table = candidate()
    table["values"][0][0] = value
    assert not compact_numeric(table)


def test_numeric_rows_require_two_columns_in_two_rows() -> None:
    table = candidate()
    table["values"][2] = ["East", "West"]
    assert not compact_numeric(table)
    table["values"][2] = ["East 30", "West"]
    assert not compact_numeric(table)


def test_paint_support_requires_distinct_long_strokes() -> None:
    table = candidate()
    assert not paint_support(table, [stroke(0), stroke(0.5)])
    assert not paint_support(table, [stroke(0, 69), stroke(60, 69)])
    assert not paint_support(table, [stroke(-3), stroke(63)])
    assert paint_support(table, [stroke(-2, 70), stroke(62, 70)])


def test_adjacent_candidates_do_not_overlap_but_duplicate_candidates_do() -> None:
    first = candidate()
    second = deepcopy(first)
    second["bbox"] = [100, 0, 200, 60]
    assert not overlaps(first["bbox"], second["bbox"])
    assert route_tables("vector-veto", [], [first, deepcopy(first), second], []) == [first, second]


def test_unknown_route_and_fixed_error_denominator() -> None:
    with pytest.raises(ValueError, match="Unknown"):
        route_tables("invented", [], [], [])
    rows = [{"route": route, "status": "error"} for route in RULES["routes"]]
    summary = totals(rows, {"pages": [{}, {}]})
    assert all(value["pages"] == 2 and value["exact_page"] == 0 and value["errors"] == 2 for value in summary.values())
