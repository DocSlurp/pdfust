"""Score independently pinned exploratory R002 termination prefixes."""

# ruff: noqa: EM101, TRY003, PLC0415, C901
from __future__ import annotations

import argparse
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_oplog_content_audit as source
from bench import p003_oplog_content_eval as base
from bench import p003_oplog_termination as controller

CODE_FILES = tuple(dict.fromkeys(("p003_oplog_termination_eval.py", "p003_oplog_termination.py", *base.CODE_FILES)))


def verify(
    prepared: Path, approved_sha256: str, trusted_code: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Verify complete policy/source prefix freezes before any derivative target comparison."""
    from bench.silver import guard_path

    authority = source.read_json(trusted_code)
    for name in CODE_FILES:
        if source.digest(Path(__file__).with_name(name).read_bytes()) != authority.get(name):
            raise ValueError("Root-pinned runtime differs: " + name)
    if source.digest((prepared / "frozen.json").read_bytes()) != approved_sha256:
        raise ValueError("Approved source-only policy freeze differs")
    frozen = source.read_json(prepared / "frozen.json")
    if frozen["policies"] != controller.POLICIES:
        raise ValueError("Entire predeclared policy family differs")
    for name, expected in frozen["code_sha256"].items():
        if authority.get(name) != expected:
            raise ValueError("Source-only controller implementation differs")
    for name, key in (
        ("source-traces.json", "source_traces_sha256"),
        ("source-prefixes.json", "source_prefixes_sha256"),
    ):
        if source.digest(guard_path(prepared / name).read_bytes()) != frozen[key]:
            raise ValueError("Frozen complete trace/prefix evidence differs")
    with tempfile.TemporaryDirectory(prefix="p003-r002-controller-replay-") as temp:
        replay = Path(temp) / "replay"
        regenerated = controller.prepare(
            Path(frozen["original_prepared"]), frozen["original_source_freeze_sha256"], replay
        )
        if {k: v for k, v in regenerated.items() if k != "resources"} != {
            k: v for k, v in frozen.items() if k != "resources"
        }:
            raise ValueError("Source-only controller replay differs")
        for name in ("source-traces.json", "source-prefixes.json"):
            if (replay / name).read_bytes() != (prepared / name).read_bytes():
                raise ValueError("Exact source-only prefix replay differs")
    return (
        frozen,
        source.read_json(prepared / "source-traces.json"),
        source.read_json(prepared / "source-prefixes.json"),
    )


def evaluate(prepared: Path, approved_sha256: str, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Compare the entire frozen family, retaining original and hypothetical cost ledgers separately."""
    from bench.decision_context_cases import context_cases
    from bench.decision_oplog_run import score
    from bench.p003_render_reuse import Monitor
    from bench.p003_row_content_audit import compare_body
    from bench.silver import guard_path, write_json

    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh controller evaluation required")
    with Monitor() as resources:
        frozen, traces, predictions = verify(prepared, approved_sha256, trusted_code)
        # Post-hoc exploratory derivative target scoring begins only after whole-family source replay.
        cases = context_cases()
        original = source.read_json(Path(frozen["original_directory"]) / "results.json")
        original_scores = {(s["model"], s["case_index"]): s["score"] for s in original["sessions"]}
        references, records = {}, []
        for trace in traces["traces"]:
            key = trace["model"], trace["case_index"]
            initial = source.state_from(trace["initial_state"])
            case = cases[trace["case_index"]]
            if score(case, source.state_from(trace["final_state"])) != original_scores[key]:
                raise ValueError("Original target witnesses differ")
            references[key] = base.target_body(case, initial)
        for row in predictions["records"]:
            key = row["model"], row["case_index"]
            reference, exclusion = references[key]
            content = compare_body(reference, row["body_table"]) if reference is not None else None
            records.append({**row, "reference_body": reference, "exclusion": exclusion, "content": content})
        models = []
        for model in sorted({r["model"] for r in records}):
            calls = [c for t in traces["traces"] if t["model"] == model for c in t["calls"]]
            original_costs = [c["cost"]["effective_usd"] for c in calls]
            cost_complete = all(isinstance(v, (float, int)) and not isinstance(v, bool) for v in original_costs)
            for policy in controller.POLICIES:
                group = [r for r in records if r["model"] == model and r["policy"] == policy]
                counts: Counter[str] = Counter()
                for row in group:
                    if row["content"] is not None:
                        if not row["content"]["supported"]:
                            raise ValueError("Declared known body comparison unsupported")
                        counts.update(row["content"]["counts"])
                hypothetical_costs = [r["hypothetical_omitted_effective_usd"] for r in group]
                hypothetical_times = [r["hypothetical_omitted_http_seconds"] for r in group]
                models.append(
                    {
                        "model": model,
                        "policy": policy,
                        "intended_sessions": len(group),
                        "known_body_sessions": sum(r["content"] is not None for r in group),
                        "exclusions": dict(Counter(r["exclusion"] for r in group if r["exclusion"])),
                        "controller_stops": dict(Counter(r["controller_stop"] for r in group if r["controller_stop"])),
                        "retained_original_stop_types": dict(
                            Counter(r["original_prefix_stop"] for r in group if r["original_prefix_stop"])
                        ),
                        "source_complete_outputs": sum(r["source_complete"] for r in group),
                        "controller_stops_with_topology_options": sum(
                            r["controller_stop"] is not None and any(r["available_topology_operations"].values())
                            for r in group
                        ),
                        "content_counts": dict(counts),
                        "emitted_content_precision": counts["matched"] / counts["prediction_units"]
                        if counts["prediction_units"]
                        else 0.0,
                        "known_body_content_recall": counts["matched"] / counts["reference_units"]
                        if counts["reference_units"]
                        else 0.0,
                        "emitted_recovered_bodies": sum(
                            r["content"] is not None and r["content"].get("content_recovered_with_row_order", False)
                            for r in group
                        ),
                        "retained_model_finished_recovered_bodies": sum(
                            r["original_prefix_stop"] == "finished"
                            and r["content"] is not None
                            and r["content"].get("content_recovered_with_row_order", False)
                            for r in group
                        ),
                        "controller_stopped_recovered_bodies": sum(
                            r["controller_stop"] is not None
                            and r["content"] is not None
                            and r["content"].get("content_recovered_with_row_order", False)
                            for r in group
                        ),
                        "retained_original_calls": sum(r["processed_original_calls"] for r in group),
                        "hypothetically_omitted_original_calls": sum(r["omitted_original_calls"] for r in group),
                        "hypothetical_omitted_effective_usd": sum(hypothetical_costs)
                        if all(v is not None for v in hypothetical_costs)
                        else None,
                        "hypothetical_omitted_http_seconds": sum(hypothetical_times)
                        if all(v is not None for v in hypothetical_times)
                        else None,
                        "original_call_count": len(calls),
                        "original_effective_usd": sum(original_costs) if cost_complete else None,
                        "original_cost_complete": cost_complete,
                        "realized_api_savings": 0,
                        "semantic_or_schema_acceptance": None,
                    }
                )
    result = {
        "version": "p003-r002-exploratory-termination-evaluation-v1",
        "policies": controller.POLICIES,
        "source_freeze_sha256": approved_sha256,
        "source_traces_sha256": frozen["source_traces_sha256"],
        "source_prefixes_sha256": frozen["source_prefixes_sha256"],
        "runtime_authority_sha256": source.digest(trusted_code.read_bytes()),
        "design": frozen["design"],
        "records": records,
        "models": models,
        "original_calls": original["calls"],
        "resources": resources.metrics(),
        "new_api_calls": 0,
        "cost_policy": frozen["cost_policy"],
        "completion_policy": frozen["completion_policy"],
        "original_score_dictionaries_reproduced": True,
    }
    output.mkdir(parents=True)
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Require independent whole-family source freeze and runtime authority."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--source-frozen-sha256", required=True)
    parser.add_argument("--trusted-code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    evaluate(args.prepared, args.source_frozen_sha256, args.trusted_code, args.output)


if __name__ == "__main__":
    main()
