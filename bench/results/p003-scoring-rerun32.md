# Independent scorer replay: 32 retained pipeline runs

All 32 fresh CPU replays reproduce the previous strict scores, complete tolerant alignment witnesses/counts, and inference rates exactly. This reruns evaluation of retained outputs; it makes **zero new model calls** and changes no predictions, targets, or scorer settings. Separate decision-only selector, ownership, and header comparisons retain their attribution rules and are outside this full-pipeline inventory.

The independently approved six-file scorer authority matched current code byte for byte before execution. Both original plans and every report/evaluation/frozen/corpus/run-manifest pin were admitted before references were opened. The replay used 166.66 s wall, 156.30 s process CPU (93.78%), and 623,321,088 bytes peak sampled RSS; psutil sampled this one CPU process every 100 ms. No worker inference or GPU ran.

Strict cells and strict complete tables remain the primary historical measurements. Equivalent tables add only the versioned conservative global adjacent-column lexical schema rule. Content P/R measures monotone alignment units, including synthetic spaces introduced by cell joins; these are **not literal character recovery counts**. Content completion can coexist with wrong spans, extra blank rows, or incorrect structure. Missing and extra tables enter content P/R.

Each row is one retained run; no repeated-run uncertainty is hidden behind a pooled score. Rates are original inference usable-output pages/min and pages/APIUSD under the recorded contention, not scorer speed or structurally correct-page rates. Unknown rates stay unmeasured. Costs retain their original provider/catalog/BYOK basis. No subgroup cost allocation is inferred.

## Natural DEV16

16 pages, 53 reference tables, 2,333 cells; four negative pages.

| Model/treatment (run ID) | Strict cells | Strict tables | Strict or equivalent | Content tables | Content P/R | Errors scored/all | Extra/missing | Negative FP pages | Original ppm | Pages/APIUSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| acquisition-luna-yolo640-crop1024-r0-c3 | 290/2333 | 3/53 | 4/53 | 3/53 | 0.889/0.202 | 1/1 | 0/39 | 0 | 3.37 | 1162.63 |
| acquisition-luna-yolo1024-crop1024-r0-c3 | 807/2333 | 3/53 | 4/53 | 3/53 | 0.816/0.515 | 2/2 | 9/31 | 0 | 2.52 | 867.29 |
| acquisition-luna-yolo1280-crop1024-r0-c3 | 290/2333 | 4/53 | 5/53 | 4/53 | 0.935/0.199 | 2/2 | 0/40 | 0 | 1.64 | 562.96 |
| acquisition-haiku-matrix-yolo640-crop1024-r0-c3 | 373/2333 | 2/53 | 3/53 | 2/53 | 0.884/0.241 | 2/2 | 2/40 | 0 | 6.26 | 1554.78 |
| acquisition-haiku-matrix-yolo1024-crop1024-r0-c3 | 295/2333 | 3/53 | 4/53 | 3/53 | 0.864/0.245 | 2/2 | 2/38 | 1 | 4.90 | 1408.58 |
| acquisition-haiku-matrix-yolo1280-crop1024-r0-c3 | 295/2333 | 2/53 | 3/53 | 2/53 | 0.943/0.200 | 2/2 | 0/40 | 0 | 2.56 | 574.62 |
| acquisition-sonnet-yolo640-crop1024-r0-c3 | 292/2333 | 3/53 | 4/53 | 3/53 | 0.946/0.216 | 1/1 | 0/39 | 0 | 5.29 | 66.77 |
| acquisition-sonnet-yolo1024-crop1024-r0-c3 | 362/2333 | 3/53 | 5/53 | 3/53 | 0.866/0.276 | 1/1 | 1/36 | 0 | 4.31 | 56.43 |
| acquisition-sonnet-yolo1280-crop1024-r0-c3 | 291/2333 | 3/53 | 4/53 | 3/53 | 0.939/0.200 | 2/2 | 0/40 | 0 | 3.50 | 59.65 |
| acquisition-gemma31-yolo640-crop1024-r0-c3 | 262/2333 | 3/53 | 4/53 | 3/53 | 0.870/0.160 | 4/4 | 0/42 | 0 | 0.83 | 1508.48 |
| acquisition-gemma31-yolo1280-crop1024-r0-c3 | 269/2333 | 3/53 | 4/53 | 3/53 | 0.930/0.165 | 3/3 | 0/42 | 0 | 2.31 | 4156.20 |
| acquisition-ministral14-yolo640-crop1024-r0-c3 | 207/2333 | 2/53 | 3/53 | 2/53 | 0.877/0.162 | 3/3 | 1/41 | 0 | 4.77 | 3553.66 |
| acquisition-ministral14-yolo1280-crop1024-r0-c3 | 574/2333 | 2/53 | 3/53 | 2/53 | 0.805/0.405 | 4/4 | 7/38 | 0 | 2.79 | 2207.18 |

