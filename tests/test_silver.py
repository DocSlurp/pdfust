"""DEV boundary, reproducibility and reporting tests for the opt-in silver runner."""

# Mock subprocess arguments and heterogeneous JSON fixtures follow the runner schema.
# ruff: noqa: ANN401

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from bench import silver
from conftest import build_pdf


def make_dataset(tmp_path: Path, *, encodings: tuple[str, ...] = ("positioned",)) -> Path:
    """Write a tiny DEV dataset without importing or generating the full corpus."""
    directory = tmp_path / "dataset"
    (directory / "pdfs").mkdir(parents=True)
    records = []
    gold = []
    data = build_pdf(["Anchor"])
    for index, encoding in enumerate(encodings):
        case_id = f"case-{index}"
        (directory / "pdfs" / (case_id + ".pdf")).write_bytes(data)
        records.append(
            {
                "id": case_id,
                "pdf_path": f"pdfs/{case_id}.pdf",
                "pdf_sha256": silver.sha(data),
                "split": "DEV",
                "family": "math",
                "producer_group": "same",
                "encoding": encoding,
            }
        )
        gold.append({"id": case_id, "pdf_sha256": silver.sha(data), "expected_text": ["Anchor"]})
    silver.write_json(directory / "manifest.json", {"split": "DEV", "cases": records, "dataset_sha256": "fixture"})
    silver.write_json(directory / "gold.json", gold)
    return directory


@pytest.mark.parametrize("split", [None, "TEST", "dev"])
@pytest.mark.parametrize("scope", ["manifest", "case"])
def test_reject_split_before_gold_or_pdf(tmp_path: Path, split: str | None, scope: str) -> None:
    directory = make_dataset(tmp_path)
    manifest = json.loads((directory / "manifest.json").read_text())
    target = manifest if scope == "manifest" else manifest["cases"][0]
    target["split"] = split
    silver.write_json(directory / "manifest.json", manifest)
    (directory / "gold.json").unlink()
    (directory / "pdfs/case-0.pdf").unlink()
    with pytest.raises(ValueError, match="DEV"):
        silver.benchmark(directory)
    with pytest.raises(ValueError, match="DEV"):
        silver.gallery(directory)


@pytest.mark.parametrize("name", ["heldout-silver", "silver-heldout-v1"])
def test_guard_heldout_paths_and_symlinks(tmp_path: Path, name: str) -> None:
    blocked = tmp_path / name
    # No fixture contents exist, so a read would fail differently from the boundary guard.
    with pytest.raises(ValueError, match="Held-out"):
        silver.benchmark(blocked)
    with pytest.raises(ValueError, match="Held-out"):
        silver.gallery(blocked)
    with pytest.raises(ValueError, match="Held-out"):
        silver.worker(blocked / "input.pdf")
    alias = tmp_path / "alias"
    alias.symlink_to(blocked, target_is_directory=True)
    with pytest.raises(ValueError, match="Held-out"):
        silver.load_manifest(alias)


@pytest.mark.parametrize("relative", ["../outside.pdf", "/outside.pdf"])
def test_reject_manifest_path_traversal(tmp_path: Path, relative: str) -> None:
    directory = make_dataset(tmp_path)
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["cases"][0]["pdf_path"] = relative
    silver.write_json(directory / "manifest.json", manifest)
    (directory / "gold.json").unlink()
    with pytest.raises(ValueError, match="relative"):
        silver.benchmark(directory)


def test_reject_symlink_escape(tmp_path: Path) -> None:
    directory = make_dataset(tmp_path)
    path = directory / "pdfs/case-0.pdf"
    path.unlink()
    path.symlink_to(tmp_path / "outside.pdf")
    with pytest.raises(ValueError, match="escapes"):
        silver.load_manifest(directory)


@pytest.mark.parametrize("operation", [silver.benchmark, silver.gallery])
def test_verify_pdf_checksum(tmp_path: Path, operation: Any) -> None:
    directory = make_dataset(tmp_path)
    (directory / "pdfs/case-0.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash changed"):
        operation(directory)


def test_timeout_retained_and_run_directories_unique(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = make_dataset(tmp_path)

    def timeout(*args: Any, **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(silver.platform, "platform", lambda: "test platform")
    monkeypatch.setattr(silver.platform, "processor", lambda: "test CPU")
    monkeypatch.setattr(silver.subprocess, "run", timeout)
    first = silver.benchmark(directory)
    second = silver.benchmark(directory)
    assert first["run_directory"] != second["run_directory"]
    assert first["completed"] == 0
    row = json.loads((Path(first["run_directory"]) / "metadata.jsonl").read_text())
    assert row["status"] == "error"
    assert row["error_type"] == "TimeoutExpired"
    assert row["timeout_seconds"] == 120


def test_document_and_page_exports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = make_dataset(tmp_path)
    result = {
        "metadata": {
            "pages": [{"page_number": 0, "text": {"characters": 6}}, {"page_number": 1, "text": {"characters": 7}}]
        },
        "extraction": {"text": "Anchor", "markdown": "Anchor", "warm_equal": True},
        "resources": {"peak_rss_bytes": 123},
        "warnings": [],
    }

    def completed(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs["env"]["CUDA_VISIBLE_DEVICES"] == ""
        return subprocess.CompletedProcess(args[0], 0, json.dumps(result), "")

    monkeypatch.setattr(silver.platform, "platform", lambda: "test platform")
    monkeypatch.setattr(silver.platform, "processor", lambda: "test CPU")
    monkeypatch.setattr(silver.subprocess, "run", completed)
    summary = silver.benchmark(directory)
    output = Path(summary["run_directory"])
    pages = [json.loads(line) for line in (output / "pages.jsonl").read_text().splitlines()]
    assert [page["page_number"] for page in pages] == [0, 1]
    assert all(page["id"] == "case-0" and page["split"] == "DEV" for page in pages)
    with (output / "pages.csv").open(newline="") as handle:
        csv_pages = list(csv.DictReader(handle))
    assert csv_pages[1]["text.characters"] == "7"
    assert (output / "metadata.csv").exists()
    assert (output / "case-0.txt").read_text() == "Anchor"
    row = json.loads((output / "metadata.jsonl").read_text())
    assert row["silver_anchor_score"]["found"] == 1
    assert "not layout/math correctness" in row["silver_anchor_score"]["metric"]


def test_gallery_keeps_encoding_modes(tmp_path: Path) -> None:
    directory = make_dataset(tmp_path, encodings=("vector-outlines", "raster-image", "positioned-math"))
    sheet = silver.gallery(directory)
    assert sheet.exists()
    assert len(list(sheet.parent.glob("case-*.png"))) == 3


def test_worker_extracts_with_explicit_resource_scope(tmp_path: Path) -> None:
    directory = make_dataset(tmp_path)
    result = silver.worker(directory / "pdfs/case-0.pdf")
    assert "Anchor" in result["extraction"]["text"]
    assert result["extraction"]["warm_equal"]
    assert result["metadata"]["pages"][0]["page_number"] == 0
    resources = result["resources"]
    assert resources["wall_ms"] > 0
    assert resources["cpu_ms"] >= 0
    assert "after imports" in resources["scope"]
    assert "including imports" in resources["scope"]
    assert resources["peak_rss_bytes"] is None or resources["peak_rss_bytes"] > 0
