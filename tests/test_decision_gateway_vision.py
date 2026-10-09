"""Mock-only native vision translation, conservation, billing and route isolation."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Self

import pytest
from bench import decision_hosted as hosted
from bench.decision_gateway import ENDPOINT as TYPESAFE_ENDPOINT
from bench.decision_gateway import GatewayDecisionClient, request_identity
from bench.decision_gateway_vision import (
    ENDPOINT,
    MODEL,
    GatewayVisionDecisionClient,
    normalize_answers,
    translate,
    validate_wire,
)
from bench.lowlevel_run import parse_response


def canonical() -> dict[str, Any]:
    return {
        "model": MODEL,
        "state": '{"literal":"Ω 10"}',
        "images": ["data:image/png;base64,YWJj"],
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": "Choose exact source grouping",
                "criteria": {"join": "One", "split": "Two", "unresolved": "Unknown"},
            }
        },
    }


def native_response() -> dict[str, Any]:
    return {
        "model": MODEL,
        "answers": [
            {
                "name": "q0",
                "type": "choice",
                "choice": "join",
                "probabilities": [
                    {"value": "join", "probability": 0.8},
                    {"value": "split", "probability": 0.1},
                    {"value": "unresolved", "probability": 0.1},
                ],
            }
        ],
        "usage": {"input_tokens": 100},
        "provider_metadata": {"gateway": {"cost": "0.002", "routing": {"finalProvider": "liquid"}}},
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> GatewayVisionDecisionClient:
    prior = tmp_path / "bench/results/structure-artifacts/hosted-ledger.json"
    prior.parent.mkdir(parents=True)
    prior.write_text('{"requests":[]}')
    monkeypatch.setattr(hosted, "TOTAL_LIMIT", 100.0)
    monkeypatch.setattr(hosted, "CAMPAIGN_LIMIT", 98.0)
    monkeypatch.setattr(GatewayDecisionClient, "_telemetry", lambda *_: {})
    return GatewayVisionDecisionClient(tmp_path, api_key="mock-only", rates={MODEL: {"input": 0.04e-6, "output": 0}})


def transport(monkeypatch: pytest.MonkeyPatch, result: dict[str, Any]) -> list[Any]:
    calls = []

    class Response:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_: object) -> None:
            pass

        def read(self, limit: int) -> bytes:
            return json.dumps(result).encode()[:limit]

    def send(request: Any, *, timeout: int) -> Response:  # noqa: ANN401
        assert timeout == 90
        calls.append(request)
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", send)
    return calls


def test_translation_preserves_question_order_values_text_images_and_options() -> None:
    body = canonical()
    original = deepcopy(body)
    wire = translate(body)
    assert body == original
    assert wire["input"][0]["content"][0]["text"] == body["state"]
    assert wire["input"][0]["content"][1]["image_url"] == body["images"][0]
    assert wire["questions"][0]["instructions"] == body["questions"]["q0"]["instructions"]
    assert wire["questions"][0]["choices"] == [
        {"value": k, "description": v} for k, v in body["questions"]["q0"]["criteria"].items()
    ]
    assert json.loads(validate_wire(wire, 7500)) == wire
    with pytest.raises(ValueError, match="native wire fields"):
        validate_wire(body, 7500)
    wire["providerOptions"] = {"gateway": {"models": ["other"]}}
    with pytest.raises(ValueError, match="fallbacks"):
        validate_wire(wire, 7500)


def test_native_wire_identity_retention_replay_usage_and_provider_cost(
    client: GatewayVisionDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = native_response()
    calls = transport(monkeypatch, raw)
    wire = translate(canonical())
    result = client.request(wire, tag="L016/test", max_body_bytes=7500)
    assert calls[0].full_url == ENDPOINT
    transmitted = calls[0].data
    assert json.loads(transmitted) == wire
    entry = result["entry"]
    assert entry["request_sha256"] == hashlib.sha256(transmitted).hexdigest()
    assert entry["request_identity_sha256"] == request_identity(transmitted, endpoint=ENDPOINT)
    assert entry["request_identity_sha256"] != request_identity(transmitted, endpoint=TYPESAFE_ENDPOINT)
    assert json.loads((client.directory / entry["response_file"]).read_bytes()) == raw
    assert entry["accounted_usd"] == 0.002
    assert entry["provider"] == "liquid"
    assert "output_tokens" not in result["result"]["usage"]
    assert parse_response(result["result"], 1)[0]["choice"] == "join"
    assert client.request(wire, tag="L016/replay", max_body_bytes=7500)["replayed"]
    assert len(calls) == 1


@pytest.mark.parametrize("defect", ["duplicate", "sum", "missing", "refusal", "wrong-choice"])
def test_malformed_answer_refused(defect: str) -> None:
    raw = native_response()
    answer = raw["answers"][0]
    if defect == "duplicate":
        answer["probabilities"].append(answer["probabilities"][0])
    elif defect == "sum":
        answer["probabilities"][0]["probability"] = 0.6
    elif defect == "missing":
        answer.pop("probabilities")
    elif defect == "refusal":
        answer["type"] = "refusal"
    else:
        answer["choice"] = "split"
    with pytest.raises(ValueError, match="Gateway vision"):
        normalize_answers(raw, translate(canonical()))


def test_paid_refusal_retains_charge_and_blocks_retry(
    client: GatewayVisionDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = native_response()
    raw["answers"][0] = {"name": "q0", "type": "refusal"}
    calls = transport(monkeypatch, raw)
    wire = translate(canonical())
    with pytest.raises(RuntimeError, match="accounting retained"):
        client.request(wire, tag="L016/refusal", max_body_bytes=7500)
    entry = json.loads(client.ledger.read_bytes())["requests"][0]
    assert entry["accounted_usd"] == 0.002
    assert entry["response_file"]
    with pytest.raises(RuntimeError, match="Previous identical"):
        client.request(wire, tag="L016/retry", max_body_bytes=7500)
    assert len(calls) == 1


def test_typesafe_record_cannot_replay_native_wire(
    client: GatewayVisionDecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    wire = translate(canonical())
    raw_wire = validate_wire(wire, 7500)
    client.ledger.write_text(
        json.dumps(
            {
                "requests": [
                    {
                        "gateway": "vercel",
                        "request_sha256": hashlib.sha256(raw_wire).hexdigest(),
                        "request_identity_sha256": request_identity(raw_wire),
                        "accounted_usd": 0,
                        "error": "HTTP422",
                    }
                ]
            }
        )
    )
    calls = transport(monkeypatch, native_response())
    assert not client.request(wire, tag="L016/new", max_body_bytes=7500)["replayed"]
    assert len(calls) == 1
