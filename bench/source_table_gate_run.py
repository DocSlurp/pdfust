"""Explicit paid source-presence runner; retained scoring is the default."""

# ruff: noqa: EM101, TRY003, ANN401
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
from statistics import median
from typing import Any

from bench.decision_hosted import RESERVATION, ROOT, DecisionClient, accounted_cost, checkpoint, exclusive_lock
from bench.decision_oplog_run import parse_choice
from bench.reprice_model_rates import request_cost
from bench.silver import guard_path
from bench.source_table_gate import CRITERIA, MODELS, VISIBLE_KEYS, variants

TAG_PREFIX = "G001-source-gate/"
WAVE_LIMIT = 0.50


def verify(directory: Path) -> dict[str, Any]:
    """Verify every body and literal-source identity before constructing a paid client."""
    directory = guard_path(directory)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    if sha(directory / "source-frozen.json") != manifest["source_sha256"]:
        raise ValueError("Frozen source identity changed")
    if set(manifest["models"]) != set(MODELS):
        raise ValueError("Undeclared gate model")
    sources = {p["id"]: p for p in json.loads((directory / "source-frozen.json").read_text())["pages"]}
    expected_prompts = {v["name"]: v["instructions"] for v in variants()}
    seen = set()
    for record in manifest["records"]:
        if record["route"] == "native_vector":
            continue
        name = record["request"]
        if Path(name).name != name or sha(directory / name) != record["sha256"]:
            raise ValueError("Frozen body hash or path changed")
        body = json.loads((directory / name).read_text())
        q0 = body["questions"]["q0"]
        visible = json.loads(body["state"][0])
        key = (record["id"], record["model"], record["variant"])
        if key in seen or record["route"] != "hosted_presence_gate":
            raise ValueError("Duplicate or undeclared gate route")
        seen.add(key)
        if (
            body["model"] != record["model"]
            or record["model"] not in MODELS
            or q0["criteria"] != CRITERIA
            or set(record["choices"]) != set(CRITERIA)
            or q0["instructions"] != expected_prompts[record["variant"]]
            or set(visible) != VISIBLE_KEYS
            or visible["source_words"] != sources[record["id"]]["words"]
        ):
            raise ValueError("Frozen model, prompt, menu or literal source changed")
    native = {r["id"] for r in manifest["records"] if r["route"] == "native_vector"}
    expected = {
        (identifier, model, variant)
        for identifier in sources
        if identifier not in native
        for model in MODELS
        for variant in expected_prompts
    }
    if seen != expected or not native <= set(sources) or len(sources) != manifest["pages"]:
        raise ValueError("Incomplete or mismatched frozen gate cohort")
    return manifest


