# Fresh concurrent metering plan

Freeze: 2026-10-10, CPU-only mocked transport. No runner wiring or live inference.
Goal: preserve the shared reservation ledger while releasing its flock during HTTP.

Reuse DecisionClient's offline pricing and optional telemetry hooks; leave its
implementation unchanged. A wrapper supports only its exact OpenRouter client,
fresh requests, fixed P001/P002 wave caps, and a persistent bounded concurrency policy.
Reserve a unique index/UUID under the existing ledger flock. Reload and update only
that reservation when completing; never write a stale whole-ledger snapshot.

Acceptance gates: mocked concurrent threads cannot oversubscribe cumulative,
campaign or wave reservation caps; identical in-flight requests never transmit twice;
out-of-order settlement retains unrelated additions/annotations; failures keep
unresolved reserves and raw bounded responses; failed settlement prevents further
admission while a response awaits settlement. No automatic replay, retry, expiry or
reservation release. Pricing and telemetry behavior must match existing pure hooks.

Reservations must bound possible provider charges to guarantee actual spend caps.
A provider charge exceeding its reserve is recorded truthfully and blocks future
concurrent admission; already in-flight requests cannot be cancelled by this proof.
Crashes leave in-flight slots occupied until explicit offline investigation. Future
rollout must use atomic wave admission for every request in that wave; legacy external
wave checks are insufficient when mixed with concurrent requests. Historical prior
cost ledgers must remain immutable while this shared admission runs.

Use deterministic Events/barriers, bounded thread joins and an injected fake opener.
Read no credentials, make no network requests, and do not claim live latency gains.
