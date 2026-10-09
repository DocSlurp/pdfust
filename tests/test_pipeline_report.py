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