def sha(path: Path) -> str:
    """Hash complete frozen bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wave_admission(entries: list[dict[str, Any]]) -> None:
    """Keep persistent gate-prefix reservations separate from actual cost reports."""
    used = sum(accounted_cost(e["accounted_usd"]) for e in entries if e.get("tag", "").startswith(TAG_PREFIX))
    if used + RESERVATION > WAVE_LIMIT + 1e-12:
        raise RuntimeError("Persistent gate-prefix cap cannot admit another reservation")


def _entries(client: Any) -> list[dict[str, Any]]:
    return json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []


def run(directory: Path, targets_path: Path, client: Any, *, report_path: Path | None = None) -> dict[str, Any]:  # noqa: C901
    """Execute only explicitly requested frozen requests, stopping each model on its first failure."""
    began, cpu = time.perf_counter(), time.process_time()
    manifest = verify(directory)
    with exclusive_lock(client.ledger.parent / "run.lock"):
        result_path = directory / "hosted-results.json"
        retained = json.loads(result_path.read_bytes()) if result_path.exists() else {"calls": [], "stopped_models": []}
        calls, stopped = retained["calls"], set(retained["stopped_models"])
        prior = _entries(client)
        for entry in prior:
            if entry.get("tag", "").startswith(TAG_PREFIX) and not entry.get("response_file"):
                stopped.add(entry.get("requested_model"))
        done = {r["sha256"] for r in calls}
        prices_path = client.ledger.parent / "langfuse/catalog-prices.json"
        catalog = json.loads(prices_path.read_bytes()) if prices_path.exists() else {"prices": {}}
        budget_stopped = False
        for record in manifest["records"]:
            if (
                record["route"] != "hosted_presence_gate"
                or record["sha256"] in done
                or record["model"] in stopped
                or budget_stopped
            ):
                continue
            raw = (directory / record["request"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != record["sha256"]:
                raise ValueError("Frozen request changed after initial verification")
            body = json.loads(raw)
            digest = hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest()
            entries = _entries(client)
            known = next((e for e in entries if e.get("request_sha256") == digest), None)
            if known is None:
                try:
                    wave_admission(entries)
                except RuntimeError:
                    budget_stopped = True
                    break
            row = {
                **record,
                "status": "pending",
                "usage": {},
                "answer": {},
                "replayed": False,
                "http_elapsed_ms": None,
                "cost": {"effective_usd": None},
            }
            calls.append(row)
            checkpoint(
                result_path,
                {
                    "calls": calls,
                    "stopped_models": sorted(stopped),
                    "tag_prefix": TAG_PREFIX,
                    "wave_limit_usd": WAVE_LIMIT,
                },
            )
            try:
                if known is not None and not known.get("response_file"):
                    raise RuntimeError("Prior identical request failed; no retry")  # noqa: TRY301
                response = client.request(
                    body,
                    tag=f"{TAG_PREFIX}{record['model']}/{record['variant']}/{record['id']}",
                    max_body_bytes=750_000,
                )
                row.update(
                    entry=response["entry"],
                    usage=response["result"].get("usage", {}),
                    replayed=response["replayed"],
                    http_elapsed_ms=response["entry"].get("elapsed_ms"),
                )
                row["cost"] = request_cost(
                    row["entry"], row["usage"], catalog.get("prices", {}).get(record["model"], {})
                )
                row["answer"] = parse_choice(response["result"], set(body["questions"]["q0"]["criteria"]))
                row["status"] = "ok"
            except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
                row.update(status="error", error=type(error).__name__)
                failed = next((e for e in _entries(client) if e.get("request_sha256") == digest), None)
                if failed is not None and "entry" not in row:
                    row.update(entry=failed, usage={}, http_elapsed_ms=failed.get("elapsed_ms"))
                    row["cost"] = request_cost(failed, {}, catalog.get("prices", {}).get(record["model"], {}))
                stopped.add(record["model"])
            checkpoint(
                result_path,
                {
                    "calls": calls,
                    "stopped_models": sorted(stopped),
                    "tag_prefix": TAG_PREFIX,
                    "wave_limit_usd": WAVE_LIMIT,
                },
            )
        summary = evaluate(directory, targets_path, calls)
        summary.update(
            tag_prefix=TAG_PREFIX,
            wave_limit_usd=WAVE_LIMIT,
            stopped_models=sorted(stopped),
            budget_stopped=budget_stopped,
            frozen_manifest_sha256=hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
            catalog_provenance=catalog,
            execution_resources={
                "wall_seconds": time.perf_counter() - began,
                "cpu_seconds": time.process_time() - cpu,
                "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                "measurement": "SELF process_time/perf_counter; process-lifetime getrusage RSS; "
                "serial requests, no children or periodic sampling; HTTP wait included in wall",
            },
            preparation={k: manifest[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")},
            code_sha256={
                str(p.name): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (
                    Path(__file__),
                    Path(__file__).with_name("source_table_gate.py"),
                    Path(__file__).with_name("decision_hosted.py"),
                )
            },
        )
        checkpoint(directory / "evaluation.json", summary)
        if report_path:
            report_path.write_text(render_report(summary))
        return summary


def evaluate(directory: Path, targets_path: Path, calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Load reference presence kinds only after verifying frozen source-only requests."""
    manifest = verify(directory)
    sources = json.loads((directory / "source-frozen.json").read_text())["pages"]
    targets = {p["id"]: p for p in json.loads(guard_path(targets_path).read_text())}
    if {p["id"] for p in sources} != set(targets):
        raise ValueError("Reference cohort differs from frozen sources")
    native = {r["id"] for r in manifest["records"] if r["route"] == "native_vector"}
    lookup = {(r["id"], r["model"], r["variant"]): r for r in calls}
    cohorts: dict[str, Any] = {}
    for model in MODELS:
        for variant in variants():
            rows = []
            for page in sources:
                identifier = page["id"]
                kind = targets[identifier]["kind"]
                call = lookup.get((identifier, model, variant["name"]))
                choice = call["answer"]["choice"] if call and call["status"] == "ok" else "unmeasured_or_failed"
                if identifier in native:
                    choice = "native_vector_zero_call"
                expected = {"borderless": "table_present", "prose": "not_table"}.get(kind)
                rows.append(
                    {
                        "id": identifier,
                        "kind": kind,
                        "choice": choice,
                        "scored": expected is not None and identifier not in native,
                        "correct": choice == expected if expected is not None and identifier not in native else None,
                    }
                )
            slices = {}
            for kind in ("borderless", "prose"):
                selected = [r for r in rows if r["kind"] == kind and r["scored"]]
                slices[kind] = {
                    "pages": len(selected),
                    "correct": sum(r["correct"] for r in selected),
                    "table_present": sum(r["choice"] == "table_present" for r in selected),
                    "unresolved_or_failed": sum(
                        r["choice"] in {"unresolved", "unmeasured_or_failed"} for r in selected
                    ),
                }
            relevant = [r for r in calls if r["model"] == model and r["variant"] == variant["name"]]
            cohorts[f"{model}/{variant['name']}"] = {
                "rows": rows,
                "slices": slices,
                "ambiguous_unscored_pages": sum(r["kind"] == "ambiguous" for r in rows),
                "native_zero_call_pages": len(native),
                "actual_gate_accounting": accounting(relevant),
            }
    return {
        "cohorts": cohorts,
        **accounting(calls),
        "pages": len(sources),
        "limits": "Presence labels only for borderless/prose. Native controls zero-call; other kinds unscored. "
        "No reconstruction or cached cascade performance claim.",
    }


