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
    reported = sum(
        (
            v
            for k, v in amounts.items()
            if k in {"provider-reported USD", "provider-reported BYOK upstream plus gateway USD"}
        ),
        Decimal(0),
    )
    estimates = amounts.get("catalog estimate", Decimal(0))
    reserved = amounts.get("reserved", Decimal(0))
    exposed = sum(amounts.values(), Decimal(0))
    supported = {
        "provider-reported USD",
        "provider-reported BYOK upstream plus gateway USD",
        "catalog estimate",
        "reserved",
    }
    unknown_basis = sum(r.get("cost_status") not in supported for r in rows)
    total = sum((v for k, v in amounts.items() if k in supported), Decimal(0))
    complete = not unknown and not unknown_basis
    return {
        "attempts": len(rows),
        "states": dict(Counter(r.get("concurrent_state", "legacy") for r in rows)),
        "ledger_classified_reported_usd": str(reported),
        "catalog_estimated_usd": str(estimates),
        "unresolved_reserved_usd": str(reserved),
        "known_accounted_usd": str(total),
        "unknown_amount_entries": unknown,
        "unknown_basis_entries": unknown_basis,
        "accounting_complete": complete,
        "exposed_ledger_conservative_usd": str(exposed),
        "effective_reported_plus_estimated_subtotal_usd": str(reported + estimates),
        "cost_status_totals_usd": {k: str(v) for k, v in amounts.items()},
        "wave_remaining_usd": str(Decimal(50) - total) if complete else None,
        "prior_conservative_baseline_usd": str(BASELINE),
        "prior_baseline_reference": (
            "Root-authorized prior cumulative conservative snapshot, retained in AGENTS.md P003 authorization; "
            "not recomputed from a changing ledger"
        ),
        "baseline_plus_wave_conservative_usd": str(BASELINE + exposed),
        "cumulative_remaining_usd": str(Decimal(200) - BASELINE - total) if complete else None,
        "basis": "Ledger accounted_usd grouped by its retained cost_status; reserved exposure is not billed cost",
    }


def queue_summary(queue: dict[str, Any], status: Path) -> dict[str, Any]:
    """Keep synthetic question counters distinct from PDF page outcomes."""
    states = Counter(a["status"] for a in queue["arms"])
    completed = [a for a in queue["arms"] if a["status"] == "completed"]
    result = {
        "name": status.parent.name,
        "required": len(queue["frozen_order"]),
        "completed_jobs": len(completed),
        "running_jobs": states["running"],
        "starting_jobs": states["starting"],
        "queued_jobs": len(queue["frozen_order"]) - len(queue["arms"]),
        "failed_jobs": sum(states[k] for k in ("failed", "error", "timeout")),
        "job_state_counts": dict(states),
        "completed_with_evaluation_file": sum(
            (status.parent / a["name"] / "evaluation.json").exists() for a in completed
        ),
        "evaluation_scope": "presence only; freshness/quality verification belongs to evaluator",
        "running": [a["name"] for a in queue["arms"] if a["status"] == "running"],
        "worker_resources": queue.get("resources"),
    }
    question_kinds = {"micro", "synthetic_relations", "synthetic_shared_context", "synthetic_resolution"}
    alias_receipts = []
    for arm in completed:
        if arm.get("kind") not in question_kinds:
            continue
        filename = {
            "synthetic_shared_context": "synthetic-shared-alias-evaluation.json",
            "synthetic_resolution": "synthetic-resolution-evaluation.json",
        }.get(arm.get("kind"), "synthetic-alias-evaluation.json")
        path = status.parent / arm["name"] / filename
        if not path.exists():
            continue
        audit, receipt = observed(path)
        original, secondary = audit.get("original_verified", {}), audit.get("secondary_verified", {})
        alias_receipts.append(
            {
                **receipt,
                "arm": arm["name"],
                "original_verification_recorded": bool(original.get("report_sha256")),
                "secondary_verification_recorded": bool(secondary.get("report_sha256")),
                "secondary_scope": secondary.get("scope"),
                "scope": "Retained independent evaluator receipt; reporter does not rerun scoring or inspect requests",
            }
        )
    if alias_receipts:
        result["synthetic_independent_alias_audits"] = alias_receipts
        result["synthetic_recorded_original_verified_jobs"] = sum(
            r["original_verification_recorded"] for r in alias_receipts
        )
        result["synthetic_recorded_secondary_verified_jobs"] = sum(
            r["secondary_verification_recorded"] for r in alias_receipts
        )
    pdf = [a for a in completed if a.get("kind") not in question_kinds]
    synthetic = [a for a in completed if a.get("kind") in question_kinds]
    if pdf:
        result["attempted_pdf_pages"] = sum(a.get("attempted_pages", 0) or 0 for a in pdf)
        result["operational_pdf_pages"] = sum(a.get("completed_pages", 0) or 0 for a in pdf)
    if synthetic:
        result["synthetic_question_counts"] = {
            key: sum(a.get(key, 0) or 0 for a in synthetic)
            for key in (
                "intended_questions",
                "attempted_questions",
                "valid_returned_questions",
                "nonabstaining_questions",
            )
        }
        question_states: Counter[str] = Counter()
        for arm in synthetic:
            question_states.update(arm.get("question_status_counts", {}))
        result["question_status_counts"] = dict(question_states)
        result["question_correctness_measured"] = False
    return result


