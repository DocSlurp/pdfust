# Synthetic indexed ledger experiment

The indexed SQLite/WAL prototype makes the synthetic short-call workload much
cheaper than the existing JSON financial path. Increasing JSON capacity from
three to six did not improve useful throughput in this one-process experiment.
This supports investigating bookkeeping architecture; it does not establish
production throughput or authorize a ledger migration.

Every arm uses 23,000 independently generated historical entries and 30
distinct fresh attempts. The fake provider waits 50 ms. Twenty-seven receipts
report USD 0.001 each; three unknown transport failures retain their full USD
0.30 reservation. Fresh synthetic accounting is therefore USD 0.927. Both
implementations check complete totals, contiguous indexes, unique reservation
UUIDs, single transmission and zero remaining in-flight attempts. SQLite also
records maximum persistent in-flight count, enforces its cap transactionally,
rejects duplicate settlement and blocks an identical failed request from retry.
None of these synthetic amounts are real charges.

| Backend | Workers / slots | Export delay | Wall seconds | CPU seconds | Sampled peak RSS, MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Actual JSON financial methods | 3 | 0 | 32.64 | 31.82 | 338.6 |
| SQLite WAL/FULL prototype | 3 | 0 | 0.542 | 0.039 | 198.5 |
| Actual JSON financial methods | 6 | 0 | 33.36 | 32.52 | 543.6 |
| SQLite WAL/FULL prototype | 6 | 0 | 0.322 | 0.043 | 229.6 |
| Actual JSON financial methods | 3 | 0.5 s | 32.21 | 31.26 | 339.9 |
| SQLite WAL/FULL prototype | 3 | 0.5 s | 5.544 | 0.046 | 246.3 |
| Actual JSON financial methods | 6 | 0.5 s | 35.64 | 34.64 | 544.4 |
| SQLite WAL/FULL prototype | 6 | 0.5 s | 2.827 | 0.053 | 229.6 |

Zero-export scaling controls show the JSON history-size dependence. At 1000
entries, JSON takes 1.96/1.98 seconds for three/six workers; at 10,000 it takes
15.90/16.72 seconds. SQLite remains near 0.55/0.32 seconds at both sizes. All
30-attempt accounting invariants also pass in those controls.

The zero-export JSON reserve/settlement/annotation stages sum to 92.3 seconds
across the three-worker calls and 190.3 seconds with six workers. These sums
include lock waiting and overlap between threads; they are not additional CPU
or elapsed time. Each arm consumes about one CPU core overall. Even the fake
50 ms provider reads sum to 4.6–4.7 seconds in JSON, versus the intended 1.5
seconds in SQLite, consistent with scheduling/GIL delay around serialized local
work. This experiment does not measure remote provider service time.

With delayed export, SQLite's summed export occupancy is about 15 seconds and
dominates its occupied slots. JSON remains dominated by bookkeeping. All slots
deliberately cover reserve, provider, settlement, synchronous export and
annotation, preserving the measured lifecycle. Task enqueue-to-thread delay is
recorded separately from semaphore wait. Thirty tasks use only three or six
active threads; they do not become 30 simultaneous reservations.

SQLite stores an indexed attempt table and transactional aggregate totals.
Each caller opens an independent connection and uses `BEGIN IMMEDIATE` for
reserve and settlement. The prototype uses WAL, `synchronous=FULL`, a 60-second
busy timeout and automatic checkpoint at 1000 pages. Annotation is a separate
transaction after financial settlement. Database size is 35.4 MB and resident
WAL size 35.7 MB, plus 98 KB shared-memory file, before the last held connection
closes. Much of this allocated WAL belongs to fixture construction; both initial
and final sizes are retained. JSON ends at 23.9 MB. SQLite is not a storage-size
win here. Actual fsync count/latency and power-loss durability were not measured.
The JSON control uses unchanged `hosted.checkpoint` durability behavior; no
extra fsync was inserted to make the comparison favorable.

Comparability has strict limits. JSON executes the unchanged real financial
reserve, settlement and telemetry annotation methods through narrow timing
hooks, with only a fake provider and delayed telemetry stub. SQLite implements
the synthetic fixed-charge, P003-only accounting scenario. It omits production
HTTP, raw request/response artifact persistence, bounded model/payload admission,
catalog estimates, BYOK metadata, diagnostics, campaign/cumulative/prior-rental
limits, deadlines, reservation overrun handling, arm circuit breaking, migration
and crash recovery. Tags are uniquely indexed, a stricter rule than production
for changed bodies. Those differences do not affect these distinct fixed-input
attempts, but prevent any drop-in or deployable-adapter claim. A full production
implementation would require those guarantees and independent fault testing.

The experiment runs on Python 3.14.7, Linux, eight visible/affinity CPUs, with
OMP/MKL/OpenBLAS thread settings 2. One process hosts three or six worker threads;
provider/export waits are controlled sleeps. Process CPU and RSS sampled every
100 ms include only the measured attempt interval. Fixture construction,
database population, imports and post-run conservation checks are excluded.
Fresh fixtures are used but OS cache is not reset, and sequential runs retain
allocator/cache effects; sampled RSS is not a clean independent-process comparison.
There are no live-ledger copies, credentials, network calls, inference, GPU work
or full-pipeline/quality claims. All production clients remain unchanged.

```sh
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
python -m bench.p003_sqlite_ledger_perf --history-count 23000 --attempts 30 \
  --export-delay 0 --output /absolute/path/fresh-zero-control
```

Repeat with `--export-delay 0.5` for the synchronous-export treatment. The CLI
also admits 1000/10000-entry scaling controls and 60 attempts. The module is
standalone research code. Ten focused CPU tests exercise both backends and
capacities, positive and unknown accounting, strict identity, cap refusal and
duplicate settlement, while trapping actual network/client initialization.
Invariant checks remain active under Python optimization.
