"""Offline scoring distinguishes model success, retention, false positives and coverage."""
# ruff: noqa: SLF001 - verify target-access ordering at the pin boundary.
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_extension_score as score
from bench.pipeline_assembly import _clean_table

CORPUS = (Path(__file__).resolve().parents[1]
          / "bench/results/pdf-master-artifacts/decisions/p003/extension64-inventor-v3")


def fixture() -> tuple[dict, dict, dict]:
    source = {"page_size": [0, 0, 100, 100], "words": [
        {"id": "a", "text": "$10.00", "bbox": [1, 1, 8, 8]},
        {"id": "b", "text": "$20.00", "bbox": [12, 1, 19, 8]},
    ]}
    lookup = {w["id"]: w for w in source["words"]}
    table = {"row_count": 1, "col_count": 2, "cells": [{"source_ids": ["a"]}, {"source_ids": ["b"]}],
             "spans": [{"row": 0, "column": c, "row_span": 1, "column_span": 1} for c in range(2)]}
    good = {"id": "transport-annotation", "tables": [{**_clean_table(table, lookup), "bbox": [0, 0, 20, 10]}],
            "unresolved_ids": []}
    wrong = deepcopy(good)
    wrong["tables"][0]["cells"].reverse()
    wrong["tables"][0] = {**_clean_table(wrong["tables"][0], lookup), "bbox": [0, 0, 20, 10]}
    menus = {}
    targets = []
    for ident in ("selected", "abstained", "failed", "missing"):
        baseline = wrong if ident in {"selected", "abstained"} else good
        menus[ident] = {"source": source, "baseline": baseline,
                        "candidates": [{"id": "candidate-a", "state": good}, {"id": "candidate-b", "state": wrong}]}
        targets.append({"id": ident, "structural_scored": True, "tables": deepcopy(good["tables"])})
    frozen = {"targets": targets, "menus": menus,
              "stress": {ident: {"treatments": []} for ident in menus}, "receipts": {}}
    return frozen, good, wrong


def test_full_intended_denominator_keeps_failures_and_baseline_retention_separate() -> None:
    frozen, good, wrong = fixture()
    selected = deepcopy(good)
    selected.pop("id")
    report = {"config": {"page_ids": list(frozen["menus"]), "run_id": "test"}, "results": [
        {"id": "selected", "status": "selected", "selected_state": selected, "baseline_state": wrong},
        {"id": "abstained", "status": "abstained", "selected_state": None, "baseline_state": wrong},
        {"id": "failed", "status": "transport_error", "selected_state": None, "baseline_state": good},
    ], "costs": {"provider_reported_usd": 0, "effective_estimate_usd": None}, "resources": {"cpu_seconds": 1}}
    result = score.score_run(frozen, report)
    assert result["intended_pages"] == 4
    assert result["status_counts"] == {"selected": 1, "abstained": 1, "transport_error": 1, "not_attempted": 1}
    assert result["model_selected_only"]["strict"]["totals"]["all_page_errors"] == 3
    assert result["model_selected_only"]["strict"]["totals"]["exact_page"] == 1
    assert result["composed_with_baseline_retention"]["strict"]["totals"]["exact_page"] == 3
    assert result["comparisons"]["improved"] == result["comparisons"]["selected_improved"] == 1
    assert result["costs"] == report["costs"]
    assert result["resources"] == report["resources"]


def test_invented_or_unfrozen_selected_states_are_invalid_and_do_not_improve_scores() -> None:
    frozen, good, wrong = fixture()
    invented = deepcopy(good)
    invented["tables"][0]["cells"][0]["source_ids"] = ["invented"]
    result = score.score_run(frozen, {"config": {"page_ids": ["selected"]}, "results": [
        {"id": "selected", "status": "selected", "selected_state": invented, "baseline_state": wrong},
    ]})
    assert result["status_counts"] == {"invalid": 1}
    assert result["pages"][0]["baseline_retained"]
    assert result["pages"][0]["invalid_reason"] == "Unknown source ID"
    assert result["model_selected_only"]["strict"]["totals"]["strict_exact_cells"] == 0
    outside_menu = deepcopy(good)
    outside_menu["tables"][0]["bbox"] = [0, 0, 25, 10]
    result = score.score_run(frozen, {"config": {"page_ids": ["selected"]}, "results": [
        {"id": "selected", "status": "selected", "selected_state": outside_menu, "baseline_state": wrong},
    ]})
    assert result["status_counts"] == {"invalid": 1}
    assert "outside frozen" in result["pages"][0]["invalid_reason"]


def test_negative_false_positive_regresses_despite_zero_expected_exact_cells() -> None:
    frozen, good, _wrong = fixture()
    empty = {"tables": [], "unresolved_ids": ["a", "b"]}
    frozen["menus"]["selected"]["baseline"] = empty
    frozen["menus"]["selected"]["candidates"].append({"id": "empty", "state": empty})
    frozen["targets"][0]["tables"] = []
    result = score.score_run(frozen, {"config": {"page_ids": ["selected"]}, "results": [
        {"id": "selected", "status": "selected", "selected_state": good, "baseline_state": empty},
    ]})
    assert result["comparisons"]["selected_regressed"] == 1
    assert result["pages"][0]["strict_change"] == "regressed"
    assert not result["pages"][0]["model_negative_presence_correct"]
    assert result["model_selected_only"]["v2"]["counts"]["extra_tables"] == 1
    assert result["model_selected_only"]["wrap"]["counts"]["extra_tables"] == 1


def test_candidate_ceiling_is_offline_and_preserves_every_missing_menu_answer() -> None:
    frozen, _good, wrong = fixture()
    frozen["menus"]["failed"]["candidates"] = [{"id": "wrong-only", "state": wrong}]
    result = score.coverage(frozen)
    assert result["intended_pages"] == 4
    assert result["coverage_failures"] == ["failed"]
    assert result["independent_candidate_ceilings"]["strict"]["strict"]["totals"]["exact_page"] == 3
    assert "never" in result["scope"]


def test_target_hash_pin_and_source_admission_before_target_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    changed = tmp_path / "private-targets.json"
    changed.write_text(json.dumps({"pages": []}))
    with pytest.raises(ValueError, match="changed"):
        score._read(changed, score.PINS["private-targets.json"])
    if not CORPUS.exists():
        pytest.skip("Frozen source corpus is a local ignored artifact")
    for name in ("manifest.json", "frozen.json", "source-inventory.json"):
        (tmp_path / name).write_bytes((CORPUS / name).read_bytes())
    read_names = []
    original = score._read

    def track(path: Path, expected: str) -> dict:
        read_names.append(path.name)
        return original(path, expected)

    monkeypatch.setattr(score, "_read", track)
    with pytest.raises(FileNotFoundError):
        score.load_frozen(tmp_path)
    assert "private-targets.json" not in read_names


def test_rejects_duplicate_unknown_results_and_success_filtered_intended_ids() -> None:
    frozen, good, wrong = fixture()
    row = {"id": "selected", "status": "selected", "selected_state": good, "baseline_state": wrong}
    with pytest.raises(ValueError, match="Duplicate"):
        score.score_run(frozen, {"config": {"page_ids": ["selected"]}, "results": [row, row]})
    with pytest.raises(ValueError, match="outside-intended"):
        score.score_run(frozen, {"config": {"page_ids": ["failed"]}, "results": [row]})
    result = score.score_run(frozen, {"config": {}, "results": [row]})
    assert result["intended_pages"] == 4
    assert result["status_counts"]["not_attempted"] == 3
