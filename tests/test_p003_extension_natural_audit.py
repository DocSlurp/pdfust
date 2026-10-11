"""Declared page admission and scan/error denominators for the natural DEV check."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_extension_natural_audit as audit
from bench.p003_extension_score import prediction, score_predictions
from bench.silver import sha

import pylopdf


def test_extracts_declared_nonzero_page_and_retains_exact_pdf_hash(tmp_path: Path) -> None:
    with pylopdf.Document() as document:
        document.new_page().insert_text((30, 50), "Firstpage")
        document.new_page().insert_text((30, 50), "Secondpage")
        raw = document.tobytes()
    path = tmp_path / "two-pages.pdf"
    path.write_bytes(raw)
    record = {"id": "opaque", "pdf_path": str(path), "pdf_sha256": sha(raw), "page_number": 1}
    row = audit.extract_record(record)
    assert row["status"] == "ok"
    assert [w["text"] for w in row["source"]["words"]] == ["Secondpage"]
    assert row["source"]["words"][0]["id"].startswith("w")
    record["pdf_sha256"] = "incorrect-hash"
    with pytest.raises(ValueError, match="PDF changed"):
        audit.extract_record(record)


def test_no_text_pages_are_not_applicable_and_stay_in_complete_denominator(tmp_path: Path) -> None:
    with pylopdf.Document() as document:
        document.new_page()
        raw = document.tobytes()
    path = tmp_path / "no-text.pdf"
    path.write_bytes(raw)
    row = audit.extract_record({"id": "opaque", "pdf_path": str(path), "pdf_sha256": sha(raw), "page_number": 0})
    assert row["status"] == "not_applicable_no_source_text"
    assert row["source"]["words"] == []
    table = {"row_count": 1, "col_count": 1, "values": [["Visible raster value"]],
             "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}]}
    target = {"id": "opaque", "tables": [table], "structural_scored": True}
    result = score_predictions([target], [prediction("opaque", row["states"]["native"], status=row["status"])])
    assert result["strict"]["totals"]["pages"] == 1
    assert result["strict"]["totals"]["all_page_errors"] == 1
    assert result["strict"]["totals"]["strict_exact_cells"] == 0
    assert result["v2"]["counts"]["missing_tables"] == 1


def test_changed_source_manifest_is_refused_without_target_reads(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "manifest.json").write_text(json.dumps({"split": "DEV", "pages": []}))
    with pytest.raises(ValueError, match="manifest"):
        audit.prepare(corpus, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_changed_source_freeze_prevents_target_loader_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "frozen.json").write_text(json.dumps({"references_read": False}))
    called = []
    monkeypatch.setattr(audit, "load_corpus", lambda _path: called.append("target-loader"))
    with pytest.raises(ValueError, match="receipt changed"):
        audit.evaluate(tmp_path, frozen_sha256="incorrect-freeze-pin", targets_sha256="unused-pin")
    assert called == []
