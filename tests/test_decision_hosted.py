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


def test_explicit_pinned_serving_price_precedes_generic_catalog(client: hosted.DecisionClient) -> None:
    prices = client.directory / "langfuse/catalog-prices.json"
    prices.parent.mkdir()
    prices.write_text(json.dumps({
        "prices": {hosted.JEV: {"input": 0.001, "output": 0.002}},
        "serving_prices": {hosted.JEV: {"example/bf16": {"input": 0.003, "output": 0.004}}},
    }))
    request = {**body(), "provider": {"only": ["example/bf16"], "allow_fallbacks": False}}
    entry = {"index": 0, "accounted_usd": 0.3, "reservation_usd": 0.3, "cost_status": "reserved"}
    result = {"usage": {"cost": 0, "prompt_tokens": 10, "completion_tokens": 20}}
    client._account_result(request, result, entry)  # noqa: SLF001 - isolated settlement pricing regression.
    assert entry["accounted_usd"] == pytest.approx(0.11)
    assert entry["provider_reported_usd"] == 0
    assert entry["catalog_rates"] == {"input": 0.003, "output": 0.004}


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


@pytest.mark.parametrize("reserve", [True, 0.0, 0.29, float("nan"), float("inf")])
def test_invalid_custom_reservation_never_transmits(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch, reserve: object
) -> None:
    transmit = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    with pytest.raises(ValueError, match="reservation"):
        client.request(body(), tag="invalid-reserve", reservation_usd=reserve)  # type: ignore[arg-type]
    transmit.assert_not_called()
    assert not client.ledger.exists()


def test_larger_request_reservation_is_persisted_before_network_failure(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_args: Any, **_kwargs: Any) -> None:  # noqa: ANN401
        entry = json.loads(client.ledger.read_text())["requests"][0]
        assert entry["accounted_usd"] == entry["reservation_usd"] == 1.25
        raise TimeoutError

    monkeypatch.setattr(hosted.urllib.request, "urlopen", fail)
    with pytest.raises(RuntimeError, match="failed"):
        client.request(body(), tag="larger-reserve", reservation_usd=1.25)
    assert json.loads(client.ledger.read_text())["requests"][0]["accounted_usd"] == 1.25


