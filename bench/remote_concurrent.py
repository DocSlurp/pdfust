"""Run disjoint source-only worker lanes without duplicating requests or retries.

Shared-server lanes amortize model weights. Native lanes load independent model
copies and require explicit measured memory admission. This module never loads
scorer references; root can score the merged attempts with remote_report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from bench.remote_worker import Sampler, inventory

ADAPTERS = (
    "bench.remote_vllm",
    "bench.remote_intern",
    "bench.remote_clef",
    "bench.remote_pplx",
    "bench.remote_jpt",
    "bench.remote_nimble",
)
GPU_COLUMNS = 4
MAX_LOG_BYTES = 64 * 1024 * 1024
FAILURE_LIMIT = 3


def _write(path: Path, value: Any) -> None:  # noqa: ANN401
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shard(packets: str | Path, output: str | Path, limit: int, lanes: int) -> dict[str, Any]:
    """Freeze exact hardlinked/copied bytes into balanced, nonoverlapping lanes."""
    if lanes not in {1, 2, 4, 8}:
        message = "lanes must be 1, 2, 4 or 8"
        raise ValueError(message)
    source = Path(packets).resolve(strict=True)
    rows = inventory(source, limit)
    if lanes > len(rows):
        message = "every lane must contain at least one source request"
        raise ValueError(message)
    directory = Path(output).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    facts: dict[str, Any] = {
        "schema_version": 1,
        "source_manifest_sha256": _hash(source),
        "lanes": lanes,
        "records": [],
    }
    for lane in range(lanes):
        folder = directory / "shards" / f"lane-{lane:02d}"
        folder.mkdir(parents=True)
        selected = []
        for position in range(lane, len(rows), lanes):
            row = rows[position]
            files = [row["request_file"], *row["image_files"]]
            targets = []
            for index, original in enumerate(files):
                name = f"r{position:04d}-f{index:02d}{original.suffix}"
                target = folder / name
                try:
                    os.link(original, target)
                except OSError:
                    shutil.copyfile(original, target)
                if _hash(target) != _hash(original):
                    message = "staged source bytes differ"
                    raise ValueError(message)
                targets.append(name)
            selected.append({"id": row["id"], "request_file": targets[0], "image_files": targets[1:]})
            facts["records"].append(
                {
                    "id": row["id"],
                    "lane": lane,
                    "request_sha256": _hash(files[0]),
                    "image_sha256": [_hash(f) for f in files[1:]],
                }
            )
        _write(folder / "manifest.json", {"records": selected})
    _write(directory / "shards.json", facts)
    return facts


class ProcessSampler:
    """Sample simultaneous union RSS and observed CPU, not summed peak RSS."""

    def __init__(self, path: Path, server_pid: int | None) -> None:
        """Configure one-second sampling of the measured process scopes."""
        self.path = path
        self.server_pid = server_pid
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.previous: dict[tuple[int, float], float] = {}

    def _run(self) -> None:
        try:
            import psutil  # type: ignore[import-untyped]  # noqa: PLC0415
        except ImportError:
            self.path.write_text(json.dumps({"status": "unmeasured", "reason": "psutil unavailable"}) + "\n")
            return
        cumulative = 0.0
        while not self.stop.is_set():
            processes = {}
            discovery_complete = True
            for pid in [os.getpid(), self.server_pid]:
                if pid is None:
                    continue
                try:
                    parent = psutil.Process(pid)
                    for process in [parent, *parent.children(recursive=True)]:
                        processes[process.pid] = process
                except (psutil.Error, OSError):
                    discovery_complete = False
            rss = 0
            delta = 0.0
            count = 0
            skipped = 0
            for process in processes.values():
                try:
                    key = (process.pid, process.create_time())
                    counter = process.cpu_times()
                    cpu = counter.user + counter.system
                    if key in self.previous:
                        delta += max(0.0, cpu - self.previous[key])
                    self.previous[key] = cpu
                    rss += process.memory_info().rss
                    count += 1
                except (psutil.Error, OSError):
                    skipped += 1
            cumulative += delta
            sample = {
                "monotonic_seconds": time.monotonic(),
                "rss_sum_bytes": rss if count else None,
                "observed_cpu_delta_seconds": delta if count else None,
                "observed_cpu_cumulative_seconds": cumulative,
                "process_count": count,
                "skipped_process_count": skipped,
                "discovery_complete": discovery_complete,
                "scope": "supervisor plus recursive children and optional server tree; de-duplicated PIDs",
                "rss_semantics": "simultaneous sampled sum; shared pages may be counted twice",
                "cpu_limitations": "pre-observation and unsampled final process exit CPU unavailable",
            }
            with self.path.open("a") as handle:
                handle.write(json.dumps(sample, allow_nan=False) + "\n")
            self.stop.wait(1.0)

    def start(self) -> None:
        """Start sampling without loading any model or adapter."""
        self.thread.start()

    def close(self) -> None:
        """Stop the sampler after its current observation."""
        self.stop.set()
        self.thread.join(timeout=3)


def _events(path: Path) -> tuple[list[dict[str, Any]], bool]:
    if not path.exists():
        return [], False
    if path.stat().st_size > MAX_LOG_BYTES:
        message = "worker log exceeds admission bound"
        raise ValueError(message)
    payload = path.read_bytes()
    rows = payload.splitlines()
    events = []
    partial = False
    for index, row in enumerate(rows):
        try:
            events.append(json.loads(row))
        except (ValueError, UnicodeError):
            if index == len(rows) - 1 and not payload.endswith(b"\n"):
                partial = True
            else:
                message = "malformed worker log before final checkpoint tail"
                raise ValueError(message) from None
    return events, partial


def collect(directory: str | Path, wall_seconds: float) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Verify shard IDs and hashes, retain all attempts, and merge for root scoring."""
    folder = Path(directory)
    facts = json.loads((folder / "shards.json").read_text())
    known = {row["id"]: row for row in facts["records"]}
    events = []
    states: list[dict[str, Any]] = []
    tails = []
    for lane in range(facts["lanes"]):
        worker = folder / f"worker-{lane:02d}"
        state = (
            json.loads((worker / "status.json").read_text())
            if (worker / "status.json").exists()
            else {"status": "missing"}
        )
        states.append(state)
        returned, partial = _events(worker / "attempts.jsonl")
        if partial:
            if state["status"] == "complete":
                message = "complete worker has incomplete JSONL tail"
                raise ValueError(message)
            tails.append(lane)
        for event in returned:
            if event.get("id") not in known or known[event["id"]]["lane"] != lane:
                message = "attempt ID outside its source shard"
                raise ValueError(message)
            if (
                event.get("event") == "attempt_completed"
                and event.get("request_sha256") != known[event["id"]]["request_sha256"]
            ):
                message = "completion request hash differs from source"
                raise ValueError(message)
            events.append(dict(event, lane=lane))
    events.sort(key=lambda e: (e["monotonic_seconds"], e["event"] != "attempt_started", e["id"]))
    seen = set()
    finished = set()
    for event in events:
        key = event["id"]
        if event["event"] == "attempt_started":
            if key in seen:
                message = "duplicate source attempt or retry"
                raise ValueError(message)
            seen.add(key)
        elif event["event"] == "attempt_completed":
            if key not in seen or key in finished:
                message = "completion without unique source start"
                raise ValueError(message)
            finished.add(key)
        else:
            message = "unknown worker event"
            raise ValueError(message)
    completed = [e for e in events if e["event"] == "attempt_completed"]
    span = max((e["monotonic_seconds"] + e["wall_seconds"] for e in completed), default=None)
    starts = [e["monotonic_seconds"] for e in events if e["event"] == "attempt_started"]
    duration = span - min(starts) if span is not None and starts else None
    complete = all(s["status"] == "complete" for s in states) and len(finished) == len(known)
    cpu_complete = all(isinstance(s.get("cpu_seconds"), (int, float)) for s in states)
    success = sum(e.get("status") == "ok" for e in completed)
    summary = {
        "status": "complete" if complete else "checkpoint",
        "planned_records": len(known),
        "attempted_records": len(seen),
        "successful_records": success,
        "failed_records": len(completed) - success,
        "lanes": facts["lanes"],
        "wall_seconds": wall_seconds,
        "cpu_seconds": sum(s["cpu_seconds"] for s in states) if cpu_complete else None,
        "cpu_scope": "additive child worker CPU totals; excludes supervisor and external server",
        "peak_rss_bytes": None,
        "resource_scope": "use simultaneous process tree samples; child high-water RSS is not summed",
        "concurrent_request_span_seconds": duration,
        "span_scope": "first source attempt start through last completion; includes lane idle/load imbalance",
        "regions_per_global_minute": success * 60 / wall_seconds if complete and wall_seconds > 0 else None,
        "regions_per_concurrent_span_minute": success * 60 / duration
        if complete and duration and duration > 0
        else None,
        "child_status": states,
        "incomplete_child_log_tails": tails,
        "gpu_sample_interval_seconds": 1.0,
        "gpu_sample_scope": "device-wide; not summed across lanes",
        "cuda": {"peak_allocated_bytes": None, "peak_reserved_bytes": None},
        "initialization": {"wall_seconds": None, "cpu_seconds": None},
    }
    with (folder / "attempts.jsonl").open("w") as handle:
        for event in events:
            handle.write(json.dumps(event, allow_nan=False) + "\n")
    _write(folder / "status.json", summary)
    return summary