def checkpoint(  # noqa: C901, PLR0912
    statuses: list[Path], ledger: Path, output: Path, planned: list[str], metadata: Path | None = None
) -> Path:
    """Read one snapshot and write immutable JSON/Markdown plus latest local views."""
    started, cpu = time.monotonic(), time.process_time()
    pairs = [(status, *observed(status)) for status in statuses]
    summaries = [queue_summary(queue, status) for status, queue, _ in pairs]
    sources = [receipt for _, _, receipt in pairs]
    book, ledger_receipt = observed(ledger)
    rows = [r for r in book["requests"] if r.get("tag", "").startswith("P003/")]
    costs = money(rows)
    plans = []
    for declaration in planned:
        name, count = declaration.rsplit("=", 1)
        plans.append(
            {"name": name, "required": int(count), "scope": "coordinator-declared plan; launch telemetry unavailable"}
        )
    coordinator: dict[str, Any] = {}
    if metadata is not None:
        coordinator, receipt = observed(metadata)
        sources.append(receipt)
        allowed = {
            "coordinator_last_published_utc",
            "publication_precision",
            "next_coordinator_publication_deadline_utc",
            "service_observations",
        }
        if set(coordinator) - allowed:
            message = "Coordinator receipt must contain only publication/service metadata"
            raise ValueError(message)
    now = datetime.now(UTC)
    unfinished = any(q["running_jobs"] or q["starting_jobs"] or q["queued_jobs"] for q in summaries)
    if unfinished:
        next_action = "Finish the active queue, independently verify outputs, root admits the next reviewed queue"
        eta = "Unknown: no aggregate queue rate; mixed arm kinds and individual time limits"
    elif plans:
        next_action = "Root confirms admission of the declared next phase; verify and summarize completed cohorts"
        eta = "Next-phase launch is not observed; completion ETA is unknown"
    else:
        next_action = "Verify and summarize completed cohorts; root decides the next reviewed work"
        eta = "Observed queues have drained; no active queue completion remains to estimate"
    snapshot = {
        "reported_at_utc": now.isoformat(),
        "coordinator_last_published_utc": None,
        "next_coordinator_publication_deadline_utc": (now + timedelta(minutes=5)).isoformat(),
        "sources": [*sources, ledger_receipt],
        "roles": {
            "root": "coordination and new experiments",
            "catalog": "queues and baselines",
            "eval": "independent verification",
            "reporter": "progress and actual-input visuals",
        },
        "queues": summaries,
        "plans": plans,
        "costs": costs,
        "worker_resources": [q["worker_resources"] for q in summaries],
        "reporting_model_cost_usd": None,
        "reporting_model_cost_scope": "not exposed in authorized telemetry",
        "new_hosted_calls": 0,
        "paid_cutoff_utc": "2026-10-11T02:12:00Z",
        "wave_finish_utc": "2026-10-11T02:27:00Z",
        "eta": eta,
        "next": next_action,
        "cadence": "Coordinator publishes within five minutes and on material changes; no autonomous timer",
    }
    snapshot.update(coordinator)
    display = {
        key: f"{Decimal(value):.10f}" if isinstance(value, str) and key.endswith("_usd") else value
        for key, value in costs.items()
    }
    text = f"P003 checkpoint — {now:%Y-%m-%d %H:%M:%S UTC}\n\n"
    text += "| Queue | Required | Completed jobs | Running | Starting | Queued | Job failures |\n"
    text += "| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n"
    for q in summaries:
        text += (
            f"| {q['name']} | {q['required']} | {q['completed_jobs']} | {q['running_jobs']}"
            f" | {q['starting_jobs']} | {q['queued_jobs']} | {q['failed_jobs']} |\n"
        )
    for plan in plans:
        text += (
            f"| {plan['name']} plan | {plan['required']} | Job status not observed | "
            "Unknown | Unknown | Job status not observed | Unknown |\n"
        )
    text += "\n"
    if coordinator:
        text += "Coordinator-supplied observations (not independently verified service telemetry):\n"
        text += json.dumps(coordinator, sort_keys=True) + "\n\n"
    for q in summaries:
        if "synthetic_independent_alias_audits" in q:
            text += (
                f"{q['name']}: independent synthetic original verification recorded "
                f"{q['synthetic_recorded_original_verified_jobs']}/{q['completed_jobs']}; "
                f"secondary alias replay {q['synthetic_recorded_secondary_verified_jobs']}/{q['completed_jobs']}. "
                "Original strict outcomes preserved; reporter does not rerun verification.\n"
            )
        else:
            text += (
                f"{q['name']}: evaluation files {q['completed_with_evaluation_file']}/{q['completed_jobs']} "
                "(presence does not certify freshness).\n"
            )
        if "attempted_pdf_pages" in q:
            text += (
                f"PDF outcomes: {q['attempted_pdf_pages']} attempted; {q['operational_pdf_pages']} operational; "
                f"{q['attempted_pdf_pages'] - q['operational_pdf_pages']} non-success.\n"
            )
        if "synthetic_question_counts" in q:
            text += f"Synthetic question outcomes, distinct from PDF pages: {q['synthetic_question_counts']}.\n"
    text += "Operational/schema-valid results do not certify strict correctness.\n"
    text += f"""
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

Sources observed from file timestamps: {json.dumps(snapshot["sources"], sort_keys=True)}.
Worker CPU/RAM measurement is the
retained psutil 100 ms queue-plus-recursive-descendant sample, not reporter cost:
{json.dumps(snapshot["worker_resources"], sort_keys=True)}.
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
    parser.add_argument("--status", type=Path, required=True, action="append")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--planned", action="append", default=[])
    parser.add_argument("--coordinator-metadata", type=Path)
    args = parser.parse_args()
    print(checkpoint(args.status, args.ledger, args.output, args.planned, args.coordinator_metadata))


if __name__ == "__main__":
    main()
