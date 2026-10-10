# P003 topology-first source ownership

The P002 failure evidence separates structure and source vocabulary. Geometry and
row context can place existing strings, but missing OCR text remains absent.
Whole-crop transcription can supply visible strings beyond that inventory, with
model-transcribed provenance. This experiment targets the placement component
without silently turning source-owned values into transcriptions.

Three distinct modes address different ceilings:

1. **Frozen topology, source-owned choices (implemented pure helper).** An
   image-only topology hypothesis fixes all table bounds, rows, columns and
   merges. Native choices assign each original word to a table/logical row, then
   a physical anchor. All admitted logical rows are choices, removing the
   geometry-candidate shortlist as a placement ceiling. Outside and unresolved
   choices preserve original inventory. This cannot recover absent source text.
2. **Frozen transcription candidate selection (existing candidate picker).**
   Screenshot-guided ranking selects one exact complete candidate without edits.
   It can recover a string absent from OCR only when a candidate already contains
   it. An edit protocol restricted to source IDs shares the source vocabulary
   ceiling; rewriting malformed or missing strings would change the experiment.
3. **Frozen topology, literal image transcription.** Independently transcribing
   requested physical anchors can recover missing OCR strings. It requires
   separate model-transcribed provenance, costs and strict complete anchor
   coverage. Existing topology scaffolding describes this mode; this module does
   not implement or claim its text recovery.

`bench/p003_topology_ownership.py` is pure and has no model client, PDF loading,
credential, evaluator, network, or GPU access. `topology_request` wraps the
existing strict topology scaffold. `parse_topology` validates no-text predictions
through the unchanged transcription adapter using empty structural matrices,
then rejects overlapping tables. These empty values are validation scaffolding,
not inferred visible blanks. Semantically wrong topology remains possible.

`freeze(source,result,viewport,url)` retains only original source IDs, complete
literal strings and display boxes, admitted no-text topology, crop viewport and
actual decoded image SHA-256 in an immutable snapshot. Annotations, source model
names, quality labels and prior generated strings do not enter evidence. The crop
uses original page display coordinates, while table bounds in the topology
response are normalized relative to this exact crop; the strict adapter maps them
back into display space. Source strings keep their original global identities and
order throughout all batches.

`batches(plan,model,url)` builds row choices. `collect(plan,bodies,results)` requires
complete row answers before `batches(...,rows=receipt)` constructs physical anchor
choices. Merged anchors spanning the selected row remain eligible even when their
anchor row is earlier. Covered continuation slots are never ownership choices.
`assemble(plan,row_bodies,row_results,cell_bodies,cell_results)` replays both stages
and commits the entire source state once, or raises without modifying any input.
The runner must retain its original whole-page output on any crop/stage failure.

Every original word has one table anchor or remains unresolved in the source
state. Outside and explicit abstention inventories are separately retained; the
combined unresolved list preserves original source order. Cell strings join exact
owned source words in original order with the existing assembler's inferred
spaces. Complete source tiling expands ordinary physical anchors into unit spans,
a mechanical representation conversion required by the unchanged source
validator. Model topology does not prove semantic rows, correct text, pixel
visibility, genuinely empty cells, or calibrated probabilities.

Admission is explicit: at most 16 tables, 128 logical rows across all tables, 32
columns per table, 4096 aggregate slots, 256 words, 16,000 UTF-8 bytes for complete
source JSON, and 128,000 bytes for local text plus question menus. Each stage has
at most sixteen batches and each batch at most sixteen typed questions. Full
source/menus are refused above caps; no subset is silently emitted. Source caps
should be checked before any new paid topology generation. Worst case is 32
ownership calls plus one fresh topology call; a retained fixed topology has
historical generation costs and at most 32 new ownership calls. Smaller batches
can exceed the sixteen-batch cap and are refused. Root must compare total calls,
image bytes, cost and incremental latency rather than assuming a token advantage.

Typed responses must cover exact batch IDs and exact option probabilities, with
finite values in [0,1], maximum-probability choice and the existing 0.015 rounding
budget. Raw probabilities, mass delta and confidence remain uncalibrated
provenance. There are no extra confidence gates. Explicit unresolved is the
abstention mechanism. Frozen body/evidence/image/criteria mutation, duplicate or
missing batches, wrong receipt snapshot, malformed topology and partial responses
fail the whole operation.

