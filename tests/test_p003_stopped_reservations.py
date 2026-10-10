"""Synthetic local ledger checks; no credentials, process signals or paid calls."""

import json
from pathlib import Path

import pytest
from bench import p003_stopped_reservations as stopped


def test_dead_arm_releases_only_slot_and_preserves_live_reservations(tmp_path, monkeypatch):  # noqa: ANN001, ANN201
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "status.json").write_text(json.dumps({"arms": [
        {"name": "dead", "pid": 200, "status": "failed", "interrupted": "wall_limit",
         "started_at": 100, "wall_seconds": 10},
        {"name": "live", "pid": 201, "status": "running"},
    ]}))
    entries = [
        {"index": i, "tag": "P003/" + name + "/page/0", "concurrent_state": "in_flight",
         "accounted_usd": .3, "cost_status": "reserved", "reservation_uuid": str(i), "started_at": 105}
        for i, name in enumerate(("dead", "live", "dead-other"))
    ]
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"requests": entries, "concurrent_policy": {"max_inflight": 3}}))
    monkeypatch.setattr(stopped, "group_dead", lambda pid: pid == 200)
    result = stopped.reconcile(queue, ledger, tmp_path / "audit.json")
    saved = json.loads(ledger.read_bytes())
    assert result["events"] == 1
    assert result["money_released"] is False
    assert saved["requests"][0]["concurrent_state"] == "interrupted"
    assert saved["requests"][0]["accounted_usd"] == .3
    assert saved["requests"][0]["cost_status"] == "reserved"
    assert saved["requests"][1:] == entries[1:]
    assert saved["concurrent_policy"] == {"max_inflight": 3}
    assert stopped.reconcile(queue, ledger, tmp_path / "audit2.json")["events"] == 0


def test_reported_interruption_with_live_process_group_is_untouched(tmp_path, monkeypatch):  # noqa: ANN001, ANN201
    (tmp_path / "status.json").write_text(json.dumps({"arms": [
        {"name": "still-live", "pid": 222, "status": "failed", "interrupted": "wall_limit"},
    ]}))
    monkeypatch.setattr(stopped, "group_dead", lambda _pid: False)
    result = stopped.reconcile(tmp_path, tmp_path / "absent-ledger.json", tmp_path / "audit.json")
    assert result["events"] == 0
    assert not (tmp_path / "audit.json").exists()


@pytest.mark.parametrize(("later_attempt", "raw_response"), [(True, False), (False, True)])
def test_later_same_name_attempt_and_retained_response_are_never_released(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, later_attempt: bool, raw_response: bool,
) -> None:
    (tmp_path / "status.json").write_text(json.dumps({"arms": [
        {"name": "same-name", "pid": 222, "status": "failed", "interrupted": "wall_limit",
         "started_at": 100, "wall_seconds": 10},
    ]}))
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"requests": [{
        "index": 0, "tag": "P003/same-name/page/0", "concurrent_state": "in_flight",
        "accounted_usd": .3, "cost_status": "reserved", "started_at": 2000 if later_attempt else 105,
    }]}))
    original = ledger.read_bytes()
    if raw_response:
        (tmp_path / "response-000.json").write_text('{"usage":{"cost":1.2}}')
    monkeypatch.setattr(stopped, "group_dead", lambda _pid: True)
    result = stopped.reconcile(tmp_path, ledger, tmp_path / "audit.json")
    assert result["events"] == 0
    assert len(result["blocked_entries"]) == 1
    assert ledger.read_bytes() == original
