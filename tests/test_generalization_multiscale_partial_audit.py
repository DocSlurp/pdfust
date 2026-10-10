"""Named multiscale controls retain unsubmitted proposals in offline partial audits."""
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_partial_audit as audit


def write(path: Path, data: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data).encode()
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize("controls", [("unknown",), (), (audit.MULTISCALE_CONTROLS[0],) * 2])
def test_unnamed_empty_or_duplicate_controls_refused_before_file_access(
    tmp_path: Path, controls: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError, match="unique explicitly named"):
        audit.audit(tmp_path, tmp_path / "output", controls=controls)


def test_multiscale_preserves_pending_regions_and_original_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = [f"page{i}" for i in range(16)]
    corpus = tmp_path / "screens/natural16"
    manifest_sha = write(corpus / "manifest.json", {
        "split": "DEV", "dataset_sha256": "fixture", "pages": [{"id": i} for i in ids],
    })
    write(corpus / "private-targets.json", {
        "dataset_sha256": "fixture", "pages": [{"id": i, "tables": []} for i in ids],
    })
    region = {"index": 0, "request_index": 0, "viewport": [0, 0, 10, 10], "detector_box": [0, 0, 10, 10],
              "status": "not_requested"}
    results = [{"id": i, "status": "error", "viewport": [0, 0, 100, 100], "proposal_count": 1,
                "calls": [], "transcription_regions": [region]} for i in ids]
    name = audit.MULTISCALE_CONTROLS[0]
    report_sha = write(tmp_path / name / "report.json", {"results": results})
    write(tmp_path / name / "verified-evaluation.json", {
        "report_sha256": report_sha, "manifest_sha256": manifest_sha, "dataset_sha256": "fixture",
        "page_scores": [{"id": i, "error": True} for i in ids], "scores": {}, "costs": {}, "resources": {},
    })
    monkeypatch.setattr(audit, "score_dataset", lambda *_: {"totals": {}, "pages": []})
    result = audit.audit(tmp_path, tmp_path / "output", controls=(name,))
    assert len(result["runs"]) == 1
    pages = result["runs"][0]["partial_pages"]
    assert len(pages) == 16
    for page in pages:
        assert page["status"] == "partial"
        assert page["baseline_status"] == "error"
        assert page["baseline_proposal_count"] == 1
        assert page["baseline_calls"] == []
        assert page["baseline_region_inventory"][0]["status"] == "not_requested"
        assert page["baseline_region_inventory"][0]["response_present"] is False
        assert page["tables"] == []
        assert page["quarantined"]