Sixteen synthetic CPU-only tests exercise merged continuation ownership, complete
literal inventory, annotation exclusion, exact source order, raw confidence and
rounding, malformed late batches, duplicate/missing identities, crop mutation,
invalid bounds/spans, overlapping tables, empty inventory and bounded refusal.
No gold or source artifact was used to generate protocol evidence.

## Retained incremental harness

`bench/p003_topology_run.py` accepts a source-owned `regions` baseline and a
separately authenticated `vision_regions` baseline, both matching the complete
same16 PDF/page/manifest inventory. The predeclared topology baseline is chosen
without reference labels; it contributes strictly admitted normalized bounds,
dimensions and merged spans only. All generated strings are stripped before any
new native decision request. Its retained crop image bytes, request model/provider
pin, original body digest, image hash, byte count and display viewport must agree.
No image rerendering, OCR, extraction, detection or initial topology generation is
repeated. Both historical generation reports and all original failures remain
separate provenance, with no combined historical cost inferred by summing them.

Coordinates must match the same original page display viewport and rotation.
A source baseline that actually normalized a nonzero rotation is unsupported,
even when page dimensions happen to match. Each complete source word must be
wholly contained in one positive-topology crop or remain outside every crop;
straddling boxes and duplicate ownership are refused. Existing source tables may
not cross that partition. Crops overlapping retained vector grids are refused.
Empty source cannot recover image text. Every crop is capacity checked before the
first paid call on a page, including the complete local native menus and the
750,000-byte transport cap. Unsupported pages retain their baseline outputs and
explicit reasons; they are not silently omitted from quality denominators.

This first harness processes only positive admitted topology crops. Empty
retained topology does not trigger a new classifier or remove an original table;
such pages/crops retain the baseline and are `not_applicable`. This treatment is
conditional placement research, not a new detector or a missing-source-text
solution. Residual source regions retain unaffected baseline tables and literal
words. All newly staged crop states compose through the unchanged source-region
validator. New table overlap or late rendering failures retain the complete
original page, including original structure/Markdown bytes, status, calls and
source ownership. Earlier staged crops become discarded rather than successful.

Root can prepare in a fresh directory before any paid run:

```sh
python -m bench.p003_topology_run \
  --source-baseline SOURCE_REGIONS_DIRECTORY \
  --source-trusted-code ROOT_AUTHENTICATED_SOURCE_MAP.json \
  --topology-baseline FIXED_VISION_DIRECTORY \
  --topology-trusted-code ROOT_AUTHENTICATED_TOPOLOGY_MAP.json \
  --model cloudflare/clef-omni --output FRESH_PREPARATION_DIRECTORY \
  --prepare-only
```

Preparation constructs no client and exposes source counts, unsupported reasons,
exact row requests and maximum ownership call counts. To measure fresh root-paid
choices, use another fresh directory with `--run-hosted` instead. Root coordinates
spending and exclusive paid work. Optional `--transport-concurrency 3` selects the
shared persistent P003 concurrent circuit breaker; default is serial. Local
workers remain one. Explicit historical Sonnet parser compatibility takes the
same repeatable root-reviewed digest flag as the candidate runner, retaining
independent trusted-map requirements and current strict parsing. No reconciliation
or ledger activation occurs in this harness.

Current and baseline code archives, original source/topology requests/responses,
full immutable baseline outputs, planned source partitions, word/crop snapshots,
all new request/response pairs, row receipts, final ownership audits and updated
states remain in the output. Transport evidence is copied for every shared-ledger
attempt, including failed or unresolved reservations. Incremental metrics cover
retained-artifact preparation inside processing, waits, validation, composition,
rendering and writing; authentication/code/baseline copying precede that measured
interval and are separately labeled unmeasured. Historical pipeline wall/CPU/cost
remain untouched. `pages_per_minute` and `pages_per_dollar` are undefined. CPU/RSS
use existing one-process resource measurements with 100ms sampling, and hosted
GPU is unmeasured.

