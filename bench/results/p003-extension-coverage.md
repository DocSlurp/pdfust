# P003 extension64 frozen menu coverage

Offline evaluation of the freshly authored v3 DEV corpus began on 2026-10-11 after its source and menu freeze. Existing corpora and heldout data were not read. Source menus and model requests remain unchanged.

The evaluator authenticates the exact manifest, freeze receipt and source inventory, verifies all 320 inventoried source artifacts and complete candidate ownership, then opens only the newly authored target file. Target SHA-256 is pinned at `f93a9b6dea989a1b89aeb35e38fcc9e73c9f0d47eba4b8a7fd35df0c150a93a9`.

| Strict coverage | Native baseline | Best frozen candidate |
| --- | ---: | ---: |
| Exact pages, all intended | 56 / 64 | 56 / 64 |
| Exact positive pages | 48 / 56 | 48 / 56 |
| Exact negative pages | 8 / 8 | 8 / 8 |
| Exact source-owned cells | 2,807 / 3,201 | 2,968 / 3,201 |

All eight borderless pages remain incomplete under the strict scoring-only oracle. The candidate set can restore 161 strict cells compared with the native-empty baseline but cannot recover a complete borderless page. Paid selection cannot exceed candidate coverage. Ruled/native pages principally measure regression control; the separately labeled missing/doubled/swapped/wrap stress states measure actual repair. Baseline output retention after abstention, transport failure or preparation failure is not model success.

The new helper maps predictions into unchanged `p003_report.strict_scores`, `p003_scoring_audit.dual_scores`, and the wrap diagnostic. `score_run` uses an explicitly declared intended-page inventory or all 64 pages, never a success-filtered result set. Absent outcomes are `not_attempted`. It validates model selections against exact frozen source-owned candidates and compares selected-only results separately from composed output with baseline retention. Strict, v2 and wrap changes and source ownership omissions/duplicates remain separately visible. Unknown charges or resource measurements are preserved rather than converted to zero.

The independent candidate ceiling is an offline scoring oracle, never a model proposal or selector. Wrap scores measure ordered character retention and cannot establish semantic row identity, headers, wrapping or schema correctness. Unsupported comparisons and every failed page stay in the denominator. The complete v2/wrap audit is running separately and will be reconciled in this report after completion.
