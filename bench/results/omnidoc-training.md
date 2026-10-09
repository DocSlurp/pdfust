# Reviewed reference-derived TRAINING layouts

The selected revision is **v3.1**, with all 16 references and every derivative linked as TRAINING. The review inspected all 16 source/derivative pairs, followed by enlarged slide, newspaper, notebook and colorful-textbook comparisons. Mask semantics, typography, script, column density and page decoration are substantially improved; these remain approximate layouts, not approved almost-clones or independent evaluation data.

[Selected registry](../omnidoc-training/synthetic-v3.1-registry.json) retains source IDs, parent uncertainty, hashes, all measured scalar/page metadata, and per-page comparisons. PDF version, file/content/string bytes and fractions, image coverage/counts, text geometry and noise proxies are available per row. Only verbose font-resource and image-placement records remain solely in the full ignored manifest. Reference inputs are images, so original PDF byte/version metadata is unavailable. No missing measurement has been invented.

The fixed generator leaves masks blank, suppresses discarded annotations and duplicate list containers (58 suppressed blocks), measures line/grid profiles without OCR, authors native CJK and vertical Chinese text, and uses font-metric wrapping, page colors, highlights, original tables and procedural vector illustrations. Source prose, photographs and formulas are not copied. A final audit found 15 out-of-page Latin credit words in frozen v3; v3.1 rotates and fits those narrow credits. Both versions remain preserved.

Final v3.1 source extraction contains **5,117 words**, with **zero out-of-page words**, **zero word centers inside true masked regions**, and **zero metadata errors** across all 16 pages. These checks do not establish complete absence of overlap or correct reading order. The metadata scanner fix recognizes legal PDF `>>stream` delimiters; old v2 diagnostics remain unchanged.

All 16 rows are reported below. Tile dark-ink MAE compares 16×16 tile occupancy after resizing each image to 256×256; dark means arithmetic RGB mean below 180. Lower values indicate closer coarse ink distribution only. They do not measure semantics, exact table structure, OCR quality or visual realism.

| Page | v2 tile ink MAE | v3.1 tile ink MAE | Suppressed blocks | PDF bytes | Extracted words | Metadata errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| training-000 | 0.0477 | 0.0441 | 1 | 95765 | 114 | 0 |
| training-001 | 0.1172 | 0.0671 | 0 | 5232 | 90 | 0 |
| training-002 | 0.0357 | 0.0202 | 9 | 179843 | 62 | 0 |
| training-003 | 0.1714 | 0.1127 | 10 | 155929 | 2247 | 0 |
| training-004 | 0.0256 | 0.0153 | 3 | 137886 | 55 | 0 |
| training-005 | 0.2207 | 0.2166 | 1 | 49814 | 26 | 0 |
| training-006 | 0.0511 | 0.0424 | 0 | 31225 | 954 | 0 |
| training-007 | 0.0139 | 0.0028 | 1 | 7142 | 113 | 0 |
| training-008 | 0.0445 | 0.0347 | 0 | 233579 | 41 | 0 |
| training-009 | 0.0401 | 0.0262 | 7 | 166180 | 34 | 0 |
| training-010 | 0.0617 | 0.0058 | 0 | 15231 | 428 | 0 |
| training-011 | 0.0316 | 0.0291 | 2 | 26925 | 575 | 0 |
| training-012 | 0.0551 | 0.0091 | 5 | 10377 | 227 | 0 |
| training-013 | 0.1714 | 0.1480 | 2 | 14060 | 136 | 0 |
| training-014 | 0.0154 | 0.0067 | 15 | 31882 | 8 | 0 |
| training-015 | 0.0341 | 0.0079 | 2 | 1914 | 7 | 0 |

The final manifest uses the inherited diagnostic key `v3` for the current v3.1 rendering; its design version is explicitly `3.1`. All 16 coarse ink errors decrease relative to v2, but major mismatches remain: photographs are vector substitutes; handwriting is typeset; exact fonts, mixed emphasis, scan texture, source formulas and table internals are approximate. Repeated authored sentence templates and clipped prose fragments are still visible. The reference tagged language `other` includes French, while the derivative uses English. Chinese is supported, but typeface and historical typography are approximate. These limits prevent an almost-clone claim.

All references and descendants inherit the source research-only/noncommercial restrictions and are not commercially cleared. Known filename parent groups are linked; UUID and other unknown parents prevent a document-independence guarantee. This is geometry/style-derived training preparation, not a naturally sampled benchmark or a heldout evaluation.

Frozen artifact directory: `bench/results/pdf-master-artifacts/omnidoc-training-v1/synthetic-v3.1/`. Generator commit: `85c8240`; generator, dependencies, font hashes, style profiles and private authored targets were frozen before PDF rendering, extraction and measurement. The final registry-only metadata projection preserves those frozen artifacts. Geometry SHA256: `054b6a8691e2575995c6c3885e3109cf7bef6858deeb8366620e869153bb0139`. Full manifest SHA256: `794496be684779719cf24dffab35c24418a6152dcde0542a84b821f2b26299b1`.

Local inspection: [all 16 source/derivative pairs](pdf-master-artifacts/omnidoc-training-v1/synthetic-v3.1/gallery.html), [first four pairs](pdf-master-artifacts/omnidoc-training-v1/synthetic-v3.1/gallery-pairs-0.png), and the remaining `gallery-pairs-1.png` through `gallery-pairs-3.png` in that directory. These raw previews remain ignored. `geometry-audit.json` retains the per-page source bounds/mask audit.

Preparation used 8.182s wall, 8.228s process CPU and 738.14 MiB peak RSS, one sequential CPU process. Timing uses `perf_counter`/`process_time`; RSS uses current-executable `/proc/self/status` VmHWM, with no periodic sampling or subprocess work. No inference, training or GPU. Validation: 23 focused training/metadata tests pass; Ruff and targeted mypy pass.

---

# Earlier v2 preparation (retained provenance)

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

Retired v2 preparation: 2.234s wall, 2.238s process CPU, 137.18 MiB current-executable peak RSS. One sequential CPU process; /proc/self/status VmHWM, no periodic sampling. Reference acquisition records CPU/wall separately; acquisition RSS is unmeasured. No inference or GPU.

Three focused tests, Ruff and targeted mypy pass. Complete metadata includes actual image areas, native text geometry, PDF/content/string byte counts and descriptive layout/noise proxies. Five raw-string token scans fail with unterminated-literal parser errors and remain explicitly unknown. No quality score or independent evaluation claim follows.
