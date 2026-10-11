# Selected-only candidate comparison

The bounded adapter `bench.p003_candidate_visual_review` renders two natural16 DEV examples from the independently verified 64-run partial-decision audit. It compares `choice-pplx-512-rgb-r2-c6` with the matched `choice-pplx-512-rgb-blank-r0-c6`, using only the pinned `primary_predictions` list. Retained fallback tables never receive visual or scoring credit. This is candidate selection over historical complete crops, not a complete extraction pipeline.

The ignored batch is `bench/results/pdf-master-artifacts/pipeline-p003/visual-review-v1/candidate-selected-259dbee3549f8feda6ee/`:

- `p6ef5d3c5c2edb1c109c4-T1-matched-control.png`: all eight disturbance rows are retained by RGB selection. Character precision is 0.9819 and recall is 1; percent-spacing representation differences account for the remaining disagreement. The blank control selects no table on this page.
- `p9f92a30432da612d1bcc-T0-matched-control.png`: the CJK labels and all numeric entries are exact under the pinned character metric. The blank control selects no table on this page.
- `<id>-original.png` retains each complete white-background source page. Native source crops, actual selected output, complete alignment witnesses, font/settings hashes and CPU/RSS provenance remain alongside the images.

The examples do not replace cohort denominators. Across all 16 intended pages, RGB has 981 strict exact cells, normalized-character recall 0.6122 and precision 0.9513; blank has two strict exact cells, recall 0.01166 and precision 0.9372. The high blank precision reflects its small retained output and does not imply successful selection.

Group colors use exact retained match/reference/prediction character counts: red at zero, yellow at 0.5 and green at one. Gray denotes groups without character units. Amber borders independently flag changed merge membership. Groups are schematic alignments, not physical source cell boxes, semantic correctness probabilities or inferred scores. Original strict scores and earlier diagnostic batches remain unchanged.

Validation: scoped Ruff and mypy pass; nine relevant candidate/color/alignment tests pass, including a check that a blank control cannot inherit fallback output and that altered primary predictions fail their frozen hash.
