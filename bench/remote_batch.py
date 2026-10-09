"""Bounded source-only true-batch GPU worker; root-local scoring stays separate.

Per-record attempts preserve native responses and source hashes, with no assigned
individual duration. Actual wall/CPU/CUDA measurements belong to unique batches.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import multiprocessing
import time
from pathlib import Path
from typing import Any

from bench.remote_worker import (
    MAX_MANIFEST_BYTES,
    MAX_REQUEST_BYTES,
    Sampler,
    _append,
    _bytes,
    _checkpoint,
    _cuda,
    _json,
    _rss_bytes,
    inventory,
)

BATCH_SIZES = (1, 2, 4, 8, 16)
FAILURE_LIMIT = 3


def run(  # noqa: C901, PLR0912, PLR0913
    adapter: Any,  # noqa: ANN401 -- injected external adapter contract
    *,
    model_dir: str,
    packets: str,
    output: str,
    limit: int,
    batch_size: int,
    deadline_seconds: float,
    device: str = "cuda",
    sample_gpu: bool = True,
) -> dict[str, Any]:
    """Load one model copy, predict bounded microbatches, and retain every attempt."""
    if batch_size not in BATCH_SIZES or not math.isfinite(deadline_seconds) or deadline_seconds <= 0:
        message = "supported batch size and positive finite deadline required"
        raise ValueError(message)
    rows = inventory(packets, limit)
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    started, cpu_started = time.monotonic(), time.process_time()
    state: dict[str, Any] = {
        "status": "initializing",
        "planned_records": len(rows),
        "attempted_records": 0,
        "successful_records": 0,
        "failed_records": 0,
        "active_records": [],
        "batch_size": batch_size,
        "attempted_batches": 0,
        "successful_batches": 0,
        "measurement_scope": "one model copy; unique microbatch metrics, individual duration unassigned",
    }
    _checkpoint(directory, state)
    sampler = Sampler(directory / "gpu-samples.jsonl") if sample_gpu else None
    if sampler:
        sampler.start()
    durations: list[float] = []
    cuda_peaks: list[dict[str, Any]] = []
    consecutive = 0
    try:
        init_wall, init_cpu = time.monotonic(), time.process_time()
        engine = adapter.load(model_dir, device=device)
        initialization: dict[str, Any] = {
            "wall_seconds": time.monotonic() - init_wall,
            "cpu_seconds": time.process_time() - init_cpu,
            "peak_rss_bytes": _rss_bytes(),
            "cuda": _cuda(),
        }
        state["initialization"] = initialization
        cuda_peaks.append(initialization["cuda"])
        for offset in range(0, len(rows), batch_size):
            if time.monotonic() - started >= deadline_seconds:
                state["status"] = "deadline_exceeded"
                break
            selected = rows[offset : offset + batch_size]
            batch_id = f"b{offset // batch_size:04d}"
            batch_started = time.monotonic()
            state.update(status="running", active_records=[r["id"] for r in selected])
            state["attempted_records"] += len(selected)
            state["attempted_batches"] += 1
            _checkpoint(directory, state)
            for row in selected:
                _append(
                    directory / "attempts.jsonl",
                    {
                        "event": "attempt_started",
                        "id": row["id"],
                        "batch_id": batch_id,
                        "monotonic_seconds": batch_started,
                    },
                )
            bodies = []
            hashes = []
            batch_cpu = time.process_time()
            infer_wall = infer_cpu = None
            infer_duration: float | None = None
            infer_cpu_duration: float | None = None
            _cuda(reset=True)
            try:
                for row in selected:
                    payload = _bytes(row["request_file"], MAX_REQUEST_BYTES)
                    hashes.append(hashlib.sha256(payload).hexdigest())
                    bodies.append(json.loads(payload))
                infer_wall, infer_cpu = time.monotonic(), time.process_time()
                responses = adapter.predict_batch(engine, bodies, [r["image_files"] for r in selected])
                infer_duration, infer_cpu_duration = time.monotonic() - infer_wall, time.process_time() - infer_cpu
                if len(responses) != len(selected):
                    message = "batch response count differs from source inventory"
                    raise ValueError(message)  # noqa: TRY301
                json.dumps(responses, allow_nan=False)
                status, error = "ok", None
                state["successful_records"] += len(selected)
                state["successful_batches"] += 1
                consecutive = 0
            except Exception as exception:
                status, error = "error", {"error_type": type(exception).__name__, "error": str(exception)[:4096]}
                infer_duration = time.monotonic() - infer_wall if infer_wall is not None else None
                infer_cpu_duration = time.process_time() - infer_cpu if infer_cpu is not None else None
                responses = [None] * len(selected)
                state["failed_records"] += len(selected)
                consecutive += len(selected)
            duration, cpu = time.monotonic() - batch_started, time.process_time() - batch_cpu
            cuda = _cuda()
            cuda_peaks.append(cuda)
            batch_event = {
                "batch_id": batch_id,
                "ids": [r["id"] for r in selected],
                "status": status,
                "monotonic_seconds": batch_started,
                "wall_seconds": duration,
                "cpu_seconds": cpu,
                "inference_wall_seconds": infer_duration,
                "inference_cpu_seconds": infer_cpu_duration,
                "peak_rss_bytes": _rss_bytes(),
                "cuda": cuda,
            }
            if error:
                batch_event.update(error)
            _append(directory / "batches.jsonl", batch_event)
            if infer_duration is not None:
                durations.append(infer_duration)
            for index, (row, response) in enumerate(zip(selected, responses, strict=True)):
                event = {
                    "event": "attempt_completed",
                    "id": row["id"],
                    "batch_id": batch_id,
                    "monotonic_seconds": batch_started,
                    "status": status,
                    "request_sha256": hashes[index] if index < len(hashes) else None,
                    "wall_seconds": None,
                    "cpu_seconds": None,
                    "inference_wall_seconds": None,
                    "inference_cpu_seconds": None,
                    "duration_scope": "unassigned per record; unique shared batch metrics in batches.jsonl",
                }
                if status == "ok":
                    event["response"] = response
                elif error:
                    event.update(error)
                _append(directory / "attempts.jsonl", event)
            state["active_records"] = []
            _checkpoint(directory, state)
            if consecutive >= FAILURE_LIMIT:
                state["status"] = "failure_limit"
                break
        else:
            state["status"] = "complete"
    except Exception as exception:
        state.update(status="worker_error", error_type=type(exception).__name__, error=str(exception)[:4096])
    finally:
        if sampler:
            sampler.close()
        state.update(
            wall_seconds=time.monotonic() - started,
            cpu_seconds=time.process_time() - cpu_started,
            peak_rss_bytes=_rss_bytes(),
            total_batch_inference_seconds=sum(durations),
            batch_inference_measurement_complete=len(durations) == state["attempted_batches"],
            cuda={
                "peak_allocated_bytes": max(
                    (r["peak_allocated_bytes"] for r in cuda_peaks if r.get("peak_allocated_bytes") is not None),
                    default=None,
                ),
                "peak_reserved_bytes": max(
                    (r["peak_reserved_bytes"] for r in cuda_peaks if r.get("peak_reserved_bytes") is not None),
                    default=None,
                ),
            },
        )
        if state["status"] == "complete" and sum(durations) > 0:
            state["regions_per_batch_inference_minute"] = state["successful_records"] * 60 / sum(durations)
            state["regions_per_worker_minute"] = state["successful_records"] * 60 / state["wall_seconds"]
        _checkpoint(directory, state)
    return state


def _child(options: dict[str, Any]) -> None:
    adapter = importlib.import_module("bench.remote_clef_batch")
    run(adapter, **options)


def supervise(options: dict[str, Any]) -> int:
    """Terminate blocked model loading or forward calls at the hard deadline."""
    directory = Path(options["output"])
    if directory.exists():
        message = "output must be fresh; failed requests cannot be silently retried"
        raise ValueError(message)
    process = multiprocessing.get_context("spawn").Process(target=_child, args=(dict(options),))
    process.start()
    process.join(timeout=options["deadline_seconds"])
    if process.is_alive():
        process.terminate()
        process.join(timeout=3)
        if process.is_alive():
            process.kill()
            process.join(timeout=3)
        directory.mkdir(parents=True, exist_ok=True)
        status = _json(directory / "status.json", MAX_MANIFEST_BYTES) if (directory / "status.json").exists() else {}
        status.update(status="deadline_exceeded", hard_deadline=True)
        _checkpoint(directory, status)
        return 2
    if process.exitcode != 0 or not (directory / "status.json").exists():
        return 2
    return 0 if _json(directory / "status.json", MAX_MANIFEST_BYTES)["status"] == "complete" else 2


def main() -> None:
    """Execute one declared Clef batch-size configuration, without scoring."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "packets", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--batch-size", type=int, choices=BATCH_SIZES, required=True)
    parser.add_argument("--deadline-seconds", type=float, required=True)
    parser.add_argument("--device", default="cuda")
    options = vars(parser.parse_args())
    if not math.isfinite(options["deadline_seconds"]) or options["deadline_seconds"] <= 0:
        parser.error("deadline must be finite and positive")
    raise SystemExit(supervise(options))


if __name__ == "__main__":
    main()
