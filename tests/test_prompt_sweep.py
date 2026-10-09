"""Prompt sweeps freeze instruction-only changes without reading scorer files."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from bench import prompt_sweep


def test_freeze_retains_evidence_and_never_reads_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for name in ("source-frozen.json", "candidates-frozen.json", "private-targets.json"):
        (source / name).write_text("unreadable private/scorer data")
    body: dict[str, Any] = {
        "model": prompt_sweep.runner.MODELS[0],
        "state": ["literal words", {"image": "bytes"}],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "original",
                "criteria": {"C0": "candidate", "not_table": "prose", "unresolved": "unknown"},
            }
        },
    }
    (source / "request.json").write_text(json.dumps(body))
    manifest = {
        "records": [
            {
                "route": "hosted_admission",
                "arm": "image512",
                "id": "source",
                "request": "request.json",
                "model": body["model"],
                "choices": list(body["questions"]["q0"]["criteria"]),
            }
        ]
    }
    (source / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(prompt_sweep.runner, "verify", lambda _: manifest)
    result = prompt_sweep.freeze(source, tmp_path / "out", "structure")
    assert len(result["runs"]) == 5
    for directory in map(Path, result["runs"]):
        frozen = json.loads((directory / "manifest.json").read_text())
        assert len(frozen["records"]) == 2
        for row in frozen["records"]:
            raw = (directory / row["request"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == row["sha256"]
            changed = json.loads(raw)
            changed["model"] = body["model"]
            changed["questions"]["q0"]["instructions"] = "original"
            assert changed == body
