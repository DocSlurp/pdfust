"""Mocked concurrent ledger races; no credentials or network access."""

from __future__ import annotations

import io
import json
import threading
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from email.message import Message
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from bench import decision_hosted as hosted
from bench.decision_concurrent import ConcurrentDecisionClient


@pytest.fixture(autouse=True)
def _admission_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep P003 admission open so these mocks do not expire with the real deadlines."""
    from bench import research_policy  # noqa: PLC0415

    monkeypatch.setattr(research_policy, "P003_PAID_CUTOFF", float("inf"))
    monkeypatch.setattr(research_policy, "P003_EXTENSION_CUTOFF", float("inf"))


@pytest.fixture
def base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> hosted.DecisionClient:
    client = hosted.DecisionClient.__new__(hosted.DecisionClient)
    client.root = tmp_path
    client.directory = tmp_path / "artifacts"
    client.directory.mkdir()
    client.ledger = client.directory / "ledger.json"
    client.key = "fake-key-no-credential-file"
    monkeypatch.setattr(client, "_prior_api_cost", lambda: 0)
    monkeypatch.setattr(client, "_telemetry", lambda _body, _result, _entry: {"status": "disabled"})
    return client


def body(name: str = "a") -> dict[str, Any]:
    return {"model": hosted.JEV, "state": name, "questions": {}}


def payload(cost: object = 0.01) -> bytes:
    return json.dumps({"model": "served", "provider": "mock", "id": "fake-id", "usage": {"cost": cost}}).encode()


def response(data: bytes) -> MagicMock:
    mock = MagicMock()
    mock.__enter__.return_value.read.side_effect = lambda size: data[:size]
    return mock


def ledger(client: hosted.DecisionClient) -> dict[str, Any]:
    return json.loads(client.ledger.read_text())


def test_reserves_before_http_and_reuses_accounting_and_telemetry(
    base: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    telemetry = MagicMock(return_value={"status": "exported", "trace_id": "mock"})
    monkeypatch.setattr(base, "_telemetry", telemetry)

    def opener(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401
        rows = ledger(base)["requests"]
        assert rows[0]["concurrent_state"] == "in_flight"
        assert rows[0]["accounted_usd"] == 0.3
        assert (base.directory / "request-000.json").read_bytes() == request.data
        assert request.get_header("Authorization") == "Bearer fake-key-no-credential-file"
        assert timeout == 90
        return response(payload())

    client = ConcurrentDecisionClient(base, opener=opener)
    out = client.request(body(), tag="P002/a")
    assert out["replayed"] is False
    assert out["entry"]["accounted_usd"] == 0.01
    assert out["entry"]["concurrent_state"] == "completed"
    assert out["entry"]["telemetry"]["status"] == "exported"
    assert (base.directory / out["entry"]["response_file"]).read_bytes() == payload()
    assert telemetry.call_count == 1
    assert "fake-key" not in base.ledger.read_text()


def test_ten_root_clients_wait_without_oversubscribing_eight_paid_reservations(
    base: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bench import research_policy  # noqa: PLC0415
    from bench.p003_client import P003ConcurrentClient  # noqa: PLC0415

    monkeypatch.setenv("JEV_P003_TRANSPORT_SLOTS", "8")
    monkeypatch.setattr(research_policy, "P003_PAID_CUTOFF", float("inf"))
    lock = threading.Lock()
    active = peak = 0

    def opener(_request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401, ARG001
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
            assert sum(r.get("concurrent_state") == "in_flight" for r in ledger(base)["requests"]) <= 8
        time.sleep(0.15)
        with lock:
            active -= 1
        return response(payload())

    clients = [P003ConcurrentClient(client=base, opener=opener) for _ in range(10)]
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [
            pool.submit(client.request, body(str(i)), tag=f"P003/slot-test-{i}") for i, client in enumerate(clients)
        ]
        results = [future.result(timeout=10) for future in futures]
    rows = ledger(base)["requests"]
    assert peak == 8
    assert active == 0
    assert len(rows) == 10
    assert all(r["concurrent_state"] == "completed" for r in rows)
    assert sum(r["accounted_usd"] for r in rows) == pytest.approx(0.10)
    assert all(r["transport_admission"]["slots"] == 8 for r in results)
    assert any(r["transport_admission"]["wait_seconds"] > 0.1 for r in results)


def test_two_http_requests_can_overlap_and_wave_cap_cannot_oversubscribe(base: hosted.DecisionClient) -> None:
    both_http = threading.Barrier(3)
    finish = threading.Event()

    def opener(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401, ARG001
        both_http.wait(timeout=5)
        assert finish.wait(timeout=5)
        return response(payload())

    client = ConcurrentDecisionClient(base, max_inflight=3, wave_limits={"P002": 0.6}, opener=opener)
    with ThreadPoolExecutor(max_workers=3) as pool:
        first = pool.submit(client.request, body("a"), tag="P002/a")
        second = pool.submit(client.request, body("b"), tag="P002/b")
        both_http.wait(timeout=5)
        assert len(ledger(base)["requests"]) == 2
        try:
            with pytest.raises(RuntimeError, match="wave cap"):
                client.request(body("c"), tag="P002/c")
        finally:
            finish.set()
        assert first.result(timeout=5)["entry"]["index"] != second.result(timeout=5)["entry"]["index"]
    assert len(ledger(base)["requests"]) == 2


@pytest.mark.parametrize("cap", ["campaign_limit_usd", "authorized_total_usd"])
def test_cumulative_and_campaign_caps_include_inflight_reserves(base: hosted.DecisionClient, cap: str) -> None:
    initial = {"requests": [], cap: 0.6 if cap == "campaign_limit_usd" else hosted.PRIOR_RENTAL + 0.6}
    hosted.checkpoint(base.ledger, initial)
    entered = threading.Event()
    release = threading.Event()

    def opener(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401, ARG001
        entered.set()
        assert release.wait(timeout=5)
        return response(payload())

    client = ConcurrentDecisionClient(base, opener=opener)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(client.request, body(), tag="P002/a", reservation_usd=0.6)
        assert entered.wait(timeout=5)
        try:
            with pytest.raises(RuntimeError, match="cumulative or wave cap"):
                client.request(body("b"), tag="P002/b")
        finally:
            release.set()
        pending.result(timeout=5)
    assert len(ledger(base)["requests"]) == 1


def test_duplicate_inflight_never_transmits_twice(base: hosted.DecisionClient) -> None:
    entered = threading.Event()
    release = threading.Event()
    transmissions = []

    def opener(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401, ARG001
        transmissions.append(request)
        entered.set()
        assert release.wait(timeout=5)
        return response(payload())

    client = ConcurrentDecisionClient(base, opener=opener)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(client.request, body(), tag="P002/a")
        assert entered.wait(timeout=5)
        try:
            with pytest.raises(RuntimeError, match="Identical request"):
                client.request(body(), tag="P002/b")
        finally:
            release.set()
        first.result(timeout=5)
    assert len(transmissions) == 1


def test_out_of_order_settlement_reloads_without_stale_overwrite(base: hosted.DecisionClient) -> None:
    entered = {"a": threading.Event(), "b": threading.Event()}
    release = {"a": threading.Event(), "b": threading.Event()}

    def opener(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401, ARG001
        name = json.loads(request.data)["state"]
        entered[name].set()
        assert release[name].wait(timeout=5)
        return response(payload(0.01 if name == "a" else 0.02))

    client = ConcurrentDecisionClient(base, opener=opener)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(client.request, body("a"), tag="P002/a")
        assert entered["a"].wait(timeout=5)
        b = pool.submit(client.request, body("b"), tag="P002/b")
        assert entered["b"].wait(timeout=5)
        try:
            release["b"].set()
            assert b.result(timeout=5)["entry"]["accounted_usd"] == 0.02
            with hosted.exclusive_lock(base.directory / "ledger.lock"):
                current = ledger(base)
                current["requests"][0]["coordinator_note"] = "must survive"
                current["requests"].append({"index": 2, "tag": "P001/other", "accounted_usd": 0.05})
                hosted.checkpoint(base.ledger, current)
        finally:
            release["a"].set()
        assert a.result(timeout=5)["entry"]["coordinator_note"] == "must survive"
    rows = ledger(base)["requests"]
    assert len(rows) == 3
    assert [r["accounted_usd"] for r in rows] == [0.01, 0.02, 0.05]


def test_failed_settlement_retains_reservation_and_raw_response_and_blocks_admission(
    base: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = hosted.checkpoint

    def fail_settlement(path: Path, value: dict[str, Any]) -> None:
        if value["requests"][-1]["concurrent_state"] != "in_flight":
            message = "fake disk failure"
            raise OSError(message)
        original(path, value)

    monkeypatch.setattr(hosted, "checkpoint", fail_settlement)
    opener = MagicMock(return_value=response(payload(0.01)))
    client = ConcurrentDecisionClient(base, opener=opener)
    with pytest.raises(RuntimeError, match="Settlement failed"):
        client.request(body(), tag="P002/a")
    row = ledger(base)["requests"][0]
    assert row["accounted_usd"] == 0.3
    assert row["concurrent_state"] == "in_flight"
    assert (base.directory / "response-000.json").read_bytes() == payload(0.01)
    with pytest.raises(RuntimeError, match="awaits settlement"):
        client.request(body("b"), tag="P002/b")
    assert opener.call_count == 1


@pytest.mark.parametrize("cost", [0, None])
def test_unknown_cost_preserves_reserve_and_reported_zero(base: hosted.DecisionClient, cost: object) -> None:
    client = ConcurrentDecisionClient(base, opener=lambda *_args, **_kwargs: response(payload(cost)))
    out = client.request(body(), tag="P002/a")
    assert out["entry"]["accounted_usd"] == 0.3
    assert out["entry"]["cost_status"] == "reserved"
    if cost == 0:
        assert out["entry"]["provider_reported_usd"] == 0
    else:
        assert "provider_reported_usd" not in out["entry"]


def test_catalog_estimate_preserves_reported_zero(base: hosted.DecisionClient) -> None:
    catalog = base.directory / "langfuse/catalog-prices.json"
    catalog.parent.mkdir()
    catalog.write_text(
        json.dumps({"fetched_at": "offline-test", "prices": {hosted.JEV: {"input": 0.001, "output": 0.002}}})
    )
    raw = json.dumps({"usage": {"cost": 0, "prompt_tokens": 10, "completion_tokens": 20}}).encode()
    out = ConcurrentDecisionClient(base, opener=lambda *_args, **_kwargs: response(raw)).request(body(), tag="P002/a")
    assert out["entry"]["provider_reported_usd"] == 0
    assert out["entry"]["accounted_usd"] == pytest.approx(0.05)
    assert out["entry"]["cost_status"] == "catalog estimate"


def test_failed_http_retains_reserve_and_sanitized_diagnostic(base: hosted.DecisionClient) -> None:
    opener = MagicMock(
        side_effect=urllib.error.HTTPError(
            "mock", 503, "fake-key-no-credential-file", Message(), io.BytesIO(b'{"error":{"code":503}}')
        )
    )
    client = ConcurrentDecisionClient(base, opener=opener)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        client.request(body(), tag="P002/a")
    row = ledger(base)["requests"][0]
    assert row["accounted_usd"] == 0.3
    assert row["concurrent_state"] == "failed"
    assert "fake-key" not in base.ledger.read_text()
    with pytest.raises(RuntimeError, match="failed or unresolved"):
        client.request(body(), tag="P002/b")
    assert opener.call_count == 1


def test_malformed_response_is_raw_retained_with_unknown_reserve(base: hosted.DecisionClient) -> None:
    client = ConcurrentDecisionClient(base, opener=lambda *_args, **_kwargs: response(b"not JSON"))
    with pytest.raises(RuntimeError, match="JSONDecodeError"):
        client.request(body(), tag="P002/a")
    row = ledger(base)["requests"][0]
    assert row["accounted_usd"] == 0.3
    assert (base.directory / row["response_file"]).read_bytes() == b"not JSON"


def test_reservation_overrun_blocks_future_admission(base: hosted.DecisionClient) -> None:
    opener = MagicMock(return_value=response(payload(0.4)))
    client = ConcurrentDecisionClient(base, opener=opener)
    out = client.request(body(), tag="P002/a")
    assert out["entry"]["accounted_usd"] == 0.4
    assert out["entry"]["reservation_exceeded"] is True
    with pytest.raises(RuntimeError, match="blocked after reservation overrun"):
        client.request(body("b"), tag="P002/b")
    assert opener.call_count == 1


def test_fresh_identical_completed_request_is_a_new_transmission(base: hosted.DecisionClient) -> None:
    opener = MagicMock(return_value=response(payload()))
    client = ConcurrentDecisionClient(base, opener=opener)
    first = client.request(body(), tag="P002/a")
    second = client.request(body(), tag="P002/b")
    assert first["entry"]["reservation_uuid"] != second["entry"]["reservation_uuid"]
    assert opener.call_count == 2
    for kwargs in ({"replay": True}, {"retry_failed_index": 0}, {"retry_reason": "retry"}):
        with pytest.raises(ValueError, match="fresh-only"):
            client.request(body(), tag="P002/c", **kwargs)


def test_persistent_inflight_bound_and_policy_mismatch_are_fail_closed(base: hosted.DecisionClient) -> None:
    entered = threading.Event()
    release = threading.Event()

    def opener(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401, ARG001
        entered.set()
        assert release.wait(timeout=5)
        return response(payload())

    client = ConcurrentDecisionClient(base, max_inflight=1, opener=opener)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(client.request, body(), tag="P002/a")
        assert entered.wait(timeout=5)
        try:
            with pytest.raises(RuntimeError, match="in-flight limit"):
                client.request(body("b"), tag="P002/b")
            incompatible = ConcurrentDecisionClient(base, max_inflight=2, opener=opener)
            with pytest.raises(RuntimeError, match="policy differs"):
                incompatible.request(body("c"), tag="P002/c")
        finally:
            release.set()
        pending.result(timeout=5)


def test_telemetry_failure_never_retransmits_and_preserves_priced_charge(
    base: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(base, "_telemetry", MagicMock(side_effect=RuntimeError("fake optional telemetry failure")))
    opener = MagicMock(return_value=response(payload(0.02)))
    out = ConcurrentDecisionClient(base, opener=opener).request(body(), tag="P002/a")
    assert out["entry"]["accounted_usd"] == 0.02
    assert out["entry"]["telemetry"] == {"status": "error", "error": "RuntimeError"}
    assert opener.call_count == 1


def test_oversized_response_keeps_bounded_prefix_and_reservation(
    base: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(hosted, "MAX_RESPONSE_BYTES", 20)
    opener = MagicMock(return_value=response(b"x" * 100))
    client = ConcurrentDecisionClient(base, opener=opener)
    with pytest.raises(RuntimeError, match="ValueError"):
        client.request(body(), tag="P002/a")
    row = ledger(base)["requests"][0]
    assert row["response_truncated"] is True
    assert (base.directory / row["response_prefix_file"]).read_bytes() == b"x" * 21
    assert row["accounted_usd"] == 0.3
    assert opener.call_count == 1


def test_external_financial_change_is_not_overwritten_by_settlement(base: hosted.DecisionClient) -> None:
    def opener(request: Any, *, timeout: int) -> MagicMock:  # noqa: ANN401, ARG001
        with hosted.exclusive_lock(base.directory / "ledger.lock"):
            current = ledger(base)
            current["requests"][0]["accounted_usd"] = 0.2
            hosted.checkpoint(base.ledger, current)
        return response(payload(0.01))

    client = ConcurrentDecisionClient(base, opener=opener)
    with pytest.raises(RuntimeError, match="Settlement failed"):
        client.request(body(), tag="P002/a")
    assert ledger(base)["requests"][0]["accounted_usd"] == 0.2
    with pytest.raises(RuntimeError, match="awaits settlement"):
        client.request(body("b"), tag="P002/b")


def test_queued_four_worker_requests_have_no_transient_admission_failure(base: hosted.DecisionClient) -> None:
    client = ConcurrentDecisionClient(base, max_inflight=4, opener=lambda *_args, **_kwargs: response(payload()))
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(client.request, body(str(i)), tag=f"P002/page-{i}") for i in range(24)]
        results = [future.result(timeout=10) for future in futures]
    assert len({out["entry"]["reservation_uuid"] for out in results}) == 24
    assert all(row["concurrent_state"] == "completed" for row in ledger(base)["requests"])
    assert sum(row["accounted_usd"] for row in ledger(base)["requests"]) == pytest.approx(0.24)


def test_telemetry_runs_outside_lock_after_financial_settlement(
    base: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    telemetry_entered = threading.Event()
    release = threading.Event()

    def telemetry(_body: Any, _result: Any, entry: Any) -> dict[str, str]:  # noqa: ANN401
        if entry["index"] == 0:
            telemetry_entered.set()
            assert release.wait(timeout=5)
        return {"status": "disabled"}

    monkeypatch.setattr(base, "_telemetry", telemetry)
    client = ConcurrentDecisionClient(base, max_inflight=1, opener=lambda *_args, **_kwargs: response(payload()))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(client.request, body("a"), tag="P002/a")
        assert telemetry_entered.wait(timeout=5)
        try:
            second = pool.submit(client.request, body("b"), tag="P002/b")
            assert second.result(timeout=5)["entry"]["index"] == 1
        finally:
            release.set()
        assert first.result(timeout=5)["entry"]["index"] == 0
    assert all(row["accounted_usd"] == 0.01 for row in ledger(base)["requests"])


def test_telemetry_checkpoint_failure_keeps_financial_settlement(
    base: hosted.DecisionClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkpoint = hosted.checkpoint

    def reject_annotation(path: Path, value: dict[str, Any]) -> None:
        if any("telemetry" in row for row in value["requests"]):
            raise OSError("mock annotation IO failure")  # noqa: EM101, TRY003
        checkpoint(path, value)

    monkeypatch.setattr(hosted, "checkpoint", reject_annotation)
    opener = MagicMock(side_effect=lambda *_args, **_kwargs: response(payload()))
    client = ConcurrentDecisionClient(base, opener=opener)
    with pytest.raises(RuntimeError, match="Telemetry checkpoint failed"):
        client.request(body(), tag="P002/a")
    row = ledger(base)["requests"][0]
    assert row["accounted_usd"] == 0.01
    assert row["concurrent_state"] == "completed"
    assert (base.directory / row["response_file"]).read_bytes() == payload()
    assert opener.call_count == 1


def test_explicit_p003_matched_inflight_replicates(base: hosted.DecisionClient) -> None:
    """Same model inputs may overlap only for explicitly distinct P003 tags."""
    client = ConcurrentDecisionClient(base, max_inflight=3, wave_limits={"P003": 50}, allow_matched_replicates=True)
    encoded = json.dumps(body(), separators=(",", ":")).encode()
    first = client._reserve(body(), encoded, "P003/arm-a/page", 0.3)  # noqa: SLF001
    second = client._reserve(body(), encoded, "P003/arm-b/page", 0.3)  # noqa: SLF001
    assert first["index"] != second["index"]
    assert sum(row["accounted_usd"] for row in ledger(base)["requests"]) == 0.6
    with pytest.raises(RuntimeError, match="tag already"):
        client._reserve(body(), encoded, "P003/arm-a/page", 0.3)  # noqa: SLF001
    saved = ledger(base)
    saved["requests"][0].update(concurrent_state="failed", error="OSError")
    base.ledger.write_text(json.dumps(saved))
    with pytest.raises(RuntimeError, match="failed or unresolved"):
        client._reserve(body(), encoded, "P003/arm-c/page", 0.3)  # noqa: SLF001


def test_default_matched_inflight_still_refused(base: hosted.DecisionClient) -> None:
    client = ConcurrentDecisionClient(base, wave_limits={"P003": 50})
    encoded = json.dumps(body(), separators=(",", ":")).encode()
    client._reserve(body(), encoded, "P003/a", 0.3)  # noqa: SLF001
    with pytest.raises(RuntimeError, match="in flight"):
        client._reserve(body(), encoded, "P003/b", 0.3)  # noqa: SLF001


def test_matched_policy_cannot_admit_other_waves(base: hosted.DecisionClient) -> None:
    with pytest.raises(ValueError, match="P003-only"):
        ConcurrentDecisionClient(base, allow_matched_replicates=True)
    with pytest.raises(ValueError, match="P003-only"):
        ConcurrentDecisionClient(base, wave_limits={"P002": 50}, allow_matched_replicates=True)


def test_interrupted_reservation_frees_slot_keeps_charge_and_allows_named_rerun(
    base: hosted.DecisionClient,
) -> None:
    client = ConcurrentDecisionClient(
        base, max_inflight=1, opener=lambda request, *, timeout: response(payload()),  # noqa: ARG005
        wave_limits={"P003": 50.0}, allow_matched_replicates=True,
    )
    # Simulate a process killed between reservation and settlement.
    encoded = json.dumps(body(), separators=(",", ":")).encode()
    reservation = client._reserve(body(), encoded, "P003/extension-v1-a/q", 0.3)  # noqa: SLF001
    with pytest.raises(RuntimeError, match="in-flight limit"):
        client.request(body("other"), tag="P003/extension-v1-b/q")
    with pytest.raises(ValueError, match="investigated reason"):
        client.reconcile_interrupted(reservation["index"], " ")
    marked = client.reconcile_interrupted(reservation["index"], "host reboot")
    assert marked["concurrent_state"] == "interrupted"
    assert marked["cost_status"] == "reserved"
    assert marked["accounted_usd"] == 0.3
    with pytest.raises(RuntimeError, match="unsettled in-flight"):
        client.reconcile_interrupted(reservation["index"], "again")
    ok = ConcurrentDecisionClient(
        base, max_inflight=1, opener=lambda request, *, timeout: response(payload()),  # noqa: ARG005
        wave_limits={"P003": 50.0}, allow_matched_replicates=True,
    )
    ok.request(body(), tag="P003/extension-v1-a-r2/q")
    rows = ledger(base)["requests"]
    assert rows[0]["accounted_usd"] == 0.3
    assert rows[1]["concurrent_state"] == "completed"