def _terminate(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)


def run(  # noqa: C901, PLR0913
    *,
    adapter: str,
    model_dir: str,
    packets: str,
    output: str,
    limit: int,
    lanes: int,
    deadline_seconds: float,
    device: str = "cuda",
    server_pid: int | None = None,
    native_budget_gib: float | None = None,
    per_lane_peak_gib: float | None = None,
) -> dict[str, Any]:
    """Launch bounded fresh workers; no automatic retry or remote scorer access."""
    if adapter not in ADAPTERS or not math.isfinite(deadline_seconds) or deadline_seconds <= 0:
        message = "supported adapter and positive finite deadline required"
        raise ValueError(message)
    if adapter != "bench.remote_vllm" and lanes > 1:  # noqa: SIM102
        if (
            native_budget_gib is None
            or per_lane_peak_gib is None
            or not math.isfinite(native_budget_gib)
            or not math.isfinite(per_lane_peak_gib)
            or native_budget_gib <= 0
            or per_lane_peak_gib <= 0
            or lanes * per_lane_peak_gib > native_budget_gib
        ):
            message = "native concurrency requires explicit measured per-lane memory within budget"
            raise ValueError(message)
    facts = shard(packets, output, limit, lanes)
    folder = Path(output)
    started = time.monotonic()
    gpu = Sampler(folder / "gpu-samples.jsonl")
    resources = ProcessSampler(folder / "process-samples.jsonl", server_pid)
    children = []
    logs = []
    stop_reason = None
    gpu.start()
    resources.start()
    try:
        for lane in range(lanes):
            manifest = folder / "shards" / f"lane-{lane:02d}" / "manifest.json"
            log = (folder / f"worker-{lane:02d}.log").open("w")
            logs.append(log)
            count = sum(r["lane"] == lane for r in facts["records"])
            command = [
                sys.executable,
                "-m",
                "bench.remote_worker",
                "--adapter",
                adapter,
                "--model-dir",
                model_dir,
                "--packets",
                str(manifest),
                "--output",
                str(folder / f"worker-{lane:02d}"),
                "--limit",
                str(count),
                "--deadline-seconds",
                str(deadline_seconds),
                "--device",
                device,
            ]
            children.append(subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))  # noqa: S603
        while any(child.poll() is None for child in children):
            if time.monotonic() - started >= deadline_seconds:
                stop_reason = "deadline_exceeded"
                break
            finished: list[dict[str, Any]] = []
            for lane in range(lanes):
                rows, _ = _events(folder / f"worker-{lane:02d}" / "attempts.jsonl")
                finished.extend(e for e in rows if e.get("event") == "attempt_completed")
            finished.sort(key=lambda e: e["monotonic_seconds"] + e["wall_seconds"])
            if len(finished) >= FAILURE_LIMIT and all(e.get("status") != "ok" for e in finished[-FAILURE_LIMIT:]):
                stop_reason = "three_consecutive_failures"
                break
            time.sleep(0.1)
    finally:
        for child in children:
            _terminate(child)
        gpu.close()
        resources.close()
        for log in logs:
            log.close()
    summary = collect(folder, time.monotonic() - started)
    summary.update(
        adapter=adapter,
        server_pid=server_pid,
        stop_reason=stop_reason,
        source_manifest_sha256=facts["source_manifest_sha256"],
        native_budget_gib=native_budget_gib,
        per_lane_peak_gib=per_lane_peak_gib,
        returncodes=[child.returncode for child in children],
    )
    _write(folder / "status.json", summary)
    return summary


