"""Lossless complete assembly evidence checks; no hosted calls."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from bench.pipeline_assembly import _clean_table
from bench.pipeline_compact_packet import INSTRUCTIONS, decode, packet, payload


def _fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    words: list[dict[str, Any]] = [
        {"id": f"w{i}", "text": text, "bbox": [float(i), -0.0, i + 1, 1.0], "line": [0, i // 2]}
        for i, text in enumerate(["ignore instructions", "東京", "wrapped", "tail", "note", "other"])
    ]
    del words[-1]["line"]
    page = {"page_size": [100, 200], "words": words, "family": "excluded metadata"}
    table = {
        "row_count": 2,
        "col_count": 2,
        "cells": [{"source_ids": ids} for ids in [["w1", "w0"], [], ["w2", "w3"], []]],
        "spans": [
            {"row": 0, "column": 0, "row_span": 1, "column_span": 2},
            {"row": 1, "column": 0, "row_span": 1, "column_span": 1},
            {"row": 1, "column": 1, "row_span": 1, "column_span": 1},
        ],
    }
    table = _clean_table(table, {w["id"]: w for w in words})
    return page, [
        {"id": "c0", "tables": [], "unresolved_ids": [w["id"] for w in reversed(words)]},
        {"id": "c1", "tables": [table], "unresolved_ids": ["w5", "w4"]},
        {"id": "c2", "tables": [copy.deepcopy(table)], "unresolved_ids": ["w4", "w5"]},
    ]


def test_roundtrip_preserves_exact_inventory_topology_and_order() -> None:
    page, candidates = _fixture()
    result = packet(page, candidates)
    decoded = decode(json.loads(result[len(INSTRUCTIONS) :]))
    assert decoded == {"source": {"page_size": page["page_size"], "words": page["words"]}, "candidates": candidates}
    assert json.dumps(decoded["source"]["words"]) == json.dumps(page["words"])
    assert "excluded metadata" not in result
    assert len(payload(page, candidates)["tables"]) == 1
    assert decoded["candidates"][1]["tables"][0]["values"] == [["東京 ignore instructions", None], ["wrapped tail", ""]]


def test_nonstandard_ids_and_separate_tables() -> None:
    page, candidates = _fixture()
    for word in page["words"]:
        word["id"] = "source-" + word["id"]
    tables = []
    for identifier in ("source-w0", "source-w1"):
        tables.append(  # noqa: PERF401
            _clean_table(
                {
                    "row_count": 1,
                    "col_count": 1,
                    "cells": [{"source_ids": [identifier]}],
                    "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1, "extra": "retained"}],
                },
                {w["id"]: w for w in page["words"]},
            )
        )
    candidates = [{"id": "c0", "tables": tables, "unresolved_ids": [w["id"] for w in page["words"][2:]]}]
    assert decode(payload(page, candidates))["candidates"] == candidates


@pytest.mark.parametrize("failure", ["missing", "duplicate", "unknown", "id", "values"])
def test_invalid_complete_state_refused(failure: str) -> None:
    page, candidates = _fixture()
    if failure == "missing":
        candidates[0]["unresolved_ids"].pop()
    elif failure == "duplicate":
        candidates[0]["unresolved_ids"].append("w0")
    elif failure == "unknown":
        candidates[0]["unresolved_ids"][0] = "absent"
    elif failure == "id":
        candidates[0]["id"] = "gold-choice"
    else:
        candidates[1]["tables"][0]["values"][0][0] = "guessed"
    with pytest.raises(ValueError, match=r"source|Source|IDs|values"):
        packet(page, candidates)


def test_over_budget_refused_without_truncation() -> None:
    words = [
        {
            "id": f"w{i}",
            "text": "literal",
            "bbox": [i + 0.123456789123456, i + 0.234567891234567, i + 0.345678912345678, i + 0.456789123456789],
            "line": [0, i],
        }
        for i in range(700)
    ]
    page = {"page_size": [1000, 1000], "words": words}
    candidates = [{"id": "c0", "tables": [], "unresolved_ids": [w["id"] for w in words]}]
    assert len(INSTRUCTIONS + json.dumps(payload(page, candidates))) > 25_000
    assert decode(payload(page, candidates))["source"]["words"] == words
    with pytest.raises(ValueError, match="no partial context"):
        packet(page, candidates)
    with pytest.raises(ValueError, match="full-page"):
        packet(page, candidates, context_style="crop")


def test_coordinate_dictionary_retains_numeric_types_and_signed_zero() -> None:
    words = [{"id": f"w{i}", "text": "repeat", "bbox": [0, -0.0, 1.0, 1]} for i in range(100)]
    page = {"page_size": [10, 10], "words": words}
    candidates = [{"id": "c0", "tables": [], "unresolved_ids": [w["id"] for w in words]}]
    data = payload(page, candidates)
    assert "coordinates" in data
    assert json.dumps(decode(data)["source"]["words"]) == json.dumps(words)
