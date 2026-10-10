from __future__ import annotations

from typing import Any

import pytest
from bench.decision_hosted import DecisionClient
from bench.p003_client import P003DecisionClient


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
