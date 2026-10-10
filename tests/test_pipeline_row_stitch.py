"""Capacity continuation alternatives preserve literal ownership and baseline."""

from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_assembly import _clean_table
from bench.pipeline_regions import split, validate_composed
from bench.pipeline_row_stitch import propose


def fixture(*, repeated: bool = False, drift: float = 0, gap: float = 0) -> tuple[dict[str, Any], dict[str, Any]]:
    page: dict[str, Any] = {"page_size": [300, 400], "vector_candidates": [], "words": []}
    for row in range(8):
        for col in range(2):
            text = ("Name", "Value")[col] if row == 0 or (repeated and row == 4) else f"item{row}-{col}"
            x = 10 + col * 100 + (drift if row >= 4 else 0)
            y = 10 + row * 20 + (gap if row >= 4 else 0)
            page["words"].append({"id": f"w{row}-{col}", "text": text, "bbox": [x, y, x + 30, y + 10]})
    plan = split(page, max_words=8)
    states = {}
    lookup = {w["id"]: w for w in page["words"]}
    for region in plan["regions"]:
        ids = region["source_ids"]
        rows = len(ids) // 2
        table = {
            "row_count": rows,
            "col_count": 2,
            "cells": [{"source_ids": [i], "role": "unknown"} for i in ids],
            "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(rows) for c in range(2)],
        }
        states[region["id"]] = {"id": "c0", "tables": [_clean_table(table, lookup)], "unresolved_ids": []}
    return plan, states


def test_aligned_adjacent_capacity_rows_offer_complete_stitch_without_mutation() -> None:
    plan, states = fixture(drift=3)
    previous = deepcopy((plan, states))
    alternatives = propose(plan, states)
    assert len(alternatives) == 2
    assert len(alternatives[0]["tables"]) == 2
    assert alternatives[1]["tables"][0]["row_count"] == 8
    assert alternatives[1]["tables"][0]["values"][4] == ["item4-0", "item4-1"]
    assert (plan, states) == previous
    for state in alternatives:
        validate_composed(plan, state)


def test_repeated_header_keep_and_drop_have_explicit_unique_source_ownership() -> None:
    plan, states = fixture(repeated=True)
    alternatives = propose(plan, states)
    assert len(alternatives) == 3
    keep, drop = alternatives[1:]
    assert keep["tables"][0]["row_count"] == 8
    assert drop["tables"][0]["row_count"] == 7
    assert drop["repeated_header_unresolved_ids"] == ["w4-0", "w4-1"]
    assert drop["unresolved_ids"] == ["w4-0", "w4-1"]
    assert keep["repeated_header_unresolved_ids"] == []
    for state in alternatives:
        validate_composed(plan, state)


@pytest.mark.parametrize("kwargs", [{"drift": 30}, {"gap": 100}])
def test_misaligned_or_separate_blocks_abstain(kwargs: dict[str, float]) -> None:
    plan, states = fixture(drift=kwargs.get("drift", 0), gap=kwargs.get("gap", 0))
    assert len(propose(plan, states)) == 1


def test_word_capacity_boundaries_are_not_complete_row_continuations() -> None:
    plan, states = fixture()
    plan["regions"][0]["boundary"] = "capacity_words"
    assert len(propose(plan, states)) == 1


def test_sparse_profiles_without_two_samples_per_column_abstain() -> None:
    plan, states = fixture()
    table = states["r1"]["tables"][0]
    # Return absent second-column words to unresolved rather than discarding them.
    lookup = {w["id"]: w for w in plan["words"]}
    for row in range(1, 4):
        cell = table["cells"][row * 2 + 1]
        states["r1"]["unresolved_ids"].extend(cell["source_ids"])
        cell["source_ids"] = []
    states["r1"]["tables"][0] = _clean_table(table, lookup)
    assert len(propose(plan, states)) == 1


def test_missing_output_and_admission_reject_complete_result() -> None:
    plan, states = fixture(repeated=True)
    with pytest.raises(ValueError, match="Missing"):
        propose(plan, {"r0": states["r0"]})
    with pytest.raises(ValueError, match="inventory exceeds"):
        propose(plan, states, max_alternatives=2)


def test_internal_merged_spans_shift_without_crossing_capacity_boundary() -> None:
    plan, states = fixture()
    lookup = {w["id"]: w for w in plan["words"]}
    second = states["r1"]["tables"][0]
    second["cells"][0]["source_ids"].extend(second["cells"][1]["source_ids"])
    second["cells"][1]["source_ids"] = []
    second["spans"] = [
        {"row": 0, "column": 0, "row_span": 1, "column_span": 2},
        *[s for s in second["spans"] if s["row"] > 0],
    ]
    states["r1"]["tables"][0] = _clean_table(second, lookup)
    alternatives = propose(plan, states)
    assert len(alternatives) == 2
    joined = alternatives[1]["tables"][0]
    assert {"row": 4, "column": 0, "row_span": 1, "column_span": 2} in joined["spans"]
    assert joined["values"][4][1] is None
    validate_composed(plan, alternatives[1])
