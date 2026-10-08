"""CPU-only evaluation of bounded binary PDF layout decisions.

Raw probability scores are descriptive: threshold selection is not probability
calibration. Missing and failed predictions remain in operational denominators.
No inference, document editing, or network access occurs in this module.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

CONFIDENCE_GRID = (0.5, 0.7, 0.8, 0.9, 0.95, 0.99)
ANSWERABILITY_GRID = (0.5, 0.7, 0.8, 0.9, 0.95, 0.99)
FIXED_POLICY = {"confidence": 0.9, "answerability": 0.9, "abstain_all": False}
MIN_CALIBRATION_ACCEPTED = 8
MAX_CALIBRATION_UNSAFE_UPPER = 0.1
ECE_BINS = 10
LOG_EPSILON = 1e-15
WILSON_Z = 1.959963984540054
DECISION_THRESHOLD = 0.5


def _number(value: object, name: str, *, probability: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        message = f"{name} must be a finite number, not a boolean"
        raise ValueError(message)  # noqa: TRY004 - malformed records use one validation exception
    result = float(value)
    if not math.isfinite(result) or result < 0 or (probability and result > 1):
        message = f"{name} must be finite and {'between 0 and 1' if probability else 'nonnegative'}"
        raise ValueError(message)
    return result


def _name(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        message = f"{field} must be a nonempty string"
        raise ValueError(message)
    return value


def wilson_upper(wrong: int, total: int) -> float | None:
    """Return the upper endpoint of a two-sided 95% Wilson interval."""
    if isinstance(wrong, bool) or isinstance(total, bool) or not isinstance(wrong, int) or not isinstance(total, int):
        message = "Wilson counts must be integers"
        raise ValueError(message)  # noqa: TRY004 - malformed records use one validation exception
    if total < 0 or wrong < 0 or wrong > total:
        message = "Wilson counts must satisfy 0 <= wrong <= total"
        raise ValueError(message)
    if total == 0:
        return None
    proportion = wrong / total
    square = WILSON_Z**2
    return (
        proportion
        + square / (2 * total)
        + WILSON_Z * math.sqrt(proportion * (1 - proportion) / total + square / (4 * total**2))
    ) / (1 + square / total)


def _accepted(prediction: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    if prediction.get("error") or policy["abstain_all"]:
        return False
    probability = prediction["p_yes"]
    return max(probability, 1 - probability) >= policy["confidence"] and (
        prediction["p_answerable"] >= policy["answerability"]
    )


def _selective(rows: list[tuple[dict[str, Any], dict[str, Any]]], policy: Mapping[str, Any]) -> dict[str, Any]:
    accepted = [(case, prediction) for case, prediction in rows if _accepted(prediction, policy)]
    unknown = sum(case["gold"] is None for case, _ in accepted)
    wrong = sum(
        case["gold"] is not None and (prediction["p_yes"] >= DECISION_THRESHOLD) != case["gold"]
        for case, prediction in accepted
    )
    total = len(rows)
    count = len(accepted)
    labeled = count - unknown
    return {
        "total": total,
        "accepted": count,
        "accepted_labeled": labeled,
        "accepted_correct": labeled - wrong,
        "accepted_wrong": wrong,
        "unknown_accepted": unknown,
        "unsafe_accepted": wrong + unknown,
        "abstained": total - count,
        "coverage": count / total if total else None,
        "wrong_rate_labeled": wrong / labeled if labeled else None,
        "wrong_rate_labeled_wilson95_upper": wilson_upper(wrong, labeled),
        "unsafe_rate": (wrong + unknown) / count if count else None,
        "unsafe_rate_wilson95_upper": wilson_upper(wrong + unknown, count),
    }


def _scores(pairs: list[tuple[float, bool]]) -> dict[str, Any]:
    count = len(pairs)
    bins = []
    error = 0.0
    for index in range(ECE_BINS):
        values = [(p, y) for p, y in pairs if min(int(p * ECE_BINS), ECE_BINS - 1) == index]
        mean_probability = sum(p for p, _ in values) / len(values) if values else None
        positive_rate = sum(y for _, y in values) / len(values) if values else None
        if values:
            error += len(values) * abs(mean_probability - positive_rate)  # type: ignore[operator]
        bins.append(
            {
                "lower": index / ECE_BINS,
                "upper": (index + 1) / ECE_BINS,
                "count": len(values),
                "mean_probability": mean_probability,
                "positive_rate": positive_rate,
            }
        )
    return {
        "sample_count": count,
        "brier": sum((p - y) ** 2 for p, y in pairs) / count if count else None,
        "log_loss": -sum(math.log(max(LOG_EPSILON, min(1 - LOG_EPSILON, p if y else 1 - p))) for p, y in pairs) / count
        if count
        else None,
        "ece": error / count if count else None,
        "ece_bins": bins,
    }


def _metrics(rows: list[tuple[dict[str, Any], dict[str, Any]]], policy: Mapping[str, Any]) -> dict[str, Any]:
    labeled = [(case, prediction) for case, prediction in rows if case["gold"] is not None]
    valid = [(case, prediction) for case, prediction in rows if not prediction.get("error")]
    correct = sum(
        not prediction.get("error") and (prediction["p_yes"] >= DECISION_THRESHOLD) == case["gold"]
        for case, prediction in labeled
    )
    return {
        "total": len(rows),
        "labeled_count": len(labeled),
        "unknown_count": len(rows) - len(labeled),
        "failures": sum(bool(prediction.get("error")) for _, prediction in rows),
        "forced_correct": correct,
        "forced_accuracy": correct / len(labeled) if labeled else None,
        "decision_probability": _scores(
            [(prediction["p_yes"], case["gold"]) for case, prediction in valid if case["gold"] is not None]
        ),
        "answerability_probability": _scores(
            [(prediction["p_answerable"], case["gold"] is not None) for case, prediction in valid]
        ),
        "selective": _selective(rows, policy),
    }


def _curves(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "confidence": confidence,
            "answerability": answerability,
            **_selective(rows, {"confidence": confidence, "answerability": answerability, "abstain_all": False}),
        }
        for confidence in CONFIDENCE_GRID
        for answerability in ANSWERABILITY_GRID
    ]


def _select_policy(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    candidates = [
        point
        for point in _curves(rows)
        if point["accepted"] >= MIN_CALIBRATION_ACCEPTED
        and point["unsafe_rate_wilson95_upper"] <= MAX_CALIBRATION_UNSAFE_UPPER
    ]
    if not candidates:
        return {
            "confidence": None,
            "answerability": None,
            "abstain_all": True,
            "reason": "No calibration threshold meets minimum support and the Wilson unsafe-rate bound.",
            "calibration": _selective(rows, {"abstain_all": True}),
        }
    best = min(
        candidates,
        key=lambda point: (
            -point["accepted"],
            point["unsafe_rate_wilson95_upper"],
            -point["confidence"],
            -point["answerability"],
        ),
    )
    policy = {"confidence": best["confidence"], "answerability": best["answerability"], "abstain_all": False}
    return {
        **policy,
        "reason": "Maximum calibration coverage among qualifying grid thresholds.",
        "calibration": _selective(rows, policy),
    }


def _validated_cases(cases: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for original in cases:
        case = dict(original)
        case_id = _name(case.get("id"), "case.id")
        if case_id in result:
            message = f"Duplicate case id: {case_id}"
            raise ValueError(message)
        for field in ("family", "task"):
            _name(case.get(field), f"case.{field}")
        if case.get("split") not in ("calibration", "test"):
            message = "case.split must be calibration or test"
            raise ValueError(message)
        if "gold" not in case or (case["gold"] is not None and not isinstance(case["gold"], bool)):
            message = "case.gold must be bool or None"
            raise ValueError(message)
        case["baseline_probability"] = _number(case.get("baseline_probability"), "case.baseline_probability")
        case["baseline_answerable"] = _number(case.get("baseline_answerable"), "case.baseline_answerable")
        result[case_id] = case
    return result


def _validated_predictions(
    predictions: Iterable[Mapping[str, Any]], cases: Mapping[str, Any]
) -> dict[tuple[str, str], dict[str, Any]]:
    result = {}
    for original in predictions:
        prediction = dict(original)
        case_id = _name(prediction.get("case_id"), "prediction.case_id")
        model = _name(prediction.get("model"), "prediction.model")
        if model == "baseline" or case_id not in cases or (model, case_id) in result:
            message = "Prediction uses reserved model, unknown case id, or duplicate model/case pair"
            raise ValueError(message)
        if prediction.get("error") is not None:
            _name(prediction["error"], "prediction.error")
        if "probability_kind" in prediction:
            _name(prediction["probability_kind"], "prediction.probability_kind")
        for field in ("p_yes", "p_answerable"):
            if field in prediction or not prediction.get("error"):
                prediction[field] = _number(prediction.get(field), f"prediction.{field}")
        for field in ("elapsed_ms", "cost_usd"):
            if field in prediction:
                prediction[field] = _number(prediction[field], f"prediction.{field}", probability=False)
        result[model, case_id] = prediction
    return result


def evaluate(cases: Iterable[Mapping[str, Any]], predictions: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate records and score raw probabilities and selective held-out policies.

    Baseline inputs are numeric scores in [0, 1]. Gold None means the supplied
    evidence does not support either answer. Missing predictions count as failed
    forced decisions and selective abstentions. Each model selects one global
    policy from calibration cases only; task/family slices reuse that policy.
    """
    case_map = _validated_cases(cases)
    prediction_map = _validated_predictions(predictions, case_map)
    models = sorted({model for model, _ in prediction_map} | {"baseline"})
    report: dict[str, Any] = {
        "schema_version": 1,
        "notes": [
            "Small synthetic PDF decision study; these results do not establish production safety.",
            "Raw native, heuristic, or self-reported scores are not calibrated probabilities.",
            "Threshold selection uses calibration cases only and does not calibrate probabilities.",
            (
                "Probability metrics exclude failed predictions and publish sample counts; "
                "operational metrics retain failures."
            ),
            "Gold None denotes insufficient evidence; accepting either answer is counted as unsafe.",
            "Wilson intervals are descriptive and do not correct for grid selection or correlated synthetic variants.",
            (
                "No per-case latency or cost aggregation: "
                "batches require unique request accounting in the inference runner."
            ),
        ],
        "selection": {
            "minimum_accepted": MIN_CALIBRATION_ACCEPTED,
            "maximum_unsafe_wilson95_upper": MAX_CALIBRATION_UNSAFE_UPPER,
            "confidence_grid": list(CONFIDENCE_GRID),
            "answerability_grid": list(ANSWERABILITY_GRID),
        },
        "case_counts": {
            split: sum(case["split"] == split for case in case_map.values()) for split in ("calibration", "test")
        },
        "models": {},
    }
    for model in models:
        rows = []
        for case_id, case in case_map.items():
            prediction = (
                {"p_yes": case["baseline_probability"], "p_answerable": case["baseline_answerable"]}
                if model == "baseline"
                else prediction_map.get((model, case_id), {"error": "missing_prediction"})
            )
            rows.append((case, prediction))
        calibration = [(case, prediction) for case, prediction in rows if case["split"] == "calibration"]
        test = [(case, prediction) for case, prediction in rows if case["split"] == "test"]
        selected = _select_policy(calibration)
        report["models"][model] = {
            "probability_kinds": (
                ["heuristic_score"]
                if model == "baseline"
                else sorted(
                    {
                        prediction.get("probability_kind", "unspecified")
                        for _, prediction in rows
                        if not prediction.get("error")
                    }
                )
            ),
            "fixed_policy": dict(FIXED_POLICY),
            "selected_policy": selected,
            "test_fixed": _metrics(test, FIXED_POLICY),
            "test_selected": _metrics(test, selected),
            "calibration_curve": _curves(calibration),
            "test_curve": _curves(test),
            "by_task": {
                task: {
                    "fixed": _metrics([(case, pred) for case, pred in test if case["task"] == task], FIXED_POLICY),
                    "selected": _metrics([(case, pred) for case, pred in test if case["task"] == task], selected),
                }
                for task in sorted({case["task"] for case, _ in test})
            },
            "by_family": {
                family: {
                    "fixed": _metrics([(case, pred) for case, pred in test if case["family"] == family], FIXED_POLICY),
                    "selected": _metrics([(case, pred) for case, pred in test if case["family"] == family], selected),
                }
                for family in sorted({case["family"] for case, _ in test})
            },
            "by_task_family": [
                {
                    "task": task,
                    "family": family,
                    "fixed": _metrics(
                        [(case, pred) for case, pred in test if (case["task"], case["family"]) == (task, family)],
                        FIXED_POLICY,
                    ),
                    "selected": _metrics(
                        [(case, pred) for case, pred in test if (case["task"], case["family"]) == (task, family)],
                        selected,
                    ),
                }
                for task, family in sorted({(case["task"], case["family"]) for case, _ in test})
            ],
        }
    return report


