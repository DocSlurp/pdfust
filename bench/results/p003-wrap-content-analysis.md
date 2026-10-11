# Wrap-aware content recovery without changing strict scores

The user correctly identified a formatting penalty in the R002 comparison image. A reference containing one wrapped description and one amount was compared with an output placing the continuation on a second row with a blank amount cell. Every source string was retained, but the old row-sensitive alignment gave 50% precision and recall. Extra entirely blank rows could also prevent the old content-complete flag despite 100% character precision/recall.

The new `p003-wrap-content-v1` diagnostic gives that example 100% content precision/recall while preserving the original strict mismatch, row counts, and unfinished-session status. It measures recoverability under a bounded formatting transformation, not whether the reference and output express identical logical records. Original v2 metrics, references, model outputs and charges remain unchanged. This is a retrospective scoring revision prompted by user feedback, not blinded model improvement.

![Actual source and unchanged output with content and structure shown separately](pdf-master-artifacts/pipeline-p003/progress-reports/continuation-oplog-comparison-v3.png)

## Rules and limits

Entirely blank rows and columns contribute no content penalty; their original coordinates and all blank cells remain in the witness. The metric permits one row to match two or three adjacent nonblank rows, in either direction. A join requires exact normalized text in every corresponding column and at least one matching column containing only one nonempty anchor across the block. Blank spacer rows may be crossed and are explicitly recorded. Column text stays separate; no string is copied or discarded.

Normal comparison uses ordered per-column character edits. NFC and whitespace-run normalization preserve case, punctuation and numeric/date boundaries. Canonical orientation makes swapping inputs exchange precision/recall and missing/extra counts without changing the match. Duplicate fragments, lost values, swapped amounts and reordered records remain penalized. Multi-to-multi row pooling, joins beyond three nonblank rows, anchorless joins and unequal nonblank column counts are outside this version. Unsupported comparisons remain unknown, never zero or success. The existing v2 adjacent-column diagnostic remains available for the accepted rank/name split; this companion does not replace it.

## Every audited scope

The input freezes 166 matched table/body comparisons across 13 overlapping scopes: 18 known R002 bodies, 32 A001 candidate pairs and 116 A002 model/composed/native pairs. These are repeated authored examples, not 166 independent documents. Both R002 author-unresolved cases remain in their ten-session intended denominators but have no unique content target. All original unmatched-table penalties are retained.

| Scope | Intended pages/regions | Prior content-recovered pairs | Wrap-recovered pairs | Wrap content P / R | Unsupported pairs |
|---|---:|---:|---:|---:|---:|
| oplog/openai/gpt-6-luna-decisions | 10 | 5 | 9 | 100.00% / 100.00% | 0 |
| oplog/perplexity/pplx-decider-v1.1-27b | 10 | 6 | 9 | 100.00% / 100.00% | 0 |
| candidate/physical | 28 | 10 | 16 | 34.96% / 100.00% | 0 |
| candidate/rolling | 28 | 16 | 16 | 34.96% / 100.00% | 0 |
| admission/pplx-text-model | 24 | 12 | 12 | 23.83% / 100.00% | 0 |
| admission/pplx-text-composed | 28 | 16 | 16 | 34.96% / 100.00% | 0 |
| admission/pplx-image512-model | 24 | 12 | 12 | 37.53% / 100.00% | 0 |
| admission/pplx-image512-composed | 28 | 16 | 16 | 50.79% / 100.00% | 0 |
| admission/luna-text-model | 24 | 7 | 12 | 34.51% / 100.00% | 0 |
| admission/luna-text-composed | 28 | 11 | 16 | 47.52% / 100.00% | 0 |
| admission/luna-image512-model | 24 | 12 | 12 | 100.00% / 100.00% | 0 |
| admission/luna-image512-composed | 28 | 16 | 16 | 100.00% / 100.00% | 0 |
| admission/native-fixed_native | 4 | 4 | 4 | 100.00% / 100.00% | 0 |

