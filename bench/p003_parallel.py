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

MODULES = {
    "pipeline": "bench.p003_run", "candidate": "bench.p003_candidate_run", "boundary": "bench.p003_boundary_run",
    "gate": "bench.p003_gate_run", "topology": "bench.p003_topology_run",
    "admission": "bench.p003_structure_admission_run", "micro": "bench.p003_micro_relations_run",
    "diagram": "bench.p003_geometry_diagram_run",
    "header": "bench.p003_header_decision_run",
}
INCREMENTAL_FIELDS = {
    "candidate": ("ranking_status", "incremental_ranking"),
    "boundary": ("repair_status", "incremental_repair"),
    "gate": ("gate_status", "incremental_gate"),
    "topology": ("topology_status", "incremental_ownership"),
    "admission": ("decision_status", "incremental_admission"),
    "diagram": ("selection_status", "incremental_selection"),
    "header": ("selection_status", "incremental_header_selection"),
}
MAX_ARMS = 64
MAX_CONCURRENT = 3
MAX_WALL = 2400
MIN_DECLARED_WALL = 30
MAX_DECLARED_WALL = 10800
HEARTBEAT_SECONDS = 5.0
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
        if "max_wall_seconds" in arm and (
            type(arm["max_wall_seconds"]) is not int
            or not MIN_DECLARED_WALL <= arm["max_wall_seconds"] <= MAX_DECLARED_WALL
        ):
            message = "Declared arm duration must be an integer from 30 through 10800 seconds"
            raise ValueError(message)
        if arm.get("kind", "pipeline") not in MODULES:
            message = "Experiment kind is not a supported fixed runner"
            raise ValueError(message)
        if "manifest" in arm:
            if arm.get("kind", "pipeline") != "pipeline" or not isinstance(arm["manifest"], str):
                message = "Only pipeline arms may declare an explicit manifest path"
                raise ValueError(message)
            arm["manifest"] = str(guard_path(Path(arm["manifest"])))
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
            if value.split("=", 1)[0] in {
                "--baseline", "--trusted-code", "--source-baseline", "--topology-baseline",
                "--source-trusted-code", "--topology-trusted-code",
                "--input", "--pool", "--pool-trusted-code", "--selector-trusted-code", "--input-trusted-code",
                "--header-trusted-code", "--generation-trusted-code",
            }:
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
        if "manifest" in arm:
            manifest = guard_path(Path(arm["manifest"]))
        if manifest is None:
            message = "Pipeline arms require an explicit manifest"
            raise ValueError(message)
        # The P003 entry point fixes one CPU worker in its configuration.
        command.extend(["--manifest", str(manifest.resolve())])
    else:
        command.append("--run-hosted")
    return [*command, *arm["arguments"]]


def report_counts(status: dict[str, Any], arm_report: dict[str, Any]) -> None:
    """Label complete-pipeline rates separately from incremental artifact processing."""
    rows = arm_report["results"]
    if not isinstance(rows, list):
        message = "Arm report results must be a list"
        raise TypeError(message)
    if status["kind"] == "micro":
        # A local pair answer is not a processed PDF page, even when page IDs are retained.
        statuses = Counter(row.get("status", "missing") for row in rows)
        valid = statuses["valid_nonabstaining"] + statuses["valid_abstention"]
        status.update(
            intended_questions=len(rows), attempted_questions=arm_report["attempted_question_count"],
            valid_returned_questions=valid, nonabstaining_questions=statuses["valid_nonabstaining"],
            question_status_counts=dict(statuses), incremental_accounting=arm_report["charges"],
            question_rates_scope="partial local relationship probes; no complete page output",
            contended_valid_questions_per_minute=valid / status["wall_seconds"] * 60,
            pages_per_minute=None, pages_per_dollar=None,
        )
        return
    status["completed_pages"] = sum(row.get("status") == "ok" for row in rows)
    status["attempted_pages"] = len(rows)
    rate = status["completed_pages"] / status["wall_seconds"] * 60
    if status["kind"] == "pipeline":
        status["contended_pages_per_minute"] = rate
    else:
        status["incremental_artifact_pages_per_minute"] = rate
        stage, accounting_field = INCREMENTAL_FIELDS[status["kind"]]
        status["incremental_status_counts"] = dict(Counter(row.get(stage, "missing") for row in rows))
        accounting = arm_report[accounting_field]
        status["incremental_accounting"] = accounting
        status["rate_scope"] = "retained artifacts including authentication/copying; original pipeline excluded"


