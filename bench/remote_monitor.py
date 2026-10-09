"""Sample a remote server process tree without touching its GPU runtime.

RSS is summed across processes; shared pages may be counted more than once.
CPU utilization uses one logical core = 100%, so a tree can exceed 100%.
Only observed increases in per-PID/create-time CPU counters are accumulated;
CPU before first observation or between final observation and exit is unmeasured.
Install psutil separately on the remote host. Run alongside the HTTP worker:
python -m bench.remote_monitor --pid PID --output server.jsonl --deadline-seconds 600
"""

# ruff: noqa: ANN401, PLR0913, PLC0415 - optional runtime and injected monitor clock APIs.
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any


class TreeSampler:
    """Track server identity and monotonic CPU deltas for its observed descendants."""

    def __init__(self, pid: int, psutil_module: Any) -> None:
        """Bind the original server identity before collecting descendants."""
        self.psutil = psutil_module
        self.root = psutil_module.Process(pid)
        self.root_identity = (pid, self.root.create_time())
        self.last_cpu: dict[tuple[int, float], float] = {}
        self.previous_time: float | None = None
        self.cpu_seconds = 0.0

    def sample(self, now: float) -> dict[str, Any] | None:
        """Return one tree measurement, or None after the original server exits."""
        errors = (self.psutil.NoSuchProcess, self.psutil.AccessDenied, self.psutil.ZombieProcess)
        discovery_complete = True
        try:
            if (
                not self.root.is_running()
                or self.root.create_time() != self.root_identity[1]
                or self.root.status() == self.psutil.STATUS_ZOMBIE
            ):
                return None
            processes = [self.root, *self.root.children(recursive=True)]
        except self.psutil.NoSuchProcess:
            return None
        except self.psutil.AccessDenied:
            processes = [self.root]
            discovery_complete = False
        elapsed = None if self.previous_time is None else now - self.previous_time
        delta = 0.0
        rows = []
        seen = set()
        skipped = 0
        for process in processes:
            try:
                with process.oneshot():
                    identity = (process.pid, process.create_time())
                    if identity in seen:
                        continue
                    seen.add(identity)
                    cpu = process.cpu_times()
                    total = cpu.user + cpu.system
                    rss = process.memory_info().rss
                    threads = process.num_threads()
                previous = self.last_cpu.get(identity)
                increment = 0.0 if previous is None else max(0.0, total - previous)
                self.last_cpu[identity] = max(total, previous or 0.0)
                delta += increment
                rows.append(
                    {
                        "pid": identity[0],
                        "create_time": identity[1],
                        "rss_bytes": rss,
                        "threads": threads,
                        "cpu_user_seconds": cpu.user,
                        "cpu_system_seconds": cpu.system,
                        "observed_cpu_delta_seconds": increment,
                    }
                )
            except errors:
                skipped += 1
        self.cpu_seconds += delta
        self.previous_time = now
        return {
            "record": "sample",
            "monotonic_seconds": now,
            "unix_seconds": time.time(),
            "interval_seconds": elapsed,
            "process_count": len(rows),
            "skipped_process_count": skipped,
            "descendant_discovery_complete": discovery_complete,
            "rss_sum_bytes": sum(row["rss_bytes"] for row in rows),
            "thread_count": sum(row["threads"] for row in rows),
            "observed_cpu_delta_seconds": delta,
            "observed_cpu_cumulative_seconds": self.cpu_seconds,
            "cpu_utilization_percent": 100 * delta / elapsed if elapsed is not None and elapsed > 0 else None,
            "processes": rows,
        }


def monitor(
    pid: int,
    output: Path,
    deadline_seconds: float,
    interval_seconds: float = 1.0,
    *,
    psutil_module: Any = None,
    clock: Any = time.monotonic,
    sleep: Any = time.sleep,
) -> str:
    """Write flushed JSONL through server exit or a finite monotonic deadline."""
    if pid <= 0 or not all(math.isfinite(value) and value > 0 for value in (deadline_seconds, interval_seconds)):
        message = "PID, deadline and sample interval must be positive and finite"
        raise ValueError(message)
    if psutil_module is None:
        import psutil as psutil_module  # Optional remote-only dependency.
    started = clock()
    sampler = TreeSampler(pid, psutil_module)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects a retained server trace from accidental replacement.
    with output.open("x", encoding="utf-8") as stream:

        def write(row: dict[str, Any]) -> None:
            stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
            stream.flush()

        write(
            {
                "record": "metadata",
                "schema_version": 1,
                "root_pid": pid,
                "root_create_time": sampler.root_identity[1],
                "sample_interval_seconds": interval_seconds,
                "deadline_seconds": deadline_seconds,
                "process_scope": "server plus observed recursive children",
                "rss_semantics": "sum of process RSS; shared pages may be counted multiple times",
                "cpu_semantics": "observed user+system counter increases by PID/create_time; one core=100%",
                "cpu_limitations": "pre-observation CPU and final unsampled exit intervals are unmeasured",
                "gpu_allocations": "unmeasured; device-wide nvidia-smi sampling belongs to the worker log",
            }
        )
        samples = 0
        while True:
            now = clock()
            # The first sample is immediate even for deadlines below the interval.
            if samples and now - started >= deadline_seconds:
                reason = "deadline"
                break
            row = sampler.sample(now)
            if row is None:
                reason = "server_exited"
                break
            row["elapsed_seconds"] = now - started
            write(row)
            samples += 1
            remaining = deadline_seconds - (clock() - started)
            if remaining > 0:
                sleep(min(interval_seconds, remaining))
        write(
            {
                "record": "end",
                "reason": reason,
                "samples": samples,
                "elapsed_seconds": clock() - started,
                "observed_cpu_cumulative_seconds": sampler.cpu_seconds,
            }
        )
    return reason


def main() -> None:
    """Run the standalone remote process monitor."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--deadline-seconds", type=float, required=True)
    parser.add_argument("--interval-seconds", type=float, default=1.0)
    arguments = parser.parse_args()
    monitor(arguments.pid, arguments.output, arguments.deadline_seconds, arguments.interval_seconds)


if __name__ == "__main__":
    main()
