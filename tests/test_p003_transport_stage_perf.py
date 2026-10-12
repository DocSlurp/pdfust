"""Synthetic-only measured transport path and accounting conservation."""

from __future__ import annotations

import pytest
from bench import p003_transport_stage_perf as perf


def test_source_history_schema_contiguous_and_independent_positive_accounting() -> None:
    ledger = perf.synthetic_ledger(1000)
    assert [e["index"] for e in ledger["requests"]] == list(range(1000))
    assert len({e["request_sha256"] for e in ledger["requests"]}) == 1000
    assert ledger["concurrent_policy"] == perf.POLICY
    assert all(e["concurrent_state"] == "completed" for e in ledger["requests"])
    assert sum(e["accounted_usd"] for e in ledger["requests"]) == pytest.approx(0.1)


