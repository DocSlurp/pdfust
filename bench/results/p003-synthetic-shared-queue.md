# Standalone shared-context queue integration

`p003_synthetic_shared_queue.py` declares all 56 arms: 14 independently configured decision models, group sizes four/eight, and geometry-only/rows-and-rules evidence. The native request count is 252, with 24 question outcomes per arm. Grouping and execution ordering are separately deterministic: source-ID hash grouping comes from the frozen helper, while the queue uses seed 20261010 to shuffle arms. Inputs are unchanged synthetic v2 source evidence; no labels or hosted calls enter preparation.

The driver imports the existing `p003_parallel` scheduler in its own process. A context manager temporarily adds the new kind, question scope, shared-request counters and heavy-arm classification, then restores every altered module attribute even after an exception. It does not edit the existing queue or active helpers. The queue implementation is explicitly pinned to SHA256 `8b384404ad54c7a854f323cd567fa8c5e28eab285f85e51dcec53b46bfc464e6`; an unexpected implementation refuses execution. Existing subprocess ownership, stop/cleanup, sampling, duration bounds, shared transport slots and ledger policy are inherited. The fixed paid cutoff is 2026-10-11 02:12 UTC. It starts no new arms within the inherited 120-second margin and interrupts remaining owned workers within the inherited 60-second margin.

The queue permits six active arms and three CPU-heavy arms. All shared-context arms are heavy because their complete source authentication re-renders source images, so this standalone plan can be limited to three concurrent arms throughout. Transport remains three slots and the P003 USD 50 wave cap. There is no coordinated auxiliary/Gateway mode, policy reconciliation, retries or fallback. Root must explicitly acknowledge exclusive paid work before launch.

Exactly 25 runtime files must be clean and byte-identical to their Git HEAD blobs. Preparation records that independent map and freezes all 252 complete native wires. Launch replays the entire request inventory and source authority before the scheduler runs. Immediately before each owned subprocess launches, the driver checks all 25 runtime files again and replaces only that newly created arm's prelaunch map with the exact approved 25-file authority. A changed runtime or dirty source file refuses execution. These per-arm maps are in the queue's `trusted-code/` directory and can be supplied directly to the independent shared-context evaluator.

Question and shared-request counts remain distinct. One charge belongs to each attempted shared request; it is not repeated for each member question. Completed arms preserve all 24 statuses including refusal, error, abstention and unattempted outcomes. Queue and runner rates are contended and have separate wall scopes. Missing reports or unstarted arms suppress aggregate rates. Page/table/full-pipeline extraction rates stay undefined.

```sh
python -m bench.p003_synthetic_shared_queue \
  --input /explicit/synthetic-micro-relations-v2 \
  --trusted-code /external/synthetic-micro-relations-v2.json \
  --prepared /new/source-only-plan --prepare-only

# Root only, after the current paid queue drains:
python -m bench.p003_synthetic_shared_queue \
  --prepared /frozen/source-only-plan --directory /new/hosted-queue \
  --run-hosted --exclusive-paid-work
```

Preparation freezes literal `plan.json`, `frozen-order.json`, `trusted-code/runtime25.json`, all request bytes and `frozen.json`. A new output is required. Changing driver bytes after preparation requires a new versioned preparation directory; existing plans are never rewritten. Root should independently approve the driver commit before launching its prepared plan.

Six tests passed against the current pinned queue and authorized v2 source: exact 56-arm/252-request inventories, all actual runner CLI parses through a mock-only hosted seam, three-heavy scheduling, process-local restoration on exceptions, exact 25-file prelaunch authority, separate shared/question counters, dirty-code/digest/argument rejection, and complete preflight replay before a mocked queue launch. Ruff and targeted type checks passed. Test cleanup never signals or enumerates external worker PIDs. No hosted calls, credentials, ledger access or gold reads occurred in this implementation.
