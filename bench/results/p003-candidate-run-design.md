# P003 frozen-crop candidate ranking runner

`bench/p003_candidate_run.py` targets existing `vision_regions` artifact format.
It runs a new opt-in selector over two to four explicitly declared generation
baselines. It does not repeat detection, OCR, extraction or transcription. This
branch performed no inference or credential access.

Root entry point:

```bash
.venv/bin/python -m bench.p003_candidate_run \
  --baseline <first-predeclared-baseline> --trusted-code <first-reviewed-code-map.json> \
  --baseline <second-baseline> --trusted-code <second-reviewed-code-map.json> \
  --output <fresh-ignored-ranking-directory> \
  --model cloudflare/clef-omni --image-edge 512 --seed 20261010 --run-hosted
```

Use one independently reviewed flat filename-to-source-SHA256 map per baseline.
An artifact's own digest list is not an authenticity source. The runner checks
all archived source bytes against those maps, requires the vision-region runner,
vision transport, strict transcription adapter, frontier and pipeline archives,
and requires the authenticated adapter to match the currently executed strict
parser. Archived Python is never imported or executed. Original complete outputs
are replayed through the existing trusted vision-region verifier.

The declared baselines must contain exactly the same complete sixteen frozen
source records and source manifest hash. Record order may differ; all page IDs,
PDF paths/hashes and page indexes must agree. Same-crop candidates require identical
page viewports and proposal indexes, request indexes, global crop boxes and
detector proposals. The retained generator requests are reconstructed with the
strict original request builder and compared with saved semantics and request
hashes. This matters because artifact JSON sorts keys while original transmitted
request bytes retain builder order. Actual inline image bytes are decoded and
checked against each recorded byte count/hash/viewport, then required to be
byte-identical across baseline candidates. Generation provider/model variation is
allowed; different source image bytes or region inventories are not matched pools.

Each crop's provider response is strictly reparsed with its original global
viewport. Complete candidates are frozen through `p003_candidate_choice` and
exactly deduplicated. Alias order is deterministic from the declared seed plus a
hash of page ID and crop index, avoiding the same alias permutation on every crop.
Only opaque alias matrices/bounds/spans and optional pixels enter selector state.
Generation model names, original input indexes, historical quality and source
metadata remain external provenance. No gold or references are loaded.

Image edge controls are 0, 256, 512, 768 and 1024. Edge zero is an explicit text-only
control: pixels are unavailable to the selector. It reads no PDF. Positive edges
rerender the original frozen PDF at the same global crop viewport using a bounded
4095-edge full-page CPU raster and continuous crop geometry, then JPEG90 encoding.
The original PDF hash, original page viewport and rotation must match. Selector
image bytes, edge, viewport, dimensions, codec and hash are retained separately
from the identical original generation crop. Selector image resizing is therefore
an explicit new treatment, not a claim that generator inputs changed.

Text-only models use root's current `DECISION_MODELS`. The initial image allowlist
is `openai/gpt-6-luna-decisions`, `perplexity/pplx-decider-v1.1-27b`,
`cloudflare/clef-flash`, `cloudflare/clef`, and root-confirmed
`cloudflare/clef-omni`. Unsupported model/image combinations fail before client
construction or calls. D1 Gateway transport is outside this runner. Default hosted
execution lazily constructs root's `P003DecisionClient`; callers can inject the
same coordinated client directly. Requests are fresh, tagged
`P003/<run>/<page>/<crop>` with replay disabled and persistent reservations.

## Page admission and fallback

Input zero is the predeclared fallback, selected before looking at any response.
If that original page failed, its failure remains unchanged and no selector runs.
If another baseline page failed, the complete first page is retained with
`ranking_status="not_applicable_baseline_failure"`; valid early crops on failed
pages are not cherry-picked as rescue candidates. All invalid baseline attempts,
errors, costs and latency still remain in generation provenance. A duplicate-only
pool emits no selector call. No region/page subsets are chosen by reference quality.

