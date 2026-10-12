"""Independent teardown backstop for pdfust Vast instances.

A systemd user timer runs ``tick`` every two minutes. Each armed state file
lists the instance IDs this project created. Ticks destroy them after the hard
deadline, or once GPU utilization has stayed below the idle threshold for the
idle window after a startup grace period. Instances not listed are never
touched. The API key is read as data from the configured env file and never
logged.

    python -m bench.vast_watchdog arm --state S --env-file F --deadline ISO
    python -m bench.vast_watchdog own --state S --instance ID
    python -m bench.vast_watchdog tick --state S
    python -m bench.vast_watchdog disarm --state S
"""

# ruff: noqa: EM101, TRY003, PLR2004, C901, PLR0913
from __future__ import annotations

import argparse
import datetime as dt
import json
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

API = "https://console.vast.ai/api"
SCHEMA = "jev-pdf-vast-watchdog@v1"
Fetch = Callable[[str, str], tuple[int, Any]]


def read_key(env_file: Path) -> str:
    """Return VAST_API_KEY from an env file parsed as data, never sourced."""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, _, value = line.partition("=")
        if name.strip() in {"VAST_API_KEY", "VAST_AI_API_KEY"} and value.strip():
            return value.strip().strip('"').strip("'")
    raise RuntimeError("No Vast API key in the configured env file")


def http_fetch(key: str) -> Fetch:
    """Return an authenticated JSON fetch yielding (status, body)."""

    def fetch(method: str, path: str) -> tuple[int, Any]:
        request = urllib.request.Request(  # noqa: S310 - fixed https API origin.
            API + path, method=method, headers={"Authorization": f"Bearer {key}", "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                raw = response.read()
                return response.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            return error.code, {}

    return fetch


def load(path: Path) -> dict[str, Any]:
    """Read one watchdog state file."""
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, state: dict[str, Any]) -> None:
    """Atomically replace the state file with owner-only permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as handle:
        json.dump(state, handle, indent=1)
        temporary = Path(handle.name)
    temporary.chmod(0o600)
    temporary.replace(path)


def arm(path: Path, env_file: Path, deadline: str, *, idle_minutes: float = 15, grace_minutes: float = 25,
        idle_gpu_percent: float = 5) -> dict[str, Any]:
    """Create an armed state with a future hard deadline."""
    when = dt.datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    if when.timestamp() <= time.time():
        raise ValueError("Deadline must be in the future")
    read_key(env_file)
    state = {
        "schema": SCHEMA, "armed": True, "env_file": str(env_file.resolve()), "deadline": when.isoformat(),
        "armed_at": dt.datetime.now(dt.UTC).isoformat(), "idle_minutes": idle_minutes,
        "grace_minutes": grace_minutes, "idle_gpu_percent": idle_gpu_percent,
        "owned": {}, "destroyed": [], "log": [],
    }
    save(path, state)
    return state


def own(path: Path, instance: int) -> dict[str, Any]:
    """Record a created instance; its idle clock starts after the grace period."""
    state = load(path)
    state["owned"][str(instance)] = {"since": time.time(), "idle_since": None}
    save(path, state)
    return state


def tick(path: Path, *, fetch: Fetch | None = None, now: float | None = None) -> dict[str, Any]:
    """Destroy owned instances past the deadline or idle beyond the window."""
    state = load(path)
    if not state.get("armed") or not state["owned"]:
        return {"action": "waiting", "owned": list(state.get("owned", {}))}
    now = time.time() if now is None else now
    fetch = fetch or http_fetch(read_key(Path(state["env_file"])))
    expired = now >= dt.datetime.fromisoformat(state["deadline"]).timestamp()
    actions = []
    for instance, record in list(state["owned"].items()):
        reason = "deadline" if expired else None
        if reason is None:
            status, body = fetch("GET", f"/v0/instances/{instance}/")
            info = body.get("instances", body) if isinstance(body, dict) else {}
            if status == 404 or info is None or (
                isinstance(info, dict) and info.get("actual_status") in {"exited", "offline"}
                and now - record["since"] > state["grace_minutes"] * 60
            ):
                reason = "not_running"
            elif isinstance(info, dict) and now - record["since"] > state["grace_minutes"] * 60:
                utilization = info.get("gpu_util")
                if isinstance(utilization, (int, float)) and utilization < state["idle_gpu_percent"]:
                    record["idle_since"] = record["idle_since"] or now
                    if now - record["idle_since"] >= state["idle_minutes"] * 60:
                        reason = "idle"
                else:
                    record["idle_since"] = None
        if reason is None:
            continue
        status, _ = fetch("DELETE", f"/v0/instances/{instance}/")
        if status in {200, 404}:
            del state["owned"][instance]
            state["destroyed"].append({"instance": int(instance), "reason": reason, "at": now})
        actions.append({"instance": instance, "reason": reason, "status": status})
    state["last_tick"] = now
    if actions:
        state["log"].append({"at": now, "actions": actions})
    save(path, state)
    return {"action": "tick", "actions": actions, "owned": list(state["owned"])}


def disarm(path: Path) -> dict[str, Any]:
    """Stop enforcement after verified manual teardown."""
    state = load(path)
    state["armed"] = False
    save(path, state)
    return state


def main() -> None:
    """Dispatch one watchdog command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["arm", "own", "tick", "disarm"])
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--deadline")
    parser.add_argument("--instance", type=int)
    parser.add_argument("--idle-minutes", type=float, default=15)
    args = parser.parse_args()
    if args.command == "arm":
        result = arm(args.state, args.env_file, args.deadline, idle_minutes=args.idle_minutes)
        result = {k: v for k, v in result.items() if k != "env_file"}
    elif args.command == "own":
        result = own(args.state, args.instance)
    elif args.command == "tick":
        result = tick(args.state)
    else:
        result = disarm(args.state)
    print(json.dumps({k: v for k, v in result.items() if k != "log"}, default=str))


if __name__ == "__main__":
    main()