def summarize_rates(statuses: list[dict[str, Any]], wall: float, not_started: list[str]) -> dict[str, Any]:
    """Aggregate independent arms by kind without merging pipeline/incremental rates."""
    by_kind = {}
    for kind in MODULES:
        arms = [status for status in statuses if status["kind"] == kind]
        if kind == "micro":
            complete = bool(arms) and all(
                "valid_returned_questions" in status and not status.get("report_metrics_error") for status in arms
            ) and not not_started
            questions = sum(status.get("valid_returned_questions", 0) for status in arms)
            by_kind[kind] = {
                "valid_returned_questions_known": questions, "complete_metrics": complete,
                "scope": "partial local relationship probes; no complete page output", "arm_count": len(arms),
                "valid_returned_questions_per_minute": questions / wall * 60 if complete and wall else None,
                "pages_per_minute": None, "pages_per_dollar": None,
            }
            continue
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


def next_launch_index(ordered: list[dict[str, Any]], active: list[dict[str, Any]], limit: int) -> int | None:
    """Overlap lightweight arms while retaining the three-heavy-worker CPU bound."""
    if len(active) >= limit:
        return None
    heavy = {"pipeline", "candidate", "admission", "diagram", "header"}
    heavy_count = sum(arm.get("kind", "pipeline") in heavy for arm in active)
    return next((i for i, arm in enumerate(ordered)
                 if heavy_count < MAX_CONCURRENT or arm.get("kind", "pipeline") not in heavy), None)


def validate_coordination(plan: list[dict[str, Any]], max_arms: int,  # noqa: C901, PLR0912 - fail-closed sharing checks.
                          primary: dict[str, Any], ledger: dict[str, Any]) -> None:
    """Validate root's explicit auxiliary micro-only sharing against immutable snapshots."""
    if max_arms != MAX_CONCURRENT or not plan or any(arm.get("kind", "pipeline") != "micro" for arm in plan):
        message = "Coordinated sharing permits at most three MICRO-only hosts"
        raise ValueError(message)
    for arm in plan:
        arguments = arm.get("arguments", [])
        providers = [value.split("=", 1)[1] if "=" in value else arguments[i + 1:i + 2][0]
                     for i, value in enumerate(arguments)
                     if value.split("=", 1)[0] == "--provider" and ("=" in value or i + 1 < len(arguments))]
        if providers != ["openrouter"]:
            message = "Coordinated micro arms require one explicit OpenRouter provider"
            raise ValueError(message)
    expected = POLICY["concurrent_policy"]
    policy = primary.get("policy", {})
    if policy.get("transport_concurrency") != MAX_CONCURRENT or policy.get("concurrent_policy") != expected:
        message = "Primary queue must declare the same P003 three-slot policy"
        raise ValueError(message)
    active = [arm for arm in primary.get("arms", []) if arm.get("status") in {"running", "starting"}]
    if not active or primary.get("interrupted"):
        message = "Root coordination requires an active uninterrupted primary queue"
        raise ValueError(message)
    for arm in active:
        command = arm.get("command", [])
        if (arm.get("kind", "pipeline") != "pipeline" or len(command) < MAX_CONCURRENT
                or command[1:3] != ["-m", "bench.p003_run"]
                or command.count("--transport-concurrency") != 1
                or any(arg.startswith("--transport-concurrency=") for arg in command)
                or command[command.index("--transport-concurrency") + 1:][:1] != ["3"]
                or any("gateway" in arg.lower() or "vercel" in arg.lower() for arg in command)):
            message = "Every active primary arm must use the known pipeline transport3 command"
            raise ValueError(message)
    if ledger.get("concurrent_policy") != expected or ledger.get("concurrent_spend_blocked"):
        message = "Shared ledger policy must already be reconciled and unblocked"
        raise ValueError(message)
    entries = ledger.get("requests")
    if not isinstance(entries, list):
        message = "Complete shared ledger request inventory required"
        raise TypeError(message)
    inflight = [entry for entry in entries if entry.get("concurrent_state") == "in_flight"]
    if len(inflight) > MAX_CONCURRENT:
        message = "Shared ledger exceeds the admitted three-request capacity"
        raise ValueError(message)
    for entry in entries:
        if entry.get("concurrent_state") == "in_flight":
            if (not str(entry.get("tag", "")).startswith("P003/")
                    or entry.get("gateway") != "openrouter" or not entry.get("reservation_uuid")):
                message = "In-flight non-P003 or nonconcurrent OpenRouter work forbids coordinated sharing"
                raise ValueError(message)
        elif entry.get("cost_status") == "reserved" and not entry.get("response_file") and not entry.get("error"):
            message = "Unresolved serial transport admission forbids coordinated sharing"
            raise ValueError(message)


def coordinated_receipt(plan: list[dict[str, Any]], max_arms: int, status: Path, root: Path) -> dict[str, Any]:
    """Root-only read-only policy inspection; no client, credentials or ledger mutation."""
    from bench.decision_hosted import exclusive_lock  # noqa: PLC0415 - no transport construction.

    status = guard_path(status)
    primary_bytes = status.read_bytes()
    directory = guard_path(root / "bench/results/pdf-master-artifacts/decisions")
    with exclusive_lock(directory / "ledger.lock"):
        ledger_bytes = (directory / "ledger.json").read_bytes()
        validate_coordination(plan, max_arms, json.loads(primary_bytes), json.loads(ledger_bytes))
    return {"primary_status_path": str(status.resolve()),
            "primary_status_sha256": hashlib.sha256(primary_bytes).hexdigest(),
            "shared_ledger_sha256_at_admission": hashlib.sha256(ledger_bytes).hexdigest(),
            "shared_concurrent_policy": POLICY["concurrent_policy"],
            "scope": "Explicit root-coordinated MICRO-only auxiliary queue; separate resources, shared transport3",
            "no_other_paid_jobs_root_attested": True, "policy_mutated": False}


