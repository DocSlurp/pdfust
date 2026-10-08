"""Read-only cohort and retained-source analysis for the PDF decision pilot."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Any

from bench.decision_assembly import assemble_case
from bench.decision_eval import DECISION_THRESHOLD, FIXED_POLICY

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_SINGLETON_SUFFIX = re.compile(r"-b1\Z")
_NON_CONSTRAINT_REASONS = {"negative_decision", "abstained_decision"}


def _limitations(cases: Sequence[dict[str, Any]]) -> list[str]:
    common = [
        "The baseline is an illustrative geometry/type heuristic, not native extractor quality.",
        "Source-word conservation protects retained data; it does not establish correct logical relationships.",
        "Isolation comparisons describe batch sensitivity and do not identify its causal mechanism.",
    ]
    grounded = bool(cases) and all("provenance" in case for case in cases)
    if grounded:
        sources = {case["provenance"]["pdf_sha256"] for case in cases}
        positive = sum(case["gold"] is True for case in cases)
        negative = sum(case["gold"] is False for case in cases)
        return [
            common[0],
            (
                f"These {len(cases)} grounded regional table gates contain "
                f"{positive} positive and {negative} negative labels."
            ),
            (
                f"The regions come from {len(sources)} original sources; NICS and Senate each contribute two clips. "
                "Eight regions are not eight independent documents."
            ),
            "Sources mix original public PDFs and existing repository synthetic controls used in earlier studies.",
            (
                "These controls are test-only, with no calibration cases. "
                "The selected abstain-all policy is unsupported by calibration, not learned from the controls."
            ),
            (
                "Labels identify record tables versus prose in retained regions. "
                "They do not provide header, value-assignment, individual-cell, wrap, or complete-grid gold."
            ),
            *common[1:],
        ]
    return [
        common[0],
        ("Frozen labels describe synthetic author intent; they are not independently annotated real-world PDF truth."),
        "Unknown wrap controls contain 'continued detail', which provides a plausible continuation cue.",
        "Unknown headers place 'Observed Value' above aligned values, a conventional header cue.",
        "Negative 'Provisional estimate only' controls can plausibly qualify a numeric column.",
        "Unit-mismatched assignment controls supply stronger observable evidence than hidden-intent controls.",
        "Related templates, vocabularies, and instruction variants do not constitute independent samples.",
        "Calibration/test label priors differ; threshold transfer includes class-prior shift.",
        *common[1:],
    ]


def _decision(prediction: Mapping[str, Any] | None, policy: Mapping[str, Any]) -> bool | None:
    if prediction is None or prediction.get("error") or policy["abstain_all"]:
        return None
    probability = prediction["p_yes"]
    if max(probability, 1 - probability) < policy["confidence"]:
        return None
    if prediction["p_answerable"] < policy["answerability"]:
        return None
    return probability >= DECISION_THRESHOLD


def _quality(cases: Sequence[Mapping[str, Any]], predictions: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    missing = sum(case["id"] not in predictions for case in cases)
    failed = sum(bool(predictions[case["id"]].get("error")) for case in cases if case["id"] in predictions)
    labeled = [case for case in cases if case["gold"] is not None]
    correct = sum(
        case["id"] in predictions
        and not predictions[case["id"]].get("error")
        and (predictions[case["id"]]["p_yes"] >= DECISION_THRESHOLD) == case["gold"]
        for case in labeled
    )
    return {
        "total": len(cases),
        "labeled_count": len(labeled),
        "unknown_count": len(cases) - len(labeled),
        "missing_predictions": missing,
        "failed_predictions": failed,
        "successful_predictions": len(cases) - missing - failed,
        "status": "complete" if missing + failed == 0 else "incomplete",
        "known_correct": correct,
        "known_accuracy": correct / len(labeled) if labeled else None,
    }


def _assembly(
    cases: Sequence[dict[str, Any]], predictions: Mapping[str, Mapping[str, Any]], policy: Mapping[str, Any]
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    for case in cases:
        decision = _decision(predictions.get(case["id"]), policy)
        result = assemble_case(case, decision)
        counts["total"] += 1
        counts["affirmative_requested"] += decision is True
        counts["negative_decisions"] += decision is False
        counts["abstained_decisions"] += decision is None
        applied = bool(result["accepted"])
        counts["affirmative_applied"] += applied
        if applied:
            outcome = "unknown" if case["gold"] is None else "correct" if case["gold"] else "wrong"
            counts[f"applied_{outcome}"] += 1
        counts["source_words_before"] += len(case["state"]["words"])
        counts["source_words_after"] += len(result["words"])
        counts["source_preserved_cases"] += result["words"] == case["state"]["words"]
        for refusal in result["abstained"]:
            if refusal["reason"] not in _NON_CONSTRAINT_REASONS:
                reasons[refusal["reason"]] += 1
    keys = (
        "total",
        "affirmative_requested",
        "negative_decisions",
        "abstained_decisions",
        "affirmative_applied",
        "applied_correct",
        "applied_wrong",
        "applied_unknown",
        "source_words_before",
        "source_words_after",
        "source_preserved_cases",
    )
    return {
        **{key: counts[key] for key in keys},
        "source_word_conservation": counts["source_preserved_cases"] == len(cases),
        "constraint_refusals": sum(reasons.values()),
        "constraint_refusal_reasons": dict(sorted(reasons.items())),
    }


def _isolation(
    cases: Sequence[dict[str, Any]], batch: Mapping[str, Mapping[str, Any]], singleton: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    paired = [
        case
        for case in cases
        if case["id"] in batch
        and case["id"] in singleton
        and not batch[case["id"]].get("error")
        and not singleton[case["id"]].get("error")
    ]
    changes = []
    for case in paired:
        first, second = batch[case["id"]], singleton[case["id"]]
        forced_flip = (first["p_yes"] >= DECISION_THRESHOLD) != (second["p_yes"] >= DECISION_THRESHOLD)
        fixed_flip = _decision(first, FIXED_POLICY) != _decision(second, FIXED_POLICY)
        changes.append(
            {
                "case_id": case["id"],
                "task": case["task"],
                "gold": case["gold"],
                "p_yes_absolute_delta": abs(first["p_yes"] - second["p_yes"]),
                "p_answerable_absolute_delta": abs(first["p_answerable"] - second["p_answerable"]),
                "forced_answer_flip": forced_flip,
                "fixed_outcome_flip": fixed_flip,
            }
        )
    return {
        "total_cases": len(cases),
        "paired_successes": len(paired),
        "unpaired_or_failed": len(cases) - len(paired),
        "forced_answer_flips": sum(change["forced_answer_flip"] for change in changes),
        "fixed_outcome_flips": sum(change["fixed_outcome_flip"] for change in changes),
        "max_p_yes_absolute_delta": max((change["p_yes_absolute_delta"] for change in changes), default=None),
        "mean_p_yes_absolute_delta": (
            sum(change["p_yes_absolute_delta"] for change in changes) / len(changes) if changes else None
        ),
        "max_p_answerable_absolute_delta": max(
            (change["p_answerable_absolute_delta"] for change in changes), default=None
        ),
        "changes": changes,
    }


def analyze(
    cases: Sequence[dict[str, Any]], predictions: Sequence[Mapping[str, Any]], report: Mapping[str, Any]
) -> dict[str, Any]:
    """Inspect frozen validated cohorts and execute both policies over retained words.

    Singleton comparisons require the identical model/variant label with only
    the ``-b1`` suffix added. Resolved or text variants are separate cohorts.
    Calibration and test are never combined when scoring or comparing isolation.
    Missing/failed predictions abstain in assembly and fail forced accuracy.
    """
    case_ids = {case["id"] for case in cases}
    cohorts: dict[str, dict[str, Mapping[str, Any]]] = {
        "baseline": {
            case["id"]: {"p_yes": case["baseline_probability"], "p_answerable": case["baseline_answerable"]}
            for case in cases
        }
    }
    for prediction in predictions:
        model, case_id = prediction["model"], prediction["case_id"]
        if model == "baseline" or case_id not in case_ids or case_id in cohorts.setdefault(model, {}):
            message = "Analysis received a reserved model, unknown case, or duplicate prediction"
            raise ValueError(message)
        cohorts[model][case_id] = prediction
    result: dict[str, Any] = {
        "schema_version": 1,
        "limitations": _limitations(cases),
        "label_counts": {
            split: dict(
                Counter(
                    "unknown" if case["gold"] is None else "true" if case["gold"] else "false"
                    for case in cases
                    if case["split"] == split
                )
            )
            for split in ("calibration", "test")
        },
        "cohorts": {},
        "isolation": [],
    }
    for model, rows in sorted(cohorts.items()):
        selected = report["models"][model]["selected_policy"]
        result["cohorts"][model] = {}
        for split in ("calibration", "test"):
            subset = [case for case in cases if case["split"] == split]
            result["cohorts"][model][split] = {
                "quality": _quality(subset, rows),
                "by_task": {
                    task: _quality([case for case in subset if case["task"] == task], rows)
                    for task in sorted({case["task"] for case in subset})
                },
                "assembly_fixed": _assembly(subset, rows, FIXED_POLICY),
                "assembly_selected": _assembly(subset, rows, selected),
            }
        if _SINGLETON_SUFFIX.search(model):
            batch_model = _SINGLETON_SUFFIX.sub("", model)
            if batch_model in cohorts:
                result["isolation"].append(
                    {
                        "batch_model": batch_model,
                        "singleton_model": model,
                        **{
                            split: _isolation(
                                [case for case in cases if case["split"] == split], cohorts[batch_model], rows
                            )
                            for split in ("calibration", "test")
                        },
                    }
                )
    return result


def _display(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _label(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_analysis(result: Mapping[str, Any]) -> str:  # noqa: C901 - ordered report sections
    """Render cohort completeness, applied edges, and isolated score comparisons."""
    lines = [
        "## Frozen cohort and assembly analysis",
        "",
        *[f"- {note}" for note in result["limitations"]],
        "",
        "| Cohort / split | Status | Successful / total | Known correct / N | Known accuracy |",
        "|---|---|---:|---:|---:|",
    ]
    for model, splits in result["cohorts"].items():
        for split, entry in splits.items():
            quality = entry["quality"]
            lines.append(
                f"| {_label(model)} / {split} | {quality['status']} | "
                f"{quality['successful_predictions']}/{quality['total']} | "
                f"{quality['known_correct']}/{quality['labeled_count']} | {_display(quality['known_accuracy'])} |"
            )
    lines.extend(
        [
            "",
            "### Retained-source application",
            "",
            (
                "| Cohort / split / policy | Affirmative requested | Applied | Correct | Wrong | Unknown | "
                "Constraint refusals | Source words before / after | Preserved cases / total |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for model, splits in result["cohorts"].items():
        for split, entry in splits.items():
            for policy in ("fixed", "selected"):
                assembly = entry[f"assembly_{policy}"]
                lines.append(
                    f"| {_label(model)} / {split} / {policy} | {assembly['affirmative_requested']} | "
                    f"{assembly['affirmative_applied']} | {assembly['applied_correct']} | "
                    f"{assembly['applied_wrong']} | {assembly['applied_unknown']} | "
                    f"{assembly['constraint_refusals']} | "
                    f"{assembly['source_words_before']}/{assembly['source_words_after']} | "
                    f"{assembly['source_preserved_cases']}/{assembly['total']} |"
                )
    lines.extend(
        [
            "",
            "### Known-label task slices",
            "",
            "| Cohort / split / task | Status | Known correct / N | Known accuracy |",
            "|---|---|---:|---:|",
        ]
    )
    for model, splits in result["cohorts"].items():
        for split, entry in splits.items():
            for task, quality in entry["by_task"].items():
                lines.append(
                    f"| {_label(model)} / {split} / {_label(task)} | {quality['status']} | "
                    f"{quality['known_correct']}/{quality['labeled_count']} | "
                    f"{_display(quality['known_accuracy'])} |"
                )
    lines.extend(
        [
            "",
            "### Identical-observation singleton versus batch",
            "",
            (
                "| Model / split | Paired successes / N | Forced flips | Fixed outcome flips | "
                "Mean decision delta | Max decision delta | Max answerability delta |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for comparison in result["isolation"]:
        for split in ("calibration", "test"):
            metrics = comparison[split]
            lines.append(
                f"| {_label(comparison['batch_model'])} / {split} | "
                f"{metrics['paired_successes']}/{metrics['total_cases']} | {metrics['forced_answer_flips']} | "
                f"{metrics['fixed_outcome_flips']} | {_display(metrics['mean_p_yes_absolute_delta'])} | "
                f"{_display(metrics['max_p_yes_absolute_delta'])} | "
                f"{_display(metrics['max_p_answerable_absolute_delta'])} |"
            )
    if not result["isolation"]:
        lines.extend(["", "No matching singleton and batch cohorts are recorded."])
    return "\n".join([*lines, ""])
