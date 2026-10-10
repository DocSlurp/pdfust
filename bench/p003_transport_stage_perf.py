"""CPU-only synthetic measurement of unchanged concurrent transport bookkeeping."""

# ruff: noqa: ANN401, EM101, TRY003, SLF001, PLR2004, PERF401
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Self

from bench import decision_hosted as hosted
from bench.decision_concurrent import ConcurrentDecisionClient
from bench.p003_client import transport_slot
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

COUNTS = (1000, 10000, 23000)
MODEL = "perplexity/pplx-decider-v1.1-27b"
POLICY = {"max_inflight": 3, "wave_limits_usd": {"P003": 50.0}, "allow_matched_replicates": True}
CODE_FILES = (
    "p003_transport_stage_perf.py",
    "decision_concurrent.py",
    "decision_hosted.py",
    "p003_client.py",
    "research_policy.py",
    "pipeline_run.py",
)


def synthetic_ledger(count: int) -> dict[str, Any]:
    """Create schema-complete positive synthetic accounting, never copied from live evidence."""
    if type(count) is not int or not 0 <= count <= 23000:
        raise ValueError("Synthetic historical request count must be bounded by 23000")
    entries = []
    for i in range(count):
        entries.append(
            {
                "index": i,
                "tag": f"P003/synthetic-history/page-{i}/0",
                "gateway": "openrouter",
                "requested_model": MODEL,
                "served_model": MODEL,
                "provider": "synthetic-provider",
                "generation_id": f"synthetic-generation-{i}",
                "request_sha256": hashlib.sha256(f"synthetic-history-{i}".encode()).hexdigest(),
                "request_bytes": 1600,
                "case_count": 1,
                "force_transmission": True,
                "accounted_usd": 0.0001,
                "provider_reported_usd": 0.0001,
                "reservation_usd": 0.3,
                "cost_status": "provider-reported USD",
                "prior_accounted_usd": hosted.PRIOR_RENTAL,
                "started_at": 1000.0 + i,
                "completed_at": 1000.5 + i,
                "elapsed_ms": 500.0,
                "concurrent_state": "completed",
                "reservation_uuid": f"synthetic-reservation-{i}",
                "response_file": f"synthetic-unread-response-{i}.json",
                "telemetry": {"status": "synthetic", "trace_id": f"synthetic-trace-{i}"},
            }
        )
    return {
        "campaign_limit_usd": hosted.CAMPAIGN_LIMIT,
        "authorized_total_usd": hosted.TOTAL_LIMIT,
        "prior_rental_reported_usd": hosted.PRIOR_RENTAL,
        "concurrent_policy": POLICY,
        "requests": entries,
    }