## Natural DEV64

64 pages, 93 tables, 3,847 cells. These repeated arms do not establish a stable model frontier.

| Model/treatment (run ID) | Strict cells | Strict tables | Strict or equivalent | Content tables | Content P/R | Errors scored/all | Extra/missing | Negative FP pages | Original ppm | Pages/APIUSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| natural64-ordinal-ocr300-512-r0-c3 | 1309/3847 | 11/93 | 12/93 | 11/93 | 0.908/0.434 | 2/2 | 11/43 | 0 | 2.69 | 1013.32 |
| natural64-crops-luna-1024-r0-c3 | 1348/3847 | 12/93 | 14/93 | 12/93 | 0.919/0.419 | 1/1 | 0/44 | 0 | 5.54 | 1985.15 |
| natural64-crops-sonnet-1024-legacy-r0-c6 | 1839/3847 | 14/93 | 17/93 | 14/93 | 0.894/0.638 | 0/0 | 4/34 | 1 | 3.20 | 140.43 |
| natural64-ordinal-ocredge2048-512-r0-c6 | 1125/3847 | 10/93 | 12/93 | 10/93 | 0.900/0.363 | 1/1 | 11/46 | 1 | 2.35 | 1051.69 |
| natural64-crops-haiku-1024-matrix_strict-r0-c6 | 1333/3847 | 12/93 | 14/93 | 12/93 | 0.937/0.373 | 6/6 | 0/50 | 0 | 3.65 | 2229.64 |
| natural64-ordinal-ocredge3072-512-r0-c6 | 1204/3847 | 12/93 | 13/93 | 12/93 | 0.912/0.377 | 2/2 | 15/46 | 0 | 2.57 | 1009.50 |
| natural64-crops-opus-1024-legacy-r0-c6 | 1617/3847 | 15/93 | 16/93 | 15/93 | 0.888/0.588 | 2/2 | 3/36 | 0 | 6.40 | 72.36 |

## Frozen confirmation48

48 pages: 32 natural and 16 authored; 66 tables, 4,203 cells. Configuration was frozen before confirmation, and these results were not used to tune it.

| Model/treatment (run ID) | Strict cells | Strict tables | Strict or equivalent | Content tables | Content P/R | Errors scored/all | Extra/missing | Negative FP pages | Original ppm | Pages/APIUSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| confirmation48-luna-1024-r0-c3 | 2467/4203 | 25/66 | 25/66 | 26/66 | 0.981/0.716 | 1/1 | 0/9 | 0 | 5.01 | 1605.26 |
| confirmation48-sonnet-1024-r0-c3 | 1891/4203 | 27/66 | 29/66 | 28/66 | 0.992/0.539 | 3/3 | 0/19 | 0 | 6.36 | 89.87 |
| confirmation48-haiku-matrix-1024-r0-c3 | 2664/4203 | 27/66 | 27/66 | 29/66 | 0.980/0.870 | 1/1 | 1/8 | 0 | 6.44 | 1337.74 |
| confirmation48-ordinal-ocr300-512-r0-c3 | 2080/4203 | 23/66 | 24/66 | 24/66 | 0.904/0.512 | 4/4 | 3/19 | 1 | 2.70 | 684.29 |

## Complete corpus276

276 attempted pages: 220 adjudicated (64 natural and 156 authored), plus 56 diagnostic pages with no adjudicated table targets. Aggregate quality is not natural-only quality.

| Model/treatment (run ID) | Strict cells | Strict tables | Strict or equivalent | Content tables | Content P/R | Errors scored/all | Extra/missing | Negative FP pages | Original ppm | Pages/APIUSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full276-ordinal-ocr300-512-r0-c6 | 6232/8897 | 165/249 | 166/249 | 165/249 | 0.777/0.708 | 3/7 | 44/49 | 11 | 5.33 | 2232.19 |
| full276-crops-luna-1024-r0-c6 | 6902/8897 | 166/249 | 168/249 | 166/249 | 0.826/0.820 | 0/1 | 12/33 | 8 | 4.86 | 3177.15 |

