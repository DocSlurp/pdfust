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

The independent candidate ceiling is an offline scoring oracle, never a model proposal or selector. Wrap scores measure ordered character retention and cannot establish semantic row identity, headers, wrapping or schema correctness. Unsupported comparisons and every failed page stay in the denominator.

The complete 64-page audit is frozen at `pdf-master-artifacts/decisions/p003/extension64-score-v1/coverage.json`. Native v2 full character recall is 88.09%. The strict oracle reaches 97.41% v2 recall while retaining its 56 exact pages. A separately optimized v2 oracle reaches 99.37% v2 recall but only 54 exact pages and 2,842 strict cells. Thus the secondary metric improves while exact output degrades.

Full wrap recall is **unknown** for both those oracles: eight merged-header pairs are unsupported and four/eight unequal-column pairs are unsupported. Supported-only wrap recall is 96.63%/99.03%; those figures are not full scores. Maximizing only fully supported wrap comparisons instead selects empty output on unsupported merged pages and reaches 76.10% full wrap recall with only 48 exact pages. This exposes a metric-selection failure, not a useful output repair.

Full candidate scoring took 500.38 s wall time and 249.26 s process CPU time. Unsampled `getrusage(RUSAGE_SELF)` lifetime peak RSS was 446,212 KiB including imports. One CPU process ran with BLAS/OMP thread counts set to one. No GPU, remote inference or paid requests were used.

## Separately frozen posthoc DEV header-band proposal

Source-only evidence identifies three coverage defects: rolling tracks omit the left-aligned sparse header when the body is right aligned; close amount/description words merge into one fragment; and text detection splits grids at blank/noisy rows. A new module derives ordered column starts from a sparse source band and assigns individual source word IDs across a sustained physical-row run. It uses no literal keywords, authored cell coordinates or family labels. It preserves any established source-native baseline.

The new policy was frozen at SHA-256 `108f2de4790bac228ea3c00e951e80ac7ce3ec09432c1242eefd68b63e1d4a22` before evaluation, with all 64 families admitted. `extension64-headerband-v1/frozen.json` and its menus are separate artifacts; v3 menus and paid requests remain untouched. Its deterministic source-only output reaches 64/64 exact pages, 3,201/3,201 strict cells, 64/64 complete tables, zero false-positive tables, zero text edit distance and v2 precision/recall 100%. Full wrap scoring remains unknown because eight merged pairs are unsupported.

This is a **posthoc DEV result** obtained after diagnosing the original eight borderless failures. It requires a separately seeded source corpus built only after the policy/code configuration freeze before claiming generalization. Exact row/column/span and literal placement improved here; this is not an all-words-collapse conservation result and does not change default library extraction behavior.
