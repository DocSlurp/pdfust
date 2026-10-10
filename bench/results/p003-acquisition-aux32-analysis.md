# Acquisition and auxiliary32 DEV comparison

Checkpoint: 20/32 independently verified arms. The frozen plan contains 13 complete generation, 9 structure-admission and 10 geometry-diagram arms. Pending arms remain visible below. All quality counts use 16 pages, 53 tables, 2333 reference cells and 4 negative pages. This is the established DEV screen, separate from fresh confirmation 48.
Generation arms include acquisition and transcription. Admission arms retain only model-admitted source-owned TATR tables; rejected, unresolved or failed pages receive no historical table credit. Diagram arms count independently selected complete disjoint crops, including valid partial predictions on operational error pages. Duplicate, unresolved and failed crops receive zero credit; conflicting positive crops are all refused. No cross-model fallback or retry is credited.
Single runs are observations, with no confidence interval or repeat estimate available for these arms. Diagram instructions explicitly identify artificial geometry-only pixels, so comparison against source pixels changes evidence framing as well as pixels. Large cell-count differences can be concentrated in dense pages. No fresh confirmation result selected these configurations.

## Complete generation


| Run | Status | Strict | Text | Structure | Complete | Missing | Extra | Negative FP pages | Score errors | Exact positive pages | USD | Rate | Scope units/APIUSD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| acquisition-luna-yolo640-crop1024-r0-c3 | running; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| acquisition-luna-yolo1024-crop1024-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| acquisition-luna-yolo1280-crop1024-r0-c3 | verified | 290 | 290 | 359 | 4 | 40 | 0 | 0 | 2 | 3 | 0.02486862 | 1.641 | 562.958 |
| acquisition-haiku-matrix-yolo640-crop1024-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| acquisition-haiku-matrix-yolo1024-crop1024-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| acquisition-haiku-matrix-yolo1280-crop1024-r0-c3 | running; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| acquisition-sonnet-yolo640-crop1024-r0-c3 | verified | 292 | 292 | 361 | 3 | 39 | 0 | 0 | 1 | 2 | 0.22463800 | 5.293 | 66.774 |
| acquisition-sonnet-yolo1024-crop1024-r0-c3 | verified | 362 | 362 | 606 | 3 | 36 | 1 | 0 | 1 | 2 | 0.26580000 | 4.306 | 56.433 |
| acquisition-sonnet-yolo1280-crop1024-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| acquisition-gemma31-yolo640-crop1024-r0-c3 | verified | 262 | 262 | 314 | 3 | 42 | 0 | 0 | 4 | 2 | 0.00795502 | 0.832 | 1508.481 |
| acquisition-gemma31-yolo1280-crop1024-r0-c3 | verified | 269 | 270 | 332 | 3 | 42 | 0 | 0 | 3 | 2 | 0.00312786 | 2.313 | 4156.196 |
| acquisition-ministral14-yolo640-crop1024-r0-c3 | verified | 207 | 207 | 319 | 2 | 41 | 1 | 0 | 3 | 2 | 0.00365820 | 4.773 | 3553.660 |
| acquisition-ministral14-yolo1280-crop1024-r0-c3 | verified | 574 | 581 | 986 | 2 | 38 | 7 | 0 | 4 | 2 | 0.00543680 | 2.790 | 2207.181 |

Rate is operational usable pages/minute for complete generation, intended retained-evidence pages/minute for admission, and attempted questions/minute for diagram. Incremental rates exclude historical acquisition/generation and are not fresh pipeline throughput.

## Incremental structure admission


