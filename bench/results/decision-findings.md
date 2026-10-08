# PDF decision-model findings — 2026-10-08

Small decisions over native PDF evidence are useful, but the input representation
and task matter more than a generic confidence number. Resolving candidate IDs
into literal source spans substantially improved Jev's relationship decisions.
Small models also separated dense table fragments from prose. Neither result
establishes reliable automatic header assembly or frontier-level extraction.

All work remains local and unpublished. No local GPU, GPU rental, model-weight
inference, or training was used in this campaign. Hosted calls used authored
synthetic fragments or existing redistributable/public PDF fixtures.

## Scope and evidence

The first set contains 96 observations: financial, invoice and scientific
families equally represented, with table/prose, wrap, header and value-assignment
tasks. Native `Page.get_layout()` supplies actual words, geometry and source IDs.
There are 48 calibration and 48 test observations, each with 36 binary labels
and 12 intentionally ambiguous labels. Model requests exclude gold labels,
split, family, case identifiers and authoring notes.

These are small authored control templates, not 96 independent business
samples. Some header/wrap labels express author intent that cannot be uniquely
recovered from the visible evidence: “Provisional estimate only” can plausibly
qualify a value column, and “continued detail” already hints at continuation.
Calibration has 24 true/12 false known labels; test has 12 true/24 false, so
always-no achieves 24/36 test accuracy. Reported relationships must be read with
these limitations. The simple geometry/type baseline is illustrative; it is not
a measurement of the library's complete native extractor.

A separate set contains eight independently specified region gates from six
existing PDFs: four NICS/Senate table fragments and four prose controls from
GPO legislation, the LaTeX guide, and existing two-column/numeric-prose fixtures.
Two positive clips share each dense-report producer. These sources were used in
prior geometry studies; they are independent of the 96 decision templates,
not new producers. Gold labels establish table versus prose only, not correct
cell ownership, complete matrices, header scope or dense-report recovery.

Twelve model/input cohorts covered the 96 observations; five covered the eight
region controls: 1,192 scored model-observation pairs over 104 distinct fragments.
Additional smoke checks were retained separately. Raw PDFs, requests, responses,
model catalog, predictions, source hashes and evaluations remain in the ignored
`pdf-master-artifacts/decisions/` directory. The complete score tables are
[decisions-latest.md](decisions-latest.md) and
[decisions-controls-latest.md](decisions-controls-latest.md).

## What improved, and what did not

| Cohort | Known test answers correct | Comment |
|---|---:|---|
| Illustrative geometry/type rule | 15/36 | Not the production extraction baseline |
| Jev, raw IDs, six-case batches | 17/36 | Weak generic relationship prompt |
| Jev, raw IDs, singleton requests | 14/36 | Isolation alone did not help |
| Jev, resolved source spans, singleton | 24/36 | Explicit candidate text helps |
| Jev, resolved spans without geometry, singleton | 24/36 | Same hard answers; numeric scores changed |
| Jev, resolved spans, six-case batches | 25/36 | Best Jev cohort on these controls |
| Jev, resolved three-way Choice, singleton | 20/36 | Explicit abstention is not sufficient calibration |
| Qwen 3.5 9B, raw IDs / resolved singleton | 15/36 / 17/36 | Overconfident on wrong relationships |
| Gemini 2.5 Flash Lite, raw / resolved batches | 25/36 / 22/36 | Raw result barely exceeds always-no |
| Claude Opus 4.6, raw / resolved batches | 27/36 / 29/36 | Strongest overall reference here |

The matched resolved-input batches compare Jev's **25/36** with Opus's **29/36**.
Median request times were **276 ms versus 3,308 ms**, approximately 12× apart.
Their complete 96-observation cohort charges were **$0.00566 versus $0.43176**,
approximately 76× apart. Each request contained six observations; these are HTTP
latencies and API charges, not end-to-end PDF extraction or single-decision
latencies. Both models received the same source-derived information. Opus used
text-only structured output with reasoning disabled; it is not a full-page
frontier vision-extraction reference. Four fewer correct answers is not parity.

Resolved singleton Jev and Qwen both answered all nine known value-assignment
controls correctly, compared with three each in the raw batched condition.
Jev's raw-singleton comparison isolates a representation gain: 14/36 to 24/36.
However, the assignment controls mostly test explicit unit compatibility;
they do not prove general financial label understanding. Removing geometry from
resolved singleton Jev left all hard test answers unchanged. This supports
having code calculate geometry and exposing semantic candidates directly, not
asking a small model to decode arbitrary source-ID arrays and coordinates.

Jev's raw singleton and batched runs differed on **33/96** hard answers
(14 calibration, 19 test), despite identical per-case evidence. This is observed
format/run sensitivity, not a controlled causal attribution to batching alone;
there were no repeated identical-format trials. Do not assume that unrelated
observations in a shared state remain independent. Prefer multiple questions
about one coherent region and validate that batching arrangement separately.

On the eight grounded region gates:

