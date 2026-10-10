"""Frozen synthetic metric tests; no corpus references or inference."""

from typing import Any

from bench.generalization_cell_inventory import compare, inventory


def table(values: list[list[str | None]], spans: list[dict[str, int]] | None = None) -> dict[str, Any]:
    return {"row_count": len(values), "col_count": len(values[0]), "values": values, "spans": spans or []}


def test_page_multiset_ignores_placement_and_consumes_duplicates_once() -> None:
    target = {"id": "synthetic", "tables": [table([["A", "B", "A"]])]}
    predicted = {"status": "ok", "tables": [table([["B", "A"]]), table([["B"]])]}
    result = compare(target, predicted)
    assert result["matched_nonempty"] == 2
    assert result["expected_nonempty"] == result["predicted_nonempty"] == 3


def test_authoritative_normalization_preserves_case_punctuation_and_complete_cells() -> None:
    target = {"id": "unicode", "tables": [table([["é  東京", "A.", "AB"]])]}
    predicted = {"status": "ok", "tables": [table([["e\u0301\n東京", "a.", "A", "B"]])]}
    assert compare(target, predicted)["matched_nonempty"] == 1


def test_empty_anchors_are_separate_and_covered_slots_do_not_count() -> None:
    merged = table([["X", None], [" ", ""]], [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}])
    assert inventory([merged]) == {"X": 1, "": 2}
    result = compare({"id": "merged", "tables": [merged]}, {"status": "ok", "tables": [table([["", "X"]])]})
    assert result["matched_nonempty"] == 1
    assert result["matched_empty"] == 1
    assert result["expected_empty"] == 2
    assert result["optimistic_total"] == 2


def test_failed_prefix_is_never_admitted_or_validated() -> None:
    target = {"id": "failed", "tables": [table([["kept", ""]])]}
    result = compare(target, {"status": "error", "tables": [{"malformed": "retained prefix"}]})
    assert not result["admitted"]
    assert result["predicted_nonempty"] == result["predicted_empty"] == result["optimistic_total"] == 0


def test_negative_page_retains_predicted_strings_without_matches() -> None:
    result = compare({"id": "negative", "tables": []}, {"status": "ok", "tables": [table([["extra"]])]})
    assert result["predicted_nonempty"] == 1
    assert result["matched_nonempty"] == 0
