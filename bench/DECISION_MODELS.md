# Typed decisions for PDF relationships

Research checked on 2026-10-08. This is a narrow proposal for choosing among
retained PDF candidates; it does not change the default extraction API.
The earlier Jev geometry gate recovered seven of nine positive tables and
rejected all six negative controls at roughly 0.25 seconds per call. That small
study does not establish header semantics, calibration, or value assignment.
Its fixed 0.5 gate and provenance are described in
[STRUCTURE_BENCHMARKS.md](STRUCTURE_BENCHMARKS.md).

## Endpoint facts that affect the experiment

The official [OpenRouter Decisions reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
documents `POST https://openrouter.ai/api/alpha/decisions`, with `model`,
`state`, and a named `questions` object. Pin `typesafe/jev-1.13`; retain the
dated model ID actually returned. State can be a string, object, or array.
A `noul` question returns `answers[id].noul`, a scalar probability of true.
A `choice` question uses an object mapping option IDs to descriptions and
returns `choice`, `probabilities`, and `confidence`. A `score` uses an ordered
criteria array and returns a possibly fractional score plus a distribution
and legend. Score is unsuitable for selecting a discrete row count or header
ID. Parse the typed fields, check the expected question IDs and finite
probabilities, and retain the complete response and usage.

[TypeSafe Noul documentation](https://docs.typesafe.ai/primitives/noul)
specifies optional criteria with literal `true` and `false` keys. It also says
question IDs are not sent to the model: put the actual target source IDs and
the relationship being assessed inside each instruction. A key named
`header_h17` is insufficient context by itself.

[TypeSafe's introduction](https://docs.typesafe.ai/introduction) says questions
share the state but are evaluated independently and in isolation. This makes
several atomic questions in one request attractive, but does not make their
answers globally consistent. Its claim that extra questions barely affect
latency is a vendor claim to measure on the actual PDF evidence bundles.

Jev's `confidence` is a distribution statistic, not an independently measured
probability of correctness. For a Choice with `n` options it equals
`(p_max - 1/n) / (1 - 1/n)`. Nouls have no separate confidence. Keep `p_max`,
runner-up probability, and the full distribution; thresholds depend on the
question and candidate set. See the official
[confidence formulas](https://docs.typesafe.ai/confidence).

## Candidate models and what has actually been established

| Candidate | Useful role | Evidence boundary |
| --- | --- | --- |
| Jev 1.13 | Hosted, typed ranking/gating baseline; narrow text/geometry evidence | Official endpoint and probability output exist. PDF-domain reliability must be measured. |
| Gemini Flash Lite; Qwen3.5 9B or 35B-A3B | Small chat controls over exactly the same choices and state | A schema-valid answer or generated confidence number does not prove a calibrated decision. Record actual served model and settings. |
| Claude Opus 4.6 | Frontier control for difficult header/value relationships | Useful comparison for semantic reasoning; latency/cost and self-reported confidence remain separate measurements. |
| Kev-4B, then Kev-9B if justified | Later remotely hosted open decision control or domain adaptation | Author repository supplies versioned weights, evaluation artifacts, and serving code. No PDF relationship result is established here. |
| Laya typed-decisions checkpoint | Later compact open encoder control for short evidence bundles | Actual author implementation exists, but truncation and label sensitivity require explicit checks. |

The actual [Kev author repository](https://github.com/jaredpalmer/kev) is
`jaredpalmer/kev`, rather than similarly named API wrappers. It describes
Qwen-based decision models, shared state with isolated questions, fitted
temperature, and pinned `v1.0` revisions. Its published evaluation distinguishes
development and test sets, but those general decision suites do not establish
PDF header performance. Start with 4B on an authorized remote worker before
paying for a larger model; preserve base/adapter revisions and temperature.

The actual [Laya author repository](https://github.com/NandhaKishorM/laya)
documents an English default context of 512 tokens and multilingual/typed
defaults of 1,024; multilingual can be configured up to 8,192. Normal prediction
can silently truncate state. Its confidence uses normalized entropy rather
than Jev's formula, and it documents label sensitivity and limitations of
generic zero-shot typed decisions. Do not transfer Jev thresholds, assume a
long state was read, or treat its repository benchmark as PDF validation.
Prefer short, explicitly bounded evidence and a pinned checkpoint.

No weights, inference, or training were run for these open alternatives during
this research. Local verification remains CPU-only. Pricing is deliberately
omitted: the pilot's provider-reported usage and dated served-model metadata
are more useful than an undated price claim.

## Two layers, with code owning the constraints

1. **Geometry and provenance layer.** Native extraction keeps positioned text,
   vector evidence, explicit grids, candidate regions, and snapshot-local source
   IDs. Generate bounded alternatives for one ambiguity, including an explicit
   abstain/none option. Preserve the original result as a fallback. Candidate
   omission is a separate failure from wrong ranking.
2. **Optional decision layer.** Send a compact evidence bundle and ask atomic
   relationship questions. Rank only the retained alternatives, then apply
   deterministic constraints and validated patches. Escalate unresolved cases
   to a stronger text or crop control when additional evidence can help.

The following bundles specify information the decision layer needs. They are
experimental designs, not measured quality claims.

| Decision | Retained evidence | Question and allowed result |
| --- | --- | --- |
| Wrapped row continuation | Adjacent physical-line source IDs and text; normalized boxes; baseline/leading; column occupancy; rules; nearest rows above/below | Choice: continuation of row R, start of next row, separate prose, or insufficient evidence. Include the literal target IDs in instructions. |
| Header role and scope | Candidate header spans; exact text/source IDs; candidate column ranges; merged-cell anchors; neighboring header levels and several body rows; units/caption | Choose among explicit source-ID relationships: header H governs columns C, row labels R, local section S, none, or abstain. Repeated text must retain distinct IDs. |
| Value assignment | Field label and expected value kind; all plausible nearby source spans and text; relative positions; units; competing labels; table/header path | Choice among candidate spans or none/abstain. Ask which source span belongs to this field, rather than generate the value. |
| Region gate | Proposed region bounds; row/cell occupancy; representative text; neighboring prose; grid support; geometry diagnostics | Noul for a narrowly defined structural statement, or Choice among table, aligned prose, form, other, insufficient evidence. Rejecting a proposal does not recover a missing table. |

Allow only known source IDs, permitted edge/assignment operations, bounded
spans, and existing geometry. Reject invented text, IDs from another snapshot,
duplicate ownership, conflicting labels, cycles in the header hierarchy,
nonrectangular merged coverage, and header bands that cut merged cells.
Preserve unresolved assignments explicitly. Valid source IDs establish
provenance, not correct semantics.

Use one Choice for mutually exclusive alternatives. Separate Nouls for each
candidate can all be high simultaneously; normalizing them afterwards does not
repair missing options or contradictory questions. For competing assignments,
solve a bounded global assignment over retained edges, with unassigned slots
and explicit capacities. Compare the best and next feasible solutions and
abstain when they are effectively tied. Treat sums of log probabilities as a
ranking objective, not a joint correctness probability: questions and errors
can be dependent. An independent recent
[coherence preprint](https://arxiv.org/abs/2609.33209) reports inconsistency
between Jev's logically related questions; it reinforces the need for local
constraints and does not measure PDFs.

## Batching and escalation economics

Batch independent questions sharing one small region state into one request.
Put different region evidence in separate bounded bundles unless all questions
can reference their targets unambiguously. Do not ask a later question to use
an earlier answer from the same Jev request. Header candidates that depend on
an accepted wrap decision require either a second stage or complete alternatives
prepared before transmission.

Measure one request with 1, 4, and 16 questions against the same total decisions
sent individually. Retain request wall time, token usage/cost, error/timeout
counts, decision flips, bytes sent, and p50/p95 where repetitions support them.
At the earlier approximately 0.25-second request time, 100 serial calls imply
roughly 25 seconds of waiting before other work; that is arithmetic, not a
throughput benchmark. Batching may save network round trips and repeated state,
but provider billing and question overhead must be read from actual usage.
Bound request sizes and in-flight work; no automatic retry should silently
consume the experiment's cap.

Escalate a single region crop when pixels contain missing discriminating
evidence: visible ruling, a merge boundary, typography, or text whose extraction
is incomplete. Include a little surrounding header/body context, the crop's
display-coordinate transform, and retained source IDs. Hold the alternatives
fixed and validate the returned patch. A stronger text control should come
first when the ambiguity is semantic and the text/geometry already contains
the relevant evidence. Vision cannot establish author-declared header roles
when two roles have identical visible pixels. Missing candidate content requires
an explicit extraction/OCR recovery stage, not a forced choice among wrong spans.

## Probability reliability and stop conditions

Keep three quantities distinct: raw decision-model probabilities; a chat model's
generated confidence; and observed correctness on held-out PDF relationships.
Neither schema enforcement nor a high raw probability supplies the third.
Temperature scaling is a practical calibration baseline in
[Guo et al.](https://arxiv.org/abs/1706.04599), while
[Ovadia et al.](https://arxiv.org/abs/1906.02530) show that post-hoc calibration
can fail under distribution shift. PDF language, producer, layout, extraction
quality, and candidate-set changes should therefore remain explicit strata.

Freeze candidate generation and prompt templates; split documents/producers
rather than individual near-duplicate rows into development, calibration, and
test sets. Label header edges and value ownership, including intentionally
unidentifiable cases. Fit any calibration mapping only on the calibration
split. For hosted probabilities, preserve the original distribution and the
fitted transformation; do not pretend unavailable raw logits were observed.
Report accuracy, candidate recall, Brier/log loss, reliability bins with counts,
accepted error versus coverage, abstention, patch rejection, and total document
cost/latency. Keep LLM self-reported confidence separately labelled and assess
it on the same held-out cases before using it as a gate.

Stop automatic acceptance when the model/prompt/candidate schema changes;
evidence is truncated; the correct candidate is absent; labels are duplicated
without distinguishing evidence; constraints conflict; the global solution is
near-tied; or a subgroup lacks enough held-out support. Never infer an acceptance
guarantee from nine positive tables. The next useful result is a measured
relationship comparison with retained failures, not another whole-document
generation score.


## Implemented pilot and reproduction

The local implementation and measured wins/failures are in
[decision-findings.md](results/decision-findings.md), with complete metric tables
in [decisions-latest.md](results/decisions-latest.md) and separate region controls
in [decisions-controls-latest.md](results/decisions-controls-latest.md).

`decision_cases.py` authors 96 partial observations through actual PDF native
extraction. `decision_controls.py` retains eight independently specified regions
from six existing PDF sources. `decision_evidence.py` resolves candidate IDs to
literal source spans; `decision_choice.py` tests mutually exclusive support,
contradiction and insufficient evidence. `decision_eval.py` measures scores and
selective acceptance; `decision_analysis.py` measures isolation sensitivity and
source conservation. `decision_assembly.py` records validated relationships only:
it neither generates replacement text nor reconstructs a PDF or Markdown table.
The public library has no new inference dependency or automatic model gate.

Run only local evaluation with:

```bash
CUDA_VISIBLE_DEVICES='' uv run python -m bench.decisions --report-only
CUDA_VISIBLE_DEVICES='' uv run python -m bench.decisions --report-only --controls
```

Explicitly opt into metered inference, selecting each frozen cohort:

```bash
CUDA_VISIBLE_DEVICES='' uv run python -m bench.decisions --run-hosted \
  --models typesafe/jev-1.13 --variant resolved --batch-size 6
CUDA_VISIBLE_DEVICES='' uv run python -m bench.decisions --run-hosted \
  --models typesafe/jev-1.13 --variant choice --batch-size 1
CUDA_VISIBLE_DEVICES='' uv run python -m bench.decisions --run-hosted \
  --models qwen/qwen3.5-9b --controls --batch-size 1
```

Variants are `rich` (ID references and positioned words), `resolved` (literal
candidate spans plus the same source evidence), `text` (raw IDs without geometry),
`resolved-text` (resolved spans without geometry), and Jev-only `choice` (resolved
spans and a three-option decision). Batch sizes are 1 and 6. `--smoke` and
`--single` are calibration diagnostics stored as raw requests, not scored cohorts.
No threshold, prompt or gold label is silently changed by the runner.

A root `.env.remote-hosts` must contain `OPENROUTER_API_KEY`; it is read without
shell evaluation and never written into artifacts. The prior study's
`bench/results/structure-artifacts/hosted-ledger.json` is required to account for
historic API spend; do not fabricate a zero ledger when spend exists. The pilot
reserves $0.30 before each bounded request, limits new campaign accounting to $3,
and includes the prior $0.684 rental and historic API ledger against the user's
$15 cap. Finite provider-reported USD replaces the reservation; unknown charges
retain it. Failed identical requests require investigation, not automatic retries.
Successful identical requests replay their retained response without another call.
One runner lock prevents concurrent result overwrites. Existing predictions must
match the frozen case hash before any manifest is rewritten.

Raw requests, responses, source PDFs, frozen manifests, model catalog, complete
predictions and evaluations stay under the ignored decisions artifact directory.
Reports distinguish complete HTTP request latency from batch amortization and
include campaign-wide accounting, even in the separate controls report. Jev Choice
returns two-decimal probabilities that can total .99 or 1.01: the parser admits
only the three-value rounding bound (.015), normalizes it, and retains raw values
and the normalization delta. This arithmetic does not calibrate probabilities.


The subsequent [eight-model catalog check](DECISION_CATALOG.md) discovers native
decision models with `GET /api/v1/models?output_modalities=decisions`; the default
model listing omits them. The runner now accepts those exact IDs on the alpha
Decisions endpoint, retaining the original default model list. See the separate
[measured comparison](results/decision-alternatives.md) for successful probes,
availability failures, prices actually reported, and quality limitations.