| Run | Status | Strict | Text | Structure | Complete | Missing | Extra | Negative FP pages | Score errors | Exact positive pages | USD | Rate | Scope units/APIUSD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| admission-pplx-detector05-edge0-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| admission-pplx-detector05-edge128-r0-c3 | running; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| admission-pplx-detector05-edge512-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| admission-lunadec-detector05-edge0-r0-c3 | verified | 185 | 187 | 315 | 2 | 42 | 0 | 0 | 0 | 1 | 0.00999040 | 14.089 | 1601.537 |
| admission-lunadec-detector05-edge128-r0-c3 | verified | 111 | 113 | 237 | 1 | 44 | 0 | 0 | 0 | 0 | 0.01006960 | 13.802 | 1588.941 |
| admission-lunadec-detector05-edge512-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| admission-clefomni-detector05-edge0-r0-c3 | verified | 94 | 94 | 102 | 1 | 51 | 1 | 1 | 0 | 1 | 0.02302380 | 17.165 | 694.933 |
| admission-clefomni-detector05-edge128-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| admission-clefomni-detector05-edge512-r0-c3 | verified | 196 | 198 | 561 | 3 | 41 | 0 | 0 | 0 | 2 | 0.02362125 | 21.887 | 677.356 |

Rate is operational usable pages/minute for complete generation, intended retained-evidence pages/minute for admission, and attempted questions/minute for diagram. Incremental rates exclude historical acquisition/generation and are not fresh pipeline throughput.

## Incremental geometry diagram


| Run | Status | Strict | Text | Structure | Complete | Missing | Extra | Negative FP pages | Score errors | Exact positive pages | USD | Rate | Scope units/APIUSD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| diagram-pplx-filled-128-r0-c3 | verified | 224 | 235 | 292 | 0 | 44 | 3 | 0 | 7 | 0 | 0.00066222 | 28.353 | 24161.155 |
| diagram-pplx-filled-512-r0-c3 | verified | 782 | 782 | 938 | 1 | 35 | 0 | 0 | 8 | 0 | 0.00067808 | 24.338 | 23596.036 |
| diagram-pplx-filled-400-r0-c3 | not_started; unverified | — | — | — | — | — | — | — | — | — | — | — | — |
| diagram-pplx-outline-128-r0-c3 | verified | 908 | 919 | 1078 | 1 | 33 | 3 | 0 | 7 | 0 | 0.00066222 | 18.473 | 24161.155 |
| diagram-pplx-outline-400-r0-c3 | verified | 193 | 204 | 227 | 0 | 47 | 3 | 0 | 8 | 0 | 0.00066636 | 23.623 | 24011.045 |
| diagram-pplx-outline-512-r0-c3 | verified | 193 | 204 | 227 | 0 | 47 | 3 | 0 | 8 | 0 | 0.00067808 | 18.169 | 23596.036 |
| diagram-lunadec-filled-128-r0-c3 | verified | 0 | 0 | 0 | 0 | 53 | 0 | 0 | 14 | 0 | 0.00260390 | 33.121 | 6144.629 |
| diagram-lunadec-filled-512-r0-c3 | verified | 0 | 0 | 0 | 0 | 53 | 0 | 0 | 14 | 0 | 0.00279310 | 16.060 | 5728.402 |
| diagram-clefomni-filled-128-r0-c3 | verified | 108 | 119 | 130 | 0 | 50 | 3 | 0 | 12 | 0 | 0.00511740 | 30.098 | 3126.588 |
| diagram-clefomni-filled-512-r0-c3 | verified | 106 | 117 | 120 | 0 | 51 | 3 | 0 | 12 | 0 | 0.00523635 | 26.524 | 3055.564 |

Rate is operational usable pages/minute for complete generation, intended retained-evidence pages/minute for admission, and attempted questions/minute for diagram. Incremental rates exclude historical acquisition/generation and are not fresh pipeline throughput.

## Actual decision outcomes


