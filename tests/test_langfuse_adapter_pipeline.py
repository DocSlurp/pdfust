"""Synthetic-fixture tests for the P001/P002 pipeline Langfuse adapters."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

import pytest
from bench.langfuse_adapters import pipeline_p001, pipeline_p002
from bench.langfuse_adapters.base import clean_scores, validate

if TYPE_CHECKING:
    from pathlib import Path


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _table(values: list[list[str]]) -> dict[str, Any]:
    rows, cols = len(values), len(values[0])
    spans = [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(rows) for c in range(cols)]
    return {"row_count": rows, "col_count": cols, "values": values, "spans": spans}


def _call(usd: float | None, status: str = "provider-reported USD") -> dict[str, Any]:
    return {
        "entry": {"provider_reported_usd": usd, "accounted_usd": usd, "cost_status": status, "requested_model": "m"}
    }


def _p001(artifacts: Path) -> None:
    corpus = artifacts / "pipeline-p001" / "corpus"
    pdf = corpus / "pdfs" / "a.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF-1.7\n")
    pages = [
        {"id": "pos", "family": "f/t", "page_number": 0, "pdf_path": str(pdf), "pdf_sha256": "aa", "pilot": True},
        {"id": "neg", "family": "f/n", "page_number": 0, "pdf_path": str(pdf), "pdf_sha256": "aa", "pilot": False},
        {"id": "diag", "family": "f/d", "page_number": 0, "pdf_path": str(pdf), "pdf_sha256": "aa", "pilot": False},
    ]
    _write(corpus / "manifest.json", {"split": "DEV", "dataset_sha256": "d1", "pages": pages})
    gold = _table([["a", "b"], ["1", "2"]])
    _write(
        corpus / "private-targets.json",
        {
            "pages": [
                {"id": "pos", "structural_scored": True, "tables": [gold]},
                {"id": "neg", "structural_scored": True, "tables": []},
                {"id": "diag", "structural_scored": False, "tables": []},
            ]
        },
    )
    words = [{"id": f"w{i}", "text": t} for i, t in enumerate(["a", "b", "1", "2"])]
    cells = [{"source_ids": [f"w{i}"]} for i in range(4)]
    full: dict[str, Any] = {
        "config": {"pilot": False, "policy": "gated", "model": "m"},
        "metrics": {"wall_seconds": 60.0, "cpu_seconds": 5.0, "peak_sampled_rss_bytes": 100},
        "provider_reported_usd": 0.01,
        "missing_provider_charge_count": 1,
        "accounted_usd": 0.31,
        "effective_usd": None,
        "cost_bases": {"provider-reported USD": 1, "reserved": 1},
        "results": [
            {
                "id": "pos",
                "status": "ok",
                "tables": [{**gold, "cells": cells}],
                "unresolved_ids": [],
                "source": {"words": words},
                "calls": [_call(0.01)],
                "wall_seconds": 2.0,
                "candidates": [{"tables": [gold]}],
            },
            {"id": "neg", "status": "error", "error": "boom", "tables": [], "calls": [_call(None, "reserved")]},
        ],
    }
    _write(artifacts / "pipeline-p001" / "full-run" / "report.json", full)
    pilot = {**full, "config": {"pilot": True, "policy": "native"}, "results": full["results"][:1]}
    pilot.update(effective_usd=0.0, cost_bases={}, provider_reported_usd=0, missing_provider_charge_count=0)
    _write(artifacts / "pipeline-p001" / "pilot-run" / "report.json", pilot)


def test_p001_rows_scores_and_costs(tmp_path: Path) -> None:
    _p001(tmp_path)
    (experiment,) = list(pipeline_p001.collect(tmp_path))
    assert experiment.dataset.startswith("exp/pipeline-p001/")
    counts = validate(experiment)
    assert counts["items"] == 3
    runs = {run.name: run for run in experiment.runs}
    full, pilot = runs["full-run"], runs["pilot-run"]
    assert len(full.rows) == 3
    assert [row.item_key for row in pilot.rows] == ["pos"]
    rows = {row.item_key: row for row in full.rows}
    assert clean_scores(rows["pos"].scores)["exact_page"] == 1.0
    assert rows["pos"].scores["source_conserved"] is True
    assert rows["pos"].metadata["provider_reported_usd"] == pytest.approx(0.01)
    assert rows["neg"].metadata["status"] == "error"
    assert rows["neg"].scores["error"] is True
    assert rows["neg"].metadata["provider_charge_missing"] == 1
    assert "provider_reported_usd" not in rows["neg"].metadata
    assert rows["diag"].metadata["status"] == "missing"
    assert rows["diag"].scores == {"operational_output": False, "error": True}
    assert full.scores["positive_exact_pages"] == 1
    assert full.scores["all_errors"] == 2
    assert full.scores["oracle_positive_exact_pages"] == 1
    assert "effective_usd" not in full.scores
    assert "pages_per_dollar" not in full.scores
    assert full.scores["reserved_calls"] == 1
    assert full.scores["pages_per_minute"] == pytest.approx(1.0)
    item = next(item for item in experiment.items if item.key == "pos")
    assert item.input["pdf"]["bytes"] == len(b"%PDF-1.7\n")
    assert item.expected["tables"][0]["values"] == [["a", "b"], ["1", "2"]]
    assert "merged_spans" not in item.expected["tables"][0]


def _evaluation(sha: str, pages: list[dict[str, Any]], effective: float | None) -> dict[str, Any]:
    totals = {
        "pages": 2,
        "correct_text_cells": sum(p.get("correct_text_cells", 0) for p in pages),
        "complete_tables": 1,
    }
    return {
        "dataset_sha256": sha,
        "intended_pages": 2,
        "scores": totals,
        "positive": {"scored_pages": 1, "exact_page": 1, "negative_page": 0},
        "negative": {"scored_pages": 1, "false_positive_page": 0},
        "positive_macro": {"exact_cell_recall": 1.0},
        "page_scores": pages,
        "operational_pages": 1,
        "all_errors": 1,
        "costs": {
            "provider_reported_subtotal_usd": 0.02,
            "missing_provider_charge_count": 0,
            "effective_usd": effective,
            "reservation_usd": 0,
            "estimated_usd": 0,
        },
        "resources": {"wall_seconds": 10.0, "cpu_seconds": 4.0, "peak_sampled_rss_bytes": 1000},
        "pages_per_minute": 6.0,
        "pages_per_dollar": None,
        "failure_taxonomy": {"counts": {"x": 1}, "pages": [{"id": "n2", "category": "invalid_table_geometry"}]},
    }


def _p002(artifacts: Path) -> None:
    root = artifacts / "pipeline-p002"
    screen = root / "screens" / "natural16"
    records = [
        {"id": "n1", "cohort": "omnidoc", "family": "omni/single-table", "pdf_path": "/x/a.pdf", "pdf_sha256": "a"},
        {"id": "n2", "cohort": "omnidoc", "family": "omni/no-table", "pdf_path": "/x/b.pdf", "pdf_sha256": "b"},
    ]
    _write(screen / "manifest.json", {"split": "DEV", "dataset_sha256": "nat", "pages": records})
    targets = [
        {"id": "n1", "structural_scored": True, "tables": [{**_table([["x"]]), "bbox": [0, 0, 1, 1]}]},
        {"id": "n2", "structural_scored": True, "tables": [], "annotation_path": "/r/pdf-master-artifacts/ann.json"},
    ]
    _write(screen / "private-targets.json", {"pages": targets})
    pages = [
        {"id": "n1", "structural_scored": True, "expected_cells": 1, "correct_text_cells": 1, "exact_page": True},
        {"id": "n2", "structural_scored": True, "error": True, "matches": []},
    ]
    run = root / "natural16-run"
    _write(run / "verified-evaluation.json", _evaluation("nat", pages, None))
    results = [
        {"id": "n1", "status": "ok", "tables": [_table([["x"]])], "calls": [_call(0.02)], "wall_seconds": 1.5},
        {"id": "n2", "status": "error", "error": "bad geometry", "tables": [], "calls": []},
    ]
    _write(run / "report.json", {"results": results})
    (run / "n1.md").write_text("<table></table>\n", encoding="utf-8")
    manifest_sha = hashlib.sha256((screen / "manifest.json").read_bytes()).hexdigest()
    interrupted = root / "natural16-interrupted"
    _write(interrupted / "frozen.json", {"manifest_sha256": manifest_sha, "records": [{"id": "n1"}, {"id": "n2"}]})
    _write(
        interrupted / "report.json",
        {
            "run_status": "interrupted",
            "results": [{"id": "n1", "status": "ok", "tables": [], "calls": [_call(0.01)]}],
            "provider_reported_usd": 0.01,
            "missing_provider_charge_count": 1,
            "accounted_usd": 0.31,
            "effective_usd": None,
            "cost_bases": {"provider-reported USD": 1, "reserved": 1},
        },
    )
    salvage = {
        "dataset_sha256": "nat",
        "runs": [
            {
                "name": "natural16-run",
                "groups": {"all16": {"secondary": {"correct_text_cells": 1}}},
                "partial_pages": [{"id": "n1", "status": "partial", "baseline_status": "ok"}],
                "secondary_page_scores": [{"id": "n1", "structural_scored": True, "correct_text_cells": 1}],
            }
        ],
    }
    _write(root / "partial-salvage-audit.json", salvage)
    _write(root / "partial-review" / "audit.json", salvage)


def test_p002_verified_interrupted_and_secondary_runs(tmp_path: Path) -> None:
    _p002(tmp_path)
    (experiment,) = list(pipeline_p002.collect(tmp_path))
    assert experiment.dataset == "exp/pipeline-p002/natural16"
    validate(experiment)
    runs = {run.name: run for run in experiment.runs}
    assert set(runs) == {"natural16-run", "natural16-interrupted", "partial-salvage/natural16-run"}
    primary = runs["natural16-run"]
    rows = {row.item_key: row for row in primary.rows}
    assert rows["n1"].scores["text_cell_recall"] == 1.0
    assert rows["n1"].output["markdown"]["bytes"] > 0
    assert rows["n1"].wall_ms == pytest.approx(1500)
    assert rows["n2"].metadata["failure_category"] == "invalid_table_geometry"
    assert rows["n2"].scores["operational_output"] is False
    assert "matches" not in rows["n2"].scores
    assert primary.scores["provider_reported_usd"] == pytest.approx(0.02)
    assert primary.scores["positive_exact_page"] == 1
    assert primary.scores["positive_macro_exact_cell_recall"] == 1.0
    for absent in ("effective_usd", "pages_per_dollar", "reservation_usd", "estimated_usd", "positive_negative_page"):
        assert absent not in primary.scores
    assert primary.metadata["crosscheck_page_text_cells_equal_total"] is True
    interrupted = runs["natural16-interrupted"]
    assert [row.output["status"] for row in interrupted.rows] == ["ok", "missing"]
    assert interrupted.scores["missing_pages"] == 2 - 1
    assert "effective_usd" not in interrupted.scores
    secondary = runs["partial-salvage/natural16-run"]
    assert secondary.metadata["secondary"] is True
    assert secondary.rows[0].output == {"status": "partial", "baseline_status": "ok"}
    item = next(item for item in experiment.items if item.key == "n2")
    assert item.expected["annotation"] == "ann.json"
    assert item.input["pdf"]["bytes"] is None


def test_adapters_refuse_protected_paths(tmp_path: Path) -> None:
    protected = tmp_path / "silver-heldout-v1"
    protected.mkdir()
    with pytest.raises(PermissionError):
        list(pipeline_p001.collect(protected))
    with pytest.raises(PermissionError):
        list(pipeline_p002.collect(protected))


def test_adapters_yield_nothing_without_artifacts(tmp_path: Path) -> None:
    assert list(pipeline_p001.collect(tmp_path)) == []
    assert list(pipeline_p002.collect(tmp_path)) == []
