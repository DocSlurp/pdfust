"""Column ambiguity cannot excuse lost rows, changed values or named field boundaries."""

from copy import deepcopy

import pytest
from bench.p003_schema_sensitivity import compare, tokens


def table(values: list[list[str]]) -> dict:
    return {"row_count": len(values), "col_count": len(values[0]), "values": values, "spans": []}


def example() -> tuple[dict, dict]:
    return (
        table([["No.", "Rec.", "Last"], ["1.Hingham", "6-0-0", "2"], ["2. Notre Dame", "4-1-1", "1"]]),
        table([["No.", "", "Rec.", "Last"], ["1.", "Hingham", "6-0-0", "2"], ["2.", "Notre Dame", "4-1-1", "1"]]),
    )


def test_both_earned_granularities_preserve_all_rows_and_headers() -> None:
    a, b = example()
    for reference, prediction in ((a, b), (b, a)):
        result = compare(reference, prediction)
        assert result["schema_equivalent"]
        assert result["fine_column_groups"] == [[0, 1], [2], [3]]
        assert result["same_position_row_token_matches"] == 3


@pytest.mark.parametrize("change", ["row_missing", "row_swapped", "column_swapped", "value", "header", "padding"])
def test_nearby_invalid_outputs_do_not_gain_acceptance(change: str) -> None:
    a, b = example()
    if change == "row_missing":
        b["values"].pop()
        b["row_count"] -= 1
    elif change == "row_swapped":
        b["values"][1], b["values"][2] = b["values"][2], b["values"][1]
    elif change == "column_swapped":
        for row in b["values"]:
            row[2], row[3] = row[3], row[2]
    elif change == "value":
        b["values"][1][2] = "6-0-1"
    elif change == "header":
        b["values"][0][1] = "Invented"
    else:
        for row in b["values"]:
            row.append("")
        b["col_count"] += 1
    assert not compare(a, b)["schema_equivalent"]


def test_token_boundaries_and_mathematical_case_are_not_erased() -> None:
    assert tokens("1 23") != tokens("12 3")
    assert tokens("New York") != tokens("NewYork")
    assert tokens("$1,200.00") == tokens("$ 1,200.00")
    assert tokens("O₂") != tokens("O2")
    assert tokens("NULL") != tokens("null")


def test_named_headers_cannot_be_collapsed_even_when_row_tokens_agree() -> None:
    a = table([["Amount Date"], ["$12 10/02/2026"]])
    b = table([["Amount", "Date"], ["$12", "10/02/2026"]])
    assert not compare(a, b)["schema_equivalent"]


def test_one_partition_must_fit_every_row_and_duplicates_keep_positions() -> None:
    a = table([["", ""], ["A B", "C"], ["A", "B C"]])
    b = table([["", "", ""], ["A", "B", "C"], ["A", "B", "C"]])
    assert not compare(a, b)["schema_equivalent"]
    same = table([["Name", "Amount"], ["Echo", "$1"], ["Echo", "$2"]])
    changed = deepcopy(same)
    changed["values"][1][-1], changed["values"][2][-1] = "$2", "$1"
    assert not compare(same, changed)["schema_equivalent"]


def test_merged_cells_are_explicitly_out_of_scope() -> None:
    merged = table([["Header", ""], ["A", "B"]])
    merged["values"][0][1] = None
    merged["spans"] = [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}]
    result = compare(merged, merged)
    assert not result["eligible"]
    assert not result["schema_equivalent"]