| Run | Native outcome counts | Attempted questions | Operational failed pages | Complete crop pages | Partial crop pages | USD basis | Scope rate per APIUSD |
|---|---|---:|---:|---:|---:|---|---:|
| diagram-pplx-filled-128-r0-c3 | not_applicable_duplicates=3, selected=9, unresolved=7 | 16 | 9 | 7 | 2 | provider-reported USD | 24161.155 |
| diagram-pplx-filled-512-r0-c3 | not_applicable_duplicates=3, selected=7, unresolved=9 | 16 | 11 | 5 | 3 | provider-reported USD | 23596.036 |
| diagram-pplx-outline-128-r0-c3 | not_applicable_duplicates=3, selected=9, unresolved=7 | 16 | 9 | 7 | 2 | provider-reported USD | 24161.155 |
| diagram-pplx-outline-400-r0-c3 | not_applicable_duplicates=3, selected=6, unresolved=10 | 16 | 12 | 4 | 4 | provider-reported USD | 24011.045 |
| diagram-pplx-outline-512-r0-c3 | not_applicable_duplicates=3, selected=6, unresolved=10 | 16 | 12 | 4 | 4 | provider-reported USD | 23596.036 |
| admission-lunadec-detector05-edge0-r0-c3 | reject=4, retain=13, unresolved=2 | 19 | 0 | — | — | catalog estimate | 1601.537 |
| admission-lunadec-detector05-edge128-r0-c3 | reject=7, retain=11, unresolved=1 | 19 | 0 | — | — | catalog estimate | 1588.941 |
| diagram-lunadec-filled-128-r0-c3 | not_applicable_duplicates=3, unresolved=16 | 16 | 14 | 2 | 0 | catalog estimate | 6144.629 |
| diagram-lunadec-filled-512-r0-c3 | not_applicable_duplicates=3, unresolved=16 | 16 | 14 | 2 | 0 | catalog estimate | 5728.402 |
| admission-clefomni-detector05-edge0-r0-c3 | reject=15, retain=3, unresolved=1 | 19 | 0 | — | — | provider-reported USD | 694.933 |
| admission-clefomni-detector05-edge512-r0-c3 | reject=7, retain=12 | 19 | 0 | — | — | provider-reported USD | 677.356 |
| diagram-clefomni-filled-128-r0-c3 | not_applicable_duplicates=3, selected=3, unresolved=13 | 16 | 13 | 3 | 1 | provider-reported USD | 3126.588 |
| diagram-clefomni-filled-512-r0-c3 | not_applicable_duplicates=3, selected=2, unresolved=14 | 16 | 14 | 2 | 2 | provider-reported USD | 3055.564 |

## Fixed dense-page sensitivity

The same two previously declared dense DEV pages contain 1972/2333 cells; the other 14 contain 361. This secondary breakdown preserves errors and does not select or tune inputs. Positive-page macro recall equally weights all 12 positive pages.

| Run | Dense2 strict /1972 | Other14 strict /361 | Positive macro strict recall |
|---|---:|---:|---:|
| diagram-pplx-filled-128-r0-c3 | 103 | 121 | 0.213 |
| diagram-pplx-filled-512-r0-c3 | 691 | 91 | 0.213 |
| diagram-pplx-outline-128-r0-c3 | 794 | 114 | 0.248 |
| diagram-pplx-outline-400-r0-c3 | 103 | 90 | 0.139 |
| diagram-pplx-outline-512-r0-c3 | 103 | 90 | 0.139 |
| admission-lunadec-detector05-edge0-r0-c3 | 0 | 185 | 0.280 |
| admission-lunadec-detector05-edge128-r0-c3 | 0 | 111 | 0.224 |
| diagram-lunadec-filled-128-r0-c3 | 0 | 0 | 0.000 |
| diagram-lunadec-filled-512-r0-c3 | 0 | 0 | 0.000 |
| admission-clefomni-detector05-edge0-r0-c3 | 0 | 94 | 0.133 |
| admission-clefomni-detector05-edge512-r0-c3 | 0 | 196 | 0.391 |
| diagram-clefomni-filled-128-r0-c3 | 103 | 5 | 0.028 |
| diagram-clefomni-filled-512-r0-c3 | 103 | 3 | 0.021 |
| acquisition-luna-yolo1280-crop1024-r0-c3 | 0 | 290 | 0.570 |
| acquisition-sonnet-yolo640-crop1024-r0-c3 | 0 | 292 | 0.616 |
| acquisition-sonnet-yolo1024-crop1024-r0-c3 | 71 | 291 | 0.580 |
| acquisition-gemma31-yolo640-crop1024-r0-c3 | 0 | 262 | 0.472 |
| acquisition-gemma31-yolo1280-crop1024-r0-c3 | 0 | 269 | 0.497 |
| acquisition-ministral14-yolo640-crop1024-r0-c3 | 0 | 207 | 0.380 |
| acquisition-ministral14-yolo1280-crop1024-r0-c3 | 369 | 205 | 0.405 |

