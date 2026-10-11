# P003 strict, schema-equivalence and partial-content audit

All 26 explicitly pinned, previously verified complete-pipeline runs were rescored offline. Original strict per-page scores reproduce exactly. No new API call, model input, reference rewrite or inference tuning is involved. All 1,160 matched table/run pairs are supported by the bounded span-aware content adapter; missing and extra tables remain in the totals. These overlapping datasets and repeated runs are not independent samples.

The conservative schema companion adds 32 accepted table/run comparisons across six distinct source tables. Only one distinct case changes column count: the source-reviewed newspaper rank/name split, accepted as either three or four columns. The other five cases retain the same columns and ordered lexical tokens while varying spacing around symbols, units or scripts. Automated equivalence is a review aid; it does not prove every physical or semantic interpretation.

## Scoring contract

- **Strict:** unchanged cell positions, text and span comparisons, with original complete-table counts and errors.
- **Strict or equivalent:** strict complete tables plus a consistent adjacent-column partition under a first-row header proxy, preserving ordered letter/digit/punctuation tokens in every row. Named-header collapse, arbitrary permutations and concatenating distinct digit tokens are rejected. Merged schemas remain ineligible for this equivalence rule.
- **Content precision/recall:** bounded monotone row alignment and one shared column path, with Levenshtein matches/substitutions/missing/extra text. Prefixes and suffixes both receive credit. Counts use normalized Unicode characters **including declared synthetic join spaces**; they are alignment-unit metrics, not literal-character recovery or business correctness. Missing/extra whole tables contribute their normalized literal units. Unsupported coverage is reported separately; this run has none.
- **Merged cells:** original span matrices validate before projection. Each anchor text occurs once in its top-left row; covered slots become empty placeholders. Span topology stays separate. A wrong span or extra blank column can retain content without earning schema correctness.
- **Scope:** exact original table matches are reused rather than selecting more favorable matches. Diagnostic-only pages have no invented quality targets; error pages contribute no predicted tables. Empty/duplicated content and row/column gaps retain explicit witnesses.

## All retained runs

The complete-table denominator is the reference-table count. Content P/R includes missing/extra tables in the scored cohort. Rates below are the original operational usable pages/minute and pages/API USD, **not** offline rescoring speed; API costs exclude local compute. Full276 has 220 scored and 56 diagnostic pages. The same source pages overlap between cohorts; do not pool rows into a model leaderboard. Unknown rates remain unmeasured.

