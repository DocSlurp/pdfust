# P002 all-page source false-positive audit

This offline audit observes every page in the fixed `full276-yolo-matrix-haiku-512` run against its already verified evaluation. All 48 negatives are retained: 24 authored (12 prose and 12 decorative) and 24 natural. The authoritative outcomes are eight authored false-positive pages (six prose, two decorative) and one natural false-positive page. There are 172 structurally scored positive pages and 56 unscored native diagnostic pages; diagnostics are not relabeled as positives or negatives. No provider calls, prompts, thresholds, inference rules, or confidence estimates were selected from these outcomes.

The source function receives only complete retained words, geometry, and raw detector output. It observes all 276 pages before joining outcome flags, never reference cell text or prediction text. Features are word and character counts, literal word length, source line identities and lengths, sentence-terminal punctuation, numeric-token fraction, median word height, half-word-height vertical center bins, normalized positive horizontal gap variation, vertical-bin gap variation, eight equal page-width occupancy bins, valid/quarantined native geometry, and detector Table box counts, area, aspect ratio and reported confidence. The fixed bin definitions are descriptive encodings, not fitted classifiers. Detector confidence is not calibrated correctness. Full feature vectors and input hashes are retained in ignored `source-negative-taxonomy.json` beside the run.

All negative pages below include correct rejections. “Output” is the authoritative detected-table count; FP marks a false-positive page. Grid counts are valid native grids after the existing quarantine. Table boxes are raw detector proposals. Area is the median proposal area divided by page area. Missing observations are shown as —.

