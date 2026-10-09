"""Root-local constrained DEV reporting of verified fresh PDF image treatments.

Every fresh PNG is reproduced from the frozen PDF before references are read.
Model decisions never receive references. Partial checkpoints preserve all
planned denominators; comparisons use matched page IDs, never a case selector.
"""

# ruff: noqa: C901, PLR0912, PERF401, SLF001 - explicit source/attempt/scoring phases.
from __future__ import annotations

import argparse
import json
import math
import resource
import time
from pathlib import Path
from typing import Any

from bench import remote_image_sizes as fresh
from bench import remote_report
from bench.lowlevel_run import score
from bench.remote_combinations import MODELS
from bench.remote_prompt_packets import _digest, _encode, _fail, _inside, _read, _safe

LIMIT = 16 * 1024 * 1024


def _number(value: Any) -> float | None:  # noqa: ANN401
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
        return None
    return float(value)


def _attempts(output: Path, expected: dict[str, str]) -> dict[str, Any]:
    """Verify every returned identity/hash before any root-local reference access."""
    status_raw = _read(output / "status.json", LIMIT)
    status = json.loads(status_raw)
    checkpoint = status.get("status") != "complete"
    path = output / "attempts.jsonl"
    raw = _read(path, LIMIT) if path.exists() else b""
    lines = raw.splitlines()
    started: dict[str, dict[str, Any]] = {}
    completed: dict[str, dict[str, Any]] = {}
    incomplete_tail = False
    for position, line in enumerate(lines):
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            if checkpoint and position == len(lines) - 1:
                incomplete_tail = True
                break
            raise
        identity = event.get("id")
        if identity not in expected:
            _fail("Worker returned an identity outside the frozen image matrix")
        if event.get("event") == "attempt_started":
            if identity in started:
                _fail("Duplicate fresh attempt/retry is not admitted")
            started[identity] = event
        elif event.get("event") == "attempt_completed":
            if identity not in started or identity in completed:
                _fail("Completion requires a unique prior start")
            if event.get("attempt") != started[identity].get("attempt"):
                _fail("Attempt start/completion indices differ")
            if event.get("request_sha256") != expected[identity]:
                _fail("Returned request hash differs from frozen source-only bytes")
            completed[identity] = event
        else:
            _fail("Unknown worker attempt event")
    if not checkpoint and (set(completed) != set(expected) or incomplete_tail):
        _fail("Complete worker status contradicts the planned completed inventory")
    samples_path = output / "gpu-samples.jsonl"
    samples, gpu_tail = (
        remote_report._jsonl(samples_path, allow_incomplete_tail=checkpoint) if samples_path.exists() else ([], False)
    )
    return {
        "status": status,
        "status_sha256": _digest(status_raw),
        "attempts_sha256": _digest(raw),
        "started": started,
        "completed": completed,
        "checkpoint": checkpoint,
        "incomplete_tail": incomplete_tail or gpu_tail,
        "gpu_samples": len(samples),
        "gpu_available_samples": sum(sample.get("raw_csv") is not None for sample in samples),
    }


