# P003 boundary-repair opportunity ceiling

The current row-boundary language has **zero attainable strict-cell or
complete-table gain** on the frozen 16-page DEV baseline under fixed baseline
table matching. More admission prompts cannot unlock a repair absent from its
candidate language. This is a posthoc oracle diagnostic, not model quality, a
global extraction ceiling, or validation of an alternative repair mechanism.

The independently authenticated baseline is
`pipeline-p003/screen-ordinal-ocr300-512-r0`, using the explicit root-trusted
`pipeline-p003/trusted-code/b773d57.json`. Every region's complete legal source-only
group graph was generated and persisted before reading references from the
explicitly authorized `pipeline-p002/screens/natural16` DEV corpus. No heldout
paths were read or enumerated. Artifacts, complete source graphs, replay script
and hashes are retained under ignored `pipeline-p003/boundary-ceiling-v1/` in both
worktree and main workspace. Diagnostic SHA256:
`c183d6778ddb32b92fdfca8e14309286d64d24a4c09991f904fc95d0c6664099`.

| Inventory or outcome | Count |
| --- | ---: |
| Intended / operational pages | 16 / 16 |
| Existing tables / references | 16 / 53 |
| Boundaries / geometry-eligible joins | 80 / 69 |
| Editable tables / protected native or merged tables | 13 / 3 |
| Editable fixed-matched / unmatched tables | 12 / 1 |
| Complete legal contiguous row groups, length 1–3 | 216 |
| Editable matched tables whose row count is already correct | 11 / 12 |
| Editable matched column-count mismatches | 1 |
| Editable matched strict anchors, baseline / oracle | 260 / 260 |
| Whole-page strict cells, baseline / replayed oracle | 384 / 384 of 2,333 |
| Complete tables, baseline / attainable ceiling | 3 / 3 of 53 |
| Missing / extra tables, baseline and oracle | 38 / 1 |

The source-only phase uses the existing `build` policy: geometry-admitted joins,
unchanged source ownership and column assignment, at most three physical rows
per logical row, at least two output rows, and no edits to protected tables.
`best_partition` then maximizes the established normalized span-aware strict
anchor score with exact dynamic programming over physical position and logical
row index. Each permitted group rebuilds literal cell text using the existing
`_table`; unchanged original tables remain explicit alternatives. This searches
all legal partitions without enumerating their Cartesian product. The oracle
scores are exact within this language and fixed pairing. The baseline pairing
uses the established scorer; its topology tie-break can change under other
edits, so this is not a global assignment oracle.

For every editable matched table, no partition improves its anchor score.
Complete-table feasibility is separately checked at the reference's exact row
and column count, with identical unit-span anchors and text; only the same
three already complete editable tables are attainable. The selected optimum
therefore retains all original boundaries. It replays through the existing
`boundary.apply`, whole-page composition and scorer, reproducing the entire
baseline score inventory. Native/merged protected tables contribute the other
124 strict cells and remain unchanged.

Of 322 reference anchors in editable matched tables, **59 cannot equal any legal
source group in their fixed column/span**, even if row placement were ignored.
These are failures of the current edit language, rather than evidence for a
specific OCR or semantic cause. The remaining three strict-cell deficits have
literal text available somewhere in a legal same-column group but cannot be
made correct simultaneously through admissible ordered partitions. The one
matched dimension mismatch has seven observed rows and three columns versus
one reference row and two columns: both the minimum-two-row constraint and
fixed columns exclude its target shape. The 38 missing tables cannot be added
by this language, and its unmatched extra table cannot be removed.

The 15 completed boundary arms yielding at most the baseline's 384 strict cells
are consistent with this opportunity ceiling. Prioritize proposal coverage,
source fidelity, column/cell placement and richer topology candidates before
additional row-join prompt sweeps on this exact baseline. A future expanded
language needs its own source-only candidate freeze and independent opportunity
audit; this diagnosis does not justify relaxing existing conservation checks.

Three pure CPU tests passed, including exhaustive small-partition agreement,
unavailable-edge preservation, maximum group length and minimum logical rows.
Ruff and strict mypy passed. The complete offline diagnostic took 1.698 wall /
1.679 CPU seconds; Linux getrusage lifetime peak RSS was 539,156 KiB, scoped to
the diagnostic process including corpus validation and retained graph/state
materialization. Root paid workers were concurrently active; this is local
diagnostic overhead, not remote inference throughput. No hosted calls occurred.
