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

## Experiment and dataset backfill

`bench.langfuse_backfill` stores the rest of the research record through the
same transport. Each step is idempotent through deterministic IDs and local
markers under the ignored `bench/results/pdf-master-artifacts/langfuse-backfill/`.

- `datasets`: `dev/silver-v1/<version>`, `dev/borderless-dev-v1/<version>`,
  `dev/silver-realism-v2/<version>`, `dev/wild-v1`, and `dev/omnidoc-dev`.
  Item inputs hold the case record and PDF identity, with the PDF as base64
  when it is at most 512 KiB. Expected outputs hold the authored targets. Item
  IDs hash the PDF bytes, and stale items are archived.
- `runs`: each retained silver-v1 benchmark becomes a run scored by
  `silver.anchor_recall` and `silver.completed`. Each wild-v1 audit level
  becomes a run scored by `wild.markdown_{f1,precision,recall}`.
- `experiments`: one `experiment/<directory>` trace per artifact directory. It
  holds a path/size/mtime digest, file and byte counts, the top-level file
  list, and up to 256 KB of top-level reports. A trace is re-sent only when the
  digest changes. Raw request/response files remain on disk; paid requests
  already export individually through `emit_request`.
- `reports`: one `report/<path>` trace per committed result summary and
  `EXPERIMENTS_LOG.md` content version.
- `heldout --custodian-release`: the protected held-out upload described in
  `bench/heldout-silver/AGENTS.md`. Other steps refuse protected paths.

Uploaded text is truncated and scrubbed of credential-like strings. Image
pages (OmniDocBench, wild-v1 assets) are referenced by path and SHA-256 rather
than uploaded.

## Experiment adapters

`bench/langfuse_adapters/` turns each experiment's retained per-item results
into datasets (`exp/<artifact>/...`), with one dataset run per model,
configuration, or treatment. Each run holds one scored trace per item. Every
module that defines `NAME` and `collect(artifacts)` is discovered
automatically; `base.py` defines the shape and the rules. Adapters report
only the experiment's own metrics, keep failed and abstained rows so
denominators match, and keep provider-reported charges separate from
catalog estimates and reservations. They refuse held-out paths. The table
lists each adapter group, its scope, and how its aggregates were checked.

| Adapters | Scope | Aggregate cross-check |
|---|---|---|
| `decisions*` | D/M/L/A/T series, waves, OmniDoc presence | 979 runs equal retained evaluations |
| `image_gates` | context30 image axes, OCR1200 admission, source-table gates | 312 image runs equal `image_axes_report` |
| `pipeline_p001`, `pipeline_p002` | complete-pipeline and generalization pages | all 56 + 47 primary runs equal reports |
| `pipeline-p003*` | P003 queues, synthetic, extension, micro, continuation | 634 runs re-sum to retained aggregates |
| `local_*` | encodings, semantic, color, geometry, headers, GPU, specialist | reports match except one retained timing |
| `corpus-*` | borderless, silver tables, realism, OmniDoc, OCR rolling, wild OCR | all checkable runs match |

Run `uv run python -m bench.langfuse_backfill adapters --dry-run [--only NAME]`
to validate offline, then run without `--dry-run` to sync. The writer
exports `LANGFUSE_RUN_WORKERS` (default 4) runs at once with
`LANGFUSE_WORKERS` (default 8) concurrent requests each. Scores go through
batched ingestion in groups of 250, and transient failures are retried with
backoff. Because Langfuse shares this host, running more than about four sync
processes lowered throughput. Runs are content-addressed, so an interrupted
or repeated sync re-sends only unfinished or changed runs.

Langfuse v4 indexes dataset run items asynchronously. After a large sync, the
dataset-run-items listing can lag behind for several minutes while the worker
queue drains. On 2026-10-11 the 175 runs that were briefly incomplete all
caught up without help. Check again before repairing. If a run is still
missing links after the queue drains, `adapters --repair` lists each run's
existing links and re-posts only the missing ones. The writer posts a run's
first link by itself before the rest because that link creates the dataset
run; concurrent first links raced on the run's unique constraint and depended
on retries.

The verified backfill on 2026-10-11 holds 109 adapter datasets, 2,175 runs,
4,299 items, 76,116 scored rows, and 838,104 row scores. Every run is fully
linked, and the project contains 117 datasets and 938,483 scores in total.