Each admitted selector answer is parsed through the strict typed helper. It can
choose one unchanged whole-crop candidate or explicitly abstain. A selected crop
retains the exact original provider response and canonical candidate state from
its chosen baseline. No synthetic response, blended cells, copied partial tables
or repaired malformed JSON is generated. Abstention retains input-zero's original
crop output with `unresolved_retained_first` audit status. Its uncertainty is not
relabelled as selector correctness.

All crop selections are staged. The complete page is composed once through the
existing `vision_regions.compose`, including aggregate slot and table non-overlap
admissions, then rendered through the strict transcription Markdown path. A
provider/parser/composition error rolls back every staged crop and preserves
input-zero structure and Markdown bytes with
`ranking_status="failed_retained_first"`. Effective `status="ok"` on fallback
means the historical output remains complete, not that ranking succeeded.
Original page errors remain errors. Every candidate and selected output remains
`text_provenance="model-transcribed"`, `source_conserved=False`; source word
ownership is not invented.

## Artifact and evaluation handoff

`frozen.json` has `processor="p003_candidate_choice"`, unchanged source records
and manifest hash, current `code_sha256`, and `candidate_inputs` entries containing
original directory, relative `baseline-0`/`baseline-1` copies, complete file hashes,
operator-supplied trusted map and original configuration. Each copied baseline
retains report, frozen config, code, page results, provider requests, complete
structures and Markdown. Raw responses remain in page-result crop records.

Per-page `ranking_regions` retain crop index, global viewport, original decoded
image hash, full frozen pool manifest, selector image metadata, typed audit,
selected baseline index and selected canonical hash. Files use
`<page>-pool-<crop>.json`, `<page>-selector-<crop>-request.json` and matching
`-response.json` containing the complete shared-client wrapper. Selected page
`transcription_regions` retain original provider responses plus selection origin
and audit. Results keep historical input-zero `calls` and timing; new calls are
`ranking_calls` and generation history for every baseline is
`candidate_generation_provenance`.

An independent evaluator should authenticate every baseline copy with a separately
supplied map, verify copied file hashes and original outputs, reconstruct each
same-image pool/permutation from raw responses, parse each retained selector result,
and require selected canonical bytes to match one frozen candidate. It should then
replay whole-page composition and compare exact output structure/Markdown. It must
validate atomic fallback bytes and page failure retention separately, and audit
requests for absence of model identity, gold and prior scores in candidate evidence.
The scorer must not treat `ranking_status` as a quality label.

`candidate_generation_reports` retain every original pipeline report, including
failed attempts and reported/estimated/unresolved costs. These are not declared
free because outputs were replayed. Combined generation accounting must deduplicate
shared ledger entries when baseline histories overlap; this runner intentionally
preserves all original reports rather than constructing an unsafe summed total.
`incremental_ranking` separately accounts for this run's P003 ledger attempts,
including failed selector calls and unresolved reservations. Partial estimates do
not become complete totals.

The CPU-only serial resource interval covers retained-pool construction, optional
rerendering, selector waiting, decoding, composition and output writing after input
authentication/archive freezing. Authentication resources are separately labeled
unmeasured. Process CPU/wall and 100 ms sampled RSS use the existing monitor;
hosted GPU resources remain unmeasured. Original full-pipeline latency stays in
generation reports. `pages_per_minute` and `pages_per_dollar` are undefined (`None`):
frozen-pool ranking is not a new end-to-end pipeline throughput measurement.

Validation: **22 focused tests passed**, including fourteen helper controls and
eight runner cases; Ruff passes. Tests use tiny synthetic sixteen-page manifests,
actual inline image bytes, authenticated local code fixtures and an isolated mock
client. They cover exact selected candidate identity, source-conservation labels,
first-output bytes, low-level image matching, unsupported image model gates,
explicit abstention, malformed typed response rollback, later-crop atomic rollback,
original page errors, duplicate pools, source archive trust and separate generation/
selector charges. No provider calls or full benchmark runs were made.
