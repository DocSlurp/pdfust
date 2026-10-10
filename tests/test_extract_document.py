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
