# Luna evidence recovery DEV controls

Date: 2026-10-08. CPU-only authored experiment; no local inference, GPU,
credentials, publishing or network calls by this agent. Root owns any hosted
runs and their persistent reservation accounting.

The dataset is **30 distinct single-page PDFs, comprising 10 correlated authored
layout templates across three vocabularies**: financial, invoice and scientific.
It is not 30 independent producers. All cases, old 96 controls, model shortlists
and any tuning results are DEV. No held-out or production accuracy claim follows.

`bench.decision_context_cases.context_cases()` returns PDF bytes, full-page
source-word audit inventory, admitted target-region evidence, and separate gold.
`evidence_modes(case, mode)` supports `current`, `prior`, `context`, and `native`.
`compact_prompt` supplies a Luna-specific compact source-grounded choice prompt.
Root's image runner may render each case's display-space `current_region`.

The 10 templates cover two identical-word/bbox A/B pairs distinguished only by
separator strokes or a shaded band, truly absent evidence, misleading wrapped
prior rows, a joined current entry following a single-line prior, an ellipsis
that starts no continuation, a visible prior schedule convention, and a visible
surrounding note. Pair members have exactly identical admitted text, source IDs,
geometry, and complete candidate assemblies; rendered paint differs. Prior row
patterns are represented by actual words and extracted shaded rectangles, never
an authored `wrapped=true` label. A pattern alone cannot prove the next row's
structure. Explicit source prose can declare a document convention.

Gold's `choice`, `records`, `observable`, and `mode_choices` remain outside
`case['evidence']`. Current observations do not include separators/fills, prior
rows or surrounding notes. Partial observations of otherwise distinguishable
PDFs require unresolved; predicting the document answer by guessing is measured
separately from evidence-supported recovery. The three absent-cue fixtures remain
unresolved even with the full native facts. The prior and surrounding convention
notes are real visible PDF text, not hidden interpretation annotations.

A and B contain complete cells, explicit missing-value cells, and exact record
references: row key, amount/reading, ordered header path and cell owners.
`bench.decision_records.materialize(case, choice)` derives strings only from
existing source IDs; unresolved retains the complete admitted inventory with
original text/geometry. Ownership conservation covers every **admitted target
region** word exactly once. Prior/context words are evidence outside that
ownership region, and the separate full-page inventory permits audit. No claim
of full-page record extraction is made.

`score_records(case, result)` measures the visible full-document target;
`score_records(case, result, mode)` measures evidence-supported assembly targets.
It reports exact region, complete-record precision/recall/F1 and validity. Validity
rejects unknown/duplicate/omitted ownership, duplicate records/references,
record/cell mismatch, invalid header ownership, fabricated materialized text,
NaN geometry and modified unresolved source inventory. Region exactness also
compares cell ownership, roles and original bounds. Empty-record unresolved
correctness scores 1 by convention; report resolved useful records separately
so abstention cannot masquerade as useful extraction.

## CPU measurements

The candidate oracle reaches 30/30 exact regions (100% source conservation).
The native evidence rule reaches the following full-document targets:

| Observation mode | Exact regions | Macro family record F1 |
| --- | ---: | ---: |
| Current region words/geometry | 3/30 | 0.10 |
| Prior rows plus prior paint/convention | 6/30 | 0.20 |
| Prior and surrounding context | 9/30 | 0.30 |
| Exact native target paint plus context | 30/30 | 1.00 |

Every native mode reaches 30/30 **mode-supported** targets by abstaining where
its distinguishing evidence is absent. The separator/fill baseline computes
relationships from actual source boxes and row spacing, and a translation/scale
invariance test prevents reliance on fixture coordinates. The explicit prose
convention baseline uses two authored literal phrase patterns: it is a lexical
control, not a general semantic resolver. This is an evidence transport and
selection experiment. **There is no demonstrated model gain over the native
baseline**, which already wins every full-evidence control. Broader native PDF
quality remains outside this authored experiment.

