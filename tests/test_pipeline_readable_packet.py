"""Readable packet invariants and direct semantic cell visibility, CPU only."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, cast

import bench.pipeline_readable_packet as module
import pytest
from bench.pipeline_assembly import _clean_table, validate
from bench.pipeline_readable_packet import INSTRUCTIONS, decode, packet, payload


def fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    words: list[dict[str, Any]] = [
        {"id": f"source-{i}", "text": text, "bbox": [i + 0.123456789012345, -0.0, i + 1.0, 10], "line": [2, i // 2]}
        for i, text in enumerate(["Name", "Detail", "Oak", "long", "tail", "東京", "Note"])
    ]
    del words[-1]["line"]
    lookup = {w["id"]: w for w in words}
    page: dict[str, Any] = {"page_size": [0, 0, 300, 500], "words": words}
    table: dict[str, Any] = {
        "row_count": 3,
        "col_count": 2,
        "cells": [
            {"source_ids": ids}
            for ids in [["source-0", "source-1"], [], ["source-2"], ["source-3", "source-4"], ["source-5"], []]
        ],
        "spans": [
            {"row": 0, "column": 0, "row_span": 1, "column_span": 2},
            *[{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in (1, 2) for c in range(2)],
        ],
    }
    table = _clean_table(table, lookup)
    candidates: list[dict[str, Any]] = [
        {"id": "c0", "tables": [], "unresolved_ids": [w["id"] for w in words]},
        {"id": "c1", "tables": [table], "unresolved_ids": ["source-6"]},
        {"id": "c2", "tables": [deepcopy(table)], "unresolved_ids": ["source-6"]},
    ]
    return page, candidates


def test_roundtrip_preserves_exact_literals_geometry_lines_spans_and_ownership() -> None:
    page, candidates = fixture()
    text = packet(page, candidates)
    decoded = decode(json.loads(text[len(INSTRUCTIONS) :]))
    assert decoded == {"source": page, "candidates": candidates}
    assert json.dumps(decoded["source"]) == json.dumps(page)
    for candidate in decoded["candidates"]:
        validate(decoded["source"], candidate)


def test_composed_cells_and_tables_are_readable_once_and_all_choices_remain() -> None:
    page, candidates = fixture()
    data = payload(page, candidates)
    assert len(data["tables"]) == 1
    assert list(data["cells"].values()).count({"value": "long tail", "source_ids": ["source-3", "source-4"]}) == 1
    assert data["tables"]["table0"]["rows"][0][1] is None
    assert any(cell["value"] == "" and cell["source_ids"] == [] for cell in data["cells"].values())
    assert data["candidates"][1]["tables"] == data["candidates"][2]["tables"]
    assert [c["id"] for c in data["candidates"]] == ["c0", "c1", "c2"]
    assert data["words"][3] == ["source-3", "long", page["words"][3]["bbox"], [2, 1]]


def test_ordered_cell_sources_are_not_sorted_or_collapsed() -> None:
    page, candidates = fixture()
    table = candidates[1]["tables"][0]
    table["cells"][3]["source_ids"].reverse()
    table["values"][1][1] = "tail long"
    decoded = decode(payload(page, candidates))
    assert decoded["candidates"][1]["tables"][0]["values"][1][1] == "tail long"
    assert decoded["candidates"][2]["tables"][0]["values"][1][1] == "long tail"
    assert len(payload(page, candidates)["tables"]) == 2


def test_private_annotations_are_not_evidence_and_input_is_unchanged() -> None:
    page, candidates = fixture()
    original = deepcopy((page, candidates))
    expected = packet(page, candidates)
    page.update(filename="SECRET", family="SECRET", gold="SECRET")
    for word in page["words"]:
        word["expected_cell"] = "SECRET"
    for candidate in candidates:
        candidate["description"] = "SECRET"
        candidate["mechanism"] = "SECRET"
    assert packet(page, candidates) == expected
    assert "SECRET" not in packet(page, candidates)
    clean_page, clean_candidates = fixture()
    assert (clean_page, clean_candidates) == original
    before = deepcopy((page, candidates))
    packet(page, candidates)
    assert (page, candidates) == before


@pytest.mark.parametrize("kind", ["duplicate", "value", "id", "span"])
def test_invalid_complete_candidates_are_refused(kind: str) -> None:
    page, candidates = fixture()
    if kind == "duplicate":
        candidates[1]["unresolved_ids"].append("source-0")
    elif kind == "value":
        candidates[1]["tables"][0]["values"][1][1] = "fabricated"
    elif kind == "id":
        candidates[1]["id"] = "not-stable"
    else:
        candidates[1]["tables"][0]["spans"].pop()
    with pytest.raises(ValueError, match=r"conservation|owned source|consecutive|tiling"):
        packet(page, candidates)


def test_full_context_and_character_bound_are_enforced_without_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    page, candidates = fixture()
    with pytest.raises(ValueError, match="full-page"):
        packet(page, candidates, context_style="selected")
    full = packet(page, candidates)
    monkeypatch.setattr(module, "MAX_PACKET_CHARACTERS", len(full))
    assert packet(page, candidates) == full
    monkeypatch.setattr(module, "MAX_PACKET_CHARACTERS", len(full) - 1)
    with pytest.raises(ValueError, match="no partial context"):
        packet(page, candidates)


def test_duplicate_source_input_and_excess_candidates_are_refused() -> None:
    page, candidates = fixture()
    page["words"].append(deepcopy(page["words"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        packet(page, candidates)
    page, candidates = fixture()
    with pytest.raises(ValueError, match="alternative count"):
        packet(page, candidates * 9)


@pytest.mark.parametrize("limit", [0, -1, 128001, True, 1.5])
def test_explicit_larger_packet_budget_is_still_bounded(limit: object) -> None:
    page, candidates = fixture()
    with pytest.raises(ValueError, match="admission"):
        packet(page, candidates, max_characters=cast("int", limit))


def test_explicit_packet_budget_preserves_complete_evidence() -> None:
    page, candidates = fixture()
    full = packet(page, candidates, max_characters=80000)
    assert full == packet(page, candidates)
    with pytest.raises(ValueError, match="no partial context"):
        packet(page, candidates, max_characters=len(full) - 1)
