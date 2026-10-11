from __future__ import annotations

import pytest
from bench import research_policy as policy


def test_wave_counts_all_providers_and_unresolved_reservations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(policy.time, "time", lambda: policy.P003_PAID_CUTOFF - 1)
    ledger = {"requests": [
        {"tag": "P002/old", "accounted_usd": 49},
        {"tag": "P003/or", "accounted_usd": 79.5},
        {"tag": "P003/gateway", "accounted_usd": 0.3, "cost_status": "reserved"},
    ]}
    with pytest.raises(RuntimeError, match="wave cap"):
        policy.admit_wave(ledger, "P003/next", 0.3)
    policy.admit_wave(ledger, "P003/next", 0.2)


def test_deadline_prevents_new_admission(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(policy.time, "time", lambda: policy.P003_PAID_CUTOFF)
    with pytest.raises(RuntimeError, match="deadline"):
        policy.admit_wave({"requests": []}, "P003/next", 0.3)
    policy.admit_wave({"requests": []}, "P002/historical", 0.3)


def test_extension_admits_only_new_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(policy.time, "time", lambda: policy.P003_PAID_CUTOFF + 1)
    policy.admit_wave({"requests": []}, "P003/extension-v1-pilot/page0", 0.3)
    for tag in ("P003/old-queue", "P003/extension-v1/pilot", "P003/extension-v10-pilot"):
        with pytest.raises(RuntimeError, match="deadline"):
            policy.admit_wave({"requests": []}, tag, 0.3)


def test_extension_deadline_and_wave_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    tag = "P003/extension-v1-pilot/page0"
    monkeypatch.setattr(policy.time, "time", lambda: policy.P003_EXTENSION_CUTOFF - 1)
    ledger = {"requests": [{"tag": "P003/historical", "accounted_usd": 79.8}]}
    with pytest.raises(RuntimeError, match="wave cap"):
        policy.admit_wave(ledger, tag, 0.3)
    monkeypatch.setattr(policy.time, "time", lambda: policy.P003_EXTENSION_CUTOFF)
    with pytest.raises(RuntimeError, match="deadline"):
        policy.admit_wave({"requests": []}, tag, 0.3)


@pytest.mark.parametrize("amount", [True, -1, float("nan"), float("inf"), "0"])
def test_invalid_wave_accounting_fails_closed(monkeypatch: pytest.MonkeyPatch, amount: object) -> None:
    monkeypatch.setattr(policy.time, "time", lambda: policy.P003_PAID_CUTOFF - 1)
    with pytest.raises(ValueError, match="accounting"):
        policy.admit_wave({"requests": [{"tag": "P003/x", "accounted_usd": amount}]}, "P003/next", 0.3)
