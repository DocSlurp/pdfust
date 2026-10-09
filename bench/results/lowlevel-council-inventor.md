# Lower-level decision mechanisms: inventor proposal

Read AGENTS.md, DECISION_MODELS.md, ROW_DECISIONS.md, OPLOG_DECISIONS.md,
decision-findings.md, decision-alternatives.md, and row-decisions-r001.md.
No held-out directories, credentials, or provider calls accessed. This is a DEV
proposal; implementation evidence below establishes control mechanics only.

## Why move lower

R001 assumes correct fragments, two rows and known columns. R002 split operates
on whole source atoms, so it cannot recover a boundary already swallowed by
word extraction. The initial Jev result improved mostly when literal candidate
spans were exposed; removing geometry left hard singleton answers unchanged.
That is evidence for explicit evidence representation, not proof that geometry
is useless when candidates themselves are damaged. Lower-level evaluation should
measure candidate recovery before ranking quality.

## Mechanisms worth trying

1. **Boundary ledger rather than a new word tokenizer.** Retain an immutable
   geometric sequence of glyph atoms with exact Unicode payload, origin,
   advance, direction, font identity and paint order. Candidate decisions toggle
   only uncertain adjacency edges. Keep current words as one segmentation and
   retain alternative cuts around small gaps, code/unit boundaries and script
   transitions. A ligature with multiple Unicode characters remains one atom;
   cutting it requires a separately labeled within-atom text partition with no
   invented geometry. Rooted source membership, not character counts, provides
   conservation. Asking a model whether `12EA` is one identifier or two fields
   can exploit a header, but cannot recover hidden author semantics absent that
   header. Do not replace a plausible alternative with a confident guess.

2. **Producer nuisance quotient.** Represent source text simultaneously as
   operator-linked atoms and a geometry-normalized glyph view. Render-equivalent
   variants swap Tj/TJ/per-glyph Tm, reorder independent paints, alias font resource
   names, or duplicate identical font objects. A selector should be invariant to
   those nuisance changes. A loss of accuracy under them exposes dependence on
   incidental authoring order. Do not quotient away actual semantic structure:
   marked-content tags, MCIDs and an explicit structure tree can carry information
   even when pixels match. Those need their own semantic channel and stratum.

3. **Reuse as a template hint with negative controls.** Repeated Form XObject
   instances or identical local font/glyph runs can nominate corresponding
   positions in a repeated form. Transfer geometric slot hypotheses, not chosen
   ownership or generated values. Reused headings and logos are negative controls;
   same font object is weak producer evidence, not a cell or record relation.
   Compare shared object, duplicated byte-identical objects, and fresh resources
   on the same raster. If shared IDs help but duplicate-equal content does not,
   test whether the gain is merely a fixture identifier shortcut.

4. **Rolling state with regret rather than commitment.** Keep at most four
   alternative region assemblies and the last three physical bands as explicit
   source-linked context. A new line can revise a previous join/split hypothesis;
   earlier choices do not become facts in the next request. Rank complete feasible
   assemblies, preserve an unresolved branch, and merge branches only when their
   exact ownership/relations coincide. Compare current-only, truthful previous
   bands, shuffled previous bands and conflicting local conventions. A rolling
   state is helpful only if gains survive shuffled-text controls and it does not
   spread one early mistaken row interpretation across the remaining page.

5. **Counterfactual evidence acquisition.** For each unresolved relation, ask
   which admitted observable differs between candidates: an intervening vector
   rule, shared background, font emphasis, or a nearby repeated row. Give the
   selector that source observation or a bounded crop. The local runner can
   compare a tight crop with a slightly expanded crop and a rules-only rendering
   while alternatives stay fixed. A gain from an expanded crop may simply expose
   omitted business context; record it as context acquisition. Crop resolution
   does not resolve genuinely identical pixels with different hidden intentions.

## Minimal implemented packet