def accounting(calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Retain costs of failed requests; unknown or incomplete measurements remain unknown."""
    unique = {r["entry"]["index"]: r for r in calls if "entry" in r}
    costs = [r["cost"] for r in unique.values()]
    times = [r["http_elapsed_ms"] for r in unique.values() if r.get("http_elapsed_ms") is not None]
    return {
        "unique_requests": len(unique),
        "effective_usd": sum(c["effective_usd"] for c in costs)
        if all(c["effective_usd"] is not None for c in costs)
        else None,
        "known_partial_usd": sum(c["effective_usd"] for c in costs if c["effective_usd"] is not None),
        "unknown_cost_requests": sum(c["effective_usd"] is None for c in costs),
        "http_elapsed_median_ms": median(times) if times else None,
        "http_elapsed_total_seconds": sum(times) / 1000 if times and len(times) == len(unique) else None,
        "http_elapsed_measured_requests": len(times),
    }


def render_report(summary: dict[str, Any]) -> str:
    """Report actual gate decisions/costs separately for each model and generic prompt."""
    lines = [
        "# Source-only table-presence gates",
        "",
        (
            "| Model / prompt | Borderless presence | Prose false presence | Unresolved/failed positives | "
            "Native | Ambiguous unscored | Actual effective USD |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, cohort in summary["cohorts"].items():
        positive, negative = cohort["slices"]["borderless"], cohort["slices"]["prose"]
        lines.append(
            f"| {key} | {positive['correct']}/{positive['pages']} | "
            f"{negative['table_present']}/{negative['pages']} | {positive['unresolved_or_failed']} | "
            f"{cohort['native_zero_call_pages']} | {cohort['ambiguous_unscored_pages']} | "
            f"{cohort['actual_gate_accounting']['effective_usd']} |"
        )
    for key, cohort in summary["cohorts"].items():
        lines += ["", f"Actual gate accounting {key}: {json.dumps(cohort['actual_gate_accounting'])}"]
    lines += [
        "",
        json.dumps({k: v for k, v in summary.items() if k != "cohorts"}, indent=2),
        "",
        (
            "Costs include retained failures. Positive provider charges take precedence; token/catalog estimates "
            "are labeled in retained cost records. Reservations are not actual gate costs. Missing costs and HTTP "
            "times stay unknown. No model confidence is calibrated correctness. Ambiguous references are unscored."
        ),
        "",
        (
            "Gate costs and HTTP timings are actual retained gate measurements only. Applying gate decisions to "
            "prior admission answers would be an offline routing simulation, not fresh provider cache or cascade "
            "latency/saving measurements. No default PDF behavior changes."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Use retained reports by default; hosted requests require the explicit run flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report", type=Path, default=ROOT / "bench/results/source-table-gate-run.md")
    args = parser.parse_args()
    verify(args.directory)
    if args.run_hosted:
        summary = run(args.directory, args.targets, DecisionClient(), report_path=args.report)
    else:
        retained = args.directory / "hosted-results.json"
        calls = json.loads(retained.read_text())["calls"] if retained.exists() else []
        summary = evaluate(args.directory, args.targets, calls)
        checkpoint(args.directory / "evaluation.json", summary)
        args.report.write_text(render_report(summary))
    print(json.dumps({k: summary[k] for k in ("unique_requests", "effective_usd")}, indent=2))


if __name__ == "__main__":
    main()
