# P003 decision evaluation contract

This contract was declared before P003 model comparisons. The experiment is DEV
research: no protected silver artifacts are read or scored. Independent reference
annotations enter only offline evaluation and source-ceiling diagnostics. Model
requests may receive source text, geometry, detector proposals and images, but
never annotation HTML, expected cells, reference boxes, reference table counts,
quality scores or case-specific gold-derived routing rules.

## Fixed inventories and breadth

The natural16 screen remains the frozen P002 sixteen pages, with twelve positive
pages, four negative pages, 53 reference tables and 2,333 anchor cells. Dataset
identity is `68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.
All sixteen source PDF byte hashes match their corresponding corpus-r2 records.
Its existing manifest and references remain unchanged.

Broad evaluation uses **all 64 omnidoc pages** from the corrected corpus-r2 DEV
manifest: forty positives, twenty-four negatives, 93 reference tables and 3,847
anchor cells. The parent dataset identity is
`e0a86f712fb7eda5f5ceb64fa19eb72c055694106a006b086fd9d09284295537`.
The source-only runner manifest is
`pipeline-p003/manifests/natural64.json`, SHA-256
`5f93b38409bcae8ada56e46766477fecd05bcfc3c7554a1f4bed20c678542238`.
It contains only IDs, PDF paths, PDF hashes and page numbers; cohort metadata and
private references are absent. The selection is the complete frozen omnidoc
cohort, rather than a difficulty or success filter. Natural64 includes the
screen's sixteen pages and is therefore broader DEV confirmation, not unseen
validation. Report all64 as primary; an additional48 diagnostic must be labeled
as a fixed complement and cannot replace the primary denominator.

The 156 authored cases and 56 unscored native diagnostic pages in corpus-r2 are
separate controls. Pooling them into natural quality would mask the previous
large gap between authored and natural complete-table recovery.

## Matched screen and fresh repeats

Screen up to eight different decision models under one fixed OCR300 / 512-image
ordinal evidence control with the same Haiku assembler. Fix source inventories,
detector model and proposals, image bytes, evidence encodings, admission limits,
assembly settings, provider routing, output budgets, concurrency and local CPU
threads. The gate is the intended intervention; compare source-only/local gates
under that same evidence where available. Price/routing/model catalog snapshots
must remain attached to actual calls. A configured default model is not proof of
an actual request.

Use three fresh repeat blocks on natural16. Alternate or deterministically
shuffle treatment order by block; declare page order seeds in advance, record actual order,
and retain every response and refusal. No local response cache substitutes for a
fresh hosted response. Source preprocessing and detector assets may be reused
with hashes. All blocks retain errors, incomplete dense pages and negative
false positives. Show each repeat independently plus median, range and sample
standard deviation. Do not publish only the strongest repeat.

After screening, freeze configurations and hypotheses before natural64 scoring.
Run the fixed baseline and selected treatments across all64 with the same
source/detector assets. Selection may use the screen only, not intermediate
natural64 quality. The broad pass is one predeclared complete pass per treatment;
if more repeats are feasible, declare them before opening broad scores and retain
all of them. Additional exploratory treatments remain explicitly exploratory.

For decision-only attribution, paired comparisons require identical retained
source and detector-evidence fingerprints. Changed OCR DPI, source tokenization,
image resolution, detector fusion, model transcription or assembly format create
a separate pipeline treatment. A gate may change routing or packet selection as
its intended mediator; report route counts and actual model/stage usage. Hash
agreement on source/detector evidence does not prove every serialized model
packet is identical, so compare stage request/image inventories separately.

## Metrics and uncertainty

Every intended page remains in the denominator, including missing records,
errors and rejected outputs. Partial successful prefixes never become outputs.
Primary metrics are complete tables / 93 or / 53; span-aware exact anchors /
3,847 or / 2,333; exact positive pages / 40 or / 12; negative false-positive
pages / 24 or / 4; extra tables; and errors. Retain structure-only cells, exact
topology, text edit distance, reference characters and IoU diagnostics separately.

The established P002 `correct_text_cells` metric matches text at row/column
anchors while intentionally ignoring the anchor's rowspan/colspan. P003 adds
`strict_exact_cells`, which requires identical anchor coordinates, spans and
normalized text. Both metrics are retained for continuity. Empty anchors count;
covered merged slots do not. A smoke replay of retained
`natural16-yolo-indices-haiku-512-gated-row-evidence` gives 336 P002 text cells
but 324 strict anchors; its original scores are not rewritten.

Positive-page macro recall gives each positive page equal weight, including zero
for failures. Dense newspapers remain in primary micro totals; density and
additional48 splits are descriptive. Negative pages are scored separately and
are not folded into positive recall. These recalls do not penalize extra tables,
so false-positive metrics remain mandatory.

`pages/min` and `pages/API USD` count independently verified complete output
pages. Also retain intended-pages/min and exact-positive-pages/min. Error-heavy
runs can finish quickly; show errors alongside throughput. API cost includes
all run-attributed ledger attempts and failed requests. Positive reported charges
are preferred; reported zero remains zero and token/rate estimates retain their
explicit basis. Unresolved reservations or unknown charges make effective total
and pages/API USD undefined. Free local controls also have undefined pages/API
USD, rather than an invented infinity. Reservation accounting remains separate.

A deterministic paired page bootstrap reports a descriptive 95% interval for
the total exact-cell difference. It includes all pages and preserves pairing,
but does not model hosted-repeat randomness or supply heldout confidence. Three
fresh repeat observations report variation directly; they are too few to claim
calibrated model confidence. Model self-reported confidence is not accuracy.

Record parent wall/process CPU and sampled RSS; record detector/other worker
measurements separately. Parent CPU excludes subprocess CPU, and overlapping
per-page CPU intervals are not additive. RSS peaks from different processes or
intervals cannot be summed as simultaneous peaks. Retain measurement tool,
sampling interval, process scope, thread count, concurrency, machine and versions.
Unmeasured fields stay unmeasured. Separate source preprocessing from remote
inference; source-cache amortization must be explicit in comparisons.

## Existing P002 bottlenecks

These are retained offline diagnostics, not new tuning targets. They do not form
an additive attribution decomposition because stages interact and the bounds
ignore different constraints.

| Stage / fixed evidence | Observed diagnostic | Interpretation |
|---|---:|---|
| Existing native/geometry candidate pool on natural16 | 0/53 complete tables; 7/53 matrix shapes; 6/53 boxes IoU >= .5 | Candidate selection alone cannot recover absent structures |
| Legacy150 literal source inventory | 1194/2333 feasible anchors; 6/53 all-anchor-feasible tables | Optimistic source-ID text supply ceiling |
| Whitespace150 literal inventory | 1238/2333; 6/53 tables | Token joining changes supply but does not repair assembly |
| Whitespace300 literal inventory | 1880/2333; 9/53 tables | Higher source supply; arbitrary order/reuse still overstates achievability |
| Fixed2048 literal inventory | 861/2333; 4/53 tables | Dense viewport OCR resolution can dominate source loss |
| Source-ID Sonnet assembly, legacy150 | 295/2333 P002 text anchors; 2/53 complete tables | Detection/topology/ownership loss remains below the optimistic text bound |
| OCR300 / YOLO / matrix Haiku1024 | 387/2333 P002 text anchors; 3/53 complete tables | Changed multiple stages; cannot attribute gain solely to OCR DPI |
| Sonnet1024 crop transcription | 982/2333 exact-coordinate text anchors; 1146 complete-string inventory matches | Placement-only repair cannot exceed this optimistic retained-string bound |
| Haiku1024 crop transcription | 687 exact-coordinate anchors; 813 complete-string inventory matches | Detection/transcription and output failures remain substantial |

Source-character multiset overlap is not OCR recall. Whole-page strings may
coincide outside their correct table, repeat labels or ignore cell ownership.
Likewise localization IoU is not cell correctness. Missing detector proposals,
missing literal source strings, malformed transcription and wrong placement must
retain their distinct labels; generic routing changes cannot be credited with
repairing text that the source-owned parser cannot emit.

The source ceiling details and preserved original measurements are in
[p002-source-inventory-ceilings.md](p002-source-inventory-ceilings.md),
[p002-source-failures.md](p002-source-failures.md), and
[p002-cell-inventory.md](p002-cell-inventory.md). No new gold-derived parameter or
case-specific fix is selected from those artifacts.

## Offline scoring seam

`bench.p003_report` accepts the existing `report.json`, `frozen.json`, archived
`code/`, per-page result/structure files and exact Markdown files. It verifies
DEV corpus identity and PDF hashes, frozen config/manifest inventory, archived
sources against current local sources or a separately trusted digest manifest,
per-page/report equality, complete source ownership, exact reconstructed Markdown,
and explicit private-reference-field absence in retained request bodies. It
never imports or executes archived Python. The established semantic replay
validator is reused; the new strict metric is independent of model inference.
Schema audits cannot prove absence of paraphrased gold inside arbitrary strings.

Use explicit source-manifest selection for natural64:

```sh
python -m bench.p003_report \
  --corpus bench/results/pdf-master-artifacts/pipeline-p002/corpus-r2 \
  --manifest bench/results/pdf-master-artifacts/pipeline-p003/manifests/natural64.json \
  --cohort omnidoc \
  --run bench/results/pdf-master-artifacts/pipeline-p003/FROZEN_RUN \
  --trusted-code bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/ROOT_COMMIT.json \
  --output bench/results/pdf-master-artifacts/pipeline-p003/FROZEN_RUN/evaluation.json \
  --markdown bench/results/P003_SUMMARY.md
