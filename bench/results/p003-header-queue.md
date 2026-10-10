# Header dispatch and coordinated micro queue

The fixed `header` kind invokes `bench.p003_header_decision_run`. The queue
guards and resolves pool, pool-code, header-code and generation-code paths
before launch. It owns output, hosted opt-in and transport capacity 3. Header
authentication is a CPU-heavy lane, bounded together with pipeline, candidate,
admission and diagram work to three active arms. Header status accounting uses
`selection_status` and `incremental_header_selection`; partial table output
does not become operational success or full-pipeline throughput.

The existing exclusive acknowledgment remains the default authorization
contract. A separate mutually exclusive root acknowledgment is available:

```sh
python -m bench.p003_parallel --plan /absolute/path/micro-plan.json \
  --directory /absolute/path/fresh-auxiliary-queue \
  --max-parallel-arms 3 \
  --coordinated-concurrent-queue /absolute/path/primary-queue/status.json
```

This mode admits only MICRO arms with an explicit OpenRouter provider and at
most three auxiliary hosts. The existing active queue must contain only known
`bench.p003_run` pipeline commands at transport capacity 3. Its declared
concurrent policy and the shared ledger must match exactly: max-inflight 3,
P003 wave limit USD 50 and matched replicas enabled. In-flight work must carry
a P003 tag, OpenRouter gateway and concurrent reservation identity. Unresolved
serial admissions, non-P003 work, blocked spending, capacity changes, Gateway
and heavier auxiliary plans are refused.

Root's path acknowledgment attests that no other paid jobs are active. The
helper reads the shared ledger under its existing lock, without constructing
a client or changing policy. The auxiliary status freezes primary-status and
ledger snapshot hashes, declares shared transport contention and retains
separate own-queue resource measurements. Original queue reports are not
changed. Three process-lock transport slots are enabled for auxiliary children;
financial admission remains enforced independently by the persistent ledger.
This is an admission-time validation, not an external process supervisor.

Focused CPU tests cover actual header CLI parsing with mocked preparation and
execution, incremental partial-result accounting, guarded authorities,
heavy-lane scheduling, coordinated-policy refusal cases and byte-preserving
reads of a synthetic ledger. No live ledger, credentials or inference are used
by the tests.
