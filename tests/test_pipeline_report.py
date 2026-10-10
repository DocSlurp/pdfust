"""Offline scoring preserves failure and unknown-cost denominators."""

import json
from pathlib import Path
from typing import Any

import pytest
from bench.pipeline_corpus import _table
from bench.pipeline_report import run
from bench.silver import canonical, sha, write_json


def _fixture(directory: Path) -> tuple[Path, dict[str, Any]]:
    corpus, pipeline = directory / "corpus", directory / "pilot-test"
    corpus.mkdir(parents=True)
    pipeline.mkdir()
    data = b"%PDF-fixture"
    pdf = corpus / "source.pdf"
    pdf.write_bytes(data)
    records = [
        {
            "id": ident,
            "pdf_path": str(pdf),
            "pdf_sha256": sha(data),
            "page_number": index,
            "family": "table" if index == 0 else "prose",
            "label_status": "authored DEV",
            "pilot": True,
        }
        for index, ident in enumerate(("positive", "negative", "absent"))
    ]
    table = _table([["a", "b"], ["c", "d"]])
    for span in table["spans"]:
        span["role"] = "unknown"
    # Roles are descriptive and are ignored by exact span topology scoring.
    table["cells"] = [{"source_ids": [f"w{i}"], "role": "unknown"} for i in range(4)]
    targets = [
        {"id": row["id"], "structural_scored": True, "tables": [table] if index == 0 else []}
        for index, row in enumerate(records)
    ]
    identity_records = [{key: value for key, value in row.items() if key != "pdf_path"} for row in records]
    identity = sha(canonical({"schema": 1, "pages": identity_records, "targets": targets}))
    manifest = {"split": "DEV", "dataset_sha256": identity, "pages": records}
    write_json(corpus / "manifest.json", manifest)
    write_json(corpus / "private-targets.json", {"dataset_sha256": identity, "pages": targets})
    config = {
        "run_id": pipeline.name,
        "pilot": True,
        "policy": "assembly",
        "model": "test-model",
        "image_edge": 512,
        "context_rows": 1,
        "legend": True,
    }
    write_json(
        pipeline / "frozen.json",
        {
            "config": config,
            "manifest_sha256": sha((corpus / "manifest.json").read_bytes()),
            "records": [{key: row[key] for key in ("id", "pdf_path", "pdf_sha256", "page_number")} for row in records],
        },
    )
    state = {"tables": [table], "unresolved_ids": []}
    prediction = {
        "id": "positive",
        "status": "ok",
        **state,
        "source": {"words": [{"id": f"w{i}"} for i in range(4)]},
        "candidates": [{"tables": []}, state],
    }
    write_json(pipeline / "positive-structure.json", state)
    (pipeline / "positive.md").write_text("<table>complete</table>\n")
    report = {
        "config": config,
        "results": [prediction, {"id": "negative", "status": "error", "tables": []}],
        "metrics": {"wall_seconds": 60.0, "cpu_seconds": 1.0, "peak_sampled_rss_bytes": 1024},
        "accounted_usd": 0.3,
        "effective_usd": None,
        "provider_reported_usd": 0.0,
        "cost_bases": {"reserved": 1},
        "missing_provider_charge_count": 1,
    }
    write_json(pipeline / "report.json", report)
    return pipeline, report


def test_missing_and_failed_negative_pages_remain_failures_and_cost_unknown(tmp_path: Path) -> None:
    _fixture(tmp_path)
    result = run(tmp_path, tmp_path / "summary.md")["runs"][0]
    assert result["scores"]["scored_pages"] == 3
    assert result["scores"]["error"] == 2
    assert result["scores"]["exact_page"] == 1
    assert result["negative"]["scored_pages"] == 2
    assert result["negative"]["exact_page"] == 0
    assert result["pages_per_minute"] == 1.0
    assert result["exact_positive_pages_per_minute"] == 1.0
    assert result["pages_per_dollar"] is None
    assert result["exact_positive_pages_per_dollar"] is None
    assert result["oracle_positive"]["exact_page"] == 1
    assert result["conserved_pages"] == 1
    assert "reference-informed and unrunnable" in (tmp_path / "summary.md").read_text()


def test_unknown_extra_page_output_is_rejected(tmp_path: Path) -> None:
    pipeline, report = _fixture(tmp_path)
    report["results"].append({"id": "outside", "status": "error", "tables": []})
    write_json(pipeline / "report.json", report)
    with pytest.raises(ValueError, match="outside"):
        run(tmp_path, tmp_path / "summary.md")


def test_success_requires_retained_complete_files(tmp_path: Path) -> None:
    pipeline, _report = _fixture(tmp_path)
    (pipeline / "positive.md").unlink()
    with pytest.raises(ValueError, match="missing a complete"):
        run(tmp_path, tmp_path / "summary.md")


def test_reservation_cannot_be_reported_as_effective_cost(tmp_path: Path) -> None:
    pipeline, report = _fixture(tmp_path)
    report["effective_usd"] = 0.3
    write_json(pipeline / "report.json", report)
    result = run(tmp_path, tmp_path / "summary.md")["runs"][0]
    assert result["effective_usd"] is None
    assert result["pages_per_dollar"] is None


def test_frozen_records_are_verified(tmp_path: Path) -> None:
    pipeline, _report = _fixture(tmp_path)
    frozen = json.loads((pipeline / "frozen.json").read_text())
    frozen["records"].pop()
    write_json(pipeline / "frozen.json", frozen)
    with pytest.raises(ValueError, match="complete intended cohort"):
        run(tmp_path, tmp_path / "summary.md")