| ID | Family | FP | Output | Words | Line words | Terminal fraction | Row gap CV | X occupancy | Grids | Table boxes | Area |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| p8240945414e8c5a0b390 | authored/decorative | yes | 1 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.565 |
| pdda9ef98649f7da7e3a7 | authored/decorative | no | 0 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.564 |
| p0da20f73a73bc46334a6 | authored/decorative | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.565 |
| p049cf451e512c7e02d54 | authored/decorative | no | 0 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.564 |
| p551488ab988222d2357e | authored/decorative | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.565 |
| pef43d17aa12c78fc1175 | authored/decorative | yes | 1 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.564 |
| p33ba0ed177446d1c60f1 | authored/decorative | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.565 |
| p87eff4b99075ff04c786 | authored/decorative | no | 0 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.564 |
| pb99be52b1c87fb444878 | authored/decorative | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.565 |
| pe7e830ee122716fe82fc | authored/decorative | no | 0 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.564 |
| p1a903da746f6305a463c | authored/decorative | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.565 |
| pae5f9da3cd33030e058f | authored/decorative | no | 0 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.564 |
| pd8caf18f06ffc182c966 | authored/prose | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.218 |
| pdda061a6df07c6cc7697 | authored/prose | yes | 1 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.355 |
| p823a5a1b710f4b2d4518 | authored/prose | yes | 1 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.218 |
| pf403bf2a5fc70490445f | authored/prose | yes | 1 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.355 |
| p276de2f57f3bfa0d338a | authored/prose | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.218 |
| p7b31fb6bc7708d4098e5 | authored/prose | yes | 1 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.354 |
| p8187fa86a7d44e8f3911 | authored/prose | yes | 1 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.218 |
| p04509096bbf7bc63197e | authored/prose | no | 0 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.354 |
| pa7a657d7d5b980cee434 | authored/prose | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.218 |
| p10d88cdd519be61a0150 | authored/prose | yes | 1 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.355 |
| pbbacbc83a7a423352210 | authored/prose | no | 0 | 137 | 10 | 0.007 | 1.274 | 4 | 0 | 1 | 0.218 |
| pa33699400f3790f079be | authored/prose | no | 0 | 202 | 5 | 0.005 | 1.274 | 6 | 0 | 1 | 0.355 |
| pdb465e3996d38f0e266f | omni/no-table | no | 0 | 328 | 4 | 0.037 | 0.520 | 3 | 0 | 0 | — |
| pdb4e1fa3babeca265abb | omni/no-table | yes | 1 | 347 | 15 | 0.063 | 0.664 | 6 | 0 | 1 | 0.039 |
| p27ec5aaca0dd08c90360 | omni/no-table | no | 0 | 9 | 1 | 0.111 | 1.594 | 1.000 | 0 | 1 | 0.854 |
| p472e201da3137e4da042 | omni/no-table | no | 0 | 2 | 1.000 | 0.000 | 0.000 | 1.000 | 0 | 0 | — |
| pc0ab300c43a54344e62f | omni/no-table | no | 0 | 930 | 7 | 0.057 | 0.386 | 5.000 | 0 | 0 | — |
| p659736dbc4293f76468a | omni/no-table | no | 0 | 1 | 1 | 1.000 | — | 1 | 0 | 0 | — |
| pa852de210493b9ba9be4 | omni/no-table | no | 0 | 30 | 1.000 | 0.100 | 0.527 | 1.000 | 0 | 0 | — |
| p5554abe22cd0f0a9f465 | omni/no-table | no | 0 | 986 | 9 | 0.057 | 0.560 | 8 | 0 | 0 | — |
| pf3dd8216a197f362b2a9 | omni/no-table | no | 0 | 611 | 3.000 | 0.002 | 0.512 | 4 | 0 | 0 | — |
| pea5b782e9acd3d9a1f4e | omni/no-table | no | 0 | 117 | 2.500 | 0.111 | 0.412 | 2.500 | 0 | 0 | — |
| p9cc5ebfad2ee46a13b5e | omni/no-table | no | 0 | 166 | 5 | 0.042 | 0.493 | 3 | 0 | 1 | 0.056 |
| p8985d21a28195d80e46c | omni/no-table | no | 0 | 286 | 4 | 0.042 | 0.536 | 2.500 | 0 | 0 | — |
| p196f7345c55faea85413 | omni/no-table | no | 0 | 592 | 10.500 | 0.035 | 0.601 | 3.000 | 0 | 0 | — |
| p226466ef30a9d49d414b | omni/no-table | no | 0 | 439 | 15 | 0.030 | 0.562 | 6.000 | 0 | 0 | — |
| p42049db34e230ce77d75 | omni/no-table | no | 0 | 489 | 5.000 | 0.029 | 1.338 | 2.000 | 0 | 0 | — |
| pec7eeb99bd5a848b520f | omni/no-table | no | 0 | 66 | 3 | 0.061 | 0.814 | 2.000 | 0 | 0 | — |
| p6fd324498831c92245be | omni/no-table | no | 0 | 89 | 1.500 | 0.146 | 0.511 | 1.500 | 0 | 0 | — |
| pb8a78ebe8d0136b50cd4 | omni/no-table | no | 0 | 89 | 3 | 0.146 | 0.873 | 3 | 0 | 1 | 0.267 |
| p59fb5ba173c662716ee2 | omni/no-table | no | 0 | 839 | 9.000 | 0.058 | 0.538 | 4 | 0 | 0 | — |
| p31c72b67a760bf47128e | omni/no-table | no | 0 | 5 | 1 | 0.000 | 0.190 | 1 | 0 | 0 | — |
| pe00342d521bf1aeb0345 | omni/no-table | no | 0 | 1503 | 7 | 0.051 | 0.854 | 7.000 | 0 | 0 | — |
| p75ca9981dd6bf8663523 | omni/no-table | no | 0 | 138 | 3 | 0.000 | 0.797 | 2 | 0 | 0 | — |
| pddb2472516559060b9c3 | omni/no-table | no | 0 | 390 | 11.500 | 0.064 | 0.349 | 3 | 0 | 1 | 0.023 |
| pa885669a5ffc8507b01c | omni/no-table | no | 0 | 6 | 1.000 | 0.000 | 0.774 | 1.000 | 0 | 0 | — |

The same features on every positive family are shown as page medians. Missing detector area excludes pages without a Table proposal; the complete JSON records each observation count and range.

