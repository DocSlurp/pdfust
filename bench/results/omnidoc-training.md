# Reference-derived TRAINING layout preparation

16 new official references, explicitly TRAINING together with all derivatives. Exact reference IDs are disjoint from DEV16; known numbered-page parents are excluded. Unknown source parents prevent a complete document-disjoint claim. Reference and derivative usage inherits the research-only/noncommercial dataset restrictions.

Geometry SHA256: `054b6a8691e2575995c6c3885e3109cf7bef6858deeb8366620e869153bb0139`. The frozen geometry contains 447 source block correspondences. Recognition text is excluded from synthetic authoring.

Visual review of a formula slide and dense newspaper reference, plus both derivative renders, confirms broad envelope/column/inset correspondence while exposing typography and content limitations. The slide lacks original color bands; newspaper tables use newly authored regular grids instead of original directory internals. These are layout scaffolds, not approved almost-clones.

| Synthetic page | Source genre/layout | Blocks | PDF version | Image placements | Image union area % | Decoded string bytes | Metadata errors |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| training-000 | research_report / 1andmore_column | 20 | 1.4 | 2 | 8.77 | 1303 | 0 |
| training-001 | PPT2PDF / single_column | 11 | 1.4 | 0 | 0.00 | 1488 | 0 |
| training-002 | exam_paper / double_column | 38 | 1.4 | 1 | 3.27 | 5605 | 0 |
| training-003 | newspaper / other_layout | 112 | 1.4 | 4 | 18.59 | 30826 | 0 |
| training-004 | book / single_column | 39 | 1.4 | 0 | 0.00 | 4747 | 0 |
| training-005 | note / single_column | 17 | 1.4 | 0 | 0.00 | 2048 | 0 |
| training-006 | academic_literature / double_column | 26 | 1.4 | 0 | 0.00 | 5717 | 0 |
| training-007 | magazine / three_column | 7 | 1.4 | 0 | 0.00 | 2677 | 0 |
| training-008 | historical_document / other_layout | 41 | 1.4 | 0 | 0.00 | 7667 | 0 |
| training-009 | colorful_textbook / other_layout | 33 | 1.4 | 4 | 1.29 | 4387 | 1 |
| training-010 | book / single_column | 20 | 1.4 | 0 | 0.00 | 3340 | 0 |
| training-011 | academic_literature / other_layout | 13 | 1.4 | 2 | 2.46 | 2183 | 1 |
| training-012 | magazine / other_layout | 26 | 1.4 | 0 | 0.00 | 4769 | 0 |
| training-013 | magazine / other_layout | 17 | 1.4 | 2 | 35.42 | 2945 | 1 |
| training-014 | book / single_column | 22 | 1.4 | 15 | 7.03 | 375 | 1 |
| training-015 | book / single_column | 5 | 1.4 | 1 | 15.83 | 91 | 1 |

Selected v2 preparation: 2.234s wall, 2.238s process CPU, 137.18 MiB current-executable peak RSS. One sequential CPU process; /proc/self/status VmHWM, no periodic sampling. Reference acquisition records CPU/wall separately; acquisition RSS is unmeasured. No inference or GPU.

Three focused tests, Ruff and targeted mypy pass. Complete metadata includes actual image areas, native text geometry, PDF/content/string byte counts and descriptive layout/noise proxies. Five raw-string token scans fail with unterminated-literal parser errors and remain explicitly unknown. No quality score or independent evaluation claim follows.
