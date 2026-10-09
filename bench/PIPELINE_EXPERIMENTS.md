# P001: complete PDF pipeline experiments

Status: implementation and DEV screening, 2026-10-09. This wave has a USD 50
ceiling inside the newly authorized cumulative USD 150 cap. Prior accounting,
including unresolved reservations, is retained. No protected confirmation files
are accessed. Root alone coordinates metered inference.

The previous experiments mostly measured decisions on supplied regions. P001
starts with a PDF page, discovers words and candidate structure automatically,
then emits complete table JSON and Markdown with all remaining source words.
Three parallel worktrees develop the corpus/scorer, whole-page assembly, and
bounded edit policy. Model inputs contain literal source evidence and opaque
source IDs, never family names, reference cells, or scoring feedback.

## Frozen screening design

1. **Native baseline:** preserve vector grids and source text without a model.
   This is the minimal faithful arm. Also measure the opt-in native text-table
   strategy to expose its table/prose tradeoff.
2. **Whole-page assembly:** generate physical, rolling, and seed-band
   alternatives; ask a decision model to select a complete assembly or abstain.
   Compare full-page RGB images at 256, 512, and 1024 pixels on the same pilot.
   A vector-first cascade tests whether reliable geometry can eliminate calls.
3. **Bounded edits:** start with a source-only provisional assembly and offer
   coordinate-addressed row edits or table rejection. Compare one versus three
   neighboring rows, with an evidence-availability legend. At most two model
   edit steps per page; each step validates exact source ownership.

Primary models are Perplexity decider, Clef Flash, and Luna decisions. Live
OpenRouter capabilities and token rates are retained before calls. Hosted APIs
permit this phase without idle GPU rentals; local preprocessing remains CPU-only.
Additional models or prompt arms require a recorded hypothesis before execution.

## Gates and measurement

The corpus agent freezes a balanced pilot and a broader DEV cohort before any
model output is scored. Construction references stay separate from inference.
Natural pages with incomplete references are diagnostic-only. Synthetic siblings
are correlated, and none of these results establish independent generalization.

Primary quality is exact complete table structure per scored page. Also report
positive-table pages separately from negative pages, exact cell and span scores,
false-positive tables, candidate recall, failures, and source conservation.
Source conservation is an engineering invariant, not a semantic quality score.
Missing candidates stay in the end-to-end denominator. Image-only inputs without
OCR are explicit unsupported failures, not successful empty extractions.

An experimental improvement requires at least two additional exact positive
pages without additional false-positive pages on the matched pilot; otherwise
retain the baseline and report the tradeoff. This is a screening criterion,
not a significance claim. Broad runs include promising and moderately plausible
arms; selection and subsequent DEV measurements remain explicitly exploratory.

Timing starts before opening each PDF and includes extraction, proposal,
rendering, packet construction, all hosted calls/telemetry, validation, and
writing final JSON/Markdown. Scoring is outside extraction timing. Report pages
per minute using completed output pages and total elapsed pipeline time, and
pages per USD using positive reported charges or labeled catalog estimates.
Also show exact-positive-page rates where possible. API failures and reservations
remain visible; unknown cost is never represented as free.

Record wall time, process CPU time, and sampled process RSS (100 ms interval),
concurrency and runtime. Provider GPU utilization is unavailable for hosted APIs.
Run three independent native timing repetitions; hosted screening is one fresh
transmission per condition, with provider-reported cache usage retained. Local
response replay is disabled. No unsupported precision or latency claims follow
from a single screening pass.

Raw sources, requests, responses, references, outputs, and ledger are ignored
artifacts under `bench/results/pdf-master-artifacts/pipeline-p001/`. Commit code,
designs, aggregate results, and reproducible commands only.

## First screening checkpoint and additional frozen hypotheses

The 32-page PPLX/512 arm recovered 15/16 positive pages exactly and falsely
admitted tables on 4/16 negatives. Clef Flash/512 recovered 5/16 with no negative
false positives. PPLX/256 and Luna/256 or /512 recovered the same 15/16 with
4/16 negative false-positive pages. These are exploratory paired observations.

Before further calls, add these mechanisms as separate arms:

- **Orientation normalization:** inspect the source page's `/Rotate`, set it to
  zero on the runner-owned loaded document, then extract and render consistently.
  This changes both evidence coordinates and pixels together. Synthetic 90/180/270
  checks preserve source words and match normalized image hashes. No source file
  or private target is changed. This addresses a candidate-discovery failure;
  larger model images cannot select a correct candidate that is absent.
- **Independent admission:** ask table/prose/unresolved from full source evidence
  before showing assembly hypotheses, then assemble only admitted pages. Compare
  minimal and relational premises; the latter asks whether rows share a record
  and attribute schema or whether prose flows independently down columns. Charge
  both calls. Reliable vector grids retain the native fast path.
- **Adaptive evidence:** source-only column conflicts, sparse/wrapped rows and
  text density select repair versus whole-page assembly and 256/512/1024 pixels.
  Context expands to three rows for observable wrapping ambiguity. Frozen rules
  contain no family names, source identities, expected text or private outcomes.

The six packet refusals from source preflight remain recorded: five oversized
complete packets and one incomplete native span tiling. Image-only sources without
OCR are explicit unsupported cases. A successful output conserves extractable
snapshot words, which does not establish preservation of unmapped glyphs or pixels.