def _group(arm: str, rows: list[dict[str, Any]], hourly_usd: float | None) -> dict[str, Any]:
    """Keep quality, planned coverage, measured resources and marginal estimates distinct."""
    known = [row for row in rows if row["expected"] != "unresolved"]
    ambiguous = [row for row in rows if row["expected"] == "unresolved"]
    valid = [row for row in rows if row["status"] == "ok"]
    events = [row["event"] for row in rows if row["event"] is not None]
    wall = [_number(event.get("inference_wall_seconds")) for event in events]
    cpu = [_number(event.get("inference_cpu_seconds")) for event in events]
    pending = any(row["status"] == "pending" for row in rows)
    seconds = (
        sum(value for value in wall if value is not None)
        if events and not pending and all(value is not None for value in wall)
        else None
    )
    cpu_seconds = (
        sum(value for value in cpu if value is not None)
        if events and not pending and all(value is not None for value in cpu)
        else None
    )
    cost = seconds * hourly_usd / 3600 if seconds is not None and hourly_usd is not None else None
    result: dict[str, Any] = {
        "arm": arm,
        "planned_regions": len(rows),
        "known_denominator": len(known),
        "ambiguous_denominator": len(ambiguous),
        "attempted_regions": sum(row["attempted"] for row in rows),
        "returned_regions": len(events),
        "completed_regions": len(valid),
        "known_correct": sum(row["choice"] == row["expected"] for row in known),
        "wrong_known_decisions": sum(row["choice"] not in (None, "unresolved", row["expected"]) for row in known),
        "known_abstentions": sum(row["choice"] == "unresolved" for row in known),
        "ambiguous_abstentions": sum(row["choice"] == "unresolved" for row in ambiguous),
        "ambiguous_decisions": sum(row["choice"] in ("join", "split") for row in ambiguous),
        "worker_failures": sum(row["status"] == "worker_error" for row in rows),
        "schema_failures": sum(row["status"] == "schema_error" for row in rows),
        "pending_attempts": sum(row["status"] == "pending" for row in rows),
        "unattempted_regions": sum(not row["attempted"] for row in rows),
        "inference_seconds": seconds,
        "inference_cpu_seconds": cpu_seconds,
        "regions_per_inference_minute": len(valid) * 60 / seconds if seconds else None,
        "hourly_usd": hourly_usd,
        "marginal_inference_usd_estimate": cost,
        "regions_per_marginal_usd_estimate": len(valid) / cost if cost else None,
        "known_correct_per_marginal_usd_estimate": None,
        "paired_baseline": {
            "arm": "fresh-" + arm.split("-")[1] + "-512",
            "paired_regions": 0,
            "changed_choices": 0,
            "known_improvements": 0,
            "known_regressions": 0,
            "ambiguous_abstention_gains": 0,
            "ambiguous_abstention_losses": 0,
        },
    }
    if cost:
        result["known_correct_per_marginal_usd_estimate"] = result["known_correct"] / cost
    for label, values in (
        ("mean_png_bytes", [_number(row.get("png_bytes")) for row in rows]),
        (
            "native_input_tokens_mean",
            [_number(event.get("response", {}).get("usage", {}).get("input_tokens")) for event in events],
        ),
        (
            "native_output_tokens_mean",
            [_number(event.get("response", {}).get("usage", {}).get("output_tokens")) for event in events],
        ),
    ):
        measured = [value for value in values if value is not None]
        result[label] = sum(measured) / len(measured) if measured and len(measured) == len(rows) else None
        result[label + "_reported_count"] = len(measured)
    for label, accessor in (
        ("peak_rss_bytes", lambda event: event.get("peak_rss_bytes")),
        ("cuda_peak_allocated_bytes", lambda event: event.get("cuda", {}).get("peak_allocated_bytes")),
        ("cuda_peak_reserved_bytes", lambda event: event.get("cuda", {}).get("peak_reserved_bytes")),
    ):
        values = [_number(accessor(event)) for event in events]
        measured = [value for value in values if value is not None]
        result[label] = max(measured) if measured else None
    for row in valid:
        baseline = row["baseline"]
        if baseline is None:
            continue
        pair = result["paired_baseline"]
        pair["paired_regions"] += 1
        pair["changed_choices"] += row["choice"] != baseline["choice"]
        was_correct, now_correct = baseline["choice"] == row["expected"], row["choice"] == row["expected"]
        if row["expected"] == "unresolved":
            pair["ambiguous_abstention_gains"] += now_correct and not was_correct
            pair["ambiguous_abstention_losses"] += was_correct and not now_correct
        else:
            pair["known_improvements"] += now_correct and not was_correct
            pair["known_regressions"] += was_correct and not now_correct
    return result


