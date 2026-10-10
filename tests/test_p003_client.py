"""Mock-only P003 shared admission and BYOK settlement checks."""
from __future__ import annotations

# ruff: noqa: ANN001, ANN201, ANN202, SLF001 - mocked client internals.
import json
from unittest.mock import MagicMock

import pytest
from bench import decision_hosted as hosted
from bench.p003_client import P003ConcurrentClient


def test_stops_arm_without_second_reservation(tmp_path, monkeypatch):
    base = hosted.DecisionClient.__new__(hosted.DecisionClient)
    base.root, base.directory = tmp_path, tmp_path
    base.ledger = tmp_path / "ledger.json"
    base.key = "mock"
    monkeypatch.setattr(base, "_prior_api_cost", lambda: 0)
    opener = MagicMock(side_effect=OSError("mock transport failure"))
    client = P003ConcurrentClient(client=base, opener=opener)
    assert client._concurrent.policy == {"max_inflight": 3, "wave_limits_usd": {"P003": 50.0}}
    with pytest.raises(RuntimeError):
        client.request({"model": hosted.JEV, "questions": {}}, tag="P003/mock")
    with pytest.raises(RuntimeError, match="arm stopped"):
        client.request({"model": hosted.JEV, "questions": {}}, tag="P003/mock-next")
    assert opener.call_count == 1
    assert len(json.loads(base.ledger.read_text())["requests"]) == 1


def test_settlement_preserves_byok_components(tmp_path, monkeypatch):
    base = hosted.DecisionClient.__new__(hosted.DecisionClient)
    base.root, base.directory = tmp_path, tmp_path
    base.ledger = tmp_path / "ledger.json"
    base.key = "mock"
    monkeypatch.setattr(base, "_prior_api_cost", lambda: 0)
    monkeypatch.setattr(base, "_telemetry", lambda *_args: {"status": "disabled"})

    def account(_body, _result, entry):
        entry.update(accounted_usd=0.05, provider_reported_usd=0.02,
                     upstream_inference_usd=0.03, gateway_reported_usd=0.02, cost_status="mock")

    monkeypatch.setattr(base, "_account_result", account)
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b'{"usage":{"cost":0.02}}'
    client = P003ConcurrentClient(client=base, opener=MagicMock(return_value=response))
    result = client.request({"model": hosted.JEV, "questions": {}}, tag="P003/mock")
    saved = json.loads(base.ledger.read_text())["requests"][0]
    for field in ("upstream_inference_usd", "gateway_reported_usd"):
        assert saved[field] == result["entry"][field]
