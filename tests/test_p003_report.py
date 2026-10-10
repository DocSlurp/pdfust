"""Independent P003 metric, accounting and paired-evaluation contracts."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.p003_report import costs, paired_comparison, repeat_summary, strict_scores, verify_archive
from bench.silver import sha


def table(values: list[list[str | None]], spans: list[dict[str, int]] | None = None) -> dict[str, Any]:
    return {"row_count": len(values), "col_count": len(values[0]), "values": values, "spans": spans or []}


def test_strict_cells_require_anchor_span() -> None:
    gold = table([["A", None], ["B", "C"]], [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}])
    prediction = table([["A", ""], ["B", "C"]])
    result = strict_scores([{"id": "p", "tables": [gold]}], [{"id": "p", "status": "ok", "tables": [prediction]}])
    assert result["totals"]["correct_text_cells"] == 3
    assert result["totals"]["strict_exact_cells"] == 2
    assert result["totals"]["complete_tables"] == 0


def test_missing_errors_and_negative_false_positives_remain_scored() -> None:
    targets = [{"id": "positive", "tables": [table([["A"]])]}, {"id": "negative", "tables": []}]
    result = strict_scores(targets, [{"id": "negative", "status": "ok", "tables": [table([["invented"]])]}])
    assert result["totals"]["expected_cells"] == 1
    assert result["totals"]["all_page_errors"] == 1
    assert result["totals"]["false_positive_page"] == 1
    assert result["totals"]["strict_exact_cells"] == 0
    assert result["positive_macro"]["strict_exact_cell_recall"] == 0


@pytest.mark.parametrize("bases", [{"reserved": 1}, {"unknown": 1}])
def test_incomplete_cost_cannot_become_total(bases: dict[str, int]) -> None:
    result = costs(
        {"effective_usd": 1, "accounted_usd": 2, "provider_reported_usd": 0, "ledger_attempts": 1, "cost_bases": bases}
    )
    assert result["effective_api_usd"] is None
    assert result["provider_reported_subtotal_usd"] == 0
    assert result["accounted_usd_including_reservations"] == 2


def test_reported_zero_and_estimate_remain_distinct() -> None:
    result = costs(
        {"effective_usd": 0.1, "provider_reported_usd": 0, "ledger_attempts": 1, "cost_bases": {"catalog estimate": 1}}
    )
    assert result["effective_api_usd"] == 0.1
    assert result["provider_reported_subtotal_usd"] == 0


def test_archive_cannot_authenticate_its_own_digest(tmp_path: Path) -> None:
    code = tmp_path / "code"
    code.mkdir()
    (code / "unknown.py").write_bytes(b"# unreviewed\n")
    digest = sha((code / "unknown.py").read_bytes())
    frozen = {"code_sha256": {"unknown.py": digest}}
    with pytest.raises(ValueError, match="Untrusted"):
        verify_archive(tmp_path, frozen)
    assert verify_archive(tmp_path, frozen, {"unknown.py": digest}) == frozen["code_sha256"]
    (code / "unknown.py").write_bytes(b"# altered\n")
    with pytest.raises(ValueError, match="changed"):
        verify_archive(tmp_path, frozen, {"unknown.py": digest})


def matched_run(name: str, values: list[int]) -> dict[str, Any]:
    return {
        "name": name,
        "dataset_sha256": "dataset",
        "manifest_sha256": "manifest",
        "cohort": "omnidoc",
        "source_fingerprint": "same",
        "detector_evidence_fingerprint": "same",
        "source_inventory_pages": 2,
        "intended_pages": 2,
        "page_scores": [{"id": str(i), "strict_exact_cells": v, "complete_tables": 0} for i, v in enumerate(values)],
    }


def test_paired_bootstrap_keeps_page_deltas_and_rejects_source_changes() -> None:
    left, right = matched_run("a", [1, 2]), matched_run("b", [3, 1])
    result = paired_comparison(left, right, samples=100)
    assert result["strict_exact_cell_delta"] == 1
    assert result["paired_page_bootstrap_95_interval"] == [-2, 4]
    assert result == paired_comparison(left, right, samples=100)
    changed = deepcopy(right)
    changed["source_fingerprint"] = "different"
    with pytest.raises(ValueError, match="source_fingerprint"):
        paired_comparison(left, changed)
    changed = deepcopy(right)
    changed["source_inventory_pages"] = 1
    with pytest.raises(ValueError, match="complete retained"):
        paired_comparison(left, changed)


def test_repeat_summary_keeps_worst_and_best_without_selection() -> None:
    runs = [matched_run("r1", [1, 2]), matched_run("r2", [3, 1]), matched_run("r3", [0, 0])]
    for run in runs:
        run["config"] = {"model": "fixed"}
        run["scores"] = {"strict_exact_cells": sum(p["strict_exact_cells"] for p in run["page_scores"])}
    summary = repeat_summary(runs)
    assert summary["metrics"]["strict_exact_cells"]["observations"] == [3, 4, 0]
    assert summary["metrics"]["strict_exact_cells"]["median"] == 3
    assert summary["metrics"]["strict_exact_cells"]["minimum"] == 0
    runs[2]["config"] = {"model": "changed"}
    with pytest.raises(ValueError, match="identical treatment"):
        repeat_summary(runs)


def test_repeat_administration_and_defaults_do_not_change_treatment() -> None:
    left, right = matched_run("r0", [1, 2]), matched_run("r1", [2, 3])
    left["config"] = {"run_id": "r0", "repeat_index": 0, "order_seed": 1, "model": "gate", "image_edge": 512}
    right["config"] = {
        "run_id": "r1",
        "repeat_index": 1,
        "order_seed": 2,
        "model": "gate",
        "image_edge": 512,
        "gate_image": True,
        "source_order": "legacy",
    }
    for run in (left, right):
        run["scores"] = {"strict_exact_cells": sum(p["strict_exact_cells"] for p in run["page_scores"])}
    assert repeat_summary([left, right])["administrative_fields"][1]["order_seed"] == 2
    for field, value in (("model", "different_gate"), ("image_edge", 1024), ("gate_image", False)):
        changed = deepcopy(right)
        changed["config"][field] = value
        with pytest.raises(ValueError, match="identical treatment"):
            repeat_summary([left, changed])
    right["code_sha256"] = {"helper.py": "new"}
    with pytest.raises(ValueError, match="operator semantic review"):
        repeat_summary([left, right])
    assert repeat_summary([left, right], reviewed_code_changes=True)["operator_reviewed_code_changes"]


def test_paired_image_changes_are_explicit() -> None:
    left, right = matched_run("a", [1, 2]), matched_run("b", [2, 3])
    left["config"] = {"gate_image": True}
    right["config"] = {"gate_image": False}
    left["request_image_inventory"] = [{"data_url_sha256": ["image"]}]
    right["request_image_inventory"] = []
    result = paired_comparison(left, right, samples=10)
    assert result["gate_image_configuration_equal"] is False
    assert result["request_image_hash_sets_equal"] is False
    assert result["treatment_changes"]["gate_image"] == [True, False]