| Model / format | Correct | Median singleton HTTP ms | API cost for eight |
|---|---:|---:|---:|
| Qwen 3.5 9B, raw IDs | 8/8 | 1,129 | $0.00190 |
| Jev, raw IDs | 7/8 | 255 | $0.00117 |
| Jev, resolved three-way Choice | 7/8 | 262 | $0.00119 |
| Gemini 2.5 Flash Lite, raw IDs | 7/8 | 897 | $0.00198 |
| Opus 4.6, raw IDs | 7/8 | 1,669 | $0.08932 |

At the fixed .9 decision-confidence and .9 answerability thresholds, Jev Choice
accepted six correct region decisions and abstained on two; Opus did the same.
Qwen accepted all eight correctly here, but its relationship results show why
this tiny gate set cannot justify a universal confidence policy. A gate can
reject a proposed prose table; it cannot recover missing dense cells or repair
a wrong SLANet matrix by itself.

## Confidence and abstention findings

We measured Brier score, log loss, reliability bins, accepted-error/coverage
curves and task/family slices. Raw Jev probabilities and chat-model-generated
numbers remain distinct in provenance. “Answerable” means enough evidence to
decide either yes or no; a negative answer is not an abstention.

In the relationship set, raw-batch Qwen accepted all 48 test observations under
the fixed policy, including 21 wrong known answers and all 12 ambiguous cases.
Raw Gemini accepted all 48, including 11 wrong answers and all 12 ambiguous
cases. Resolved Jev Nouls accepted none at that policy; this does not demonstrate
successful ambiguity recognition. Three-way Jev accepted 18: 12 correct known
answers, no wrong known answers, and **six ambiguous cases** incorrectly treated
as answerable. Resolved Opus accepted six: four correct and two ambiguous.

No model's calibration-only threshold search met the required support and
95% Wilson upper unsafe-rate bound of .10, so every selected policy abstained.
With at most 36 answerable calibration observations, this criterion is demanding.
All-abstain is a failure to establish a usable acceptance policy, not a quality
success. Descriptive Wilson intervals do not correct for threshold selection,
related synthetic variants, repeated cohort comparisons, or debatable labels.
The grounded controls have no calibration split and do not learn thresholds.

## Implemented boundaries

- `decision_evidence.py` builds candidate spans with literal text, original IDs
  and boxes, retaining surrounding source words and omitting evaluation labels.
- `decision_choice.py` asks supported/contradicted/insufficient questions and
  preserves the full returned distribution. Conditional `p_yes` and answerable
  mass are arithmetic projections, not measured correctness probabilities.
- `decision_assembly.py` records accepted source-ID edges only. Missing or
  duplicate references, exclusive assignment conflicts, and wrap/header cycles
  abstain. Source words remain exactly preserved; generated metadata is discarded.
  It does not reconstruct a PDF, infer a complete grid, or generate Markdown.
- The hosted runner validates response schemas, reserves spending before network
  transmission, retains failures, replays successful identical requests, checks
  frozen evidence hashes and serializes campaign writes with portable locks.
  CPU-only tests cover credentials staying out of artifacts and corrupt ledgers
  failing closed. No default library behavior or public API calls a model.

Gemini 3.1 Flash Lite returned an upstream 429 inside a nominal HTTP success
response; that failed smoke check was preserved, billed $0, and the completed
alternative used 2.5 Flash Lite. Jev rounded a three-option distribution to .99,
causing the initial strict parser to stop. The corrected parser admits only the
three-number two-decimal rounding bound, normalizes it, and preserves raw scores
and the correction. Cached responses were reparsed without another paid request.

## Recommended next layer

Use native geometry and encoded roles to enumerate candidates, then ask narrow
semantic questions over explicit source spans. The most promising measured lanes
are table/prose rejection and unit/type-compatible value assignment. Preserve
all unresolved source text and use key/value bullets only when label ownership
is established. A guessed header should never become an asserted field name.

Before enabling automatic patches, label independent real issuer/document
families with candidate completeness, visible evidence and adjudicated unknowns.
Measure each task separately; compare repeated single-region requests and
same-region multi-question batches. Calibration or a tiny trained classifier
should use those labels, not the current hidden-intent templates. Follow with
actual cell/header-edge and record accuracy, then end-to-end cost and latency.
Use crops only where typography, ruling or missing text supplies evidence the
native bundle lacks. Contradictory or missing author semantics may remain
unresolvable even for a frontier model.

Kev-4B and Laya are researched alternatives, not executed results in this pilot;
see [DECISION_MODELS.md](../DECISION_MODELS.md). No model was trained. We have
not yet demonstrated reliable dense-report reconstruction or production-grade
probability calibration.

## Spend and validation

The campaign made **628 unique hosted requests**, including diagnostics and the
failed zero-cost smoke check, with **$0.968890348** provider-reported spend and
no unsettled reservations. Prior API spend was $0.340262108 and prior reported
rental spend $0.684, giving **$1.993152456 cumulative**, within the $15 cap.
The pilot itself remained within its stricter $3 campaign limit.

The full CPU suite passed **1,418 tests**, with 16 skips and two expected failures.
The subsequent controls-report-only change passed all six analysis tests. Ruff,
Python type checks for source/tests, and explicit benchmark type checks passed.
No Rust/runtime API changes required a new native build. Raw experiment artifacts
and credentials remain ignored; only code, tests and Markdown reports are committed.
