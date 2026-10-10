"""Synthetic financial prototype invariants; production ledgers and networks unreachable."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest
from bench import decision_hosted as hosted
from bench import p003_sqlite_ledger_perf as perf


@pytest.mark.parametrize("backend", ["json", "sqlite"])
@pytest.mark.parametrize("workers", [3, 6])
def test_bounded_accounting_without_credentials_or_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                         backend: str, workers: int) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        message = "Actual transport or credentials forbidden"
        raise AssertionError(message)

    monkeypatch.setattr(hosted.DecisionClient, "__init__", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    result = perf.measure(tmp_path / "run", backend, 10, attempts=30, workers=workers,
                          provider_delay=0, export_delay=0)
    assert result["network_calls"] == result["real_inference_usd"] == 0
    assert result["invariants_passed"]
    assert result["unknown_failures"] == 3
    assert result["fresh_synthetic_accounted_usd"] == pytest.approx(3 * 0.3 + 27 * 0.001)
    assert all(t["provider_calls"] == 1 for t in result["traces"])
    if backend == "sqlite":
        assert result["maximum_persistent_inflight"] <= workers
        assert result["sqlite_settings"]["synchronous"] == "FULL"
    with pytest.raises(FileExistsError):
        perf.measure(tmp_path / "run", backend, 0)


def test_sqlite_caps_unique_settlement_and_unknown_identity(tmp_path: Path) -> None:
    ledger = perf.SQLiteLedger(tmp_path / "ledger.sqlite", 3)
    ledger.initialize([])
    connection = ledger.connect()
    entries = [ledger.reserve(connection, f"P003/a/{i}", f"sha-{i}") for i in range(3)]
    with pytest.raises(RuntimeError, match="cap"):
        ledger.reserve(connection, "P003/fourth", "sha-fourth")
    ledger.settle(connection, entries[0], True)
    with pytest.raises(RuntimeError, match="duplicate"):
        ledger.settle(connection, entries[0], False)
    with pytest.raises(RuntimeError, match="failure"):
        ledger.reserve(connection, "P003/changed-tag", "sha-0")
    with pytest.raises(RuntimeError, match="tag"):
        ledger.reserve(connection, "P003/a/0", "changed-body")
    ledger.settle(connection, entries[1], False)
    ledger.settle(connection, entries[2], False)
    total, inflight, maximum = connection.execute("SELECT accounted,inflight,max_inflight FROM totals").fetchone()
    assert total == pytest.approx(0.302)
    assert inflight == 0
    assert maximum == 3
    payload = json.loads(connection.execute("SELECT payload FROM attempts WHERE idx=0").fetchone()[0])
    assert payload["accounted_usd"] == 0.3
    assert "provider_reported_usd" not in payload
    connection.close()


def test_sqlite_same_body_distinct_tags_are_reserved_independently(tmp_path: Path) -> None:
    ledger = perf.SQLiteLedger(tmp_path / "ledger.sqlite", 3)
    ledger.initialize([])
    connection = ledger.connect()
    a = ledger.reserve(connection, "P003/arm-a", "same-body")
    b = ledger.reserve(connection, "P003/arm-b", "same-body")
    assert a["reservation_uuid"] != b["reservation_uuid"]
    assert connection.execute("SELECT accounted,inflight FROM totals").fetchone() == (0.6, 2)
    ledger.settle(connection, a, False)
    ledger.settle(connection, b, False)
    connection.close()