Commit b0bd663 in isolated experiment/lowlevel-corpus adds bench/lowlevel_cases.py
and tests/test_lowlevel_cases.py. cases() supplies 24 logical controls crossed
with three encodings: whole substring Tj, character arrays TJ, and per-character
Tm painted in reverse source order. Courier at size 10 has an exactly representable
six-unit advance. All 72 rendered pages are byte-identical within their logical
triples at both 72 and 144 dpi. The original size-12/7.2 attempt failed this
check because accumulated transform rounding changed raster bytes; it was
rejected rather than reported as render-equivalent. CPU-only tests: 3 passed;
Ruff and mypy clean. No model calls or quality measurements yet.

The 12 boundary controls use four short numeric/unit-like strings with gaps
0, 1.2, 3.6 and 7.2, crossed with ordinary Item code, Qty / Unit, and neutral
Entry headers. Four expected joins, four splits and four unresolved cases result.
The 12 row controls use four description pairs, a single amount and ordinary
Description/Amount headers, crossed with a full two-line cell, two ruled rows,
or no grid. Four joins, four splits and four unresolved cases result. Missing
amounts are never invented. Each encoding is crossed with every label.

Case fields id/logical_id/family/encoding/expected/expected_groups are scorer
metadata; pdf_bytes is source; only evidence and independently extracted source
observations enter a request. Evidence has task/question/bbox/choices/target.
Target supplies two display-coordinate boxes and boundary_index, with no gold
text. Every task menu is join/split/unresolved. Root should hash the completed
request before accessing expected metadata, then mutate gold to confirm request
invariance. The boundary is preselected: this cohort does not evaluate detecting
where to ask a boundary question or discovering complete rows/columns.

## Recoverability and confounds

The boundary labels are semantic hypotheses: an Item code header favors one
identifier, while Qty / Unit favors two fields. They do not establish objective
word tokenization. Units may be part of an identifier, a neutral Entry may be a
quantity, and ordinary business context supplies only conventional evidence.
Report these separately from actual grid-defined cell membership. A model can
solve this tiny cohort from header vocabulary alone; matching lexical baseline
performance is a disconfirmer of claimed glyph benefits. Four strings and four
description pairs are correlated templates, never 24 independent producers.

For row cases, glyph-only and word-only states omit the divider, so abstention
can be correct relative to admitted evidence even when the full PDF has a clear
cell boundary. Report full-source reconstruction and admitted-evidence selective
correctness separately. A model receiving vectors/crops has more evidence; its
gain cannot be attributed solely to operating before word extraction. Unruled
one-amount rows admit both wrapped descriptions and missing second-row amounts.
They must remain unresolved; linguistic continuity is not authoritative gold.

## Experiments and metrics

Freeze identical target boxes, candidate actions and source membership across
words, glyphs, glyph+operators, glyph+rules, glyph+rolling state, and glyph+crops
at 256/512px. Compare a literal header baseline and gap/rule baselines before
hosted ranking. Operator IDs/source order must never carry fixture IDs or labels.

Report candidate oracle recall, exact grouped source membership, boundary F1,
cell/row ownership edges, complete-region exactness, retained unresolved inventory,
abstention by recoverability, accepted errors/coverage, invalid choices, and
within-triple decision/distribution flips. Include text conservation and duplicate
ownership checks, but do not call preservation structural accuracy. Report local
preparation wall/CPU time and peak RSS with process scope; separate hosted
latency/cost/tokens and distinguish cached replay from new requests.

Disconfirm lower-level benefit if correct boundaries remain absent, glyphs do
not beat words after matching candidate coverage, gains disappear after removing
header vocabulary shortcuts, source-order variants flip otherwise clear decisions,
rules-only local geometry solves all claimed model wins, or rolling state adds
more propagated errors than recovered rows. A small measured gain remains DEV.

## Rejected directions

Do not treat BT/ET/Tj boundaries as words or rows: producers legally fragment
and interleave paint. Do not use font/object identity as semantic ground truth.
Do not make separate binary decisions for mutually exclusive boundaries and then
normalize contradictions away. Do not use hidden author notes, fixture names,
target cleaned strings, a chosen reconstruction in history, or model confidence
as evidence. Do not introduce a default hosted extraction path or replace the
existing bounded collectors/caches with a retained unbounded glyph lattice.
