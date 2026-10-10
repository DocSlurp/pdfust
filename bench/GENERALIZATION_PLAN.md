# P002: generalizing the complete PDF pipeline

Started 2026-10-10 02:19 UTC. Stop paid work by 07:00 UTC and finish reporting
within the user's five-hour window (07:19 UTC). Three worker worktrees plus root
are the available four concurrent agents. Root alone coordinates metered calls.
P002 has a USD 50 ceiling within the existing cumulative USD 150 authorization;
starting conservative cumulative accounting is USD 36.6672001068. Prior charges
and unresolved reservations remain intact. No GPU rental is planned initially.

## Contract and predeclared comparisons

The operation is PDF page to complete structured tables plus remaining source
text in Markdown/JSON. Generalization requires more than the earlier authored
single-table examples. Build a fresh DEV cohort of approximately 264 pages:
64 metadata-stratified OmniDocBench raster pages, 144 authored stress pages and
56 licensed native-PDF diagnostic pages. Freeze source membership and construction
or official references before extraction. Keep prior P001 regressions separate.
Protected heldout paths are neither read nor enumerated. Public benchmark model
pretraining contamination is unknown; repeated tuning on this DEV sample is not
independent confirmation or an official OmniDocBench leaderboard score.

1. Preserve the P001 original/readable reviewed configuration as the whole-page
   baseline. Measure a CPU-only native-grid baseline as the minimal faithful arm.
2. Isolate native tables and independently analyze residual geometric regions,
   retaining global source ownership. Hypothesis: this recovers mixed and multiple
   tables and bounds dense evidence without losing whole-page words. Compare
   false positives, split-table errors and all operational failures.
3. Compare original and readable evidence, cropped images at 256/512/1024 pixels,
   and CPU OCR resolution where observed source errors justify the work. Do not
   cross every setting blindly; record the failure motivating each derivative.
4. Where candidate recall limits quality, test candidate-generation or bounded
   row edits before escalating the model. If source text is missing, measure that
   independently: no placement model can recreate absent text under source-only
   constraints. Any vision transcription fallback must be separately labeled.
5. Re-run accepted combinations against P001 and all new authored/native/natural
   slices. Freeze finalists before fresh repeated measurements. Broader untested
   PDF families remain limitations, never an "all PDFs" claim.

Primary gates: exact complete authored tables and spans, natural-table structure
and text scores separately, negative false-positive pages, source conservation,
and complete outputs / attempted pages. Require a gain on the targeted failure
slice without hiding regressions elsewhere. Natural reference parser failures
stay diagnostic and visible. No family/filename/reference-derived routing.

Report output pages/minute and pages/API USD, including failed-call charges;
exact-positive throughput is supplementary. Preserve positive provider charges,
estimate only from published rates and reported tokens when zero/missing, and
retain unknown reservations. Provider cache usage only; no local response replay.
Measure process CPU time and 100 ms sampled RSS with explicit concurrency and
OCR threads. Hosted GPU utilization remains unmeasured.

## Evidence and provenance

Raw inputs, annotations, requests, responses, complete outputs and snapshots live
under ignored `bench/results/pdf-master-artifacts/pipeline-p002/`. Code, plans,
tests and aggregate reports are tracked in Git and `EXPERIMENTS_LOG.md`.
Every experiment freezes source/code/config before calls; inference reads only
source PDFs and opaque IDs, while separate scoring reads private references.

Official references checked 2026-10-10:

