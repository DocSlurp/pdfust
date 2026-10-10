# Synthetic transport-stage diagnosis

The unchanged financial path performs measurable local work as the ledger grows. This screening supports a real stage trace before increasing capacity or changing telemetry. It does **not** establish a production throughput gain or justify an outbox implementation yet. No production module, live ledger, reservation policy, credentials, network or GPU was accessed or changed.

`bench.p003_transport_stage_perf` invokes the actual `ConcurrentDecisionClient` reserve, full ledger validation, original positive-provider-charge accounting, unique settlement and telemetry annotation code. Three independent exact `DecisionClient.__new__` bases share actual persistent max-three admission and actual process-safe transport slot locks. The only stubs are the provider response, telemetry export and prior historical API-cost scan. The provider reports a positive synthetic USD0.001 charge per request; these values are accounting fixtures, not real spending. Requests use identical bodies and independently named P003 arms, exercising the existing matched-replicate policy.

The fixture contains complete retained accounting rows with contiguous indexes, unique request hashes and reservations, original response-file references and telemetry fields. It is generated locally, not copied from any live ledger. Every measured batch validates three distinct reservations, three actual fake provider calls, and exactly three once-only USD0.001 settlements. A sentinel test deliberately skips cost accounting and verifies that the completion oracle rejects it.

The predeclared diagnostic matrix uses 1k/10k/23k historical entries, three simultaneous requests, fake 50ms provider reads, and zero versus 500ms telemetry export delay. It times exclusive reserve, provider-read, financial-settlement, export, annotation and residual inside-slot stages; slot wait is separate. Nested load/validate and settlement/checkpoint events overlap these stages and must not be added to them. Fixture construction, initial ledger encoding, imports and code freezing are outside the request interval. No codec-only benchmark was repeated.

Primary matrix v2:

| History | Export delay/request | Batch wall (s) | Process CPU (s) | Peak sampled RSS (MiB) | Export fraction of summed slot occupancy |
|---:|---:|---:|---:|---:|---:|
| 1,000 | 0 | 0.176 | 0.153 | 46.1 | <0.1% |
| 1,000 | 0.5s | 0.654 | 0.165 | 48.4 | 79.7% |
| 10,000 | 0 | 1.530 | 1.482 | 133.8 | <0.1% |
| 10,000 | 0.5s | 1.739 | 1.490 | 129.3 | 32.0% |
| 23,000 | 0 | 3.681 | 3.591 | 320.2 | <0.1% |
| 23,000 | 0.5s | 3.760 | 3.638 | 314.9 | 17.7% |

The 23k synthetic ledger is 23,835,606 bytes before the three fresh attempts, similar in scale to root's separately measured immutable real snapshot. Zero-export summed overlapping caller times were reserve 2.634s, financial settlement 3.130s, and annotation 3.494s. These sums exceed batch wall because callers overlap and wait on the shared lock. Each of the three phases performs a full load/validation/checkpoint; none was removed to make this diagnostic faster.

The imposed 500ms export delay is demonstrably inside the current slot lifetime. Its sum was 1.793s at 23k because thread scheduling delayed wakeups. Batch wall increased only 0.080s in this particular matched control: export overlaps competing ledger work and changes annotation contention. It would be incorrect to equate time spent exporting with an equal end-to-end saving. More slots could move the bottleneck to financial locking and JSON work; releasing slots before settlement would weaken safety and is outside this experiment.

Limitations are material. This is one CPU process with three threads, while root's paid queue uses independent processes. The GIL extends fake-provider and fake-export wakeup times during JSON work. Prior API accounting is stubbed to zero, actual Langfuse behavior is unmeasured, and fixture history remains resident alongside the financial path. OS caches and Python allocator history are not reset. Measurements were contended with other work, with one observation per cell. Earlier matrix v1 measured 23k zero-export 4.161s and delayed-export 5.252s, illustrating environmental/scheduling variability; its source snapshot and raw failures/outputs are preserved. There is no confidence interval or acceptance claim.

Environment: Python 3.14.7, Linux 7.2.5, eight machine CPUs/eight affinity CPUs. CPU is `process_time` for the entire process including all three threads. RSS is `psutil.Process` sampled every 100ms, including the retained synthetic fixture and sampler; wall is `perf_counter`. Each fresh measured folder archives the exact local code and its hashes. Full raw reports, stage traces, ledgers, responses and resource samples remain ignored under this worktree's `bench/results/pdf-master-artifacts/p003-transport-stage-matrix-v{1,2}/`.

```bash
.venv/bin/python -m bench.p003_transport_stage_perf \
  --output bench/results/pdf-master-artifacts/p003-transport-stage-matrix-fresh \
  --provider-delay 0.05 --delayed-export 0.5
```

Four CPU-only tests cover forbidden credential-loading construction/network access, unchanged positive-charge accounting, identical-body matched admission, once-only reservation settlement, exact stage partition, bounded controls/fresh output, and skipped-accounting rejection. Root's next useful measurement is production stage timing without changing existing source identities until strict continuations complete. The production decision remains open.
