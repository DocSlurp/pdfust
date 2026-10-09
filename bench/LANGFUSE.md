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
output usage. Provider `usage.cost`, including zero, populates actual cost.
Catalog estimation is a fallback metadata field only when provider charge is
absent and provider tokens are present. Unknown ledger reservations are retained
solely as reservation metadata; they are never exported as a charge. Langfuse
can additionally calculate a catalog-based cost from its registered models when
no actual cost was provided; that remains an estimate, not a billing record.

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

Thirteen mocked CPU tests cover native usage aliases, reported zero charge,
unknown reservation separation, catalog fallback, sensitive-input exclusion,
embedding dimensions, deterministic IDs, local replay, sanitized errors,
configuration precedence, exact pricing registration, preservation/conflicts,
and verification. Live registration and readback are performed by the root
runner, not by this credential-free implementation worktree.
