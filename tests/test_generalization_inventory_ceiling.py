"""Optimistic inventory ceilings preserve literal joins and missing measurements."""

from __future__ import annotations

from itertools import product

from bench.generalization_inventory_ceiling import Inventory, evaluate
from bench.generalization_scoring import normalize_text


def test_strict_whole_tokens_preserve_spaces_case_and_punctuation() -> None:
    inventory = Inventory(["A", "B", "12", "kg", "whole token", "\t", "e\u0301"])
    assert inventory.possible("A B")
    assert inventory.possible("A A A")  # Unlimited reuse is deliberately optimistic.
    assert inventory.possible(" whole\n token ")
    assert inventory.possible("é")
    assert inventory.possible("")
    assert not inventory.possible("AB")
    assert not inventory.possible("12kg")
    assert not inventory.possible("a")
    assert not inventory.possible("A,")
    assert not inventory.possible("whole")


def test_join_normalization_factorizes_at_ascii_space_boundaries() -> None:
    tokens = [" A\n B ", "e\u0301", "\u0301", "\u00a0", "\u1100", "\u1161"]
    for sequence in product(tokens, repeat=3):
        actual = normalize_text(" ".join(sequence))
        factored = " ".join(value for token in sequence if (value := normalize_text(token)))
        assert actual == factored
        assert Inventory(tokens).possible(actual)
        assert Inventory(tokens, relaxed=True).possible(actual)


def test_relaxed_whitespace_free_decomposition_is_labeled_more_permissive() -> None:
    tokens = ["12", "kg", "e", "\u0301"]
    strict, relaxed = Inventory(tokens), Inventory(tokens, relaxed=True)
    assert not strict.possible("12kg")
    assert relaxed.possible("12kg")
    assert not strict.possible("é")
    assert relaxed.possible("é")
    assert not relaxed.possible("12KG")


def test_cells_tables_empty_anchors_and_missing_inventory_stay_distinct() -> None:
    table = {"row_count": 1, "col_count": 3, "values": [["A", "", "AB"]], "spans": []}
    targets = [{"id": "measured", "tables": [table]}, {"id": "missing", "tables": [table]}]
    predictions = [{"id": "measured", "source": {"words": [{"text": "A"}, {"text": "B"}]}}]
    result = evaluate(targets, predictions)
    totals = result["totals"]
    assert totals["expected_cells"] == 6
    assert totals["empty_cells"] == 2
    assert totals["measured_pages"] == 1
    assert totals["possible_cells"] == 2
    assert totals["possible_tables"] == 0
    assert totals["relaxed_possible_cells"] == 3
    assert totals["relaxed_possible_tables"] == 1
    assert totals["unmeasured_cells"] == 3
    assert totals["optimistic_upper_cells"] == 5
    assert totals["optimistic_upper_tables"] == 1


def test_empty_measured_inventory_is_not_an_unmeasured_page() -> None:
    table = {"row_count": 1, "col_count": 2, "values": [["", "A"]], "spans": []}
    result = evaluate([{"id": "empty", "tables": [table]}], [{"id": "empty", "source": {"words": []}}])
    assert result["totals"]["unmeasured_cells"] == 0
    assert result["totals"]["possible_cells"] == 1


def test_merged_covered_slots_are_not_anchor_denominators() -> None:
    table = {
        "row_count": 2,
        "col_count": 2,
        "values": [["A", None], ["B", ""]],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}],
    }
    result = evaluate(
        [{"id": "merged", "tables": [table]}],
        [
            {
                "id": "merged",
                "source": {"words": [{"text": "A"}, {"text": "B"}]},
            }
        ],
    )
    assert result["totals"]["expected_cells"] == 3
    assert result["totals"]["possible_cells"] == 3
    assert result["totals"]["possible_tables"] == 1