def run_queue(  # noqa: C901, PLR0912, PLR0913 - bounded lifecycle and explicit cleanup.
    plan: list[dict[str, Any]], manifest: Path | None, directory: Path, *, seed: int,
              cutoff: float = P003_PAID_CUTOFF, root: Path = ROOT, max_parallel_arms: int = 3,
              coordinated_concurrent_queue: Path | None = None) -> dict[str, Any]:
    """Run only fresh arms, with per-arm snapshots and atomic status checkpoints."""
    directory = guard_path(directory)
    manifest = guard_path(manifest) if manifest is not None else None
    ordered = validate_plan(plan, seed)
    if type(max_parallel_arms) is not int or max_parallel_arms not in (3, 6):
        message = "Queue admits exactly three or six concurrent arms"
        raise ValueError(message)
    coordination = None
    if coordinated_concurrent_queue is not None:
        coordination = coordinated_receipt(ordered, max_parallel_arms, coordinated_concurrent_queue, root)
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
    policy = {**POLICY, "max_concurrent_arms": max_parallel_arms,
              "max_cpu_heavy_arms": 3, "transport_slot_wait": max_parallel_arms > MAX_CONCURRENT,
              "heartbeat_seconds": HEARTBEAT_SECONDS,
              "declared_arm_duration_overrides": True,
              "scheduler": "first eligible in frozen order; pipeline/candidate/admission/diagram/header are CPU-heavy"}
    if coordination is not None:
        policy.update(exclusive_paid_work_required=False, root_coordinated_micro_only=True)
    record = {"policy": policy, "seed": seed, "frozen_order": json.loads(json.dumps(ordered)), "paid_cutoff": cutoff,
              "manifest": str(manifest.resolve()) if manifest is not None else None, "arms": statuses,
              "rates_label": "contended per-arm rates separated by experiment kind",
              "aggregate_rates": None, "max_observed_concurrent_arms": 0}
    if coordination is not None:
        record["coordination"] = coordination
        record["resource_scope"] = (
            "This auxiliary queue and its children only; primary queue resources excluded; shared transport contention"
        )

    last_checkpoint = started

    def checkpoint() -> None:
        nonlocal last_checkpoint
        last_checkpoint = time.monotonic()
        record["resources"] = monitor.result(time.monotonic() - started)
        write_json(directory / "status.json", record)

    interrupted = False
    try:
        while ordered or running:
            remaining = cutoff - time.time()
            while ordered and len(running) < max_parallel_arms and remaining >= START_MARGIN:
                active = [status for _process, _log, status in running.values()]
                selected_index = next_launch_index(ordered, active, max_parallel_arms)
                if selected_index is None:
                    break
                arm = ordered.pop(selected_index)
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
                          "started_at": time.time(), "rate_label": "contended", "retry": False,
                          "max_wall_seconds": arm.get("max_wall_seconds", MAX_WALL)}
                statuses.append(status)
                checkpoint()
                log = (directory / "logs" / (name + ".log")).open("x")
                try:
                    environment = os.environ.copy()
                    environment.pop("JEV_P003_TRANSPORT_SLOTS", None)
                    if max_parallel_arms > MAX_CONCURRENT or coordination is not None:
                        environment["JEV_P003_TRANSPORT_SLOTS"] = "3"
                    process = subprocess.Popen(  # noqa: S603 - fixed module and literal validated arguments.
                        command, cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                        env=environment,
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
                timeout = time.time() - status["started_at"] >= status["max_wall_seconds"] or remaining <= STOP_MARGIN
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
            if time.monotonic() - last_checkpoint >= HEARTBEAT_SECONDS:
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
    parser.add_argument("--max-parallel-arms", type=int, choices=(3, 6), default=3)
    acknowledgment = parser.add_mutually_exclusive_group(required=True)
    acknowledgment.add_argument("--exclusive-paid-work", action="store_true")
    acknowledgment.add_argument("--coordinated-concurrent-queue", type=Path)
    args = parser.parse_args()
    run_queue(json.loads(guard_path(args.plan).read_bytes()), guard_path(args.manifest) if args.manifest else None,
              guard_path(args.directory), seed=args.seed, max_parallel_arms=args.max_parallel_arms,
              coordinated_concurrent_queue=args.coordinated_concurrent_queue)


if __name__ == "__main__":
    main()
