"""Verify measured-evidence runs and matched original/identity controls before DEV scoring.

This separate reporting module preserves the frozen evidence builder code hash.
Original controls may be absent for an exploratory model; identity controls must
use exactly the same fresh RGB image and approved prompt, with no added evidence.
"""

# ruff: noqa: C901, PLR0912, PLR0913 - full source/control admission before scoring.
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from bench import remote_ambiguity_evidence as matrix
from bench.remote_prompt_packets import _digest, _encode, _fail, _safe
from bench.remote_prompt_report import events, paired, verify_sources
from bench.remote_prompt_sizes import verify as verify_prompts
from bench.remote_report import _read


def _metrics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = matrix.metrics(cases)
    if any(case.get("event", {}).get("response", {}).get("backend") == "stock-vllm-json" for case in cases):
        result.update(
            inference_cpu_seconds=None,
            inference_cpu_seconds_known_component=None,
            cuda_peak_allocated_bytes=None,
            cuda_peak_reserved_bytes=None,
            resource_scope="HTTP client process; separate model-server resources unmeasured here",
            wall_scope="sum of overlapping HTTP latencies; use retained shard status for batch elapsed",
        )
    return result


def _verify_matrix(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    provenance = json.loads(_read(_safe(directory) / "provenance.json"))
    if provenance.get("experiment") == "source-ambiguity-evidence-transport-v2":
        from bench.remote_ambiguity_transport import verify  # noqa: PLC0415

        return verify(directory)
    return matrix.verify(directory)


def evaluate(
    directory: Path,
    prompt_directory: Path,
    runs: dict[str, Path],
    original_runs: dict[str, Path],
    identity_runs: dict[str, Path],
    *,
    hourly_rates: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Verify every source/projection/run/control before the first reference read."""
    rates = hourly_rates or {}
    if set(rates) - set(runs) or any(
        not isinstance(rate, (int, float)) or isinstance(rate, bool) or not math.isfinite(rate) or rate <= 0
        for rate in rates.values()
    ):
        _fail("Hourly GPU rates must be finite positive numbers for tested models")
    source, admitted = _verify_matrix(directory)
    prompt_source, prompts = verify_prompts(prompt_directory)
    if source != prompt_source or set(runs) - {*matrix.MODELS, *matrix.EXPLORATORY_MODELS}:
        _fail("Matched evidence and prompt source freezes differ")
    if set(original_runs) - set(runs) or set(identity_runs) != set(runs):
        _fail("Control inventory differs from tested models")
    originals, observations = verify_sources(
        Path(source["source_directory"]), Path(source["source_index"]), Path(source["source_packets"]) / "manifest.json"
    )
    fresh_inventory = {row["id"]: {**row, "sha256": row["projected_request_sha256"]} for row in source["mapping"]}
    returned = {model: events(_safe(path), admitted) for model, path in runs.items()}
    original_events = {model: events(_safe(path), fresh_inventory) for model, path in original_runs.items()}
    identity_events = {model: events(_safe(path), prompts) for model, path in identity_runs.items()}
    identities = {row["fresh_id"]: row["id"] for row in prompts.values() if row["variant"] == "identity"}
    if not {row["fresh_id"] for row in admitted.values()} <= set(identities):
        _fail("Identity control source image/size coverage incomplete")
    # First reference read: every source and all five returned/control inventories have passed above.
    source_dir = Path(source["source_directory"])
    manifest = json.loads(_read(source_dir / "manifest.json"))
    raw = _read(source_dir / "private-targets.json")
    if _digest(raw) != manifest["targets_sha256"]:
        _fail("Local DEV target bytes differ")
    targets = {row["id"]: row for row in json.loads(raw)}
    models = {}
    for model, (attempts, status) in returned.items():
        groups = {}
        for edge in matrix.EDGES:
            for pack in matrix.PACKS:
                for prompt in matrix.PROMPTS:
                    entries = [
                        row
                        for row in admitted.values()
                        if row["requested_edge"] == edge and row["pack"] == pack and row["prompt"] == prompt
                    ]
                    cases, baseline = [], []
                    for row in entries:
                        page = originals[row["source_id"]]["row"]["page_ids"][0]
                        obs, target = observations[page], targets[page]
                        cases.append(matrix.scored_case(attempts.get(row["id"]), obs, target))
                        if prompt == "identity":
                            event = identity_events[model][0].get(identities[row["fresh_id"]])
                            baseline.append(matrix.scored_case(event, obs, target))
                        elif model in original_events:
                            baseline.append(
                                matrix.scored_case(original_events[model][0].get(row["fresh_id"]), obs, target)
                            )
                    entry: dict[str, Any] = {"metrics": _metrics(cases), "matched_prompt": prompt}
                    if baseline:
                        entry.update(baseline=_metrics(baseline), paired=paired(baseline, cases))
                    else:
                        entry["missing_control"] = (
                            "No matching fresh-original RGB256/500 control; next-wave preplanned 48."
                        )
                    groups[f"rgb-{edge}/{pack}/{prompt}"] = entry
        batch = status["worker_status"]
        elapsed = batch.get("wall_seconds")
        valid = sum(group["metrics"]["completed"] for group in groups.values())
        measured = isinstance(elapsed, (int, float)) and math.isfinite(elapsed) and elapsed > 0
        rate = rates.get(model)
        models[model] = {
            "groups": groups,
            "batch_metrics": {
                "valid": valid,
                "planned": len(admitted),
                "batch_wall_seconds": elapsed if measured else None,
                "cpu_seconds": batch.get("cpu_seconds"),
                "peak_rss_bytes": batch.get("peak_rss_bytes"),
                "region_inputs_per_minute": valid * 60 / elapsed if measured and valid else None,
                "hourly_gpu_usd": rate,
                "estimated_batch_gpu_usd": elapsed * rate / 3600 if measured and rate is not None and valid else None,
                "region_inputs_per_estimated_usd": valid * 3600 / (elapsed * rate)
                if measured and rate is not None and valid
                else None,
                "cost_scope": (
                    "Observed-batch dedicated GPU equivalent; excludes lifecycle/download/idle; "
                    "not invoice or additive across shared-GPU models."
                ),
                "resource_scope": batch.get("resource_scope", batch.get("cpu_scope", "unavailable")),
                "gpu_allocator": batch.get("cuda") if model not in matrix.EXPLORATORY_MODELS else None,
            },
            "status": status,
            "exploratory": model in matrix.EXPLORATORY_MODELS,
            "identity_control_status": identity_events[model][1],
            "original_control_status": original_events.get(model, (None, None))[1],
        }
    return {
        "experiment": "source-ambiguity-evidence-v1",
        "models": models,
        "scope": "24 authored DEV regions × two image sizes × three evidence packs × two fixed prompts",
        "packet_provenance_sha256": _digest(_read(directory / "provenance.json")),
        "prompt_provenance_sha256": _digest(_read(prompt_directory / "provenance.json")),
        "supplemental_pixel_edge": 640,
        "presentation": json.loads(_read(directory / "provenance.json"))["experiment"],
        "comparison": "Same-source, same-image and same-question controls; only measured evidence differs.",
    }


def markdown(report: dict[str, Any]) -> str:
    """Render complete denominators and matched evidence gains/losses."""
    lines = [
        "# Remote GPU measured ambiguity evidence",
        "",
        report["scope"],
        "",
        (
            "Supplemental pixels use a requested 640-edge fresh source render, independent of model image resolution. "
            "Original text, images, questions and whitelisted measurements passed verification before DEV scoring."
        ),
        "",
        (
            "Presentation: " + report.get("presentation", "source-ambiguity-evidence-v1") + ". "
            "V1 uses original text, image, supplemental text; V2 uses one exact-prefix text segment before the image. "
            "Presentation versions remain separate experiments."
        ),
        "",
        (
            "| Model / treatment | Valid/planned | Known correct | Ambiguous abstention | "
            "Known abstentions | Exact partition | Conserved |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        for key, group in row["groups"].items():
            m = group["metrics"]
            quality = (
                [
                    f"{m['known_correct']}/{m['known_denominator']}",
                    f"{m['ambiguous_abstentions']}/{m['ambiguous_denominator']}",
                    str(m["known_abstentions"]),
                    f"{m['partition_exact']}/{m['planned']}",
                    f"{m['conservation']}/{m['completed']}",
                ]
                if m["completed"]
                else ["N/A"] * 5
            )
            lines.append(f"| {model} / {key} | {m['completed']}/{m['planned']} | " + " | ".join(quality) + " |")
    lines += [
        "",
        (
            "All failed/missing inputs retain planned denominators in JSON. N/A means no valid model inference; "
            "transport failures are not zero model accuracy. Matched controls keep exact image and question wording. "
            "Qwen 9B has identity controls only; 48 original controls remain preplanned for a future wave. "
            "No 512-edge image is substituted."
        ),
        "",
        (
            "| Model / treatment | Control known / ambiguous | Known gains / losses | "
            "Ambiguous gains / losses | Changes | Unpaired |"
        ),
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        for key, group in row["groups"].items():
            if "paired" not in group:
                continue
            base, pair = group["baseline"], group["paired"]
            lines.append(
                f"| {model} / {key} | {base['known_correct']}/{base['known_denominator']} / "
                f"{base['ambiguous_abstentions']}/{base['ambiguous_denominator']} | "
                f"{pair['known_gains']} / {pair['known_losses']} | "
                f"{pair['abstention_gains']} / {pair['abstention_losses']} | "
                f"{pair['choice_changes']} | {pair['unpaired']} |"
            )
    lines += [
        "",
        "| Model / treatment | Inference/HTTP sum s | CPU s | Peak process/client RSS MiB |",
        "|---|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        for key, group in row["groups"].items():
            metric = group["metrics"]
            values = [
                metric[field] if metric["completed"] else None
                for field in ("inference_wall_seconds", "inference_cpu_seconds")
            ]
            wall, cpu = ["unknown" if value is None else f"{value:.3f}" for value in values]
            rss = metric["peak_rss_bytes"]
            lines.append(f"| {model} / {key} | {wall} | {cpu} | {'unknown' if rss is None else f'{rss / 2**20:.1f}'} |")
    lines += [
        "",
        (
            "| Model | Status / valid | Batch wall s | CPU s | Peak RSS MiB | Region inputs/min | "
            "GPU USD/h | Estimated batch USD | Region inputs/estimated USD |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, row in report["models"].items():
        batch = row.get("batch_metrics", {})

        def number(key: str, batch: dict[str, Any] = batch) -> str:
            value = batch.get(key)
            return "N/A" if value is None else f"{value:.4f}"

        rss = batch.get("peak_rss_bytes")
        status = row["status"]["worker_status"].get("status", "unknown")
        lines.append(
            f"| {model} | {status}; {batch.get('valid', 'unknown')}/{batch.get('planned', 'unknown')} | "
            f"{number('batch_wall_seconds')} | {number('cpu_seconds')} | "
            f"{'N/A' if rss is None else f'{rss / 2**20:.1f}'} | {number('region_inputs_per_minute')} | "
            f"{number('hourly_gpu_usd')} | {number('estimated_batch_gpu_usd')} | "
            f"{number('region_inputs_per_estimated_usd')} |"
        )
    lines += [
        "",
        (
            "Rates count repeated region inputs, not independent pages. Batch wall includes native worker "
            "initialization; Qwen HTTP clients exclude external server initialization. Dollar values use the supplied "
            "hourly host quote times observed batch wall: dedicated-GPU-equivalent estimates excluding downloads, "
            "provisioning, idle time and teardown. These are not invoices and cannot be added across companion models "
            "sharing a GPU. Failed pre-inference rows retain measured overhead but inference rates/cost estimates "
            "are N/A. Native CPU/RSS include the model process; Qwen CPU totals cover child clients. Server "
            "CPU/RSS and allocator peaks are unmeasured here. Device monitoring and server-tree samples stay separate."
        ),
        "",
    ]
    lines += [
        "",
        (
            "Native timing includes shared-GPU companion contention; baseline quality is paired but timing "
            "is not a controlled speed comparison. Qwen 9B uses eight concurrent HTTP inputs to a shared server: "
            "summed request latency is not batch elapsed, and client resources do not measure model-server resources. "
            "Group CPU/RSS cover measured model process or HTTP client as labeled. Device-wide GPU monitoring "
            "and allocator peaks are separately retained; partial/missing measurements stay unknown."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Score retained verified source-only experiments; no inference is performed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--prompt-packets", type=Path, required=True)
    parser.add_argument("--run", action="append", required=True, help="model=directory")
    parser.add_argument("--original", action="append", default=[], help="model=fresh-original-directory")
    parser.add_argument("--identity", action="append", required=True, help="model=prompt-screen-directory")
    parser.add_argument("--hourly-rate", action="append", default=[], help="model=USD_per_GPU_hour")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    def paths(items: list[str]) -> dict[str, Path]:
        return {key: Path(value) for key, value in (item.split("=", 1) for item in items)}

    result = evaluate(
        args.packets,
        args.prompt_packets,
        paths(args.run),
        paths(args.original),
        paths(args.identity),
        hourly_rates={key: float(value) for key, value in (item.split("=", 1) for item in args.hourly_rate)},
    )
    _safe(args.json_output).write_bytes(_encode(result))
    _safe(args.markdown_output).write_text(markdown(result))


if __name__ == "__main__":
    main()
