from __future__ import annotations

import json
import re
import urllib.error
from email.message import Message
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest
from bench.decision_langfuse import (
    _configuration,
    _model_definition,
    _payload,
    _prices,
    emit_request,
    sync_models,
    verify_trace,
)

MODEL = "perplexity/pplx-decider-v1.1-27b"
CONFIG = {
    "LANGFUSE_PUBLIC_KEY": "test-public",
    "LANGFUSE_SECRET_KEY": "test-secret",
    "LANGFUSE_BASE_URL": "https://example.test",
}


def sample() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        {"model": MODEL, "state": "PRIVATE SOURCE", "questions": {"q0": {"instructions": "PRIVATE PROMPT"}}},
        {
            "usage": {"input_tokens": 100, "output_tokens": 2, "cost": 0},
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": "A",
                    "probabilities": {"A": 1, "B": 0, "unresolved": 0},
                    "explanation": "PRIVATE ANSWER",
                }
            },
        },
        {
            "request_sha256": "a" * 64,
            "started_at": 1791500000.0,
            "elapsed_ms": 250.0,
            "accounted_usd": 0,
            "cost_status": "provider-reported USD",
        },
    )


def attributes(payload: dict[str, Any]) -> dict[str, Any]:
    span = payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    return {item["key"]: next(iter(item["value"].values())) for item in span["attributes"]}


def test_provider_zero_uses_catalog_estimate_and_native_usage_wins() -> None:
    body, result, entry = sample()
    result["usage"]["prompt_tokens"] = 99999
    _, payload = _payload(body, result, entry, {MODEL: {"input": 0.01, "output": 0.5}})
    attrs = attributes(payload)
    assert json.loads(attrs["langfuse.observation.usage_details"]) == {"input": 100, "output": 2}
    assert json.loads(attrs["langfuse.observation.cost_details"]) == {"input": 1.0, "output": 1.0, "total": 2.0}
    assert attrs["langfuse.observation.metadata.provider_reported_usd"] == 0.0
    assert attrs["langfuse.observation.metadata.catalog_estimated_usd"] == 2.0
    assert attrs["langfuse.observation.metadata.cost_basis"] == "estimated"
    assert attrs["langfuse.observation.metadata.effective_cost_complete"] is True
    assert "langfuse.observation.metadata.ledger_reservation_usd" not in attrs


def test_unknown_charge_retains_reservation_only_as_metadata() -> None:
    body, result, entry = sample()
    del result["usage"]["cost"]
    del result["usage"]["output_tokens"]
    entry.update(accounted_usd=0.3, cost_status="reserved")
    _, payload = _payload(body, result, entry, {MODEL: {"input": 0.001, "output": 0.001}})
    attrs = attributes(payload)
    assert json.loads(attrs["langfuse.observation.cost_details"]) == {"input": 0.1}
    assert json.loads(attrs["langfuse.observation.usage_details"]) == {"input": 100}
    assert attrs["langfuse.observation.metadata.ledger_reservation_usd"] == 0.3
    assert attrs["langfuse.observation.metadata.catalog_estimated_usd"] == 0.1
    assert attrs["langfuse.observation.metadata.catalog_estimate_is_charge"] is False
    assert attrs["langfuse.observation.metadata.catalog_estimate_complete"] is False
    assert attrs["langfuse.observation.metadata.effective_cost_complete"] is False
    assert json.loads(attrs["langfuse.observation.metadata.catalog_estimate_missing_components"]) == ["output"]


def test_positive_provider_charge_wins_over_catalog_estimate() -> None:
    body, result, entry = sample()
    result["usage"]["cost"] = 0.25
    _, payload = _payload(body, result, entry, {MODEL: {"input": 0.01, "output": 0.5}})
    attrs = attributes(payload)
    assert json.loads(attrs["langfuse.observation.cost_details"]) == {"total": 0.25}
    assert attrs["langfuse.observation.metadata.provider_reported_usd"] == 0.25
    assert attrs["langfuse.observation.metadata.cost_basis"] == "provider-reported"
    assert "langfuse.observation.metadata.catalog_estimated_usd" not in attrs


