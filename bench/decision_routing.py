"""Offline task routing selected only from known calibration labels."""

from __future__ import annotations

import math
import statistics
from typing import TYPE_CHECKING, Any

from bench.decision_eval import DECISION_THRESHOLD

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def _valid(prediction: Mapping[str, Any] | None) -> bool:
    if prediction is None or prediction.get("error"):
        return False
    probability = prediction.get("p_yes")
    return (
        isinstance(probability, (int, float))
        and not isinstance(probability, bool)
        and math.isfinite(probability)
        and 0 <= probability <= 1
        and prediction.get("probability_kind") == "native_decision_score"
    )


def _quality(cases: Sequence[Mapping[str, Any]], predictions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    known = [case for case in cases if case["gold"] is not None]
    unknown = [case for case in cases if case["gold"] is None]
    valid = {case["id"]: predictions[case["id"]] for case in cases if _valid(predictions.get(case["id"]))}
    correct = sum(
        (valid[case["id"]]["p_yes"] >= DECISION_THRESHOLD) == case["gold"] for case in known if case["id"] in valid
    )
    complete = len(valid) == len(cases)
    return {
        "total": len(cases),
        "known_count": len(known),
        "known_correct": correct,
        "known_accuracy": correct / len(known) if known and complete else None,
        "unknown_count": len(unknown),
        "unknown_yes": sum(valid[case["id"]]["p_yes"] >= DECISION_THRESHOLD for case in unknown if case["id"] in valid),
        "unknown_no": sum(valid[case["id"]]["p_yes"] < DECISION_THRESHOLD for case in unknown if case["id"] in valid),
        "missing_or_invalid": len(cases) - len(valid),
        "status": "complete" if complete else "incomplete",
    }


def _latencies(
    cases: Sequence[Mapping[str, Any]],
    predictions: Mapping[str, Mapping[str, Any]],
    ledger: Mapping[int, Mapping[str, Any]],
) -> list[float]:
    latencies = []
    for case in cases:
        prediction = predictions.get(case["id"])
        request_index = prediction.get("request_index") if prediction else None
        entry = (
            ledger.get(request_index)
            if isinstance(request_index, int) and not isinstance(request_index, bool)
            else None
        )
        latency = entry.get("elapsed_ms") if entry else None
        if (
            isinstance(latency, (int, float))
            and not isinstance(latency, bool)
            and math.isfinite(latency)
            and latency >= 0
        ):
            latencies.append(latency)
    return latencies


def evaluate_routing(
    cases: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    ledger_entries: Sequence[Mapping[str, Any]],
    models: Sequence[str],
) -> dict[str, Any]:
    """Select each task by calibration accuracy, calibration latency, then model ID.

    Every calibration prediction, including indeterminate cases, must be valid
    and have a finite recorded request latency. Test inputs never select routes.
    """
    if len({case["id"] for case in cases}) != len(cases):
        message = "Duplicate case IDs"
        raise ValueError(message)
    indexed: dict[str, dict[str, Mapping[str, Any]]] = {model: {} for model in models}
    for prediction in predictions:
        model = prediction["model"]
        if model not in indexed:
            continue
        identifier = prediction["case_id"]
        if identifier in indexed[model]:
            message = "Duplicate prediction for a model and case"
            raise ValueError(message)
        indexed[model][identifier] = prediction
    ledger = {entry["index"]: entry for entry in ledger_entries}
    if len(ledger) != len(ledger_entries):
        message = "Duplicate ledger indexes"
        raise ValueError(message)
    tasks: dict[str, Any] = {}
    routed: dict[str, Mapping[str, Any]] = {}
    for task in sorted({case["task"] for case in cases}):
        calibration = [case for case in cases if case["task"] == task and case["split"] == "calibration"]
        test = [case for case in cases if case["task"] == task and case["split"] == "test"]
        candidates: dict[str, Any] = {}
        ranking = []
        for model in sorted(indexed):
            quality = _quality(calibration, indexed[model])
            latencies = _latencies(calibration, indexed[model], ledger)
            eligible = (
                quality["status"] == "complete" and quality["known_count"] > 0 and len(latencies) == len(calibration)
            )
            median = statistics.median(latencies) if eligible else None
            candidates[model] = {"eligible": eligible, "calibration": quality, "median_http_ms": median}
            if eligible:
                ranking.append((-quality["known_accuracy"], median, model))
        chosen = min(ranking)[2] if ranking else None
        selected = indexed[chosen] if chosen else {}
        routed.update({case["id"]: selected[case["id"]] for case in test if case["id"] in selected})
        tasks[task] = {
            "chosen_model": chosen,
            "candidates": candidates,
            "calibration": _quality(calibration, selected),
            "test": _quality(test, selected),
        }
    return {
        "schema_version": 1,
        "selection": "known calibration accuracy, then median calibration HTTP latency, then model ID",
        "notes": [
            "Indeterminate calibration cases affect latency only; indeterminate test outcomes are unscored.",
            "This exploratory analysis reuses frozen tests and related synthetic templates, not fresh validation.",
            "Further tuning against these results risks post hoc overfitting.",
        ],
        "tasks": tasks,
        "test": _quality([case for case in cases if case["split"] == "test"], routed),
    }