## Random authored40

40 authored pages, 36 tables, 2,769 cells, eight negatives; separate from natural generalization.

| Model/treatment (run ID) | Strict cells | Strict tables | Strict or equivalent | Content tables | Content P/R | Errors scored/all | Extra/missing | Negative FP pages | Original ppm | Pages/APIUSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random40-luna-yolo640-crop1024-r0-c3 | 2769/2769 | 35/36 | 35/36 | 35/36 | 1.000/1.000 | 0/0 | 0/0 | 0 | 5.52 | 1761.29 |
| random40-luna-yolo1280-crop1024-r0-c3 | 2602/2769 | 28/36 | 28/36 | 28/36 | 1.000/0.938 | 1/1 | 0/2 | 0 | 5.09 | 1708.68 |
| random40-haiku-matrix-yolo640-crop1024-r0-c3 | 2733/2769 | 33/36 | 33/36 | 36/36 | 0.996/1.000 | 0/0 | 1/0 | 1 | 6.32 | 1650.59 |
| random40-haiku-matrix-yolo1280-crop1024-r0-c3 | 2561/2769 | 26/36 | 26/36 | 27/36 | 1.000/0.924 | 2/2 | 0/3 | 0 | 6.00 | 1624.44 |
| random40-sonnet-yolo640-crop1024-r0-c3 | 2769/2769 | 36/36 | 36/36 | 36/36 | 0.996/1.000 | 0/0 | 1/0 | 1 | 7.40 | 113.12 |
| random40-sonnet-yolo1280-crop1024-r0-c3 | 2499/2769 | 29/36 | 29/36 | 29/36 | 1.000/0.905 | 2/2 | 0/3 | 0 | 6.01 | 112.04 |

## Mixed-cohort interpretation

The following already verified metadata strata keep full276 natural and authored strict results distinct. Subgroup inference rates are unavailable. Full276 operational failures include diagnostic pages; the main table explicitly separates scored errors from all attempted-page errors.

| Run | Stratum | Pages | Strict cells | Strict complete tables | Errors | Extra/missing |
|---|---|---:|---:|---:|---:|---:|
| full276-ordinal-ocr300-512-r0-c6 | cohort/authored | 156 | 5050/5050 | 156/156 | 0 | 17/0 |
| full276-ordinal-ocr300-512-r0-c6 | cohort/omnidoc | 64 | 1182/3847 | 9/93 | 3 | 27/49 |
| full276-crops-luna-1024-r0-c6 | cohort/authored | 156 | 4949/5050 | 152/156 | 0 | 8/1 |
| full276-crops-luna-1024-r0-c6 | cohort/omnidoc | 64 | 1953/3847 | 14/93 | 0 | 4/32 |

Luna natural64 strict scores differ between the dedicated run (1,348) and the full276 subset (1,953), despite the previous source-only comparison finding identical retained image/request hashes for the shared actual requests. This is repeated-run variation, not an input-controlled stable quality gain. The random40 Luna640 content P/R of 1 does not repair its extra blank row; Haiku640 recovers all 36 table contents while only 33 are strict, with the three nonexact span topologies still recorded.

## Provenance

Ignored artifact root: `pipeline-p003/scoring-rerun32-v1`. `report.json` and each run JSON retain full witnesses; `reconciliation.json` pins previous artifact hashes, strict/tolerant/count hashes, scorer authority, and resource scope. Originals remain unchanged.

- report.json: SHA256 `f3fbc76d61cefc920482d16e19959e3dc323d92c7e5c58a2acb88b6e42aa5c48`
- reconciliation.json: SHA256 `33776df69d08881c6d43eff4bfd7ff5f774ac47f4245d2913487110f8ed06a56`
- Original26 plan: `333ca142f623837c724276be383ac8006f8ae504ca632ec489c5ff3417bdf743`.
- Random40 six-run plan: `79de964dfeff948b6e6ee597738001c21008c1a4bf6545e35dc0887686860abe`.
- Scorer: `p003-dual-score-audit-v2`, content alignment v2, original-anchor span adapter, unchanged strict scorer. All 32 strict and complete tolerant/count hashes equal their prior pinned results.