def test_p003_changed_price_uses_telemetry_alias_without_changing_request() -> None:
    body, result, entry = sample()
    body["model"] = "cloudflare/clef-flash"
    entry["tag"] = "P003/price-change"
    _, payload = _payload(body, result, entry, {body["model"]: {"input": 0.038 / 1e6, "output": 0.0}})
    attrs = attributes(payload)
    assert attrs["langfuse.observation.model.name"] == "cloudflare/clef-flash@2026-10-10"
    assert attrs["langfuse.observation.metadata.requested_model"] == "cloudflare/clef-flash"
    assert body["model"] == "cloudflare/clef-flash"
    assert attrs["langfuse.observation.metadata.catalog_estimated_usd"] == 100 * 0.038 / 1e6
    entry["tag"] = "P002/historical"
    _, payload = _payload(body, result, entry, {})
    assert attributes(payload)["langfuse.observation.model.name"] == "cloudflare/clef-flash"


def test_missing_charge_exports_complete_catalog_estimate_and_retains_reservation() -> None:
    body, result, entry = sample()
    del result["usage"]["cost"]
    entry.update(accounted_usd=0.3, cost_status="reserved")
    _, payload = _payload(body, result, entry, {MODEL: {"input": 0.01, "output": 0.5}})
    attrs = attributes(payload)
    assert json.loads(attrs["langfuse.observation.cost_details"]) == {"input": 1.0, "output": 1.0, "total": 2.0}
    assert attrs["langfuse.observation.metadata.ledger_reservation_usd"] == 0.3
    assert attrs["langfuse.observation.metadata.charge_unknown"] is True
    assert attrs["langfuse.observation.metadata.cost_basis"] == "estimated"
    assert "langfuse.observation.metadata.provider_reported_usd" not in attrs


def test_unknown_cost_with_missing_rates_or_usage_is_not_exported_as_zero() -> None:
    body, result, entry = sample()
    for prices, usage in ((None, {"cost": 0}), ({MODEL: {"input": 0.1, "output": 0.1}}, {})):
        result["usage"] = usage
        _, payload = _payload(body, result, entry, prices)
        attrs = attributes(payload)
        assert "langfuse.observation.cost_details" not in attrs
        assert attrs["langfuse.observation.metadata.cost_basis"] == "unknown"
        assert attrs["langfuse.observation.metadata.effective_cost_complete"] is False


def test_zero_output_rate_is_valid_and_missing_component_rate_stays_partial() -> None:
    body, result, entry = sample()
    _, payload = _payload(body, result, entry, {MODEL: {"input": 1e-7, "output": 0}})
    attrs = attributes(payload)
    costs = json.loads(attrs["langfuse.observation.cost_details"])
    assert costs == {"input": 100 * 1e-7, "output": 0.0, "total": 100 * 1e-7}
    assert attrs["langfuse.observation.metadata.effective_cost_complete"] is True
    _, payload = _payload(body, result, entry, {MODEL: {"input": 0.01}})
    attrs = attributes(payload)
    assert json.loads(attrs["langfuse.observation.cost_details"]) == {"input": 1.0}
    assert attrs["langfuse.observation.metadata.effective_cost_complete"] is False


def test_invalid_rates_are_not_used_for_estimates_or_registered() -> None:
    body, result, entry = sample()
    for invalid in (-1, float("inf"), float("nan"), True, "invalid", None):
        _, payload = _payload(body, result, entry, {MODEL: {"input": invalid, "output": invalid}})
        attrs = attributes(payload)
        assert "langfuse.observation.cost_details" not in attrs
        assert attrs["langfuse.observation.metadata.cost_basis"] == "unknown"
        assert _prices({"pricing": {"prompt": invalid, "completion": "0"}}) is None
    assert _prices({"pricing": []}) is None
    assert _prices({"pricing": {"prompt": "1e-7", "completion": "0"}}) == {"input": 1e-7, "output": 0}


