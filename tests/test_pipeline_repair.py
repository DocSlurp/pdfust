"""Source ownership and atomic repair contract tests."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_repair import apply, operations, packet, validate


def fixture(rows: list[list[Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    words = []
    cells = []
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            ids = []
            if text:
                ident = f"w{r}{c}"
                words.append({"id": ident, "text": text, "bbox": [c * 100, r * 12, c * 100 + 30, r * 12 + 10]})
                ids = [ident]
            cells.append({"source_ids": ids, "role": "unknown"})
    cols = len(rows[0])
    table = {
        "row_count": len(rows),
        "col_count": cols,
        "values": rows,
        "cells": cells,
        "spans": [
            {"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(len(rows)) for c in range(cols)
        ],
    }
    return {"words": words, "page_size": [300, 300], "vector_candidates": []}, {"tables": [table], "unresolved_ids": []}


def test_wrapped_row_merge_preserves_sources() -> None:
    page, state = fixture([["Item", "10"], ["continued", ""], ["Other", "20"]])
    ops = operations(page, state)
    op = next(o for o in ops if o["kind"] == "merge_rows")
    updated = apply(page, state, op)
    assert updated["tables"][0]["values"] == [["Item continued", "10"], ["Other", "20"]]
    validate(page, updated)
    assert state["tables"][0]["row_count"] == 3


def test_disjoint_complete_rows_have_no_merge() -> None:
    page, state = fixture([["First", "10"], ["Second", "20"]])
    assert all(o["kind"] != "merge_rows" for o in operations(page, state))


def test_far_hanging_row_has_no_merge() -> None:
    page, state = fixture([["First", "10"], ["Second", ""]])
    page["words"][-1]["bbox"][1:] = [100, 30, 110]
    assert all(o["kind"] != "merge_rows" for o in operations(page, state))


def test_rejection_retains_outside_sources() -> None:
    page, state = fixture([["First", "10"], ["Second", "20"]])
    page["words"].append({"id": "outside", "text": "Note", "bbox": [0, 80, 20, 90]})
    state["unresolved_ids"].append("outside")
    op = next(o for o in operations(page, state) if o["kind"] == "reject_table")
    updated = apply(page, state, op)
    assert updated["tables"] == []
    assert set(updated["unresolved_ids"]) == {w["id"] for w in page["words"]}


def test_duplicate_and_invented_value_rejected_atomically() -> None:
    page, state = fixture([["Item", "10"], ["continued", ""]])
    op = next(o for o in operations(page, state) if o["kind"] == "merge_rows")
    before = deepcopy(state)
    bad = deepcopy(op)
    bad["state"]["unresolved_ids"].append("w00")
    with pytest.raises(ValueError, match="admitted"):
        apply(page, state, bad)
    assert state == before
    bad = deepcopy(op)
    bad["state"]["tables"][0]["values"][0][0] = "Invented"
    with pytest.raises(ValueError, match="admitted"):
        apply(page, state, bad)
    assert state == before


def test_validate_duplicate_owner() -> None:
    page, state = fixture([["First", "10"]])
    state["unresolved_ids"].append("w00")
    with pytest.raises(ValueError, match="exactly one owner"):
        validate(page, state)


def test_split_multiline_row() -> None:
    page, state = fixture([["First", "10"], ["Second", "20"]])
    cells = state["tables"][0]["cells"]
    table = state["tables"][0]
    table.update(
        row_count=1,
        values=[["First Second", "10 20"]],
        cells=[
            {"source_ids": cells[c]["source_ids"] + cells[c + 2]["source_ids"], "role": "unknown"} for c in range(2)
        ],
        spans=[{"row": 0, "column": c, "row_span": 1, "column_span": 1} for c in range(2)],
    )
    op = next(o for o in operations(page, state) if o["kind"] == "split_row")
    assert apply(page, state, op)["tables"][0]["values"] == [["First", "10"], ["Second", "20"]]


def test_vector_prior_and_stale_operation() -> None:
    page, state = fixture([["Item", "10"], ["continued", ""]])
    op = operations(page, state)[0]
    page["vector_candidates"] = [deepcopy(state["tables"][0])]
    assert operations(page, state) == []
    with pytest.raises(ValueError, match="admitted"):
        apply(page, state, op)
    page["vector_candidates"] = []
    state["unresolved_ids"].reverse()
    changed = deepcopy(state)
    changed["tables"][0]["notes"] = "new snapshot"
    with pytest.raises(ValueError, match="Stale"):
        apply(page, changed, op)


def test_packet_source_projection_and_context_ablation() -> None:
    page, state = fixture([["Heading", "Value"], ["Item", "10"], ["continued", ""], ["Other", "20"]])
    page.update(gold={"rows": 999}, family="secret", filename="secret.pdf")
    ops = operations(page, state)
    small = json.loads(packet(page, state, ops, context_rows=1, availability_legend=False))
    large = json.loads(packet(page, state, ops, context_rows=3))
    assert "availability" not in small
    assert large["availability"]["source_pixels"] == "not supplied by this text packet"
    assert max(len(c["rows"]) for c in small["row_context"]) == 1
    assert max(len(c["rows"]) for c in large["row_context"]) == 3
    assert "secret" not in json.dumps(large)
    assert "999" not in json.dumps(large)


def test_merged_native_covered_values_are_none() -> None:
    page, state = fixture([["Title", ""]])
    table = state["tables"][0]
    table["spans"] = [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}]
    table["values"][0][1] = None
    page["vector_candidates"] = [deepcopy(table)]
    validate(page, state)
    assert operations(page, state) == []
    table["values"][0][1] = ""
    with pytest.raises(ValueError, match="span-covered"):
        validate(page, state)
