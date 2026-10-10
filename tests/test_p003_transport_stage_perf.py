"""Synthetic-only measured transport path and accounting conservation."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest
from bench import decision_hosted as hosted
from bench import p003_transport_stage_perf as perf


def test_actual_accounting_path_never_constructs_client_or_opens_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        message = "Credentials or actual network must never be reached"
        raise AssertionError(message)

    monkeypatch.setattr(hosted.DecisionClient, "__init__", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    report = perf.measure(tmp_path / "measured", 10, provider_delay=0.005, export_delay=0.03)
    assert report["network_calls"] == report["real_inference_usd"] == 0
    assert len(report["traces"]) == 3
    ledger = json.loads((tmp_path / "measured" / "ledger.json").read_bytes())
    fresh = ledger["requests"][10:]
    assert len({e["reservation_uuid"] for e in fresh}) == 3
    assert len({e["request_sha256"] for e in fresh}) == 1
    assert all(e["cost_status"] == "provider-reported USD" for e in fresh)
    assert sum(e["accounted_usd"] for e in fresh) == pytest.approx(0.003)
    for trace in report["traces"]:
        assert trace["fake_provider_calls"] == 1
        assert trace["stages"]["export"] >= 0.03
        assert trace["stages"]["provider_read"] >= 0.005
        assert sum(trace["stages"].values()) == pytest.approx(trace["slot_occupied_seconds"])
        assert trace["client_wall_seconds"] >= trace["slot_occupied_seconds"]
        assert [e["phase"] for e in trace["nested_events"] if e["event"] == "load_validate"] == [
            "reserve",
            "financial_settlement",
            "annotation",
        ]
        assert trace["entry"]["telemetry"]["status"] == "synthetic-delayed-export"
    assert report["metrics"]["cpu_seconds"] > 0
    assert report["metrics"]["peak_sampled_rss_bytes"] > 0
    assert report["quality_or_full_pipeline_rate"] is None


def test_zero_export_control_and_rejects_overwrite_and_large_delays(tmp_path: Path) -> None:
    report = perf.measure(tmp_path / "zero", 0, provider_delay=0, export_delay=0)
    assert all(t["entry"]["telemetry"]["status"] == "synthetic-zero-export" for t in report["traces"])
    assert report["slot_export_fraction"] < 1
    with pytest.raises(FileExistsError):
        perf.measure(tmp_path / "zero", 0)
    with pytest.raises(ValueError, match="bounded"):
        perf.measure(tmp_path / "invalid", 0, export_delay=100)
    with pytest.raises(ValueError, match="bounded"):
        perf.synthetic_ledger(23001)


def test_source_history_schema_contiguous_and_independent_positive_accounting() -> None:
    ledger = perf.synthetic_ledger(1000)
    assert [e["index"] for e in ledger["requests"]] == list(range(1000))
    assert len({e["request_sha256"] for e in ledger["requests"]}) == 1000
    assert ledger["concurrent_policy"] == perf.POLICY
    assert all(e["concurrent_state"] == "completed" for e in ledger["requests"])
    assert sum(e["accounted_usd"] for e in ledger["requests"]) == pytest.approx(0.1)


def test_settlement_oracle_rejects_skipped_cost_accounting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hosted.DecisionClient, "_account_result", lambda *_a: None)
    with pytest.raises(ValueError, match="conservation"):
        perf.measure(tmp_path / "skipped-accounting", 0, provider_delay=0, export_delay=0)
