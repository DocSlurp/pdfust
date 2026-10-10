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
