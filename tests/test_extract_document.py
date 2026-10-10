"""Generated native PDF integration and mocked hosted dispatch, without paid calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from bench import extract_document as wrapper
from test_pipeline_run import pdf_bytes


@pytest.fixture
def pdf(tmp_path: Path) -> Path:
    path = tmp_path / "input.pdf"
    path.write_bytes(pdf_bytes())
    return path


def test_native_generated_pdf_preserves_outputs_and_resources(pdf: Path, tmp_path: Path) -> None:
    output = tmp_path / "native-output"
    result = wrapper.extract(pdf, output)
    assert result["complete"]
    assert result["requested_pages_complete"]
    assert result["successful_pages"] == 1
    assert result["costs"]["calls"] == 0
    assert result["pipeline_resources"]["local_gpu_used"] is False
    assert result["pages"][0]["source_conserved"]
    text = (output / "document.md").read_text()
    assert "Page 1" in text
    assert "Alpha" in text
    assert "42" in text
    manifest = json.loads((output / "source-manifest.json").read_text())
    assert set(manifest) == {"schema", "split", "pages"}
    assert set(manifest["pages"][0]) == {"id", "pdf_path", "pdf_sha256", "page_number"}
    assert manifest["pages"][0]["pdf_path"] == str(pdf.resolve())
    pipeline = output / result["pipeline_directory"]
    assert (pipeline / "frozen.json").exists()
    assert (pipeline / "resources.json").exists()
    assert json.loads((output / "document.json").read_text()) == result


@pytest.mark.parametrize("mode", ["hybrid-haiku", "hybrid-sonnet"])
def test_hosted_modes_are_explicit_delegation_and_missing_pages_stay_partial(
    mode: str, pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[list[str]] = []

    def invoke(command: list[str], log: Path) -> int:
        captured.append(command)
        log.write_text("mock; no credentials or network")
        pipeline = Path(command[command.index("--output") + 1])
        pipeline.mkdir()
        manifest = json.loads(Path(command[command.index("--manifest") + 1]).read_text())
        identifier = manifest["pages"][0]["id"]
        wrapper.write_json(pipeline / "report.json", {
            "results": [{"id": identifier, "status": "error", "calls": [], "error_type": "MockAtomicFailure"}],
            "calls": 1, "ledger_attempts": 1, "accounted_usd": 0.3, "effective_usd": None,
            "metrics": {"scope": "mock child"},
        })
        return 0

    monkeypatch.setattr(wrapper, "_invoke", invoke)
    output = tmp_path / mode
    result = wrapper.extract(pdf, output, mode=mode)
    command = captured[0]
    assert "bench.generalization_hybrid_run" in command
    assert command[command.index("--generation-model") + 1] == f"anthropic/claude-{mode.split('-')[1]}-5.5"
    assert "--generation-tokens" in command
    assert command[command.index("--native-table-orientation") + 1] == "logical"
    assert result["status"] == "partial"
    assert not result["complete"]
    assert not result["requested_pages_complete"]
    assert result["requested_page_count"] == 1
    assert result["successful_pages"] == 0
    assert result["costs"]["accounted_usd"] == 0.3
    assert result["costs"]["effective_usd"] is None
    assert "Page 1 extraction failed" in (output / "document.md").read_text()


@pytest.mark.parametrize("options", [
    {"max_pages": 0}, {"max_pages": 4097}, {"pages": []}, {"pages": [0, 0]},
    {"pages": [1]}, {"pages": [-1]}, {"pages": [True]}, {"mode": "unsupported"},
])
def test_invalid_admission_precedes_output_and_dispatch(
    options: dict[str, Any], pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    invoke = MagicMock(side_effect=AssertionError)
    monkeypatch.setattr(wrapper, "_invoke", invoke)
    output = tmp_path / "absent"
    with pytest.raises(ValueError, match=r"mode|max_pages|Requested pages"):
        wrapper.extract(pdf, output, **options)
    assert not output.exists()
    invoke.assert_not_called()


def test_existing_output_is_refused_before_dispatch(pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    invoke = MagicMock(side_effect=AssertionError)
    monkeypatch.setattr(wrapper, "_invoke", invoke)
    with pytest.raises(FileExistsError, match="must be new"):
        wrapper.extract(pdf, output)
    invoke.assert_not_called()


def test_child_startup_failure_retains_missing_page_denominator(
    pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wrapper, "_invoke", lambda _command, _log: 1)
    result = wrapper.extract(pdf, tmp_path / "failed")
    assert result["pipeline_exit_code"] == 1
    assert result["requested_page_count"] == 1
    assert result["pages"][0]["error_type"] == "MissingCompletePageOutput"
    assert not result["complete"]
    assert result["costs"]["accounted_usd"] is None


def test_subset_success_never_claims_complete_document(tmp_path: Path) -> None:
    import pylopdf  # noqa: PLC0415 - generated local PDF only.

    pdf = tmp_path / "two-pages.pdf"
    with pylopdf.open() as document:
        document.new_page().insert_text((50, 50), "First page retained prose")
        document.new_page().insert_text((50, 50), "Second page retained prose")
        document.save(pdf)
    output = tmp_path / "subset"
    result = wrapper.extract(pdf, output, pages=[1])
    assert result["requested_pages_complete"]
    assert not result["complete"]
    assert result["status"] == "partial"
    assert result["source_page_count"] == 2
    assert result["requested_page_count"] == 1
    text = (output / "document.md").read_text()
    assert "Page 2" in text
    assert "Second" in text
    assert "First" not in text
    with pytest.raises(ValueError, match="max_pages admission"):
        wrapper.extract(pdf, tmp_path / "over-limit", max_pages=1)


@pytest.mark.parametrize("model_table", [True, False])
def test_hybrid_success_derives_table_provenance_and_retains_accounting(
    pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, model_table: bool
) -> None:
    def invoke(command: list[str], _log: Path) -> int:
        pipeline = Path(command[command.index("--output") + 1])
        pipeline.mkdir()
        manifest = json.loads(Path(command[command.index("--manifest") + 1]).read_text())
        identifier = manifest["pages"][0]["id"]
        tables = [{"text_provenance": "native-source", "source_conserved": True}]
        if model_table:
            tables.append({"text_provenance": "model-transcribed", "source_conserved": False})
        row = {
            "id": identifier, "status": "ok", "tables": tables,
            "source_conserved": not model_table, "accounting_complete": True, "source_inventory_complete": True,
        }
        wrapper.write_json(pipeline / f"{identifier}-structure.json", row)
        (pipeline / f"{identifier}.md").write_text("Retained native prose and table output")
        wrapper.write_json(pipeline / f"{identifier}-result.json", row)
        wrapper.write_json(pipeline / "report.json", {"results": [row]})
        return 0

    monkeypatch.setattr(wrapper, "_invoke", invoke)
    output = tmp_path / "hybrid-success"
    result = wrapper.extract(pdf, output, mode="hybrid-haiku")
    assert result["complete"]
    page = result["pages"][0]
    assert page["source_conserved"] is (not model_table)
    assert page["accounting_complete"]
    assert page["source_inventory_complete"]
    if model_table:
        assert page["text_provenance"] == "mixed native/OCR source-owned and model-transcribed"
        assert page["table_text_provenance"][1]["text_provenance"] == "model-transcribed"
    else:
        assert page["text_provenance"] == "native/OCR source-owned"
    state = json.loads((output / page["structure"]).read_text())
    assert state["tables"][0]["text_provenance"] == "native-source"


def test_combined_markdown_limit_preserves_pages_without_reading_or_truncating_them(
    pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def invoke(command: list[str], _log: Path) -> int:
        pipeline = Path(command[command.index("--output") + 1])
        pipeline.mkdir()
        manifest = json.loads(Path(command[command.index("--manifest") + 1]).read_text())
        identifier = manifest["pages"][0]["id"]
        (pipeline / f"{identifier}.md").write_text("é" * 200)
        wrapper.write_json(pipeline / f"{identifier}-structure.json", {"tables": []})
        wrapper.write_json(pipeline / "report.json", {
            "results": [{"id": identifier, "status": "ok", "source_conserved": True, "tables": []}],
        })
        return 0

    monkeypatch.setattr(wrapper, "MAX_COMBINED_BYTES", 256)
    monkeypatch.setattr(wrapper, "_invoke", invoke)
    output = tmp_path / "combined-refusal"
    result = wrapper.extract(pdf, output)
    assert result["requested_pages_complete"]
    assert not result["complete"]
    assert result["status"] == "partial"
    assert result["combined_output_error"] == "CombinedMarkdownSizeLimit"
    assert not result["combined_markdown_complete"]
    page_markdown = output / result["pages"][0]["markdown"]
    assert page_markdown.read_text() == "é" * 200
    combined = (output / "document.md").read_text()
    assert "size limit" in combined
    assert "é" not in combined
    assert len(combined.encode()) <= 256


def test_explicit_mixed_label_is_preserved_and_native_label_cannot_override_model_table() -> None:
    row = {
        "tables": [{"text_provenance": "model-transcribed", "source_conserved": False}],
        "source_conserved": False, "accounting_complete": True, "source_inventory_complete": True,
        "text_provenance": "mixed native/OCR prose and model-transcribed tables",
    }
    assert wrapper._provenance(row, "hybrid-haiku")["text_provenance"] == row["text_provenance"]  # noqa: SLF001
    row["text_provenance"] = "native/OCR source-owned"
    assert wrapper._provenance(row, "hybrid-haiku")["text_provenance"] == "model-transcribed tables"  # noqa: SLF001


def test_whole_page_admission_precedes_range_materialization(
    pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pylopdf  # noqa: PLC0415 - metadata-only mock.

    document = MagicMock()
    document.__enter__.return_value.__len__.return_value = 129
    monkeypatch.setattr(pylopdf, "open", lambda **_kwargs: document)
    materialize = MagicMock(side_effect=AssertionError("Must reject before allocating page indices"))
    monkeypatch.setattr(wrapper, "range", materialize, raising=False)
    with pytest.raises(ValueError, match="max_pages admission"):
        wrapper.extract(pdf, tmp_path / "oversized-page-count")
    materialize.assert_not_called()
