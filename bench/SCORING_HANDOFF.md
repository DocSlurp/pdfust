# Handoff: acceptable PDF table structures are being penalized as errors

We need to audit our reference datasets and table scorers for cases where a
reasonable extraction receives a harsh score because the reference encodes only
one plausible table schema. Preserve the existing strict score and add a
separately versioned tolerant score that measures retained content, row membership,
order, wrapping, and header relationships. This document preserves the original
evaluation request. Strict, schema-equivalence and partial-content scorers are
now implemented; the [26-run audit](results/p003-dual-score-audit.md) and
[random40 review](results/p003-random40-dual-score-review.md) report their results.
The follow-up now independently verifies 32 current pipeline treatments, 64
incremental decisions, 56 historical P001 pipelines, eight conditional row
assemblies and 48 older incremental decisions. These are separate scopes with
repeated documents, not 208 independent complete extraction systems. The
[coverage inventory](results/p003-rescore-coverage.md) records remaining omissions.
Header semantics and span topology still require separate checks; content
precision/recall alone cannot certify them.

## Follow-up: wrapped rows and blank padding

The user identified another harsh penalty in the R002 progress image: the
reference stores `Deferred revenue contract adjustments` and `340` in one row;
the output stores `Deferred revenue` / `340`, followed by
`contract adjustments` / an empty cell. All strings remain, but v2's row-sensitive
alignment reports 50% content precision/recall. Entirely blank extra rows could
also fail its content-recovered flag despite perfect character precision/recall.

![Actual source and output with wrap-aware content, original structure, and session status shown separately](results/pdf-master-artifacts/pipeline-p003/progress-reports/continuation-oplog-comparison-v3.png)

The [new wrap-aware diagnostic](results/p003-wrap-content-analysis.md) gives this
example 100% content credit, retains its original two-versus-one row difference,
and leaves the abstained session unfinished. It permits exact anchored joins of
up to three adjacent nonblank rows, inventories blank padding, and preserves
literal order and column associations. Strict references, old scores and outputs
are unchanged. This is content recoverability under a declared transformation,
not proof that the logical row interpretation is correct.

Independent review covers 166 retained comparisons and unchanged negative-page
penalties. Twenty-three comparisons gain content recovery. The new diagnostic
does not replace the existing adjacent-column metric: unequal nonblank column
counts, multi-to-multi row pooling and longer wraps remain outside its scope.
Original v2 images remain available for provenance; use v3 when explaining this
formatting issue so red alignment groups are not mistaken for literal text loss.

## The actual example

![Actual newspaper table on the left and extracted table on the right. Most cells are red because of strict reference-column mismatches, despite a plausible four-column extraction.](results/pdf-master-artifacts/pipeline-p003/visual-review-v1/df68e524b590fcc84c29/p1bfa52a41a5e15015698/regional-T0.png)

The user explicitly accepts either **three or four columns** for this table.
The reference combines rank and team name under `No.`; the extraction separates
rank and team name, leaving the team header blank. The source does not name the
team column, and its spacing permits either interpretation.

| Interpretation | First data row |
| --- | --- |
| Reference: three columns | `1. Hingham` / `6-0-0` / `2` |
| Extraction: four columns | `1.` / `Hingham` / `6-0-0` / `2` |

The extraction preserves the values and their row associations. A lexical audit
verified all **21 rows, including the header**, using the same prediction-column
partition throughout: `[[0, 1], [2], [3]]`. Joining the first two predicted columns
recovers the three reference columns. This audit preserves ordered word, digit,
and punctuation tokens; it does not simply delete all whitespace.

**Red in this screenshot means strict reference mismatch, not a demonstrated
extraction failure.** The right side is a schematic rendering of actual extracted
cells, not a reconstruction of their PDF coordinates. Display wrapping inside a
cell is also not evidence that the extraction placed its contents in different rows.

## Continuous score overlays

New progress images interpolate **red → yellow → green** at aligned-content
F1 values of 0, 0.5 and 1. Numeric match counts and precision/recall accompany the
colors. Gray means no character units; amber borders separately flag structural
problems. These are measured content matches, not model confidence or semantic
correctness probabilities. Strict scores and original red/green images remain
unchanged.

