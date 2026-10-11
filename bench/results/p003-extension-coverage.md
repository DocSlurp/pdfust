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

This is a **posthoc DEV result** obtained after diagnosing the original eight borderless failures. Exact row/column/span and literal placement improved here; this is not an all-words-collapse conservation result and does not change default library extraction behavior.

## Frozen-policy fresh-seed transfer

After policy/code commit `b384ed8`, the experiment declaration was frozen before building a new 64-page corpus with seed `p003-headerband-frozen-confirmation-values-20261011-v1`. No policy or code selection changed after those sources were generated. Fresh source dataset identity is `16d58b816cf6bf175293040377de1278586ce5acf0800e27202afa17f6548eec`. All 320 raw source artifacts and 64 derived menus were authenticated before fresh target interpretation; target SHA-256 is `49835607f3f5855dd2c0cce215b48d12cf272c45f1135156bd9e157281dc5e2f`.

| Fresh 64-page transfer | Native baseline | Frozen geometry repair |
| --- | ---: | ---: |
| Exact pages, all intended | 56 / 64 | 64 / 64 |
| Exact literal/spanned cells | 2,553 / 2,930 | 2,930 / 2,930 |
| v2 full content recall | 87.15% | 100% |
| False-positive tables | 0 | 0 |

All eight fresh borderless pages improved; the other 56 native/negative pages retained their source output. Full wrap recall remains unknown because eight merged pairs are unsupported. Supported-only wrap recall is 100%, a narrower diagnostic. This is **same-generator seed transfer**, not real-world generalization or independent structural adjudication.

Complete actual source PDF/renders and before/after literal Markdown/HTML outputs are retained in `extension64-headerband-output-review-v1/gallery.html`, with all eight changed pages expanded. The gallery derives output exclusively from source IDs and freezes hashes of every complete output. Evaluation is in `extension64-headerband-fresh-evaluation-v1.json`; the pre-generation plan, fresh sources, derived menus and preparation receipts are separate sibling artifacts.

Fresh preparation took 11.97 s wall / 7.27 s CPU; scoring took 24.88 s wall / 20.57 s CPU. Each unsampled single-parent lifetime peak RSS was 446,212 KiB including imports. CPU/BLAS/OMP settings remained one thread, with no new hosted requests, remote compute or GPU use.

## Existing natural16 DEV breadth limit

The explicitly authorized natural16 source inventory was processed with the unchanged header-band policy, source outputs frozen, and only then its already-DEV targets loaded. The audit honors manifest `page_number` (including a nonzero-page test), authenticates all original PDF hashes and keeps the full 16-page denominator. Source freeze is `c28597dde03d87fcb736e9cc89679c38d836a2bb8e1a60a4a2ec42c1ec595006`; target SHA-256 is `3dd46b62b4726f482f8ad5b9bf4c34e45f15efe5ad3d02ab7378fb9ec05de5b0`.

All 16 natural pages have zero extractable word IDs. Native/text/header-band arms therefore remain `not_applicable_no_source_text`, including four negative pages; they are neither omitted nor credited as model success. All three arms recover zero of 53 expected tables and zero of 2,333 reference cells. Strict exact pages, v2 recall and wrap recall are zero across the intended set. This is a concrete source-vocabulary applicability failure, not evidence of bad or good column placement. No OCR was run in this native-source audit.

Natural source preparation took 1.49 s wall / 0.75 s CPU and scoring 0.037 s wall / 0.037 s CPU, with the same unsampled 446,212 KiB lifetime RSS measurement. Frozen source outputs and evaluation are retained in `extension-headerband-natural16-v1/`. Reusing authenticated historical OCR source snapshots is a separately authorized next experiment; any historical OCR resources and cost must remain separate provenance rather than be reported as zero.

## Independent completed model screen observations

Complete screen reports 04/05/06 were independently scored against the same v3 source/target freeze, retaining eight intended pages each. The native baseline has seven exact pages. Screen 04 selects all eight but retains only five exact pages (two regressions); screen 05 selects all eight with six exact pages (one regression); screen 06 abstains five times and selects three, earning one exact model-selected page while composed baseline retention gives six exact pages (one regression). No improvement is observed in these screens. Complete per-run scoring receipts are retained under `extension64-screen-offline-v1/`; inherited reported charges/resources were preserved without fabricated totals.
