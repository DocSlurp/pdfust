"""Partial diagram decisions keep actual selected crops separate from operational failures."""

import json
from pathlib import Path

import pytest
from bench.p003_geometry_diagram_verification import quality_predictions, verify_decisions


def test_partial_selected_crop_quality_retained_without_operational_success() -> None:
    partial = {
        "id": "p",
        "status": "error",
        "selection_status": "selected_partial_crops",
        "tables": [{"literal": "selected complete table"}],
        "accepted_crop_count": 1,
    }
    failed = {
        "id": "q",
        "status": "error",
        "selection_status": "composition_failed",
        "tables": [],
        "accepted_crop_count": 0,
    }
    output = quality_predictions({"results": [partial, failed]})
    assert output[0]["status"] == "ok"
    assert output[0]["tables"] == partial["tables"]
    assert partial["status"] == "error"
    assert output[1]["status"] == "error"
    assert output[1]["tables"] == []


def test_duplicate_no_question_cannot_be_credited_as_model_selection(tmp_path: Path) -> None:
    item = {"index": 0, "page_id": "p", "crop_index": 0, "body": None, "status": "not_applicable_duplicates"}
    row = {"index": 0, "page_id": "p", "crop_index": 0, "model": "m", "status": "selected"}
    (tmp_path / "crop-0-result.json").write_text(json.dumps(row))
    with pytest.raises(ValueError, match="no-question"):
        verify_decisions(tmp_path, [item], {"model": "m"}, [row], initialization_failed=False)


def test_transport_stop_rejects_followup_answer(tmp_path: Path) -> None:
    item = {"index": 0, "page_id": "p", "crop_index": 0, "body": {"m": "question"}}
    row = {"index": 0, "page_id": "p", "crop_index": 0, "model": "m", "status": "selected"}
    (tmp_path / "crop-0-result.json").write_text(json.dumps(row))
    with pytest.raises(ValueError, match="first transport"):
        verify_decisions(tmp_path, [item], {"model": "m"}, [row], initialization_failed=True)