- [OmniDocBench source and evaluation documentation](https://github.com/opendatalab/OmniDocBench)
  describes page/block annotations, HTML table references and distinct layout,
  recognition and formula metrics. Our targeted metrics must not be named as its
  official end-to-end score.
- [Dataset and license](https://huggingface.co/datasets/opendatalab/OmniDocBench)
  supplies raster pages; their carrier PDFs do not expose original native PDF
  bytes, fonts or version. Preserve its research-use restrictions.
- [OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting)
  documents response usage. Keep original responses and distinguish missing
  cache/cost fields from reported zeros.

## Checkpoints

Append measured results, rejected hypotheses and new predeclared derivatives here
and in the experiment log as each layer finishes.

### Layer 1: source and region corrections

The initial corpus contained 12 authored RGBA scan carriers incorrectly flattened
to black. Revision `corpus-r2` preserves all 276 page IDs and references, changes
only those 12 PDFs, and retains the initial snapshot and ongoing native run as a
source-defect diagnostic. Subsequent main comparisons use r2. Natural16 is an
additional metadata-selected screen (six multiple-table, six single-table, four
negative pages) frozen before its outcomes; the original 32-page pilot is unchanged.

Region candidate coverage on authored sources initially regressed from 132/156
complete reference tables in the full-page candidate union to 116/156. Relative
vertical leading and dominant sustained horizontal corridors restore 132/156 and
remove 16 unwanted table splits. These are target-aware candidate-oracle diagnostics,
not selected model quality. All proposal rules consume source geometry only.

New predeclared derivative: allow a bounded chat model to assemble cells directly
from source IDs when finite geometry menus cannot represent natural tables. The
response contains IDs, coordinates and spans, never replacement text. Validate
ownership and topology, construct literal values locally, and retain unassigned
words. Compare against selection-only on the fixed natural screen; report its
higher generation cost and any malformed output. Missing OCR tokens remain a
separate bottleneck. Root alone transmits calls.

Discovery audit: a worker's initial file search incidentally listed two protected
filenames. No protected contents or scores were read, and no further access occurred.
Subsequent discovery is restricted to explicitly named DEV paths. This procedural
incident is retained instead of claiming there was no protected-name enumeration.

The first region natural16 run still rejects seven pages due to the 25,000-character
packet ceiling. Offline inspection finds readable region packets up to 68,824
characters, within the live PPLX 262,144-token context. Predeclare a bounded
80,000-character readable-packet arm; keep the old default and complete evidence,
never truncate. Separately test direct and admission-gated source-ID generation
with an 8,192-token answer ceiling, recording truncations and complete costs.


### Layer 2: density, OCR and direct transcription

The fixed natural screen contains two dense newspaper pages with 39/53 tables.
Keep all sixteen primary; use the remaining fourteen only as a labeled posthoc
diagnostic. Predeclare whole versus overlapping 2x2 detector proposals, source-ID
matrix assembly with 256/1024-word regions, and lossless array versus quarter-unit
coordinate evidence. Boundary-crossing proposals retain explicit incompleteness;
more detector boxes alone do not establish better extraction.

Compare fixed 150/300 DPI sources, preserving recognition outputs and all costs.
Higher word inventory alone is not OCR recall. Page display rotation is preserved
for OCR; bounded four-angle trials are an opt-in treatment with measured total
cost and abstention. Keep complete source admissions distinct from per-call OCR
box limits. Original sources and outputs remain immutable.

Add image-only Sonnet/Haiku transcription controls at fixed RGB JPEG90 1200 and
2048 pixel edges. They emit table text and spans from pixels and are explicitly
model-transcribed, table-only, with no claim of source conservation or complete
prose extraction. Validate complete responses, retain provider refusals and charge
every attempt. Compare against source-owned pipelines before selecting combinations.
The initial Haiku anchor run was interrupted after four pages; retain its twelve
missing pages and unresolved reservation, and run new controls with new identities.

### Layer 3: explicit expansions and bounded crop transcription

At 04:30 UTC the next queue is fixed before the additional 260-page outcomes:
whole-detector matrix assembly with Haiku at 512 pixels on all 276 r2 pages,
plus a matched natural16 1024-pixel arm. This is a cost-oriented expansion of a
promising architecture, not a claim that the chosen model is already best.
A separate combination uses whitespace OCR at 300 DPI and lossless array evidence;
its outcome cannot attribute a change to image resolution alone. Whole-page vision
controls compare 1200 with 2048 pixels for both Sonnet and Haiku without silent
request-size adaptation.

The 2x2 detector treatment increased proposals but reduced exact text cells from
341 to 250 compared with whole-page detection. Freeze three source-only fusion
rules before scoring: baseline NMS, larger-first containment suppression, and
aligned-overlap unions. Keep member boxes, boundary warnings, and all source IDs.
More proposals and apparent coverage remain diagnostics rather than extraction
quality. A separate detector-crop vision arm will test whether larger local text
pixels avoid both whole-page legibility limits and the fixed OCR vocabulary ceiling.
That arm remains table-only and model-transcribed, with strict page-level atomic
validation and no claim of source conservation.

Mechanical repair is not accepted by default: the frozen counterfactual that pads
short rows admitted a false table on a negative page. Retain strict responses,
errors, and charges. Geometry clipping and null-covered-cell repair are documented
separately; successful parsing is not evidence of a quality improvement.

### Layer 4: packet admission, crop evidence and compact responses

The 2048-pixel JPEG90 whole-page controls refuse five of sixteen requests at the
750,000-byte transport cap, including both dense pages. They do not measure model
readability on those pages. A source-only encoding diagnostic keeps 2048 pixels
and changes JPEG quality: 90 admits 11/16 (maximum 1,341,758 request bytes), 70
admits 14/16 (836,402), and 50 admits 16/16 (645,398). Predeclare quality 50 as a
separate fixed arm for Sonnet, Haiku and Opus, retaining quality 90 controls and
all failures. No request-specific resize, quality adaptation or retry is applied.

Detector-crop transcription uses fixed whole-page CPU YOLO proposals, a full-page
4096-pixel render cap, 1024-pixel JPEG90 crops, source-only .25 Table confidence,
at most 32 crops and 4096 aggregate slots. Reparse every raw response and verify
all detector proposals before admitting a page; failed crops fail the page
atomically. Overlapping returned tables refuse rather than guessing ownership.
This is a table-only transcription control, not complete native/OCR conservation.

Predeclare two prompt-only source-ID assembly arms on the fixed screen: row-wrap
reasoning across neighboring columns, and repeated column-track alignment with
semantic negative checks. Both preserve the complete input, output schema, strict
parser and literal source text. A separate ordinal-index response adapter will
test whether shorter identifiers reduce output-length failures; integer indexes
must expand through the exact retained source order before existing validation.

Fixed longest-edge OCR is another explicit arm: 2048 pixels with effective DPI
computed from display extent, preserving physical-scale invariance. The matched
CPU experiment re-embeds identical raster pixels at half, original and double
physical dimensions before comparing fixed DPI against fixed pixels. This tests
encoding sensitivity; more recognized boxes alone still do not establish accuracy.

### Layer 5: precision, mixed provenance and neighboring-row observations

The fixed full276 Haiku expansion gains 46 complete tables over the native
regional baseline but produces nine negative-page false positives. Preserve its
ungated control. Predeclare a matched PPLX-gated matrix arm on all 276 pages,
measuring missed positives as well as rejected false positives. A separate hybrid
retains validated native grids, transcribes disjoint detector crops and accounts
for every native/OCR word as native-owned, retained prose or explicitly superseded
by a model table. Any child or overlap failure refuses the complete composition.
The native and vision child artifacts remain independently reviewable.

Generic row evidence is frozen before its outcome audit: median word-height
normalization, signed horizontal gaps, start/end tracks, token lengths, lexical
and numeric roles, and previous/following band spacing, indentation and continuity
observations. These bands are not logical table rows. The 276-page audit has
272 complete packets and four missing-source pages, with no feature errors;
its median packet is 3.34 times the original complete word-array size. A bounded
model-context projection removes duplicate words while retaining every row.
Test it independently as generation context and semantic-gate context, with exact
IDs or immutable ordinal indexes and no fitted rejection threshold. Admit no
truncated context. The source-only helper consumes no family labels or references.

Matched smaller crop arms use explicit 400, 512 and 768 pixel JPEG90 edges against
1024, with identical proposals, full-page render cap, prompts and strict parser.
Run the complete fixed natural16 screen, including failures, if the remaining
time window permits. Do not select a different image size per page from its score.

API intervals dominate the full276 profile. A separate fresh-request concurrency
prototype must prove atomic cumulative and per-wave reservation, unique in-flight
ownership, settlement after reloading the ledger, and failed-call retention using
mocked races before any paid integration. The active paid queue remains serial.
The native-only detector shortcut remains unintegrated because its measured
eligible subset is empty. These performance hypotheses must preserve quality and
report actual whole-run elapsed time instead of summed overlapping latency.

### Layer 6: coverage, matched pixel sweeps and measured concurrency

Before their runs, freeze multiscale proposals as a 1536-pixel whole-page view
plus four overlapping tiles from a 3072-pixel source render, followed by fixed
larger-containment fusion. Retain all raw proposals and transform evidence;
transcribe every accepted crop using the existing strict 1024-pixel JPEG90
contract. Compare both Sonnet and Haiku to their whole-detector crop controls.
More proposals must earn quality gains without overlap, negative-page or atomic
failure regressions. Do not select a detector configuration from a page's gold.

Separately compare 2048-pixel JPEG50 crops for both models to 1024-pixel JPEG90.
This deliberately changes resolution and encoding together and cannot isolate
which caused an effect. The Haiku 768/512/400-pixel JPEG90 sweep does isolate
crop edge with the same original detector proposals, source render and prompt.
All sixteen intended pages and all charges remain in every report.

Queue full276 native/image hybrids for Haiku and, if enough campaign time remains,
Sonnet. Keep the 16-page pilot and additional DEV pages separately visible. The
full expansion tests whether keeping native grids avoids paying for already
solved cells while image crops improve natural pages. It is not a hidden
confidence-based cascade and has no protected-set confirmation.

The concurrency prototype passed mocked thread and independent-process budget
races. Its only paid integration is an explicit four-worker whole-page Haiku
2048-pixel JPEG50 run against the serial control. Keep fresh calls, deterministic
page ordering, all errors/costs and whole-run wall/CPU/RSS. Reserve and settle
under a cross-process lock; perform HTTP and Langfuse outside it. Run this only
after the legacy serial queue drains. Start no paid experiment after 07:00 UTC;
skip queued arms whose fixed allowance no longer fits the campaign window.

At 05:45 UTC, add one combined source-owned hypothesis if time permits: whitespace
OCR300, compact array evidence, ordinal output indexes, static column-track
instructions and a 512-pixel image. The earlier controls separately improved the
available literal vocabulary, output admission or dense-page placement. Their
combination may still lose smaller-page accuracy or fail input admission. Evaluate
all sixteen fixed pages, not only the prior misses, and label the multiple changed
factors rather than attributing any gain to one technique. This arm uses no row
reference, family label or outcome-derived per-page routing.

The four-worker control is moved into the pause between hybrid runs while a
confirmed no-source-word table/footer ordering bug is fixed. No legacy serial
request overlaps it. The 768-pixel crop control follows during that same pause;
completed runs will be removed from the later queue rather than repeated.
