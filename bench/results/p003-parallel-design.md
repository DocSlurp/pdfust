# P003 optional parallel queue

This opt-in root queue runs at most three independent complete-pipeline arms,
with one local worker each and three globally admitted OpenRouter requests.
Serial controls remain available. No hosted requests, credentials, or ledger
reconciliation were performed while implementing or testing this mechanism.

The exact offline ledger policy required by `P003ConcurrentClient` is:

```json
{"max_inflight":3,"wave_limits_usd":{"P003":50.0},"allow_matched_replicates":true}
```

Root must stop every serial queue and all other paid work, verify no in-flight
requests or pending settlement, and reconcile `concurrent_policy` offline before
activation. Do not replace historic requests, charges, unresolved reservations,
or global limits. The queue never performs this reconciliation. Its CLI requires
`--exclusive-paid-work` as root's acknowledgment of these operational conditions.
Neither this document nor producing a plan activates paid work.

`P003ConcurrentClient(ROOT)` wraps an exact `DecisionClient` using the existing
outside-lock concurrent network transport. Shared locked admissions retain the
USD 50 P003 cap, cumulative/campaign caps, reservations and deadline. Settlement
preserves provider totals and separate `upstream_inference_usd` and
`gateway_reported_usd` fields. The inherited circuit breaker stops each arm after
its first transport or admission error, with no retries. Already reserved calls
settle independently using unique reservation IDs.

Matched replicate admission permits byte-identical in-flight requests only when
root has enabled the recorded P003-only policy and the full P003 tags differ.
Identical tags, prior failures, unresolved non-in-flight attempts and responses
awaiting settlement remain blocked. Default concurrent behavior is unchanged for
P002 and other waves. No prompt nonce modifies matched model inputs.

A plan is a literal JSON list of `{name, arguments}` objects. The queue freezes a
seeded order once and records it in `status.json`, with per-arm trusted source
hash maps, full subprocess logs, fixed argv and output paths. Each launch forces
`--workers 1 --transport-concurrency 3`. Output/source overrides, Gateway/Vercel
arguments and local worker/transport overrides are rejected. An explicit
`--gate-provider openrouter` remains allowed. The output directory
must be fresh; no automatic overwrite or retry is permitted.

Root invocation after offline reconciliation:

```sh
python -m bench.p003_parallel --plan PLAN.json --manifest MANIFEST.json \
  --directory FRESH_DIRECTORY --seed 3 --exclusive-paid-work
```

Each arm has a 40-minute wall bound. Starts stop 120 seconds before the fixed
02:12 UTC paid cutoff; running arms are interrupted 60 seconds before the cutoff.
SIGINT applies to each process group; remaining group members receive SIGKILL
after 30 seconds. Interrupts and exceptions clean up every active arm.

Queue CPU counters and summed live RSS include the queue and recursive children,
sampled every 100ms, including cleanup. Records include logical CPU count,
observed process count and concurrent arm count. Summed RSS can count shared
pages twice; CPU of short-lived children between samples can be missed. Per-arm
rates are explicitly contended. Queue aggregate throughput counts complete page
runs across arms, including repeated source pages, using total queue wall time.
Missing arm report metrics leave the aggregate rate undefined. These rates are
not serial comparisons. Original per-arm reports retain their own financial and
pipeline measurements; the queue does not reinterpret charges.

Validation uses mocked exact clients, synthetic ledgers and short CPU-only Python
subprocesses: circuit breaking, BYOK components, identical matched admissions,
unique reservations, default rejection, P003-only policy, seeded plans, override
rejection, three-arm overlap, trusted maps, aggregate resource counters, no
restart/overwrite, cutoff and process cleanup. No source PDF or gold is read.

## Mixed incremental arms

Plan items optionally declare `kind`: `pipeline` (default), `candidate`, or
`boundary`. Each selects a fixed Python module; arbitrary executable modules are
not allowed. Pipeline arms alone receive the queue manifest and workers=1.
Candidate/boundary arms receive `--run-hosted` under root's explicit exclusive
paid-work acknowledgment and take their own declared baseline paths and, for
candidate pools, independent trusted maps. All kinds use transport concurrency3,
and guarded declared paths reject protected locations before opening artifacts.
Manifest is optional for a queue containing only incremental arms.

Per-arm pipeline rates retain the contended label. Incremental rates count
retained artifact processing, including authentication/copying, with separate
ranking/repair status counts and incremental accounting. They exclude historical
pipeline generation. Queue aggregate metrics are separated by kind; its legacy
summary counts only pipeline page runs. There is no combined full-pipeline rate
for mixed arms. Incremental runners preserve one local worker, record optional
`config.transport_concurrency=3`, and freeze concurrent-client/transport sources.

Candidate historical strict-adapter compatibility remains denied by default.
Root explicitly reviewed only SHA-256
`8188aca8439f7c4bf455bf81b55a7a3e9f0789ca3590abbd3042d050b784591e`:
18 archived Sonnet P002 code files authenticated against committed Git versions;
the transcription adapter difference changes only model-admission error text,
with no parser/request semantics change for Sonnet. Root may declare this digest
using repeatable `--reviewed-parser-sha256`; arbitrary digests remain rejected.
The recorded list is frozen under `config.reviewed_parser_sha256`. Every archived
file must still match the separately supplied trusted map and its actual bytes.
The current local strict parser executes; archived code is never executed.
The independent evaluator must authenticate the separate historical and current
trusted maps and enforce the same reviewed list.