def test_chat_token_aliases_and_missing_usage_are_not_fabricated() -> None:
    body, result, entry = sample()
    result["usage"] = {"prompt_tokens": 4, "completion_tokens": 0}
    _, payload = _payload(body, result, entry)
    assert json.loads(attributes(payload)["langfuse.observation.usage_details"]) == {"input": 4, "output": 0}
    result["usage"] = {}
    _, payload = _payload(body, result, entry)
    assert json.loads(attributes(payload)["langfuse.observation.usage_details"]) == {}


def test_sanitized_payload_excludes_source_prompts_images_and_free_text() -> None:
    body, result, entry = sample()
    body["state"] = [
        "PRIVATE SOURCE",
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,PRIVATE PIXELS"}},
    ]
    _, payload = _payload(body, result, entry)
    serialized = json.dumps(payload)
    assert "PRIVATE" not in serialized
    assert "data:image" not in serialized
    assert "explanation" not in serialized
    assert "test-secret" not in serialized


def test_embedding_exports_dimensions_hash_not_vectors() -> None:
    body, result, entry = sample()
    body = {"model": "google/gemini-embedding-2", "input": "PRIVATE TEXT"}
    result["data"] = [{"embedding": [0.123456789, 0.23456789]}]
    _, payload = _payload(body, result, entry)
    attrs = attributes(payload)
    assert attrs["langfuse.observation.type"] == "embedding"
    assert json.loads(attrs["langfuse.observation.output"])["embedding_dimensions"] == [2]
    assert "0.123456789" not in json.dumps(payload)


