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