| Run | Strict cells | Strict complete | Strict or equivalent | Reference tables | Content P % | Content R % | Pages/min | Pages/API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| acquisition-luna-yolo640-crop1024-r0-c3 | 290 | 3 | 4 | 53 | 88.85 | 20.21 | 3.37 | 1,162.63 |
| acquisition-luna-yolo1024-crop1024-r0-c3 | 807 | 3 | 4 | 53 | 81.56 | 51.54 | 2.52 | 867.29 |
| acquisition-luna-yolo1280-crop1024-r0-c3 | 290 | 4 | 5 | 53 | 93.54 | 19.92 | 1.64 | 562.96 |
| acquisition-haiku-matrix-yolo640-crop1024-r0-c3 | 373 | 2 | 3 | 53 | 88.40 | 24.15 | 6.26 | 1,554.78 |
| acquisition-haiku-matrix-yolo1024-crop1024-r0-c3 | 295 | 3 | 4 | 53 | 86.35 | 24.48 | 4.90 | 1,408.58 |
| acquisition-haiku-matrix-yolo1280-crop1024-r0-c3 | 295 | 2 | 3 | 53 | 94.26 | 20.03 | 2.56 | 574.62 |
| acquisition-sonnet-yolo640-crop1024-r0-c3 | 292 | 3 | 4 | 53 | 94.57 | 21.56 | 5.29 | 66.77 |
| acquisition-sonnet-yolo1024-crop1024-r0-c3 | 362 | 3 | 5 | 53 | 86.61 | 27.65 | 4.31 | 56.43 |
| acquisition-sonnet-yolo1280-crop1024-r0-c3 | 291 | 3 | 4 | 53 | 93.87 | 19.97 | 3.50 | 59.65 |
| acquisition-gemma31-yolo640-crop1024-r0-c3 | 262 | 3 | 4 | 53 | 86.99 | 16.04 | 0.83 | 1,508.48 |
| acquisition-gemma31-yolo1280-crop1024-r0-c3 | 269 | 3 | 4 | 53 | 93.03 | 16.51 | 2.31 | 4,156.20 |
| acquisition-ministral14-yolo640-crop1024-r0-c3 | 207 | 2 | 3 | 53 | 87.66 | 16.22 | 4.77 | 3,553.66 |
| acquisition-ministral14-yolo1280-crop1024-r0-c3 | 574 | 2 | 3 | 53 | 80.54 | 40.52 | 2.79 | 2,207.18 |
| natural64-ordinal-ocr300-512-r0-c3 | 1,309 | 11 | 12 | 93 | 90.83 | 43.35 | 2.69 | 1,013.32 |
| natural64-crops-luna-1024-r0-c3 | 1,348 | 12 | 14 | 93 | 91.95 | 41.91 | 5.54 | 1,985.15 |
| natural64-crops-sonnet-1024-legacy-r0-c6 | 1,839 | 14 | 17 | 93 | 89.38 | 63.79 | 3.20 | 140.43 |
| natural64-ordinal-ocredge2048-512-r0-c6 | 1,125 | 10 | 12 | 93 | 90.00 | 36.26 | 2.35 | 1,051.69 |
| natural64-crops-haiku-1024-matrix_strict-r0-c6 | 1,333 | 12 | 14 | 93 | 93.68 | 37.33 | 3.65 | 2,229.64 |
| natural64-ordinal-ocredge3072-512-r0-c6 | 1,204 | 12 | 13 | 93 | 91.19 | 37.70 | 2.57 | 1,009.50 |
| natural64-crops-opus-1024-legacy-r0-c6 | 1,617 | 15 | 16 | 93 | 88.82 | 58.81 | 6.40 | 72.36 |
| confirmation48-luna-1024-r0-c3 | 2,467 | 25 | 25 | 66 | 98.14 | 71.60 | 5.01 | 1,605.26 |
| confirmation48-sonnet-1024-r0-c3 | 1,891 | 27 | 29 | 66 | 99.25 | 53.90 | 6.36 | 89.87 |
| confirmation48-haiku-matrix-1024-r0-c3 | 2,664 | 27 | 27 | 66 | 98.04 | 86.99 | 6.44 | 1,337.74 |
| confirmation48-ordinal-ocr300-512-r0-c3 | 2,080 | 23 | 24 | 66 | 90.39 | 51.23 | 2.70 | 684.29 |
| full276-ordinal-ocr300-512-r0-c6 | 6,232 | 165 | 166 | 249 | 77.69 | 70.83 | 5.33 | unmeasured |
| full276-crops-luna-1024-r0-c6 | 6,902 | 166 | 168 | 249 | 82.58 | 81.97 | 4.86 | unmeasured |

## Reference disagreements found

| Source page / table | Table/run additions | Difference | Review status |
|---|---:|---|---|
| p6ef5d3c5c2edb1c109c4 / T1 | 22 | Percentage spacing, such as `10%` versus `10 %` | Ordered-token equivalent; original academic source previously inspected |
| p1bfa52a41a5e15015698 / T0 | 1 | Rank/name split into an unnamed fourth column | Source inspected; user explicitly accepts both schemas; all 21 rows preserved |
| p3f48fe087a3e6a59b8e5 / T0 | 5 | Spacing around plus/minus uncertainty notation | Source reviewed; only literal spaces differ, numerical/body tokens preserved |
| pfac04ae9e9cf9e0808a7 / T0 | 1 | Spacing between CJK text, digits and percentage punctuation | Source reviewed; only literal spaces differ, numerical/body tokens preserved |
| p0667c835fff3253fac3a / T0 | 1 | Spacing around plus/slash/minus percentage header | Source reviewed; only literal spaces differ, numerical/body tokens preserved |
| p0667c835fff3253fac3a / T1 | 2 | Spacing between values, currency units and CJK text | Source reviewed; only literal spaces differ, numerical/body tokens preserved |