| Positive family | Pages | Words | Line words | Terminal fraction | Row gap CV | X occupancy | Grids | Table boxes | Area |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| authored/blank | 12 | 30.500 | 1.250 | 0.033 | 1.468 | 4.000 | 1.000 | 1.000 | 0.196 |
| authored/borderless | 12 | 36.000 | 1.750 | 0.028 | 1.468 | 5.000 | 0.000 | 1.000 | 0.140 |
| authored/cropped | 12 | 36.000 | 1.750 | 0.028 | 1.468 | 4.000 | 1.000 | 1.000 | 0.234 |
| authored/dense | 12 | 191.500 | 9.000 | 0.005 | 1.062 | 7.000 | 1.000 | 1.000 | 0.480 |
| authored/merged | 12 | 34.000 | 1.250 | 0.029 | 1.468 | 5.000 | 1.000 | 1.000 | 0.195 |
| authored/mixed | 12 | 65.000 | 1.250 | 0.015 | 0.812 | 5.000 | 1.000 | 2.000 | 0.168 |
| authored/multiple | 12 | 65.000 | 1.250 | 0.015 | 0.812 | 5.000 | 2.000 | 2.000 | 0.196 |
| authored/ocr-carrier | 12 | 36.000 | 1.750 | 0.028 | 1.470 | 5.000 | 0.000 | 1.000 | 0.196 |
| authored/rotated | 12 | 36.000 | 1.750 | 0.028 | 1.468 | 5.000 | 1.000 | 1.000 | 0.196 |
| authored/ruled | 12 | 36.000 | 1.750 | 0.028 | 1.468 | 5.000 | 1.000 | 1.000 | 0.196 |
| authored/wrapped | 12 | 46.000 | 2.000 | 0.022 | 1.659 | 3.000 | 1.000 | 1.000 | 0.283 |
| omni/multiple-table | 16 | 188.500 | 5.500 | 0.044 | 0.547 | 3.250 | 0.000 | 2.000 | 0.122 |
| omni/single-table | 24 | 100.000 | 3.500 | 0.052 | 0.804 | 3.000 | 0.000 | 1.000 | 0.131 |

The authored negative prose and decorative families have identical median source counts (169.5 words), source line lengths (7.5 words), terminal punctuation fraction (0.0061), and row-gap CV (1.274). Their detector median area differs (0.286 versus 0.564), but both produce correct and false-positive outcomes. Geometry and native-grid absence do not establish record semantics: valid borderless and OCR-carrier positive tables also have no native grids.

Positive dense authored tables have median source line length 9 words, longer than the negative-family median; long lines alone would reject real tables. Natural no-table pages and natural single-table pages share median source line length 3.5 words and close punctuation fractions (0.0540 versus 0.0521). Their row-gap distributions also overlap. The one natural false positive has 347 source words, median line length 15 words, one small detector proposal covering 0.0391 of the page, and no native grid. This is an outcome-linked description, not a rule or proposed case-specific exclusion.

A falsifiable next feature set should describe local proposal content rather than whole-page length: whether adjacent columns continue the same sentence across physical baselines; whether each column repeatedly restarts independent lexical/numeric roles; whether aligned row groups have stable column participation after wrapped-cell continuations; and whether ruling intersections enclose the claimed rows rather than merely decorate prose. These are hypotheses to declare before a new matched gate control. Measure precision and missed-table cost together across all negative and positive families, including wrapped, dense, borderless, merged, rotated, and multi-table positives. Use abstention for conflicting evidence rather than interpreting raw detector confidence as correctness. The current observations neither define thresholds nor validate a classifier.

Limitations: source line IDs reflect extraction grouping, including multi-column segmentation; terminal punctuation is not a sentence parser; vertical center bins approximate rows and can split mixed font sizes or merge nearby baselines; page-wide occupancy can mix independent tables and prose. OCR word geometry and literal text errors remain in the evidence. Full natural display viewports can be physically small, so normalized geometry should be preserved. Some detector features are unavailable on failed pages; they are not zero-filled.

Unscored native diagnostic family summaries use the same source features and remain separate in the JSON. The all-page source inventory includes four missing-source failures explicitly rather than omitting them. Two other failed pages retain source features but their failed output prefixes are not counted as successful predictions.

The bounded local audit used one CPU Python process and no subprocesses: 1.377 s wall time, 1.366 s process CPU time, and 405,080 KiB Linux `getrusage(RUSAGE_SELF)` high-water RSS. The scope includes importing the native runner dependencies and inspecting all page sources; no utilization sampling or GPU work occurred. Two focused feature tests passed; Ruff and focused mypy checks passed.
