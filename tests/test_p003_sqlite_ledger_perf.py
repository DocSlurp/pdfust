"""Synthetic financial prototype invariants; production ledgers and networks unreachable."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_sqlite_ledger_perf as perf


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
