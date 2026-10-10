"""Evidence-backed BYOK corrections retain original charges and failed attempts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench.p003_cost_reconciliation import reconcile
from bench.silver import sha


def test_report_and_unresolved_failures_survive_cost_correction(tmp_path: Path) -> None:
    run = tmp_path / "sample"
    run.mkdir()
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    request = b'{"model":"example"}'
    entries = [
        {"index": i, "tag": f"P003/sample/page/{i}", "request_sha256": sha(request),
         "accounted_usd": 0.3, "cost_status": "reserved", "reservation_usd": 0.3}
        for i in range(2)
    ]
    entries[0].update(response_file="response-000.json", provider_reported_usd=0)
    usage = {"cost": 0, "is_byok": True, "cost_details": {"upstream_inference_cost": 0.012}}
    (ledger_dir / "response-000.json").write_text(json.dumps({"usage": usage}))
    for i in range(2):
        (ledger_dir / f"request-{i:03d}.json").write_bytes(request)
    path = ledger_dir / "ledger.json"
    path.write_text(json.dumps({"requests": entries}))
    report = {"config": {"campaign": "P003", "run_id": "sample"}, "ledger_attempts": 2, "accounted_usd": 0.6}
    report_bytes = json.dumps(report).encode()
    (run / "report.json").write_bytes(report_bytes)
    sidecar = reconcile(run, path, tmp_path / "corrected")
    corrected = json.loads(path.read_bytes())["requests"]
    assert (run / "report.json").read_bytes() == report_bytes
    assert corrected[0]["accounted_usd"] == 0.012
    assert corrected[0]["provider_reported_usd"] == 0
    assert corrected[0]["accounting_revisions"][0]["original"]["accounted_usd"] == 0.3
    assert corrected[1] == entries[1]
    assert sidecar["entries"][1]["response_path"] is None
    assert sidecar["entries"][0]["original_accounting"]["cost_status"] == "reserved"
    with pytest.raises(ValueError, match="already changed"):
        reconcile(run, path, tmp_path / "second")
    assert json.loads(path.read_bytes())["requests"] == corrected


def test_changed_request_refuses_ledger_mutation(tmp_path: Path) -> None:
    run = tmp_path / "sample"
    run.mkdir()
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    ledger = {"requests": [{"index": 0, "tag": "P003/sample/p/0", "request_sha256": "wrong",
                            "accounted_usd": 0.3, "cost_status": "reserved"}]}
    path = ledger_dir / "ledger.json"
    original = json.dumps(ledger).encode()
    path.write_bytes(original)
    (ledger_dir / "request-000.json").write_text("{}")
    (run / "report.json").write_text(json.dumps({
        "config": {"campaign": "P003", "run_id": "sample"}, "ledger_attempts": 1, "accounted_usd": 0.3,
    }))
    with pytest.raises(ValueError, match="request bytes"):
        reconcile(run, path, tmp_path / "correction")
    assert path.read_bytes() == original
