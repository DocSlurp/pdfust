from __future__ import annotations

import copy
import json
import math

import pytest
from bench.decision_eval import evaluate, render_report, wilson_upper


def case(case_id: str, split: str = "test", *, gold: bool | None = True) -> dict:
    return {
        "id": case_id,
        "family": "forms",
        "task": "assignment",
        "split": split,
        "gold": gold,
        "baseline_probability": 0.95,
        "baseline_answerable": 0.95,
    }


def prediction(case_id: str, p_yes: float = 0.95, p_answerable: float = 0.95) -> dict:
    return {
        "case_id": case_id,
        "model": "small",
        "p_yes": p_yes,
        "p_answerable": p_answerable,
        "probability_kind": "self_reported",
    }


def test_failures_unknowns_and_missing_predictions_remain_visible() -> None:
    cases = [case("correct"), case("wrong", gold=False), case("unknown", gold=None), case("error"), case("missing")]
    predictions = [
        prediction("correct"),
        prediction("wrong"),
        prediction("unknown"),
        {"case_id": "error", "model": "small", "error": "timeout"},
    ]
    report = evaluate(cases, predictions)
    model = report["models"]["small"]
    metrics = model["test_fixed"]
    assert metrics["total"] == 5
    assert metrics["labeled_count"] == 4
    assert metrics["forced_accuracy"] == 0.25
    assert metrics["failures"] == 2
    assert metrics["decision_probability"]["sample_count"] == 2
    assert metrics["answerability_probability"]["sample_count"] == 3
    selective = metrics["selective"]
    assert selective["accepted"] == 3
    assert selective["accepted_wrong"] == 1
    assert selective["unknown_accepted"] == 1
    assert selective["unsafe_accepted"] == 2
    assert selective["abstained"] == 2
    assert model["selected_policy"]["abstain_all"]
    assert model["test_selected"]["selective"]["accepted"] == 0
    assert model["probability_kinds"] == ["self_reported"]
    assert model["by_task_family"][0]["fixed"]["total"] == 5
    json.dumps(report, allow_nan=False)
    assert "Zero observed" in render_report(report)


def test_policy_selection_uses_calibration_only() -> None:
    cases = [case(f"cal-{index}", "calibration") for index in range(40)] + [case("heldout")]
    predictions = [prediction(item["id"]) for item in cases]
    first = evaluate(cases, predictions)
    changed = copy.deepcopy(cases)
    changed[-1]["gold"] = False
    second = evaluate(changed, predictions)
    before = first["models"]["small"]
    after = second["models"]["small"]
    assert before["selected_policy"] == after["selected_policy"]
    assert not before["selected_policy"]["abstain_all"]
    assert before["test_selected"]["selective"]["accepted_correct"] == 1
    assert after["test_selected"]["selective"]["accepted_wrong"] == 1


def test_zero_errors_small_sample_cannot_support_selected_policy() -> None:
    cases = [case(f"cal-{index}", "calibration") for index in range(8)] + [case("test")]
    report = evaluate(cases, [prediction(item["id"]) for item in cases])
    assert report["models"]["small"]["selected_policy"]["abstain_all"]
    upper = wilson_upper(0, 8)
    assert upper is not None
    assert upper > 0.3
    assert wilson_upper(0, 0) is None


def test_unknown_calibration_cases_block_unsafe_policy() -> None:
    cases = [case(f"cal-{index}", "calibration", gold=None) for index in range(40)]
    report = evaluate(cases, [prediction(item["id"]) for item in cases])
    assert report["models"]["small"]["selected_policy"]["abstain_all"]
    assert all(
        point["unsafe_accepted"] == point["accepted"] for point in report["models"]["small"]["calibration_curve"]
    )


def test_confidence_and_answerability_boundaries_and_negative_answers() -> None:
    cases = [case("negative", gold=False), case("low-answerability"), case("tie")]
    report = evaluate(
        cases, [prediction("negative", 0.1, 0.9), prediction("low-answerability", 0.99, 0.899), prediction("tie", 0.5)]
    )
    metrics = report["models"]["small"]["test_fixed"]
    assert metrics["forced_correct"] == 3
    assert metrics["selective"]["accepted"] == 1
    assert metrics["selective"]["accepted_correct"] == 1


def test_probability_metrics_include_extreme_values_in_last_bin() -> None:
    report = evaluate([case("one"), case("zero", gold=False)], [prediction("one", 1.0), prediction("zero", 0.0)])
    scores = report["models"]["small"]["test_fixed"]["decision_probability"]
    assert scores["brier"] == 0
    assert scores["ece"] == 0
    assert scores["ece_bins"][0]["count"] == 1
    assert scores["ece_bins"][-1]["count"] == 1
    assert math.isfinite(scores["log_loss"])


@pytest.mark.parametrize("bad", [True, False, -0.01, 1.01, math.nan, math.inf, "0.9", None])
def test_reject_invalid_prediction_probability(bad: object) -> None:
    row = prediction("a")
    row["p_yes"] = bad
    with pytest.raises(ValueError, match=r"prediction\.p_yes"):
        evaluate([case("a")], [row])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("gold", 1),
        ("gold", "yes"),
        ("split", "train"),
        ("baseline_probability", True),
        ("baseline_answerable", math.nan),
    ],
)
def test_reject_invalid_case(field: str, value: object) -> None:
    row = case("a")
    row[field] = value
    with pytest.raises(ValueError, match="case\\."):
        evaluate([row], [])


def test_reject_duplicate_and_unknown_records() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate([case("a"), case("a")], [])
    with pytest.raises(ValueError, match="duplicate"):
        evaluate([case("a")], [prediction("a"), prediction("a")])
    with pytest.raises(ValueError, match="unknown"):
        evaluate([case("a")], [prediction("b")])


def test_no_probability_scores_for_complete_failure() -> None:
    report = evaluate([case("a")], [{"case_id": "a", "model": "small", "error": "invalid_response"}])
    metrics = report["models"]["small"]["test_fixed"]
    assert metrics["forced_accuracy"] == 0
    assert metrics["decision_probability"]["brier"] is None
    assert metrics["selective"]["coverage"] == 0
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize(("field", "value"), [("elapsed_ms", True), ("elapsed_ms", -1), ("cost_usd", math.inf)])
def test_reject_invalid_request_measurements(field: str, value: object) -> None:
    row = prediction("a")
    row[field] = value
    with pytest.raises(ValueError, match=field):
        evaluate([case("a")], [row])
