"""Complete source ownership and local single-word arbitration contracts."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench import extension_local as local
from bench import pipeline_repair as repair
from bench.extension_protocol import EvidenceCapacityError


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    source = {
        "page_size": [100, 100],
        "words": [
            {"id": "w0", "text": "label", "bbox": [1, 1, 10, 8]},
            {"id": "w1", "text": "value", "bbox": [21, 1, 30, 8]},
            {"id": "w2", "text": "other", "bbox": [1, 21, 10, 28]},
            {"id": "w3", "text": "amount", "bbox": [21, 21, 30, 28]},
        ],
    }
    table = {
        "row_count": 2,
        "col_count": 2,
        "bbox": [0, 0, 40, 40],
        "values": [["label", "value"], ["other", "amount"]],
        "cells": [{"source_ids": [f"w{i}"], "role": "unknown"} for i in range(4)],
        "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)],
    }
    return source, {"tables": [table], "unresolved_ids": []}


def test_geometry_alone_proposes_valid_single_word_moves() -> None:
    source, current = fixture()
    current["tables"][0]["cells"][0]["source_ids"].append("w1")
    current["tables"][0]["cells"][1]["source_ids"] = []
    current["tables"][0]["values"][0] = ["label value", ""]
    frozen = local.prepare(source, current, [])
    assert frozen["applicable"]
    assert frozen["evidence"]["focus"] == 1
    assert 2 <= len(frozen["alternatives"]) <= 5
    assert frozen["alternatives"]["keep"] == current
    before = local._owners(current)  # noqa: SLF001 - direct ownership invariant assertion.
    for state in frozen["alternatives"].values():
        repair.validate(source, state)
        after = local._owners(state)  # noqa: SLF001
        assert sum(before[i] != after[i] for i in before) <= 1
        assert state["tables"][0]["spans"] == current["tables"][0]["spans"]
    assert any(state["tables"][0]["values"][0] == ["label", "value"] for state in frozen["alternatives"].values())


def test_correct_geometry_with_no_disagreement_is_no_request() -> None:
    source, current = fixture()
    frozen = local.prepare(source, current, [current])
    assert not frozen["applicable"]
    assert local.build_request(frozen, "typesafe/jev-1.13")["body"] is None
    assert frozen["alternatives"] == {"keep": current}


def test_missing_table_does_not_invent_topology() -> None:
    source, table = fixture()
    current = {"tables": [], "unresolved_ids": [w["id"] for w in source["words"]]}
    frozen = local.prepare(source, current, [table])
    assert not frozen["applicable"]
    assert frozen["shape_disagreement_count"] == 1


def test_variants_share_identical_successors_and_omit_context_explicitly() -> None:
    source, current = fixture()
    other = deepcopy(current)
    other["tables"][0]["cells"][0]["source_ids"] = ["w0", "w1"]
    other["tables"][0]["cells"][1]["source_ids"] = []
    other["tables"][0]["values"][0] = ["label value", ""]
    a = local.prepare(source, current, [other], variant="arrays", max_words=1)
    b = local.prepare(source, current, [other], variant="readable", max_words=1)
    assert a["alternatives"] == b["alternatives"]
    assert a["evidence"]["source_supplied_words"] == 1
    assert a["evidence"]["source_omitted_words"] == 3
    assert "omitted" in b["text"]
    assert json.loads(a["text"])["focus"] == a["evidence"]["words"][0][0]


def test_local_parse_native_keep_and_alternative_preserve_full_state() -> None:
    source, current = fixture()
    current["tables"][0]["cells"][0]["source_ids"].append("w1")
    current["tables"][0]["cells"][1]["source_ids"] = []
    current["tables"][0]["values"][0] = ["label value", ""]
    packet = local.build_request(local.prepare(source, current, []), "typesafe/jev-1.13")
    for choice in ["keep", "a1"]:
        raw = {
            "model": "typesafe/jev-1.13-20260917",
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": {a: int(a == choice) for a in packet["frozen"]["alternatives"]},
                }
            },
        }
        selected = local.parse_choice(raw, packet)
        assert selected["unchanged"] == (choice == "keep")
        repair.validate(source, selected["selected_state"])
    packet["frozen"]["alternatives"]["a1"]["unresolved_ids"].append("invented")
    with pytest.raises(ValueError, match="modified"):
        local.parse_choice(raw, packet)


def test_local_rejects_authored_values_and_over_capacity() -> None:
    source, current = fixture()
    other = deepcopy(current)
    other["tables"][0]["values"][0][0] = "invented"
    with pytest.raises(ValueError, match="literal cell sources"):
        local.prepare(source, current, [other])
    current["tables"][0]["cells"][0]["source_ids"].append("w1")
    current["tables"][0]["cells"][1]["source_ids"] = []
    current["tables"][0]["values"][0] = ["label value", ""]
    with pytest.raises(EvidenceCapacityError, match="byte cap"):
        local.prepare(source, current, [], max_bytes=10)
