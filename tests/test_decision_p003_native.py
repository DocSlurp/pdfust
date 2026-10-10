"""Typed native decisions use bounded local evidence and atomic full-menu replay."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.decision_p003_boundaries import parse, request
from bench.decision_p003_native import apply_decision_batches, decision_batches, parse_decision_batch
from bench.decision_p003_offline import synthetic
from test_pipeline_repair import fixture


def response(body: dict[str, Any], *, rounded: bool = False) -> dict[str, Any]:
    return {
        "answers": {
            ident: {
                "type": "choice",
                "choice": "join",
                "probabilities": {"join": 0.89 if rounded else 0.9, "split": 0.1, "unresolved": 0},
                "confidence": 0.123,
            }
            for ident in body["questions"]
        }
    }


def test_native_batches_local_union_and_text_first_image() -> None:
    page, state = synthetic(129)
    menu, batches = decision_batches(page, state, "typesafe/jev-1.13", "data:image/png;base64,fixture")
    assert len(menu["boundaries"]) == 128
    assert len(batches) == 8
    assert all(len(body["questions"]) == 16 for body in batches)
    assert set(batches[0]) == {"model", "state", "questions"}
    first = json.loads(batches[0]["state"][0])
    assert len(first["words"]) < len(menu["words"]) / 2
    assert set(first["observations"]) == set(batches[0]["questions"])
    assert first["words"][0] == menu["words"][0]
    last = json.loads(batches[-1]["state"][0])
    assert last["words"][0][0] > 0
    assert all(w[0] >= last["words"][0][0] for w in last["words"])
    assert batches[0]["state"][1] == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,fixture", "detail": "high"},
    }
    assert batches[0]["questions"]["t0b0"]["type"] == "choice"
    assert set(batches[0]["questions"]["t0b0"]["criteria"]) == {"split", "join", "unresolved"}


def test_native_rounded_scores_confidence_and_atomic_combination() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    original = deepcopy(state)
    menu, batches = decision_batches(page, state, "typesafe/jev-1.13", max_questions=1)
    results = [response(body, rounded=True) for body in batches]
    parsed = parse_decision_batch(batches[0], results[0])["t0b0"]
    assert parsed["raw_probabilities"]["join"] == 0.89
    assert parsed["probabilities"]["join"] == pytest.approx(0.89 / 0.99)
    assert parsed["normalization_delta"] == pytest.approx(-0.01)
    assert parsed["raw_confidence"] == 0.123
    updated, audit = apply_decision_batches(page, state, menu, batches, results)
    assert updated["tables"][0]["values"] == [["Record wrap", "20"], ["Last", "30"]]
    assert audit["native_decisions"]["t0b0"] == parsed
    assert state == original
    for incomplete in (results[:-1], [results[0], {"answers": {}}]):
        with pytest.raises(ValueError, match=r"incomplete|exact batch"):
            apply_decision_batches(page, state, menu, batches, incomplete)
        assert state == original


def test_native_rejects_probability_shape_rounding_choice_and_batch_drift() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    menu, batches = decision_batches(page, state, "typesafe/jev-1.13", max_questions=1)
    body = batches[0]
    for field, value in (
        ("probabilities", {"join": 0.8, "split": 0.1, "unresolved": 0}),
        ("choice", "split"),
        ("type", "boolean"),
        ("probabilities", {"join": True, "split": 0, "unresolved": 0}),
    ):
        invalid = response(body)
        invalid["answers"]["t0b0"][field] = value
        with pytest.raises(ValueError, match=r"Typed|typed|Invalid"):
            parse_decision_batch(body, invalid)
    for answers in ({}, {"wrong": response(body)["answers"]["t0b0"]}):
        with pytest.raises(ValueError, match="exact batch"):
            parse_decision_batch(body, {"answers": answers})
    bad = deepcopy(batches)
    packet = json.loads(bad[0]["state"])
    packet["words"][0][1] = "invented"
    bad[0]["state"] = json.dumps(packet)
    with pytest.raises(ValueError, match="Modified local"):
        apply_decision_batches(page, state, menu, bad, [response(b) for b in bad])
    with pytest.raises(ValueError, match="Duplicate"):
        apply_decision_batches(page, state, menu, [body, body], [response(body), response(body)])


def test_native_gold_invariance_empty_menu_and_question_admission() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    original = decision_batches(page, state, "typesafe/jev-1.13")
    page.update(gold="ignored", family="ignored")
    state.update(gold="ignored")
    assert decision_batches(page, state, "typesafe/jev-1.13") == original
    for count in (0, 17, True):
        with pytest.raises(ValueError, match="1-16"):
            decision_batches(page, state, "typesafe/jev-1.13", max_questions=count)
    page["vector_candidates"] = deepcopy(state["tables"])
    menu, batches = decision_batches(page, state, "typesafe/jev-1.13")
    assert batches == []
    assert apply_decision_batches(page, state, menu, [], [])[0] == state


def test_chat_answers_envelope_matches_shared_accounting() -> None:
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    menu, body = request(page, state, "anthropic/claude-haiku-5.5")
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema["required"] == ["answers"]
    assert set(schema["properties"]["answers"]["properties"]) == {b["id"] for b in menu["boundaries"]}
    answer = {b["id"]: {"split": 0.1, "join": 0.9, "unresolved": 0} for b in menu["boundaries"]}
    result = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"answers": answer})}}]}
    assert parse(result) == answer
    result["choices"][0]["message"]["content"] = json.dumps(answer)
    with pytest.raises(ValueError, match="answers object"):
        parse(result)
