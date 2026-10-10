"""Offline replay refuses incomplete controls and stale verified identities."""
from pathlib import Path

import pytest
from bench.generalization_native_orientation_audit import RUNS, replay
from bench.silver import sha, write_json


def fixture(root: Path, *, count: int = 276, stale: bool = False) -> None:
    manifest = root / "corpus-r2/manifest.json"
    report = root / RUNS[0] / "report.json"
    manifest.parent.mkdir()
    report.parent.mkdir()
    write_json(manifest, {"pages": [{"id": str(i)} for i in range(276)]})
    write_json(report, {"results": [{"id": str(i), "status": "error"} for i in range(count)]})
    write_json(report.with_name("verified-evaluation.json"), {
        "report_sha256": "stale" if stale else sha(report.read_bytes()),
        "manifest_sha256": sha(manifest.read_bytes()),
    })


def test_missing_page_is_rejected_before_reference_access(tmp_path: Path) -> None:
    fixture(tmp_path, count=275)
    with pytest.raises(ValueError, match="complete unique 276-page"):
        replay(tmp_path, RUNS[0])


def test_stale_verified_report_is_rejected(tmp_path: Path) -> None:
    fixture(tmp_path, stale=True)
    with pytest.raises(ValueError, match="report identity changed"):
        replay(tmp_path, RUNS[0])


def test_duplicate_page_is_rejected(tmp_path: Path) -> None:
    fixture(tmp_path)
    report = tmp_path / RUNS[0] / "report.json"
    write_json(report, {"results": [{"id": "same", "status": "error"} for _ in range(276)]})
    manifest = tmp_path / "corpus-r2/manifest.json"
    write_json(report.with_name("verified-evaluation.json"), {
        "report_sha256": sha(report.read_bytes()), "manifest_sha256": sha(manifest.read_bytes()),
    })
    with pytest.raises(ValueError, match="complete unique 276-page"):
        replay(tmp_path, RUNS[0])
