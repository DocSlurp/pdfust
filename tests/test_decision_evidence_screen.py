"""Verify source-only selection and non-vacuous abstention scoring."""

import hashlib
import json
from pathlib import Path

import pytest
from bench import decision_evidence_screen as screen


def test_screen_selection_does_not_read_gold(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    records = []
    for page, grid in (("one", True), ("two", False)):
        for arm in (*screen.ARMS, "hybrid"):
            body = {
                "model": "placeholder",
                "state": {"words": [], "vector_grid_prior": [1] if grid else []},
                "questions": {},
            }
            data = screen.encode(body)
            name = f"{page}-{arm}.json"
            (source / name).write_bytes(data)
            records.append(
                {
                    "id": page,
                    "arm": arm,
                    "request": name,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "source_admission_refusal": None,
                }
            )
    (source / "manifest.json").write_text(json.dumps({"records": records}))
    (source / "scorer-only.json").write_text("not readable as JSON")
    result = screen.prepare(source, tmp_path / "prepared")
    assert result["selected"] == ["one", "two"]
    assert len(result["records"]) == 6


def test_absent_responses_do_not_pass_as_negative(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "scorer-only.json").write_text(json.dumps({"positive": "A", "negative": "B"}))
    (output / "manifest.json").write_text(json.dumps({"source": str(source), "selected": ["positive", "negative"]}))
    (output / "results.json").write_text(json.dumps({"records": []}))
    catalog = tmp_path / "langfuse"
    catalog.mkdir()
    (catalog / "catalog-prices.json").write_text(json.dumps({"prices": {}}))
    monkeypatch.setattr(screen, "ARTIFACTS", tmp_path)
    screen.report(output, tmp_path / "report.md")
    summary = json.loads((output / "summary.json").read_text())
    assert summary["agreement"] == 0
    for row in summary["rows"]:
        assert row["tp"] == row["tn"] == 0
        assert row["fn"] == 1
        assert row["unresolved"] == 2


def test_failed_paid_response_cost_remains_visible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "scorer-only.json").write_text(json.dumps({"positive": "A"}))
    (output / "manifest.json").write_text(json.dumps({"source": str(source), "selected": ["positive"]}))
    (output / "results.json").write_text(
        json.dumps(
            {
                "records": [
                    {
                        "id": "positive",
                        "arm": screen.ARMS[0],
                        "status": "error",
                        "entry": {"index": 1, "provider_reported_usd": 0.02, "elapsed_ms": 100},
                    }
                ]
            }
        )
    )
    (tmp_path / "langfuse").mkdir()
    (tmp_path / "langfuse/catalog-prices.json").write_text(json.dumps({"prices": {}}))
    monkeypatch.setattr(screen, "ARTIFACTS", tmp_path)
    screen.report(output, tmp_path / "report.md")
    row = json.loads((output / "summary.json").read_text())["rows"][0]
    assert row["effective_usd"] == 0.02
    assert row["unresolved"] == 1
    assert row["tp"] == 0
