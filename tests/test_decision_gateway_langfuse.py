"""Gateway transport identity and published-rate telemetry isolation."""

from __future__ import annotations

import json

from bench.decision_langfuse import _payload


def test_gateway_identity_and_prices_do_not_reuse_openrouter() -> None:
    body = {"model": "liquid/d1", "state": "private", "questions": {}}
    response = {"usage": {"input_tokens": 100, "output_tokens": 0, "cost": 0}, "answers": {}}
    entry = {
        "request_sha256": "a" * 64,
        "request_identity_sha256": "b" * 64,
        "gateway": "vercel",
        "catalog_rates": {"input": 0.00000004, "output": 0},
        "started_at": 1791500000.0,
        "elapsed_ms": 100,
        "cost_status": "catalog-estimated USD",
        "accounted_usd": 0.000004,
    }
    trace, payload = _payload(body, response, entry, {"liquid/d1": {"input": 999, "output": 999}})
    assert trace == "b" * 32
    span = payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    attrs = {x["key"]: next(iter(x["value"].values())) for x in span["attributes"]}
    assert attrs["langfuse.observation.model.name"] == "vercel/liquid/d1"
    assert attrs["langfuse.observation.metadata.gateway"] == "vercel"
    assert json.loads(attrs["langfuse.observation.cost_details"])["total"] == 0.000004
    assert attrs["langfuse.observation.metadata.provider_reported_usd"] == 0
    assert attrs["langfuse.trace.metadata.request_sha256"] == "a" * 64