```

For natural16, use the existing `pipeline-p002/screens/natural16` corpus without
`--manifest` or `--cohort`. Add two `--run` arguments and `--paired` for a matched
comparison. Add identical-treatment repeat runs and `--repeat-summary` for fresh
repeat distributions. Root-authenticated digest snapshots must be captured from
reviewed sources before runs; copying the artifact's own `code_sha256` into the
trusted file does not establish independent trust.

Validation: thirteen focused CPU-only Python tests and Ruff pass. An actual retained
P002 sixteen-page invocation verifies complete source/Markdown artifacts and
writes the ignored `pipeline-p003/eval-smoke.json`. No requests, GPU workload or
paid inference were performed by this evaluation task.

## First fresh source-owned control

The root-authenticated `b773d57.json` source snapshot independently verifies
`screen-ordinal-ocr300-512-r0`: all sixteen complete outputs, zero errors,
3/53 complete tables, 384/2333 strict span-aware cells, 397 P002 text-only cells,
2/12 exact positive pages, zero negative false-positive pages and one extra table.
There are 38 missing tables. This fresh observation is one repeat, not a
confidence estimate or a matched improvement claim.

| Run | Outputs | Complete tables | Strict cells | Negative FP | Errors | Pages/min | Pages/API USD | API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ordinal OCR300 / 512 r0 | 16/16 | 3/53 | 384/2333 | 0/4 | 0 | 2.45528 | 786.972 | 0.0203311 |

Run parent processing took 390.9945 wall and 777.3788 CPU seconds, with
748,339,200 bytes sampled peak parent RSS. The report measurement is
`psutil.Process` every 100 ms plus `process_time`; separate detector-worker
measurements remain attached and are excluded from parent CPU/RSS. All eighteen
API attempts have positive reported charges, without estimates or reservations.

The offline replay itself used one CPU reporter subprocess: 0.9604 wall seconds,
0.9562 user-plus-system CPU seconds, 98,212 KiB peak RSS including imports.
Tools were `time.perf_counter` and kernel `resource.RUSAGE_CHILDREN`; RSS is the
kernel process high-water mark, not sampled. No inference call was made by the
evaluator. Raw verification stays at the ignored control's `evaluation.json`.

Repeat configuration checks ignore only `run_id`, `repeat_index` and
`order_seed`; their original observations remain in the summary. All treatment
settings, including gate model and image edge, must match. The documented
implicit `gate_image=True` and `source_order="legacy"` defaults normalize to
explicit equivalents. Different authenticated code snapshots remain visible and
require explicit operator semantic review via
`--reviewed-repeat-code-changes`; authentication alone does not establish
unchanged treatment semantics. Paired reports separately expose gate-image
configuration differences and actual serialized request image hash inventories.

## Incremental retained-state repair verification

`processor="p003_boundary_repair"` is evaluated as repair on retained source
artifacts. Historical baseline report, frozen inventory, code, results,
structures, Markdown and all retained request/response JSON are copied with
hash attestations. Every historical returned call must have its original request
body. Only retained raw response artifacts can be audited; the first fresh source
control stores request bodies and call summaries but no standalone raw response
JSON, which remains an explicit limitation.

The evaluator authenticates baseline code separately using
`--baseline-trusted-code`, verifies original and repaired source/plan/call/timing
lineage, re-decodes every completed region from its native request/menu/provider
response, and compares the independently recomposed complete source-owned output
and exact Markdown. Current local repair replay helpers must match the
independently authenticated repair archive; archived Python is never executed.
Failed atomic repair preserves the complete original output and remains
`status="ok"` when that baseline was valid, with separate repair errors.
Original errors remain errors and skipped repairs remain explicit.

Fresh full-pipeline pages/min and pages/API USD are undefined for this processor.
Incremental attempted-repair-pages/min and pages/API USD have explicit names and
include only its new attempts and measured repair interval. Historical baseline
cost/resources are separate provenance, never charged again as fresh work. A
complete synthetic runner-to-JSON-to-evaluator test verifies actual source
ownership, exact rendering, native response replay and request-copy integrity;
changing a copied request or fabricated updated cell is rejected. No provider
request is made by those tests.

Multiple source versions can be authenticated in one report by repeating
`--trusted-code` once per `--run`; a single shared snapshot also remains valid.
Historical baseline snapshots accept the same shared/per-run convention.

## Source-proposal gated crop verification

The `p003_regions` processor remains table-only model transcription, with
`source_conserved=False` and unverified complete-page coverage. Source child
interpretation must first produce a complete independently replayable source-owned
output. The evaluator then renders the immutable PDF at the fixed proposal
scale, verifies image bytes, regenerates tracks/fixed2 proposals from source and
pixels (or replays ordinary YOLO proposal selection from retained detections),
checks complete gate inventories and exact gate source/image request bodies,
replays the declared probability/overlap selection, and verifies the exact
accepted crop inventory. Fixed transcription rasters/JPEG crops and request
hash/admission metadata must match; each retained raw response is parsed strictly,
and complete crop composition and exact table-only Markdown are reconstructed.
Failures expose no partial tables and stay in all denominators. Unsupported
frozen helper semantics are rejected rather than executing archived Python.

This independent verification performs bounded CPU PDF rendering and image
encoding. Its elapsed/CPU/RSS belong to offline evaluation, not to hosted run
throughput, and no OCR or remote request is repeated. A synthetic source-owned
child plus real frozen PDF raster test verifies the entire empty-YOLO path and
rejects altered proposal image hashes. The retained source fixture is synthetic
input; that test does not claim correspondence with visible text in the blank
PDF raster.

Optional accounting reconciliation preserves the original frozen report and
quality. Invoke the reporter with `--cost-reconciliation <costs.json>` (exactly
one per run) and `--cost-ledger <explicit ledger.json>`. The sidecar binds the
original report hash and exact `P003/<run_id>/` attempt inventory, including
failed and reserved attempts. Every exact archived request body must match its
ledger SHA; retained provider responses must match their sidecar hashes,
ledger filenames and provider attribution. Original per-attempt accounting
must reproduce the immutable report totals and returned-call entries. Changed
entries also require matching preserved ledger accounting revision history.

The only permitted correction adds a finite positive provider-reported BYOK
upstream inference amount to a finite nonnegative gateway charge when the raw
response explicitly declares BYOK. The original gateway zero remains visible;
non-BYOK nested amounts are never added. Unchanged estimates retain their prior
basis, and unresolved reservations keep the reconciled total unknown. Original
and reconciled API costs and pages/APIUSD are separate outputs. The overlay
makes no invoice-total claim and never edits the report or shared ledger.

Frozen candidate selection is verified with `--candidate-trusted-code <map.json>`,
whose independent operator-supplied object maps `baseline-0`, `baseline-1`, etc.
to authenticated basename-to-code-digest snapshots. Trust maps embedded in the
candidate run itself are provenance and cannot authenticate their own code.
All declared historical reports, requests, outputs and code inventories are
hashed; original sources, detector crop inventories and actual crop bytes must
match before pool selection. The verifier reconstructs exact complete candidate
alternatives, deterministic opaque alias order, deduplication, selector pixels
(or declared text-only state), fresh requests, typed probabilities and selected
original input. Selected raw candidate responses are strictly reparsed and
recomposed; unresolved decisions retain the predeclared first baseline.

Atomic ranking failures and baseline-error skips retain the first baseline's
complete output bytes and explicit ranking status/errors. Their quality remains
in all intended-page denominators. Historical generation costs/resources and
new ranking costs/resources are reported separately. Newly measured ranking
pages processed per minute/APIUSD are incremental processing rates, and fresh
full-pipeline throughput remains null. Combined cost across generation pools
requires ledger-index deduplication and cannot be inferred by summing copied
reports, particularly when historical BYOK accounting overlays exist.

### Real frozen candidate-pool preflight and posthoc ceiling

The Luna-first/Haiku-second natural16 preflight used an isolated fake ledger and
always-unresolved typed selector at a declared 512-pixel crop edge. It made zero
paid requests and measured no selector quality. All sixteen original Luna
structure/Markdown outputs remained byte-identical. Independent verification
found seventeen whole-crop pools: fifteen distinct eligible pools on eleven
pages, two duplicate-only pools, two no-crop pages, and one page skipped because
Haiku failed. Actual selector bodies were 13,521–143,646 bytes, within the
750,000-byte admission. No source, image, inventory or request-body mismatch
occurred. The whole CPU process, including copying authenticated originals,
rendering/cropping and independent verification, took 12.16 seconds wall and
12.26 seconds CPU with peak RSS 431,412 KiB via process `getrusage`; no OCR,
network inference or GPU ran. This offline preflight is separate from run rates.

| Evidence on natural16 | Complete tables / 53 | Strict cells / 2333 | Text cells | Negative FP / 4 | Errors | Pages/min | Pages/APIUSD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fresh P003 Luna crops1024 | 3 | 784 | 795 | 0 | 0 | 4.188 | 1234.108, reconciled |
| Fresh P003 pinned Haiku crops1024 | 3 | 393 | 406 | 1 | 1 | 8.491 | 1822.069 |
| Posthoc exact Luna/Haiku whole-crop oracle | 4 | 796 | 809 | 0 | 0 | Unmeasured | Unmeasured |
| Historical P002 Sonnet crops1024 | 5 | 982 | 982 | 0 | 0 | 6.878 | 69.412 |

The oracle enumerates every whole-crop combination (at most four per page),
maximizing strict exact cells, then complete tables, then fewer false tables.
The Haiku-error page keeps the predeclared Luna fallback. Its independent
complete-table ceiling is also four. It has only twelve additional strict cells
and one additional complete table over Luna; these are finite retained-pool DEV
ceilings, not achievable hosted performance or unbiased validation. DEV
references were opened only after source-only pools froze, and neither requests
nor candidate helpers received oracle selections. No oracle cost/productivity
rate is inferred. Historical run timings and financial bases differ and are not
matched throughput trials. Luna's immutable original report has unknown effective
cost; the verified accounting overlay reports USD 0.012964825 across nineteen
BYOK attempts and supplies the separately labeled rate above.

The explicitly named complete P002 Sonnet run has the same frozen sixteen source
records/manifest, detector crop inventories and all nineteen original request
crop pixel hashes. Its report matches tracked P002 SHA
`58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
Its historical strict adapter differs from the current adapter by one model
admission error-message string. That finding permits operator review, not
self-authentication or automatic admission of historical code. Expanding pools
requires an authenticated, separately reviewed whole-run input and keeps the
first-baseline fallback rule; individual crops must not be chosen as inputs by
DEV gold. Ignored full artifacts are under
`pipeline-p003/preflight-candidate-luna-haiku-r0/`, including clearly fake
preflight evidence, exhaustive oracle and Sonnet source/crop compatibility.

