"""Source-only region proposals conserve complete dense and mixed pages."""

from collections import Counter
from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_assembly import native_state, propose
from bench.pipeline_regions import compose, split, unresolved_region, validate_composed


def page() -> dict[str, Any]:
    return {"page_size": [600, 1000], "words": [], "vector_candidates": []}


def add_word(source: dict[str, Any], x: float, y: float, text: str = "literal", width: float = 25) -> None:
    source["words"].append({"id": f"global-{len(source['words'])}", "text": text, "bbox": [x, y, x + width, y + 10]})


def add_grid(source: dict[str, Any], y: float, *, merged: bool = False) -> None:
    boxes: list[list[float] | None] = [
        [10, y, 70, y + 20],
        [70, y, 130, y + 20],
        [10, y + 20, 70, y + 40],
        [70, y + 20, 130, y + 40],
    ]
    spans = [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)]
    if merged:
        boxes[0] = [10, y, 130, y + 20]
        boxes[1] = None
        spans = [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}, *spans[2:]]
    source["vector_candidates"].append({"row_count": 2, "col_count": 2, "cells": boxes, "spans": spans})
    for box in boxes:
        if box is not None:
            add_word(source, box[0] + 5, box[1] + 5)


def all_unresolved(plan: dict[str, Any]) -> dict[str, Any]:
    return compose(plan, {r["id"]: unresolved_region(r) for r in plan["regions"]})


def test_mixed_native_borderless_and_prose_remain_separate() -> None:
    source = page()
    add_grid(source, 20, merged=True)
    add_grid(source, 150)
    for row in range(4):
        for column in range(2):
            add_word(source, 10 + 60 * column, 300 + 20 * row, str(row + column))
    add_word(source, 10, 800, "Footer prose")
    plan = split(source)
    assert [r["kind"] for r in plan["regions"]].count("native") == 2
    states = {
        r["id"]: native_state(r["source"]) if r["kind"] == "native" else propose(r["source"])[0]
        for r in plan["regions"]
    }
    state = compose(plan, states)
    assert len(state["tables"]) == 2
    assert state["tables"][0]["values"][0][1] is None
    assert len(state["unresolved_ids"]) == 9
    validate_composed(source, state)
    assert all(r["source"]["page_size"] == source["page_size"] for r in plan["regions"])


def test_dense_page_exceeds_old_whole_page_admission_without_loss() -> None:
    source = page()
    source["page_size"] = [600, 10_000]
    for row in range(600):
        for column in range(10):
            add_word(source, 10 + column * 40, 10 + row * 15, "complete literal source")
    plan = split(source, max_words=200, max_characters=4000)
    assert len(source["words"]) > 4096
    assert sum(len(w["text"]) for w in source["words"]) > 25_000
    assert all(len(r["source"]["words"]) <= 200 for r in plan["regions"])
    assert all(not r["context_complete"] for r in plan["regions"])
    state = all_unresolved(plan)
    assert state["unresolved_ids"] == [w["id"] for w in source["words"]]


def test_side_by_side_blocks_with_ocr_drift_and_vertical_blocks() -> None:
    source = page()
    for row in range(4):
        for offset in (10, 310):
            add_word(source, offset, 20 + row * 20, width=50)
            add_word(source, offset + 60, 22 + row * 20, width=40)
    for row in range(3):
        add_word(source, 10, 300 + row * 20, "lower prose", width=100)
    plan = split(source)
    assert len(plan["regions"]) == 3
    assert sorted(len(r["source_ids"]) for r in plan["regions"]) == [3, 8, 8]
    assert Counter(i for r in plan["regions"] for i in r["source_ids"]) == Counter(w["id"] for w in source["words"])
    assert all_unresolved(plan)["tables"] == []


def test_false_positive_prose_region_does_not_admit_semantics() -> None:
    source = page()
    for row in range(4):
        for x in (10, 90):
            add_word(source, x, 20 + row * 20, "Sentence ends.", width=60)
    plan = split(source)
    assert len(plan["regions"]) == 1
    assert all_unresolved(plan)["tables"] == []


def test_capacity_cut_single_band_is_explicit_and_preserves_global_ids() -> None:
    source = page()
    for index in range(8):
        add_word(source, index * 30, 20)
    plan = split(source, max_words=3)
    assert all(r["boundary"] == "capacity_words" for r in plan["regions"])
    assert all_unresolved(plan)["unresolved_ids"] == [w["id"] for w in source["words"]]


def test_native_budget_is_atomic_and_uses_legacy_limit() -> None:
    source = page()
    add_grid(source, 20)
    plan = split(source, max_words=2)
    assert len(plan["regions"]) == 1
    assert len(plan["regions"][0]["source_ids"]) == 4
    assert plan["regions"][0]["boundary"] == "atomic_native"


def test_invalid_native_and_missing_or_duplicate_outputs_fail_closed() -> None:
    source = page()
    add_grid(source, 20)
    broken = deepcopy(source)
    broken["vector_candidates"][0]["spans"].pop()
    with pytest.raises(ValueError, match="complete table tiling"):
        split(broken)
    plan = split(source)
    with pytest.raises(ValueError, match="Missing"):
        compose(plan, {})
    state = unresolved_region(plan["regions"][0])
    state["unresolved_ids"].append(state["unresolved_ids"][0])
    with pytest.raises(ValueError, match="conservation"):
        compose(plan, {"r0": state})


def test_source_mutation_and_page_invalidity_reject_composition() -> None:
    source = page()
    add_word(source, 10, 20)
    plan = split(source)
    plan["regions"][0]["source"]["words"] = deepcopy(plan["regions"][0]["source"]["words"])
    plan["regions"][0]["source"]["words"][0]["text"] = "invented"
    with pytest.raises(ValueError, match="differs"):
        all_unresolved(plan)
    source["words"].append(deepcopy(source["words"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        split(source)


@pytest.mark.parametrize("kwargs", [{"max_words": 0}, {"max_characters": 16001}, {"crop_padding": float("nan")}])
def test_bad_configuration_fails_closed(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r"budget|padding"):
        split(page(), **kwargs)


def test_empty_page_is_complete_without_regions() -> None:
    plan = split(page())
    assert plan["regions"] == []
    assert compose(plan, {})["unresolved_ids"] == []


@pytest.mark.parametrize("columns", [3, 4, 5])
def test_sparse_leading_and_repeated_column_gaps_preserve_one_table_region(columns: int) -> None:
    source = page()
    for row in range(5):
        for column in range(columns):
            add_word(source, 10 + column * 110, 20 + row * 33, f"value {row} {column}", width=45)
            source["words"][-1]["bbox"][3] = 28 + row * 33
    add_word(source, 10, 700, "Footer")
    plan = split(source)
    table_regions = [r for r in plan["regions"] if any(w["bbox"][1] < 200 for w in r["source"]["words"])]
    assert len(table_regions) == 1
    assert len(table_regions[0]["source_ids"]) == columns * 5
    assert all_unresolved(plan)["unresolved_ids"] == [w["id"] for w in source["words"]]


def test_side_by_side_multicolumn_tables_keep_their_internal_gutters() -> None:
    source = page()
    for row in range(5):
        for block_x in (10, 330):
            for column in range(2):
                add_word(source, block_x + column * 70, 20 + row * 20, width=35)
    plan = split(source)
    assert len(plan["regions"]) == 2
    assert all(r["boundary"] == "wide_gutter" for r in plan["regions"])
    assert all(len(r["source_ids"]) == 10 for r in plan["regions"])
