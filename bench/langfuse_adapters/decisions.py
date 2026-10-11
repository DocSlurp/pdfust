"""D001–D005 binary relationship-decision pilot and existing-PDF region controls.

Covered retained artifacts under ``decisions/``:

- ``cases/cases.json`` + ``predictions.json`` (+ ``evaluation.json``): 96
  authored DEV observations (48 calibration, 48 test) and every evaluated model
  label, including the heuristic ``baseline``. Runs are model labels exactly as
  ``bench.decision_eval.evaluate`` reports them (``@variant`` and ``-b1``
  suffixes preserved).
- ``controls/cases.json`` + ``predictions-controls.json``: eight
  existing-PDF table/prose region controls (test only).
- ``task-routing.json``: the D005 calibration-selected per-task router,
  replayed as one extra run over the pilot predictions.

Scores reuse ``bench.decision_eval``. Row ``correct`` is the forced decision at
p_yes ≥ 0.5 against a known gold label; a failed or missing prediction counts
as wrong, and insufficient-evidence (gold ``None``) cases carry no ``correct``
score, exactly like ``forced_accuracy``. ``accepted_*``/``unsafe_*`` follow the
fixed (0.9/0.9) and calibration-selected policies. Run scores are the
recomputed test-split metrics, cross-checked against the retained evaluation;
any difference is recorded in ``metadata["retained_mismatch"]``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.decision_eval import FIXED_POLICY, evaluate
from bench.langfuse_adapters.base import Experiment, Item, Row, Run, file_ref, guard, read_json
from bench.langfuse_adapters.decisions_common import (
    DECISION_THRESHOLD,
    catalog_prices,
    cohort_ledger,
    cost_fields,
    cost_summary,
    ledger,
    mismatches,
    relative,
    response_usage,
    state_ref,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

NAME = "decisions"

ROUTER = "task-router@D005"
_RUN_METRICS = ("total", "labeled_count", "unknown_count", "failures", "forced_correct", "forced_accuracy")
_PROBABILITY_METRICS = ("sample_count", "brier", "log_loss", "ece")
_SELECTIVE_METRICS = ("accepted", "accepted_wrong", "unknown_accepted", "unsafe_accepted", "abstained", "coverage")


def _accepted(prediction: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    """Mirror ``decision_eval._accepted`` for one prediction."""
    if prediction.get("error") or policy.get("abstain_all"):
        return False
    probability = prediction["p_yes"]
    return (
        max(probability, 1 - probability) >= policy["confidence"]
        and prediction["p_answerable"] >= policy["answerability"]
    )


def _item(root: Path, case: Mapping[str, Any], pdf_directory: str) -> Item:
    pdf = root / pdf_directory / f"{case['id']}.pdf"
    provenance = case.get("provenance") or {}
    if provenance.get("pdf"):
        pdf = root / pdf_directory / provenance["pdf"]
    source = file_ref(pdf) if pdf.is_file() else None
    payload: dict[str, Any] = {
        "case_id": case["id"],
        "family": case["family"],
        "task": case["task"],
        "split": case["split"],
        "question": case["question"],
        "state": state_ref(case.get("state")),
        "baseline_probability": case.get("baseline_probability"),
        "baseline_answerable": case.get("baseline_answerable"),
    }
    if source:
        payload["pdf"] = source
    if provenance:
        payload["provenance"] = {
            key: provenance[key]
            for key in ("pdf", "pdf_sha256", "page_zero_based", "clip_display", "license")
            if key in provenance
        }
    return Item(
        key=case["id"],
        input=payload,
        expected={"gold": case["gold"], "answerable": case["gold"] is not None},
        metadata={"split": case["split"], "task": case["task"], "family": case["family"]},
    )


def _row(
    case: Mapping[str, Any],
    prediction: Mapping[str, Any],
    selected: Mapping[str, Any],
    accounting: dict[str, Any],
) -> Row:
    error = prediction.get("error")
    gold = case["gold"]
    scores: dict[str, float | None] = {"failed": float(bool(error))}
    output: dict[str, Any] = {"error": error} if error else {}
    if not error:
        p_yes = prediction["p_yes"]
        predicted = p_yes >= DECISION_THRESHOLD
        output.update(p_yes=p_yes, p_answerable=prediction["p_answerable"], predicted=predicted)
        scores.update(p_yes=p_yes, p_answerable=prediction["p_answerable"])
        if gold is not None:
            scores["p_gold"] = p_yes if gold else 1 - p_yes
            scores["brier"] = (p_yes - float(gold)) ** 2
    if gold is not None:
        scores["correct"] = float(not error and (prediction["p_yes"] >= DECISION_THRESHOLD) == gold)
    for name, policy in (("fixed", FIXED_POLICY), ("selected", selected)):
        accepted = _accepted(prediction, policy)
        scores[f"accepted_{name}"] = float(accepted)
        scores[f"unsafe_{name}"] = float(
            accepted and (gold is None or (prediction["p_yes"] >= DECISION_THRESHOLD) != gold)
        )
    status = "missing" if error == "missing_prediction" else "failed" if error else "ok"
    metadata = {
        "status": status,
        "split": case["split"],
        "task": case["task"],
        "family": case["family"],
        **({"probability_kind": prediction["probability_kind"]} if "probability_kind" in prediction else {}),
        **accounting,
    }
    return Row(item_key=case["id"], output=output, scores=scores, metadata=metadata)


def _run_scores(model_report: Mapping[str, Any]) -> dict[str, float | None]:
    scores: dict[str, float | None] = {}
    for policy in ("fixed", "selected"):
        metrics = model_report[f"test_{policy}"]
        if policy == "fixed":
            scores.update({f"test_{key}": metrics[key] for key in _RUN_METRICS})
            probability = metrics["decision_probability"]
            scores.update({f"test_{key}": probability[key] for key in _PROBABILITY_METRICS})
        scores.update({f"test_{policy}_{key}": metrics["selective"][key] for key in _SELECTIVE_METRICS})
    return scores


def _accounting(root: Path, prediction: Mapping[str, Any], model: str) -> dict[str, Any]:
    entry = ledger(root).get(prediction.get("request_index", -1))
    if entry is None:
        return {}
    requested = entry.get("requested_model") or model.split("@", 1)[0]
    return cost_fields(entry, response_usage(root, entry), catalog_prices(root).get(requested))


def _experiment(  # noqa: PLR0913 - one retained study and its labels.
    root: Path,
    *,
    cases_path: Path,
    predictions_path: Path,
    evaluation_path: Path,
    dataset: str,
    description: str,
    pdf_directory: str,
    tag_prefix: str = "",
    routing_path: Path | None = None,
) -> Experiment:
    cases = read_json(cases_path)
    predictions = read_json(predictions_path)["predictions"]
    report = evaluate(cases, predictions)
    retained = read_json(evaluation_path)["models"] if evaluation_path.exists() else {}
    by_pair = {(prediction["model"], prediction["case_id"]): prediction for prediction in predictions}
    items = [_item(root, case, pdf_directory) for case in cases]
    runs = []
    for model, model_report in report["models"].items():
        selected = model_report["selected_policy"]
        rows = []
        for case in cases:
            if model == "baseline":
                prediction: Mapping[str, Any] = {
                    "p_yes": case["baseline_probability"],
                    "p_answerable": case["baseline_answerable"],
                    "probability_kind": "heuristic_score",
                }
            else:
                prediction = by_pair.get((model, case["id"]), {"error": "missing_prediction"})
            rows.append(_row(case, prediction, selected, _accounting(root, prediction, model)))
        scores = _run_scores(model_report)
        problems = mismatches(_run_scores(retained[model]), scores) if model in retained else ["not in retained report"]
        runs.append(
            Run(
                name=model,
                description=f"{model}: forced p_yes ≥ 0.5 plus fixed/selected selective policies; test-split scores.",
                rows=rows,
                scores=scores,
                metadata={
                    "model": model.split("@", 1)[0],
                    "variant": model.split("@", 1)[1] if "@" in model else None,
                    "probability_kinds": ", ".join(model_report["probability_kinds"]),
                    "selected_policy": (
                        "abstain all"
                        if selected["abstain_all"]
                        else f"confidence>={selected['confidence']}, answerability>={selected['answerability']}"
                    ),
                    "retained_mismatch": "; ".join(problems) or None,
                    **{f"cost_{key}": value for key, value in cost_summary(row.metadata for row in rows).items()},
                    **(cohort_ledger(root, f"{tag_prefix}{model}/batch") if model != "baseline" else {}),
                },
            )
        )
    if routing_path is not None and routing_path.exists():
        runs.append(_router(read_json(routing_path), cases, by_pair, root))
    return Experiment(
        dataset=dataset,
        description=description,
        items=items,
        runs=runs,
        source=relative(cases_path.parent),
    )


def _router(
    routing: Mapping[str, Any],
    cases: list[dict[str, Any]],
    by_pair: Mapping[tuple[str, str], Mapping[str, Any]],
    root: Path,
) -> Run:
    """Replay the D005 router: each case uses the calibration-chosen model for its task."""
    chosen = {task: entry["chosen_model"] for task, entry in routing["tasks"].items()}
    rows = []
    for case in cases:
        model = chosen.get(case["task"])
        prediction = (
            by_pair.get((model, case["id"]), {"error": "missing_prediction"}) if model else {"error": "no_route"}
        )
        row = _row(case, prediction, {"abstain_all": True}, _accounting(root, prediction, model or ""))
        row.metadata["routed_model"] = model
        rows.append(row)
    test = [row for row, case in zip(rows, cases, strict=True) if case["split"] == "test" and "correct" in row.scores]
    calibration = [
        row for row, case in zip(rows, cases, strict=True) if case["split"] == "calibration" and "correct" in row.scores
    ]
    scores = {
        "test_forced_correct": sum(row.scores["correct"] or 0 for row in test),
        "test_labeled_count": len(test),
        "test_forced_accuracy": sum(row.scores["correct"] or 0 for row in test) / len(test) if test else None,
        "calibration_forced_correct": sum(row.scores["correct"] or 0 for row in calibration),
        "calibration_labeled_count": len(calibration),
    }
    retained = {
        "test_forced_correct": sum(entry["test"]["known_correct"] for entry in routing["tasks"].values()),
        "test_labeled_count": sum(entry["test"]["known_count"] for entry in routing["tasks"].values()),
        "calibration_forced_correct": sum(entry["calibration"]["known_correct"] for entry in routing["tasks"].values()),
    }
    return Run(
        name=ROUTER,
        description="D005 offline task router: per-task model chosen by calibration accuracy; no confidence gate.",
        rows=rows,
        scores=scores,
        metadata={
            "routes": ", ".join(f"{task}={model}" for task, model in sorted(chosen.items())),
            "selection": routing.get("selection"),
            "retained_mismatch": "; ".join(mismatches(retained, scores)) or None,
        },
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield the binary pilot and the existing-PDF region controls."""
    root = guard(artifacts / "decisions")
    if (root / "cases" / "cases.json").exists() and (root / "predictions.json").exists():
        yield _experiment(
            root,
            cases_path=root / "cases" / "cases.json",
            predictions_path=root / "predictions.json",
            evaluation_path=root / "evaluation.json",
            dataset="exp/decisions/pilot-v1",
            description=(
                "D001–D005 typed relationship decisions: 96 authored DEV observations (48 calibration, 48 test; "
                "gold true/false/insufficient evidence). Raw model scores are not calibrated probabilities."
            ),
            pdf_directory="cases",
            routing_path=root / "task-routing.json",
        )
    if (root / "controls" / "cases.json").exists() and (root / "predictions-controls.json").exists():
        yield _experiment(
            root,
            cases_path=root / "controls" / "cases.json",
            predictions_path=root / "predictions-controls.json",
            evaluation_path=root / "evaluation-controls.json",
            dataset="exp/decisions/controls-v1",
            description=(
                "Eight existing-PDF table/prose region controls from six sources (test split only); "
                "no relationship or matrix gold."
            ),
            pdf_directory="controls",
            tag_prefix="controls/",
        )
