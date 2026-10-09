"""Stage exact L011 source packets and verify native results before DEV scoring.

Source preparation never opens references. Reviewed full-source and admitted-
scope agreement remain separate;24 overlapping regions from one Senate page
are not independent documents or independently adjudicated structural gold.
"""

# ruff: noqa: C901, PLR0912, PLR2004 - explicit complete source/result admissions.
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.lowlevel_natural import ARMS
from bench.lowlevel_natural import verify as source_verify
from bench.lowlevel_run import parse_response
from bench.remote_report import _choice, _dev, _json, _jsonl, _path, _read, _verified

SOURCE_COUNT = 24
BODY_COUNT = SOURCE_COUNT * len(ARMS)


def _fail(message: str) -> None:
    raise ValueError(message)


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_inventory(source: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Verify the original source-only freeze, without matrix/reference access."""
    manifest = source_verify(source)
    if manifest.get("experiment") != "L011-source" or len(manifest["pages"]) != SOURCE_COUNT:
        _fail("Expected original24-region L011 source freeze")
    if len(manifest["records"]) != BODY_COUNT:
        _fail("Expected original96 natural source packets")
    manifest_hash = _digest(_read(source / "manifest.json"))
    rows = []
    for record in manifest["records"]:
        if set(record) != {"request", "sha256", "model", "arm", "page_ids", "body_bytes", "non_image_bytes"}:
            _fail("Natural source records must not include scorer fields")
        raw = _verified(_path(source, record["request"]), record["sha256"])
        body = json.loads(raw)
        if (
            len(body["state"]) != 2
            or not isinstance(body["state"][0], str)
            or body["state"][1].get("type") != "image_url"
        ):
            _fail("Natural canonical image state differs")
        url = body["state"][1]["image_url"]["url"]
        if not url.startswith("data:image/png;base64,"):
            _fail("Natural packet must retain its canonical PNG data URI")
        png = base64.b64decode(url.split(",", 1)[1], validate=True)
        ident = _digest(
            json.dumps(
                ["L011-native", manifest_hash, record["sha256"], record["arm"], record["page_ids"]],
                separators=(",", ":"),
            ).encode()
        )[:24]
        rows.append(
            {"id": ident, "record": record, "request_bytes": raw, "image_bytes": png, "image_sha256": _digest(png)}
        )
    if len({row["id"] for row in rows}) != BODY_COUNT:
        _fail("Natural opaque source identities collide")
    return manifest, rows


def prepare(source_dir: Path, output: Path) -> Path:
    """Freeze exact96 source bodies and PNGs; leave all references root-local."""
    started, cpu = time.monotonic(), time.process_time()
    source = _dev(source_dir)
    destination = _dev(output)
    manifest, rows = source_inventory(source)
    destination.mkdir(parents=True, exist_ok=False)
    records, index = [], []
    for row in rows:
        request = row["id"] + ".json"
        image = row["image_sha256"] + ".png"
        (destination / request).write_bytes(row["request_bytes"])
        image_path = destination / image
        if not image_path.exists():
            image_path.write_bytes(row["image_bytes"])
        records.append({"id": row["id"], "request_file": request, "image_files": [image]})
        index.append({"id": row["id"], **row["record"], "image_sha256": row["image_sha256"]})
    (destination / "manifest.json").write_text(json.dumps({"records": records}, indent=2) + "\n")
    (destination / "source-index.json").write_text(json.dumps(index, indent=2) + "\n")
    (destination / "provenance.json").write_text(
        json.dumps(
            {
                "experiment": "L011-native-source",
                "source_manifest_sha256": _digest(_read(source / "manifest.json")),
                "source_pdf_sha256": manifest["source_sha256"],
                "worker_manifest_sha256": _digest(_read(destination / "manifest.json")),
                "source_index_sha256": _digest(_read(destination / "source-index.json")),
                "request_count": BODY_COUNT,
                "source_regions": SOURCE_COUNT,
                "references_copied": False,
                "projection": "none; original request bytes/model/state/questions/PNG retained",
                "preparation_wall_seconds": time.monotonic() - started,
                "preparation_cpu_seconds": time.process_time() - cpu,
            },
            indent=2,
        )
        + "\n"
    )
    return destination / "manifest.json"


def verify_stage(source: Path, packets: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify all retained stage artifacts against exact source-only packets."""
    manifest, rows = source_inventory(source)
    expected = {row["id"]: row for row in rows}
    provenance = _json(packets.parent / "provenance.json")
    _verified(source / "manifest.json", provenance["source_manifest_sha256"])
    staged = json.loads(_verified(packets, provenance["worker_manifest_sha256"]))
    index = json.loads(_verified(packets.parent / "source-index.json", provenance["source_index_sha256"]))
    if staged.keys() != {"records"} or len(staged["records"]) != BODY_COUNT or len(index) != BODY_COUNT:
        _fail("Natural stage inventory differs")
    expected_index = [{"id": row["id"], **row["record"], "image_sha256": row["image_sha256"]} for row in rows]
    if index != expected_index:
        _fail("Natural source index differs from exact frozen inventory")
    seen = set()
    for row in staged["records"]:
        if set(row) != {"id", "request_file", "image_files"} or row["id"] in seen:
            _fail("Natural worker inventory contains unsupported fields or duplicateIDs")
        seen.add(row["id"])
        original = expected[row["id"]]
        if (
            len(row["image_files"]) != 1
            or _read(_path(packets.parent, row["request_file"])) != original["request_bytes"]
        ):
            _fail("Natural staged source request differs")
        if _read(_path(packets.parent, row["image_files"][0])) != original["image_bytes"]:
            _fail("Natural staged source PNG differs")
    if seen != set(expected):
        _fail("Natural worker/source identities differ")
    return manifest, expected


def verify_events(output: Path, inventory: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify every returned identity and request hash before references."""
    status = _json(output / "status.json")
    path = output / "attempts.jsonl"
    rows, tail = (
        _jsonl(path, allow_incomplete_tail=status.get("status") != "complete") if path.exists() else ([], False)
    )
    started, completed = set(), {}
    for row in rows:
        ident = row["id"]
        if ident not in inventory:
            _fail("Natural returned ID differs from source inventory")
        if row["event"] == "attempt_started":
            if ident in started:
                _fail("Natural duplicate fresh attempt/retry")
            started.add(ident)
        elif row["event"] == "attempt_completed":
            if ident not in started or ident in completed:
                _fail("Natural completion lacks unique prior start")
            if row.get("request_sha256") != inventory[ident]["record"]["sha256"]:
                _fail("Natural returned request hash differs")
            completed[ident] = row
        else:
            _fail("Unknown natural worker event")
    return completed, {
        "worker_status": status,
        "started": len(started),
        "completed": len(completed),
        "incomplete_tail": tail,
    }


def agreement(choice: str, reference: dict[str, Any], arm: str) -> dict[str, bool]:
    """Apply the existing L011 provisional full-source/scoped comparison semantics."""
    scoped = reference["scope_references"][arm.split("-", maxsplit=1)[0]]["choice"]
    return {
        "full_match": choice == reference["choice"],
        "scope_match": choice == scoped,
        "scope_abstention": scoped == "unresolved" and choice == "unresolved",
    }


def warm_rates(summary: dict[str, Any], hourly_rate: float | None) -> dict[str, Any]:
    """Price measured serial warm prediction time; never invent complete missing costs."""
    if hourly_rate is not None and (
        isinstance(hourly_rate, bool) or not math.isfinite(hourly_rate) or hourly_rate <= 0
    ):
        _fail("Hourly rental rate must be finite and positive or unknown")
    seconds = summary["inference_seconds"]
    completed = summary["counts"].get("completed", 0)
    cost = hourly_rate * seconds / 3600 if hourly_rate is not None and seconds is not None else None
    return {
        "hourly_rate_usd": hourly_rate,
        "warm_inference_estimated_usd": cost,
        "warm_region_inputs_per_minute": 60 * completed / seconds if seconds is not None and seconds > 0 else None,
        "warm_region_inputs_per_estimated_usd": completed / cost if cost is not None and cost > 0 else None,
        "cost_scope": (
            "idealized dedicated-GPU warm prediction time; excludes download/load/startup/idle/teardown; not invoice"
        ),
    }


def parse_decision(response: dict[str, Any], *, allow_exploratory_stock: bool = False) -> dict[str, Any]:
    """Admit stock labels only explicitly, without fabricated native probabilities."""
    if response.get("backend") != "stock-vllm-json":
        return parse_response(response, 1)[0]
    if not allow_exploratory_stock:
        _fail("Stock generated labels require explicit exploratory opt-in")
    parsed = _choice(response)
    answer = response["answers"]["q0"]
    if set(answer) - {"type", "choice", "decision"} or answer.get("decision", parsed["choice"]) != parsed["choice"]:
        _fail("Stock label contains unsupported fields or conflicting aliases")
    return {**parsed, "tie_abstention": False}


def concurrent_rates(status: dict[str, Any], completed: int) -> dict[str, Any]:
    """Use measured global lifecycle/span for concurrent throughput, never latency sums."""
    values: dict[str, Any] = {"concurrent": bool(status.get("lanes", 1) > 1)}
    for field in ("wall_seconds", "concurrent_request_span_seconds"):
        value = status.get(field)
        valid = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0
        if valid and isinstance(value, (int, float)):
            values[field] = float(value)
            values[field + "_inputs_per_minute"] = completed * 60 / value
        else:
            values[field] = values[field + "_inputs_per_minute"] = None
    return values


def sampled_resources(output: Path) -> dict[str, Any]:
    """Retain simultaneous union RSS/observed CPU and device-wide GPU samples."""
    sample_path = output / "process-samples.jsonl"
    samples, _ = _jsonl(sample_path) if sample_path.exists() else ([], False)
    gpu, _ = _jsonl(output / "gpu-samples.jsonl") if (output / "gpu-samples.jsonl").exists() else ([], False)
    values = []
    for sample in gpu:
        raw = sample.get("raw_csv")
        if isinstance(raw, str):
            for line in raw.splitlines():
                try:
                    row = [float(value.strip()) for value in line.split(",")]
                except ValueError:
                    continue
                if len(row) == 4 and all(math.isfinite(value) for value in row):
                    values.append(row)
    return {
        "process_sample_count": len(samples),
        "sampled_union_peak_rss_bytes": max((row["rss_sum_bytes"] for row in samples), default=None),
        "sampled_observed_cpu_seconds": max(
            (row["observed_cpu_cumulative_seconds"] for row in samples), default=None
        ),
        "gpu_sample_count": len(gpu),
        "gpu_available_rows": len(values),
        "gpu_mean_utilization_percent": sum(row[1] for row in values) / len(values) if values else None,
        "gpu_peak_device_mib": max((row[2] for row in values), default=None),
        "scope": "nominal 1 s union supervisor/children/optional server; shared RSS may double count; device-wide GPU",
        "cpu_limitations": "pre-observation and unsampled exit CPU unavailable",
    }


def evaluate(  # noqa: PLR0913 - explicit source/reference and opt-in contracts.
    source_dir: Path,
    packets: Path,
    runs: dict[str, Path],
    *,
    references_dir: Path,
    hourly_rates: dict[str, float] | None = None,
    allow_exploratory_stock: bool = False,
) -> dict[str, Any]:
    """Verify complete source/stage/all-model outputs before local DEV references."""
    source, packet_manifest = _dev(source_dir), _dev(packets)
    manifest, inventory = verify_stage(source, packet_manifest)
    returned = {model: verify_events(_dev(path), inventory) for model, path in runs.items()}
    for completed, _status in returned.values():
        if not allow_exploratory_stock and any(
            event.get("response", {}).get("backend") == "stock-vllm-json" for event in completed.values()
        ):
            _fail("Stock generated labels require explicit exploratory opt-in")
    # First reference access: source/stage and every returned model have been checked.
    reference_root = _dev(references_dir)
    reference_manifest = _json(reference_root / "manifest.json")
    if (
        reference_manifest.get("experiment") != "L011"
        or reference_manifest["parent_manifest_sha256"] != _digest(_read(source / "manifest.json"))
        or reference_manifest["pages"] != manifest["pages"]
    ):
        _fail("Natural reviewed matrix differs from original source freeze")
    reviewed = json.loads(
        _verified(reference_root / "private-references.json", reference_manifest["references_sha256"])
    )
    if reviewed["source_manifest_sha256"] != _digest(_read(source / "manifest.json")):
        _fail("Natural reference provenance differs from original source")
    references = {row["id"]: row for row in reviewed["references"]}
    if set(references) != {row["id"] for row in manifest["pages"]}:
        _fail("Natural reference inventory differs")
    models = {}
    for model, (completed, status) in returned.items():
        summaries: list[dict[str, Any]] = []
        for arm in ARMS:
            records = [row for row in inventory.values() if row["record"]["arm"] == arm]
            counts: Counter[str] = Counter()
            choices: Counter[str] = Counter()
            times: list[float] = []
            cpu: list[float] = []
            rss: list[int] = []
            allocated: list[int] = []
            reserved: list[int] = []
            for row in records:
                event = completed.get(row["id"])
                if event is None:
                    counts["missing"] += 1
                    continue
                for key, destination in (("inference_wall_seconds", times), ("inference_cpu_seconds", cpu)):
                    value = event.get(key)
                    if (
                        isinstance(value, (int, float))
                        and not isinstance(value, bool)
                        and math.isfinite(value)
                        and value >= 0
                    ):
                        destination.append(float(value))
                if event.get("peak_rss_bytes") is not None:
                    rss.append(event["peak_rss_bytes"])
                for key, gpu_values in (("peak_allocated_bytes", allocated), ("peak_reserved_bytes", reserved)):
                    value = event.get("cuda", {}).get(key)
                    if value is not None:
                        gpu_values.append(value)
                if event.get("status") != "ok":
                    counts["worker_error"] += 1
                    continue
                try:
                    parsed = parse_decision(event["response"], allow_exploratory_stock=allow_exploratory_stock)
                except (ValueError, TypeError, KeyError):
                    counts["schema_error"] += 1
                    continue
                choice = parsed["choice"]
                choices[choice] += 1
                counts["completed"] += 1
                counts["tie_abstentions"] += parsed["tie_abstention"]
                result = agreement(choice, references[row["record"]["page_ids"][0]], arm)
                counts.update({key: int(value) for key, value in result.items()})
            summaries.append(
                {
                    "arm": arm,
                    "planned": len(records),
                    "counts": dict(counts),
                    "choices": dict(choices),
                    "inference_seconds": sum(times) if len(times) == len(records) else None,
                    "inference_known_seconds": sum(times),
                    "cpu_seconds": sum(cpu) if len(cpu) == len(records) else None,
                    "cpu_known_seconds": sum(cpu),
                    "peak_rss_bytes": max(rss, default=None),
                    "cuda_allocated_bytes": max(allocated, default=None),
                    "cuda_reserved_bytes": max(reserved, default=None),
                }
            )
        worker = status["worker_status"]
        concurrent = concurrent_rates(worker, sum(row["counts"].get("completed", 0) for row in summaries))
        for summary in summaries:
            summary.update(warm_rates(summary, None if concurrent["concurrent"] else (hourly_rates or {}).get(model)))
            if concurrent["concurrent"]:
                summary["warm_region_inputs_per_minute"] = None
        hourly = (hourly_rates or {}).get(model)
        warm_rates({"inference_seconds": None, "counts": {}}, hourly)  # Validate supplied rate independently.
        span = concurrent["concurrent_request_span_seconds"]
        concurrent["hourly_rate_usd"] = hourly
        concurrent["warm_span_estimated_usd"] = span * hourly / 3600 if span and hourly else None
        rate = concurrent["concurrent_request_span_seconds_inputs_per_minute"]
        concurrent["warm_span_inputs_per_estimated_usd"] = rate * 60 / hourly if rate and hourly else None
        models[model] = {
            "summaries": summaries, "status": status, "execution_rates": concurrent,
            "sampled_resources": sampled_resources(_dev(runs[model])),
        }
    return {
        "experiment": "L011-native-dev",
        "exploratory_stock_labels": allow_exploratory_stock,
        "source_regions": SOURCE_COUNT,
        "inputs_per_model": BODY_COUNT,
        "models": models,
        "source_manifest_sha256": _digest(_read(source / "manifest.json")),
        "reference_annotation": reviewed.get("annotation"),
        "scope": "single source-aware provisional review;24 overlapping regions from one Senate page",
    }


def markdown(result: dict[str, Any]) -> str:
    """Report natural reference agreement without claiming independently reviewed gold."""
    lines = [
        "# Natural DEV comparison: explicit exploratory stock labels"
        if result.get("exploratory_stock_labels") else "# Native natural DEV comparison",
        "",
        result["scope"],
        "",
        (
            "Original96 L011 request bodies and PNGs are unchanged. Source preparation read no references; "
            "all staged/returned hashes were verified before references were opened locally. "
            "Full-source reference agreement and admitted-scope agreement are separate measurements."
        ),
        "",
        (
            "| Model | Arm | Valid/planned | Full-source matches | Scope matches | Abstentions | "
            "Inference s | CPU s | RSS MiB |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, output in result["models"].items():
        for row in output["summaries"]:
            count = row["counts"]

            def metric(key: str, row: dict[str, Any] = row) -> str:
                value = row[key]
                return "unknown" if value is None else f"{value:.3f}"

            rss = row["peak_rss_bytes"]
            lines.append(
                f"| {model} | {row['arm']} | {count.get('completed', 0)}/{row['planned']} | "
                f"{count.get('full_match', 0)}/{row['planned']} | {count.get('scope_match', 0)}/{row['planned']} | "
                f"{row['choices'].get('unresolved', 0)} | {metric('inference_seconds')} | {metric('cpu_seconds')} | "
                f"{'unknown' if rss is None else f'{rss / 2**20:.1f}'} |"
            )
    lines += [
        "",
        "| Model | Arm | Rental USD/h | Warm estimated USD | Region inputs/min | Region inputs/estimated USD |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for model, output in result["models"].items():
        for row in output["summaries"]:
            values = [
                row[key]
                for key in (
                    "hourly_rate_usd",
                    "warm_inference_estimated_usd",
                    "warm_region_inputs_per_minute",
                    "warm_region_inputs_per_estimated_usd",
                )
            ]
            cells = ["unknown" if value is None else f"{value:.6g}" for value in values]
            lines.append(f"| {model} | {row['arm']} | " + " | ".join(cells) + " |")
    lines += [
        "",
        (
            "Denominators include failed, missing and malformed outputs. Native tied maxima become unresolved. "
            "No accuracy over independent documents or natural structural gold is claimed. "
            "Scope and fixed-edge resolution "
            "jointly change legibility. Inference wall/CPU covers serial adapter prediction; RSS is process-lifetime "
            "high water, including loading. CUDA allocator peaks and detailed failures remain in JSON; GPU device-wide "
            "utilization is separate. Rental estimates multiply measured serial warm prediction time by the supplied "
            "hourly host rate; they exclude download, loading, startup, idle and teardown. They are idealized "
            "dedicated-GPU estimates, not actual invoices. Inputs/min and inputs/USD count overlapping region inputs, "
            "not independent pages or end-to-end extraction."
        ),
        "",
        f"Source manifest SHA256: `{result['source_manifest_sha256']}`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Prepare source-only artifacts or score explicit returned native outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--packets", type=Path)
    parser.add_argument("--run", action="append", help="model-label=output-directory")
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--references-dir", type=Path)
    parser.add_argument("--allow-exploratory-stock", action="store_true")
    parser.add_argument("--hourly-rate", action="append", default=[], help="model-label=USD-per-hour")
    args = parser.parse_args()
    if args.prepare is not None:
        if args.run or args.packets or args.references_dir:
            parser.error("Preparation cannot read worker results")
        print(prepare(args.source, args.prepare))
    else:
        if not all((args.packets, args.run, args.markdown, args.json, args.references_dir)):
            parser.error("Reporting requires packets, runs, markdown and json")
        runs = {model: Path(path) for model, path in (item.split("=", 1) for item in args.run)}
        rates = {model: float(rate) for model, rate in (item.split("=", 1) for item in args.hourly_rate)}
        result = evaluate(
            args.source, args.packets, runs, references_dir=args.references_dir,
            hourly_rates=rates, allow_exploratory_stock=args.allow_exploratory_stock,
        )
        args.markdown.write_text(markdown(result))
        args.json.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