def _display(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def render_report(report: Mapping[str, Any]) -> str:
    """Render the evaluation, sample counts, policies, and subgroup metrics."""
    lines = [
        "# PDF decision probability pilot",
        "",
        *[f"- {note}" for note in report["notes"]],
        "",
        f"Cases: calibration {report['case_counts']['calibration']}; test {report['case_counts']['test']}.",
        "",
        (
            "| Model / policy | Test N | Labeled N | Failures | Forced accuracy | Probability N | Brier | Log loss | "
            "ECE | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, entry in report["models"].items():
        label = model.replace("|", "\\|").replace("\n", " ")
        for name in ("fixed", "selected"):
            metrics = entry[f"test_{name}"]
            scores = metrics["decision_probability"]
            selective = metrics["selective"]
            lines.append(
                f"| {label} / {name} | {metrics['total']} | {metrics['labeled_count']} | {metrics['failures']} | "
                f"{_display(metrics['forced_accuracy'])} | {scores['sample_count']} | {_display(scores['brier'])} | "
                f"{_display(scores['log_loss'])} | {_display(scores['ece'])} | {selective['accepted']} | "
                f"{selective['accepted_wrong']} | {selective['unknown_accepted']} | "
                f"{_display(selective['unsafe_rate_wilson95_upper'])} |"
            )
    for model, entry in report["models"].items():
        label = model.replace("|", "\\|").replace("\n", " ")
        policy = entry["selected_policy"]
        lines.extend(
            [
                "",
                f"**{label} selected policy:** "
                + (
                    "abstain all"
                    if policy["abstain_all"]
                    else f"confidence ≥ {policy['confidence']}, answerability ≥ {policy['answerability']}"
                )
                + f". {policy['reason']}",
                "",
            ]
        )
        lines.extend(["Raw score provenance: " + ", ".join(entry["probability_kinds"]) + ".", ""])
        # Keep each model's subgroup evidence alongside its threshold decision.
        lines.extend(
            [
                (
                    "| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | "
                    "Unknown accepted | Unsafe Wilson upper |"
                ),
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for dimension in ("by_task", "by_family"):
            for group, policies in entry[dimension].items():
                group_label = group.replace("|", "\\|").replace("\n", " ")
                for name, metrics in policies.items():
                    selective = metrics["selective"]
                    lines.append(
                        f"| {dimension.removeprefix('by_')}:{group_label} / {name} | {metrics['total']} | "
                        f"{metrics['labeled_count']} | {metrics['failures']} | "
                        f"{_display(metrics['forced_accuracy'])} | "
                        f"{selective['accepted']} | {selective['accepted_wrong']} | {selective['unknown_accepted']} | "
                        f"{_display(selective['unsafe_rate_wilson95_upper'])} |"
                    )
        lines.append("")
    lines.extend(
        [
            "Fixed policy: confidence ≥ 0.9 and answerability ≥ 0.9. A probability of exactly 0.5 predicts yes.",
            "",
            (
                f"Selection requires ≥ {report['selection']['minimum_accepted']} accepted calibration cases and "
                f"unsafe-rate Wilson upper ≤ {report['selection']['maximum_unsafe_wilson95_upper']}."
            ),
            "",
            (
                "Zero observed wrong decisions does not imply zero risk. "
                "Full threshold curves and reliability bins are retained in JSON."
            ),
            "",
        ]
    )
    return "\n".join(lines)
