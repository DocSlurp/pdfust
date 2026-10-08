from __future__ import annotations

import copy
import json

import pytest
from bench.decision_analysis import analyze, render_analysis
from bench.decision_controls import build_controls
from bench.decision_eval import evaluate


def case(identifier: str, split: str, *, gold: bool | None = True) -> dict:
    return {
        "id": identifier,
        "family": "invoice",
        "task": "assignment",
        "split": split,
        "gold": gold,
        "baseline_probability": 0.95,
        "baseline_answerable": 0.95,
        "state": {
            "task": "assignment",
            "candidate": {"label": [0], "value": [1], "alternatives": [[1]]},
            "words": [
                {"id": 0, "text": "USD", "bbox": [0, 0, 10, 10]},
                {"id": 1, "text": "120", "bbox": [20, 0, 30, 10]},
            ],
        },
    }


def prediction(identifier: str, model: str, probability: float = 0.95) -> dict:
    return {"case_id": identifier, "model": model, "p_yes": probability, "p_answerable": 0.95}


def test_actual_assembly_counts_wrong_unknown_refused_and_missing_without_source_changes() -> None:
    cases = [
        case("right", "test"),
        case("wrong", "test", gold=False),
        case("unknown", "test", gold=None),
        case("refused", "test"),
        case("missing", "test"),
    ]
    cases[3]["state"]["candidate"]["value"] = [0]
    frozen = copy.deepcopy(cases)
    predictions = [prediction(item["id"], "small@rich") for item in cases[:-1]]
    result = analyze(cases, predictions, evaluate(cases, predictions))
    cohort = result["cohorts"]["small@rich"]["test"]
    assert cohort["quality"]["status"] == "incomplete"
    assert cohort["quality"]["missing_predictions"] == 1
    assert cohort["quality"]["known_accuracy"] == 0.5
    assembly = cohort["assembly_fixed"]
    assert assembly["affirmative_requested"] == 4
    assert assembly["affirmative_applied"] == 3
    assert assembly["applied_correct"] == 1
    assert assembly["applied_wrong"] == 1
    assert assembly["applied_unknown"] == 1
    assert assembly["constraint_refusal_reasons"] == {"duplicate_relation_ids": 1}
    assert assembly["source_word_conservation"]
    assert assembly["source_words_before"] == assembly["source_words_after"] == 10
    assert cohort["assembly_selected"]["affirmative_applied"] == 0
    assert cases == frozen
    json.dumps(result, allow_nan=False)
    markdown = render_analysis(result)
    assert "incomplete" in markdown
    assert '"bbox"' not in markdown
    assert "native extractor quality" in markdown


def test_singleton_isolation_never_combines_splits_or_different_variants() -> None:
    cases = [case("cal", "calibration"), case("test", "test"), case("failed", "test")]
    predictions = [
        prediction("cal", "small@rich", 0.49),
        prediction("cal", "small@rich-b1", 0.51),
        prediction("test", "small@rich", 0.95),
        prediction("test", "small@rich-b1", 0.05),
        prediction("failed", "small@rich"),
        {"case_id": "failed", "model": "small@rich-b1", "error": "timeout"},
        prediction("cal", "small@resolved-b1"),
    ]
    result = analyze(cases, predictions, evaluate(cases, predictions))
    assert len(result["isolation"]) == 1
    comparison = result["isolation"][0]
    assert comparison["batch_model"] == "small@rich"
    assert comparison["calibration"]["paired_successes"] == 1
    assert comparison["calibration"]["forced_answer_flips"] == 1
    assert comparison["calibration"]["fixed_outcome_flips"] == 0
    assert comparison["test"]["paired_successes"] == 1
    assert comparison["test"]["unpaired_or_failed"] == 1
    assert comparison["test"]["forced_answer_flips"] == 1
    assert comparison["test"]["fixed_outcome_flips"] == 1
    assert result["cohorts"]["small@rich-b1"]["test"]["quality"]["status"] == "incomplete"


def test_selected_policy_is_reused_for_application_without_test_tuning() -> None:
    cases = [case(f"cal-{index}", "calibration") for index in range(40)] + [case("test", "test", gold=False)]
    predictions = [prediction(item["id"], "small@rich") for item in cases]
    report = evaluate(cases, predictions)
    assert not report["models"]["small@rich"]["selected_policy"]["abstain_all"]
    result = analyze(cases, predictions, report)
    assembly = result["cohorts"]["small@rich"]["test"]["assembly_selected"]
    assert assembly["affirmative_applied"] == 1
    assert assembly["applied_wrong"] == 1
    assert assembly["source_word_conservation"]


def test_failed_prediction_never_applies_edge_despite_present_scores() -> None:
    cases = [case("failed", "test")]
    predictions = [{**prediction("failed", "small@rich"), "error": "invalid_output"}]
    result = analyze(cases, predictions, evaluate(cases, predictions))
    entry = result["cohorts"]["small@rich"]["test"]
    assert entry["quality"]["known_accuracy"] == 0
    assert entry["quality"]["failed_predictions"] == 1
    assert entry["assembly_fixed"]["affirmative_requested"] == 0
    assert entry["assembly_fixed"]["constraint_refusals"] == 0


def test_analysis_rejects_duplicate_predictions() -> None:
    cases = [case("test", "test")]
    predictions = [prediction("test", "small@rich")]
    report = evaluate(cases, predictions)
    with pytest.raises(ValueError, match="duplicate"):
        analyze(cases, predictions * 2, report)


def test_grounded_controls_report_describes_actual_sources_and_label_scope() -> None:
    cases = build_controls()
    result = analyze(cases, [], evaluate(cases, []))
    markdown = render_analysis(result)
    assert len(cases) == 8
    assert len({item["provenance"]["pdf_sha256"] for item in cases}) == 6
    assert result["label_counts"] == {"calibration": {}, "test": {"true": 4, "false": 4}}
    assert "8 grounded regional table gates contain 4 positive and 4 negative" in markdown
    assert "6 original sources" in markdown
    assert "NICS and Senate each contribute two clips" in markdown
    assert "test-only, with no calibration cases" in markdown
    assert "not learned from the controls" in markdown
    assert "individual-cell" in markdown
    assert "illustrative geometry/type heuristic" in markdown
    assert "Source-word conservation" in markdown
    assert "synthetic author intent" not in markdown
    assert "label priors differ" not in markdown
    assert "continued detail" not in markdown
    assert "Provisional estimate only" not in markdown
