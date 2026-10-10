"""Synthetic SQLite/WAL accounting prototype; deliberately not a production ledger adapter."""

# ruff: noqa: ANN401, EM101, TRY003, PLR0913, PLR2004, E501, SLF001, TRY301, TRY300, FBT001
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Self

from bench import decision_hosted as hosted
from bench import p003_transport_stage_perf as original
from bench.decision_concurrent import ConcurrentDecisionClient
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

RESERVATION = 0.3
CHARGE = 0.001


def check(condition: bool) -> None:
    """Enforce experiment invariants even when Python assertions are disabled."""
    if not condition:
        raise ValueError("Synthetic accounting invariant failed")


class SQLiteLedger:
    """Fresh synthetic database with indexed identities and transactional cached totals."""

    def __init__(self, path: Path, capacity: int, *, synchronous: str = "FULL") -> None:
        """Declare a fresh disposable database and explicit durable-write policy."""
        if capacity not in (3, 6) or synchronous not in ("FULL", "NORMAL"):
            raise ValueError("Explicit bounded synthetic capacity and sync setting required")
        self.path, self.capacity, self.synchronous = path, capacity, synchronous

    def connect(self) -> sqlite3.Connection:
        """Use one independent connection per caller; never share transaction state."""
        connection = sqlite3.connect(self.path, timeout=60, isolation_level=None)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=" + self.synchronous)
        connection.execute("PRAGMA wal_autocheckpoint=1000")
        return connection

    def initialize(self, entries: list[dict[str, Any]]) -> None:
        """Build complete synthetic history outside measured operations."""
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE attempts (
                  idx INTEGER PRIMARY KEY, reservation_uuid TEXT UNIQUE NOT NULL,
                  tag TEXT UNIQUE NOT NULL, request_sha256 TEXT NOT NULL,
                  state TEXT NOT NULL, accounted REAL NOT NULL CHECK(accounted >= 0),
                  reservation REAL NOT NULL, payload TEXT NOT NULL, telemetry TEXT
                );
                CREATE INDEX request_identity ON attempts(request_sha256);
                CREATE INDEX attempt_state ON attempts(state);
                CREATE TABLE totals (
                  singleton INTEGER PRIMARY KEY CHECK(singleton=1), accounted REAL NOT NULL,
                  inflight INTEGER NOT NULL, max_inflight INTEGER NOT NULL, blocked INTEGER NOT NULL
                );
            """)
            connection.execute("BEGIN IMMEDIATE")
            connection.executemany("INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?,NULL)", [
                (entry["index"], entry["reservation_uuid"], entry["tag"], entry["request_sha256"],
                 entry["concurrent_state"], entry["accounted_usd"], entry["reservation_usd"], json.dumps(entry))
                for entry in entries])
            connection.execute("INSERT INTO totals VALUES(1,?,0,0,0)",
                               (math.fsum(entry["accounted_usd"] for entry in entries),))
            connection.execute("COMMIT")

    def reserve(self, connection: sqlite3.Connection, tag: str, request_sha: str) -> dict[str, Any]:
        """Atomically preserve cap, identity, unknown-history and positive reservation semantics."""
        connection.execute("BEGIN IMMEDIATE")
        try:
            total, inflight, _maximum, blocked = connection.execute(
                "SELECT accounted,inflight,max_inflight,blocked FROM totals WHERE singleton=1").fetchone()
            if blocked or inflight >= self.capacity or total + RESERVATION > 50:
                raise RuntimeError("Synthetic admission cap or blocked accounting")
            if not tag.startswith("P003/"):
                raise ValueError("Synthetic P003-only policy")
            if connection.execute("SELECT 1 FROM attempts WHERE tag=?", (tag,)).fetchone():
                raise RuntimeError("Duplicate attempt tag; no retry")
            same = connection.execute("SELECT state FROM attempts WHERE request_sha256=?", (request_sha,)).fetchall()
            if any(state not in ("in_flight", "completed") for (state,) in same):
                raise RuntimeError("Prior identical failure/unknown blocks automatic retry")
            index = connection.execute("SELECT COALESCE(MAX(idx),-1)+1 FROM attempts").fetchone()[0]
            entry = {"index": index, "tag": tag, "request_sha256": request_sha,
                     "reservation_uuid": uuid.uuid4().hex, "concurrent_state": "in_flight",
                     "accounted_usd": RESERVATION, "reservation_usd": RESERVATION,
                     "cost_status": "reserved", "requested_model": original.MODEL}
            connection.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?,NULL)",
                               (index, entry["reservation_uuid"], tag, request_sha, "in_flight",
                                RESERVATION, RESERVATION, json.dumps(entry)))
            connection.execute("UPDATE totals SET accounted=accounted+?,inflight=inflight+1,"
                               "max_inflight=MAX(max_inflight,inflight+1) WHERE singleton=1", (RESERVATION,))
            connection.execute("COMMIT")
            return entry
        except BaseException:
            connection.execute("ROLLBACK")
            raise

    def settle(self, connection: sqlite3.Connection, entry: dict[str, Any], failed: bool) -> None:
        """Settle one UUID exactly once; unknown failures retain their full reservation."""
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = connection.execute("SELECT idx,state,accounted FROM attempts WHERE reservation_uuid=?",
                                     (entry["reservation_uuid"],)).fetchone()
            if row != (entry["index"], "in_flight", RESERVATION):
                raise RuntimeError("Unique unsettled attempt required; duplicate settlement refused")
            charge = RESERVATION if failed else CHARGE
            entry.update(concurrent_state="failed" if failed else "completed", accounted_usd=charge,
                         cost_status="reserved unknown failure" if failed else "provider-reported USD")
            if failed:
                entry["error"] = "SyntheticUnknownFailure"
            else:
                entry["provider_reported_usd"] = CHARGE
                entry["response_file"] = f"synthetic-response-{entry['index']}.json"
            connection.execute("UPDATE attempts SET state=?,accounted=?,payload=? WHERE reservation_uuid=?",
                               (entry["concurrent_state"], charge, json.dumps(entry), entry["reservation_uuid"]))
            connection.execute("UPDATE totals SET accounted=accounted+?,inflight=inflight-1 WHERE singleton=1",
                               (charge - row[2],))
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            raise

    def annotate(self, connection: sqlite3.Connection, entry: dict[str, Any], telemetry: dict[str, Any]) -> None:
        """Update telemetry independently after committed financial settlement."""
        changed = connection.execute("UPDATE attempts SET telemetry=? WHERE reservation_uuid=? AND state!='in_flight'",
                                     (json.dumps(telemetry), entry["reservation_uuid"])).rowcount
        if changed != 1:
            raise RuntimeError("Telemetry requires an exact settled attempt")


class JSONClient(original.MeasuredClient):
    """Instrument unchanged financial methods at synthetic capacity three or six."""

    def __init__(self, base: hosted.DecisionClient, trace: dict[str, Any], opener: Any, capacity: int) -> None:
        """Extend only measurement capacity without altering shared financial methods."""
        ConcurrentDecisionClient.__init__(self, base, max_inflight=capacity, wave_limits={"P003": 50},
                                          opener=opener, allow_matched_replicates=True)
        self.trace, self.phase = trace, "reserve"


def body(index: int) -> dict[str, Any]:
    """Keep every attempt distinct without altering any production request."""
    return {"model": original.MODEL, "state": f"synthetic complete evidence {index}",
            "questions": {"q0": {"type": "choice", "criteria": {"yes": "Yes", "unresolved": "Unresolved"}}}}


def json_request(directory: Path, index: int, capacity: int, provider_delay: float,  # noqa: PLR0917 - stage fixture inputs.
                 export_delay: float, failed: bool, trace: dict[str, Any]) -> None:
    """Actual accounting path with a fake provider and telemetry, never credentials/network."""
    base = hosted.DecisionClient.__new__(hosted.DecisionClient)
    base.root, base.directory, base.ledger = directory, directory, directory / "ledger.json"
    base.key = "SYNTHETIC-NEVER-TRANSMITTED"
    base._prior_api_cost = lambda: 0.0

    class Response:
        """Fake bounded receipt; never implements a network connection."""

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, limit: int) -> bytes:
            """Return a synthetic positive charge or a controlled unknown failure."""
            began = time.perf_counter()
            time.sleep(provider_delay)
            trace["provider_finished"] = time.perf_counter()
            trace["stages"]["provider_read"] = trace["provider_finished"] - began
            if failed:
                raise OSError("Synthetic unknown response; no retry")
            result = {"model": original.MODEL, "usage": {"cost": CHARGE, "prompt_tokens": 50, "completion_tokens": 10},
                      "answers": {"q0": {"type": "choice", "choice": "yes", "probabilities": {"yes": 1, "unresolved": 0}}}}
            raw = json.dumps(result).encode()
            check(len(raw) <= limit)
            return raw

    def opener(_request: Any, *, timeout: float) -> Response:
        check(timeout == 90)
        trace["provider_calls"] += 1
        return Response()

    def telemetry(_body: Any, _result: Any, entry: dict[str, Any]) -> dict[str, Any]:
        began = time.perf_counter()
        trace["stages"]["financial_settlement"] = began - trace["provider_finished"]
        check(entry["concurrent_state"] != "in_flight")
        time.sleep(export_delay)
        trace["stages"]["export"] = time.perf_counter() - began
        return {"status": "synthetic", "delay_seconds": export_delay}

    base._telemetry = telemetry
    client = JSONClient(base, trace, opener, capacity)
    try:
        result = client.request(body(index), tag=f"P003/synthetic/{index}", replay=False, reservation_usd=RESERVATION)
        trace["entry"] = result["entry"]
    except RuntimeError:
        if not failed:
            raise
        trace["unknown_failure"] = True


def sqlite_request(ledger: SQLiteLedger, index: int, provider_delay: float,  # noqa: PLR0917 - stage fixture inputs.
                   export_delay: float, failed: bool, trace: dict[str, Any]) -> None:
    """Match stage order while using independent indexed financial transactions."""
    connection = ledger.connect()
    try:
        encoded = json.dumps(body(index), separators=(",", ":"), allow_nan=False).encode()
        began = time.perf_counter()
        entry = ledger.reserve(connection, f"P003/synthetic/{index}", sha(encoded))
        trace["stages"]["reserve"] = time.perf_counter() - began
        began = time.perf_counter()
        trace["provider_calls"] += 1
        time.sleep(provider_delay)
        trace["stages"]["provider_read"] = time.perf_counter() - began
        began = time.perf_counter()
        ledger.settle(connection, entry, failed)
        trace["stages"]["financial_settlement"] = time.perf_counter() - began
        began = time.perf_counter()
        time.sleep(export_delay)
        trace["stages"]["export"] = time.perf_counter() - began
        began = time.perf_counter()
        ledger.annotate(connection, entry, {"status": "synthetic", "delay_seconds": export_delay})
        trace["stages"]["annotation"] = time.perf_counter() - began
        trace["entry"] = entry
    finally:
        connection.close()


def measure(output: Path, backend: str, count: int, *, workers: int = 3, attempts: int = 30,
            provider_delay: float = 0.05, export_delay: float = 0, synchronous: str = "FULL") -> dict[str, Any]:
    """Measure bounded distinct fresh attempts; initialization excluded, all failures charged conservatively."""
    if (backend not in ("json", "sqlite") or workers not in (3, 6) or attempts not in (3, 6, 30, 60)
            or not 0 <= provider_delay <= 1 or not 0 <= export_delay <= 1):
        raise ValueError("Explicit bounded synthetic matrix required")
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=False)
    history = original.synthetic_ledger(count)
    history["concurrent_policy"] = {**history["concurrent_policy"], "max_inflight": workers}
    ledger = SQLiteLedger(output / "ledger.sqlite", workers, synchronous=synchronous)
    keeper = None
    if backend == "json":
        hosted.checkpoint(output / "ledger.json", history)
    else:
        ledger.initialize(history["requests"])
        keeper = ledger.connect()  # Hold WAL resident until byte measurement; no transaction held.
    initial_storage = {path.name: path.stat().st_size for path in output.glob("ledger*") if path.is_file()}
    del history
    semaphore = threading.BoundedSemaphore(workers)

    submitted = time.perf_counter()

    def call(index: int) -> dict[str, Any]:
        trace = {"index": index, "stages": {}, "nested_events": [], "provider_calls": 0,
                 "expected_unknown_failure": index % 10 == 9}
        began = time.perf_counter()
        trace["batch_enqueue_to_thread_begin_seconds"] = began - submitted
        with semaphore:
            occupied = time.perf_counter()
            trace["slot_wait_seconds"] = occupied - began
            if backend == "json":
                json_request(output, index, workers, provider_delay, export_delay, trace["expected_unknown_failure"], trace)
            else:
                sqlite_request(ledger, index, provider_delay, export_delay, trace["expected_unknown_failure"], trace)
            trace["slot_occupied_seconds"] = time.perf_counter() - occupied
        trace["client_wall_seconds"] = time.perf_counter() - began
        trace["stages"]["other_inside_slot"] = max(0, trace["slot_occupied_seconds"] - sum(trace["stages"].values()))
        return trace

    with Resources() as resources, ThreadPoolExecutor(max_workers=workers) as executor:
        traces = list(executor.map(call, range(attempts)))
    if backend == "json":
        entries = json.loads((output / "ledger.json").read_bytes())["requests"]
        max_inflight = None  # Actual persistent cap checked by unchanged client, not continuously sampled.
        cached_total = math.fsum(entry["accounted_usd"] for entry in entries)
    else:
        check(keeper is not None)
        entries = [json.loads(row[0]) for row in keeper.execute("SELECT payload FROM attempts ORDER BY idx")]
        cached_total, inflight, max_inflight = keeper.execute(
            "SELECT accounted,inflight,max_inflight FROM totals WHERE singleton=1").fetchone()
        check(inflight == 0 and max_inflight <= workers)
    fresh = entries[count:]
    unknowns = sum(index % 10 == 9 for index in range(attempts))
    expected_total = count * 0.0001 + (attempts - unknowns) * CHARGE + unknowns * RESERVATION
    check(len(fresh) == attempts and len({entry["reservation_uuid"] for entry in fresh}) == attempts)
    check([entry["index"] for entry in entries] == list(range(count + attempts)))
    check(math.isclose(math.fsum(entry["accounted_usd"] for entry in entries), expected_total, abs_tol=1e-8))
    check(math.isclose(cached_total, expected_total, abs_tol=1e-8))
    check(sum(entry["concurrent_state"] == "failed" for entry in fresh) == unknowns)
    check(all(trace["provider_calls"] == 1 for trace in traces))
    storage = {path.name: path.stat().st_size for path in output.glob("ledger*") if path.is_file()}
    result = {"backend": backend, "history_count": count, "attempts": attempts, "workers": workers,
              "transport_slots": workers, "provider_delay_seconds": provider_delay, "export_delay_seconds": export_delay,
              "sqlite_settings": {"journal_mode": "WAL", "synchronous": synchronous, "wal_autocheckpoint": 1000,
                                  "busy_timeout_seconds": 60} if backend == "sqlite" else None,
              "json_durability": "Unchanged hosted.checkpoint; no additional fsync inserted",
              "metrics": resources.summary(), "storage_bytes_before_final_connection_close": storage,
              "storage_bytes_before_measured_attempts": initial_storage,
              "durability_measurement": "Declared SQLite synchronous setting; fsync system-call count/latency and crash durability unmeasured",
              "traces": traces, "maximum_persistent_inflight": max_inflight,
              "unknown_failures": unknowns, "synthetic_accounted_usd": expected_total,
              "fresh_synthetic_accounted_usd": expected_total - count * 0.0001,
              "invariants_passed": True, "network_calls": 0, "real_inference_usd": 0,
              "summed_stage_seconds": {stage: sum(t["stages"][stage] for t in traces) for stage in traces[0]["stages"]},
              "summed_slot_occupied_seconds": sum(t["slot_occupied_seconds"] for t in traces),
              "summed_slot_wait_seconds": sum(t["slot_wait_seconds"] for t in traces),
              "scope": "Synthetic one-process threaded accounting; not hosted throughput, quality or deployable adapter",
              "code_sha256": {name: sha(Path(__file__).with_name(name).read_bytes()) for name in
                               (*original.CODE_FILES, "p003_sqlite_ledger_perf.py")},
              "omitted_guarantees": ["SQLite omits real HTTP/raw request-response artifact persistence and size/model admission",
                  "SQLite models one P003 wave cap only; campaign/cumulative/prior-rental/wave deadlines omitted",
                  "No crash recovery, fsync fault injection, cross-process stress or migrations",
                  "No BYOK/catalog estimate fallback, provider metadata, diagnostic redaction or Langfuse exporter",
                  "SQLite totals checked against full inventory afterward; no real ledger copied or production client changed",
                  "JSON historical prior-API accounting stubbed; controlled export delay is not actual telemetry",
                  "Single-process GIL/OS cache and SQLite durability differ from current multiprocess production"]}
    if keeper is not None:
        keeper.close()
    write_json(output / "report.json", result)
    write_json(output / "resources.json", resources.samples)
    return result


def main() -> None:
    """Run a bounded synthetic matrix with no production configuration changes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--history-count", type=int, choices=original.COUNTS, action="append")
    parser.add_argument("--attempts", type=int, choices=(30, 60), default=30)
    parser.add_argument("--export-delay", type=float, default=0)
    args = parser.parse_args()
    output = guard_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for count in args.history_count or original.COUNTS:
        for workers in (3, 6):
            for backend in ("json", "sqlite"):
                result = measure(output / f"{backend}-{count}-{workers}", backend, count,
                                 workers=workers, attempts=args.attempts, export_delay=args.export_delay)
                rows.append({key: result[key] for key in ("backend", "history_count", "workers", "metrics",
                             "attempts", "unknown_failures", "summed_stage_seconds", "storage_bytes_before_final_connection_close")})
                print(json.dumps(rows[-1]), flush=True)
    write_json(output / "report.json", {"rows": rows, "network_calls": 0, "production_changes": False,
                                       "scope": "Synthetic architecture experiment only", "machine_cpu_count": os.cpu_count()})


if __name__ == "__main__":
    main()