## Charge bases


| Run | Effective APIUSD | Original reported subtotal USD | Missing reported attempts | Retained basis |
|---|---:|---:|---:|---|
| diagram-pplx-filled-128-r0-c3 | 0.00066222 | 0.00066222 | 0 | provider-reported USD |
| diagram-pplx-filled-512-r0-c3 | 0.00067808 | 0.00067808 | 0 | provider-reported USD |
| diagram-pplx-outline-128-r0-c3 | 0.00066222 | 0.00066222 | 0 | provider-reported USD |
| diagram-pplx-outline-400-r0-c3 | 0.00066636 | 0.00066636 | 0 | provider-reported USD |
| diagram-pplx-outline-512-r0-c3 | 0.00067808 | 0.00067808 | 0 | provider-reported USD |
| admission-lunadec-detector05-edge0-r0-c3 | 0.00999040 | 0.00000000 | 0 | catalog estimate |
| admission-lunadec-detector05-edge128-r0-c3 | 0.01006960 | 0.00000000 | 0 | catalog estimate |
| diagram-lunadec-filled-128-r0-c3 | 0.00260390 | 0.00000000 | 0 | catalog estimate |
| diagram-lunadec-filled-512-r0-c3 | 0.00279310 | 0.00000000 | 0 | catalog estimate |
| admission-clefomni-detector05-edge0-r0-c3 | 0.02302380 | 0.02302380 | 0 | provider-reported USD |
| admission-clefomni-detector05-edge512-r0-c3 | 0.02362125 | 0.02362125 | 0 | provider-reported USD |
| diagram-clefomni-filled-128-r0-c3 | 0.00511740 | 0.00511740 | 0 | provider-reported USD |
| diagram-clefomni-filled-512-r0-c3 | 0.00523635 | 0.00523635 | 0 | provider-reported USD |
| acquisition-luna-yolo1280-crop1024-r0-c3 | 0.02486862 | 0.00000000 | 0 | provider-reported BYOK upstream plus gateway USD |
| acquisition-sonnet-yolo640-crop1024-r0-c3 | 0.22463800 | 0.22463800 | 0 | provider-reported USD |
| acquisition-sonnet-yolo1024-crop1024-r0-c3 | 0.26580000 | 0.26580000 | 0 | provider-reported USD |
| acquisition-gemma31-yolo640-crop1024-r0-c3 | 0.00795502 | 0.00795502 | 0 | provider-reported USD |
| acquisition-gemma31-yolo1280-crop1024-r0-c3 | 0.00312786 | 0.00312786 | 0 | provider-reported USD |
| acquisition-ministral14-yolo640-crop1024-r0-c3 | 0.00365820 | 0.00365820 | 0 | provider-reported USD |
| acquisition-ministral14-yolo1280-crop1024-r0-c3 | 0.00543680 | 0.00519840 | 0 | catalog estimate, provider-reported USD |
Reported zero is preserved separately from estimates. No cost sidecar replaces original reports; unresolved or missing cost components cannot become a complete total.

Operational failure counts are separate from scorer errors: valid complete crops on partial diagram pages remain scored. Native abstention is a valid response, and receives no predicted tables. Positive provider-reported charges and labeled catalog estimates remain separate bases; missing charges remain unmeasured. Rates per APIUSD have the same incremental scope as the preceding rate table.

## Resources and provenance

All arms are contended, with per-arm transport cap 3 and a shared paid-request cap 3. Parent CPU is process_time, RSS is sampled every 100 ms. Separate detector-worker CPU/RSS is reported where available; peaks are not summed. No GPU workload was used. Historical preprocessing/inference costs are excluded from incremental arms.