The four additional source audits are retained in the ignored `visual-review-v1/schema-source-5a38ddcd20c1584118cf/four-case-contact-sheet.png`, with actual full-page images, extracted matrices and character witnesses. The separate timestamped source-review receipt records completed inspection without mutating generation-time metadata.

The source-reviewed random40 irregular form is a separate ambiguity candidate outside these 26 runs: its eight label/value pairs are faithfully emitted as a two-column table, but the authored reference declares zero tables. Sonnet640 and Haiku640 emit identical matrices. Each original false-positive count remains one; no automatic correctness score or reference relabeling is added. See [visual review](../P003_VISUAL_REVIEW.md) and the [portable handoff](../SCORING_HANDOFF.md).

## Findings and limits

Fresh48 Haiku matrix has 27 strict complete tables versus Sonnet standard 27; the schema companion gives Sonnet 29. Their content P/R is 98.04%/86.99% versus 99.25%/53.90%. This reveals different coverage despite similar complete-table counts. It is one frozen confirmation per configuration, with different output representations, not a general model ranking. Natural64 Sonnet reaches 17 strict-or-equivalent tables versus Opus 16, while strict counts are 14 versus 15. This small reversal is metric-sensitive and does not prove overall superiority.

Full276 Luna retains 81.97% alignment-unit recall and 82.58% precision versus ordinal 70.83%/77.69%, while complete tables change only from 166 to 168 and 165 to 166 under schema equivalence. Most failures remain localization, omitted tables, invalid outputs or real content/structure errors; tolerance does not turn those into successes.

Normalization remains deliberately limited. Dot leaders, LaTeX versus Unicode math, inferred labels, vertical-span semantics and source-specific header meanings need separate evidence-aware treatment. The first-row header proxy is not a semantic header detector. No cell text is borrowed across rows or tables, and perfect content alone cannot certify a schema.

## Reproduction and resources

Run `python -m bench.p003_scoring_audit --plan <pinned-plan> --output <fresh-directory>` against explicitly authorized artifacts only. The initial v1 audit declined 203 merged pairs; its immutable report and exact code bytes remain archived. V2 adds the validated anchor-row adapter and supports all 1,160 pairs. Neither original reports nor old audit outputs were overwritten.

V2 measured 141.337 seconds wall and 121.525 CPU seconds across the 26 scoring intervals, with 537.258 MiB maximum sampled process RSS. Measurement: process_time and psutil RSS every 100 ms, one CPU-only Python process, OMP/OpenBLAS/MKL threads limited to one. Source admission/loading outside scoring intervals is excluded; process RSS includes retained corpus/interpreter allocations. No local GPU or remote inference was used.

52 focused schema/content/span/audit tests pass on main. [Independent review](p003-dual-score-review.md) re-admits every pinned run and checks original strict equality plus count conservation for every pair/run. The normalized literal reference basis is constant per cohort; reference alignment units vary by 0–85 for natural16, 0–57 for natural64, zero for fresh48 and 1–17 for full276 because joins insert declared spaces.

- Audit output: ignored `pipeline-p003/scoring-audit26-v2/`.
- Plan SHA256: `333ca142f623837c724276be383ac8006f8ae504ca632ec489c5ff3417bdf743`.
- Root runtime authority SHA256: `da48f3a34238fe11f1a57827628b3208e7e2ce9b28893393a5c226a311e7b956` (Git `191cbb5`, six source files).
- Original inference costs, tokens, failures, raw model outputs and source artifacts remain in their unchanged per-run reports.