All 166 matched pairs recover their literal content under this bounded diagnostic; 23 gain complete-content recovery relative to v2. There are 55 accepted wrap groups across repeated views. This reflects the source-owned candidate language: models selected or rearranged existing strings rather than transcribing unrestricted pages. It does not establish general extraction quality. False prose tables remain material: model-only PPLX text precision is 23.83%, PPLX image512 is 37.53%, and Luna text is 34.51%. Luna image512 preserves its original 12/12 exact positive tables and zero of twelve prose false positives. Its authored cohort remains a narrow development result.

Physical candidates now recover the same content as rolling candidates, but rolling still has the stronger exact row structure. The original physical/rolling strict complete counts remain six/twelve out of sixteen expected tables; four merged controls lose span topology in both candidate alternatives. Native A002 controls preserve those spans and remain separately attributed.

For R002, Luna has nine wrap-recovered bodies and nine finished recovered sessions out of ten intended; PPLX has nine recovered bodies but only one finished recovered session. Original strict body counts remain five and six. Content, structure and completion are independent outputs; the new diagnostic does not mark an abstention as a successful completed session.

## Rates, units and resources

No new model calls or host charges occurred. Original conditional model rates and all reported/estimated charges remain in the [R002 report](p003-oplog-content-analysis.md) and [A002 comparison](p003-rolling-admission-dual-score.md). Rescoring does not change pages per minute or pages per dollar and cannot establish realized API savings.

Counts use normalized Unicode characters plus declared wrap-join spaces in matched pairs. Unmatched table penalties use normalized anchor literal characters only, as in the existing v2 cohort policy. The audit separately exports introduced separator units; blank padding adds zero. All nonzero residuals in this retained input are extra-table penalties, and they remain exactly unchanged.

The scoring interval took 1.082412 seconds wall, 0.656555 process CPU and 57,204,736 bytes peak sampled RSS. Measurement: process_time and psutil RSS every 100 ms, one CPU-only process with OMP/OpenBLAS/MKL set to one. Imports, initial artifact loading/authentication and final JSON serialization are outside this interval; preparation was not resource-measured. No subprocess or GPU ran during scoring. These short sampled intervals do not establish lifetime memory peaks or inference throughput.

## Verification and reproduction

All reconstructed reference/prediction matrices reproduce the old v2 content counts before new scoring. Inputs come only from already reviewed retained score witnesses; this audit does not reopen original target files. Strict and old-content fields remain preserved. Independent review verifies all 166 pairs, all 13 aggregate scopes, 55 exact anchored wraps and 10,842 character operations, including complete ordered literal/coordinate/character-index consumption and unchanged negative-page penalties. No audited pair crosses an empty row; that policy is covered by separate adversarial tests.

Validation: 80 targeted tests pass across the new scorer, independent adversarial cases, wrapper, existing alignment, span adapter and original scoring audit. Whole-workspace Ruff passes; explicitly scoped mypy passes five new source/test files with imported dependencies silenced. No fresh full-suite or whole-benchmark typing claim is made.

Frozen inputs: `pipeline-p003/continuation-wrap166-inputs-v1.json`, SHA256 `c882849b7248a43ec85805329d121bd91a80f3b39b2108ce4ea75c01c61b18d8`. Official result: `continuation-wrap166-evaluation-v1.json`, SHA256 `6d97882abe258c2d81841a5dfbb664a327e589e3a3328bbba111f48d08707396`. Independent review: `continuation-wrap166-independent-review-v1.json`, SHA256 `3f55151cab319673ba309bcfc9d6ee34499f92821880f1104b7ed6524c4fb88e`. Raw images, comparison literals and receipts stay ignored locally.

Use `python -m bench.p003_wrap_audit prepare --input <pipeline-p003> --output <fresh-input.json>`, then `python -m bench.p003_wrap_audit score --input <frozen-input.json> --sha256 <approved-input-sha256> --output <fresh-result.json>`. The declared source reports are explicitly pinned; changed artifacts fail closed. The scorer is experimental benchmark code and does not modify the library extraction pipeline.
