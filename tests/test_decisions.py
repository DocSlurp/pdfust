from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from bench.decisions import load_predictions


def test_saved_predictions_require_matching_evidence(tmp_path: Path) -> None:
    path, evidence = tmp_path / "predictions.json", tmp_path / "cases.json"
    cases = [{"id": "one", "gold": True}]
    predictions = [{"case_id": "one", "p_yes": 0.9}]
    digest = hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest()
    path.write_text(json.dumps({"predictions": predictions, "cases_sha256": digest}))
    assert load_predictions(path, evidence, cases) == predictions
    with pytest.raises(ValueError, match="do not match"):
        load_predictions(path, evidence, [{"id": "one", "gold": False}])


def test_legacy_predictions_need_exact_retained_evidence(tmp_path: Path) -> None:
    path, evidence = tmp_path / "predictions.json", tmp_path / "cases.json"
    cases = [{"id": "one", "gold": True}]
    predictions = [{"case_id": "one", "p_yes": 0.9}]
    path.write_text(json.dumps({"predictions": predictions}))
    with pytest.raises(ValueError, match="do not match"):
        load_predictions(path, evidence, cases)
    evidence.write_text(json.dumps(cases))
    assert load_predictions(path, evidence, cases) == predictions
    evidence.write_text(json.dumps([{"id": "one", "gold": False}]))
    with pytest.raises(ValueError, match="do not match"):
        load_predictions(path, evidence, cases)
