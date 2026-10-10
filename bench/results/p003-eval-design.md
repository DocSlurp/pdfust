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
shuffle treatment order by block; keep page order fixed, record the actual order,
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

Validation: eight focused CPU-only Python tests and Ruff pass. An actual retained
P002 sixteen-page invocation verifies complete source/Markdown artifacts and
writes the ignored `pipeline-p003/eval-smoke.json`. No requests, GPU workload or
paid inference were performed by this evaluation task.
