"""Synthetic-fixture tests for the P003 Langfuse adapters (no network, no retained artifacts)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters import (
    pipeline_p003,
    pipeline_p003_continuation,
    pipeline_p003_extension,
    pipeline_p003_micro,
    pipeline_p003_synthetic,
)
from bench.langfuse_adapters.base import clean_scores, validate

if TYPE_CHECKING:
    from pathlib import Path

GOLD_SHA = "68d1800d" + "0" * 56


def _write(path: Path, value: Any) -> None:  # noqa: ANN401 - arbitrary JSON fixture.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _page(page_id: str, *, strict: int, expected: int = 10, error: bool = False, scored: bool = True) -> dict[str, Any]:
    return {
        "id": page_id,
        "structural_scored": scored,
        "error": error,
        "malformed": False,
        "expected_tables": 1,
        "detected_tables": 0 if error else 1,
        "matched_tables": 0 if error else 1,
        "missing_tables": 1 if error else 0,
        "false_positive_tables": 0,
        "expected_cells": expected,
        "predicted_cells": 0 if error else expected,
        "correct_structure_cells": strict,
        "correct_text_cells": strict,
        "complete_tables": int(strict == expected),
        "exact_page": strict == expected,
        "strict_exact_cells": strict,
        "text_edit_distance": 0,
        "reference_characters": 40,
        "positive_page": True,
        "negative_page": False,
        "matches": [],
    }


def _evaluation(name: str, pages: list[dict[str, Any]], costs: dict[str, Any]) -> dict[str, Any]:
    scored = [p for p in pages if p["structural_scored"]]
    keys: tuple[str, ...] = (
        "error",
        "malformed",
        "detected_tables",
        "matched_tables",
        "missing_tables",
        "false_positive_tables",
    )
    keys += ("predicted_cells", "correct_structure_cells", "correct_text_cells", "complete_tables", "exact_page")
    keys += ("strict_exact_cells", "text_edit_distance", "expected_cells")
    totals = {k: sum(int(p[k]) for p in scored) for k in keys}
    totals["all_page_errors"] = sum(int(p["error"]) for p in pages)
    positive = [p for p in pages if p["positive_page"]]
    return {
        "runs": [
            {
                "name": name,
                "evaluation_scope": "complete pipeline",
                "dataset_sha256": GOLD_SHA,
                "config": {"model": "vendor/model", "preset": "ordinal"},
                "intended_pages": len(pages),
                "scores": totals,
                "page_scores": pages,
                "positive_macro": {
                    "positive_pages": len(positive),
                    "strict_exact_cell_recall": sum(p["strict_exact_cells"] / p["expected_cells"] for p in positive)
                    / len(positive),
                },
                "costs": costs,
                "resources": {"cpu_seconds": 3.0, "peak_sampled_rss_bytes": 1024, "wall_seconds": 2.0},
                "artifacts": [{"id": p["id"], "markdown_sha256": "ab" * 32, "operational": True} for p in pages],
            }
        ]
    }


def _tables_fixture(artifacts: Path) -> None:
    campaign = artifacts / "pipeline-p003"
    pages = [_page("p1", strict=10), _page("p2", strict=4), _page("p3", strict=0, error=True, scored=False)]
    exact = {
        "effective_api_usd": 0.02,
        "provider_reported_subtotal_usd": 0.02,
        "ledger_attempts": 2,
        "missing_provider_charge_count": 0,
        "cost_bases": {"provider-reported USD": 2},
    }
    byok = {
        "effective_api_usd": 0.05,
        "provider_reported_subtotal_usd": 0,
        "ledger_attempts": 2,
        "missing_provider_charge_count": 0,
        "cost_bases": {"provider-reported BYOK upstream plus gateway USD": 2},
    }
    reserved = {
        "effective_api_usd": None,
        "provider_reported_subtotal_usd": 0,
        "ledger_attempts": 2,
        "accounted_usd_including_reservations": 0.6,
        "cost_bases": {"catalog estimate": 1, "reserved": 1},
    }
    _write(campaign / "parallel-q-v1" / "arm-a" / "evaluation.json", _evaluation("arm-a", pages, exact))
    _write(campaign / "parallel-q-v1" / "arm-b" / "evaluation.json", _evaluation("arm-b", pages, byok))
    _write(campaign / "parallel-q-v1" / "arm-a" / "history" / "evaluation.json", _evaluation("copy", pages, exact))
    (campaign / "parallel-q-v1" / "arm-c").mkdir(parents=True)
    (campaign / "parallel-q-v1" / "arm-c" / "evaluation.json").write_text('{"runs": [', encoding="utf-8")
    _write(campaign / "screen-x" / "evaluation.json", _evaluation("screen-x", pages, reserved))
    overlay = _evaluation("screen-x", pages, reserved)
    overlay["runs"][0]["cost_reconciliation"] = {
        "reconciled": {"effective_api_usd": 0.01, "ledger_attempts": 2, "cost_bases": {"provider-reported USD": 2}}
    }
    _write(campaign / "screen-x" / "evaluation-cost-reconciled.json", overlay)
    _write(campaign / "transcription-screen-v1-status.json", {"arms": [{"name": "screen-x"}]})
    _write(
        campaign / "structure-grid-v1" / "evaluation.json",
        {
            "scope": "offline treatments",
            "treatments": {"t0.3": {"pages": pages, "totals": _evaluation("t", pages, {})["runs"][0]["scores"]}},
        },
    )


def test_tables_groups_queues_and_keeps_every_page(tmp_path: Path) -> None:
    _tables_fixture(tmp_path)
    experiments = {e.dataset: e for e in pipeline_p003.collect(tmp_path)}
    assert set(experiments) == {
        "exp/pipeline-p003/parallel-q-v1/screen-3p",
        "exp/pipeline-p003/transcription-screen-v1/screen-3p",
        "exp/pipeline-p003/structure-grid-v1/screen-3p",
    }
    queue = experiments["exp/pipeline-p003/parallel-q-v1/screen-3p"]
    assert validate(queue)["rows"] == 6
    assert queue.labels["skipped_files"] == 1
    assert [r.name for r in queue.runs] == ["parallel-q-v1/arm-a", "parallel-q-v1/arm-b"]
    arm_a, arm_b = queue.runs
    assert arm_a.metadata["aggregate_check"] == "ok"
    statuses = {row.item_key: row.metadata["status"] for row in arm_a.rows}
    assert statuses == {"p1": "scored", "p2": "scored", "p3": "error"}
    p2 = next(row for row in arm_a.rows if row.item_key == "p2")
    assert clean_scores(p2.scores)["strict_exact_cell_recall"] == 0.4
    p3 = next(row for row in arm_a.rows if row.item_key == "p3")
    assert set(p3.scores) == {"structural_scored", "error", "malformed"}
    assert arm_a.scores["provider_reported_usd"] == 0.02
    assert "provider_reported_usd" not in arm_b.scores
    assert arm_b.scores["effective_usd"] == 0.05
    assert arm_b.scores["byok_provider_reported_attempts"] == 2
    item = next(i for i in queue.items if i.key == "p1")
    assert item.expected["expected_cells"] == 10
    screen = experiments["exp/pipeline-p003/transcription-screen-v1/screen-3p"].runs[0]
    assert "effective_usd" not in screen.scores
    assert "provider_reported_usd" not in screen.scores
    assert screen.scores["reconciled_effective_usd"] == 0.01
    grid = experiments["exp/pipeline-p003/structure-grid-v1/screen-3p"].runs[0]
    assert grid.name == "structure-grid-v1/t0.3"


def _synthetic_fixture(artifacts: Path) -> None:
    campaign = artifacts / "pipeline-p003"
    cases = [
        {"id": "s1", "kind": "row", "expected_choice": "same", "evidence_limitation": False, "pdf_sha256": "a"},
        {"id": "s2", "kind": "cell", "expected_choice": "separate", "evidence_limitation": True, "pdf_sha256": "b"},
        {"id": "s3", "kind": "wrap", "expected_choice": "same", "evidence_limitation": False, "pdf_sha256": "c"},
    ]
    _write(
        campaign / "synthetic-micro-relations-v2" / "private-gold.json", {"source_frozen_sha256": "F", "cases": cases}
    )
    rows = [
        {"index": 0, "id": "s1", "kind": "row", "status": "valid_nonabstaining", "receipt": {"choice": "same"}},
        {"index": 1, "id": "s2", "kind": "cell", "status": "malformed_response"},
        {"index": 2, "id": "s3", "kind": "wrap", "status": "valid_abstention", "receipt": {"choice": "unresolved"}},
    ]
    secondary = [
        dict(rows[0]),
        {**rows[1], "status": "valid_nonabstaining", "receipt": {"choice": "separate"}},
        rows[2],
    ]
    block = {"intended_count": 3, "valid_nonabstaining_count": 1, "author_label_matches": 1}
    scores = {
        "all_24": {**block, "strict_author_label_fraction": 1 / 3},
        "visually_cued_18": {"intended_count": 2, "valid_nonabstaining_count": 1, "author_label_matches": 1},
        "indeterminate_6": {"intended_count": 1, "valid_nonabstaining_count": 0, "author_label_matches": 0},
        "charges": {"ledger_attempts": 3, "provider_reported_usd": 0.003, "cost_bases": {"provider-reported USD": 3}},
    }
    arm = campaign / "parallel-synthetic48-v2" / "synth-m-r0"
    _write(
        arm / "synthetic-alias-evaluation.json",
        {
            "original_verified": {"source_frozen_sha256": "F", "rows": rows, "config": {"model": "m"}},
            "original_scores": scores,
            "secondary_verified": {"rows": secondary},
        },
    )
    _write(
        arm / "report.json",
        {"results": [{"index": i, "entry": {"provider_reported_usd": 0.001, "cost_status": "x"}} for i in range(3)]},
    )
    (campaign / "parallel-synthetic48-v2" / "logs").mkdir()


def test_synthetic_rows_follow_strict_denominator(tmp_path: Path) -> None:
    _synthetic_fixture(tmp_path)
    (experiment,) = pipeline_p003_synthetic.collect(tmp_path)
    assert experiment.dataset == "exp/pipeline-p003/parallel-synthetic48-v2/synthetic-relations-3"
    assert experiment.labels["skipped_arms"] == 0
    (run,) = experiment.runs
    assert run.metadata["aggregate_check"] == "ok"
    by_case = {row.item_key: clean_scores(row.scores) for row in run.rows}
    assert by_case["s1"]["author_label_match"] == 1.0
    assert by_case["s2"]["author_label_match"] == 0.0
    assert by_case["s2"]["malformed"] == 1.0
    assert by_case["s2"]["alias_replay_author_label_match"] == 1.0
    assert by_case["s3"]["abstained"] == 1.0
    assert by_case["s1"]["provider_reported_usd"] == 0.001
    assert run.scores["provider_reported_usd"] == 0.003
    assert next(i for i in experiment.items if i.key == "s2").expected == {"expected_choice": "separate"}


def _extension_score(page_ids: list[str]) -> dict[str, Any]:
    composed = [_page(i, strict=10 if i == "e1" else 5) for i in page_ids]
    totals = {k: sum(int(p[k]) for p in composed) for k in ("strict_exact_cells", "complete_tables", "exact_page")}
    view = {"strict": {"pages": composed, "totals": totals}, "v2": {"full_content_recall": 0.9}}
    return {
        "config": {"model": "m", "page_ids": page_ids},
        "intended_pages": len(page_ids),
        "pages": [
            {"id": "e1", "status": "selected", "changes": {"strict": "improved"}, "model_credit": True},
            {"id": "e2", "status": "not_attempted", "changes": {"strict": "unchanged"}, "model_credit": False},
        ],
        "composed_with_baseline_retention": view,
        "terminal_model_selected_only": view,
        "native_baseline": view,
        "comparisons_by_metric": {"strict": {"improved": 1, "unchanged": 1}},
        "costs": {"ledger_attempts": 1, "provider_reported_usd": 0.01, "cost_bases": {"provider-reported USD": 1}},
    }


def test_extension_skips_running_arms(tmp_path: Path) -> None:
    runs = tmp_path / "pipeline-p003" / "extension-v1" / "runs"
    _write(runs / "extension-v1-local-00" / "local-score-v1.json", _extension_score(["e1", "e2"]))
    (runs / "extension-v1-local-01").mkdir()
    (experiment,) = pipeline_p003_extension.collect(tmp_path)
    assert experiment.dataset == "exp/pipeline-p003/extension-v1/local-2p"
    assert experiment.labels["skipped_unscored_arms"] == 1
    (run,) = experiment.runs
    assert run.metadata["aggregate_check"] == "ok"
    rows = {row.item_key: clean_scores(row.scores) for row in run.rows}
    assert rows["e1"]["strict_improved"] == 1.0
    assert rows["e2"]["selected"] == 0.0
    assert run.scores["provider_reported_usd"] == 0.01


def test_micro_has_no_invented_correctness(tmp_path: Path) -> None:
    arm = tmp_path / "pipeline-p003" / "gateway-micro-v1" / "d1-micro-r0"
    results = [
        {
            "page_id": "p1",
            "pair_id": "q1",
            "status": "valid_nonabstaining",
            "receipt": {"decision": {"choice": "same", "confidence": 0.4}},
            "entry": {"cost_status": "provider-reported USD", "provider_reported_usd": 0.0},
        },
        {"page_id": "p1", "pair_id": "q2", "status": "not_attempted"},
    ]
    _write(arm / "report.json", {"results": results, "status_counts": {"valid_nonabstaining": 1, "not_attempted": 1}})
    (experiment,) = pipeline_p003_micro.collect(tmp_path)
    (run,) = experiment.runs
    assert run.metadata["aggregate_check"] == "ok"
    assert all(item.expected is None for item in experiment.items)
    names = {name for row in run.rows for name in clean_scores(row.scores)}
    assert "author_label_match" not in names
    assert clean_scores(run.rows[0].scores)["provider_reported_usd"] == 0.0


def test_continuation_keeps_excluded_cases(tmp_path: Path) -> None:
    content = {"supported": True, "precision": 0.5, "recall": 0.5, "counts": {"matched": 1, "reference_units": 2}}
    records = [
        {"case_id": "c0", "model": "m", "content": content, "strict_body_complete": False, "exclusion": None},
        {"case_id": "c1", "model": "m", "content": content, "exclusion": "author-unresolved"},
    ]
    report = {"records": records, "models": [{"model": "m", "known_body_content_recall": 0.5}]}
    _write(tmp_path / "pipeline-p003" / "continuation-oplog-evaluation-v1" / "report.json", report)
    (experiment,) = pipeline_p003_continuation.collect(tmp_path)
    (run,) = experiment.runs
    assert run.metadata["aggregate_check"] == "ok"
    statuses = {row.item_key: row.metadata["status"] for row in run.rows}
    assert statuses == {"c0": "scored", "c1": "excluded:author-unresolved"}
    assert "content_recall" not in run.rows[1].scores


def test_missing_campaign_yields_nothing(tmp_path: Path) -> None:
    for module in (
        pipeline_p003,
        pipeline_p003_synthetic,
        pipeline_p003_extension,
        pipeline_p003_micro,
        pipeline_p003_continuation,
    ):
        assert list(module.collect(tmp_path)) == []