def evaluate(
    directory: Path, output: Path, baseline_output: Path, *, model: str, hourly_usd: float | None = None
) -> dict[str, Any]:
    """Authorize only the frozen image metadata projection, then score DEV locally."""
    started, cpu = time.perf_counter(), time.process_time()
    if model not in MODELS.values() or (hourly_usd is not None and _number(hourly_usd) is None):
        _fail("Unknown engine model or invalid explicit hourly rate")
    directory, output, baseline_output = map(_safe, (directory, output, baseline_output))
    # Every fresh PNG/source/state is checked before any reference-accessing scorer runs.
    provenance = fresh.verify(directory)
    expected = {row["id"]: row["projected_request_sha256"] for row in provenance["mapping"]}
    returned = _attempts(output, expected)
    source, original_index, original_packets = (
        Path(provenance[key]) for key in ("source_directory", "source_index", "source_packets")
    )
    original_rows = json.loads(_read(original_index, LIMIT))
    baseline_events = _attempts(baseline_output, {row["id"]: row["sha256"] for row in original_rows})
    baseline = remote_report.evaluate(
        source, original_index, baseline_output, model=model, packets=original_packets / "manifest.json"
    )
    manifest = json.loads(_read(source / "manifest.json", LIMIT))
    # Authorized root-local target access follows BOTH source and worker identity verification.
    targets_raw = _read(source / "private-targets.json", LIMIT)
    if _digest(targets_raw) != manifest["targets_sha256"]:
        _fail("Frozen DEV reference hash changed")
    targets = {target["id"]: target for target in json.loads(targets_raw)}
    pages = {page["id"]: page for page in manifest["pages"]}
    if set(targets) != set(pages):
        _fail("DEV reference page inventory differs from frozen sources")
    observations = {
        identity: json.loads(_read(_inside(source, page["observation_file"]), LIMIT))
        for identity, page in pages.items()
    }
    for page_id, target in targets.items():
        score(observations[page_id], target, target["expected"])
    original_by_id = {row["id"]: row for row in original_rows}
    baseline_choices = {
        (original_by_id[row["id"]]["page_ids"][0], row["arm"]): row
        for row in baseline["results"]
        if row["status"] == "ok"
    }
    rows = []
    for mapping in provenance["mapping"]:
        identity, page_id = mapping["id"], mapping["page_id"]
        event = returned["completed"].get(identity)
        attempted = identity in returned["started"]
        status = "pending" if attempted else "unattempted"
        choice, scored, error_type = None, None, None
        if event is not None:
            if event.get("status") != "ok":
                status = "worker_error"
            else:
                try:
                    parsed = remote_report._choice(event["response"])
                    choice = parsed["choice"]
                    scored = score(observations[page_id], targets[page_id], choice)
                    status = "ok"
                except (ValueError, TypeError, KeyError) as error:
                    status, error_type, choice = "schema_error", type(error).__name__, None
        original_arm = "fresh-" + mapping["image_mode"] + "-512"
        prior = baseline_choices.get((page_id, original_arm))
        if prior is not None and prior["score"]["expected"] != targets[page_id]["expected"]:
            _fail("Matched baseline reference differs from frozen relation")
        rows.append(
            {
                "id": identity,
                "page_id": page_id,
                "arm": mapping["arm"],
                "expected": targets[page_id]["expected"],
                "choice": choice,
                "status": status,
                "attempted": attempted,
                "event": event,
                "score": scored,
                "error_type": error_type,
                "baseline": {"choice": prior["parsed"]["choice"]} if prior is not None else None,
                "png_bytes": mapping["png_bytes"],
            }
        )
    groups = [
        _group(f"fresh-{mode}-{edge}", [row for row in rows if row["arm"] == f"fresh-{mode}-{edge}"], hourly_usd)
        for mode in fresh.MODES
        for edge in fresh.EDGES
    ]
    if any(group["planned_regions"] != fresh.SOURCE_COUNT for group in groups):
        _fail("Planned per-arm source inventory differs")
    baseline_results = {row["id"]: row for row in baseline["results"]}
    baseline_rows = []
    for row in original_rows:
        identity, page_id = row["id"], row["page_ids"][0]
        event = baseline_events["completed"].get(identity)
        attempted = identity in baseline_events["started"]
        prior = baseline_results.get(identity)
        status = "pending" if attempted else "unattempted"
        if event is not None:
            status = "worker_error" if event.get("status") != "ok" else "schema_error"
        if prior is not None:
            status = prior["status"]
        baseline_rows.append(
            {
                "arm": row["arm"],
                "expected": targets[page_id]["expected"],
                "choice": prior["parsed"]["choice"] if prior and status == "ok" else None,
                "status": status,
                "attempted": attempted,
                "event": event,
                "baseline": None,
                "png_bytes": row.get("png_bytes"),
            }
        )
    baseline_groups = [
        _group(arm, [row for row in baseline_rows if row["arm"] == arm], hourly_usd)
        for arm in sorted({row["arm"] for row in original_rows})
    ]
    return {
        "schema": 1,
        "experiment": "constrained-fresh-image-size-dev",
        "model": model,
        "groups": groups,
        "results": rows,
        "baseline_groups": baseline_groups,
        "baseline_checkpoint": baseline["checkpoint"],
        "baseline_output": str(baseline_output),
        "baseline_source_manifest_sha256": baseline["source_manifest_sha256"],
        "baseline_worker_status": baseline["worker_status"],
        "fresh_provenance_sha256": _digest(_read(directory / "provenance.json", LIMIT)),
        "fresh_worker_manifest_sha256": provenance["worker_manifest_sha256"],
        "analysis_code_sha256": {
            "reporter": _digest(_read(Path(__file__), LIMIT)),
            "fresh_verifier": _digest(_read(Path(fresh.__file__), LIMIT)),
            "baseline_scorer": _digest(_read(Path(remote_report.__file__), LIMIT)),
        },
        "worker_status": returned["status"],
        "checkpoint": returned["checkpoint"],
        "incomplete_final_log_line": returned["incomplete_tail"],
        "worker_attempts_sha256": returned["attempts_sha256"],
        "worker_status_sha256": returned["status_sha256"],
        "planned_regions": len(rows),
        "valid_regions": sum(row["status"] == "ok" for row in rows),
        "gpu_sample_count": returned["gpu_samples"],
        "gpu_available_samples": returned["gpu_available_samples"],
        "preparation": json.loads(_read(directory / "preparation.json", LIMIT)),
        "analysis_resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "scope": "one CPU report process; includes source re-render verification; Linux RSS lifetime peak",
        },
        "cost_scope": "explicit hourly rate times retained adapter inference seconds /3600; marginal occupancy "
        "estimate only, excludes startup/downloads/idle/teardown and actual lifecycle billing",
    }