def test_larger_reservation_cannot_cross_campaign_cap(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(hosted, "CAMPAIGN_LIMIT", 1.0)
    transmit = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    with pytest.raises(RuntimeError, match="authorized spend"):
        client.request(body(), tag="larger-over-cap", reservation_usd=1.25)
    transmit.assert_not_called()
    assert not client.ledger.exists()


@pytest.mark.parametrize("model", hosted.ANTHROPIC_BASELINE_MODELS)
def test_claude55_relationship_requests_use_supported_reasoning_settings(model: str) -> None:
    request = hosted.request_body(model, [], "rich")
    assert "temperature" not in request
    assert request["reasoning"] == {"effort": "medium"}
    assert request["max_tokens"] == 4096
    assert request["response_format"]["type"] == "json_schema"


def test_openrouter_does_not_replay_gateway_body(
    client: hosted.DecisionClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transmit = MagicMock(return_value=response(json.dumps(result()).encode()))
    monkeypatch.setattr(hosted.urllib.request, "urlopen", transmit)
    first = client.request(body(), tag="first")
    ledger = json.loads(client.ledger.read_text())
    ledger["requests"][0]["gateway"] = "vercel"
    client.ledger.write_text(json.dumps(ledger))
    second = client.request(body(), tag="openrouter")
    assert not second["replayed"]
    assert second["entry"]["index"] != first["entry"]["index"]
    assert transmit.call_count == 2


def failed_retry_entry(client: hosted.DecisionClient) -> dict[str, Any]:
    """Seed a synthetic retained failure without invoking transport or credentials."""
    import hashlib  # noqa: PLC0415 - fixture-only request fingerprint.

    entry = {
        "index": 0,
        "request_sha256": hashlib.sha256(json.dumps(body(), separators=(",", ":")).encode()).hexdigest(),
        "accounted_usd": hosted.RESERVATION,
        "reservation_usd": hosted.RESERVATION,
        "cost_status": "reserved",
        "error": "HTTP 500",
    }
    hosted.checkpoint(client.ledger, {"requests": [entry]})
    return entry


def test_explicit_retry_is_reserved_before_transport_and_only_once(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = failed_retry_entry(client)

    def transmit(*_args: Any, **_kwargs: Any) -> MagicMock:  # noqa: ANN401
        rows = json.loads(client.ledger.read_text())["requests"]
        assert rows[0] == original
        assert rows[1]["retry_of_index"] == 0
        assert rows[1]["retry_reason"] == "Investigated transient provider failure"
        assert rows[1]["accounted_usd"] == rows[1]["reservation_usd"] == hosted.RESERVATION
        return response(json.dumps(result()).encode())

    mock = MagicMock(side_effect=transmit)
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    answer = client.request(
        body(), tag="explicit", retry_failed_index=0, retry_reason="Investigated transient provider failure"
    )
    assert not answer["replayed"]
    assert answer["entry"]["force_transmission"] is True
    rows = json.loads(client.ledger.read_text())["requests"]
    assert rows[0] == original
    assert sum(row["accounted_usd"] for row in rows) == pytest.approx(hosted.RESERVATION + 0.01)
    with pytest.raises(RuntimeError, match="already been consumed"):
        client.request(body(), tag="reuse", replay=False, retry_failed_index=0, retry_reason="Investigated")
    mock.assert_called_once()


@pytest.mark.parametrize("replay", [True, False])
def test_failed_http500_stays_blocked_by_default(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch, *, replay: bool
) -> None:
    failed_retry_entry(client)
    before = client.ledger.read_bytes()
    mock = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    with pytest.raises(RuntimeError, match="previous identical call failed"):
        client.request(body(), tag="default", replay=replay)
    assert client.ledger.read_bytes() == before
    mock.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        {"error": "HTTP 429"},
        {"error": "HTTP 401"},
        {"error": "HTTP 400"},
        {"error": "TimeoutError"},
        {"request_sha256": "different"},
        {"response_file": None},
        {"index": 3},
        {"gateway": "vercel"},
    ],
)
def test_retry_refuses_ineligible_failure(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch, change: dict[str, Any]
) -> None:
    entry = failed_retry_entry(client)
    entry.update(change)
    hosted.checkpoint(client.ledger, {"requests": [entry]})
    before = client.ledger.read_bytes()
    mock = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    with pytest.raises(RuntimeError, match="same response-free HTTP 5xx"):
        client.request(body(), tag="bad", retry_failed_index=0, retry_reason="Investigated")
    assert client.ledger.read_bytes() == before
    mock.assert_not_called()


@pytest.mark.parametrize(
    ("index", "reason"),
    [
        (None, "Reason"),
        (0, None),
        (-1, "Reason"),
        (True, "Reason"),
        (0, " "),
        (0, "x" * 241),
        (0, "line\nbreak"),
        (0, "fake-test-key-only"),
    ],
)
def test_retry_refuses_unsafe_or_incomplete_approval(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch, index: int | None, reason: str | None
) -> None:
    mock = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    with pytest.raises(ValueError, match="safe nonempty reason"):
        client.request(body(), tag="bad", retry_failed_index=index, retry_reason=reason)
    mock.assert_not_called()
    assert not client.ledger.exists()


@pytest.mark.parametrize("limit", ["CAMPAIGN_LIMIT", "TOTAL_LIMIT"])
def test_retry_preserves_history_and_requires_fresh_budget(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    failed_retry_entry(client)
    before = client.ledger.read_bytes()
    monkeypatch.setattr(hosted, limit, hosted.RESERVATION + 0.1)
    mock = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    with pytest.raises(RuntimeError, match="authorized spend"):
        client.request(body(), tag="over-cap", retry_failed_index=0, retry_reason="Investigated")
    mock.assert_not_called()
    assert client.ledger.read_bytes() == before


def test_retry_cannot_bypass_another_matching_failure(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = failed_retry_entry(client)
    hosted.checkpoint(client.ledger, {"requests": [first, {**first, "index": 1}]})
    mock = MagicMock()
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    with pytest.raises(RuntimeError, match="previous identical call failed"):
        client.request(body(), tag="other-failure", retry_failed_index=0, retry_reason="Investigated")
    mock.assert_not_called()


def test_failed_replacement_also_consumes_retry_approval(
    client: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = failed_retry_entry(client)
    mock = MagicMock(side_effect=urllib.error.HTTPError("https://openrouter.ai", 503, "failure", Message(), None))
    monkeypatch.setattr(hosted.urllib.request, "urlopen", mock)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        client.request(body(), tag="replacement", retry_failed_index=0, retry_reason="Investigated")
    with pytest.raises(RuntimeError, match="already been consumed"):
        client.request(body(), tag="reuse", retry_failed_index=0, retry_reason="Investigated")
    rows = json.loads(client.ledger.read_text())["requests"]
    assert rows[0] == original
    assert sum(row["accounted_usd"] for row in rows) == pytest.approx(2 * hosted.RESERVATION)
    mock.assert_called_once()
