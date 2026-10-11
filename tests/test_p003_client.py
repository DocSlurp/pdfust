"""Mock-only P003 shared admission and BYOK settlement checks."""
from __future__ import annotations

# ruff: noqa: ANN001, ANN201, ANN202, SLF001 - mocked client internals.
import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from bench import decision_hosted as hosted
from bench.decision_hosted import DecisionClient
from bench.p003_client import P003ConcurrentClient, P003DecisionClient


@pytest.fixture(autouse=True)
def _admission_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep P003 admission open so these mocks do not expire with the real deadlines."""
    from bench import research_policy  # noqa: PLC0415

    monkeypatch.setattr(research_policy, "P003_PAID_CUTOFF", float("inf"))
    monkeypatch.setattr(research_policy, "P003_EXTENSION_CUTOFF", float("inf"))


def test_stops_arm_without_second_reservation(tmp_path, monkeypatch):
    base = hosted.DecisionClient.__new__(hosted.DecisionClient)
    base.root, base.directory = tmp_path, tmp_path
    base.ledger = tmp_path / "ledger.json"
    base.key = "mock"
    monkeypatch.setattr(base, "_prior_api_cost", lambda: 0)
    opener = MagicMock(side_effect=OSError("mock transport failure"))
    client = P003ConcurrentClient(client=base, opener=opener)
    assert client._concurrent.policy == {
        "max_inflight": 3, "wave_limits_usd": {"P003": 280.0}, "allow_matched_replicates": True,
    }
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


def test_transport_failure_stops_subsequent_paid_admissions(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(P003DecisionClient)
    calls = []

    def failed(_self: object, body: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        calls.append(body)
        raise RuntimeError

    monkeypatch.setattr(DecisionClient, "request", failed)
    with pytest.raises(RuntimeError):
        client.request({"model": "example"}, tag="P003/first")
    with pytest.raises(RuntimeError, match="arm stopped"):
        client.request({"model": "different"}, tag="P003/second")
    assert len(calls) == 1


def test_success_does_not_stop_new_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(P003DecisionClient)
    monkeypatch.setattr(DecisionClient, "request", lambda *_args, **_kwargs: {"result": {}})
    assert client.request({}, tag="P003/a") == {"result": {}}
    assert client.request({}, tag="P003/b") == {"result": {}}
    assert not client.stopped