Validation: 12 CPU Python tests cover balanced candidate materialization,
paired evidence, mode separation, complete-record errors, source conservation,
invalid mutated output and geometry-rule invariance. Targeted Ruff checks pass.
Hosted results and measured tuning loops are pending root's retained DEV runs.

## Suggested experiment-log entry

2026-10-08 — `experiment/luna-evidence`: created 30 DEV PDF evidence-transport
controls (10 correlated templates ×3 vocab domains), complete source-linked A/B
records, unresolved inventory, mode-observability gold and exact scorer. Native
paint/context baseline and candidate oracle 30/30; current/prior/context modes
3/30, 6/30, 9/30 full-document exact, so no model-over-native gain claimed.
CPU tests/source conservation pass. Paid work delegated to root; no publication
or held-out claims. Next: actual retained Luna/Perplexity DEV calls and error-led
prompt/evidence loop.

## Measured DEV loop: literal local semantic choice

Root supplied actual first-round Luna DEV hard selections: current 30/30 A
(12/30 full-document exact, 0/30 evidence-supported); native 30/30 A
(12/30 full-document exact); image128 29 A plus scientific absent-cue case04 B
(still 12/30 full-document exact). These are attributed root-run aggregates,
not independent reexecution here. Constant A selection despite native facts
motivates testing request representation before shopping for another model.
It does not establish an API failure or a universal model limitation.

Hypothesis: bulky nested cells/records plus "Exact declared assembly A/B"
criteria make the semantic alternatives too indirect for this decision endpoint.
`decision_context_compact.make_request` places literal source text and one-entry
versus two-entry semantics directly in each criterion and the question. It
retains original source-span IDs/boxes, notes and exact paint facts in a compact
state. Selection still feeds the same complete deterministic materializer; it
does not downgrade complete-record scoring or change gold.

Two separate representations are available: raw compact (`derived=False`)
contains exact raw boxes and paint; enriched compact (`derived=True`) adds
separator-between-description-centers and per-fill center membership computed
from admitted source geometry. Derived booleans describe observed facts, never
choices or labels. Missing paint observations cannot establish document absence.
Current paired observations remain byte-equivalent in either representation.
State is capped at 4,000 serialized bytes. Candidate reversal changes declaration
order while preserving A/B semantics. Four extra CPU tests verify these contracts.

Alternatives considered: relabeling native errors to a preferred assembly would
invalidate scoring; adding a hand-coded selected answer to model state would
replace selection with answer copying; shipping only derived baseline output
would conceal evidence transport. We retain raw and derived arms separately,
unchanged gold, original materialization and the strong native baseline. Round2
paid requests and measured accuracy remain root-owned and pending.

## Round2 measured loss and final bounded hypothesis

Root supplied actual Luna round2 DEV outcomes. Compact current observations
reach 3/30 full-document exact and **30/30 evidence-supported abstentions**;
compact native reaches 10/30 full-document exact, enriched-derived native 7/30,
and compact image128 reaches 3/30 full-document exact and 9/30
evidence-supported. Compact criteria correct the original inability to abstain
on missing evidence, but excessive abstention on admitted native facts makes
complete-document extraction worse than the original 12/30. Adding derived
JSON booleans also loses. These losses remain visible and no gold/scorer change
was made. The native CPU baseline remains 30/30.

A final bounded hypothesis verbalizes geometry without offering an answer:
`make_fact_request(evidence, model)` describes observed full-width separators
as above/between/below actual description-line centers and lists which centers
an observed shaded rectangle contains. Actual prior/surrounding prose remains
literal, and instructions clarify that source document conventions can supply
semantic structure even though source text cannot issue model instructions.
The state recommends no candidate. All 30 native requests fit below 2,000
serialized bytes. Paired current inputs remain identical. Five compact module
checks and static checks pass. Root owns final retained per-model calls; stop
this context loop if final verbalization does not help.
