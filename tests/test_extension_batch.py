"""Independent batch decisions preserve exact complete source ownership."""

# ruff: noqa: SLF001
from copy import deepcopy
from typing import Any

import pytest
from bench import extension_batch as batch
from bench import extension_local as local
from bench import extension_protocol as protocol
from bench import pipeline_repair as repair


def fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    words = [
        {
            "id": f"w{i}",
            "text": f"literal{i}",
            "bbox": [i % 2 * 20 + 1, i // 2 * 20 + 1, i % 2 * 20 + 10, i // 2 * 20 + 8],
        }
        for i in range(16)
    ]
    source = {"words": words, "page_size": [40, 160]}
    current = {
        "tables": [
            {
                "row_count": 8,
                "col_count": 2,
                "bbox": [0, 0, 40, 160],
                "cells": [{"source_ids": [w["id"]], "role": "unknown"} for w in words],
                "values": [[f"literal{i}", f"literal{i + 1}"] for i in range(0, 16, 2)],
                "spans": [{"row": i // 2, "column": i % 2, "row_span": 1, "column_span": 1} for i in range(16)],
            }
        ],
        "unresolved_ids": [],
    }
    correct = deepcopy(current)
    for ident, destination in [("w1", (0, 0)), ("w13", (0, 12))]:
        current = local._move(source, current, ident, destination)
    return source, current, correct


def response(packet: dict[str, Any], choice: str) -> dict[str, Any]:
    return {
        "model": "typesafe/jev-1.13-20260917",
        "answers": {
            name: {
                "type": "choice",
                "choice": choice,
                "probabilities": {a: int(a == choice) for a in packet["frozen"]["questions"][name]["alternatives"]},
            }
            for name in packet["question_ids"]
        },
    }


def test_independent_batch_equals_matched_singles() -> None:
    source, current, _ = fixture()
    frozen = batch.prepare(source, current, [], max_alternatives=2)
    assert frozen["applicable"]
    assert len(frozen["questions"]) == 2
    packet = batch.build_request(frozen, "typesafe/jev-1.13")
    for choice in ("keep", "a1"):
        result = batch.parse_choice(response(packet, choice), packet)
        choices = {}
        for single in batch.split_requests(packet):
            assert single["body"]["state"] == packet["body"]["state"]
            parsed = batch.parse_choice(response(single, choice), single)
            choices.update({name: answer["choice"] for name, answer in parsed["answers"].items()})
        assert batch.compose(frozen, choices) == result["selected_state"]
        assert result["all_unchanged"] == (choice == "keep")
        repair.validate(source, result["selected_state"])
    assert batch.compose(frozen, dict.fromkeys(frozen["questions"], "keep")) == current


def test_variants_and_bounded_shared_context() -> None:
    source, current, _ = fixture()
    a = batch.prepare(source, current, [], max_alternatives=2, max_words=2)
    b = batch.prepare(source, current, [], max_alternatives=2, max_words=2, variant="readable")
    assert a["questions"] == b["questions"]
    assert a["evidence"] == b["evidence"]
    assert a["evidence"]["source_supplied_words"] == 2
    assert a["evidence"]["source_omitted_words"] == 14
    assert a["evidence"]["context_omitted_words"] > 0
    assert "omitted" in b["text"]


def test_correct_unchanged_control_and_single_dispute_do_not_request_batch() -> None:
    source, _, correct = fixture()
    frozen = batch.prepare(source, correct, [correct])
    assert not frozen["applicable"]
    assert batch.build_request(frozen, "typesafe/jev-1.13")["body"] is None
    current = local._move(source, correct, "w1", (0, 0))
    assert not batch.prepare(source, current, [], max_alternatives=2)["applicable"]


def test_strict_response_and_authentication() -> None:
    source, current, _ = fixture()
    packet = batch.build_request(batch.prepare(source, current, [], max_alternatives=2), "typesafe/jev-1.13")
    raw = response(packet, "a1")
    raw["answers"].pop("q1")
    with pytest.raises(ValueError, match="identities"):
        batch.parse_choice(raw, packet)
    raw = response(packet, "a1")
    raw["answers"]["q0"]["probabilities"]["invented"] = 0
    with pytest.raises(ValueError, match="distribution"):
        batch.parse_choice(raw, packet)
    raw = response(packet, "keep")
    raw["model"] = "other/model"
    with pytest.raises(ValueError, match="identity"):
        batch.parse_choice(raw, packet)
    packet["body"]["state"] += "changed"
    with pytest.raises(ValueError, match="modified"):
        batch.parse_choice(raw, packet)


def test_atomic_conflict_and_destination_validation() -> None:
    source, current, _ = fixture()
    frozen = batch.prepare(source, current, [], max_alternatives=2)
    altered = deepcopy(frozen)
    altered["questions"]["q1"]["footprint"] = altered["questions"]["q0"]["footprint"]
    altered.pop("freeze_sha256")
    altered["freeze_sha256"] = protocol.digest(altered)
    with pytest.raises(ValueError, match="footprints conflict"):
        batch.compose(altered, {"q0": "a1", "q1": "a1"})
    altered = deepcopy(frozen)
    altered["questions"]["q0"]["destinations"]["a1"] = None
    altered.pop("freeze_sha256")
    altered["freeze_sha256"] = protocol.digest(altered)
    with pytest.raises(ValueError, match="declared destination"):
        batch.compose(altered, {"q0": "a1"})
    assert frozen["current"] == current


def test_reject_authored_values_and_evidence_overflow() -> None:
    source, current, _ = fixture()
    bad = deepcopy(current)
    bad["tables"][0]["values"][0][0] = "authored"
    with pytest.raises(ValueError, match="literal cell sources"):
        batch.prepare(source, bad, [])
    with pytest.raises(protocol.EvidenceCapacityError, match="byte cap"):
        batch.prepare(source, current, [], max_alternatives=2, max_bytes=10)


def test_vercel_d1_preserves_all_question_identities() -> None:
    source, current, _ = fixture()
    packet = batch.build_request(batch.prepare(source, current, [], max_alternatives=2), "liquid/d1", provider="vercel")
    raw = response(packet, "keep")
    raw["model"] = "liquid/d1"
    for name, answer in raw["answers"].items():
        answer["name"] = name
    assert batch.parse_choice(raw, packet)["all_unchanged"]
    singles = batch.split_requests(packet)
    for single in singles:
        assert len(single["body"]["questions"]) == 1
        assert single["body"]["input"] == packet["body"]["input"]
    raw["answers"]["q1"]["name"] = "q0"
    with pytest.raises(ValueError, match="exactly echo"):
        batch.parse_choice(raw, packet)
