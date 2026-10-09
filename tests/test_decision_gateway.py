"""Gateway route isolation and shared-budget checks with mocked HTTP only."""

from __future__ import annotations

import hashlib
import json
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any, Self

import pytest
from bench import decision_hosted as hosted
from bench.decision_gateway import (
    ENDPOINT,
    GATEWAY,
    MODELS,
    GatewayDecisionClient,
    normalize_response,
    read_gateway_key,
    request_identity,
)
from bench.lowlevel_run import parse_response


def body(model: str = "liquid/d1") -> dict[str, Any]:
    value: dict[str, Any] = {
        "model": model,
        "state": {"literal": "Keep source characters exactly"},
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Choose source grouping",
                "criteria": {"join": "One group", "split": "Two groups", "unresolved": "Unknown"},
            }
        },
    }
    if model != "liquid/d1":
        value["providerOptions"] = {"gateway": {"only": ["boundless"]}}
    return value


def payload(model: str = "liquid/d1", cost: str | None = "0.002") -> dict[str, Any]:
    gateway: dict[str, Any] = {"routing": {"finalProvider": "liquid"}, "generationId": "gen-test"}
    if cost is not None:
        gateway["cost"] = cost
    return {
        "model": model,
        "answers": {
            "q0": {"type": "choice", "choice": "join", "probabilities": {"join": 0.8, "split": 0.1, "unresolved": 0.1}}
        },
        "usage": {"input_tokens": 100, "output_tokens": 0},
        "provider_metadata": {"gateway": gateway},
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> GatewayDecisionClient:
    # Explicit synthetic prior evidence supports the exact shared budget calculation.
    prior = tmp_path / "bench/results/structure-artifacts/hosted-ledger.json"
    prior.parent.mkdir(parents=True)
    prior.write_text('{"requests":[]}')
    monkeypatch.setattr(hosted, "TOTAL_LIMIT", 100.0)
    monkeypatch.setattr(hosted, "CAMPAIGN_LIMIT", 98.0)
    monkeypatch.setattr(GatewayDecisionClient, "_telemetry", lambda *_: {"status": "local mock"})
    return GatewayDecisionClient(
        tmp_path,
        api_key="test-secret-123",
        rates={model: {"input": 0.04 / 1e6 if model == "liquid/d1" else 0, "output": 0} for model in MODELS},
    )


def transport(monkeypatch: pytest.MonkeyPatch, result: dict[str, Any]) -> list[Any]:
    calls: list[Any] = []
    raw = json.dumps(result, indent=2).encode()

    class Response:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_: object) -> None:
            pass

        def read(self, limit: int) -> bytes:
            assert limit == hosted.MAX_RESPONSE_BYTES + 1
            return raw[:limit]

    def open_mock(request: Any, *, timeout: int) -> Response:  # noqa: ANN401
        assert request.full_url == ENDPOINT
        assert timeout == 90
        calls.append(request)
        return Response()

    monkeypatch.setattr("bench.decision_gateway.urllib.request.urlopen", open_mock)
    return calls


def test_key_precedence_uses_only_synthetic_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "process-dummy")
    (tmp_path / ".env.remote-hosts").write_text("AI_GATEWAY_API_KEY=remote-dummy\n")
    (tmp_path / ".env").write_text("export AI_GATEWAY_API_KEY='local-dummy' # comment\n")
    assert read_gateway_key(tmp_path) == "local-dummy"
    (tmp_path / ".env").unlink()
    assert read_gateway_key(tmp_path) == "remote-dummy"
    (tmp_path / ".env.remote-hosts").unlink()
    assert read_gateway_key(tmp_path) == "process-dummy"
    monkeypatch.delenv("AI_GATEWAY_API_KEY")
    with pytest.raises(RuntimeError, match="not configured"):
        read_gateway_key(tmp_path)


