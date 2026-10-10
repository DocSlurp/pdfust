"""Frozen report audits count failures and reject incomplete retained outputs."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.generalization_report import (
    _bounds,
    _costs,
    _evaluate,
    _ratio,
    load_corpus,
    markdown_report,
    score_run,
    verify_code,
    verify_output,
)
from bench.pipeline_assembly import native_state
from bench.pipeline_regions import compose, split, unresolved_region
from bench.pipeline_report import _render_markdown
from bench.silver import canonical, sha


def write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


@pytest.fixture
def fixture(tmp_path: Path) -> dict[str, Any]:
    corpus, run = tmp_path / "corpus", tmp_path / "run"
    corpus.mkdir()
    (run / "code").mkdir(parents=True)
    pdf = corpus / "input.pdf"
    pdf.write_bytes(b"frozen pdf bytes; evaluator hashes but never interprets")
    pages = [
        {
            "id": ident,
            "cohort": cohort,
            "family": cohort + "/test",
            "pilot": True,
            "pdf_path": str(pdf),
            "pdf_sha256": sha(pdf.read_bytes()),
            "page_number": 0,
        }
        for ident, cohort in [("positive", "authored"), ("negative", "omni"), ("diagnostic", "native")]
    ]
    table = {"row_count": 1, "col_count": 1, "values": [["A"]], "spans": []}
    targets = {
        "schema": 1,
        "pages": [
            {"id": "positive", "tables": [table], "structural_scored": True},
            {"id": "negative", "tables": [], "structural_scored": True},
            {"id": "diagnostic", "structural_scored": False},
        ],
    }
    identity = sha(
        canonical(
            {
                "schema": 1,
                "pages": [{k: v for k, v in p.items() if k != "pdf_path"} for p in pages],
                "targets": targets["pages"],
            }
        )
    )
    manifest = {"schema": 1, "split": "DEV", "dataset_sha256": identity, "pages": pages}
    targets["dataset_sha256"] = identity
    write(corpus / "manifest.json", manifest)
    write(corpus / "private-targets.json", targets)
    config = {"pilot": False, "processor": "whole", "policy": "native"}
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "w0", "text": "hello", "bbox": [0, 0, 20, 10], "line": [0, 0]},
        ],
        "vector_candidates": [],
    }
    state = native_state(source)
    prediction = {
        "id": "negative",
        "status": "ok",
        "source": source,
        "tables": [],
        "unresolved_ids": ["w0"],
        "calls": [],
    }
    write(run / "negative-result.json", prediction)
    write(run / "negative-structure.json", state)
    (run / "negative.md").write_text(_render_markdown(source, state))
    local = Path(__file__).parents[1] / "bench"
    hashes = {}
    for name in ("pipeline_run.py", "pipeline_assembly.py"):
        data = (local / name).read_bytes()
        hashes[name] = sha(data)
        (run / "code" / name).write_bytes(data)
    frozen = {
        "config": config,
        "manifest_sha256": sha((corpus / "manifest.json").read_bytes()),
        "code_sha256": hashes,
        "records": [{k: p[k] for k in ("id", "pdf_path", "pdf_sha256", "page_number")} for p in pages],
    }
    report = {
        "config": config,
        "results": [prediction],
        "metrics": {"wall_seconds": 2, "cpu_seconds": 1, "peak_sampled_rss_bytes": 1000},
        "calls": 0,
        "ledger_attempts": 0,
        "accounted_usd": 0,
        "effective_usd": 0,
        "provider_reported_usd": 0,
        "missing_provider_charge_count": 0,
        "cost_bases": {},
    }
    write(run / "frozen.json", frozen)
    write(run / "report.json", report)
    return {
        "corpus": corpus,
        "run": run,
        "manifest": manifest,
        "targets": targets,
        "prediction": prediction,
        "frozen": frozen,
        "report": report,
    }


def test_complete_manifest_errors_groups_and_free_costs(fixture: dict[str, Any]) -> None:
    f = fixture
    manifest, targets = load_corpus(f["corpus"])
    report = score_run(f["run"], f["corpus"] / "manifest.json", manifest, targets)
    assert report["intended_pages"] == 3
    assert report["operational_pages"] == 1
    assert report["all_errors"] == 2
    assert report["statuses"] == {"ok": 1, "missing": 2}
    assert report["groups"]["cohort"]["authored"]["expected_tables"] == 1
    assert report["groups"]["cohort"]["native"]["diagnostic_pages"] == 1
    assert report["authored_legacy_exact"]["cell_slots"] == 1
    assert report["pages_per_minute"] == 30
    assert report["pages_per_dollar"] is None
    markdown = markdown_report([report])
    assert "native/test" in markdown
    assert "all ledger attempts" in markdown
    assert "unmeasured" in markdown


def test_corpus_hash_detects_pdf_and_reference_changes(fixture: dict[str, Any]) -> None:
    f = fixture
    altered = deepcopy(f["targets"])
    altered["pages"][0]["tables"][0]["values"] = [["changed"]]
    write(f["corpus"] / "private-targets.json", altered)
    with pytest.raises(ValueError, match="identity"):
        load_corpus(f["corpus"])
    write(f["corpus"] / "private-targets.json", f["targets"])
    (f["corpus"] / "input.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source PDF"):
        load_corpus(f["corpus"])


def test_outcome_selected_frozen_subset_rejected(fixture: dict[str, Any]) -> None:
    f = fixture
    frozen = deepcopy(f["frozen"])
    frozen["records"] = frozen["records"][1:2]
    write(f["run"] / "frozen.json", frozen)
    with pytest.raises(ValueError, match="complete intended"):
        score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])


def test_archived_python_is_hashed_and_never_executed(fixture: dict[str, Any]) -> None:
    f = fixture
    (f["run"] / "code" / "pipeline_run.py").write_text("raise RuntimeError('must never execute')")
    with pytest.raises(ValueError, match="Archived code"):
        verify_code(f["run"], f["frozen"], processor="whole")


def test_markdown_and_result_tampering_rejected(fixture: dict[str, Any]) -> None:
    f = fixture
    (f["run"] / "negative.md").write_text("unowned invented prose")
    with pytest.raises(ValueError, match="Markdown"):
        verify_output(f["run"], f["prediction"], processor="whole")
    altered = deepcopy(f["prediction"])
    altered["status"] = "error"
    write(f["run"] / "negative-result.json", altered)
    with pytest.raises(ValueError, match="retained result"):
        verify_output(f["run"], f["prediction"], processor="whole")


def test_region_recomposition_and_exact_markdown(tmp_path: Path) -> None:
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "w0", "text": "A", "bbox": [10, 10, 20, 20]},
            {"id": "w1", "text": "B", "bbox": [10, 70, 20, 80]},
        ],
        "vector_candidates": [],
    }
    plan = split(source)
    states = {r["id"]: unresolved_region(r) for r in plan["regions"]}
    state = compose(plan, states)
    _bounds(source, state)
    prediction = {
        "id": "regions",
        "status": "ok",
        "source": source,
        "tables": state["tables"],
        "unresolved_ids": state["unresolved_ids"],
        "region_plan": {k: v for k, v in plan.items() if k != "words"},
        "regions": [{"id": r["id"], "state": states[r["id"]]} for r in plan["regions"]],
    }
    write(tmp_path / "regions-result.json", prediction)
    write(tmp_path / "regions-structure.json", state)
    (tmp_path / "regions.md").write_text(
        "\n".join(_render_markdown(r["source"], states[r["id"]]) for r in plan["regions"])
    )
    assert verify_output(tmp_path, prediction, processor="regions")["conserved"]
    altered = deepcopy(prediction)
    altered["regions"][0]["state"]["unresolved_ids"] = []
    write(tmp_path / "regions-result.json", altered)
    with pytest.raises(ValueError, match=r"source|ownership|conservation"):
        verify_output(tmp_path, altered, processor="regions")


def test_reservations_unknown_and_zero_charges_do_not_become_totals() -> None:
    report = {
        "ledger_attempts": 3,
        "calls": 1,
        "provider_reported_usd": 0,
        "accounted_usd": 1,
        "effective_usd": 1,
        "cost_bases": {"reserved": 1, "catalog_estimate": 2},
    }
    cost = _costs(report)
    assert cost["effective_usd"] is None
    assert cost["provider_reported_subtotal_usd"] == 0
    assert cost["reservation_usd"] is None
    assert cost["estimated_usd"] is None
    report["cost_bases"] = {"unknown": 1}
    assert _costs(report)["effective_usd"] is None
    assert _ratio(1, 0) is None
    assert _ratio(1, None) is None


def test_gold_field_in_retained_request_rejected(fixture: dict[str, Any]) -> None:
    f = fixture
    report = deepcopy(f["report"])
    prediction = report["results"][0]
    prediction["calls"] = [{"entry": {}}]
    write(f["run"] / "report.json", report)
    write(f["run"] / "negative-result.json", prediction)
    write(f["run"] / "negative-request-0.json", {"payload": {"gold_tables": []}})
    with pytest.raises(ValueError, match="reference fields"):
        score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])


def test_natural_unit_spans_canonicalize_and_localization_is_separate() -> None:
    table = {"row_count": 1, "col_count": 2, "values": [["A", "B"]], "spans": [], "bbox": [0, 0, 100, 10]}
    prediction = deepcopy(table)
    prediction["spans"] = [{"row": 0, "column": c, "row_span": 1, "column_span": 1} for c in range(2)]
    result = _evaluate([{"id": "natural", "tables": [table]}], [{"id": "natural", "tables": [prediction]}])
    assert result["totals"]["exact_page"] == 1
    assert result["totals"]["localized_tables_iou_ge_0_5"] == 1
    prediction["bbox"] = [0, 0, 20, 10]
    result = _evaluate([{"id": "natural", "tables": [table]}], [{"id": "natural", "tables": [prediction]}])
    assert result["totals"]["geometry_matches"] == 1
    assert result["totals"]["localized_tables_iou_ge_0_5"] == 0


def test_failed_request_body_is_audited_without_successful_call(fixture: dict[str, Any]) -> None:
    f = fixture
    write(f["run"] / "positive-request-0.json", {"annotation_html": "private reference"})
    with pytest.raises(ValueError, match="reference fields"):
        score_run(f["run"], f["corpus"] / "manifest.json", f["manifest"], f["targets"])