def test_frozen_pdf_hash_is_verified(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "corpus/source.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="PDF bytes changed"):
        run(tmp_path, tmp_path / "summary.md")


def test_summary_cannot_overwrite_completed_artifacts(tmp_path: Path) -> None:
    pipeline, _report = _fixture(tmp_path)
    with pytest.raises(ValueError, match="overwrite completed"):
        run(tmp_path, pipeline / "positive.md")


def test_native_display_hides_unused_model_settings_preserving_raw_config(tmp_path: Path) -> None:
    pipeline, report = _fixture(tmp_path)
    report["config"].update(policy="native", normalize_rotation=True, gate_premise=False)
    frozen = json.loads((pipeline / "frozen.json").read_text())
    frozen["config"] = report["config"]
    write_json(pipeline / "frozen.json", frozen)
    write_json(pipeline / "report.json", report)
    result = run(tmp_path, tmp_path / "summary.md")
    text = (tmp_path / "summary.md").read_text()
    assert "| native | CPU only | — | — | — | — | True | False | — |" in text
    assert result["runs"][0]["config"]["model"] == "test-model"
    assert result["runs"][0]["config"]["image_edge"] == 512
    assert "<summary>Complete per-family structure scores</summary>" in text


def test_incomplete_frozen_runs_are_visible_without_scoring_partial_outputs(tmp_path: Path) -> None:
    pipeline, _report = _fixture(tmp_path)
    incomplete = tmp_path / "unfinished"
    incomplete.mkdir()
    frozen = json.loads((pipeline / "frozen.json").read_text())
    frozen["config"]["run_id"] = "unfinished"
    frozen["config"]["policy"] = "adaptive"
    write_json(incomplete / "frozen.json", frozen)
    # Partial result content must not be parsed or promoted to completed scoring.
    (incomplete / "positive-result.json").write_text("not complete JSON")
    result = run(tmp_path, tmp_path / "summary.md")
    assert len(result["runs"]) == 1
    assert result["incomplete_runs"] == [
        {
            "name": "unfinished",
            "config": frozen["config"],
            "planned_pages": 3,
            "result_files": 1,
            "source_contract_matches": True,
        }
    ]
    text = (tmp_path / "summary.md").read_text()
    assert "| unfinished | adaptive | test-model | — | 3 | 1 | True |" in text
    assert "wall/CPU and RSS remain unknown" in text


def test_ocr_setting_visible_and_unused_gate_premise_hidden(tmp_path: Path) -> None:
    pipeline, report = _fixture(tmp_path)
    report["config"].update(policy="assembly", ocr_empty=True, gate_premise="relational")
    frozen = json.loads((pipeline / "frozen.json").read_text())
    frozen["config"] = report["config"]
    write_json(pipeline / "frozen.json", frozen)
    write_json(pipeline / "report.json", report)
    result = run(tmp_path, tmp_path / "summary.md")
    text = (tmp_path / "summary.md").read_text()
    assert "| assembly | test-model | — | 512 | 1 | True | False | True | — |" in text
    assert result["runs"][0]["config"]["gate_premise"] == "relational"
    report["config"]["policy"] = "gated"
    frozen["config"] = report["config"]
    write_json(pipeline / "frozen.json", frozen)
    write_json(pipeline / "report.json", report)
    run(tmp_path, tmp_path / "summary.md")
    assert (
        "| gated | test-model | — | 512 | 1 | True | False | True | relational |"
        in (tmp_path / "summary.md").read_text()
    )


def test_review_model_and_successful_call_costs_visible_without_changing_artifacts(tmp_path: Path) -> None:
    pipeline, report = _fixture(tmp_path)
    report["config"].update(policy="gated", gate_review_model="anthropic/claude-sonnet-5.5")
    frozen = json.loads((pipeline / "frozen.json").read_text())
    frozen["config"] = report["config"]
    write_json(pipeline / "frozen.json", frozen)
    report["results"][0]["calls"] = [
        {
            "entry": {
                "requested_model": "test-model",
                "accounted_usd": 0.01,
                "provider_reported_usd": 0.01,
                "cost_status": "provider-reported USD",
            }
        },
        {
            "entry": {
                "requested_model": "anthropic/claude-sonnet-5.5",
                "accounted_usd": 0.02,
                "provider_reported_usd": 0,
                "cost_status": "catalog estimate",
            }
        },
        {"entry": {"requested_model": "unsettled-model", "accounted_usd": 0.3, "cost_status": "reserved"}},
    ]
    write_json(pipeline / "report.json", report)
    original = (pipeline / "report.json").read_bytes()
    result = run(tmp_path, tmp_path / "summary.md")["runs"][0]
    assert (pipeline / "report.json").read_bytes() == original
    groups = result["successful_call_models"]
    assert groups["test-model"]["calls"] == 1
    assert groups["test-model"]["effective_usd"] == 0.01
    assert groups["anthropic/claude-sonnet-5.5"]["provider_reported_subtotal_usd"] == 0
    assert groups["anthropic/claude-sonnet-5.5"]["effective_usd"] == 0.02
    assert groups["unsettled-model"]["effective_usd"] is None
    assert groups["unsettled-model"]["missing_provider_charge_count"] == 1
    text = (tmp_path / "summary.md").read_text()
    assert "| gated | test-model | anthropic/claude-sonnet-5.5 |" in text
    assert "Failed or parse-rejected attempts" in text
    assert result["config"]["gate_review_model"] == "anthropic/claude-sonnet-5.5"
