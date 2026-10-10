"""Exact retained native ownership including absent geometric boundaries."""

from types import SimpleNamespace
from typing import NamedTuple

import pytest
from bench.pipeline_native_tables import observed_table


class Diagnostics(NamedTuple):
    """Minimal retained diagnostic record."""

    strategy: str


def fixture(cells: list, anchors: list, values: list, rows: int, columns: int) -> SimpleNamespace:
    return SimpleNamespace(
        cells=cells,
        _cell_anchors=anchors,
        extract=lambda: values,
        row_count=rows,
        col_count=columns,
        bbox=[0, 0, 30, 30],
        diagnostics=Diagnostics("lines"),
    )


def test_full_width_two_row_header_uses_anchors_with_blank_owner() -> None:
    table = fixture(
        [[0, 0, 30, 20], None, None, None, [0, 20, 15, 30], [15, 20, 30, 30]],
        [0, 0, 0, 0, 4, 5],
        [["", None], [None, None], ["A", "B"]],
        3,
        2,
    )
    result = observed_table(table)
    assert result["spans"][0] == {"row": 0, "column": 0, "row_span": 2, "column_span": 2}
    assert sum(span["row_span"] * span["column_span"] for span in result["spans"]) == 6
    assert result["values"][0][0] == ""


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_right_angle_geometry_preserves_slot_ownership(rotation: int) -> None:
    def rotate(box: list) -> list:
        points = [(box[0], box[1]), (box[2], box[3])]
        for _ in range(rotation // 90):
            points = [(30 - y, x) for x, y in points]
        return [
            min(x for x, _ in points),
            min(y for _, y in points),
            max(x for x, _ in points),
            max(y for _, y in points),
        ]

    table = fixture(
        [rotate([0, 0, 30, 15]), None, rotate([0, 15, 15, 30]), rotate([15, 15, 30, 30])],
        [0, 0, 2, 3],
        [["Head", None], ["A", "B"]],
        2,
        2,
    )
    assert observed_table(table)["spans"][0]["column_span"] == 2


def test_borderless_gaps_are_not_extra_rows_or_columns() -> None:
    table = fixture(
        [[0, 0, 10, 10], [20, 0, 30, 10], [0, 20, 10, 30], [20, 20, 30, 30]],
        [0, 1, 2, 3],
        [["A", "B"], ["C", "D"]],
        2,
        2,
    )
    assert all(span["row_span"] == span["column_span"] == 1 for span in observed_table(table)["spans"])


def test_duplicate_geometry_cannot_claim_distinct_owners() -> None:
    table = fixture([[0, 0, 30, 30], [0, 0, 30, 30]], [0, 1], [["A", "B"]], 1, 2)
    with pytest.raises(ValueError, match="overlap"):
        observed_table(table)


def test_nonrectangular_ownership_is_rejected() -> None:
    table = fixture([[0, 0, 30, 30], None, None, [15, 15, 30, 30]], [0, 0, 0, 3], [["A", None], [None, "B"]], 2, 2)
    with pytest.raises(ValueError, match="rectangle"):
        observed_table(table)
