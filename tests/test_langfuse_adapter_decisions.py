"""Synthetic checks for the hosted relationship-decision Langfuse adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench.decision_eval import evaluate
from bench.langfuse_adapters import (
    decisions,
    decisions_cohorts,
    decisions_common,
    decisions_context,
    decisions_lowlevel,
    decisions_waves,
)
from bench.langfuse_adapters.base import validate


def _write(path: Path, value: Any) -> None:  # noqa: ANN401 - arbitrary JSON fixture.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _case(index: int, split: str, *, gold: bool | None, task: str = "table") -> dict[str, Any]:
    return {
        "id": f"decision-{index:03d}",
        "family": "financial",
        "task": task,
        "split": split,
        "question": "Is this one table?",
        "state": {"words": [index]},
        "gold": gold,
        "baseline_probability": 0.6,
        "baseline_answerable": 0.7,
    }


def _pilot(tmp_path: Path) -> Path:
    root = tmp_path / "decisions"
    cases = [
        _case(0, "calibration", gold=True),
        _case(1, "test", gold=True),
        _case(2, "test", gold=False),
        _case(3, "test", gold=None),
        _case(4, "test", gold=True, task="wrap"),
    ]
    model = "openai/gpt-6-luna-decisions@resolved-b1"
    predictions = [
        {"case_id": "decision-000", "model": model, "p_yes": 0.9, "p_answerable": 0.95, "request_index": 7},
        {"case_id": "decision-001", "model": model, "p_yes": 0.95, "p_answerable": 0.95, "request_index": 8},
        {"case_id": "decision-002", "model": model, "p_yes": 0.7, "p_answerable": 0.9},
        {"case_id": "decision-003", "model": model, "p_yes": 0.2, "p_answerable": 0.3},
        {"case_id": "decision-004", "model": model, "error": "RuntimeError", "request_index": 9},
    ]
    _write(root / "cases" / "cases.json", cases)
    _write(root / "predictions.json", {"predictions": predictions, "cases_sha256": "synthetic"})
    _write(root / "evaluation.json", evaluate(cases, predictions))
    entry = {"requested_model": "openai/gpt-6-luna-decisions", "case_count": 1, "elapsed_ms": 250.0}
    _write(
        root / "ledger.json",
        {
            "requests": [
                {
                    **entry,
                    "index": 7,
                    "tag": f"{model}/batch/000",
                    "accounted_usd": 0,
                    "cost_status": "provider-reported USD",
                    "response_file": "response-007.json",
                },
                {
                    **entry,
                    "index": 8,
                    "tag": f"{model}/batch/001",
                    "accounted_usd": 0.004,
                    "cost_status": "provider-reported USD",
                    "response_file": "response-008.json",
                },
                {**entry, "index": 9, "tag": f"{model}/batch/002", "accounted_usd": 0.3, "cost_status": "reserved"},
            ]
        },
    )
    _write(root / "response-007.json", {"usage": {"input_tokens": 1000, "output_tokens": 0, "cost": 0}})
    _write(root / "response-008.json", {"usage": {"input_tokens": 1000, "output_tokens": 0, "cost": 0.004}})
    _write(
        root / "langfuse" / "catalog-prices.json",
        {"prices": {"openai/gpt-6-luna-decisions": {"input": 1e-07, "output": 0.0}}},
    )
    _write(
        root / "task-routing.json",
        {
            "selection": "known calibration accuracy",
            "tasks": {
                task: {
                    "chosen_model": model,
                    "calibration": {"known_correct": correct_cal, "known_count": count_cal},
                    "test": {"known_correct": correct, "known_count": count},
                }
                for task, correct_cal, count_cal, correct, count in (("table", 1, 1, 1, 2), ("wrap", 0, 0, 0, 1))
            },
        },
    )
    return root


def test_pilot_keeps_failures_and_matches_retained_evaluation(tmp_path: Path) -> None:
    _pilot(tmp_path)
    (experiment,) = list(decisions.collect(tmp_path))
    counts = validate(experiment)
    assert experiment.dataset == "exp/decisions/pilot-v1"
    assert counts["items"] == 5
    runs = {run.name: run for run in experiment.runs}
    assert set(runs) == {"baseline", "openai/gpt-6-luna-decisions@resolved-b1", decisions.ROUTER}
    luna = runs["openai/gpt-6-luna-decisions@resolved-b1"]
    assert len(luna.rows) == 5
    rows = {row.item_key: row for row in luna.rows}
    assert rows["decision-004"].scores["failed"] == 1.0
    assert rows["decision-004"].scores["correct"] == 0.0
    assert rows["decision-004"].metadata["status"] == "failed"
    assert "correct" not in rows["decision-003"].scores
    assert rows["decision-002"].scores["correct"] == 0.0
    assert rows["decision-001"].scores["correct"] == 1.0
    assert luna.scores["test_forced_correct"] == 1
    assert luna.scores["test_labeled_count"] == 3
    assert luna.scores["test_failures"] == 1
    assert luna.metadata["retained_mismatch"] is None
    assert runs[decisions.ROUTER].metadata["retained_mismatch"] is None
    assert runs[decisions.ROUTER].scores["test_forced_correct"] == 1


def test_pilot_cost_keeps_reported_zero_estimates_and_reservations_distinct(tmp_path: Path) -> None:
    _pilot(tmp_path)
    (experiment,) = list(decisions.collect(tmp_path))
    luna = next(run for run in experiment.runs if run.name.startswith("openai/"))
    rows = {row.item_key: row for row in luna.rows}
    zero = rows["decision-000"].metadata
    assert zero["provider_reported_usd"] == 0
    assert zero["estimated_usd"] == pytest.approx(1e-04)
    assert zero["cost_basis"] == "catalog estimate"
    assert rows["decision-001"].metadata["provider_reported_usd"] == 0.004
    assert "estimated_usd" not in rows["decision-001"].metadata
    reserved = rows["decision-004"].metadata
    assert reserved["reservation_usd"] == 0.3
    assert "effective_usd" not in reserved
    assert "provider_reported_usd" not in reserved
    assert "request_index" not in rows["decision-002"].metadata
    assert luna.metadata["cost_unknown_cost_requests"] == 1
    assert luna.metadata["cost_effective_usd"] is None
    assert luna.metadata["ledger_requests"] == 3


def test_pilot_records_retained_mismatch(tmp_path: Path) -> None:
    root = _pilot(tmp_path)
    report = json.loads((root / "evaluation.json").read_text())
    report["models"]["openai/gpt-6-luna-decisions@resolved-b1"]["test_fixed"]["forced_correct"] = 3
    _write(root / "evaluation.json", report)
    (experiment,) = list(decisions.collect(tmp_path))
    luna = next(run for run in experiment.runs if run.name.startswith("openai/"))
    assert "test_forced_correct" in luna.metadata["retained_mismatch"]


def test_context_runs_score_exact_regions(tmp_path: Path) -> None:
    def record(case: str, *, exact: bool, choice: str) -> dict[str, Any]:
        return {
            "case_id": case,
            "family": "financial",
            "model": "perplexity/pplx-decider-v1.1-27b",
            "arm": "native",
            "pdf_sha256": "a" * 64,
            "expected_document": "A",
            "expected_evidence": "A",
            "answer": {"choice": choice, "probabilities": {"A": 0.7, "B": 0.2, "unresolved": 0.1}},
            "score": {"valid": True, "source_conservation": True, "region_exact": exact, "record_f1": float(exact)},
            "evidence_score": {"region_exact": exact, "record_f1": float(exact)},
            "entry": {"index": 1, "cost_status": "provider-reported USD", "accounted_usd": 1e-05},
            "usage": {"input_tokens": 10, "output_tokens": 0, "cost": 1e-05},
            "replayed": False,
        }

    records = [record("c-00", exact=True, choice="A"), record("c-01", exact=False, choice="unresolved")]
    _write(tmp_path / "decisions" / "context-run-initial.json", {"records": records, "evidence_status": "DEV"})
    (experiment,) = list(decisions_context.collect(tmp_path))
    validate(experiment)
    (run,) = experiment.runs
    assert run.name == "initial/perplexity/pplx-decider-v1.1-27b/native"
    assert run.scores["region_exact_count"] == 1
    assert run.scores["abstained_count"] == 1
    assert run.rows[0].scores["p_expected"] == 0.7
    assert run.metadata["cost_unique_requests"] == 1


def _lowlevel(tmp_path: Path, known_exact: int = 1) -> None:
    wave = tmp_path / "decisions" / "lowlevel-v1" / "basic-final"
    score = {
        "choice_correct": True,
        "description_partition_exact": True,
        "answerable": True,
        "ambiguous_abstention": False,
        "candidate_oracle": True,
        "output": {"groups": [["g1"]], "conservation": True},
    }
    outcomes = [
        {
            "id": "p1",
            "model": "m",
            "arm": "words",
            "family": "wrap",
            "expected": "join",
            "status": "ok",
            "score": score,
        },
        {
            "id": "p2",
            "model": "m",
            "arm": "words",
            "family": "wrap",
            "expected": "split",
            "status": "failed",
            "refused": False,
            "reason": "model stopped on first failure; no retry",
            "score": None,
        },
    ]
    cohort = {"model": "m", "arm": "words", "inputs": 2, "scored": 1, "known_inputs": 2, "known_exact": known_exact}
    _write(
        wave / "evaluation.json",
        {
            "experiment": "L001",
            "outcomes": outcomes,
            "cohorts": [{**cohort, "ambiguous_inputs": 0, "ambiguous_abstentions": 0, "failures": 1}],
            "native_baseline": [{"id": "p1", "family": "wrap", "expected": "join", "choice": "join", "score": score}],
        },
    )
    _write(wave / "private-targets.json", [{"id": "p1", "expected": "join", "expected_groups": [["g1"]]}])


def test_lowlevel_keeps_failed_inputs_unscored(tmp_path: Path) -> None:
    _lowlevel(tmp_path)
    (experiment,) = list(decisions_lowlevel.collect(tmp_path))
    validate(experiment)
    runs = {run.name: run for run in experiment.runs}
    words = runs["m/words"]
    failed = next(row for row in words.rows if row.item_key == "p2")
    assert failed.scores == {}
    assert failed.metadata["status"] == "failed"
    assert words.scores["known_exact_rate"] == 0.5
    assert words.metadata["retained_mismatch"] is None
    assert runs["native-baseline"].scores["known_exact"] == 1


def test_lowlevel_flags_cohort_disagreement(tmp_path: Path) -> None:
    _lowlevel(tmp_path, known_exact=2)
    (experiment,) = list(decisions_lowlevel.collect(tmp_path))
    words = next(run for run in experiment.runs if run.name == "m/words")
    assert "known_exact" in words.metadata["retained_mismatch"]


def test_cohort_slices_and_unscored_ambiguous_pages(tmp_path: Path) -> None:
    directory = tmp_path / "decisions" / "prompt-sweep-v1" / "original" / "structure" / "P001"
    rows = [
        {"id": "case-000", "kind": "borderless", "selection": "rolling", "conservation": True,
         "scores": {"exact_page": True, "exact_cells": True, "exact_spans": True, "owned_values": 3,
                    "owned_words": 4, "false_positive_page": False}},
        {"id": "case-001", "kind": "ambiguous", "selection": "not_table", "conservation": True,
         "truth_status": "ambiguous-unscored", "scores": None},
    ]  # fmt: skip
    slices = {"borderless": {"pages": 1, "exact_page": 1, "owned_values": 3, "false_positive_page": 0}}
    _write(directory / "evaluation.json", {"cohorts": {"m/image512": {"pages": 2, "rows": rows, "slices": slices}}})
    (experiment,) = list(decisions_cohorts.collect(tmp_path))
    validate(experiment)
    assert experiment.dataset == "exp/decisions/prompt-sweep-v1/original"
    (run,) = experiment.runs
    assert run.name == "structure/P001/m/image512"
    assert run.scores["borderless_exact_page"] == 1
    assert run.metadata["retained_mismatch"] is None
    ambiguous = next(row for row in run.rows if row.item_key == "case-001")
    assert ambiguous.scores == {"source_conservation": 1.0}
    assert ambiguous.metadata["status"] == "ambiguous-unscored"


def test_omnidoc_unknown_labels_and_refusals_stay_unscored(tmp_path: Path) -> None:
    wave = tmp_path / "decisions" / "omnidoc-dev-presence-v9"
    requests = [
        {"key": "observation-00/rgb128/m", "model": "m", "arm": "rgb128", "status": "prepared"},
        {"key": "observation-01/rgb128/m", "model": "m", "arm": "rgb128", "status": "refused"},
    ]
    _write(wave / "manifest.json", {"requests": requests})
    _write(
        wave / "private-labels.json",
        {
            "observations": [
                {"key": "observation-00/rgb128/m", "labels": [True, False, None]},
                {"key": "observation-01/rgb128/m", "labels": [False, False, None]},
            ]
        },
    )
    _write(
        wave / "results.json",
        {"rows": [{"key": "observation-00/rgb128/m", "model": "m", "status": "ok", "probabilities": [0.8, 0.6, 0.9]}]},
    )
    confusion = [
        {"tp": 1, "tn": 0, "fp": 0, "fn": 0, "unknown": 0, "unscored": 1},
        {"tp": 0, "tn": 0, "fp": 1, "fn": 0, "unknown": 0, "unscored": 1},
        {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "unknown": 2, "unscored": 0},
    ]
    _write(wave / "evaluation.json", {"groups": {"m/rgb128": {"confusion": confusion}}})
    (experiment,) = list(decisions_waves.collect(tmp_path))
    validate(experiment)
    (run,) = experiment.runs
    assert run.metadata["retained_mismatch"] is None
    assert run.scores["completed_pages"] == 1
    assert run.scores["table_accuracy"] == 1.0
    refused = next(row for row in run.rows if row.item_key == "observation-01/rgb128")
    assert refused.metadata["status"] == "refused"
    assert refused.scores == {}
    answered = next(row for row in run.rows if row.item_key == "observation-00/rgb128")
    assert "multiple_columns_correct" not in answered.scores


def test_image_wave_keeps_unattempted_cases(tmp_path: Path) -> None:
    wave = tmp_path / "decisions" / "image-context"
    observation = {
        "case_id": "c-0",
        "answer": {"choice": "A", "probabilities": {"A": 0.9, "B": 0.05, "unresolved": 0.05}},
        "expected_document": "A",
        "score": {"region_exact": True, "record_f1": 1.0},
    }
    batch = {"model": "m", "scope": "page", "arm": "rgb-128", "case_ids": ["c-0"], "expected_document": ["A"]}
    batches = [
        {**batch, "status": "ok", "observations": [observation]},
        {**batch, "arm": "rgb-256", "status": "unattempted", "case_indices": [0]},
    ]
    _write(wave / "results.json", {"batches": batches})
    summary = [{"model": "m", "scope": "page", "arm": "rgb-128", "n": 1, "exact": 1, "errors": 0, "unattempted": 0}]
    _write(wave / "summary.json", {"rows": summary})
    (experiment,) = list(decisions_waves.collect(tmp_path))
    validate(experiment)
    runs = {run.name: run for run in experiment.runs}
    assert runs["m/page/rgb-128"].metadata["retained_mismatch"] is None
    assert runs["m/page/rgb-128"].rows[0].scores["choice_correct"] == 1.0
    skipped = runs["m/page/rgb-256"]
    assert skipped.rows[0].metadata["status"] == "unattempted"
    assert skipped.rows[0].scores == {}
    assert skipped.scores["unattempted"] == 1


def test_protected_paths_are_refused(tmp_path: Path) -> None:
    protected = tmp_path / "silver-heldout-v1"
    (protected / "decisions").mkdir(parents=True)
    for module in (decisions, decisions_context, decisions_lowlevel, decisions_cohorts, decisions_waves):
        with pytest.raises(PermissionError):
            list(module.collect(protected))
    with pytest.raises(PermissionError):
        decisions_common.ledger(protected / "decisions")


def test_cost_summary_never_completes_partial_totals() -> None:
    summary = decisions_common.cost_summary(
        [
            {"request_index": 1, "provider_reported_usd": 0.0, "effective_usd": 0.001, "estimated_usd": 0.001},
            {"request_index": 1, "provider_reported_usd": 0.0, "effective_usd": 0.001, "estimated_usd": 0.001},
            {"request_index": 2, "reservation_usd": 0.3},
        ]
    )
    assert summary["unique_requests"] == 2
    assert summary["provider_reported_usd"] == 0.0
    assert summary["estimated_usd"] == 0.001
    assert summary["effective_usd"] is None
    assert summary["effective_usd_known"] == 0.001
    assert summary["unknown_cost_requests"] == 1
