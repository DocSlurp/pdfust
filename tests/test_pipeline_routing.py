"""Frozen routing responds to source geometry, independent of metadata."""

from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_routing import route


def source(rows: list[list[str]]) -> tuple[dict[str, Any], dict[str, Any]]:
    words, cells = [], []
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            ids = []
            if text:
                ids = [f"w{r}-{c}"]
                words.append({"id": ids[0], "text": text, "bbox": [100 * c, 12 * r, 100 * c + 30, 12 * r + 10]})
            cells.append({"source_ids": ids, "role": "unknown"})
    cols = len(rows[0])
    table = {
        "row_count": len(rows),
        "col_count": cols,
        "cells": cells,
        "values": rows,
        "spans": [
            {"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(len(rows)) for c in range(cols)
        ],
    }
    return {"words": words, "page_size": [300, 300], "vector_candidates": []}, {"tables": [table], "unresolved_ids": []}


def test_no_table_escalates() -> None:
    page, candidate = source([["First", "10"], ["Second", "20"]])
    empty = {"tables": [], "unresolved_ids": [w["id"] for w in page["words"]]}
    selected = route(page, empty, [empty, candidate])
    assert selected["action"] == "assemble"
    assert selected["context_rows"] == 3
    assert selected["image_edge"] == 512


def test_native_grid_keeps_cheap_path() -> None:
    page, state = source([["First", "10"], ["Second", "20"]])
    page["vector_candidates"] = [deepcopy(state["tables"][0])]
    assert route(page, state, [state]) == {
        "action": "keep_native",
        "reasons": ["All provisional tables match immutable observed vector grids."],
        "context_rows": 1,
        "image_edge": 256,
    }


def test_wrapping_gets_more_context_but_row_repair() -> None:
    page, state = source([["First", "10"], ["continued", ""]])
    selected = route(page, state, [state])
    assert selected["action"] == "repair"
    assert (selected["context_rows"], selected["image_edge"]) == (3, 512)


def test_small_source_text_gets_larger_pixels() -> None:
    page, state = source([["First", "10"], ["Second", "20"]])
    for word in page["words"]:
        word["bbox"][3] = word["bbox"][1] + 6
    assert route(page, state, [state])["image_edge"] == 1024


def test_column_conflict_escalates() -> None:
    page, state = source([["First", "10"], ["Second", "20"]])
    alternative = deepcopy(state)
    ids = [i for c in alternative["tables"][0]["cells"] for i in c["source_ids"]]
    alternative["tables"] = [
        {
            "row_count": 1,
            "col_count": 1,
            "cells": [{"source_ids": ids, "role": "unknown"}],
            "values": [[" ".join(w["text"] for w in page["words"])]],
            "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}],
        }
    ]
    assert route(page, state, [state, alternative])["action"] == "assemble"


def test_labels_and_id_spelling_do_not_change_route() -> None:
    page, state = source([["First", "10"], ["Second", "20"]])
    expected = route(page, state, [state])
    page.update(family="irrelevant", filename="irrelevant.pdf", gold={"tables": []})
    names = {w["id"]: f"arbitrary-{i}" for i, w in enumerate(page["words"])}
    for word in page["words"]:
        word["id"] = names[word["id"]]
    for cell in state["tables"][0]["cells"]:
        cell["source_ids"] = [names[i] for i in cell["source_ids"]]
    assert route(page, state, [state]) == expected


def test_bounded_candidate_admission() -> None:
    page, state = source([["First", "10"]])
    with pytest.raises(ValueError, match="admission"):
        route(page, state, [state] * 25)


def test_long_multiline_overlap_escalates() -> None:
    page, state = source([["First", "10"], ["Second", "20"]])
    page["words"] = [w for w in page["words"] if w["id"] != "w1-0"]
    ids = []
    for i in range(12):
        ident = f"long-{i}"
        ids.append(ident)
        top = 6 + 12 * (i // 4)
        page["words"].append({"id": ident, "text": "word", "bbox": [i % 4 * 10, top, i % 4 * 10 + 8, top + 10]})
    state["tables"][0]["cells"][2]["source_ids"] = ids
    state["tables"][0]["values"][1][0] = " ".join("word" for _ in ids)
    result = route(page, state, [state])
    assert result["action"] == "assemble"
    assert any("overlaps" in reason for reason in result["reasons"])


def test_reversed_provisional_columns_escalate() -> None:
    page, state = source([["First", "10"], ["Second", "20"]])
    for word in page["words"]:
        word["bbox"][0], word["bbox"][2] = 200 - word["bbox"][2], 200 - word["bbox"][0]
    assert route(page, state, [state])["action"] == "assemble"