| Run | Execution wall s | Parent CPU s | Parent RSS MiB | Prepare CPU s | Detector worker CPU s | Worker peak MiB | Report SHA prefix |
|---|---:|---:|---:|---:|---:|---:|---|
| diagram-pplx-filled-128-r0-c3 | 33.859 | 22.500 | 173.551 | unmeasured | unmeasured | unmeasured | adc011aba823 |
| diagram-pplx-filled-512-r0-c3 | 39.445 | 24.184 | 152.602 | unmeasured | unmeasured | unmeasured | 9927f2b87c66 |
| diagram-pplx-outline-128-r0-c3 | 51.969 | 21.779 | 173.234 | unmeasured | unmeasured | unmeasured | f39703b9c4df |
| diagram-pplx-outline-400-r0-c3 | 40.638 | 23.139 | 149.465 | unmeasured | unmeasured | unmeasured | 44cf8c334c50 |
| diagram-pplx-outline-512-r0-c3 | 52.838 | 22.023 | 172.203 | unmeasured | unmeasured | unmeasured | d156378e0cae |
| admission-lunadec-detector05-edge0-r0-c3 | 68.139 | 24.492 | 216.098 | 31.737 | unmeasured | unmeasured | ff3e14b45b78 |
| admission-lunadec-detector05-edge128-r0-c3 | 69.557 | 24.836 | 216.570 | 31.828 | unmeasured | unmeasured | 8365c18e7367 |
| diagram-lunadec-filled-128-r0-c3 | 28.985 | 21.805 | 172.957 | unmeasured | unmeasured | unmeasured | d7c2865c4828 |
| diagram-lunadec-filled-512-r0-c3 | 59.775 | 20.282 | 173.438 | unmeasured | unmeasured | unmeasured | e9f9f7e5890e |
| admission-clefomni-detector05-edge0-r0-c3 | 55.929 | 26.918 | 192.371 | 30.622 | unmeasured | unmeasured | f098ed6fda71 |
| admission-clefomni-detector05-edge512-r0-c3 | 43.862 | 26.946 | 219.457 | 31.973 | unmeasured | unmeasured | db858f1f159f |
| diagram-clefomni-filled-128-r0-c3 | 31.896 | 22.433 | 149.449 | unmeasured | unmeasured | unmeasured | cdc70bc25435 |
| diagram-clefomni-filled-512-r0-c3 | 36.194 | 22.956 | 174.559 | unmeasured | unmeasured | unmeasured | c099e1e5bb88 |
| acquisition-luna-yolo1280-crop1024-r0-c3 | 511.804 | 67.823 | 389.703 | unmeasured | 85.763 | 1376.164 | a737190c53c6 |
| acquisition-sonnet-yolo640-crop1024-r0-c3 | 170.031 | 37.908 | 390.012 | unmeasured | 24.566 | 1122.324 | 5fb427c1fb00 |
| acquisition-sonnet-yolo1024-crop1024-r0-c3 | 209.030 | 41.430 | 389.371 | unmeasured | 52.200 | 1275.758 | 28b33f4c44bd |
| acquisition-gemma31-yolo640-crop1024-r0-c3 | 865.341 | 36.174 | 400.684 | unmeasured | 24.120 | 1110.707 | 076e8cf38034 |
| acquisition-gemma31-yolo1280-crop1024-r0-c3 | 337.166 | 43.327 | 390.527 | unmeasured | 91.529 | 1407.062 | f14da57edc8a |
| acquisition-ministral14-yolo640-crop1024-r0-c3 | 163.407 | 33.607 | 403.801 | unmeasured | 24.070 | 1134.379 | c396756b53cb |
| acquisition-ministral14-yolo1280-crop1024-r0-c3 | 258.021 | 41.523 | 381.656 | unmeasured | 90.654 | 1368.422 | 6530e32ed6d9 |

Full frozen source inventories, external Git-authenticated code maps, actual serialized request/image hashes, raw typed responses, exact selected states, per-page scores, complete resources and accounting evidence are retained in ignored per-arm evaluation.json/report.json artifacts. Verification makes no new API call and executes no archived experiment code.
