from __future__ import annotations

import json
import sys
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from bench import decision_hosted as hosted


@pytest.fixture
def client(tmp_path: Path) -> hosted.DecisionClient:
    (tmp_path / ".env.remote-hosts").write_text("OPENROUTER_API_KEY='fake-test-key-only'\n")
    prior = tmp_path / "bench/results/structure-artifacts/hosted-ledger.json"
    prior.parent.mkdir(parents=True)
    prior.write_text(json.dumps({"requests": [{"accounted_usd": 0.12}]}))
    return hosted.DecisionClient(tmp_path)


def body() -> dict[str, Any]:
    return {"model": hosted.JEV, "state": "source evidence", "questions": {}}


def result(*, cost: object = 0.01) -> dict[str, Any]:
    return {
        "model": "typesafe/jev-1.13-20260917",
        "provider": "TypeSafe",
        "id": "fake-generation",
        "usage": {"cost": cost},
        "answers": {
            "q0_yes": {"type": "noul", "noul": 0.9},
            "q0_answerable": {"type": "noul", "noul": 0.8},
        },
    }


def response(payload: bytes) -> MagicMock:
    mock = MagicMock()
    mock.__enter__.return_value.read.return_value = payload
    return mock


def test_reservation_precedes_transmission_and_success_replays(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = MagicMock()

    def transmit(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401
        calls(request)
        persisted = json.loads(client.ledger.read_text())["requests"]
        assert len(persisted) == 1
        assert persisted[0]["cost_status"] == "reserved"
        assert persisted[0]["accounted_usd"] == hosted.RESERVATION
        assert persisted[0]["prior_accounted_usd"] == pytest.approx(hosted.PRIOR_RENTAL + 0.12)
        assert request.full_url == "https://openrouter.ai/api/alpha/decisions"
        assert request.get_header("Authorization") == "Bearer fake-test-key-only"
        assert timeout == 90
        return response(json.dumps(result()).encode())

    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    first = client.request(body(), tag="first")
    second = client.request(body(), tag="replay")
    assert not first["replayed"]
    assert second["replayed"]
    assert first["result"] == second["result"]
    assert first["entry"]["accounted_usd"] == 0.01
    assert first["entry"]["cost_status"] == "provider-reported USD"
    assert calls.call_count == 1
    assert len(json.loads(client.ledger.read_text())["requests"]) == 1
    for path in client.directory.rglob("*"):
        if path.is_file():
            assert "fake-test-key-only" not in path.read_text()


@pytest.mark.parametrize("cost", [None, True, -1, "0.01", float("nan"), float("inf")])
def test_unknown_cost_keeps_reservation(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
    cost: object,
) -> None:
    mock = MagicMock(return_value=response(json.dumps(result(cost=cost)).encode()))
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    entry = client.request(body(), tag="unknown-cost")["entry"]
    assert entry["accounted_usd"] == hosted.RESERVATION
    assert entry["cost_status"] == "reserved"


def test_http_failure_retains_reservation_without_secret_error_body(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = urllib.error.HTTPError("https://openrouter.ai", 429, "fake-test-key-only", Message(), None)
    transmit = MagicMock(side_effect=failure)
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    with pytest.raises(RuntimeError, match="HTTP 429") as captured:
        client.request(body(), tag="failed")
    entry = json.loads(client.ledger.read_text())["requests"][0]
    assert entry["accounted_usd"] == hosted.RESERVATION
    assert entry["error"] == "HTTP 429"
    assert "response_file" not in entry
    assert "fake-test-key-only" not in str(captured.value)
    assert "fake-test-key-only" not in client.ledger.read_text()
    with pytest.raises(RuntimeError):
        client.request(body(), tag="failed-again")
    assert transmit.call_count == 1


@pytest.mark.parametrize("payload", [b"invalid json", b"x" * (hosted.MAX_RESPONSE_BYTES + 1)])
def test_invalid_or_oversized_response_retains_reservation(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
) -> None:
    mock = response(payload)
    monkeypatch.setattr(hosted.urllib.request, "urlopen", MagicMock(return_value=mock))
    with pytest.raises(RuntimeError, match="reservation retained"):
        client.request(body(), tag="bad-response")
    mock.__enter__.return_value.read.assert_called_once_with(hosted.MAX_RESPONSE_BYTES + 1)
    entry = json.loads(client.ledger.read_text())["requests"][0]
    assert entry["accounted_usd"] == hosted.RESERVATION
    assert "response_file" not in entry


@pytest.mark.parametrize("limit", ["CAMPAIGN_LIMIT", "TOTAL_LIMIT"])
def test_cap_refusal_does_not_transmit_or_reserve(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
    limit: str,
) -> None:
    monkeypatch.setattr(hosted, limit, 0.1)
    transmit = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    with pytest.raises(RuntimeError, match="authorized spend"):
        client.request(body(), tag="over-cap")
    transmit.assert_not_called()
    assert not client.ledger.exists()


def test_existing_campaign_reservations_count_toward_cap(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hosted.checkpoint(
        client.ledger, {"requests": [{"request_sha256": "prior", "accounted_usd": hosted.CAMPAIGN_LIMIT - 0.1}]}
    )
    transmit = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    before = client.ledger.read_bytes()
    with pytest.raises(RuntimeError, match="authorized spend"):
        client.request(body(), tag="existing-cap")
    transmit.assert_not_called()
    assert client.ledger.read_bytes() == before


@pytest.mark.parametrize("cost", [float("nan"), float("inf"), -0.1, True, "0.01", None])
@pytest.mark.parametrize("ledger_kind", ["prior", "campaign"])
def test_corrupted_accounting_refuses_network_without_new_reservation(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
    cost: object,
    ledger_kind: str,
) -> None:
    path = (
        client.root / "bench/results/structure-artifacts/hosted-ledger.json"
        if ledger_kind == "prior"
        else client.ledger
    )
    hosted.checkpoint(path, {"requests": [{"request_sha256": "previous", "accounted_usd": cost}]})
    before = path.read_bytes()
    transmit = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    with pytest.raises(ValueError, match="finite nonnegative"):
        client.request(body(), tag="corrupted-accounting")
    transmit.assert_not_called()
    assert path.read_bytes() == before


def test_windows_lock_initializes_one_byte_and_unlocks_after_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native = MagicMock()
    monkeypatch.setitem(sys.modules, "msvcrt", native)
    monkeypatch.setattr(hosted.sys, "platform", "win32")
    path = tmp_path / "portable.lock"

    def fail_inside_lock() -> None:
        with hosted.exclusive_lock(path):
            assert path.read_bytes() == b"\0"
            message = "inside lock"
            raise RuntimeError(message)

    with pytest.raises(RuntimeError, match="inside lock"):
        fail_inside_lock()
    assert native.locking.call_count == 2
    assert native.locking.call_args_list[0].args[1:] == (native.LK_LOCK, 1)
    assert native.locking.call_args_list[1].args[1:] == (native.LK_UNLCK, 1)


@pytest.mark.parametrize("request_data", [{"model": "unapproved"}, {"model": hosted.JEV, "state": "x" * 32_001}])
def test_request_admission_precedes_reservation(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
    request_data: dict[str, Any],
) -> None:
    transmit = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    with pytest.raises(ValueError, match="admission"):
        client.request(request_data, tag="not-admitted")
    transmit.assert_not_called()
    assert not client.ledger.exists()


@pytest.mark.parametrize("value", [True, None, "0.5", -0.01, 1.01, float("nan"), float("inf")])
def test_probability_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError, match="finite number"):
        hosted.probability(value)


def test_jev_parsing_requires_exact_candidate_keys() -> None:
    valid = result()
    assert hosted.parse_answers(hosted.JEV, valid, 1) == [{"p_yes": 0.9, "p_answerable": 0.8}]
    valid["answers"]["q1_yes"] = {"noul": 0.9}
    with pytest.raises(ValueError, match="keys"):
        hosted.parse_answers(hosted.JEV, valid, 1)
    valid["answers"].pop("q1_yes")
    valid["answers"].pop("q0_answerable")
    with pytest.raises(ValueError, match="keys"):
        hosted.parse_answers(hosted.JEV, valid, 1)


def chat_result(answers: dict[str, Any], *, finish: str = "stop") -> dict[str, Any]:
    return {"choices": [{"finish_reason": finish, "message": {"content": json.dumps(answers)}}]}


def test_chat_parsing_rejects_truncation_extra_fields_and_invalid_scores() -> None:
    answers = {"answers": {"q0": {"p_yes": 0.0, "p_answerable": 1.0}}}
    model = hosted.MODELS[1]
    assert hosted.parse_answers(model, chat_result(answers), 1) == [{"p_yes": 0.0, "p_answerable": 1.0}]
    with pytest.raises(ValueError, match="truncated"):
        hosted.parse_answers(model, chat_result(answers, finish="length"), 1)
    answers["answers"]["q0"]["invented"] = 0.1
    with pytest.raises(ValueError, match="fields"):
        hosted.parse_answers(model, chat_result(answers), 1)
    answers["answers"]["q0"].pop("invented")
    answers["answers"]["q0"]["p_yes"] = 2
    with pytest.raises(ValueError, match="finite number"):
        hosted.parse_answers(model, chat_result(answers), 1)
    with pytest.raises(ValueError, match="keys"):
        hosted.parse_answers(model, chat_result({"answers": {}}), 1)
    with pytest.raises(ValueError, match="keys"):
        hosted.parse_answers(model, chat_result({**answers, "extra": 1}), 1)


def test_request_ablation_excludes_gold_without_mutating_evidence() -> None:
    case: dict[str, Any] = {
        "question": "Is w1 assigned to r1?",
        "gold": True,
        "split": "test",
        "state": {"page": {"width": 100}, "words": [{"id": "w1", "text": "42", "bbox": [1, 2, 3, 4], "line": 0}]},
    }
    stripped = hosted.public_case(case, "text")
    assert stripped == {"question": case["question"], "data": {"words": [{"id": "w1", "text": "42"}]}}
    assert "bbox" in case["state"]["words"][0]
    request = hosted.request_body(hosted.JEV, [case], "rich")
    assert set(request["questions"]) == {"q0_yes", "q0_answerable"}
    assert all("observations.q0" in item["instructions"] for item in request["questions"].values())
    assert "gold" not in json.dumps(request)


@pytest.mark.parametrize("reported", [0, None])
def test_zero_or_missing_cost_uses_catalog_and_retains_reported_value(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch, reported: float | None
) -> None:
    prices = client.directory / "langfuse/catalog-prices.json"
    prices.parent.mkdir()
    prices.write_text(json.dumps({"fetched_at": 123, "prices": {hosted.JEV: {"input": 0.000001, "output": 0}}}))
    payload = result(cost=reported)
    payload["usage"].update(input_tokens=1000, output_tokens=0)
    monkeypatch.setattr(
        hosted.urllib.request, "urlopen", lambda *_args, **_kwargs: response(json.dumps(payload).encode())
    )
    entry = client.request(body(), tag="catalog-fallback")["entry"]
    assert entry["accounted_usd"] == pytest.approx(0.001)
    assert entry["cost_status"] == "catalog estimate"
    assert entry.get("provider_reported_usd") == reported
    assert entry["catalog_fetched_at"] == 123


def test_large_image_admission_is_explicit_and_bounded(client: hosted.DecisionClient) -> None:
    oversized = body()
    oversized["state"] = "x" * (hosted.MAX_BODY_BYTES + 1)
    with pytest.raises(ValueError, match="admission"):
        client.request(oversized, tag="default-rejects-large-image")
    with pytest.raises(ValueError, match="ceiling"):
        client.request(oversized, tag="hard-ceiling", max_body_bytes=hosted.MAX_IMAGE_BODY_BYTES + 1)
    assert not client.ledger.exists()


def test_explicit_cache_probe_retransmits_identical_successful_body(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = MagicMock(return_value=response(json.dumps(result()).encode()))
    monkeypatch.setattr(hosted.urllib.request, "urlopen", calls)
    first = client.request(body(), tag="first")
    second = client.request(body(), tag="actual-repeat", replay=False)
    assert calls.call_count == 2
    assert not first["replayed"]
    assert not second["replayed"]
    assert first["entry"]["request_sha256"] == second["entry"]["request_sha256"]
    assert first["entry"]["index"] != second["entry"]["index"]
    assert second["entry"]["force_transmission"] is True
    assert len(json.loads(client.ledger.read_text())["requests"]) == 2