def test_trace_and_span_ids_remain_deterministic() -> None:
    body, result, entry = sample()
    first = _payload(body, result, entry)
    second = _payload(body, result, entry)
    assert first == second
    span = first[1]["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    assert len(first[0]) == 32
    assert len(span["spanId"]) == 16
    assert int(span["endTimeUnixNano"]) - int(span["startTimeUnixNano"]) == 250_000_000


def test_export_replay_does_not_duplicate_billable_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr("bench.decision_langfuse._configuration", lambda _root: CONFIG)

    def record_http(*args: object) -> dict[str, Any]:
        calls.append(args)
        return {}

    monkeypatch.setattr("bench.decision_langfuse._http", record_http)
    body, result, entry = sample()
    assert emit_request(tmp_path, body, result, entry)["status"] == "exported"
    assert emit_request(tmp_path, body, result, entry)["status"] == "replayed"
    assert len(calls) == 1
    assert str(calls[0][0]).endswith("/api/public/otel/v1/traces")


def test_export_errors_are_nonfatal_and_do_not_expose_provider_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("bench.decision_langfuse._configuration", lambda _root: CONFIG)

    def fail(*_args: object) -> dict[str, Any]:
        message = "PRIVATE SECRET"
        endpoint = "https://example.test"
        raise urllib.error.HTTPError(endpoint, 401, message, Message(), None)

    monkeypatch.setattr("bench.decision_langfuse._http", fail)
    body, result, entry = sample()
    assert emit_request(tmp_path, body, result, entry) == {"status": "error", "error": "HTTP 401"}
    assert not list(tmp_path.rglob("*.json"))


def test_dotenv_precedes_remote_host_file_without_reading_real_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in CONFIG:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    (tmp_path / ".env.remote-hosts").write_text(
        'LANGFUSE_PUBLIC_KEY="fallback-public"\nLANGFUSE_SECRET_KEY="fallback-secret"\n'
    )
    (tmp_path / ".env").write_text(
        'LANGFUSE_PUBLIC_KEY="test-public"\nLANGFUSE_SECRET_KEY="test-secret"\nLANGFUSE_BASE_URL="https://example.test"\n'
    )
    assert _configuration(tmp_path) == CONFIG


def test_exact_registry_patterns_and_per_token_tiers() -> None:
    definition = _model_definition(MODEL, {"input": 0.000001, "output": 0})
    assert re.fullmatch(definition["matchPattern"], MODEL)
    assert not re.fullmatch(definition["matchPattern"], MODEL + "-other")
    assert definition["startDate"].startswith("2026-10-08")
    assert definition["pricingTiers"][0]["prices"]["input"] == 0.000001
    assert definition["pricingTiers"][0]["isDefault"] is True


def test_registry_idempotence_preserves_managed_and_unrelated_definitions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("bench.decision_langfuse._configuration", lambda _root: CONFIG)
    existing: list[dict[str, Any]] = [
        {"modelName": "unrelated", "isLangfuseManaged": False},
        {"modelName": MODEL, "isLangfuseManaged": True},
    ]
    calls = []

    def mock_http(url: str, method: str = "GET", body: Any = None, config: Any = None) -> dict[str, Any]:  # noqa: ANN401 - mocked JSON transport.
        del config
        calls.append((url, method))
        if "openrouter.ai" in url:
            return {"data": [{"id": MODEL, "pricing": {"prompt": "0.000001", "completion": "0"}}]}
        if method == "GET":
            return {"data": existing, "meta": {"totalPages": 1}}
        existing.append({**body, "isLangfuseManaged": False})
        return body

    monkeypatch.setattr("bench.decision_langfuse._http", mock_http)
    assert sync_models(tmp_path, (MODEL,))["created"] == [MODEL]
    assert sync_models(tmp_path, (MODEL,))["existing"] == [MODEL]
    assert sum(method == "POST" for _, method in calls) == 1
    assert any("/embeddings/models" in url for url, _ in calls)
    assert existing[0]["modelName"] == "unrelated"
    assert existing[1]["isLangfuseManaged"] is True


def test_exact_project_price_conflict_is_reported_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("bench.decision_langfuse._configuration", lambda _root: CONFIG)
    existing = {**_model_definition(MODEL, {"input": 1, "output": 1}), "isLangfuseManaged": False}

    def mock_http(url: str, method: str = "GET", body: Any = None, config: Any = None) -> dict[str, Any]:  # noqa: ANN401 - mocked JSON transport.
        del body, config
        assert method == "GET"
        if "openrouter.ai" in url:
            return {"data": [{"id": MODEL, "pricing": {"prompt": "0.000001", "completion": "0"}}]}
        return {"data": [existing], "meta": {"totalPages": 1}}

    monkeypatch.setattr("bench.decision_langfuse._http", mock_http)
    assert sync_models(tmp_path, (MODEL,))["conflicts"] == [MODEL]


def test_verification_uses_exact_trace_current_api_without_io(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("bench.decision_langfuse._configuration", lambda _root: CONFIG)
    urls = []

    def mock_http(url: str, **_kwargs: Any) -> dict[str, Any]:  # noqa: ANN401 - mocked JSON transport.
        urls.append(url)
        return {
            "data": [{"traceId": "a" * 32, "input": "PRIVATE", "output": "PRIVATE", "usageDetails": {"input": 100}}]
        }

    monkeypatch.setattr("bench.decision_langfuse._http", mock_http)
    result = verify_trace(tmp_path, "a" * 32, 1791500000.0)
    assert result["status"] == "verified"
    assert "PRIVATE" not in json.dumps(result)
    assert "/api/public/v2/observations?" in urls[0]
    assert "fromStartTime" in urls[0]
    assert "traceId=" + "a" * 32 in urls[0]


def test_provider_cache_retransmissions_have_distinct_trace_identity() -> None:
    body, result, entry = sample()
    entry.update(force_transmission=True, index=1)
    first, payload = _payload(body, result, entry)
    entry["index"] = 2
    second, _ = _payload(body, result, entry)
    assert first != second
    assert attributes(payload)["langfuse.observation.metadata.request_sha256"] == entry["request_sha256"]


def test_cache_read_estimate_uses_published_cached_rate() -> None:
    body, result, entry = sample()
    result["usage"]["input_tokens_details"] = {"cached_tokens": 80, "cache_write_tokens": 0}
    _, payload = _payload(body, result, entry, {MODEL: {"input": 0.1, "output": 0.1, "input_cache_read": 0.01}})
    attrs = attributes(payload)
    assert json.loads(attrs["langfuse.observation.cost_details"])["total"] == 3.0
    assert attrs["langfuse.observation.metadata.cache_status"] == "reported counters"
