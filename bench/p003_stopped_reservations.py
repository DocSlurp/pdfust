"""Release concurrency slots only for proved-dead queue arms; preserve all money."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from bench.decision_hosted import checkpoint, exclusive_lock
from bench.silver import guard_path, sha, write_json


def group_dead(pid: int) -> bool:
    """Require the complete worker process group to be gone, without signaling it."""
    if type(pid) is not int or pid <= 1:
        raise ValueError("Expected a recorded worker process group")
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def reconcile(queue: Path, ledger_path: Path, audit: Path) -> dict[str, Any]:  # noqa: C901 - explicit postmortem gates.
    """Mark dead transports interrupted under the shared lock; never estimate their cost."""
    queue, ledger_path, audit = map(guard_path, (queue, ledger_path, audit))
    if audit.exists():
        raise FileExistsError("Prior interruption audit must not be overwritten")
    status_path = queue / "status.json"
    raw_status = status_path.read_bytes()
    status = json.loads(raw_status)
    dead = {}
    for arm in status["arms"]:
        if arm.get("status") not in {"failed", "interrupted"} or not arm.get("interrupted"):
            continue
        name = arm["name"]
        if not isinstance(name, str) or Path(name).name != name or name in {".", ".."}:
            raise ValueError("Unsafe recorded arm name")
        if group_dead(arm["pid"]):
            dead[f"P003/{name}/"] = {"name": name, "pid": arm["pid"], "reason": arm["interrupted"]}
    events = []
    if dead:
        with exclusive_lock(ledger_path.parent / "ledger.lock"):
            original_bytes = ledger_path.read_bytes()
            ledger = json.loads(original_bytes)
            for entry in ledger["requests"]:
                matches = [v for prefix, v in dead.items() if entry.get("tag", "").startswith(prefix)]
                if not matches or entry.get("concurrent_state") != "in_flight":
                    continue
                if len(matches) != 1 or not group_dead(matches[0]["pid"]):
                    raise ValueError("Stopped arm identity changed during reconciliation")
                before = dict(entry)
                entry.update(concurrent_state="interrupted", error="Owned queue arm ended before settlement")
                entry["interruption_provenance"] = {
                    **matches[0], "timestamp": time.time(), "queue_status_sha256": sha(raw_status),
                    "amount_unchanged": True, "automatic_retry": False,
                }
                if (entry["accounted_usd"], entry["cost_status"]) != (before["accounted_usd"], before["cost_status"]):
                    raise ValueError("Slot release must preserve every financial field")
                events.append({"before": before, "after": dict(entry)})
            if events:
                write_json(audit, {"ledger_before_sha256": sha(original_bytes), "events": events,
                                   "scope": "Dead-arm transport slots only; all charges/reservations retained"})
                checkpoint(ledger_path, ledger)
    return {"events": len(events), "proved_dead_arms": list(dead.values()), "money_released": False}


def main() -> None:
    """Root-only local postmortem bookkeeping; no credentials or network requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    if guard_path(args.audit).exists():
        parser.error("Use a fresh audit path; prior interruption receipts are immutable")
    print(json.dumps(reconcile(args.queue, args.ledger, args.audit)))


if __name__ == "__main__":
    main()
