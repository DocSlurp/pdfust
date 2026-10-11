# Langfuse decision telemetry

The optional `bench.decision_langfuse` adapter sends sanitized request traces
through current OTLP HTTP/JSON, without additional Python dependencies. Legacy
trace ingestion is not used: its cloud sunset is November 16, 2026.
[Official API documentation](https://langfuse.com/docs/api-and-data-platform/features/public-api)
confirms the migration and current observations read API.
[Official OpenTelemetry documentation](https://langfuse.com/integrations/native/opentelemetry)
confirms HTTP/JSON support and the usage/cost attribute mapping.

The root runner explicitly invokes these functions:

```python
from pathlib import Path
from bench.decision_langfuse import emit_request, sync_models, verify_trace

root = Path.cwd()
registry = sync_models(root)
status = emit_request(root, body, provider_result, retained_ledger_entry)
check = verify_trace(root, status["trace_id"], retained_ledger_entry["started_at"])
```

Configuration reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and
`LANGFUSE_BASE_URL` from `.env`, falling back to `.env.remote-hosts`.
`LANGFUSE_HOST` remains a base-URL alias; environment variables take precedence.
Missing keys disable telemetry. HTTPS and explicitly configured HTTP endpoints
are accepted; authenticated redirects are refused. Keys and server error bodies
are never returned or printed. Requests have a ten-second timeout and bounded
response/payload reads. Exceptions return a sanitized status and must never
retry a paid model request.

`sync_models(root)` fetches regular, decisions and embedding OpenRouter catalogs.
It registers exact admitted model IDs, including the three multimodal embedding
IDs, with anchored literal match patterns, `startDate=2026-10-08`, token units and
one default pricing tier. Catalog rates are already USD per token. Definitions
that already match are retained; conflicting exact custom definitions are
reported without being overwritten. Managed and unrelated project definitions
are never changed. Missing catalog entries remain missing rather than acquiring
invented rates. The [official API schema](https://cloud.langfuse.com/generated/api/openapi.yml)
defines `startDate` and `pricingTiers` as the current creation fields.

Provider-reported `input_tokens`/`output_tokens` win over chat-style
`prompt_tokens`/`completion_tokens`. Missing usage remains missing, including
output usage. Positive provider `usage.cost` takes precedence and populates
`cost_details.total` with `cost_basis=provider-reported`. When the provider cost
is zero or missing, retained published catalog/provider rates times the provider's
reported token counts populate effective `cost_details` with
`cost_basis=estimated`. The original reported zero is preserved separately as
`provider_reported_usd=0`; an estimate is not a confirmed billing charge.
Catalog prices are per token, and zero rates are valid. Invalid, negative,
non-finite, or unavailable rates are excluded.

Estimates include only measured token components with valid rates. Missing
input/output tokens are never invented from total usage or treated as zero.
Partial estimates export component costs without `total`, record missing
components, and set `catalog_estimate_complete=false` and
`effective_cost_complete=false`. Complete estimates include a total. Without
usable rates and counts, cost remains unknown and no cost details are exported.
`catalog_estimated_usd` is the available component sum, so inspect its completeness
flag before treating it as a complete request estimate. Ledger reservations stay
separate as reservation metadata and are never exported as a charge. Langfuse
may calculate costs from registered models; these remain estimates, not billing
records. This adapter does not rewrite the spending ledger.

Trace and span IDs derive deterministically from the retained request SHA-256.
Successful export writes a local marker under ignored
`bench/results/pdf-master-artifacts/decisions/langfuse/`. Replaying an exported
request sends no new generation and creates no new spend. A failed export can
retry telemetry under the same IDs. The root client must retain its original
ledger timestamps during replay or backfill. This adapter does not make model
calls or change the spending ledger.

Input is reduced to request hash, byte count, question count and state shape.
Output retains compact numeric decision answers; free-text explanations and
unknown answer labels are omitted. Images, prompt text and embedding vectors
are excluded. Embeddings retain dimensions and the response hash. Exact trace
verification uses `/api/public/v2/observations` with a trace-ID filter, bounded
time window, and selected core/model/usage fields; it never requests input or
output. Readback can be pending while asynchronous ingestion completes.

Mocked CPU tests cover native usage aliases, zero/missing charge fallback,
positive charge precedence, unknown cost, partial estimates, invalid rates,
reservation separation, sensitive-input exclusion,
embedding dimensions, deterministic IDs, local replay, sanitized errors,
configuration precedence, exact pricing registration, preservation/conflicts,
and verification. Live registration and readback are performed by the root
runner, not by this credential-free implementation worktree.

## Markdown element-score dataset and runs

`bench.markdown_score_langfuse` reuses this module's configuration and
transport. `uv run python -m bench.markdown_scores --score` syncs after writing
the summary whenever `.env` configures Langfuse (`--no-langfuse` skips it,
`--langfuse-force` re-sends synced runs). It upserts dataset
`pdf-markdown-elements-v1`. Each item is one synthetic fixture: its input holds
the PDF SHA-256, source and notes, and its expected output is the exact ground
truth. Item IDs hash the PDF and truth, so a changed fixture creates a new item
and stale items are archived. Each converter becomes one dataset run named
`<tool> @ <producing commit>[-dirty] out:<output hash>`. The commit comes from
the checkout recorded when the outputs were produced. Each case trace stores
the complete Markdown with inline base64 replaced by its SHA-256, plus timing
metadata. Traces carry per-category `md.*` scores and `md.case_mean`. Runs
carry the report's check-weighted `md.*` category scores and `md.overall`.
Deterministic IDs and local markers under the ignored
`bench/results/pdf-master-artifacts/markdown-scores/langfuse/` make re-syncing
idempotent. Errors are sanitized and never fail scoring.