def local_evaluate(  # noqa: PLR0913
    *,
    source_dir: str | Path,
    source_index: str | Path,
    packets: str | Path,
    output: str | Path,
    model: str,
    hourly_usd: float | None = None,
) -> dict[str, Any]:
    """Root-only scoring after source verification, with concurrent span rates.

    No CLI invocation calls this function. References remain on the root host;
    only the source-only orchestration module and packets go to GPU workers.
    """
    from bench.remote_report import evaluate  # noqa: PLC0415 -- root-only scorer

    if hourly_usd is not None and (not math.isfinite(hourly_usd) or hourly_usd < 0):
        message = "hourly allocation quote must be finite and nonnegative"
        raise ValueError(message)
    quality = evaluate(
        source_dir=source_dir, source_index=source_index, worker_output=output, packets=packets, model=model
    )
    folder = Path(output)
    status = quality["worker_status"]
    events, partial = _events(folder / "attempts.jsonl")
    if partial:
        message = "merged concurrent log must contain only complete retained event lines"
        raise ValueError(message)
    by_id = {row["id"]: row for row in quality["results"]}
    completed = {e["id"]: e for e in events if e["event"] == "attempt_completed"}
    for group in quality["groups"]:
        rows = [r for r in quality["results"] if r["arm"] == group["arm"]]
        attempts = [completed[r["id"]] for r in rows if r["id"] in completed]
        span = (
            (
                max(e["monotonic_seconds"] + e["wall_seconds"] for e in attempts)
                - min(e["monotonic_seconds"] for e in attempts)
            )
            if attempts
            else None
        )
        complete = (
            group["completed_regions"] == group["planned_regions"]
            and group["schema_failures"] == group["worker_failures"] == 0
        )
        rate = group["completed_regions"] * 60 / span if complete and span and span > 0 else None
        group.update(
            concurrent_request_span_seconds=span,
            regions_per_concurrent_minute=rate,
            estimated_warm_regions_per_usd=rate * 60 / hourly_usd if rate and hourly_usd else None,
        )
        # Summed per-request latency is diagnostic work, not concurrent throughput.
        group["regions_per_inference_minute"] = None
    samples, _ = _events(folder / "process-samples.jsonl")
    rss = [s["rss_sum_bytes"] for s in samples if isinstance(s.get("rss_sum_bytes"), (int, float))]
    observed_cpu = [
        s["observed_cpu_cumulative_seconds"]
        for s in samples
        if isinstance(s.get("observed_cpu_cumulative_seconds"), (int, float))
    ]
    gpu_samples, _ = _events(folder / "gpu-samples.jsonl")
    gpu_values = []
    for sample in gpu_samples:
        raw = sample.get("raw_csv")
        if isinstance(raw, str):
            for line in raw.splitlines():
                try:
                    values = [float(value.strip()) for value in line.split(",")]
                    if len(values) == GPU_COLUMNS and all(math.isfinite(v) for v in values):
                        gpu_values.append(values)
                except ValueError:
                    continue
    quality.update(
        concurrent_lanes=status.get("lanes"),
        global_wall_seconds=status.get("wall_seconds"),
        regions_per_global_minute=status.get("regions_per_global_minute"),
        regions_per_concurrent_span_minute=status.get("regions_per_concurrent_span_minute"),
        global_concurrent_request_span_seconds=status.get("concurrent_request_span_seconds"),
        hourly_allocation_quote_usd=hourly_usd,
        estimated_warm_regions_per_usd=(
            status["regions_per_concurrent_span_minute"] * 60 / hourly_usd
            if status.get("regions_per_concurrent_span_minute") and hourly_usd
            else None
        ),
        sampled_process_tree_peak_rss_bytes=max(rss) if rss else None,
        sampled_process_tree_observed_cpu_seconds=max(observed_cpu) if observed_cpu else None,
        sample_scope=(
            "supervisor, worker descendants, optional shared server; union of PIDs; "
            "shared RSS pages may be counted twice"
        ),
        cpu_sample_limitations="pre-observation and unsampled exit intervals unavailable",
        gpu_available_rows=len(gpu_values),
        gpu_total_samples=len(gpu_samples),
        gpu_mean_utilization_percent=sum(v[1] for v in gpu_values) / len(gpu_values) if gpu_values else None,
        gpu_peak_device_mib=max(v[2] for v in gpu_values) if gpu_values else None,
        rate_scope=(
            "same supplied regions; concurrent attempt span includes lane imbalance; full-page extraction unavailable"
        ),
        cost_scope=(
            "warm serving estimate from GPU-plus-disk quote; excludes startup, downloads, "
            "idle, cleanup; not billed cost"
        ),
    )
    # Results retain all source-scored cases, including unresolved/schema failures.
    if set(by_id) != {
        json.loads((folder / "shards.json").read_text())["records"][i]["id"] for i in range(status["planned_records"])
    }:
        message = "source-scored inventory differs from planned concurrent records"
        raise ValueError(message)
    return quality


