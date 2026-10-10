"""Write coordinator-driven P003 checkpoints from authorized telemetry metadata."""

# Mixed experiment and ledger metadata retain unknown observations explicitly.
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import resource
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from bench.silver import guard_path

BASELINE = Decimal("44.9319455668")


def observed(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Capture content and its own file timestamp without reading request bodies."""
    with guard_path(path.resolve()).open("rb") as source:
        data = source.read()
        stamp = os.fstat(source.fileno()).st_mtime
    return json.loads(data), {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "observed_file_mtime_utc": datetime.fromtimestamp(stamp, UTC).isoformat(),
    }


def money(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Separate ledger-classified reported amounts, estimates and reservations."""
    amounts: dict[str, Decimal] = {}
    unknown = 0
    for row in rows:
        amount = row.get("accounted_usd")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
            unknown += 1
            continue
        category = row.get("cost_status", "unknown basis")
        amounts[category] = amounts.get(category, Decimal(0)) + Decimal(str(amount))
    reported = sum((v for k, v in amounts.items() if k.startswith("provider-reported")), Decimal(0))
    estimates = amounts.get("catalog estimate", Decimal(0))
    reserved = amounts.get("reserved", Decimal(0))
    total = sum(amounts.values(), Decimal(0))
    return {
        "attempts": len(rows),
        "states": dict(Counter(r.get("concurrent_state", "legacy") for r in rows)),
        "ledger_classified_reported_usd": str(reported),
        "catalog_estimated_usd": str(estimates),
        "unresolved_reserved_usd": str(reserved),
        "known_accounted_usd": str(total),
        "unknown_amount_entries": unknown,
        "cost_status_totals_usd": {k: str(v) for k, v in amounts.items()},
        "wave_remaining_usd": str(Decimal(50) - total) if not unknown else None,
        "prior_conservative_baseline_usd": str(BASELINE),
        "baseline_plus_wave_conservative_usd": str(BASELINE + total),
        "cumulative_remaining_usd": str(Decimal(200) - BASELINE - total) if not unknown else None,
        "basis": "Ledger accounted_usd grouped by its retained cost_status; reserved exposure is not billed cost",
    }


def checkpoint(status: Path, ledger: Path, output: Path, planned: list[str]) -> Path:
    """Read one snapshot and write immutable JSON/Markdown plus latest local views."""
    started, cpu = time.monotonic(), time.process_time()
    queue, queue_receipt = observed(status)
    book, ledger_receipt = observed(ledger)
    rows = [r for r in book["requests"] if r.get("tag", "").startswith("P003/")]
    states = Counter(a["status"] for a in queue["arms"])
    completed = [a for a in queue["arms"] if a["status"] == "completed"]
    required = len(queue["frozen_order"])
    evaluations = sum((status.parent / a["name"] / "evaluation.json").exists() for a in completed)
    costs = money(rows)
    plans = []
    for declaration in planned:
        name, count = declaration.rsplit("=", 1)
        plans.append(
            {"name": name, "required": int(count), "scope": "coordinator-declared plan; launch telemetry unavailable"}
        )
    now = datetime.now(UTC)
    snapshot = {
        "reported_at_utc": now.isoformat(),
        "coordinator_last_published_utc": None,
        "next_coordinator_publication_deadline_utc": (now + timedelta(minutes=5)).isoformat(),
        "sources": [queue_receipt, ledger_receipt],
        "roles": {
            "root": "coordination and new experiments",
            "catalog": "queues and baselines",
            "eval": "independent verification",
            "reporter": "progress and actual-input visuals",
        },
        "current_queue": {
            "required": required,
            "completed_jobs": len(completed),
            "running_jobs": states["running"],
            "queued_jobs": required - len(queue["arms"]),
            "failed_jobs": sum(v for k, v in states.items() if k not in {"completed", "running"}),
            "completed_with_evaluation_file": evaluations,
            "evaluation_scope": "presence only; freshness/quality verification belongs to evaluator",
            "attempted_pages_completed_jobs": sum(a.get("attempted_pages", 0) or 0 for a in completed),
            "operational_pages_completed_jobs": sum(a.get("completed_pages", 0) or 0 for a in completed),
            "running": [a["name"] for a in queue["arms"] if a["status"] == "running"],
        },
        "plans": plans,
        "costs": costs,
        "worker_resources": queue.get("resources"),
        "reporting_model_cost_usd": None,
        "reporting_model_cost_scope": "not exposed in authorized telemetry",
        "new_hosted_calls": 0,
        "paid_cutoff_utc": "2026-10-11T02:12:00Z",
        "wave_finish_utc": "2026-10-11T02:27:00Z",
        "eta": "Unknown: no aggregate queue rate; mixed arm kinds and individual time limits",
        "next": "Finish the active queue, independently verify outputs, root admits the next reviewed queue",
        "cadence": "Coordinator publishes within five minutes and on material changes; no autonomous timer",
    }
    q = snapshot["current_queue"]
    page_errors = q["attempted_pages_completed_jobs"] - q["operational_pages_completed_jobs"]
    display = {
        key: f"{Decimal(value):.10f}" if isinstance(value, str) and key.endswith("_usd") else value
        for key, value in costs.items()
    }
    text = f"""P003 checkpoint — {now:%Y-%m-%d %H:%M:%S UTC}

| Queue | Required | Completed jobs | Running | Queued | Job failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| {status.parent.name} | {required} | {len(completed)} | {states["running"]} | {q["queued_jobs"]} | {q["failed_jobs"]} |
"""
    for plan in plans:
        text += f"| {plan['name']} plan | {plan['required']} | Not launched/unknown | Unknown | Plan only | Unknown |\n"
    text += f"""
Completed-job evidence files: {evaluations}/{len(completed)}; presence does not certify freshness.
Completed jobs attempted {q["attempted_pages_completed_jobs"]} pages and retained
{q["operational_pages_completed_jobs"]} operational successes, with {page_errors}
non-success page outcomes. Operational success is separate from strict quality.

| P003 ledger category | USD |
| --- | ---: |
| Ledger-classified reported charges | {display["ledger_classified_reported_usd"]} |
| Catalog estimates | {display["catalog_estimated_usd"]} |
| Unresolved reserved exposure | {display["unresolved_reserved_usd"]} |
| Conservative known accounting | {display["known_accounted_usd"]} |
| Remaining from USD 50 wave ceiling | {display["wave_remaining_usd"]} |

Prior conservative baseline USD {BASELINE} stays separate. Baseline plus current
P003 accounting is USD {display["baseline_plus_wave_conservative_usd"]} against the
USD 200 cumulative ceiling; this is not a total of billed charges. Reporting model
cost is unknown; no additional hosted calls were made for this checkpoint.

Roles: root coordinates experiments; catalog prepares queues/baselines; eval
verifies independently; reporter maintains checkpoints and real-input visuals.

Next: {snapshot["next"]}. ETA: {snapshot["eta"]}.
Paid admissions stop at 02:12 UTC; reporting/validation ends at 02:27 UTC.
Coordinator-driven next publication is due within five minutes; no timer is claimed.

Sources observed from file timestamps: queue {queue_receipt["observed_file_mtime_utc"]};
ledger {ledger_receipt["observed_file_mtime_utc"]}. Worker CPU/RAM measurement is the
retained psutil 100 ms queue-plus-recursive-descendant sample, not reporter cost:
{json.dumps(queue.get("resources"), sort_keys=True)}.
"""
    output = guard_path(output.resolve())
    output.mkdir(parents=True, exist_ok=True)
    name = now.strftime("%Y%m%dT%H%M%S") + f"-{now.microsecond:06d}Z"
    snapshot["reporter_local_resources"] = {
        "wall_seconds": time.monotonic() - started,
        "cpu_seconds": time.process_time() - cpu,
        "lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "scope": "single CPU reporting process; getrusage lifetime peak; no sampling",
    }
    (output / (name + ".json")).write_text(json.dumps(snapshot, indent=2) + "\n")
    (output / (name + ".md")).write_text(text)
    (output / "latest.md").write_text(text)
    markup = (
        "<!doctype html><meta charset=utf-8><title>P003 progress</title>"
        "<style>body{font:16px sans-serif;max-width:1100px;margin:30px}"
        "pre{white-space:pre-wrap}</style><pre>" + html.escape(text) + "</pre>"
    )
    (output / "latest.html").write_text(markup)
    return output / (name + ".md")


def main() -> None:
    """Run one coordinator-triggered metadata checkpoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--planned", action="append", default=[])
    args = parser.parse_args()
    print(checkpoint(args.status, args.ledger, args.output, args.planned))


if __name__ == "__main__":
    main()