Root explicitly authenticated the full historical Sonnet source archive from Git
and reviewed historical parser digest
`8188aca8439f7c4bf455bf81b55a7a3e9f0789ca3590abbd3042d050b784591e`.
Candidate verification requires both the independent baseline digest map and
external `--reviewed-parser-sha256 <digest>` admission matching the frozen
configuration. The sole reviewed digest is allowlisted; archived code remains
unexecuted and current strict parsing/recomposition runs. Frozen self-declared
compatibility alone cannot admit an older parser.

Additional exhaustive posthoc DEV whole-run pool bounds are:

| Declared whole16 candidate inputs | Strict cells / 2333 | Text cells | Complete tables / 53 | Extra tables | Negative FP / 4 | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna + Sonnet | 1088 | 1099 | 5 | 3 | 0 | 0 |
| Luna + Haiku + Sonnet | 1097 | 1110 | 5 | 0 | 0 | 0 |

Both independently optimized complete-table ceilings are five, and both retain
26 missing tables. The same strict-cell objective and atomic first-baseline
fallback rule apply, including the Haiku-error page in the three-input bound.
Each complete source run supplies every eligible crop; no input crop is selected
by gold. These ceilings describe only exact retained alternatives, not an
achievable model result, repeat variance or cost comparison. Oracle selections
stay in ignored offline diagnostics and do not enter source-only evidence.