def markdown(evaluation: dict[str, Any]) -> str:
    """Render source-verified quality and measured parallel resources locally."""

    def number(value: Any) -> str:  # noqa: ANN401
        return "unmeasured" if value is None else f"{value:.2f}"

    groups = evaluation["groups"]
    lines = [
        f"# Concurrent {evaluation['model']}, {evaluation['concurrent_lanes']} lanes",
        "",
        (
            f"Status: {'checkpoint' if evaluation['checkpoint'] else 'complete'}. "
            "Source identity verified before root-local DEV scoring; references were not staged remotely."
        ),
        "",
        "| Arm | Valid / planned | Known / denominator | Abstain / denominator | Inputs/min | Est. warm inputs/USD |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for g in groups:
        lines.append(  # noqa: PERF401
            f"| {g['arm']} | {g['completed_regions']}/{g['planned_regions']} | "
            f"{g['known_correct']}/{g['known_denominator']} | "
            f"{g['ambiguous_abstentions']}/{g['ambiguous_denominator']} | "
            f"{number(g['regions_per_concurrent_minute'])} | {number(g['estimated_warm_regions_per_usd'])} |"
        )
    rss = evaluation["sampled_process_tree_peak_rss_bytes"]
    lines += [
        "",
        (
            f"Global wall: {number(evaluation['global_wall_seconds'])} s; "
            f"global rate: {number(evaluation['regions_per_global_minute'])} inputs/min. "
            f"Concurrent span: {number(evaluation['global_concurrent_request_span_seconds'])} s; "
            f"span rate: {number(evaluation['regions_per_concurrent_span_minute'])} inputs/min."
        ),
        f"Sampled simultaneous process-tree peak RSS: {number(rss / 2**30 if rss is not None else None)} GiB; "
        f"observed CPU: {number(evaluation['sampled_process_tree_observed_cpu_seconds'])} s. "
        + evaluation["sample_scope"]
        + ". "
        + evaluation["cpu_sample_limitations"]
        + ".",
        (
            f"Device GPU samples: {evaluation['gpu_available_rows']}/{evaluation['gpu_total_samples']}; "
            f"mean utilization {number(evaluation['gpu_mean_utilization_percent'])}%; "
            f"peak device memory {number(evaluation['gpu_peak_device_mib'])} MiB. "
            "Device observations are not summed child CUDA high-water counters."
        ),
        evaluation["rate_scope"] + ". " + evaluation["cost_scope"] + ".",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Run one explicitly bounded concurrency configuration into a fresh folder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=ADAPTERS, required=True)
    for name in ("model-dir", "packets", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--lanes", type=int, choices=(1, 2, 4, 8), required=True)
    parser.add_argument("--deadline-seconds", type=float, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--server-pid", type=int)
    parser.add_argument("--native-budget-gib", type=float)
    parser.add_argument("--per-lane-peak-gib", type=float)
    summary = run(**vars(parser.parse_args()))
    raise SystemExit(0 if summary["status"] == "complete" else 2)


if __name__ == "__main__":
    main()
