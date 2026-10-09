# Observed history and complete assembly prompts — DEV design, 2026-10-08

The text experiment compares Perplexity Decider and Luna Decisions on identical
source-preserving A/B assemblies with an explicit unresolved outcome. It prepares
requests only; the root runner owns hosted calls, image admission, and the single
spending ledger. No model call, credential read, network inference, GPU operation,
push, or held-out inspection was performed by this worktree.

`bench.decision_context_prompts.assembly_request(evidence, model,
representation="both", reverse_candidates=False)` returns the alpha Decisions
body with singleton `questions.q0`. `parse_assembly(result)` validates all option
probabilities and declared argmax. It retains original scores, normalized scores,
and rounding delta; none is a calibrated probability of correctness. The body
also accepts a list of up to sixteen independent evidence objects, validated by
`parse_assembly_response(result, count)`.

The compatible evidence comes from
`bench.decision_context_cases.evidence_modes(case, mode)`. Its target words,
assemblies, native ruling/fills, prior-row drawings and surrounding source text
survive an explicit allowlist. Gold, family, fixture IDs, PDF paths, split and
unknown metadata are omitted. Numeric word IDs become snapshot-local `wN`
aliases. Every candidate must own every target word once or preserve it in an
unassigned inventory. Complete record source references and ordered header paths
are retained. Text never comes from a model.

The three representations differ only in prior-row presentation:

- `raw`: preceding physical rows, retaining literal text and geometry.
- `summary`: prior-row count, geometry opportunities, aligned close pairs,
  median and most recent row leading, most recent horizontal start change and
  observed ellipsis count.
- `both`: both channels together.

The summary uses at most eight preceding rows. Prior words below the target's
start are excluded before grouping; explicit physical-row inputs are sliced
strictly before `focus_row_index`. No candidate labels, previous predictions,
true wrap labels or future rows enter the summary. Aligned close pairs are
geometry proxies, explicitly marked as unestablished wrap events. A start or
leading change remains visible so a long historical pattern cannot silently
overrule current boundaries. Ellipsis is an observed flag, not a wrap instruction.
The prompt tells the selector that present ruling, color and boundaries can
outweigh counts. No causal or calibration claim follows from these features.

Candidate reversal changes dictionary presentation order only; semantic A/B
labels and assemblies remain identical. The parser therefore leaves labels
unchanged. Evaluate paired outcome flips and per-family exact records, together
with raw score changes; no gains are asserted before live DEV results.

A separate `assembly_request(..., diagnostics=True)` emits a five-option Choice:
context truncated, candidates incomplete, native content absent, truly ambiguous,
or sufficient. These are alternative diagnoses, not assembly acceptance gates.
An omitted native drawing is not proof of absent native text; truly ambiguous
requires complete evidence. The parser uses
`parse_assembly_response(result, 1, diagnostics=True)`. Unverified gateway enum
syntax is deliberately not used. Invalid enum-shaped responses fail closed.
Candidate completeness is a corpus/assembly audit as well as a diagnosis: the
selector cannot establish correctness of an alternative absent from its menu.

A 32,000-byte request cap rejects excessive input instead of silently truncating
evidence. The root image adapter must separately preflight the final image-bearing
body. Images are not generated or transmitted by this module.

Validation: 26 CPU-only Python tests pass, Ruff passes, and Mypy passes for the
owned module and tests. Tests cover metadata exclusion, ownership conservation,
representation equivalence, preceding-only history, regime change, candidate
order, malformed distributions/choice types, strict diagnostic options, provider
rounding, and payload refusal. These authored DEV regions are mechanism probes,
not independent producer samples or unseen validation.

## Worktree log

- Initial revision: prompt builder and parser ready for root's centralized DEV
  run. No live measurements yet; observed failures and tuning followup will be
  appended after the root returns retained results.