class MeasuredClient(ConcurrentDecisionClient):
    """Time actual financial code through narrow subclass hooks, never edit production."""

    def __init__(self, base: hosted.DecisionClient, trace: dict[str, Any], opener: Any) -> None:
        """Wrap one exact uninitialized/no-credentials base and fake provider."""
        super().__init__(base, max_inflight=3, wave_limits={"P003": 50}, opener=opener, allow_matched_replicates=True)
        self.trace = trace
        self.phase = "reserve"

    def _load(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            return super()._load()
        finally:
            self.trace["nested_events"].append(
                {"phase": self.phase, "event": "load_validate", "wall_seconds": time.perf_counter() - start}
            )

    def _reserve(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        start = time.perf_counter()
        self.phase = "reserve"
        try:
            return super()._reserve(*args, **kwargs)
        finally:
            self.trace["stages"]["reserve"] = time.perf_counter() - start
            self.phase = "financial_settlement"

    def _settle_locked(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            return super()._settle_locked(*args, **kwargs)
        finally:
            self.trace["nested_events"].append(
                {
                    "phase": "financial_settlement",
                    "event": "settle_patch_checkpoint",
                    "wall_seconds": time.perf_counter() - start,
                }
            )

    def _annotate_telemetry(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        start = time.perf_counter()
        self.phase = "annotation"
        try:
            return super()._annotate_telemetry(*args, **kwargs)
        finally:
            self.trace["stages"]["annotation"] = time.perf_counter() - start


def independent_request(directory: Path, index: int, provider_delay: float, export_delay: float) -> dict[str, Any]:
    """Run one synthetic call through actual shared financial code and local slot lifecycle."""
    trace: dict[str, Any] = {"index": index, "stages": {}, "nested_events": []}
    base = hosted.DecisionClient.__new__(hosted.DecisionClient)
    base.root, base.directory, base.ledger = directory, directory, directory / "ledger.json"
    base.key = "SYNTHETIC-NEVER-TRANSMITTED"
    base._prior_api_cost = lambda: 0.0

    class Response:
        """Fake provider response; no network implementation is reachable."""

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, limit: int) -> bytes:
            """Simulate bounded provider wait and return positive reported accounting."""
            start = time.perf_counter()
            time.sleep(provider_delay)
            result = {
                "id": f"synthetic-fresh-{index}",
                "model": MODEL,
                "provider": "synthetic-provider",
                "usage": {"cost": 0.001, "prompt_tokens": 50, "completion_tokens": 10},
                "answers": {
                    "q0": {"type": "choice", "choice": "yes", "probabilities": {"yes": 0.9, "unresolved": 0.1}}
                },
            }
            raw = json.dumps(result, separators=(",", ":")).encode()
            if len(raw) > limit:
                raise ValueError("Synthetic receipt unexpectedly exceeds read cap")
            trace["provider_finished"] = time.perf_counter()
            trace["stages"]["provider_read"] = trace["provider_finished"] - start
            return raw

    def opener(request: Any, *, timeout: float) -> Response:
        if request.full_url != "https://openrouter.ai/api/alpha/decisions" or timeout != 90:
            raise ValueError("Unexpected fake transport contract")
        trace["fake_provider_calls"] = trace.get("fake_provider_calls", 0) + 1
        return Response()

    def telemetry(_body: Any, _result: Any, entry: dict[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        trace["stages"]["financial_settlement"] = start - trace["provider_finished"]
        if entry["cost_status"] != "provider-reported USD" or entry["concurrent_state"] != "completed":
            raise ValueError("Export began before durable synthetic accounting")
        time.sleep(export_delay)
        trace["stages"]["export"] = time.perf_counter() - start
        return {
            "status": "synthetic-delayed-export" if export_delay else "synthetic-zero-export",
            "delay_seconds": export_delay,
            "trace_id": f"synthetic-fresh-trace-{index}",
        }

    base._telemetry = telemetry
    client = MeasuredClient(base, trace, opener)
    body = {
        "model": MODEL,
        "state": "identical synthetic evidence",
        "questions": {"q0": {"type": "choice", "criteria": {"yes": "Yes", "unresolved": "Unresolved"}}},
    }
    began = time.perf_counter()
    with transport_slot(directory, enabled=True) as waited:
        acquired = time.perf_counter()
        response = client.request(
            body, tag=f"P003/synthetic-fresh-arm-{index}/page/0", replay=False, reservation_usd=0.3
        )
        trace["slot_occupied_seconds"] = time.perf_counter() - acquired
    trace["slot_wait_seconds"] = waited
    trace["client_wall_seconds"] = time.perf_counter() - began
    trace["stages"]["other_inside_slot"] = max(0.0, trace["slot_occupied_seconds"] - sum(trace["stages"].values()))
    trace["entry"] = response["entry"]
    return trace


def measure(
    output: Path, count: int, *, provider_delay: float = 0.05, export_delay: float = 0.0, workers: int = 3
) -> dict[str, Any]:
    """Measure three independent callers on a fresh disposable synthetic ledger."""
    output = guard_path(output)
    if workers != 3 or any(type(v) not in (int, float) or not 0 <= v <= 10 for v in (provider_delay, export_delay)):
        raise ValueError("Three callers and bounded zero-to-ten second fake delays required")
    output.mkdir(parents=True, exist_ok=False)
    (output / "code").mkdir()
    for name in CODE_FILES:
        shutil.copyfile(Path(__file__).with_name(name), output / "code" / name)
    ledger = synthetic_ledger(count)
    # Fixture construction/encoding are outside the measured request interval.
    hosted.checkpoint(output / "ledger.json", ledger)
    initial_bytes = (output / "ledger.json").stat().st_size
    with Resources() as resources, ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(independent_request, output, i, provider_delay, export_delay) for i in range(3)]
        traces = [future.result() for future in futures]
    final = json.loads((output / "ledger.json").read_bytes())
    fresh = final["requests"][count:]
    if (
        len(fresh) != 3
        or len({r["reservation_uuid"] for r in fresh}) != 3
        or any(r["concurrent_state"] != "completed" or r["accounted_usd"] != 0.001 for r in fresh)
    ):
        raise ValueError("Synthetic financial settlement conservation failed")
    metrics = resources.summary()
    result = {
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine_cpu_count": os.cpu_count(),
            "cpu_affinity_count": len(os.sched_getaffinity(0)),
            "coldness": "fresh ledger/client; imports and fixture encoding excluded; OS cache not reset",
        },
        "history_count": count,
        "provider_delay_seconds": provider_delay,
        "export_delay_seconds": export_delay,
        "callers": 3,
        "transport_slots": 3,
        "ledger_initial_bytes": initial_bytes,
        "ledger_final_bytes": (output / "ledger.json").stat().st_size,
        "metrics": metrics,
        "traces": traces,
        "summed_stage_seconds": {key: sum(t["stages"][key] for t in traces) for key in traces[0]["stages"]},
        "local_synthetic_calls_per_minute": 3 / metrics["wall_seconds"] * 60,
        "slot_export_fraction": sum(t["stages"]["export"] for t in traces)
        / sum(t["slot_occupied_seconds"] for t in traces),
        "scope": "One CPU process, three independent threads, unchanged actual financial client/locks; "
        "fake provider/export",
        "network_calls": 0,
        "real_inference_usd": 0,
        "quality_or_full_pipeline_rate": None,
        "accounting_test_only_synthetic_usd": 0.003,
        "limitations": [
            "One process and three threads; GIL wakeup delay differs from root multi-process arms",
            "Historical prior-API accounting scan stubbed to zero; no live records or credentials",
            "Export is a controlled delay stub, not actual Langfuse behavior",
            "Nested events overlap exclusive stages and must not be added to their totals",
            "Local synthetic throughput does not estimate hosted throughput or quality",
        ],
        "code_sha256": {name: sha(Path(__file__).with_name(name).read_bytes()) for name in CODE_FILES},
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Run an explicit bounded offline matrix, never construct a credential-loading client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--history-count", type=int, choices=COUNTS, action="append")
    parser.add_argument("--provider-delay", type=float, default=0.05)
    parser.add_argument("--delayed-export", type=float, default=0.5)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for count in args.history_count or COUNTS:
        for delay in (0.0, args.delayed_export):
            results.append(
                measure(
                    args.output / f"history-{count}-export-{delay:g}",
                    count,
                    provider_delay=args.provider_delay,
                    export_delay=delay,
                )
            )
    write_json(
        args.output / "report.json",
        {"results": results, "network_calls": 0, "scope": "synthetic local path measurement, not hosted throughput"},
    )
    print(
        json.dumps(
            [
                {k: r[k] for k in ("history_count", "export_delay_seconds", "metrics", "slot_export_fraction")}
                for r in results
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
