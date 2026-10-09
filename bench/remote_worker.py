"""Bounded source-only remote decision worker; no scorer or provider credentials.

CLI supervision terminates the inference process at its wall-clock deadline.
Process CPU/RSS includes adapter work and sampler thread, excluding subprocesses;
nvidia-smi samples are device-wide, at one-second intervals, not per-worker GPU
allocation. CUDA allocation/reservation peaks are reported only when available.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import multiprocessing
import os
import resource
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

ADAPTERS = (
    "bench.remote_intern",
    "bench.remote_clef",
    "bench.remote_pplx",
    "bench.remote_vllm",
    "bench.remote_jpt",
    "bench.remote_nimble",
)
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_REQUEST_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 4096
MAX_IMAGES = 16
SAMPLE_SECONDS = 1.0
FAILURE_LIMIT = 3


def _bytes(path: Path, bound: int) -> bytes:
    with path.open("rb") as handle:
        payload = handle.read(bound + 1)
    if len(payload) > bound:
        message = "JSON input exceeds its byte bound"
        raise ValueError(message)
    return payload


def _json(path: Path, bound: int) -> Any:  # noqa: ANN401
    return json.loads(_bytes(path, bound))


def _append(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _checkpoint(directory: Path, state: dict[str, Any]) -> None:
    temporary = directory / "status.tmp"
    temporary.write_text(json.dumps(state, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(directory / "status.json")


def _relative(base: Path, value: str) -> Path:
    path = (base / value).resolve(strict=True)
    if not path.is_relative_to(base) or not path.is_file():
        message = "packet paths must be existing files inside the manifest directory"
        raise ValueError(message)
    return path


def inventory(manifest: str | Path, limit: int) -> list[dict[str, Any]]:
    """Validate only source request/image paths; never read reference labels."""
    if limit < 1:
        message = "limit must be positive"
        raise ValueError(message)
    path = Path(manifest).resolve(strict=True)
    data = _json(path, MAX_MANIFEST_BYTES)
    if not isinstance(data, dict) or set(data) != {"records"}:
        message = "source manifest must contain only records"
        raise ValueError(message)
    records = data["records"]
    if not isinstance(records, list) or not records or len(records) > MAX_RECORDS:
        message = "source record inventory is invalid or over its bound"
        raise ValueError(message)
    admitted = []
    seen = set()
    for row in records:
        if not isinstance(row, dict) or set(row) != {"id", "request_file", "image_files"}:
            message = "each source record requires id, request_file and image_files only"
            raise ValueError(message)
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in seen:
            message = "source record IDs must be nonempty and unique"
            raise ValueError(message)
        seen.add(row["id"])
        if not isinstance(row["request_file"], str) or not isinstance(row["image_files"], list):
            message = "source file references are invalid"
            raise TypeError(message)
        if len(row["image_files"]) > MAX_IMAGES or not all(isinstance(image, str) for image in row["image_files"]):
            message = "source image inventory is invalid"
            raise ValueError(message)
        admitted.append(
            {
                "id": row["id"],
                "request_file": _relative(path.parent, row["request_file"]),
                "image_files": [_relative(path.parent, image) for image in row["image_files"]],
            }
        )
    return admitted[:limit]


def _rss_bytes() -> int | None:
    try:
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == "darwin" else value * 1024)
    except (AttributeError, OSError):
        return None


def _cuda(*, reset: bool = False) -> dict[str, Any]:
    # Adapter imports torch lazily. Merely importing the worker never imports it.
    torch = sys.modules.get("torch")
    if torch is None:
        return {"peak_allocated_bytes": None, "peak_reserved_bytes": None, "available": False}
    try:
        if not torch.cuda.is_available():
            return {"peak_allocated_bytes": None, "peak_reserved_bytes": None, "available": False}
        if reset:
            torch.cuda.reset_peak_memory_stats()
        return {
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
            "available": True,
        }
    except Exception as error:
        return {"peak_allocated_bytes": None, "peak_reserved_bytes": None, "error_type": type(error).__name__}


class Sampler:
    """Retain device-wide GPU observations, including unavailable samples."""

    def __init__(self, output: Path) -> None:
        """Attach an output log without querying hardware yet."""
        self.output = output
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self.stop.is_set():
            tick = time.monotonic()
            sample: dict[str, Any] = {
                "monotonic_seconds": tick,
                "scope": "device-wide",
                "interval_seconds": SAMPLE_SECONDS,
            }
            try:
                result = subprocess.run(  # noqa: S603 -- fixed hardware query, no packet-supplied command
                    [
                        shutil.which("nvidia-smi") or "/usr/bin/nvidia-smi",
                        "--query-gpu=index,utilization.gpu,memory.used,memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=True,
                )
                sample["raw_csv"] = result.stdout[:65536]
                sample["columns"] = ["gpu_index", "utilization_percent", "used_mib", "total_mib"]
            except (OSError, subprocess.SubprocessError) as error:
                sample["raw_csv"] = None
                sample["error_type"] = type(error).__name__
            _append(self.output, sample)
            self.stop.wait(max(0, SAMPLE_SECONDS - (time.monotonic() - tick)))

    def start(self) -> None:
        """Start the one-second sampling loop."""
        self.thread.start()

    def close(self) -> None:
        """Stop sampling after any active nvidia-smi timeout."""
        self.stop.set()
        self.thread.join(timeout=3)


def run(  # noqa: PLR0913
    adapter: Any,  # noqa: ANN401 -- injected external adapter contract
    model_dir: str | Path,
    packets: str | Path,
    output: str | Path,
    limit: int,
    *,
    device: str = "cuda",
    deadline_seconds: float = 600,
    sample_gpu: bool = True,
) -> dict[str, Any]:
    """Execute fresh source records; CLI parent enforces blocked-call deadlines."""
    if not math.isfinite(deadline_seconds) or deadline_seconds <= 0:
        message = "deadline must be finite and positive"
        raise ValueError(message)
    rows = inventory(packets, limit)
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "attempts.jsonl").exists() or (directory / "status.json").exists():
        message = "output already contains attempts; choose a fresh directory, no automatic retries"
        raise ValueError(message)
    started = time.monotonic()
    cpu_started = time.process_time()
    state: dict[str, Any] = {
        "status": "initializing",
        "pid": os.getpid(),
        "planned_records": len(rows),
        "attempted_records": 0,
        "successful_records": 0,
        "failed_records": 0,
        "consecutive_failures": 0,
        "active_record": None,
        "deadline_seconds": deadline_seconds,
        "resource_scope": "worker process and threads; excludes subprocess CPU/RSS",
        "rss_measurement": "resource.getrusage(RUSAGE_SELF).ru_maxrss process lifetime high-water mark",
        "gpu_sample_scope": "device-wide, not per-worker",
        "gpu_sample_interval_seconds": SAMPLE_SECONDS,
        "gpu_sampling_enabled": sample_gpu,
    }
    _checkpoint(directory, state)
    sampler = Sampler(directory / "gpu-samples.jsonl") if sample_gpu else None
    if sampler:
        sampler.start()
    try:
        init_wall, init_cpu = time.monotonic(), time.process_time()
        engine = adapter.load(model_dir, device=device)
        state["initialization"] = {
            "wall_seconds": time.monotonic() - init_wall,
            "cpu_seconds": time.process_time() - init_cpu,
            "peak_rss_bytes": _rss_bytes(),
            "cuda": _cuda(),
        }
        state["status"] = "running"
        _checkpoint(directory, state)
        for index, row in enumerate(rows):
            if time.monotonic() - started >= deadline_seconds:
                state["status"] = "deadline_exceeded"
                break
            state["active_record"] = row["id"]
            state["attempted_records"] += 1
            _checkpoint(directory, state)
            event = {
                "event": "attempt_started",
                "attempt": index,
                "id": row["id"],
                "monotonic_seconds": time.monotonic(),
            }
            _append(directory / "attempts.jsonl", event)
            wall, cpu = time.monotonic(), time.process_time()
            _cuda(reset=True)
            infer_wall = infer_cpu = None
            try:
                payload = _bytes(row["request_file"], MAX_REQUEST_BYTES)
                event["request_sha256"] = hashlib.sha256(payload).hexdigest()
                body = json.loads(payload)
                infer_wall, infer_cpu = time.monotonic(), time.process_time()
                response = adapter.predict(engine, body, row["image_files"])
                event["inference_wall_seconds"] = time.monotonic() - infer_wall
                event["inference_cpu_seconds"] = time.process_time() - infer_cpu
                # Validate serialization before counting success or dropping native fields.
                json.dumps(response, allow_nan=False)
                event.update(status="ok", response=response)
                state["successful_records"] += 1
                state["consecutive_failures"] = 0
            except Exception as error:
                event.update(status="error", error_type=type(error).__name__, error=str(error)[:4096])
                event.setdefault(
                    "inference_wall_seconds", None if infer_wall is None else time.monotonic() - infer_wall
                )
                event.setdefault(
                    "inference_cpu_seconds", None if infer_cpu is None else time.process_time() - infer_cpu
                )
                state["failed_records"] += 1
                state["consecutive_failures"] += 1
            event.update(
                event="attempt_completed",
                wall_seconds=time.monotonic() - wall,
                cpu_seconds=time.process_time() - cpu,
                peak_rss_bytes=_rss_bytes(),
                cuda=_cuda(),
                inference_scope="adapter predict, including native input preprocessing",
            )
            _append(directory / "attempts.jsonl", event)
            state["active_record"] = None
            _checkpoint(directory, state)
            if state["consecutive_failures"] >= FAILURE_LIMIT:
                state["status"] = "failure_limit"
                break
        else:
            state["status"] = "complete"
    except Exception as error:
        state.update(status="worker_error", error_type=type(error).__name__, error=str(error)[:4096])
        state.setdefault(
            "initialization",
            {
                "wall_seconds": time.monotonic() - init_wall,
                "cpu_seconds": time.process_time() - init_cpu,
                "peak_rss_bytes": _rss_bytes(),
                "cuda": _cuda(),
                "status": "error",
            },
        )
    finally:
        if sampler:
            sampler.close()
        state.update(
            wall_seconds=time.monotonic() - started,
            cpu_seconds=time.process_time() - cpu_started,
            peak_rss_bytes=_rss_bytes(),
            cuda=_cuda(),
        )
        _checkpoint(directory, state)
    return state


def _child(options: dict[str, Any]) -> None:
    adapter = importlib.import_module(options.pop("adapter"))
    run(adapter, **options)


def supervise(options: dict[str, Any]) -> int:
    """Terminate the child on deadline, including blocked initialization/calls."""
    directory = Path(options["output"])
    if (directory / "status.json").exists() or (directory / "attempts.jsonl").exists():
        message = "output must be fresh; attempts cannot be automatically retried"
        raise ValueError(message)
    process = multiprocessing.get_context("spawn").Process(target=_child, args=(dict(options),))
    started = time.monotonic()
    process.start()
    process.join(timeout=options["deadline_seconds"])
    if process.is_alive():
        process.terminate()
        process.join(timeout=3)
        if process.is_alive():
            process.kill()
            process.join(timeout=3)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "status.json"
        status = _json(path, MAX_MANIFEST_BYTES) if path.exists() else {}
        status.update(
            status="deadline_exceeded", hard_deadline=True, supervisor_wall_seconds=time.monotonic() - started
        )
        _checkpoint(directory, status)
        return 2
    path = directory / "status.json"
    if process.exitcode != 0 or not path.exists():
        directory.mkdir(parents=True, exist_ok=True)
        status = _json(path, MAX_MANIFEST_BYTES) if path.exists() else {}
        status.update(status="worker_process_error", exit_code=process.exitcode)
        _checkpoint(directory, status)
        return 1
    return 0 if _json(path, MAX_MANIFEST_BYTES)["status"] == "complete" else 1


def main() -> None:
    """Run only an explicit staged adapter and source manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=ADAPTERS, required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--packets", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--deadline-seconds", type=float, default=600)
    parser.add_argument("--device", default="cuda")
    options = vars(parser.parse_args())
    if not math.isfinite(options["deadline_seconds"]) or options["deadline_seconds"] <= 0 or options["limit"] < 1:
        parser.error("deadline and request limit must be positive")
    raise SystemExit(supervise(options))


if __name__ == "__main__":
    main()
