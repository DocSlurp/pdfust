from __future__ import annotations

import copy
import json

import pytest
from bench.decision_routing import evaluate_routing


def fixture() -> tuple[list[dict], list[dict], list[dict]]:
    cases = [
        {"id": "cal", "task": "header", "split": "calibration", "gold": True},
        {"id": "unknown", "task": "header", "split": "calibration", "gold": None},
        {"id": "test", "task": "header", "split": "test", "gold": False},
        {"id": "test-unknown", "task": "header", "split": "test", "gold": None},
    ]
    predictions = []
    ledger = []
    for model, latency in [("a", 20), ("b", 10)]:
        for case in cases:
            index = len(ledger)
            predictions.append(
                {
                    "case_id": case["id"],
                    "model": model,
                    "p_yes": 0.9,
                    "probability_kind": "native_decision_score",
                    "request_index": index,
                }
            )
            ledger.append({"index": index, "elapsed_ms": latency})
    return cases, predictions, ledger


def test_test_gold_predictions_and_latency_never_select_routes() -> None:
    cases, predictions, ledger = fixture()
    frozen = copy.deepcopy((cases, predictions, ledger))
    first = evaluate_routing(cases, predictions, ledger, ["a", "b"])
    assert first["tasks"]["header"]["chosen_model"] == "b"
    assert (cases, predictions, ledger) == frozen
    cases[2]["gold"] = True
    for prediction in predictions:
        if prediction["case_id"].startswith("test"):
            prediction["p_yes"] = 0.1
            ledger[prediction["request_index"]]["elapsed_ms"] = 9999
    second = evaluate_routing(cases, predictions, ledger, ["a", "b"])
    assert second["tasks"]["header"]["chosen_model"] == "b"
    assert first["test"]["unknown_yes"] == 1
    assert second["test"]["unknown_no"] == 1
    json.dumps(second, allow_nan=False)


def test_calibration_quality_beats_latency_and_unknown_only_affects_latency() -> None:
    cases, predictions, ledger = fixture()
    predictions[4]["p_yes"] = 0.1
    result = evaluate_routing(cases, predictions, ledger, ["a", "b"])
    assert result["tasks"]["header"]["chosen_model"] == "a"
    predictions[4]["p_yes"] = 0.9
    predictions[5]["p_yes"] = 0.0
    ledger[5]["elapsed_ms"] = 100
    result = evaluate_routing(cases, predictions, ledger, ["a", "b"])
    assert result["tasks"]["header"]["chosen_model"] == "a"
    assert result["tasks"]["header"]["candidates"]["b"]["calibration"]["known_correct"] == 1


@pytest.mark.parametrize("problem", ["missing", "failed", "probability", "latency", "unknown-failed"])
def test_incomplete_or_invalid_calibration_candidate_cannot_win(problem: str) -> None:
    cases, predictions, ledger = fixture()
    if problem == "missing":
        predictions.pop(4)
    elif problem == "failed":
        predictions[4]["error"] = "timeout"
    elif problem == "probability":
        predictions[4]["p_yes"] = float("nan")
    elif problem == "latency":
        ledger[4].pop("elapsed_ms")
    else:
        predictions[5]["error"] = "timeout"
    result = evaluate_routing(cases, predictions, ledger, ["a", "b"])
    assert result["tasks"]["header"]["chosen_model"] == "a"
    assert not result["tasks"]["header"]["candidates"]["b"]["eligible"]


def test_no_eligible_calibration_keeps_test_incomplete_and_lexical_tie_is_stable() -> None:
    cases, predictions, ledger = fixture()
    for entry in ledger:
        entry["elapsed_ms"] = 10
    assert evaluate_routing(cases, predictions, ledger, ["b", "a"])["tasks"]["header"]["chosen_model"] == "a"
    result = evaluate_routing(cases[2:], predictions, ledger, ["a", "b"])
    assert result["tasks"]["header"]["chosen_model"] is None
    assert result["test"]["status"] == "incomplete"
    assert result["test"]["known_accuracy"] is None