[Accepted three/four-column case with score groups](results/pdf-master-artifacts/pipeline-p003/visual-review-v1/content-gradient-6fba505b4c10afba3e11/p1bfa52a41a5e15015698-T0-groups.png)
and [a genuine missing-row and wrong-value example](results/pdf-master-artifacts/pipeline-p003/visual-review-v1/content-gradient-6fba505b4c10afba3e11/p1bfa52a41a5e15015698-T8-groups.png)
show the actual source beside extracted output. The latter also has dot-leader
and fraction-encoding disagreements; not every colored mismatch is a wrong
business value. Full original source pixels and alignment witnesses are retained.

## Requested behavior

1. **Keep strict scoring.** Preserve original gold, predictions, exact cell scores,
   full-cohort denominators, and historical reports. Publish tolerant metrics
   alongside them, with a versioned policy and auditable alignment witnesses.
2. **Accept supported schema alternatives.** Allow consistent adjacent splits or
   joins such as rank/name or first/last name when the source permits them. An
   unnamed column is not automatically an invented data column. Evaluate inferred
   header labels separately from source text; distinguish a useful schema label
   from a claim that the label appeared in the document.
3. **Align rows monotonically.** Missing or extra rows should not cause all later
   rows to fail. Preserve row order and penalize omitted, duplicated, or inserted
   content. Do not borrow matching words from another row.
4. **Align cells within rows.** Support bounded adjacent joins/splits and gaps.
   An inserted middle column should receive its own penalty while correct cells
   on both sides retain credit. Do not permit arbitrary permutations or choose
   unrelated column mappings independently for every row.
5. **Measure partial text recovery.** Explore Levenshtein-style sequence alignment
   with explicit matched, substituted, missing, and extra content. Recognize both
   prefixes and suffixes; a prefix-only substring check loses valid trailing text.
   Publish content precision and recall so extra text cannot earn free credit.
6. **Preserve meaningful distinctions.** Normalize line wrapping conservatively.
   Do not turn `1 23` into `12 3`, collapse distinct values, silently erase
   punctuation, or give full credit for wrong-row values. Handle duplicate strings,
   empty cells, merged spans, headers, and numeric/date/currency formats explicitly.
7. **Show the reason for each verdict.** Visuals should distinguish exact matches,
   accepted schema alternatives, partial recovery, omissions, and hallucinations.
   Include source pixels, actual output, and alignment evidence. Never label every
   strict mismatch as a model failure.

## Audit scope and deliverables

Inventory all reference datasets already used in these experiments, including
authorized DEV and already-used frozen confirmation sets. Review cases with low
strict scores but apparently intact content, unnamed columns, split names/ranks,
wrapped cells, missing rows, and shifted columns. Include genuine extraction
failures as controls. Record disagreements and acceptable alternatives with
source-based evidence; do not silently rewrite gold to suit a model output.

Protected unused heldout directories remain excluded: `bench/heldout-silver/` and
`bench/results/pdf-master-artifacts/silver-heldout-v1/`. Confirmation-set auditing
must not feed reference answers into inference prompts or model tuning.

Deliver a reference-issue inventory, a documented strict/tolerant scoring contract,
tests for acceptable alternatives and adversarial near-misses, rescored comparisons
on unchanged outputs, and visual examples of both corrected penalties and real
errors. Report schema equivalence separately from recoverable partial content;
do not collapse all distinctions into one unexplained score.

## Evidence and provenance

- Page ID: `p1bfa52a41a5e15015698`; source table `T0`; matched prediction `T1`.
- Run: `acquisition-sonnet-yolo1024-crop1024-r0-c3`.
- Recorded model: `anthropic/claude-sonnet-5.5`.
- Detector inference edge: 1024; raster edge: 1536; crop edge: 1024.
- Original image is linked above and remains unchanged.
- [Annotated view of the same input/output](results/pdf-master-artifacts/pipeline-p003/visual-review-v1/18ef578699bf7fb67f49/p1bfa52a41a5e15015698/regional-T0.png).
- [Exact column-partition audit](results/pdf-master-artifacts/pipeline-p003/visual-review-v1/18ef578699bf7fb67f49/p1bfa52a41a5e15015698/column-partition-audit.json).

Images and raw evidence are local ignored artifacts. For a portable handoff,
share the accompanying local `scoring-handoff-v1` directory or ZIP, which includes
the original request with relative image links, both images, and the partition
audit. That frozen v1 package predates the completed scoring audits linked above.
The newer `scoring-handoff-v3.zip` includes the gradient examples and current
separate-scope reports, with a file-hash manifest. Earlier packages stay intact.
