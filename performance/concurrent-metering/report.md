# Bounded concurrent metering experiment

A separate fresh-only wrapper is feasible without changing DecisionClient. The
wrapper reserves a unique UUID/index under the existing ledger flock, releases
that lock for HTTP and bounded response reads, then retains the raw receipt and
settles only its reservation against a freshly loaded ledger in one locked local
operation. Optional Langfuse export runs outside the lock. A second UUID-only
annotation adds telemetry without overwriting financial state or unrelated rows.
No runner or default behavior was changed, and no real inference was executed.

```python
client = ConcurrentDecisionClient(
    existing_decision_client,
    max_inflight=4,
    wave_limits={"P002": 50.0},
)
response = client.request(
    body,
    tag="P002/run/page-id",
    max_body_bytes=750_000,
    replay=False,
    reservation_usd=model_specific_worst_case_usd,
)
```

The constructor reads no credentials and requires the exact existing OpenRouter
DecisionClient type. It retains compatible `root`, `directory`, `ledger`, request
and response filenames, result/entry/replayed return keys, catalog pricing, and
optional telemetry hooks. Each admission validates the cumulative, campaign and
wave limits while accounting for all existing charges and unresolved reserves.
The first reservation freezes the concurrency/wave policy in the shared ledger;
subsequent wrapper instances must match it. The default is two in-flight requests;
the explicit supported bound is one through eight. Replay and retry are rejected.

The 21 new mocked tests and 76 existing client tests pass (97 total). Focused Ruff
and mypy checks pass. Tests cover overlapping HTTP calls, cap oversubscription,
duplicate in-flight requests, completion in reverse order, unrelated ledger edits,
financial changes during transport, failed financial checkpoints, unknown charges,
reported zero with catalog estimates, bounded oversized/malformed raw responses,
HTTP failure diagnostics, provider overruns, telemetry errors and checkpoint
failure, and 24 queued fresh requests with four workers. Slow telemetry permits
new admission after financial settlement. An unresolved retained response blocks
further admission after a failed financial checkpoint; no reservation expires or
is automatically released.

The measured pytest subprocess used 0.902 seconds wall, 0.810 seconds CPU,
69.16 MiB sampled peak RSS (psutil at 100 ms), and 68.57 MiB lifetime peak RSS
(getrusage children). Scope is the single CPU-only pytest subprocess, with mocked
transport only. Exact test output and measurements are retained locally under
`bench/results/pdf-master-artifacts/pipeline-p002/concurrent-metering-mock-tests/`.
These measurements establish test cost, not production throughput or quality.

Actual spend guarantees require a sufficient per-request worst-case reservation.
Reported charges above that reservation are retained truthfully and block future
admission; requests already in flight cannot be undone. Unknown charges retain the
full reserve. A process crash retains its in-flight slot until offline investigation.
Historical prior-cost ledgers must remain immutable during the experiment. Every
concurrent request in a wave must use atomic wave admission: an older caller's
external wave check does not become atomic merely by sharing this ledger.

Receipt/checkpoint disk failures can leave an unresolved reservation; this is
fail-closed rather than a retransmission opportunity. Telemetry checkpoint failure
leaves financial settlement and raw receipt intact and reports an explicit error.
A financial checkpoint failure still attempts the existing optional trace hook
outside the lock, with its independent marker; it cannot annotate the failed ledger.
Private accounting/telemetry helper reuse creates a compatibility dependency on
DecisionClient and should be reviewed whenever that module changes. Cross-process
coordination uses the existing native file lock; the acceptance races here were
threaded mocks on Linux, not a Windows or process-crash integration measurement.

A later matched whole-page vision-only run can compare serial and four-worker
wall time with the same frozen pages, model, render settings and reservation policy.
Measure whole-run CPU/RSS directly; overlapping per-page CPU is nonadditive. Keep
OCR/native/detector workers outside that first experiment. No quality or live
latency conclusion follows from these mocked accounting checks.