Independent replay seam: `frozen.config.processor` is `p003_topology_source`;
`frozen.source_baseline` and `frozen.topology_baseline` contain original config,
separate trusted maps, `file_sha256` inventories and copied directories
`source-baseline`/`topology-baseline`. `frozen.manifest_sha256` pins their source
manifest. Each page retains `{id}-ownership-plan.json`; each crop snapshot file
contains the canonical JSON for `ownership.Plan`. Its region metadata lists row
and cell request stems, each with `-request.json` and `-response.json`. Responses
retain typed `response.result`. Reconstruct the no-text topology from the strict
raw retained transcription, reproduce the exact original-source partition, then
call `ownership.assemble` on complete retained batches and compare audit/updated
state. Compose every residual/new region and use the recorded original/legacy
source-order renderer. All fallback output bytes must match the independently
verified source baseline. Current and both historical archives require separate
root-authenticated code maps; copied digest inventories are not their own trust
roots. No archived Python code is executed.

Twenty-seven helper/harness tests, plus the twenty-nine strict transcription
scaffold tests, use only synthetic JSON, temporary fake ledgers and mocked native
answers. Coverage includes complete same16 authentication/preparation, no client
in preparation, ownership conservation, absent generated-string evidence, exact
fallback after a later crop fails, all-crop preflight, native protection, rotation
and word-boundary refusal, preserved baseline errors, separate historical/new
cost intervals and strict complete-page replay. No source PDF, reference, API,
credential or GPU was accessed during implementation or tests.

## Real baseline eligibility diagnostic

CPU preparation of the independently trusted ordinal OCR300 source baseline and Luna pinned1024 topology baseline completed on natural16 without a model client: seven pages prepared, five had no positive topology, and four refused source-word/crop partition boundaries. Preparation alone does not verify quality. All four refusals were `ambiguous_or_straddling_source_word`, with no multiply contained word among these cases:

| Page ID | Original source words | Positive crops | Straddling words | Fraction of each word box inside its one intersecting crop |
|---|---:|---:|---:|---|
| p6ef5d3c5c2edb1c109c4 | 544 | 2 | 6 | 0.862 each |
| p98d10ef50dee4b24506a | 2700 | 2 | 7 | 0.834–0.994 |
| p656361df32bd7d69a39e | 77 | 2 | 1 | 0.754 |
| pf012d6adb9592dab9a13 | 88 | 1 | 2 | 0.722–0.736 |

These are retained source bounding-box/crop measurements, not image visibility or quality judgments. The existing all-word partition refuses even one partial intersection and therefore blocks an entire page; a fraction such as 0.994 is not a calibrated ownership probability.

A minimal source-safe alternative is an explicit boundary treatment retaining each entire straddling word in the original residual source region, exposing an excluded-boundary-ID audit and unchanged box/string rather than clipping or silently dropping it. This may make smaller pages eligible while preventing those words from entering repaired cells; a later existing-table partition or inventory cap may still refuse. A richer explicit treatment admits the complete word to its sole intersecting crop, preserves its original global box, marks partial image support, and offers outside/unresolved choices. It must refuse multi-crop ambiguity and preserve each ID once; image pixels outside the crop remain unavailable, so this cannot establish missing evidence. Neither treatment is active by default. Large inventories such as the 2700-word page may hit subsequent 256-word per-crop admission even after boundary handling.

A useful independent geometry control would rank fixed physical anchors by normalized overlap and center distance, enforce one global owner per source ID, and abstain on ties, small margin, crop boundary uncertainty, or inconsistent merged spans. Its scores would be deterministic geometry heuristics, not probabilities. It cannot fix absent source text and should use the same frozen source/topology plan, page atomic composition and literal-string assembly as the decision treatment.

The explicit `--boundary-words residual` treatment is now runnable. Strict default partition and requests are unchanged. Partial or multiply owned crop-edge words retain their complete original strings/boxes in their original residual regions, with plan `boundary_words.retained_original_region_ids` audit; no clipped word is sent for repair. An original source table crossing the resulting partition still refuses the whole page. Actual natural16 CPU preparation increases prepared pages from seven to nine (five not applicable, two still unsupported). The remaining failures are `original_table_crosses_crop_partition` on p6ef5d3c5c2edb1c109c4 and `ownership_inventory_or_menu_capacity` on p98d10ef50dee4b24506a. The preflight upper bound is 70 native row/cell requests; no request was made. This treatment exposes a conservative repair limitation, not a quality improvement claim.
