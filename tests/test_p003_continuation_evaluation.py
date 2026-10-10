"""Captured continuation accounting cannot invent stopped CPU/RSS or omit attempts."""

import json
from pathlib import Path

import pytest
from bench.p003_boundary_run import _charges
from bench.p003_continuation_evaluation import close, verify_measurements
from bench.silver import sha


def fixture(path: Path) -> list[dict]:
    segment = path / "segment"
    segment.mkdir()
    (segment / "frozen.json").write_text(json.dumps({"config": {"run_id": "run"}}))
    entries = [
        {
            "index": 1,
            "tag": "P003/run/page/r0/0",
            "accounted_usd": 0.1,
            "provider_reported_usd": 0.1,
            "cost_status": "provider-reported USD",
        }
    ]
    (path / "ledger.json").write_text(json.dumps({"requests": entries}))
    charges = _charges(entries)
    charges["cost_scope"] = (
        "All attempts in exact original segment tag prefix; includes failures and preserves all accounting bases."
    )
    (path / "costs-0.json").write_text(json.dumps(charges))
    (path / "queue-0.json").write_text(json.dumps({"arms": [{"name": "run", "wall_seconds": 2.0}]}))
    return [
        {
            "directory": str(segment),
            "measurement": {
                "cost_receipt": str(path / "costs-0.json"),
                "cost_receipt_sha256": sha((path / "costs-0.json").read_bytes()),
                "queue_status_sha256": sha((path / "queue-0.json").read_bytes()),
                "ledger_sha256": sha((path / "ledger.json").read_bytes()),
                "effective_usd": 0.1,
                "accounted_usd": 0.1,
                "metrics": {"wall_seconds": 2.0, "cpu_seconds": None, "peak_sampled_rss_bytes": None},
            },
        }
    ]


def test_absent_stopped_parent_resources_remain_unknown(tmp_path: Path) -> None:
    specs = fixture(tmp_path)
    output = verify_measurements(tmp_path, specs, [None])
    assert output["aggregate_parent_cpu_seconds"] is None
    specs[0]["measurement"]["metrics"]["cpu_seconds"] = 0
    with pytest.raises(ValueError, match="invents"):
        verify_measurements(tmp_path, specs, [None])


def test_captured_attempt_inventory_cannot_be_removed(tmp_path: Path) -> None:
    specs = fixture(tmp_path)
    costs = json.loads((tmp_path / "costs-0.json").read_text())
    costs["entries"] = []
    (tmp_path / "costs-0.json").write_text(json.dumps(costs))
    specs[0]["measurement"]["cost_receipt_sha256"] = sha((tmp_path / "costs-0.json").read_bytes())
    with pytest.raises(ValueError, match="omit"):
        verify_measurements(tmp_path, specs, [None])


def test_boolean_and_missing_costs_are_not_totals() -> None:
    assert not close(True, 1)
    assert not close(None, 0)
