"""Generate P003 progress tables from explicitly named independently verified evaluations."""

# Retained benchmark JSON has heterogeneous resource/score fields.
# ruff: noqa: ANN401, EM101, TRY003, C901, PLR0912, ISC004
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from bench.p003_decision_evidence import decision_evidence
from bench.silver import guard_path, sha

KNOWN_RUNS = (
    "screen-ordinal-ocr300-512-r0",
    "screen-gated-pplx-ocr300-512-r0",
    "screen-crops-haiku-1024-pinned-r0",
    "screen-crops-luna-1024-pinned-r0",
)
EVALUATION_NAMES = ("evaluation-cost-reconciled.json", "evaluation.json", "verified-evaluation.json")


def load_evaluations(paths: list[Path], report_directory: Path | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Read explicit paths only; missing completed evaluations stay visible as pending."""
    runs: dict[str, dict[str, Any]] = {}
    pending = []
    for requested in paths:
        path = guard_path(requested)
        candidates = [path] if path.suffix == ".json" else [path / name for name in EVALUATION_NAMES]
        selected = next((p for p in candidates if p.is_file()), None)
        if selected is None:
            pending.append(str(path))
            continue
        content = selected.read_bytes()
        payload = json.loads(content)
        for observed in payload["runs"]:
            required = {
                "name",
                "report_sha256",
                "code_sha256",
                "scores",
                "resources",
                "costs",
                "intended_pages",
                "operational_pages",
                "errors",
                "exact_positive_pages",
                "evaluation_scope",
            }
            if not required <= observed.keys() or not observed["code_sha256"]:
                raise ValueError("Progress input lacks independently verified run provenance")
            if observed["operational_pages"] + observed["errors"] != observed["intended_pages"]:
                raise ValueError("Progress input drops failures from intended-page denominator")
            run = {**observed, "evaluation_path": str(selected), "evaluation_sha256": sha(content)}
            if Path(run["name"]).name != run["name"] or run["name"] in {".", ".."}:
                raise ValueError("Unsafe verified run name")
            source_report = selected.parent / "report.json"
            if not source_report.is_file() and report_directory is not None:
                source_report = report_directory / run["name"] / "report.json"
            source_report = guard_path(source_report)
            if source_report.is_file():
                raw = guard_path(source_report).read_bytes()
                if sha(raw) != run["report_sha256"]:
                    raise ValueError("Provider cache source report differs from independently verified report hash")
                report = json.loads(raw)
                run["decision_evidence"] = decision_evidence(report)
                incremental_key, call_key = {
                    "p003_candidate_choice": ("incremental_ranking", "ranking_calls"),
                    "p003_boundary_repair": ("incremental_repair", "repair_calls"),
                    "p003_gate": ("incremental_gate", "calls"),
                    "p003_topology_source": ("incremental_ownership", "topology_calls"),
                    "p003_structure_admission": ("incremental_admission", "decision_results"),
                    "p003_geometry_diagram": ("incremental_selection", "decision_results"),
                    "p003_header_decision": ("incremental_header_selection", "decision_results"),
                }.get(report["config"].get("processor"), (None, "calls"))
                measured_calls = [call for page in report["results"] for call in page.get(call_key, [])]
                attempt_scope = report[incremental_key] if incremental_key else report
                measured_attempts = attempt_scope.get("charges", attempt_scope).get("ledger_attempts")
                if report["config"].get("transcript_replay") is True:
                    if measured_attempts != 0:
                        raise ValueError("Transcript replay declares new provider attempts")
                    original_report = report["transcript_origin"]["original_report"]
                    run["retained_transcript_provider_cache_usage"] = cache_usage(
                        measured_calls, original_report["incremental_ownership"].get("ledger_attempts")
                    )
                    measured_calls = []
                run["provider_cache_usage"] = cache_usage(measured_calls, measured_attempts)
                baseline_reports = report.get("candidate_generation_reports", [])
                if report.get("baseline_report") is not None:
                    baseline_reports = [report["baseline_report"]]
                if report.get("source_generation_report") is not None:
                    baseline_reports = [report["source_generation_report"], report["topology_generation_report"]]
                run["historical_provider_cache_usage"] = [
                    cache_usage(
                        [call for page in baseline["results"] for call in page.get("calls", [])],
                        baseline.get("ledger_attempts"),
                    )
                    for baseline in baseline_reports
                ]
            prior = runs.get(run["name"])
            if prior is not None:
                if prior["report_sha256"] != run["report_sha256"] or prior["scores"] != run["scores"]:
                    raise ValueError("Conflicting frozen quality for the same run name")
                if prior.get("cost_reconciliation") is not None and run.get("cost_reconciliation") is None:
                    continue
            runs[run["name"]] = run
    return list(runs.values()), pending


def cache_usage(calls: list[dict[str, Any]], ledger_attempts: int | None) -> dict[str, Any]:
    """Sum explicit provider cache counters over unique fresh returned ledger entries only."""
    indexed: dict[int, dict[str, Any]] = {}
    replayed = unattributed = unknown_freshness = 0
    for call in calls:
        if call.get("replayed") is True:
            replayed += 1
            continue
        if call.get("replayed") is not False:
            unknown_freshness += 1
            continue
        index = call.get("entry", {}).get("index")
        if type(index) is not int:
            unattributed += 1
            continue
        direct_usage = call.get("usage")
        nested_usage = call.get("result", {}).get("usage")
        if isinstance(direct_usage, dict) and isinstance(nested_usage, dict) and direct_usage != nested_usage:
            raise ValueError("Conflicting provider usage within returned response wrapper")
        usage = direct_usage if isinstance(direct_usage, dict) else nested_usage
        usage = usage if isinstance(usage, dict) else {}
        if index in indexed and indexed[index] != usage:
            raise ValueError("Conflicting provider usage for the same ledger attempt")
        indexed[index] = usage
    counters = {}
    for key in ("cached_tokens", "cache_write_tokens"):
        values = [usage.get("prompt_tokens_details", {}).get(key) for usage in indexed.values()]
        valid = [
            value
            for value in values
            if not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
        ]
        counters[key] = {
            "provider_reported_known_subtotal": sum(valid),
            "counter_present_calls": len(valid),
            "counter_missing_calls": len(values) - len(valid),
            "complete_counter_total": sum(valid)
            if len(valid) == len(values) and ledger_attempts == len(values)
            else None,
        }
    return {
        "unique_fresh_returned_attempts": len(indexed),
        "ledger_attempts": ledger_attempts,
        "all_attempt_usage_coverage": len(indexed) == ledger_attempts and not unattributed and not unknown_freshness,
        "replayed_records_excluded": replayed,
        "unknown_freshness_records_excluded": unknown_freshness,
        "unattributed_records_excluded": unattributed,
        "counters": counters,
        "scope": "Provider-reported prompt cache counters; missing counters unknown; no local replay claim",
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "Unmeasured"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(_fmt(value) for value in row) + " |" for row in rows),
    ]


def render(runs: list[dict[str, Any]], pending: list[str]) -> str:
    """Keep observed quality, original/reconciled accounting and incremental work separate."""
    lines = [
        "# P003 decision-model progress",
        "",
        "These tables read completed independently verified DEV evaluations. All intended pages remain in "
        "quality/error denominators. Single runs do not establish hosted repeat confidence. "
        "Historical candidate generation and newly measured incremental work are separate.",
        "",
    ]
    confirmed_runs = [r for r in runs if r.get("decision_confirmed_quality") is not None]
    if confirmed_runs:
        lines += [
            "Primary candidate quality includes only model-selected complete crop states. Abstained, failed and "
            "identical no-question regions receive no model credit; full intended denominators remain. "
            "Historical retained pipeline quality follows separately.",
            "",
        ]
        lines += _table(
            [
                "Run",
                "Model-confirmed strict cells",
                "Complete tables",
                "Missing tables",
                "Extra tables",
                "Negative FP",
                "Decision quality errors",
                "Exact positive pages",
            ],
            [
                [
                    r["name"],
                    f"{q['strict_exact_cells']}/{q['expected_cells']}",
                    f"{q['complete_tables']}/{q['expected_tables']}",
                    q["missing_tables"],
                    q["false_positive_tables"],
                    f"{q['false_positive_page']}/{q['negative_page']}",
                    q["all_page_errors"],
                    r["decision_confirmed_quality"]["exact_positive_pages"],
                ]
                for r in confirmed_runs
                for q in [r["decision_confirmed_quality"]["scores"]]
            ],
        )
        lines += ["Retained pipeline output quality (including historical fallback outputs):", ""]
    composed_runs = [r for r in runs if r.get("successful_incremental_composition_quality") is not None]
    if composed_runs:
        lines += [
            "Successful incremental ownership composition, including deterministic geometry and protected source. "
            "Failed, skipped and no-question baseline pages receive no composition credit. "
            "This is not model-only attribution.",
            "",
        ]
        lines += _table(
            [
                "Run",
                "Composed strict cells",
                "Complete tables",
                "Missing / extra",
                "Negative FP",
                "Incremental failures",
            ],
            [
                [
                    r["name"],
                    f"{q['strict_exact_cells']}/{q['expected_cells']}",
                    f"{q['complete_tables']}/{q['expected_tables']}",
                    f"{q['missing_tables']} / {q['false_positive_tables']}",
                    f"{q['false_positive_page']}/{q['negative_page']}",
                    q["all_page_errors"],
                ]
                for r in composed_runs
                for q in [r["successful_incremental_composition_quality"]["scores"]]
            ],
        )
        lines += ["Legacy retained pipeline output quality follows separately.", ""]
    quality = []
    for run in runs:
        scores = run["scores"]
        quality.append(
            [
                run["name"],
                run["config"].get("generation_model", run["config"].get("model", "native")),
                ", ".join(
                    f"{key}={run['config'][key]}"
                    for key in (
                        "processor",
                        "acquisition",
                        "threshold",
                        "treatment",
                        "preset",
                        "transcription_representation",
                        "transcription_wire_schema",
                        "image_edge",
                        "image_mode",
                        "image_visibility",
                        "gate_image",
                        "gate_image_edge",
                        "gate_packet",
                        "gate_image_mode",
                        "gate_instructions",
                        "evidence_mode",
                        "evidence_max_bytes",
                        "geometry_first",
                        "ownership_protocol",
                        "chunked_inventory",
                        "topology_evidence",
                        "band_mode",
                        "boundary_words",
                        "crossed_tables",
                    )
                    if key in run["config"]
                ),
                f"{run['operational_pages']}/{run['intended_pages']}",
                run["errors"],
                f"{scores.get('complete_tables', 0)}/{scores.get('expected_tables', 0)}",
                f"{scores.get('strict_exact_cells', 0)}/{scores.get('expected_cells', 0)}",
                scores.get("correct_text_cells"),
                scores.get("correct_structure_cells"),
                scores.get("missing_tables"),
                scores.get("false_positive_tables"),
                f"{scores.get('false_positive_page', 0)}/{scores.get('negative_page', 0)}",
                run["exact_positive_pages"],
            ]
        )
    lines += _table(
        [
            "Run",
            "Model",
            "Treatment",
            "Outputs/intended",
            "Errors",
            "Complete tables",
            "Strict cells",
            "Text cells",
            "Structure cells",
            "Missing tables",
            "Extra tables",
            "Negative FP",
            "Exact positive pages",
        ],
        quality,
    )
    decision_runs = [r for r in runs if r.get("decision_evidence") is not None]
    if decision_runs:
        lines += [
            "",
            "Fresh model decisions are separate from retained pipeline outputs. A valid unresolved "
            "response is an abstention, not a model-selected output. Served model version aliases are retained "
            "as provenance; they alone do not establish model substitution.",
            "",
        ]
        lines += _table(
            [
                "Run",
                "Fresh attempts",
                "Returned calls",
                "Parsed selected choices",
                "Parsed abstentions",
                "Committed model crops",
                "Fully chosen candidate pages",
                "Pages retaining output on abstention",
                "Requested-model mismatches",
                "Explicit retry attempts",
            ],
            [
                [
                    r["name"],
                    d["fresh_ledger_attempts"],
                    d["fresh_returned_calls"],
                    d.get("parsed_selected_choices"),
                    d.get("parsed_unresolved_abstentions"),
                    d.get("committed_model_crop_choices"),
                    d.get("fully_chosen_incremental_pages"),
                    d.get("pages_with_unresolved_baseline_retention"),
                    d["requested_model_mismatch_attempts"],
                    d["explicit_retry_attempts"],
                ]
                for r in decision_runs
                for d in [r["decision_evidence"]]
            ],
        )
    lines += [
        "",
        "Full-pipeline rates count verified operational outputs. Cost overlays leave original report "
        "costs visible. Transport concurrency is part of the treatment; contended runs are separate evidence.",
        "",
    ]
    rates = []
    for run in runs:
        config, accounting = run["config"], run["costs"]
        overlay = run.get("cost_reconciliation", {}).get("reconciled", {})
        concurrency = config.get("transport_concurrency", config.get("workers", run["resources"].get("concurrency", 1)))
        rates.append(
            [
                run["name"],
                run["evaluation_scope"],
                f"serial ({concurrency})" if concurrency == 1 else f"contended ({concurrency})",
                run.get("pages_per_minute"),
                run.get("pages_per_api_usd"),
                accounting.get("effective_api_usd"),
                accounting.get("accounted_usd_including_reservations"),
                overlay.get("effective_api_usd"),
                run.get("reconciled_pages_per_api_usd"),
            ]
        )
    lines += _table(
        [
            "Run",
            "Measured scope",
            "Transport",
            "Pages/min",
            "Original pages/APIUSD",
            "Original effective USD",
            "Original accounted incl reserves USD",
            "Reconciled effective USD",
            "Reconciled pages/APIUSD",
        ],
        rates,
    )
    incremental = [run for run in runs if run["evaluation_scope"] != "complete pipeline"]
    if incremental:
        lines += ["", "Incremental processing rates exclude historical baseline generation.", ""]
        lines += _table(
            [
                "Run",
                "Repair attempted pages/min",
                "Repair attempted pages/APIUSD",
                "Ranking processed pages/min",
                "Ranking processed pages/APIUSD",
            ],
            [
                [
                    r["name"],
                    *(
                        r.get(key)
                        for key in (
                            "incremental_attempted_pages_per_minute",
                            "incremental_attempted_pages_per_api_usd",
                            "incremental_ranking_pages_processed_per_minute",
                            "incremental_ranking_pages_processed_per_api_usd",
                            "incremental_admission_intended_pages_per_minute",
                            "incremental_admission_valid_pages_per_minute",
                            "incremental_admission_intended_pages_per_api_usd",
                            "incremental_admission_valid_pages_per_api_usd",
                            "incremental_selection_questions_per_minute",
                            "incremental_selection_questions_per_api_usd",
                        )
                    ),
                ]
                for r in incremental
            ],
        )
    lines += [
        "",
        "CPU/RSS observations retain their process scopes; worker RSS peaks are never added to parent peaks.",
        "",
    ]
    resources = []
    for run in runs:
        metrics = run["resources"]
        resources.append(
            [
                run["name"],
                "parent",
                metrics.get("wall_seconds"),
                metrics.get("cpu_seconds"),
                metrics.get("peak_rss_bytes", metrics.get("peak_sampled_rss_bytes")),
                metrics.get("measurement_scope", metrics.get("measurement", "retained run process scope")),
            ]
        )
        worker = metrics.get("layout_detector_worker")
        if worker:
            initialization = worker.get("initialization", {}).get("initialization", {})
            resources.append(
                [
                    run["name"],
                    "detector worker initialization",
                    initialization.get("wall_seconds"),
                    initialization.get("cpu_seconds"),
                    initialization.get("peak_sampled_rss_bytes"),
                    initialization.get("measurement", worker.get("scope")),
                ]
            )
            requests = [row["metrics"] for row in worker.get("requests", [])]
            if requests:
                resources.append(
                    [
                        run["name"],
                        "detector worker request intervals",
                        sum(row["wall_seconds"] for row in requests)
                        if all("wall_seconds" in row for row in requests)
                        else None,
                        sum(row["cpu_seconds"] for row in requests)
                        if all("cpu_seconds" in row for row in requests)
                        else None,
                        max(
                            (row["peak_sampled_rss_bytes"] for row in requests if "peak_sampled_rss_bytes" in row),
                            default=None,
                        ),
                        f"{len(requests)} retained single-worker request intervals; "
                        "sum recorded interval wall/CPU; max sampled RSS. " + worker.get("scope", ""),
                    ]
                )
    lines += _table(
        ["Run", "Process", "Wall seconds", "CPU seconds", "Peak RSS bytes", "Measurement scope/evidence"], resources
    )
    lines += [
        "",
        "Provider cache counters are unmeasured in these evaluation-only inputs unless explicitly retained "
        "as provider-reported usage. No local replay or cache-hit claim is inferred from latency or cost.",
        "",
    ]
    cache_rows = []
    for run in runs:
        usages = [
            ("current measured stage", run.get("provider_cache_usage")),
            *(
                (f"historical baseline {index}", usage)
                for index, usage in enumerate(run.get("historical_provider_cache_usage", []))
            ),
        ]
        if run.get("retained_transcript_provider_cache_usage") is not None:
            usages.append(("historical retained ownership decisions", run["retained_transcript_provider_cache_usage"]))
        for scope, usage in usages:
            if usage is None:
                cache_rows.append([run["name"], scope, None, None, None, None, None, None])
                continue
            counters = usage["counters"]
            cached, written = counters["cached_tokens"], counters["cache_write_tokens"]
            cache_rows.append(
                [
                    run["name"],
                    scope,
                    f"{usage['unique_fresh_returned_attempts']}/{usage['ledger_attempts']}",
                    cached["provider_reported_known_subtotal"] if cached["counter_present_calls"] else None,
                    written["provider_reported_known_subtotal"] if written["counter_present_calls"] else None,
                    cached["counter_missing_calls"],
                    written["counter_missing_calls"],
                    usage["all_attempt_usage_coverage"],
                ]
            )
    lines += _table(
        [
            "Run",
            "Cache scope",
            "Observed returned/all attempts",
            "Reported read tokens subtotal",
            "Reported write tokens subtotal",
            "Read counter missing calls",
            "Write counter missing calls",
            "All-attempt usage coverage",
        ],
        cache_rows,
    )
    lines.append("")
    for run in runs:
        lines.append(
            f"- `{run['name']}`: evaluation `{run['evaluation_sha256']}`; report `{run['report_sha256']}`; "
            f"failures `{json.dumps(run.get('failure_categories', {}), sort_keys=True)}`; "
            f"transport `{json.dumps(run.get('returned_call_transport_failures', {}), sort_keys=True)}`."
        )
        provenance = run.get("baseline_provenance") or {}
        baseline_hashes = [baseline.get("report_sha256") for baseline in provenance.get("candidate_baselines", [])]
        if provenance.get("report_sha256"):
            baseline_hashes.append(provenance["report_sha256"])
        if baseline_hashes:
            lines.append(
                "  Historical baseline report hashes: " + ", ".join(f"`{value}`" for value in baseline_hashes) + "."
            )
        overlay = run.get("cost_reconciliation")
        if overlay:
            lines.append(
                "  Verified accounting sidecar `" + overlay.get("sidecar_sha256", "unmeasured") + "`; "
                "original report `" + overlay.get("original_report_sha256", run["report_sha256"]) + "`."
            )
    if pending:
        lines += ["", "Pending completed evaluation: " + ", ".join(f"`{Path(p).name}`" for p in pending) + "."]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Generate progress from a frozen explicit run list without discovering artifact directories."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True, help="Explicit P003 artifact base directory")
    parser.add_argument("--run", type=Path, action="append", help="Explicit run directory or evaluation JSON; repeat")
    parser.add_argument("--plan", type=Path, help="Explicit JSON list of run paths; no automatic discovery")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    requested = args.run or []
    if args.plan:
        plan = json.loads(guard_path(args.plan).read_bytes())
        if not isinstance(plan, list) or any(not isinstance(value, str) for value in plan):
            parser.error("Progress plan must be a JSON list of explicit run paths")
        requested.extend(Path(value) for value in plan)
    paths = [p if p.is_absolute() else args.directory / p for p in requested or map(Path, KNOWN_RUNS)]
    runs, pending = load_evaluations(paths, report_directory=guard_path(args.directory))
    output = guard_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(runs, pending))


if __name__ == "__main__":
    main()
