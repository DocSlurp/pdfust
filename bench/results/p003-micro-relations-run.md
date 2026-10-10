# Independent hosted micro relation probes

The new `p003_micro_relations_run` runner requires root opt-in, one explicit
model, one provider and one evidence mode. It has no model switch, retry,
geometry assignment, original-table fallback or baseline quality credit.

Preparation authenticates the complete ordinal DEV16 source baseline using an
external root trusted-code map. It rebuilds the existing bounded source-only
pair plans and checks complete micro-state capacity for both treatments. It
ranks candidates by SHA256 of canonical page ID, question kind and original
source IDs, greedily accepting four cell, four row and four wrap questions with
at most two questions per page. Unmet quotas refuse preparation. Selection is
independent of model, provider and micro/verbose mode. Actual DEV16 preparation
selects twelve pairs across nine pages; the largest selected micro state is
620 UTF-8 bytes. The frozen inventory digest is
`eb65bbb38c35c5939165b18588496125f935cfd4f9043d608f6ac69fbb258a3e`.

Every canonical request, Gateway wire request and exact transport JSON encoding
is retained and hashed before client construction. Laya uses the existing
Gateway Boundless-only wire; d1 uses the existing native text wire. There are no
images. The frozen source archive, source plans, original manifest identity,
external trusted baseline code map and current code archive provide replay
provenance. Archived Python is not executed.

```
python -m bench.p003_micro_relations_run \
  --baseline ORDINAL_DEV16 --trusted-code ROOT_SOURCE_MAP \
  --output FRESH_PRIVATE_IGNORED_DIRECTORY \
  --model convaiinnovations/laya --provider gateway --mode micro \
  --run-hosted --exclusive-paid-work --transport-concurrency 1
```

Gateway requires exclusive paid work and serial transport. OpenRouter accepts
registered decision models and transport concurrency one or three using the
existing root P003 shared-policy clients. Requests within an arm are sequential;
three-slot transport permits root to coordinate independent OpenRouter arms.
Every request has `replay=False` and the existing reservation boundary. The
first client transport/admission exception prevents every remaining call and
reservation. A malformed returned response is retained, fails the strict
canonical receipt parser, and permits the next distinct pair. No failed pair is
retried. Initialization failures retain all frozen inputs and mark every pair
unattempted. Exceptions retain sanitized metadata rather than arbitrary
credential-bearing messages.

`question-INDEX-result.json` and `report.results` expose `valid_abstention`,
`valid_nonabstaining`, `malformed_response`, `transport_error` and
`not_attempted`. Complete responses and provider usage/entries are retained.
Raw probabilities are uncalibrated and validated by the original strict
micro receipt helper. `pure_model_outcomes_by_page` revalidates retained pure
receipts. A valid choice is not verified correctness; no table quality is
claimed. Page coverage means pages represented by local pair probes, never
complete page processing.

Local source authentication/freezing CPU and wall are separate from the hosted
probe interval. The latter uses process CPU and RSS sampled every 100 ms;
reported admission wait is retained when provided and otherwise remains
unmeasured. All arm ledger attempts, failures and unresolved reservations use
the existing `_entries`/`_charges` accounting with probe-specific scope. Missing
accounting cannot become free inference. Rates are questions/minute and, when
cost is known and positive, questions/dollar. Page and full-pipeline rates are
always undefined.

Ten tests across helper and runner cover deterministic quotas, source-complete
capacity, same evidence across modes, strict answers, abstention, stop-without-
reservation behavior, malformed distinct-pair continuation, exact Gateway wire,
OpenRouter shared-client admission and unchanged encoded request hashes. Ruff
passes. All development validation used mock clients or source-only preparation;
no credentials, ledger or provider inference were accessed.
