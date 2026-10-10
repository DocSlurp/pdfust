# P003 decision-gated region processor

`bench.p003_regions_run.process(record, config, output, client)` integrates the
source-only proposals with a separately metered semantic gate and existing
strict image transcription. It returns **table-only, model-transcribed output**
with `source_conserved=False`, `output_atomic=True`, and `coverage=unverified`.
It does not preserve or reconstruct page prose and must not be reported as a
complete PDF text converter.

No hosted calls, credential access, protected input access, or inference were
performed during implementation. Tests use generated PDFs, local source
extraction, fake gate answers, fake metered records and fake transcription
responses. Root owns all real clients, reservations, model allowances and
campaign dispatch/code freezing.

## Frozen configuration seam

| Field | Value / behavior |
|---|---|
| `processor` | root dispatch name `p003_regions` |
| `campaign` | required `P003` |
| `run_id` | required nonempty retained identity |
| `region_proposal_arm` | `tracks_whole` default; `tracks_fixed2`; or separate `yolo` |
| `candidate_cap` | 1–32, default 32 |
| `gate_enabled` | true default; false permitted only for `yolo` control |
| `gate_image` | true default; false declares text-only gate evidence |
| `model` | exact gate model ID, required when gate enabled |
| `proposal_edge` / `gate_image_edge` | fixed 1536 / 512 |
| `image_edge` / `jpeg_quality` | fixed 1024 / 90 |
| `generation_model` | default `anthropic/claude-haiku-5.5` |
| `generation_tokens` | default 16384; existing adapter token admission applies |
| `workers` | fixed 1 |
| `conflict_policy` | `table_probability_then_proposal_order_nonoverlap` |
| `_layout_detector` | initialized persistent CPU detector, only required by `yolo` arm |

The processor forces its child to native policy, layout detector none,
OCR 300 dpi with whitespace tokenization, empty-page OCR mode, fixed OCR
orientation, original rotation preserved, and raster-grid insertion disabled.
The child is invoked without any client and writes under `native/`. Native text
therefore remains native; OCR runs when no extractable text exists, rather than
silently overlaying every page. Any unsupported/error child status propagates
with its original diagnostics. A source failure cannot become a successful
empty table output. Source and original raster viewports/rotation must match.

The original PDF hash is verified before independent rendering. Source proposals
read only full-source page_size/words and the original full-page white raster.
The source-only plan is retained in `<id>-proposals.json` before independent
copies acquire gate metadata. Cap omissions, raster-view refusals, partial
windows and source packet omissions remain explicit. See the
[proposal design and CPU profile](p003-region-candidates.md) for generator
thresholds, pixel/word limits and limitations.

## Gate and conflict handling

Each candidate receives one `q0` Choice over **table / prose / unresolved**.
The exact source packet, bbox, mechanism evidence, capacity flag and warnings
are data; gate instructions explicitly explain incomplete OCR evidence and
unknown physical completeness. Image-capable arms add a fixed 512-edge JPEG
using the existing continuous-viewport crop helper. Text-only models receive
the same literal prompt without an image; this is a separately declared
evidence arm, not an assumed vision capability. Native decisions and supported
chat controls use their existing exact transport contracts.

Requests carry `P003/<run>/<page>/gate/<proposal>` tags and use `baseline.call`
with the root's metered client. Local gate files use separate names from
transcription files. Every successful returned answer/call is retained; on a
failed transmitted call, matching new ledger entries are retained without
logging provider error bodies. The first gate failure stops the page before
transcription. The root client's transport circuit breaker remains responsible
for stopping later calls across pages/models. No retry or response replay is
introduced here.

All gates complete before overlap selection. Only `table` choices enter a
deterministic greedy selector. Returned table probability sorts descending when
available; unavailable distributions remain `None`, and proposal order breaks
ties. No confidence threshold or calibrated-correctness claim is introduced.
A selected bbox blocks later boxes with any positive-area overlap; touching
edges are allowed. Boxes are never extended, merged or repaired. Every conflict
records its ID, selected conflicts, returned probability or missing value, and
`not_transcribed_overlap` disposition. Prose and abstained IDs remain separate.
Selected boxes return to declared proposal order for request/composition order.
This can discard true neighboring/overlapping tables or favor an incomplete
region; those are policy limitations, not evidence that discarded proposals
were non-tables.

## Strict transcription and output scope

Disjoint selected regions are cropped at JPEG90/1024 from a separately rendered
full-page raster capped at edge 4096. Existing `vision._transcribe` preserves
raw responses, actual calls and root accounting; it receives `campaign=P003`.
The processor uses the unchanged `pipeline_vision_transcription.parse` and
`generalization_vision_regions.compose`: normalized table bounds must stay
inside their exact proposal viewport, matrices must be rectangular, covered
merged slots must be empty, aggregate cell slots are bounded, and returned
tables must be disjoint. Any strict parse/composition failure rejects the
complete parent table output, preserving prior successful crop records and all
paid attempts. No coordinate repair, text rewrite, topology salvage, missing
source invention or partial primary output occurs.

Successful table HTML/Markdown and structure are written only after strict
complete parsing/composition. Parent results retain native child diagnostics,
source geometry, frozen proposal inventory, gate records, conflict decisions,
selected count, transcription regions and every call. Empty proposals, negative
gates, or all-abstained gates can produce a valid empty table-only output with
coverage unverified. An empty inventory does not establish that the page has
no table.

## Separate YOLO controls

`region_proposal_arm="yolo", gate_enabled=False` uses the existing CPU Table
class/confidence >=0.25 proposal selection, including its complete refusal above
32 proposals. A lower configured cap also refuses the complete inventory;
no detector subset is silently selected. It bypasses semantic requests with an
explicit `bypassed_ordinary_yolo` marker, then uses the same overlap policy and
strict crop transcription. YOLO+gate is available as its own separately labeled
arm. Neither arm fuses learned proposals with source-track/raster proposals.

This YOLO arm is a matched **P003 acquisition control**, with the same source
precondition and conflict policy as the new processor. It is not byte-identical
to the original P002 image-only ordinary YOLO processor, which did not require
OCR/native source and could transcribe overlapping proposals before atomic
composition failed. Retain the original `vision_regions` arm when that exact
historical control is required.

## Validation and root integration

Root must dispatch the processor and freeze this module plus its dependency
files. Shared `baseline.call` must accept P003 tags and `vision._transcribe`
must honor config campaign for tags/accounting; root has already prepared
those shared seams. No shared files were edited in this commit.

Validation: 18 new processor tests plus 18 candidate tests and 28 existing crop
integration tests pass (64 total). Targeted Ruff and strict mypy pass on the two
new files. New checks cover genuine generated-PDF native child extraction,
rotation preservation, immutable source proposal snapshots, partial evidence,
text-only contracts, explicit abstention, disjoint global bounds, probability
and missing-probability conflicts, charged transport failure, atomic malformed
bbox/matrix/truncation failure, native unsupported status propagation, fixed
configuration admission, and the separate YOLO bypass arm. Paid quality,
serving compatibility, full-pipeline throughput and provider resource use remain
unmeasured by this implementation.
