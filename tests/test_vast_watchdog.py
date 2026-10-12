"""Offline checks for the Vast teardown watchdog; no network or credentials."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest
from bench import vast_watchdog as wd


def _armed(tmp_path: Path, minutes_ahead: float = 60) -> Path:
    env = tmp_path / "env"
    env.write_text("OTHER=1\nVAST_API_KEY=fake-key\n")
    state = tmp_path / "state.json"
    deadline = (dt.datetime.now(dt.UTC) + dt.timedelta(minutes=minutes_ahead)).isoformat()
    wd.arm(state, env, deadline, idle_minutes=15)
    return state


class FakeApi:
    """Record calls and report one fixed GPU utilization."""

    def __init__(self, utilization: float = 50.0) -> None:  # noqa: D107
        self.utilization = utilization
        self.calls: list[tuple[str, str]] = []

    def __call__(self, method: str, path: str) -> tuple[int, Any]:  # noqa: D102
        self.calls.append((method, path))
        if method == "GET":
            return 200, {"instances": {"actual_status": "running", "gpu_util": self.utilization}}
        return 200, {}


def test_key_is_read_as_data_and_required(tmp_path: Path) -> None:
    env = tmp_path / "env"
    env.write_text('VAST_API_KEY="abc"\n')
    assert wd.read_key(env) == "abc"
    env.write_text("NOTHING=1\n")
    with pytest.raises(RuntimeError):
        wd.read_key(env)


def test_deadline_destroys_only_owned_instances(tmp_path: Path) -> None:
    state = _armed(tmp_path)
    wd.own(state, 101)
    api = FakeApi()
    deadline = dt.datetime.fromisoformat(wd.load(state)["deadline"]).timestamp()
    result = wd.tick(state, fetch=api, now=deadline + 1)
    assert result["actions"] == [{"instance": "101", "reason": "deadline", "status": 200}]
    assert api.calls == [("DELETE", "/v0/instances/101/")]
    assert wd.load(state)["owned"] == {}


def test_idle_gpu_destroys_after_grace_and_window(tmp_path: Path) -> None:
    state = _armed(tmp_path, minutes_ahead=600)
    wd.own(state, 7)
    since = wd.load(state)["owned"]["7"]["since"]
    api = FakeApi(utilization=1.0)
    assert wd.tick(state, fetch=api, now=since + 10 * 60)["actions"] == []  # inside grace
    assert wd.tick(state, fetch=api, now=since + 26 * 60)["actions"] == []  # idle clock starts
    result = wd.tick(state, fetch=api, now=since + 42 * 60)
    assert result["actions"][0]["reason"] == "idle"


def test_busy_gpu_resets_idle_clock(tmp_path: Path) -> None:
    state = _armed(tmp_path, minutes_ahead=600)
    wd.own(state, 7)
    since = wd.load(state)["owned"]["7"]["since"]
    idle, busy = FakeApi(1.0), FakeApi(80.0)
    wd.tick(state, fetch=idle, now=since + 26 * 60)
    wd.tick(state, fetch=busy, now=since + 35 * 60)
    assert wd.tick(state, fetch=idle, now=since + 45 * 60)["actions"] == []


def test_disarmed_state_never_destroys(tmp_path: Path) -> None:
    state = _armed(tmp_path)
    wd.own(state, 5)
    wd.disarm(state)
    api = FakeApi()
    assert wd.tick(state, fetch=api, now=1e12)["action"] == "waiting"
    assert api.calls == []


def test_missing_instance_record_is_cleared(tmp_path: Path) -> None:
    state = _armed(tmp_path)
    wd.own(state, 9)
    calls: list[tuple[str, str]] = []

    def gone(method: str, path: str) -> tuple[int, Any]:
        calls.append((method, path))
        return 200, {"instances": None}

    result = wd.tick(state, fetch=gone)
    assert result["actions"] == [{"instance": "9", "reason": "not_running", "status": 200}]
    assert wd.load(state)["owned"] == {}
