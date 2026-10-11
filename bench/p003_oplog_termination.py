"""Freeze exploratory source-only controller prefixes over all retained R002 traces."""

# ruff: noqa: EM101, TRY003, PLC0415, PLR2004, PERF401
from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from bench import p003_oplog_content_audit as source
from bench.decision_oplog import Session, State, apply, proposals

POLICIES = {
    "baseline-original": "Retain the original entire attempted trace and original ending",
    "P1-source-complete": "Before a next request, stop iff unassigned and deferred are both empty",
    "P2-seen-successors": (
        "Before a next request, stop iff at least one non-finish/non-unresolved proposal exists "
        "and every such admissible successor hash is already seen"
    ),
    "P3-fixed-three": "Before a next request, stop after three original calls; preserve earlier original stops",
}
VERSION = "p003-r002-exploratory-source-termination-v1"


def stop_decision(policy: str, state: State, seen: set[str], processed: int) -> str | None:
    """Apply fixed source-only rules; full ownership does not establish topology correctness."""
    if policy not in POLICIES:
        raise ValueError("Unknown frozen controller")
    if policy == "P1-source-complete" and not state.unassigned and not state.deferred:
        return "controller-source-complete"
    if policy == "P2-seen-successors":
        productive = [op for op in proposals(state) if op.kind not in {"finish", "leave_unresolved"}]
        if productive and all(apply(state, op).sha256 in seen for op in productive):
            return "controller-seen-successors"
    if policy == "P3-fixed-three" and processed >= 3:
        return "controller-fixed-call-cap"
    return None


def prefix(initial: State, calls: list[dict[str, Any]], policy: str, max_steps: int) -> dict[str, Any]:
    """Replay an unmodified trace prefix; controller stops never become model finish."""
    session = Session(initial, max_steps=max_steps)
    seen, processed, controller = {initial.sha256}, 0, None
    for call in calls:
        if session.stop_reason is not None:
            raise ValueError("Call after original ending")
        controller = stop_decision(policy, session.state, seen, processed)
        if controller is not None:
            break
        menu = proposals(session.state)
        if session.state.sha256 != call["before_state_sha256"]:
            raise ValueError("Prefix source state differs")
        session.choose(call["answer"]["choice"], menu)
        if session.state.sha256 != call["after_state_sha256"] or session.stop_reason != call["stop_reason"]:
            raise ValueError("Prefix transition differs")
        processed += 1
        seen.add(session.state.sha256)
    remaining = calls[processed:]
    costs = [c["cost"]["effective_usd"] for c in remaining]
    times = [c.get("http_elapsed_ms") for c in remaining]
    complete_cost = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in costs)
    complete_time = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in times)
    menu = proposals(session.state) if controller is not None else ()
    body = source.body_table(session.state, initial)
    return {
        "policy": policy,
        "controller_stop": controller,
        "original_prefix_stop": session.stop_reason,
        "processed_original_calls": processed,
        "omitted_original_calls": len(remaining),
        "state": asdict(session.state),
        "state_sha256": session.state.sha256,
        "body_table": body,
        "body_sha256": source.digest(json.dumps(body, sort_keys=True).encode()),
        "source_complete": not session.state.unassigned and not session.state.deferred,
        "available_topology_operations": {
            kind: sum(op.kind == kind for op in menu) for kind in ("move", "join", "split")
        },
        "retained_original_receipt_indices": [c["entry"]["index"] for c in calls[:processed]],
        "hypothetical_omitted_suffix": [
            {
                "entry_index": c["entry"]["index"],
                "request_sha256": c["request_sha256"],
                "response_file": c["entry"]["response_file"],
                "http_elapsed_ms": c.get("http_elapsed_ms"),
                "original_cost": c["cost"],
                "step": c["step"],
            }
            for c in remaining
        ],
        "hypothetical_omitted_effective_usd": sum(costs) if complete_cost else None,
        "hypothetical_omitted_http_seconds": sum(times) / 1000 if complete_time else None,
        "suffix_cost_complete": complete_cost,
        "suffix_time_complete": complete_time,
    }


def prepare(prepared: Path, approved_sha256: str, output: Path) -> dict[str, Any]:
    """Freeze all policy decisions and all 20 source traces before derivative target scoring."""
    from bench.p003_render_reuse import Monitor
    from bench.silver import guard_path, write_json

    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh exploratory preparation required")
    if source.digest((prepared / "frozen.json").read_bytes()) != approved_sha256:
        raise ValueError("Root-approved base source freeze differs")
    frozen = source.read_json(prepared / "frozen.json")
    for name, expected in frozen["code_sha256"].items():
        if source.digest(Path(__file__).with_name(name).read_bytes()) != expected:
            raise ValueError("Base source helper differs")
    with Monitor() as resources:
        with tempfile.TemporaryDirectory(prefix="p003-r002-termination-source-") as temp:
            replay = Path(temp) / "replay"
            source.prepare(Path(frozen["directory"]), replay)
            if (replay / "source-output.json").read_bytes() != (prepared / "source-output.json").read_bytes():
                raise ValueError("Complete original source replay differs")
        report = source.read_json(Path(frozen["directory"]) / "results.json")
        records, traces = [], []
        manifest = source.read_json(Path(frozen["directory"]) / "manifest.json")
        for original in report["sessions"]:
            calls = [
                c
                for c in report["calls"]
                if (c["model"], c["case_index"]) == (original["model"], original["case_index"])
            ]
            initial = source.state_from(
                original["history"][0]["before"] if original["history"] else original["final_state"]
            )
            traces.append(
                {
                    "model": original["model"],
                    "case_index": original["case_index"],
                    "initial_state": asdict(initial),
                    "calls": calls,
                    "final_state": original["final_state"],
                    "history": original["history"],
                    "original_stop_reason": original["stop_reason"],
                }
            )
            for policy in POLICIES:
                records.append(
                    {
                        "model": original["model"],
                        "case_index": original["case_index"],
                        "original_stop_reason": original["stop_reason"],
                        **prefix(initial, calls, policy, manifest["max_steps"]),
                    }
                )
    output.mkdir(parents=True)
    write_json(output / "source-traces.json", {"traces": traces})
    write_json(output / "source-prefixes.json", {"records": records})
    plan = {
        "version": VERSION,
        "policies": POLICIES,
        "original_source_freeze_sha256": approved_sha256,
        "original_prepared": str(prepared),
        "original_directory": frozen["directory"],
        "source_traces_sha256": source.digest((output / "source-traces.json").read_bytes()),
        "source_prefixes_sha256": source.digest((output / "source-prefixes.json").read_bytes()),
        "code_sha256": {
            n: source.digest(Path(__file__).with_name(n).read_bytes())
            for n in (
                "p003_oplog_termination.py",
                "p003_oplog_content_audit.py",
                "decision_oplog.py",
                "p003_render_reuse.py",
            )
        },
        "sessions": 20,
        "policy_session_observations": 80,
        "original_calls": 83,
        "resources": resources.metrics(),
        "derivative_target_scoring": False,
        "new_api_calls": 0,
        "design": "Post-hoc exploratory source-only policies; original gold already inspected in the base audit",
        "cost_policy": "Preserve every original cost; suffix omission is hypothetical exposure, never realized savings",
        "completion_policy": (
            "Controller actions remain separate from original model finish; ownership is not semantic correctness"
        ),
    }
    write_json(output / "frozen.json", plan)
    return plan


def main() -> None:
    """Prepare the entire frozen policy family without accessing derivative targets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--source-frozen-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.prepared, args.source_frozen_sha256, args.output)


if __name__ == "__main__":
    main()
