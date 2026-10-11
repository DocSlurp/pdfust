"""Old P001 slot metrics and new anchor/content metrics retain distinct contracts."""

from __future__ import annotations

from bench.p003_p001_rescore import historical_rows, score_outputs


def test_original_report_table_counts() -> None:
    text = """| Run | Exact scored pages | other |
|---|---|---|
| arm | 3/4 | 2/5 | 2/2 | 2/2 | 7/8/9 | 0/3 | 4/4 | 2/2 |
| Run | Output p/min |
"""
    row = historical_rows(text)["arm"]
    assert row["complete_tables"] == 2
    assert row["correct_cell_slots"] == 7
    assert row["false_positive_tables"] == 3
    assert row["penalized_cell_slots"] == 9


def test_covered_slots_are_not_new_anchor_cells() -> None:
    table = {
        "row_count": 2,
        "col_count": 2,
        "values": [["A", None], ["B", "C"]],
        "spans": [
            {"row": 0, "column": 0, "row_span": 1, "column_span": 2},
            {"row": 1, "column": 0, "row_span": 1, "column_span": 1},
            {"row": 1, "column": 1, "row_span": 1, "column_span": 1},
        ],
    }
    scores = score_outputs(
        [{"id": "a", "structural_scored": True, "tables": [table]}], [{"id": "a", "status": "ok", "tables": [table]}]
    )
    assert scores["historical_strict"]["totals"]["correct_cell_slots"] == 4
    assert scores["mapped_strict"]["totals"]["strict_exact_cells"] == 3
    assert scores["historical_strict"]["totals"]["complete_tables"] == 1
    assert scores["secondary"]["counts"]["content_recovered_tables"] == 1


def test_page_failure_removes_output_credit_for_both_scorers() -> None:
    table = {
        "row_count": 1,
        "col_count": 1,
        "values": [["A"]],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}],
    }
    scores = score_outputs(
        [{"id": "a", "tables": [table], "structural_scored": True}], [{"id": "a", "status": "error", "tables": [table]}]
    )
    assert scores["historical_strict"]["totals"]["correct_cell_slots"] == 0
    assert scores["mapped_strict"]["totals"]["strict_exact_cells"] == 0
    assert scores["secondary"]["counts"]["missing_tables"] == 1