def test_gateway_replay_never_reads_same_body_openrouter_record(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    request_body = body()
    encoded = json.dumps(request_body, separators=(",", ":")).encode()
    client.ledger.write_text(
        json.dumps(
            {
                "requests": [
                    {
                        "index": 0,
                        "request_sha256": hashlib.sha256(encoded).hexdigest(),
                        "accounted_usd": 0.3,
                        "response_file": "do-not-read-openrouter.json",
                        "error": "prior OR failure",
                    }
                ]
            }
        )
    )
    calls = transport(monkeypatch, payload())
    first = client.request(request_body, tag="L009/test")
    assert not first["replayed"]
    assert len(calls) == 1
    assert first["entry"]["index"] == 1
    assert first["entry"]["gateway"] == GATEWAY
    assert first["entry"]["request_sha256"] == hashlib.sha256(encoded).hexdigest()
    assert first["entry"]["request_identity_sha256"] == request_identity(encoded)
    assert first["entry"]["accounted_usd"] == 0.002
    raw = (client.directory / first["entry"]["response_file"]).read_bytes()
    assert raw == json.dumps(payload(), indent=2).encode()
    assert parse_response(first["result"], 1)[0]["choice"] == "join"
    second = client.request(request_body, tag="L009/test")
    assert second["replayed"]
    assert len(calls) == 1
    assert second["result"] == first["result"]
    assert "test-secret-123" not in client.ledger.read_text()
    assert "test-secret-123" not in (client.directory / "request-001.json").read_text()


@pytest.mark.parametrize("value", ["0", None])
def test_gateway_zero_or_missing_charge_estimates_only_complete_usage(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    raw = payload(cost=value)
    raw["usage"].pop("output_tokens")
    transport(monkeypatch, raw)
    result = client.request(body(), tag="L009/incomplete")
    assert "output_tokens" not in result["result"]["usage"]
    assert result["entry"]["cost_status"] == "reserved"
    assert result["entry"]["accounted_usd"] == hosted.RESERVATION
    assert result["entry"].get("provider_reported_usd") == (0 if value == "0" else None)


def test_zero_charge_uses_gateway_rates_and_preserves_reported_zero(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport(monkeypatch, payload(cost="0"))
    result = client.request(body(), tag="L009/estimate")
    assert result["entry"]["provider_reported_usd"] == 0
    assert result["entry"]["provider_cost_raw"] == "0"
    assert result["entry"]["accounted_usd"] == pytest.approx(100 * 0.04 / 1e6)
    assert result["entry"]["catalog_rates"] == {"input": 0.04 / 1e6, "output": 0}
    assert result["entry"]["pricing_gateway"] == GATEWAY


def test_shared_budget_includes_other_gateways_and_prior_api(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = transport(monkeypatch, payload())
    client.ledger.write_text('{"requests":[{"accounted_usd":97.8}]}')
    with pytest.raises(RuntimeError, match="shared campaign"):
        client.request(body(), tag="L009/campaign")
    client.ledger.write_text('{"requests":[{"accounted_usd":97.2}]}')
    prior = client.root / "bench/results/structure-artifacts/hosted-ledger.json"
    prior.write_text('{"requests":[{"accounted_usd":2}]}')
    with pytest.raises(RuntimeError, match="cumulative"):
        client.request(body(), tag="L009/cumulative")
    assert not calls


def test_failure_retains_reservation_and_is_never_retried(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []

    def fail(request: Any, *, timeout: int) -> None:  # noqa: ANN401
        calls.append(request)
        assert timeout == 90
        raise urllib.error.HTTPError(ENDPOINT, 503, "not logged", Message(), None)

    monkeypatch.setattr("bench.decision_gateway.urllib.request.urlopen", fail)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        client.request(body(), tag="L009/failure")
    with pytest.raises(RuntimeError, match="Previous identical Gateway call"):
        client.request(body(), tag="L009/failure")
    assert len(calls) == 1
    entry = json.loads(client.ledger.read_text())["requests"][0]
    assert entry["accounted_usd"] == hosted.RESERVATION
    assert entry["error"] == "HTTP 503"
    assert entry["elapsed_ms"] >= 0


def test_camel_usage_normalizes_without_changing_answers_or_inventing_outputs() -> None:
    raw: dict[str, Any] = {
        "answers": {"q0": {"choice": "join"}},
        "usage": {"inputTokens": 11},
        "providerMetadata": {"gateway": {"cost": "0.001"}},
    }
    normalized = normalize_response(raw)
    assert normalized["answers"] == raw["answers"]
    assert normalized["usage"]["input_tokens"] == 11
    assert normalized["usage"]["cost"] == 0.001
    assert "output_tokens" not in normalized["usage"]
    assert "input_tokens" not in raw["usage"]
    for invalid in ("nan", "-1", "inf", True):
        changed = {**raw, "providerMetadata": {"gateway": {"cost": invalid}}}
        assert "cost" not in normalize_response(changed)["usage"]


def test_model_routing_images_and_byte_admission_refuse_before_network(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = transport(monkeypatch, payload(MODELS[0]))
    for changed in (
        {**body(), "model": "typesafe-ai/laya"},
        {**body(MODELS[0]), "providerOptions": {}},
        {**body(), "providerOptions": {"gateway": {"models": ["fallback"]}}},
        {**body(MODELS[0]), "images": ["data:image/png;base64,YQ=="]},
        {**body(), "images": ["https://example.com/image.png"]},
    ):
        with pytest.raises(ValueError, match=r"Gateway|Laya|liquid"):
            client.request(changed, tag="L009/refusal")
    with pytest.raises(ValueError, match="byte admission"):
        client.request(body(), tag="L009/bytes", max_body_bytes=1)
    assert not calls
    assert not client.ledger.exists()
    client.request(body(MODELS[0]), tag="L009/laya")
    assert json.loads(calls[0].data)["providerOptions"] == {"gateway": {"only": ["boundless"]}}


def test_unrequested_model_is_rejected_after_retaining_actual_charge(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport(monkeypatch, payload(model="unexpected/fallback"))
    with pytest.raises(RuntimeError, match="ValueError"):
        client.request(body(), tag="L009/wrong-model")
    entry = json.loads(client.ledger.read_text())["requests"][0]
    assert entry["served_model"] == "unexpected/fallback"
    assert entry["response_file"]
    assert entry["accounted_usd"] == 0.002
    assert entry["cost_status"] == "provider-reported USD"
    with pytest.raises(RuntimeError, match="Previous identical Gateway call"):
        client.request(body(), tag="L009/wrong-model")


def test_oversize_response_fails_with_conservative_reservation(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = payload()
    raw["oversized"] = "x" * hosted.MAX_RESPONSE_BYTES
    calls = transport(monkeypatch, raw)
    with pytest.raises(RuntimeError, match="ValueError"):
        client.request(body(), tag="L009/oversize")
    assert len(calls) == 1
    entry = json.loads(client.ledger.read_text())["requests"][0]
    assert "response_file" not in entry
    assert entry["accounted_usd"] == hosted.RESERVATION


def test_http_diagnostics_keep_only_known_types_locations_and_numeric_retry() -> None:
    from io import BytesIO  # noqa: PLC0415 - synthetic provider body only.

    from bench.decision_gateway import safe_http_error  # noqa: PLC0415 - isolated diagnostic contract.

    raw = {
        "error_type": "invalid_request",
        "message": "questions.q0.type: secret-source-value",
        "detail": [
            {
                "type": "string_type",
                "loc": ["body", "state", "glyphs", "rows", 0, "text"],
                "input": "secret-source-value",
                "msg": "secret-credential-value",
            },
            {
                "type": "secret-source-value",
                "loc": ["body", "state", "secret-source-value"],
                "ctx": {"secret": "secret-credential-value"},
            },
        ],
    }
    headers = Message()
    headers["Retry-After"] = "12.5"
    headers["Authorization"] = "secret-credential-value"
    error = urllib.error.HTTPError(ENDPOINT, 422, "secret-credential-value", headers, BytesIO(json.dumps(raw).encode()))
    result = safe_http_error(error)
    assert result["http_status"] == 422
    assert result["retry_after_seconds"] == 12.5
    assert result["error_types"] == ["invalid_request", "string_type"]
    assert ["body", "state", "glyphs", "rows", 0, "text"] in result["locations"]
    assert ["questions", "q0", "type"] in result["locations"]
    assert ["body", "state", "<redacted>"] in result["locations"]
    assert "secret-" not in json.dumps(result)


@pytest.mark.parametrize("value", [None, "Wed, 21 Oct 2026 07:28:00 GMT", "nan", "inf", "-1", "1e3", "999999", True])
def test_retry_after_rejects_dates_arbitrary_or_unbounded_values(value: object) -> None:
    from bench.decision_gateway import retry_after_seconds  # noqa: PLC0415 - pure bounded header parser.

    assert retry_after_seconds(value) is None
    assert retry_after_seconds("0") == 0
    assert retry_after_seconds(" 15 ") == 15


def test_error_diagnostic_payload_and_list_work_are_bounded() -> None:
    from io import BytesIO  # noqa: PLC0415 - synthetic provider body only.

    from bench.decision_gateway import MAX_ERROR_BYTES, MAX_ERROR_ITEMS, safe_http_error  # noqa: PLC0415

    oversized = BytesIO(b"x" * (MAX_ERROR_BYTES + 5000))
    error = urllib.error.HTTPError(ENDPOINT, 429, "secret", Message(), oversized)
    result = safe_http_error(error)
    assert result["body_admission"] == "too_large"
    assert oversized.tell() == MAX_ERROR_BYTES + 1
    records = [{"type": "string_type", "loc": ["state", "rows", index]} for index in range(100)]
    error = urllib.error.HTTPError(
        ENDPOINT, 422, "secret", Message(), BytesIO(json.dumps({"detail": records}).encode())
    )
    result = safe_http_error(error)
    assert result["body_admission"] == "json"
    assert result["items_limited"]
    assert len(result["locations"]) <= MAX_ERROR_ITEMS
    non_json = urllib.error.HTTPError(ENDPOINT, 500, "secret", Message(), BytesIO(b"secret-source-value"))
    result = safe_http_error(non_json)
    assert result["body_admission"] == "non_json"
    assert "secret" not in json.dumps(result)


def test_gateway_failure_persists_safe_diagnostics_without_retry(
    client: GatewayDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from io import BytesIO  # noqa: PLC0415 - synthetic provider body only.

    headers = Message()
    headers["Retry-After"] = "7"

    def fail(request: Any, *, timeout: int) -> None:  # noqa: ANN401
        assert timeout == 90
        assert request.full_url == ENDPOINT
        raise urllib.error.HTTPError(
            ENDPOINT,
            422,
            "not logged",
            headers,
            BytesIO(b'{"error_type":"invalid_request","message":"state: secret-source-value"}'),
        )

    monkeypatch.setattr("bench.decision_gateway.urllib.request.urlopen", fail)
    with pytest.raises(RuntimeError, match="HTTP 422"):
        client.request(body(), tag="L012/diagnostics")
    entry = json.loads(client.ledger.read_text())["requests"][0]
    assert client.gateway == GATEWAY
    assert entry["http_error_diagnostic"]["retry_after_seconds"] == 7
    assert entry["http_error_diagnostic"]["locations"] == [["state"]]
    assert entry["accounted_usd"] == hosted.RESERVATION
    assert "secret-source-value" not in client.ledger.read_text()
