"""Root-local DEV scoring of returned source-only remote worker outputs.

References are opened only after source, staged packet and attempt identities
are verified. This reporter never connects to a host or transfers references.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from bench.lowlevel_run import CHOICES, parse_response, score

MAX_JSON_BYTES = 16 * 1024 * 1024
PROTECTED_NAMES = {"heldout-silver", "silver-heldout-v1"}


def _dev(path: str | Path) -> Path:
    value = Path(path)
    if PROTECTED_NAMES.intersection(value.parts):
        message = "protected source paths are excluded from DEV reporting"
        raise ValueError(message)
    resolved = value.resolve()
    if PROTECTED_NAMES.intersection(resolved.parts):
        message = "protected source paths are excluded from DEV reporting"
        raise ValueError(message)
    return resolved


def _read(path: Path) -> bytes:
    with path.open("rb") as handle:
        payload = handle.read(MAX_JSON_BYTES + 1)
    if len(payload) > MAX_JSON_BYTES:
        message = "report input exceeds the bounded file admission"
        raise ValueError(message)
    return payload


def _json(path: Path) -> Any:  # noqa: ANN401
    return json.loads(_read(path))


def _jsonl(path: Path, *, allow_incomplete_tail: bool) -> tuple[list[dict[str, Any]], bool]:
    rows = []
    raw_lines = _read(path).splitlines()
    for index, raw in enumerate(raw_lines):
        try:
            rows.append(json.loads(raw))
        except (json.JSONDecodeError, UnicodeDecodeError):
            if allow_incomplete_tail and index == len(raw_lines) - 1:
                return rows, True
            raise
    return rows, False


def _path(base: Path, value: str) -> Path:
    path = _dev(base / value)
    if not path.is_relative_to(base):
        message = "source artifact paths must remain inside their frozen directory"
        raise ValueError(message)
    return path


def _verified(path: Path, digest: str) -> bytes:
    payload = _read(path)
    if hashlib.sha256(payload).hexdigest() != digest:
        message = f"artifact hash differs: {path.name}"
        raise ValueError(message)
    return payload


def _positive(value: Any) -> float | None:  # noqa: ANN401
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return None
    return float(value)


def _choice(response: dict[str, Any]) -> dict[str, Any]:
    """Validate native distributions or explicit stock generated labels."""
    if response.get("backend") != "stock-vllm-json":
        return parse_response(response, 1)[0]
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != {"q0"}:
        message = "stock response question inventory differs"
        raise ValueError(message)
    answer = answers["q0"]
    if (
        not isinstance(answer, dict)
        or answer.get("type") != "choice"
        or answer.get("choice") not in CHOICES
        or "probabilities" in answer
        or "confidence" in answer
    ):
        message = "stock response must contain an admitted label without invented probabilities"
        raise ValueError(message)
    return {"choice": answer["choice"], "probabilities": None, "calibration": "unavailable: generated label"}


def evaluate(  # noqa: C901, PLR0913, PLR0912
    source_dir: str | Path,
    source_index: str | Path,
    worker_output: str | Path,
    *,
    model: str,
    packets: str | Path,
    transport_model: str | None = None,
    rental_cost_usd: float | None = None,
    rental_cost_scope: str = "whole-run",
    allocated_cost_usd: float | None = None,
    allocation_method: str | None = None,
) -> dict[str, Any]:
    """Verify all source artifacts before locally reading DEV references.

    An optional transport override admits changing only body.model, retaining
    both original/source and staged hashes. Planned per-arm references remain
    the denominator even when a pilot returns only a subset of the 24 regions.
    Allocated model cost can be split across arms only by explicit measured
    inference-wall-share; whole-run rental facts are otherwise not attributed.
    """
    for cost in (rental_cost_usd, allocated_cost_usd):
        if cost is not None and (isinstance(cost, bool) or not math.isfinite(cost) or cost < 0):
            message = "cost must be finite, nonnegative or unknown"
            raise ValueError(message)
    if rental_cost_scope not in {"whole-run", "marginal-estimate"}:
        message = "rental cost scope must distinguish whole-run from marginal estimates"
        raise ValueError(message)
    if allocated_cost_usd is not None and allocation_method != "inference-wall-share":
        message = "allocated model cost requires explicit inference-wall-share method"
        raise ValueError(message)
    source = _dev(source_dir)
    output = _dev(worker_output)
    index = _json(_dev(source_index))
    manifest = _json(source / "manifest.json")
    if manifest.get("experiment") != "L015" or not isinstance(index, list):
        message = "report requires the frozen L015 DEV source and a list source index"
        raise ValueError(message)
    pages = {page["id"]: page for page in manifest["pages"]}
    source_records = {row["request"]: row for row in manifest["records"]}
    staged_manifest = _dev(packets)
    staged = {row["id"]: row for row in _json(staged_manifest)["records"]}
    by_id: dict[str, dict[str, Any]] = {}
    observations = {}
    for row in index:
        source_row = source_records[row["request"]]
        for key in ("sha256", "model", "arm", "page_ids", "image_file", "image_sha256"):
            if row[key] != source_row[key]:
                message = "source index differs from the frozen L015 inventory"
                raise ValueError(message)
        if row["id"] in by_id or len(row["page_ids"]) != 1:
            message = "source index requires unique IDs and singleton regions"
            raise ValueError(message)
        original = _verified(_path(source, row["request"]), row["sha256"])
        image_bytes = _verified(_path(source, row["image_file"]), row["image_sha256"])
        staged_row = staged[row["id"]]
        staged_bytes = _read(_path(staged_manifest.parent, staged_row["request_file"]))
        if staged_bytes != original:
            source_body = json.loads(original)
            staged_body = json.loads(staged_bytes)
            source_body["model"] = transport_model
            if transport_model is None or staged_body != source_body:
                message = "staged request differs beyond the declared model-only transport override"
                raise ValueError(message)
        if len(staged_row["image_files"]) != 1:
            message = "L015 staging must retain exactly one source crop"
            raise ValueError(message)
        if _read(_path(staged_manifest.parent, staged_row["image_files"][0])) != image_bytes:
            message = "staged image differs from the frozen source crop"
            raise ValueError(message)
        page_id = row["page_ids"][0]
        page = pages[page_id]
        if page_id not in observations:
            _verified(_path(source, page["source_file"]), page["source_sha256"])
            observations[page_id] = json.loads(
                _verified(_path(source, page["observation_file"]), page["observation_sha256"])
            )
        by_id[row["id"]] = dict(row, staged_request_sha256=hashlib.sha256(staged_bytes).hexdigest())
    if set(staged) != set(by_id):
        message = "staged/source ID inventory differs"
        raise ValueError(message)
    status = _json(output / "status.json")
    checkpoint = status.get("status") != "complete"
    events: list[dict[str, Any]] = []
    incomplete_tail = False
    attempts = output / "attempts.jsonl"
    if attempts.exists():
        events, incomplete_tail = _jsonl(attempts, allow_incomplete_tail=checkpoint)
    started, completed = {}, {}
    for returned in events:
        if returned["id"] not in by_id:
            message = "returned attempt ID is outside the frozen source inventory"
            raise ValueError(message)
        if returned["event"] == "attempt_started":
            if returned["id"] in started:
                message = "duplicate fresh attempt or retry in worker output"
                raise ValueError(message)
            started[returned["id"]] = returned
        elif returned["event"] == "attempt_completed":
            if returned["id"] not in started or returned["id"] in completed:
                message = "completion has no unique prior start event"
                raise ValueError(message)
            if returned.get("request_sha256") != by_id[returned["id"]]["staged_request_sha256"]:
                message = "returned request hash differs from verified staged bytes"
                raise ValueError(message)
            completed[returned["id"]] = returned
        else:
            message = "unknown worker event"
            raise ValueError(message)
    # This is the first scorer-reference access. It remains entirely root-local.
    targets = json.loads(_verified(source / "private-targets.json", manifest["targets_sha256"]))
    targets_by_id = {row["id"]: row for row in targets}
    groups: dict[str, dict[str, Any]] = {}
    results = []
    for source_id, row in by_id.items():
        target = targets_by_id[row["page_ids"][0]]
        arm = row["arm"]
        group = groups.setdefault(
            arm,
            {
                "model": model,
                "arm": arm,
                "planned_regions": 0,
                "known_denominator": 0,
                "ambiguous_denominator": 0,
                "known_correct": 0,
                "ambiguous_abstentions": 0,
                "attempted_regions": 0,
                "completed_regions": 0,
                "schema_failures": 0,
                "worker_failures": 0,
                "pending_attempts": 0,
                "known_completed": 0,
                "ambiguous_completed": 0,
                "inference_seconds": 0.0,
                "inference_duration_complete": True,
                "inference_cpu_seconds": 0.0,
                "inference_cpu_duration_complete": True,
                "peak_rss_bytes": None,
                "cuda_peak_allocated_bytes": None,
                "cuda_peak_reserved_bytes": None,
            },
        )
        group["planned_regions"] += 1
        group["ambiguous_denominator" if target["expected"] == "unresolved" else "known_denominator"] += 1
        if source_id not in started:
            continue
        group["attempted_regions"] += 1
        event = completed.get(source_id)
        if event is None:
            group["pending_attempts"] += 1
            group["inference_duration_complete"] = False
            group["inference_cpu_duration_complete"] = False
            continue
        duration = _positive(event.get("inference_wall_seconds"))
        if duration is None:
            group["inference_duration_complete"] = False
        else:
            group["inference_seconds"] += duration
        cpu = event.get("inference_cpu_seconds")
        if isinstance(cpu, bool) or not isinstance(cpu, (int, float)) or not math.isfinite(cpu) or cpu < 0:
            group["inference_cpu_duration_complete"] = False
        else:
            group["inference_cpu_seconds"] += cpu
        for label, value in (
            ("peak_rss_bytes", event.get("peak_rss_bytes")),
            ("cuda_peak_allocated_bytes", event.get("cuda", {}).get("peak_allocated_bytes")),
            ("cuda_peak_reserved_bytes", event.get("cuda", {}).get("peak_reserved_bytes")),
        ):
            if value is not None:
                group[label] = max(group[label] or 0, value)
        if event.get("status") != "ok":
            group["worker_failures"] += 1
            continue
        try:
            parsed = _choice(event["response"])
            scored = score(observations[row["page_ids"][0]], target, parsed["choice"])
        except (ValueError, TypeError, KeyError) as error:
            group["schema_failures"] += 1
            results.append({"id": source_id, "arm": arm, "status": "schema_error", "error": str(error)})
            continue
        group["completed_regions"] += 1
        group["known_completed" if scored["answerable"] else "ambiguous_completed"] += 1
        group["known_correct"] += int(scored["answerable"] and scored["choice_correct"])
        group["ambiguous_abstentions"] += int(scored["ambiguous_abstention"])
        results.append(
            {
                "id": source_id,
                "arm": arm,
                "status": "ok",
                "parsed": parsed,
                "score": scored,
                "native_response": event["response"],
            }
        )
    total_seconds = sum(row["inference_seconds"] for row in groups.values())
    complete_durations = all(row["inference_duration_complete"] for row in groups.values())
    for group in groups.values():
        duration = group["inference_seconds"] if group["inference_duration_complete"] else None
        group["regions_per_inference_minute"] = 60 * group["completed_regions"] / duration if duration else None
        group["allocated_usd"] = None
        group["regions_per_allocated_usd"] = None
        if allocated_cost_usd is not None and complete_durations and total_seconds > 0:
            group["allocated_usd"] = allocated_cost_usd * group["inference_seconds"] / total_seconds
            if group["allocated_usd"] > 0:
                group["regions_per_allocated_usd"] = group["completed_regions"] / group["allocated_usd"]
    gpu_samples = output / "gpu-samples.jsonl"
    samples, incomplete_gpu_tail = (
        _jsonl(gpu_samples, allow_incomplete_tail=checkpoint) if gpu_samples.exists() else ([], False)
    )
    return {
        "experiment": "L015-remote-dev",
        "model": model,
        "groups": list(groups.values()),
        "results": results,
        "source_manifest_sha256": hashlib.sha256(_read(source / "manifest.json")).hexdigest(),
        "source_index_sha256": hashlib.sha256(_read(_dev(source_index))).hexdigest(),
        "transport_model_override": transport_model,
        "worker_status": status,
        "checkpoint": checkpoint,
        "incomplete_final_log_line": incomplete_tail or incomplete_gpu_tail,
        "gpu_sample_count": len(samples),
        "gpu_available_samples": sum(row.get("raw_csv") is not None for row in samples),
        "gpu_sampling_scope": "device-wide utilization/VRAM, nominal one-second interval",
        "rental_cost_usd": rental_cost_usd,
        "rental_cost_scope": rental_cost_scope,
        "allocated_cost_usd": allocated_cost_usd,
        "allocation_method": allocation_method,
        "full_page_pages_per_minute": None,
        "full_page_pages_per_usd": None,
        "scope": (
            "one supplied two-chunk region per authored source page; "
            "conditional relationship decisions, not full-page extraction"
        ),
    }


def markdown(evaluation: dict[str, Any]) -> str:
    """Format planned denominators, partial coverage and measured region rates."""
    lines = [
        f"# Remote DEV decisions: {evaluation['model']}",
        "",
        evaluation["scope"] + ".",
        f"Report state: {'partial checkpoint' if evaluation['checkpoint'] else 'completed worker output'}.",
        (
            "Single-source authored references; external model benchmarks are not this PDF score. "
            "Unattempted regions remain in planned denominators. Full-page throughput and pages/USD are unavailable."
        ),
        "",
        (
            "| Arm | Valid / planned | Known correct | Ambiguous abstain | Schema / worker failures | "
            "Regions/min inference | Regions/allocated USD | Inference CPU s | Peak process RSS MiB | "
            "CUDA allocated / reserved MiB |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def number(value: float | None) -> str:
        return "unmeasured" if value is None else f"{value:.2f}"

    for row in evaluation["groups"]:
        rss = row["peak_rss_bytes"] / 2**20 if row["peak_rss_bytes"] is not None else None
        gpu = [
            row[key] / 2**20 if row[key] is not None else None
            for key in ("cuda_peak_allocated_bytes", "cuda_peak_reserved_bytes")
        ]
        cells = [
            row["arm"],
            f"{row['completed_regions']}/{row['planned_regions']}",
            f"{row['known_correct']}/{row['known_denominator']}",
            f"{row['ambiguous_abstentions']}/{row['ambiguous_denominator']}",
            f"{row['schema_failures']} / {row['worker_failures']}",
            number(row["regions_per_inference_minute"]),
            number(row["regions_per_allocated_usd"]),
            number(
                row["inference_cpu_seconds"]
                if row["attempted_regions"] and row["inference_cpu_duration_complete"]
                else None
            ),
            number(rss),
            f"{number(gpu[0])} / {number(gpu[1])}",
        ]
        lines.append("| " + " | ".join(cells) + " |")
    initialization = evaluation["worker_status"].get("initialization", {})
    lines.extend(
        [
            "",
            (
                "Inference timing is adapter predict wall time including native input preprocessing, "
                "not whole-page parsing. "
                "Process CPU/RSS excludes subprocesses; RSS is a lifetime high-water mark. "
                "CUDA peaks are current-device observations."
            ),
            (
                f"GPU samples: {evaluation['gpu_available_samples']}/{evaluation['gpu_sample_count']} available; "
                + evaluation["gpu_sampling_scope"]
                + "."
            ),
            (
                f"Initialization: {number(initialization.get('wall_seconds'))} wall seconds, "
                f"{number(initialization.get('cpu_seconds'))} process CPU seconds. "
                f"Worker process CPU total: {number(evaluation['worker_status'].get('cpu_seconds'))} seconds. "
                f"Worker status: {evaluation['worker_status'].get('status')}."
            ),
            (
                f"Rental cost: {number(evaluation['rental_cost_usd'])} USD ({evaluation['rental_cost_scope']}); "
                f"allocated model cost: {number(evaluation['allocated_cost_usd'])} USD; "
                f"method: {evaluation['allocation_method'] or 'none'}. "
                "Whole-run costs are not silently assigned to individual arms. Zero-cost rates are unavailable."
            ),
            (
                "Source/staged request and PNG bytes were verified before root-local DEV references were read. "
                "This proves staged evidence identity, not that a model used the visual input."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    """Write ignored local JSON and an explicitly requested Markdown report."""
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("source-dir", "source-index", "worker-output", "packets", "model", "markdown"):
        parser.add_argument("--" + argument, required=True)
    parser.add_argument("--transport-model")
    parser.add_argument("--rental-cost-usd", type=float)
    parser.add_argument("--rental-cost-scope", choices=("whole-run", "marginal-estimate"), default="whole-run")
    parser.add_argument("--allocated-cost-usd", type=float)
    parser.add_argument("--allocation-method", choices=("inference-wall-share",))
    options = vars(parser.parse_args())
    report_path = Path(options.pop("markdown"))
    evaluation = evaluate(**options)
    raw = _dev(options["worker_output"]) / "evaluation.json"
    raw.write_text(json.dumps(evaluation, indent=2, allow_nan=False) + "\n")
    report_path.write_text(markdown(evaluation))


if __name__ == "__main__":
    main()
