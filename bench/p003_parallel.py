"""Root-only opt-in contended P003 queue; no ledger policy changes or retries."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable  # noqa: TC003 - public cleanup callback type.
from contextlib import suppress
from pathlib import Path
from typing import Any

import psutil

from bench.decision_hosted import ROOT
from bench.research_policy import P003_PAID_CUTOFF
from bench.silver import guard_path, write_json

MODULES = {"pipeline": "bench.p003_run", "candidate": "bench.p003_candidate_run", "boundary": "bench.p003_boundary_run"}
MAX_ARMS = 64
MAX_CONCURRENT = 3
MAX_WALL = 2400
START_MARGIN = 120
STOP_MARGIN = 60

POLICY = {
    "max_concurrent_arms": 3,
    "transport_concurrency": 3,
    "workers_per_arm": 1,
    "max_arm_wall_seconds": 2400,
    "minimum_start_seconds_before_cutoff": 120,
    "sample_interval_seconds": 0.1,
    "concurrent_policy": {"max_inflight": 3, "wave_limits_usd": {"P003": 50.0}, "allow_matched_replicates": True},
    "root_only_offline_reconciliation": True,
    "exclusive_paid_work_required": True,
    "gateway_parallel_allowed": False,
    "automatic_retries": False,
}


def validate_plan(plan: Any, seed: int) -> list[dict[str, Any]]:  # noqa: ANN401, C901, PLR0912 - explicit independent argument checks.
    """Validate literal arms and freeze a deterministic randomized execution order."""
    if not isinstance(plan, list) or not 1 <= len(plan) <= MAX_ARMS:
        message = "Parallel queue requires 1 through 64 declared arms"
        raise ValueError(message)
    plan = json.loads(json.dumps(plan))  # Preserve caller input while resolving declared paths.
    names = set()
    for arm in plan:
        if not isinstance(arm, dict):
            message = "Each arm must be an object"
            raise TypeError(message)
        if arm.get("kind", "pipeline") not in MODULES:
            message = "Experiment kind must be pipeline, candidate or boundary"
            raise ValueError(message)
        name, arguments = arm.get("name"), arm.get("arguments")
        if (not isinstance(name, str) or not name or name in names
                or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name)):
            message = "Arm names must be unique safe lowercase filenames"
            raise ValueError(message)
        if not isinstance(arguments, list) or any(not isinstance(v, str) for v in arguments):
            message = "Arm arguments must be literal strings"
            raise ValueError(message)
        forbidden = {"--output", "--manifest", "--workers", "--transport-concurrency"}
        if any(v.split("=", 1)[0] in forbidden for v in arguments):
            message = "Queue owns output, manifest, workers, transport and gate-provider controls"
            raise ValueError(message)
        for i, value in enumerate(arguments):
            if value.split("=", 1)[0] in {"--baseline", "--trusted-code"}:
                path = value.split("=", 1)[1] if "=" in value else (
                    arguments[i + 1] if i + 1 < len(arguments) else ""
                )
                if not path or path.startswith("--"):
                    message = "Declared baseline/trust-map path is missing"
                    raise ValueError(message)
                resolved = str(guard_path(Path(path)))
                if "=" in value:
                    arguments[i] = value.split("=", 1)[0] + "=" + resolved
                else:
                    arguments[i + 1] = resolved
            if value.split("=", 1)[0] == "--gate-provider":
                provider = value.split("=", 1)[1] if "=" in value else (
                    arguments[i + 1] if i + 1 < len(arguments) else None
                )
                if provider != "openrouter":
                    message = "Gateway/Vercel gate providers are forbidden in parallel arms"
                    raise ValueError(message)
        if any("gateway" in v.lower() or "vercel" in v.lower() for v in arguments):
            message = "Gateway/Vercel parallel arms are forbidden"
            raise ValueError(message)
        names.add(name)
    ordered = json.loads(json.dumps(plan))
    random.Random(seed).shuffle(ordered)  # noqa: S311 - reproducible experiment order, not security.
    return ordered


def command_for(arm: dict[str, Any], manifest: Path | None, output: Path) -> list[str]:
    """Build a fixed module command with kind-specific hosted controls."""
    kind = arm.get("kind", "pipeline")
    command = [sys.executable, "-m", MODULES[kind], "--output", str(output.resolve()),
               "--transport-concurrency", "3"]
    if kind == "pipeline":
        if manifest is None:
            message = "Pipeline arms require an explicit manifest"
            raise ValueError(message)
        command.extend(["--manifest", str(manifest.resolve()), "--workers", "1"])
    else:
        command.append("--run-hosted")
    return [*command, *arm["arguments"]]


def report_counts(status: dict[str, Any], arm_report: dict[str, Any]) -> None:
    """Label complete-pipeline rates separately from incremental artifact processing."""
    rows = arm_report["results"]
    if not isinstance(rows, list):
        message = "Arm report results must be a list"
        raise TypeError(message)
    status["completed_pages"] = sum(row.get("status") == "ok" for row in rows)
    status["attempted_pages"] = len(rows)
    rate = status["completed_pages"] / status["wall_seconds"] * 60
    if status["kind"] == "pipeline":
        status["contended_pages_per_minute"] = rate
    else:
        status["incremental_artifact_pages_per_minute"] = rate
        stage = "ranking_status" if status["kind"] == "candidate" else "repair_status"
        status["incremental_status_counts"] = dict(Counter(row.get(stage, "missing") for row in rows))
        accounting = arm_report["incremental_ranking" if status["kind"] == "candidate" else "incremental_repair"]
        status["incremental_accounting"] = accounting
        status["rate_scope"] = "retained artifacts including authentication/copying; original pipeline excluded"


def summarize_rates(statuses: list[dict[str, Any]], wall: float, not_started: list[str]) -> dict[str, Any]:
    """Aggregate independent arms by kind without merging pipeline/incremental rates."""
    by_kind = {}
    for kind in MODULES:
        arms = [status for status in statuses if status["kind"] == kind]
        complete = bool(arms) and all(
            "completed_pages" in status and not status.get("report_metrics_error") for status in arms
        ) and not not_started
        pages = sum(status.get("completed_pages", 0) for status in arms)
        by_kind[kind] = {"completed_page_runs_known": pages, "complete_metrics": complete,
                         "scope": "complete pipeline" if kind == "pipeline" else "incremental retained artifacts",
                         "completed_page_runs_per_minute": pages / wall * 60 if complete and wall else None,
                         "arm_count": len(arms)}
        if kind != "pipeline":
            by_kind[kind]["incremental_artifact_page_runs_per_minute"] = by_kind[kind].pop(
                "completed_page_runs_per_minute"
            )
    return {"label": "contended queue aggregate by kind; repeated pages count per arm",
            "by_kind": by_kind, "not_a_serial_comparison": True,
            # Preserve pipeline-only queue summary compatibility; excludes incremental arms.
            **by_kind["pipeline"]}


class AggregateMonitor:
    """Sample actual queue/descendant CPU counters and summed live RSS at 100ms."""

    def __init__(self) -> None:
        """Initialize counters without reading artifacts or financial state."""
        self.process = psutil.Process()
        self.initial_cpu = sum(self.process.cpu_times()[:2])
        self.cpu: dict[tuple[int, float], float] = {}
        self.peak_rss = 0
        self.samples = 0
        self.max_process_count = 0

    def sample(self) -> None:
        """Capture one aggregate sample, tolerating exited child processes."""
        rss, count = 0, 0
        for process in [self.process, *self.process.children(recursive=True)]:
            try:
                key = (process.pid, process.create_time())
                value = sum(process.cpu_times()[:2])
                self.cpu[key] = max(self.cpu.get(key, 0), value)
                rss += process.memory_info().rss
                count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        self.peak_rss = max(self.peak_rss, rss)
        self.max_process_count = max(self.max_process_count, count)
        self.samples += 1

    def result(self, wall: float) -> dict[str, Any]:
        """Return measured counters with explicit scope and sampling limitations."""
        cpu = max(0, sum(self.cpu.values()) - self.initial_cpu)
        return {"interval": "contended parallel queue including child arms",
                "tool": "psutil process CPU counters and RSS", "sample_interval_seconds": 0.1,
                "scope": "queue process and recursive descendants; summed RSS may count shared pages twice",
                "cpu_seconds_sampled": cpu, "cpu_core_equivalents_sampled": cpu / wall if wall else None,
                "peak_aggregate_rss_bytes_sampled": self.peak_rss, "samples": self.samples,
                "max_observed_process_count": self.max_process_count, "machine_logical_cpu_count": os.cpu_count(),
                "limitation": "CPU of children exiting between samples may be missed",
                "wall_seconds": wall, "full_pipeline_pages_per_minute": None}


def stop_group(process: subprocess.Popen, sample: Callable[[], None] | None = None) -> None:
    """Interrupt the entire arm group, then kill remaining descendants after 30s."""
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            process.wait()
            return
        process.poll()  # Reap parent even when grandchildren remain.
        if sample is not None:
            sample()
        time.sleep(0.1)
    with suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def run_queue(  # noqa: C901, PLR0912, PLR0913 - bounded lifecycle and explicit cleanup.
    plan: list[dict[str, Any]], manifest: Path | None, directory: Path, *, seed: int,
              cutoff: float = P003_PAID_CUTOFF, root: Path = ROOT) -> dict[str, Any]:
    """Run only fresh arms, with per-arm snapshots and atomic status checkpoints."""
    directory = guard_path(directory)
    manifest = guard_path(manifest) if manifest is not None else None
    ordered = validate_plan(plan, seed)
    for arm in ordered:
        command_for(arm, manifest, directory / arm["name"])
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "logs").mkdir()
    (directory / "trusted-code").mkdir()
    git = shutil.which("git")
    if git is None:
        message = "Git required for trusted snapshots"
        raise RuntimeError(message)
    statuses: list[dict[str, Any]] = []
    running: dict[str, tuple[subprocess.Popen, Any, dict[str, Any]]] = {}
    monitor, started = AggregateMonitor(), time.monotonic()
    record = {"policy": POLICY, "seed": seed, "frozen_order": json.loads(json.dumps(ordered)), "paid_cutoff": cutoff,
              "manifest": str(manifest.resolve()) if manifest is not None else None, "arms": statuses,
              "rates_label": "contended per-arm rates separated by experiment kind",
              "aggregate_rates": None, "max_observed_concurrent_arms": 0}

    def checkpoint() -> None:
        record["resources"] = monitor.result(time.monotonic() - started)
        write_json(directory / "status.json", record)

    interrupted = False
    try:
        while ordered or running:
            remaining = cutoff - time.time()
            while ordered and len(running) < MAX_CONCURRENT and remaining >= START_MARGIN:
                arm = ordered.pop(0)
                name = arm["name"]
                output = directory / name
                if output.exists():
                    message = "Arm output already exists; no overwrite or retry"
                    raise ValueError(message)  # noqa: TRY301 - output collision aborts all active arms.
                files = subprocess.check_output([git, "ls-files", "bench/*.py"], cwd=root, text=True).splitlines()  # noqa: S603
                trust = {Path(p).name: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in files}
                write_json(directory / "trusted-code" / (name + ".json"), trust)
                command = command_for(arm, manifest, output)
                status = {"name": name, "kind": arm.get("kind", "pipeline"), "status": "starting", "command": command,
                          "started_at": time.time(), "rate_label": "contended", "retry": False}
                statuses.append(status)
                checkpoint()
                log = (directory / "logs" / (name + ".log")).open("x")
                try:
                    process = subprocess.Popen(  # noqa: S603 - fixed module and literal validated arguments.
                        command, cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    )
                except BaseException:
                    log.close()
                    status["status"] = "launch_failed"
                    raise
                status.update(status="running", pid=process.pid)
                running[name] = (process, log, status)
                record["max_observed_concurrent_arms"] = max(record["max_observed_concurrent_arms"], len(running))
            monitor.sample()
            for name, (process, log, status) in list(running.items()):
                timeout = time.time() - status["started_at"] >= MAX_WALL or remaining <= STOP_MARGIN
                if process.poll() is None and timeout:
                    stop_group(process, monitor.sample)
                    status["interrupted"] = "wall_limit" if remaining > STOP_MARGIN else "paid_cutoff"
                code = process.poll()
                if code is not None:
                    stop_group(process, monitor.sample)  # Clean descendants even after parent exits normally.
                    status.update(status="completed" if code == 0 and not status.get("interrupted") else "failed",
                                  exit_code=code, wall_seconds=time.time() - status["started_at"])
                    report_path = directory / name / "report.json"
                    if report_path.exists():
                        try:
                            arm_report = json.loads(report_path.read_bytes())
                            report_counts(status, arm_report)
                        except (ValueError, KeyError, TypeError, AttributeError):
                            status["report_metrics_error"] = "unreadable_report"
                    log.close()
                    del running[name]
                    checkpoint()
            if remaining < START_MARGIN and ordered:
                record["not_started"] = [arm["name"] for arm in ordered]
                ordered.clear()
            if running:
                time.sleep(0.1)
    except BaseException:
        interrupted = True
        raise
    finally:
        for process, log, status in running.values():
            stop_group(process, monitor.sample)
            log.close()
            status.update(status="interrupted", exit_code=process.returncode,
                          wall_seconds=time.time() - status["started_at"])
        monitor.sample()
        record["interrupted"] = interrupted
        wall = time.monotonic() - started
        record["aggregate_rates"] = summarize_rates(statuses, wall, record.get("not_started", []))
        checkpoint()
    return record


def main() -> None:
    """Require root's explicit exclusivity acknowledgment; never reconcile ledgers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--exclusive-paid-work", action="store_true")
    args = parser.parse_args()
    if not args.exclusive_paid_work:
        parser.error("Root must stop all serial/other paid work and reconcile policy offline before acknowledgment")
    run_queue(json.loads(guard_path(args.plan).read_bytes()), guard_path(args.manifest) if args.manifest else None,
              guard_path(args.directory), seed=args.seed)


if __name__ == "__main__":
    main()
