"""Synthetic local ledger checks; no credentials, process signals or paid calls."""

import json

from bench import p003_stopped_reservations as stopped


def test_dead_arm_releases_only_slot_and_preserves_live_reservations(tmp_path, monkeypatch):  # noqa: ANN001, ANN201
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "status.json").write_text(json.dumps({"arms": [
        {"name": "dead", "pid": 200, "status": "failed", "interrupted": "wall_limit"},
        {"name": "live", "pid": 201, "status": "running"},
    ]}))
    entries = [
        {"index": i, "tag": "P003/" + name + "/page/0", "concurrent_state": "in_flight",
         "accounted_usd": .3, "cost_status": "reserved", "reservation_uuid": str(i)}
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