def _fmt(value: float | None, divisor: float = 1) -> str:
    return "unmeasured" if value is None else f"{value / divisor:.3f}"


def markdown(evaluations: list[dict[str, Any]]) -> str:
    """Compare complete planned cohorts without choosing a winner per reference."""
    lines = [
        "# Fresh remote DEV image sizes",
        "",
        (
            "Fresh PDF source crops at 128/256/384/400/448/500/640 pixels, independently encoded as RGB8, gray8 and "
            "four-level two-bit PNGs. Each arm retains 24 authored supplied-region decisions (16 known, 8 ambiguous); "
            "504 planned inputs per model. These are correlated treatments of the same 24 logical pages, not "
            "independent cases or full-page extraction scores."
        ),
        "",
        (
            "Every fresh PNG was re-rendered from its frozen source PDF and literal state/questions verified before "
            "DEV references were read. All source and returned request hashes were checked. Verification establishes "
            "transport identity, not a model's actual use of images. Missing, failed and unattempted inputs stay "
            "in planned denominators. Native response probabilities are not correctness calibration."
        ),
        "",
    ]
    planned = sum(evaluation["planned_regions"] for evaluation in evaluations)
    valid = sum(evaluation["valid_regions"] for evaluation in evaluations)
    ambiguous = sum(row["ambiguous_denominator"] for evaluation in evaluations for row in evaluation["groups"])
    abstained = sum(row["ambiguous_abstentions"] for evaluation in evaluations for row in evaluation["groups"])
    lines.extend(
        [
            (
                f"Across included runs: {valid}/{planned} valid inputs; {abstained}/{ambiguous} ambiguous "
                "abstentions. Changing size/color is not an established remedy for insufficient-evidence decisions."
            ),
            "",
        ]
    )
    for evaluation in evaluations:
        lines.extend(
            [
                f"## {evaluation['model']}",
                "",
                (
                    f"State: {'checkpoint' if evaluation['checkpoint'] else 'complete'}; "
                    f"{evaluation['valid_regions']}/{evaluation['planned_regions']} valid fresh inputs. "
                    f"Baseline: `{Path(evaluation['baseline_output']).name}` "
                    f"({'checkpoint' if evaluation['baseline_checkpoint'] else 'complete'})."
                ),
                "",
                (
                    "| Arm | Valid/planned | Known correct | Wrong known | Known abstain | Ambiguous abstain | "
                    "Schema/worker errors | Regions/min | CPU s | RSS MiB | GPU alloc/reserved MiB | "
                    "Marginal USD est. |"
                ),
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in evaluation["baseline_groups"]:
            lines.append(
                f"| original {row['arm']} | {row['completed_regions']}/{row['planned_regions']} | "
                f"{row['known_correct']}/{row['known_denominator']} | {row['wrong_known_decisions']} | "
                f"{row['known_abstentions']} | "
                f"{row['ambiguous_abstentions']}/{row['ambiguous_denominator']} | "
                f"{row['schema_failures']}/{row['worker_failures']} | "
                f"{_fmt(row['regions_per_inference_minute'])} | {_fmt(row['inference_cpu_seconds'])} | "
                f"{_fmt(row['peak_rss_bytes'], 2**20)} | "
                f"{_fmt(row['cuda_peak_allocated_bytes'], 2**20)}/{_fmt(row['cuda_peak_reserved_bytes'], 2**20)} | "
                f"{_fmt(row['marginal_inference_usd_estimate'])} |"
            )
        for row in evaluation["groups"]:
            lines.append(
                f"| {row['arm']} | {row['completed_regions']}/{row['planned_regions']} | "
                f"{row['known_correct']}/{row['known_denominator']} | {row['wrong_known_decisions']} | "
                f"{row['known_abstentions']} | {row['ambiguous_abstentions']}/{row['ambiguous_denominator']} | "
                f"{row['schema_failures']}/{row['worker_failures']} | {_fmt(row['regions_per_inference_minute'])} | "
                f"{_fmt(row['inference_cpu_seconds'])} | {_fmt(row['peak_rss_bytes'], 2**20)} | "
                f"{_fmt(row['cuda_peak_allocated_bytes'], 2**20)}/{_fmt(row['cuda_peak_reserved_bytes'], 2**20)} | "
                f"{_fmt(row['marginal_inference_usd_estimate'])} |"
            )
        lines.extend(
            [
                "",
                (
                    "| Fresh arm | Paired with original same-mode512 | Changed choices | Known gains/losses | "
                    "Ambiguous abstention gains/losses |"
                ),
                "|---|---:|---:|---:|---:|",
            ]
        )
        for row in evaluation["groups"]:
            pair = row["paired_baseline"]
            lines.append(
                f"| {row['arm']} | {pair['paired_regions']} | {pair['changed_choices']} | "
                f"{pair['known_improvements']}/{pair['known_regressions']} | "
                f"{pair['ambiguous_abstention_gains']}/{pair['ambiguous_abstention_losses']} |"
            )
        lines.extend(
            [
                "",
                (
                    "| Arm | Mean PNG bytes | Mean native input tokens | Mean native output tokens | "
                    "Regions/marginal USD est. |"
                ),
                "|---|---:|---:|---:|---:|",
            ]
        )
        for row in [*evaluation["baseline_groups"], *evaluation["groups"]]:
            prefix = "original " if row in evaluation["baseline_groups"] else ""
            lines.append(
                f"| {prefix}{row['arm']} | {_fmt(row['mean_png_bytes'])} | "
                f"{_fmt(row['native_input_tokens_mean'])} | {_fmt(row['native_output_tokens_mean'])} | "
                f"{_fmt(row['regions_per_marginal_usd_estimate'])} |"
            )
        status = evaluation["worker_status"]
        lines.extend(
            [
                "",
                (
                    "Timing includes adapter predict and native input preprocessing. CPU/RSS scope is the "
                    "worker process and threads, excluding subprocesses; RSS is a lifetime high-water mark. "
                    "CUDA peaks are maximum recorded attempt counters, not per-arm isolated allocations."
                ),
                (
                    f"GPU samples available: {evaluation['gpu_available_samples']}/{evaluation['gpu_sample_count']}; "
                    f"scope: {status.get('gpu_sample_scope', 'unmeasured')}; "
                    f"nominal interval: {status.get('gpu_sample_interval_seconds', 'unmeasured')} seconds."
                ),
                evaluation["cost_scope"] + ". Full-page pages/USD and lifecycle billed cost are unknown.",
                f"Explicit supplied hourly rate: {_fmt(evaluation['groups'][0]['hourly_usd'])} USD/hour.",
                (
                    "Token means require a reported field on every input; missing fields remain unknown. Native "
                    "output-token fields describe the adapter's usage report, not generated explanation text. "
                    "Token observations alone do not establish a processor resolution floor or provider billing."
                ),
                (
                    "Source-major order puts 128RGB first. Retained inference time includes first-predict lazy warmup; "
                    "these single runs do not isolate steady-state latency. Initialization and idle time are excluded "
                    "from the marginal estimate."
                ),
                (
                    f"Local verification/report CPU: {_fmt(evaluation['analysis_resources']['cpu_seconds'])} s; "
                    f"RSS lifetime peak: {_fmt(evaluation['analysis_resources']['peak_rss_bytes'], 2**20)} MiB."
                ),
                "",
            ]
        )
    lines.extend(
        [
            (
                "A treatment's size and color effects must be assessed across the full frozen matrix. This report "
                "does not select a representation per reference or treat paired improvements as an operational "
                "oracle. No protected held-out inputs were accessed."
            ),
            "",
            (
                "Reproduce with `python -m bench.remote_image_size_report --directory <fresh-freeze> "
                "--run flash=<fresh-output>=<original-output>=1.275 --markdown "
                "bench/results/remote-gpu-image-sizes.md --json <ignored-output>`. Repeat `--run` for each "
                "model with its explicit baseline and supplied hourly rate. This CPU-only command verifies every "
                "fresh PNG before DEV scoring and makes no inference calls."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """CPU-only report; run declarations bind model, fresh output, baseline and hourly rate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="model alias=fresh output=original baseline output=explicit hourly USD",
    )
    parser.add_argument("--markdown", required=True, type=Path)
    parser.add_argument("--json", required=True, type=Path)
    args = parser.parse_args()
    reports = []
    for declaration in args.run:
        name, output, baseline, rate = declaration.split("=")
        reports.append(
            evaluate(args.directory, Path(output), Path(baseline), model=MODELS[name], hourly_usd=float(rate))
        )
    _safe(args.markdown).write_text(markdown(reports))
    _safe(args.json).write_bytes(_encode({"evaluations": reports}))


if __name__ == "__main__":
    main()
