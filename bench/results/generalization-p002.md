# P002 natural-PDF generalization progress

Frozen runs with independently verified successful states, exact Markdown and explicit text provenance appear below. Missing/error pages remain in every scored denominator. Protocol groups use different frozen datasets and must not be pooled into one quality score. Timing/throughput cover page processing, excluding freeze/client setup and command startup; overlapping concurrent per-page CPU intervals are not additive.

## Authoritative natural16 DEV screen

Dataset SHA-256: `68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells / expected | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Pages/min | Pages/API USD | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| natural16-whole-reviewed | 9/16 | 7 | 0/12 | 0 | 0 | 2/2333 | 0/2333 | 16804/16640 | 1 | 0 | 2.74509 | 181.398 | 0.0496148 |
| natural16-regions-reviewed | 9/16 | 7 | 0/12 | 0 | 0 | 2/2333 | 0/2333 | 16804/16640 | 1 | 0 | 2.62157 | 251.199 | 0.0358282 |
| natural16-regions-80k | 16/16 | 0 | 0/12 | 0 | 1 | 320/2333 | 4/2333 | 25948/16640 | 3 | 5 | 3.6026 | 109.434 | 0.146207 |
| natural16-raster-select-512 | 16/16 | 0 | 0/12 | 0 | 3 | 418/2333 | 92/2333 | 25511/16640 | 5 | 5 | 3.91377 | 111.17 | 0.143924 |
| natural16-generate-sonnet | 16/16 | 0 | 1/12 | 2 | 10 | 419/2333 | 295/2333 | 14588/16640 | 15 | 7 | 2.59737 | 13.3194 | 1.20126 |
| natural16-generate-whitespace | 15/16 | 1 | 1/12 | 2 | 7 | 447/2333 | 236/2333 | 16144/16640 | 13 | 7 | 2.15636 | 12.0499 | 1.24482 |
| natural16-matrix-sonnet-512 | 14/16 | 2 | 1/12 | 2 | 9 | 327/2333 | 227/2333 | 15229/16640 | 13 | 9 | 2.7044 | 14.4924 | 0.966024 |
| natural16-matrix-haiku-512 | 16/16 | 0 | 1/12 | 2 | 10 | 406/2333 | 240/2333 | 14902/16640 | 14 | 3 | 1.98919 | 225.443 | 0.0709715 |
| natural16-yolo-matrix-sonnet-512 | 15/16 | 1 | 1/12 | 2 | 12 | 437/2333 | 341/2333 | 13543/16640 | 15 | 3 | 3.88937 | 52.2889 | 0.286868 |
| natural16-yolo-tiles2-matrix-sonnet-512 | 15/16 | 1 | 1/12 | 2 | 10 | 431/2333 | 250/2333 | 14446/16640 | 14 | 1 | 2.32983 | 33.3856 | 0.449296 |
| natural16-vision-sonnet-1200 | 15/16 | 1 | 2/12 | 3 | 14 | 408/2333 | 299/2333 | 12984/16640 | 14 | 0 | 6.50775 | 106.649 | 0.140648 |
| natural16-vision-haiku-1200 | 13/16 | 3 | 2/12 | 2 | 8 | 358/2333 | 245/2333 | 14802/16640 | 9 | 3 | 6.40679 | 1527.9 | 0.0085084 |
| natural16-yolo-matrix-haiku-512 | 15/16 | 1 | 1/12 | 2 | 12 | 359/2333 | 258/2333 | 13879/16640 | 14 | 1 | 3.24057 | 638.725 | 0.0234843 |
| natural16-vision-sonnet-2048 | 11/16 | 5 | 2/12 | 3 | 12 | 244/2333 | 203/2333 | 13931/16640 | 12 | 0 | 12.8658 | 79.7668 | 0.137902 |
| natural16-vision-haiku-2048 | 11/16 | 5 | 2/12 | 3 | 11 | 244/2333 | 201/2333 | 14419/16640 | 12 | 2 | 11.4908 | 1255.84 | 0.0087591 |
| natural16-yolo-matrix-haiku-1024 | 14/16 | 2 | 1/12 | 2 | 11 | 336/2333 | 247/2333 | 14369/16640 | 12 | 1 | 3.56989 | 662.449 | 0.0211337 |
| natural16-yolo-ocr300-matrix-haiku-1024 | 15/16 | 1 | 2/12 | 3 | 11 | 440/2333 | 387/2333 | 13206/16640 | 13 | 0 | 2.59567 | 903.468 | 0.0166027 |
| natural16-vision-sonnet-2048-q50 | 16/16 | 0 | 2/12 | 7 | 20 | 622/2333 | 540/2333 | 11698/16640 | 19 | 2 | 9.69541 | 63.2871 | 0.252816 |
| natural16-vision-haiku-2048-q50 | 14/16 | 2 | 2/12 | 2 | 9 | 261/2333 | 208/2333 | 15829/16640 | 10 | 4 | 12.4331 | 1190.19 | 0.0117628 |
| natural16-vision-crops-sonnet-1024 | 16/16 | 0 | 3/12 | 5 | 25 | 1287/2333 | 982/2333 | 7864/16640 | 23 | 0 | 6.87782 | 69.4119 | 0.230508 |
| natural16-vision-crops-haiku-1024 | 14/16 | 2 | 3/12 | 4 | 14 | 862/2333 | 687/2333 | 11089/16640 | 14 | 3 | 8.56503 | 1538.73 | 0.0090984 |
| natural16-vision-opus-2048-q50 | 16/16 | 0 | 2/12 | 3 | 14 | 463/2333 | 300/2333 | 15091/16640 | 15 | 6 | 6.84489 | 34.5862 | 0.462612 |
| natural16-yolo-fused-ocr2048-haiku-1024 | 15/16 | 1 | 2/12 | 3 | 11 | 471/2333 | 285/2333 | 14352/16640 | 14 | 1 | 2.83641 | 619.341 | 0.0242193 |
| natural16-yolo-matrix-haiku-512-rowwrap | 15/16 | 1 | 1/12 | 2 | 12 | 349/2333 | 231/2333 | 14139/16640 | 14 | 1 | 3.21552 | 594.347 | 0.0252378 |
| natural16-yolo-matrix-haiku-512-columns | 16/16 | 0 | 1/12 | 2 | 12 | 545/2333 | 332/2333 | 13616/16640 | 14 | 0 | 3.38242 | 584.159 | 0.0273898 |
| natural16-yolo-indices-haiku-512 | 16/16 | 0 | 1/12 | 2 | 12 | 477/2333 | 311/2333 | 13497/16640 | 15 | 1 | 3.50996 | 645.992 | 0.0247681 |
| natural16-yolo-indices-haiku-512-gated | 15/16 | 1 | 1/12 | 2 | 9 | 314/2333 | 232/2333 | 14832/16640 | 10 | 7 | 3.05878 | 539.852 | 0.0277854 |
| natural16-hybrid-sonnet-1024 | 15/16 | 1 | 3/12 | 4 | 14 | 361/2333 | 289/2333 | 13209/16640 | 14 | 0 | 3.99775 | 67.3225 | 0.222808 |
| natural16-vision-haiku-2048-q50-workers4 | 13/16 | 3 | 3/12 | 4 | 9 | 261/2333 | 216/2333 | 14878/16640 | 9 | 3 | 30.9319 | 1181.46 | 0.0110033 |
| natural16-vision-crops-haiku-768 | 16/16 | 0 | 2/12 | 3 | 13 | 533/2333 | 403/2333 | 13298/16640 | 14 | 0 | 9.86646 | 1849.2 | 0.0086524 |
| natural16-vision-crops-haiku-512 | 16/16 | 0 | 2/12 | 2 | 12 | 364/2333 | 290/2333 | 13879/16640 | 14 | 1 | 9.7988 | 1979.73 | 0.0080819 |
| natural16-vision-crops-haiku-400 | 16/16 | 0 | 2/12 | 3 | 12 | 359/2333 | 225/2333 | 14420/16640 | 12 | 2 | 8.49134 | 1779.68 | 0.0089904 |
| natural16-hybrid-haiku-1024 | 14/16 | 2 | 2/12 | 3 | 11 | 339/2333 | 289/2333 | 13601/16640 | 11 | 1 | 4.47476 | 1534.1 | 0.0091259 |

### natural16-whole-reviewed

Scope: complete source assembly; text: source-owned; source-conserved pages: 9/16.

Failure categories: `{"local_input_or_output_admission": 7}`.

Supplementary positive-page macro recall (12 pages): exact cells 0.00%; complete tables 0.00%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 0/14 | 0/10 | 0 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `unmeasured`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| perplexity/pplx-decider-v1.1-27b | 16 | 16 | 0.0104728 | 0 / 0 / 16 |
| anthropic/claude-sonnet-5.5 | 1 | 1 | 0.039142 | 0 / 1 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 0 | 2/2333 | 16804/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 196.715s; CPU 374.167s; sampled RSS 588820480 bytes; verified output pages/min 2.74509; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 17; reported USD subtotal 0.0496148; missing reported charges 0; cost bases `{"provider-reported USD": 17}`. Reservation amount 0; estimate amount 0.


### natural16-regions-reviewed

Scope: complete source assembly; text: source-owned; source-conserved pages: 9/16.

Failure categories: `{"local_input_or_output_admission": 7}`.

Supplementary positive-page macro recall (12 pages): exact cells 0.00%; complete tables 0.00%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 0/14 | 0/10 | 0 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `unmeasured`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| perplexity/pplx-decider-v1.1-27b | 24 | 24 | 0.0073622 | 0 / 0 / 24 |
| anthropic/claude-sonnet-5.5 | 1 | 1 | 0.028466 | 0 / 1 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 0 | 2/2333 | 16804/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 205.984s; CPU 342.123s; sampled RSS 636424192 bytes; verified output pages/min 2.62157; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 25; reported USD subtotal 0.0358282; missing reported charges 0; cost bases `{"provider-reported USD": 25}`. Reservation amount 0; estimate amount 0.


### natural16-regions-80k

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 4.18%; complete tables 0.00%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 2 |
| remaining_fourteen | 0/14 | 0/10 | 2 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| perplexity/pplx-decider-v1.1-27b | 56 | 56 | 0.0239754 | 0 / 0 / 56 |
| anthropic/claude-sonnet-5.5 | 5 | 5 | 0.122232 | 0 / 5 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 1 | 320/2333 | 25948/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 266.475s; CPU 359.703s; sampled RSS 660725760 bytes; verified output pages/min 3.6026; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 61; reported USD subtotal 0.146207; missing reported charges 0; cost bases `{"provider-reported USD": 61}`. Reservation amount 0; estimate amount 0.


### natural16-raster-select-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 15.31%; complete tables 0.00%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 2 |
| remaining_fourteen | 0/14 | 0/10 | 90 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| perplexity/pplx-decider-v1.1-27b | 57 | 57 | 0.0226022 | 0 / 0 / 57 |
| anthropic/claude-sonnet-5.5 | 5 | 5 | 0.121322 | 0 / 5 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 3 | 418/2333 | 25511/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 245.288s; CPU 327.633s; sampled RSS 633634816 bytes; verified output pages/min 3.91377; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 62; reported USD subtotal 0.143924; missing reported charges 0; cost bases `{"provider-reported USD": 62}`. Reservation amount 0; estimate amount 0.


### natural16-generate-sonnet

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 50.38%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 60 |
| remaining_fourteen | 2/14 | 1/10 | 235 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 47 | 47 | 1.20126 | 0 / 47 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 10 | 419/2333 | 14588/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 369.605s; CPU 314.827s; sampled RSS 598724608 bytes; verified output pages/min 2.59737; exact positive pages/min 0.162335. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 47; reported USD subtotal 1.20126; missing reported charges 0; cost bases `{"provider-reported USD": 47}`. Reservation amount 0; estimate amount 0.


### natural16-generate-whitespace

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"invalid_anchor_collection": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 43.55%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 8 |
| remaining_fourteen | 2/14 | 1/10 | 228 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 49 | 49 | 1.24482 | 0 / 49 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 7 | 447/2333 | 16144/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 417.369s; CPU 344.472s; sampled RSS 651649024 bytes; verified output pages/min 2.15636; exact positive pages/min 0.143758. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 49; reported USD subtotal 1.24482; missing reported charges 0; cost bases `{"provider-reported USD": 49}`. Reservation amount 0; estimate amount 0.


### natural16-matrix-sonnet-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 14/16.

Failure categories: `{"provider_content_filter": 2}`.

Supplementary positive-page macro recall (12 pages): exact cells 41.11%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 59 |
| remaining_fourteen | 2/14 | 1/10 | 168 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 44 | 44 | 0.966024 | 0 / 44 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 9 | 327/2333 | 15229/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 310.605s; CPU 360.122s; sampled RSS 647983104 bytes; verified output pages/min 2.7044; exact positive pages/min 0.193171. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 44; reported USD subtotal 0.966024; missing reported charges 0; cost bases `{"provider-reported USD": 44}`. Reservation amount 0; estimate amount 0.


### natural16-matrix-haiku-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 46.65%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 3 |
| remaining_fourteen | 2/14 | 1/10 | 237 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 47 | 47 | 0.0709715 | 0 / 47 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 10 | 406/2333 | 14902/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 482.609s; CPU 393.46s; sampled RSS 639729664 bytes; verified output pages/min 1.98919; exact positive pages/min 0.124324. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 47; reported USD subtotal 0.0709715; missing reported charges 0; cost bases `{"provider-reported USD": 47}`. Reservation amount 0; estimate amount 0.


### natural16-yolo-matrix-sonnet-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"provider_content_filter": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 52.27%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 104 |
| remaining_fourteen | 2/14 | 1/10 | 237 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 19 | 19 | 0.286868 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 12 | 437/2333 | 13543/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 231.4s; CPU 304.83s; sampled RSS 612708352 bytes; verified output pages/min 3.88937; exact positive pages/min 0.259291. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.286868; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.56802s, CPU 5.28494s; 16 per-page measurement entries, request CPU total 14.4786s; maximum sampled request RSS 1189687296 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-yolo-tiles2-matrix-sonnet-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"provider_content_filter": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 45.97%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 8 |
| remaining_fourteen | 2/14 | 1/10 | 242 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 29 | 29 | 0.449296 | 0 / 29 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 10 | 431/2333 | 14446/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 386.294s; CPU 317.07s; sampled RSS 603447296 bytes; verified output pages/min 2.32983; exact positive pages/min 0.155322. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 29; reported USD subtotal 0.449296; missing reported charges 0; cost bases `{"provider-reported USD": 29}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.61685s, CPU 5.46881s; 16 per-page measurement entries, request CPU total 69.3252s; maximum sampled request RSS 1206677504 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-sonnet-1200

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{"invalid_table_geometry": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 54.95%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 25 |
| remaining_fourteen | 3/14 | 2/10 | 274 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-sonnet-5.5`; review `unmeasured`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 16 | 16 | 0.140648 | 0 / 16 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 14 | 408/2333 | 12984/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 138.297s; CPU 9.53371s; sampled RSS 225779712 bytes; verified output pages/min 6.50775; exact positive pages/min 0.8677. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 16; reported USD subtotal 0.140648; missing reported charges 0; cost bases `{"provider-reported USD": 16}`. Reservation amount 0; estimate amount 0.


### natural16-vision-haiku-1200

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{"invalid_table_topology": 3}`.

Supplementary positive-page macro recall (12 pages): exact cells 39.61%; complete tables 16.67%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 1 |
| remaining_fourteen | 2/14 | 2/10 | 244 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 16 | 16 | 0.0085084 | 0 / 16 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 8 | 358/2333 | 14802/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 121.746s; CPU 9.48039s; sampled RSS 283582464 bytes; verified output pages/min 6.40679; exact positive pages/min 0.98566. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 16; reported USD subtotal 0.0085084; missing reported charges 0; cost bases `{"provider-reported USD": 16}`. Reservation amount 0; estimate amount 0.


### natural16-yolo-matrix-haiku-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"provider_output_length": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 51.05%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 2/14 | 1/10 | 258 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 18 | 18 | 0.0234843 | 0 / 18 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 12 | 359/2333 | 13879/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 277.729s; CPU 302.662s; sampled RSS 573603840 bytes; verified output pages/min 3.24057; exact positive pages/min 0.216038. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 18; reported USD subtotal 0.0234843; missing reported charges 0; cost bases `{"provider-reported USD": 18}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.62406s, CPU 5.34481s; 16 per-page measurement entries, request CPU total 15.4999s; maximum sampled request RSS 1178177536 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-sonnet-2048

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{"local_input_or_output_admission": 5}`.

Supplementary positive-page macro recall (12 pages): exact cells 50.01%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 3/14 | 2/10 | 203 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-sonnet-5.5`; review `unmeasured`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 16 | 11 | 0.137902 | 0 / 11 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 12 | 244/2333 | 13931/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 51.2988s; CPU 8.4647s; sampled RSS 252555264 bytes; verified output pages/min 12.8658; exact positive pages/min 2.33924. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 11; reported USD subtotal 0.137902; missing reported charges 0; cost bases `{"provider-reported USD": 11}`. Reservation amount 0; estimate amount 0.


### natural16-vision-haiku-2048

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{"local_input_or_output_admission": 5}`.

Supplementary positive-page macro recall (12 pages): exact cells 45.46%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 3/14 | 2/10 | 201 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 16 | 11 | 0.0087591 | 0 / 11 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 11 | 244/2333 | 14419/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 57.4374s; CPU 8.0963s; sampled RSS 230289408 bytes; verified output pages/min 11.4908; exact positive pages/min 2.08923. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 11; reported USD subtotal 0.0087591; missing reported charges 0; cost bases `{"provider-reported USD": 11}`. Reservation amount 0; estimate amount 0.


### natural16-yolo-matrix-haiku-1024

Scope: complete source assembly; text: source-owned; source-conserved pages: 14/16.

Failure categories: `{"local_input_or_output_admission": 2}`.

Supplementary positive-page macro recall (12 pages): exact cells 47.38%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 2/14 | 1/10 | 247 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 17 | 0.0211337 | 0 / 17 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 11 | 336/2333 | 14369/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 235.301s; CPU 297.055s; sampled RSS 580620288 bytes; verified output pages/min 3.56989; exact positive pages/min 0.254992. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 17; reported USD subtotal 0.0211337; missing reported charges 0; cost bases `{"provider-reported USD": 17}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.61326s, CPU 5.2969s; 16 per-page measurement entries, request CPU total 14.1969s; maximum sampled request RSS 1211076608 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-yolo-ocr300-matrix-haiku-1024

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"local_input_or_output_admission": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 52.08%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 116 |
| remaining_fourteen | 3/14 | 2/10 | 271 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 18 | 17 | 0.0166027 | 0 / 17 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 11 | 440/2333 | 13206/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 346.731s; CPU 772.823s; sampled RSS 700506112 bytes; verified output pages/min 2.59567; exact positive pages/min 0.346089. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 17; reported USD subtotal 0.0166027; missing reported charges 0; cost bases `{"provider-reported USD": 17}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.65171s, CPU 5.39285s; 16 per-page measurement entries, request CPU total 14.6069s; maximum sampled request RSS 1208901632 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-sonnet-2048-q50

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 64.10%; complete tables 23.40%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 4/39 | 0/2 | 247 |
| remaining_fourteen | 3/14 | 2/10 | 293 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-sonnet-5.5`; review `unmeasured`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 16 | 16 | 0.252816 | 0 / 16 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 7 | 20 | 622/2333 | 11698/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 99.0159s; CPU 10.41s; sampled RSS 239202304 bytes; verified output pages/min 9.69541; exact positive pages/min 1.21193. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 16; reported USD subtotal 0.252816; missing reported charges 0; cost bases `{"provider-reported USD": 16}`. Reservation amount 0; estimate amount 0.


### natural16-vision-haiku-2048-q50

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{"invalid_table_geometry": 1, "invalid_table_topology": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 40.34%; complete tables 16.67%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 2/14 | 2/10 | 208 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 16 | 16 | 0.0117628 | 0 / 16 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 9 | 261/2333 | 15829/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 67.5617s; CPU 10.5548s; sampled RSS 238407680 bytes; verified output pages/min 12.4331; exact positive pages/min 1.77615. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 16; reported USD subtotal 0.0117628; missing reported charges 0; cost bases `{"provider-reported USD": 16}`. Reservation amount 0; estimate amount 0.


### natural16-vision-crops-sonnet-1024

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 66.97%; complete tables 25.64%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 1/39 | 0/2 | 692 |
| remaining_fourteen | 4/14 | 3/10 | 290 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-sonnet-5.5`; review `unmeasured`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 19 | 19 | 0.230508 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 5 | 25 | 1287/2333 | 7864/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 139.579s; CPU 16.3054s; sampled RSS 338841600 bytes; verified output pages/min 6.87782; exact positive pages/min 1.28959. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.230508; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.73209s, CPU 5.61704s; 16 per-page measurement entries, request CPU total 15.0211s; maximum sampled request RSS 1203773440 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-crops-haiku-1024

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{"invalid_table_geometry": 1, "invalid_table_topology": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 52.90%; complete tables 25.00%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 416 |
| remaining_fourteen | 4/14 | 3/10 | 271 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 19 | 0.0090984 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 4 | 14 | 862/2333 | 11089/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 98.0732s; CPU 15.9637s; sampled RSS 347344896 bytes; verified output pages/min 8.56503; exact positive pages/min 1.83536. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.0090984; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.86041s, CPU 5.93336s; 16 per-page measurement entries, request CPU total 14.2593s; maximum sampled request RSS 1202114560 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-opus-2048-q50

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 62.01%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 7 |
| remaining_fourteen | 3/14 | 2/10 | 293 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-opus-5.5`; review `unmeasured`; generation `anthropic/claude-opus-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-opus-5.5 | 16 | 16 | 0.462612 | 0 / 16 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 14 | 463/2333 | 15091/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 140.251s; CPU 10.5721s; sampled RSS 237559808 bytes; verified output pages/min 6.84489; exact positive pages/min 0.855611. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 16; reported USD subtotal 0.462612; missing reported charges 0; cost bases `{"provider-reported USD": 16}`. Reservation amount 0; estimate amount 0.


### natural16-yolo-fused-ocr2048-haiku-1024

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"local_input_or_output_admission": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 51.53%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 12 |
| remaining_fourteen | 3/14 | 2/10 | 273 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 28 | 27 | 0.0242193 | 0 / 27 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 11 | 471/2333 | 14352/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 317.303s; CPU 343.496s; sampled RSS 577916928 bytes; verified output pages/min 2.83641; exact positive pages/min 0.378188. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 27; reported USD subtotal 0.0242193; missing reported charges 0; cost bases `{"provider-reported USD": 27}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.69088s, CPU 5.45845s; 16 per-page measurement entries, request CPU total 66.1159s; maximum sampled request RSS 1186115584 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-yolo-matrix-haiku-512-rowwrap

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"provider_output_length": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 47.92%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 2/14 | 1/10 | 231 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 18 | 18 | 0.0252378 | 0 / 18 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 12 | 349/2333 | 14139/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 279.892s; CPU 303.585s; sampled RSS 590168064 bytes; verified output pages/min 3.21552; exact positive pages/min 0.214368. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 18; reported USD subtotal 0.0252378; missing reported charges 0; cost bases `{"provider-reported USD": 18}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.57637s, CPU 5.26687s; 16 per-page measurement entries, request CPU total 14.3686s; maximum sampled request RSS 1204649984 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-yolo-matrix-haiku-512-columns

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 48.82%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 101 |
| remaining_fourteen | 2/14 | 1/10 | 231 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 19 | 0.0273898 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 12 | 545/2333 | 13616/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 283.821s; CPU 300.288s; sampled RSS 584110080 bytes; verified output pages/min 3.38242; exact positive pages/min 0.211401. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.0273898; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.60641s, CPU 5.36507s; 16 per-page measurement entries, request CPU total 14.0722s; maximum sampled request RSS 1192894464 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-yolo-indices-haiku-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 48.63%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 80 |
| remaining_fourteen | 2/14 | 1/10 | 231 |

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 19 | 0.0247681 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 12 | 477/2333 | 13497/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 273.507s; CPU 318.325s; sampled RSS 583811072 bytes; verified output pages/min 3.50996; exact positive pages/min 0.219372. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.0247681; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.79578s, CPU 5.80919s; 16 per-page measurement entries, request CPU total 16.5937s; maximum sampled request RSS 1198284800 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-yolo-indices-haiku-512-gated

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"provider_output_length": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 41.20%; complete tables 12.50%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 2/14 | 1/10 | 232 |

Policy `gated`; assembly `gated_generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 16 | 16 | 0.0252561 | 0 / 16 / 0 |
| perplexity/pplx-decider-v1.1-27b | 19 | 19 | 0.00252928 | 0 / 0 / 19 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 9 | 314/2333 | 14832/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 294.235s; CPU 316.183s; sampled RSS 618385408 bytes; verified output pages/min 3.05878; exact positive pages/min 0.203919. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 35; reported USD subtotal 0.0277854; missing reported charges 0; cost bases `{"provider-reported USD": 35}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.94507s, CPU 6.3519s; 16 per-page measurement entries, request CPU total 13.9478s; maximum sampled request RSS 1198125056 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-hybrid-sonnet-1024

Scope: complete retained-source assembly with explicit mixed text provenance; text: mixed native-source/model-transcribed; source-conserved pages: 5/16.

Failure categories: `{"invalid_table_topology": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 60.43%; complete tables 25.00%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 4/14 | 3/10 | 289 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-sonnet-5.5`; review `unmeasured`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 19 | 19 | 0.222808 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 4 | 14 | 361/2333 | 13209/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 225.127s; CPU 303.9s; sampled RSS 648929280 bytes; verified output pages/min 3.99775; exact positive pages/min 0.799549. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.222808; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.7259s, CPU 5.9275s; 16 per-page measurement entries, request CPU total 13.7779s; maximum sampled request RSS 1217159168 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-haiku-2048-q50-workers4

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{"invalid_table_geometry": 1, "invalid_table_topology": 2}`.

Supplementary positive-page macro recall (12 pages): exact cells 43.01%; complete tables 25.00%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 4/14 | 3/10 | 216 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 16 | 16 | 0.0110033 | 0 / 16 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 4 | 9 | 261/2333 | 14878/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 25.2167s; CPU 17.9386s; sampled RSS 513708032 bytes; verified output pages/min 30.9319; exact positive pages/min 7.13813. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 4; logical CPUs 8.

Ledger attempts 16; reported USD subtotal 0.0110033; missing reported charges 0; cost bases `{"provider-reported USD": 16}`. Reservation amount 0; estimate amount 0.


### natural16-vision-crops-haiku-768

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 59.10%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 110 |
| remaining_fourteen | 3/14 | 2/10 | 293 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 19 | 0.0086524 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 13 | 533/2333 | 13298/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 97.2993s; CPU 16.0702s; sampled RSS 353124352 bytes; verified output pages/min 9.86646; exact positive pages/min 1.23331. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.0086524; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.6506s, CPU 5.61253s; 16 per-page measurement entries, request CPU total 16.0262s; maximum sampled request RSS 1209356288 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-crops-haiku-512

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 58.29%; complete tables 16.67%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 2 |
| remaining_fourteen | 2/14 | 2/10 | 288 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 19 | 0.0080819 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 2 | 12 | 364/2333 | 13879/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 97.9712s; CPU 16.0089s; sampled RSS 352960512 bytes; verified output pages/min 9.7988; exact positive pages/min 1.22485. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.0080819; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.56285s, CPU 5.26988s; 16 per-page measurement entries, request CPU total 13.9584s; maximum sampled request RSS 1193586688 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-vision-crops-haiku-400

Scope: table-only image transcription comparator; text: model-transcribed; source-conserved pages: 0/16.

Failure categories: `{}`.

Supplementary positive-page macro recall (12 pages): exact cells 46.49%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 3/14 | 2/10 | 225 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 19 | 0.0089904 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 12 | 359/2333 | 14420/16640 | 0/4 |

Page-processing run wall (excludes freeze/client setup) 113.056s; CPU 15.8973s; sampled RSS 342110208 bytes; verified output pages/min 8.49134; exact positive pages/min 1.06142. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.0089904; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.56095s, CPU 5.23286s; 16 per-page measurement entries, request CPU total 14.5423s; maximum sampled request RSS 1202163712 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.


### natural16-hybrid-haiku-1024

Scope: complete retained-source assembly with explicit mixed text provenance; text: mixed native-source/model-transcribed; source-conserved pages: 4/16.

Failure categories: `{"invalid_table_geometry": 1, "invalid_table_topology": 1}`.

Supplementary positive-page macro recall (12 pages): exact cells 56.06%; complete tables 20.83%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 3/14 | 2/10 | 289 |

Policy `gated`; assembly `select`; configured gate/selector `anthropic/claude-haiku-5.5`; review `unmeasured`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 19 | 19 | 0.0091259 | 0 / 19 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 3 | 11 | 339/2333 | 13601/16640 | 1/4 |

Page-processing run wall (excludes freeze/client setup) 187.72s; CPU 308.846s; sampled RSS 603193344 bytes; verified output pages/min 4.47476; exact positive pages/min 0.639251. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.0091259; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.58069s, CPU 5.32563s; 16 per-page measurement entries, request CPU total 14.5005s; maximum sampled request RSS 1208565760 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.

## Corrected full corpus-r2 DEV baseline and fixed expansion

Dataset SHA-256: `e0a86f712fb7eda5f5ceb64fa19eb72c055694106a006b086fd9d09284295537`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells / expected | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Pages/min | Pages/API USD | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native-full-r2 | 270/276 | 6 | 96/172 | 120 | 120 | 4258/8897 | 4258/8897 | 31739/55180 | 96 | 0 | 39.3111 | unmeasured | 0 |
| native-regional-full-r2 | 272/276 | 4 | 96/172 | 120 | 120 | 4258/8897 | 4258/8897 | 31739/55180 | 96 | 0 | 36.7759 | unmeasured | 0 |
| full276-yolo-matrix-haiku-512 | 270/276 | 6 | 136/172 | 166 | 197 | 6784/8897 | 6329/8897 | 25472/55180 | 180 | 10 | 12.6423 | 2116.13 | 0.127591 |

### native-full-r2

Scope: complete source assembly; text: source-owned; source-conserved pages: 270/276.

Failure categories: `{"invalid_table_topology": 1, "local_input_or_output_admission": 1, "other_failure": 4}`.

Supplementary positive-page macro recall (172 pages): exact cells 59.30%; complete tables 59.30%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Policy `native`; assembly `native`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `unmeasured`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| No retained remote requests | 0 | 0 | unmeasured | unmeasured |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| authored | 156/156 | 120 | 120 | 4258/5050 | 4389/27830 | 0/24 |
| native-diagnostic | 56/0 | unscored | unscored | unscored/unscored | unscored/unscored | unscored/unscored |
| omnidoc | 64/64 | 0 | 0 | 0/3847 | 27350/27350 | 0/24 |

Page-processing run wall (excludes freeze/client setup) 412.098s; CPU 1232.85s; sampled RSS 725770240 bytes; verified output pages/min 39.3111; exact positive pages/min 13.9773. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 0; reported USD subtotal 0; missing reported charges 0; cost bases `{}`. Reservation amount 0; estimate amount 0.


### native-regional-full-r2

Scope: complete source assembly; text: source-owned; source-conserved pages: 272/276.

Failure categories: `{"missing_source_text": 4}`.

Supplementary positive-page macro recall (172 pages): exact cells 59.30%; complete tables 59.30%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Policy `native`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| No retained remote requests | 0 | 0 | unmeasured | unmeasured |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| authored | 156/156 | 120 | 120 | 4258/5050 | 4389/27830 | 0/24 |
| native-diagnostic | 56/0 | unscored | unscored | unscored/unscored | unscored/unscored | unscored/unscored |
| omnidoc | 64/64 | 0 | 0 | 0/3847 | 27350/27350 | 0/24 |

Page-processing run wall (excludes freeze/client setup) 443.769s; CPU 1345.78s; sampled RSS 709750784 bytes; verified output pages/min 36.7759; exact positive pages/min 12.9797. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 0; reported USD subtotal 0; missing reported charges 0; cost bases `{}`. Reservation amount 0; estimate amount 0.


### full276-yolo-matrix-haiku-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 270/276.

Failure categories: `{"missing_source_text": 4, "provider_output_length": 2}`.

Supplementary positive-page macro recall (172 pages): exact cells 90.46%; complete tables 80.52%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Policy `gated`; assembly `generate`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `anthropic/claude-haiku-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | 119 | 119 | 0.127591 | 0 / 119 / 0 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| authored | 156/156 | 155 | 155 | 5030/5050 | 7602/27830 | 8/24 |
| native-diagnostic | 56/0 | unscored | unscored | unscored/unscored | unscored/unscored | unscored/unscored |
| omnidoc | 64/64 | 11 | 42 | 1754/3847 | 17870/27350 | 1/24 |

Page-processing run wall (excludes freeze/client setup) 1281.41s; CPU 1288.23s; sampled RSS 795222016 bytes; verified output pages/min 12.6423; exact positive pages/min 6.36797. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 119; reported USD subtotal 0.127591; missing reported charges 0; cost bases `{"provider-reported USD": 119}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.91058s, CPU 6.57843s; 272 per-page measurement entries, request CPU total 256.538s; maximum sampled request RSS 1245454336 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.

## Historical full-r1 snapshot — invalid scan carriers

Dataset SHA-256: `68dda47aa6b0e3fd61cb751d53c7d8ae11546dea4e97ab74e6f9cac6d528332b`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells / expected | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Pages/min | Pages/API USD | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native-full-r1 | 258/276 | 18 | 96/172 | 120 | 120 | 4258/8897 | 4258/8897 | 31739/55180 | 96 | 0 | 38.3011 | unmeasured | 0 |

### native-full-r1

Scope: complete source assembly; text: source-owned; source-conserved pages: 258/276.

Failure categories: `{"invalid_table_topology": 1, "local_input_or_output_admission": 1, "other_failure": 16}`.

Supplementary positive-page macro recall (172 pages): exact cells 59.30%; complete tables 59.30%. Equal page weights; failures contribute zero; negatives remain separately scored. Primary cell/table totals and false-positive metrics remain unchanged.

Policy `native`; assembly `native`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `None`; generation `unmeasured`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| No retained remote requests | 0 | 0 | unmeasured | unmeasured |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| authored | 156/156 | 120 | 120 | 4258/5050 | 4389/27830 | 0/24 |
| native-diagnostic | 56/0 | unscored | unscored | unscored/unscored | unscored/unscored | unscored/unscored |
| omnidoc | 64/64 | 0 | 0 | 0/3847 | 27350/27350 | 0/24 |

Page-processing run wall (excludes freeze/client setup) 404.166s; CPU 1266.32s; sampled RSS 700555264 bytes; verified output pages/min 38.3011; exact positive pages/min 14.2516. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 0; reported USD subtotal 0; missing reported charges 0; cost bases `{}`. Reservation amount 0; estimate amount 0.

## Pending completed reports

- natural16-generate-haiku: interrupted after 4/16 retained pages; 12 missing pages remain failures; unresolved USD 0.30 reservation and unknown rate prevent a completed cost comparison

## Interpretation

Exact topology and character edits separate structural assembly from text agreement. Text edits are positional table text errors, not independent raster OCR CER; character inventory observations are diagnostics only. Low IoU >= 0.1 correspondences are not detection recall or AP. The stricter localization count uses IoU >= 0.5; legacy prediction boxes derive from owned text extents and can lie inside annotated table borders.

Complete tables and exact positive pages use different units and denominators: two complete tables may occupy only one exact positive page. Negative-page empty outputs can be exact without recovering a positive table. Authored DEV silver, independently annotated Omni pages, and unscored native diagnostics remain separate. A protocol screen is a predeclared DEV experiment, not a heldout estimate. Runs with different packet, OCR, generation, image or region settings are not isolated causal comparisons. Concurrent background workloads may affect timings.


## Latest comparison and priorities

Source-ID matrix Sonnet 512 completed a full 16-page attempt with 14 operational
outputs, two complete tables on one exact positive page (1/12), nine exact
topologies, 327/2333 structural cells, 227 exact text cells, and 13 localized
tables. It added nine extra tables, including one false-positive negative page.
All 44 calls were positively provider-charged, totaling USD 0.966024. Both
failed pages are independently confirmed `content_filter` finishes with no
content; neither is an observed output-length finish. No retries were performed.

The previous Sonnet anchor format retained 16 operational outputs, the same two
complete tables on one exact positive page, ten exact topologies, 419 structural
cells, and 295 exact text cells. Whitespace-anchor generation retained 15 outputs
with one invalid anchor collection, two complete tables, and 236 exact text
cells. Matrix format has not improved complete-table recovery in this screen;
its lower text recovery, extra tables, operational failures, and cost must be
considered together. These treatments also differ in settings and cannot isolate
the effect of output format.

The two dense newspaper pages contain 39/53 target tables and 1972/2333 cells.
Matrix Sonnet recovers no complete table there, with 121 structural and 59 exact
text cells. The remaining fourteen pages contain fourteen target tables and
recover two complete tables, 206 structural and 168 text cells. That subgroup
also contains four negative pages, so its exact-page count cannot be presented
as positive recovery. This is a posthoc density diagnosis; all sixteen pages
and every official target remain the primary denominator.

Priority is improving dense-page evidence and coherent table boundaries, then
checking whether image-only transcription can exceed missing-OCR source-ID
ceilings. Raising token budgets does not address the observed content-filter
failures. A new table-only vision comparator must preserve model transcription
provenance and cannot claim complete page prose or source conservation. No
current result supports a general PDF extraction quality claim.

## Corpus correction and reference review

The original full-r1 snapshot had 12 scan carriers whose transparency was
composited onto black. Their image evidence was invalid. `corpus-r2` composites
onto white before RGB wrapping, changes those 12 PDF byte hashes, and preserves
annotations and the original snapshot. Full-r1 is retained for provenance; its
metrics are not a valid natural-image baseline and cannot establish a method
improvement against the corrected full-r2 run. The authoritative natural16
screen uses the corrected input carriers.

Pixel review reported one suspected German character discrepancy: the official
annotation contains `Fuβ`, while the visible word appears to be `Fuß`. Both
characters remain distinct under the scorer's NFC policy. This is suspected
reference noise, not an adjudicated correction. References remain unchanged,
and no new equivalence rule or score adjustment was introduced.

The 80,000-character region packet run removes the earlier packet-size errors
and improves partial structural recovery, but still recovers zero complete
reference tables or exact positive pages. It also produces more extra tables
and more positional text edits than the smaller-packet baselines. These gains
and losses are reported together; operation success is not table correctness.

Complete per-page scores, family groups, source-character diagnostics, candidate
ceilings, model usage/cache-field observations, frozen runtime identities and
verification records remain in ignored `verified-evaluation.json` artifacts
under each named run. The compact report is derived from those independently
verified complete artifacts. No heldout evidence or hosted inference is used by
the report command.

## Matrix Haiku cost and density tradeoff

The completed matrix Haiku 512 arm has 16/16 operational outputs, two complete
tables on one exact positive page (1/12), ten exact topologies, 406 structural
cells, 240 exact text cells, fourteen localized tables, and three extra tables.
All four negative pages remain empty. Its 47 positively provider-charged calls
cost USD 0.0709715, versus Sonnet matrix USD 0.966024. Wall time is higher,
482.61 versus 310.61 seconds; this is a measured quality/cost/latency tradeoff,
not a throughput or generalization claim.

The posthoc split exposes an aggregate limitation. Haiku recovers only three
exact text cells and 75 structural cells on the two dense newspapers, versus
Sonnet's 59 and 121. Neither completes a dense table. On the remaining fourteen,
Haiku obtains fourteen low-threshold table correspondences with no missing or
extra tables, 331 structural cells, and 237 exact text cells; Sonnet has 206
structural and 168 text cells there. A correspondence is not detection recall
or a complete table. The cheaper arm is promising for this easier subset, but
its dense-page losses forbid extrapolating the cost advantage into broadly
accurate PDF extraction. Full sixteen-page scores remain primary.

## YOLO region proposals with matrix Sonnet 512

The completed detector-routed arm retains 15/16 operational outputs, two
complete tables on one exact positive page (1/12), twelve exact topologies,
437 structural cells, 341 exact text cells, fifteen localized tables, and three
extra tables. All four negatives remain empty. One failed positive page has an
independently confirmed `content_filter` finish. Nineteen positively charged
calls total USD 0.286868. Relative to the earlier matrix Sonnet screen, partial
text/topology coverage improves and API call count decreases; complete-table
recovery remains two, and neither dense newspaper obtains a complete table.
The dense pair has 129 structural and 104 text cells, versus 121/59 without
this detector treatment. These are partial gains, not broad table recovery.

The report preserves separate CPU worker measurements. Parent wall includes
initialization and requests, while parent CPU and RSS exclude the detector
worker. Its startup consumes 5.28 CPU seconds and has approximately 1.09 GB
sampled RSS; request CPU totals and maximum sampled request RSS appear above.
Parent and worker RSS peaks are not summed. Configuration changes and background
CPU load prevent treating elapsed-time differences as an isolated detector
speedup. No GPU or additional report-time inference is used.

## Whole-page image transcription at 1200 pixels

These controls produce table-only model transcription, with zero source-conserved
pages and no complete page prose. Sonnet retains 15/16 operational outputs,
three complete tables on two exact positive pages (2/12), fourteen exact
topologies, 408/2333 structural cells, 299/2333 exact text cells, fourteen
localized tables, and no extras. Its sixteen positively charged calls cost
USD 0.140648. Verified table-only throughput is 6.51 pages/min and 106.65
pages/API USD; CPU is 9.53 seconds, versus much higher OCR CPU in source-ID
arms. Remaining-fourteen text agreement is 274/361 cells with 455 character
edits against 3799 reference characters. The dense pair still misses 37/39
tables, yields only 25 exact text cells, and completes none.

Sonnet's sole error is invalid normalized geometry on
`pf012d6adb9592dab9a13`: returned bbox `[113, 777, 899, 1098]`, image
845×1200 pixels, display viewport
`[0, 0, 213.1199951171875, 302.3999938964844]`. Bottom 1098 violates the
required normalized 0..1000 coordinate range, while right 899 also exceeds
raw pixel width 845. These numbers do not establish a consistent raw-pixel
box; mixed units or invalid geometry remain possible. No clipping, rescaling,
reference-driven correction, or successful-table-prefix salvage was applied.
The provider finished normally, so this is a protocol/geometry failure rather
than observed output-length exhaustion.

Haiku retains 13/16 operational outputs, two complete tables on two exact
positive pages (2/12), eight exact topologies, 358/2333 structural cells,
245/2333 exact text cells, nine localized tables, and three extras. Its sixteen
positive charges total USD 0.0085084, with 6.41 verified pages/min and 1527.90
pages/API USD. Three normally completed responses fail strict parsing: two
nonrectangular/nonstring matrices and one invalid merged span. One failed
page is a negative control, so negative operational success is 3/4; zero
admitted negative false positives must not hide that failure. Dense text
recovery is one cell, with no complete table; remaining-fourteen text agreement
is 244/361 cells. Cost is low but does not compensate for weak dense recovery
and protocol failures.

Fresh vision demonstrates useful simpler-page text recovery without CPU OCR,
but the 1200-pixel whole-page treatment is inadequate for minute newspaper
content. These results motivate matched-resolution and retained-ROI controls,
not a claim that all OCR ceilings have been solved. Table-only operational
throughput is not full page-conversion throughput. All sixteen primary pages,
53 official tables, failed responses, and positive API charges remain retained.

## Detector 2×2 tiles with matrix Sonnet 512

The tiled arm retains 15/16 operational outputs and the same two complete
tables on one exact positive page (1/12). It has ten exact topologies,
431/2333 structural cells, 250/2333 exact text cells, fourteen localized tables,
and one extra table. Twenty-nine positive provider charges total USD 0.449296;
verified throughput is 2.33 pages/min and 33.39 pages/API USD. A retained
`content_filter` response fails dense page `p98d10ef50dee4b24506a`; no retry
or successful-prefix salvage is applied.

Compared with untiled YOLO, exact text cells fall from 341 to 250 and API cost
rises from USD 0.286868 to USD 0.449296, while extras fall from three to one.
The two dense pages have 108 structural and eight text cells, with no complete
table; remaining-fourteen text agreement is 242/361. Geometric proposal
improvements did not yield broad table recovery in the composed output.
All primary pages, charged attempts, and the dense failure remain scored;
changed detector/packet settings do not isolate a causal tiling effect.

## Native regional full-corpus confirmation

The completed regional native control retains 272/276 operational outputs,
versus 270/276 in the earlier whole-page native control. All four remaining
failures are unscored native diagnostics with no extracted or recognized text.
Natural cohort operational errors improve from one to zero; native diagnostic
errors improve from five to four. Positive table quality is unchanged: 120
complete authored tables, 4258 structural/text cells, 96/172 exact positive
pages, and zero complete natural tables. The natural cohort still misses all
93 reference tables. This improves operational coverage without improving
natural table accuracy.

Wall time rises from 412.10 to 443.77 seconds and process CPU from 1232.85 to
1345.78 seconds; sampled peak RSS decreases from 725.77 to 709.75 MB. Both
runs have zero hosted calls or API charges. Measurements share the documented
100 ms parent-process RSS and process CPU scope; concurrent workloads may
affect timings.

## Wave 6 completed controls

The untiled YOLO matrix Haiku512 run admits 15/16 complete outputs and retains
359 structural cells, 258 exact text cells, 12 exact topologies, and two complete
tables on one exact positive page. All 53 tables and 2333 reference cells remain
primary. The remaining fourteen pages account for every admitted table; the
two dense newspapers contribute zero tables, including one atomic page failure
with a retained provider `length` finish. One extra table creates one negative
page false positive. All 18 attempts are charged: USD 0.0234843, 3.24 operational
pages/minute and 638.72 operational pages/API USD. This cheaper expansion was
selected before its sixteen-page quality score; it is not established as the
best pipeline.

Whole-page Sonnet2048 admits 11/16 outputs, three complete tables on two exact
positive pages, 244 structural cells and 203 exact text cells. Five pages fail
locally before inference because their requests exceed the frozen 750000-byte
body admission, including both dense newspapers. The eleven requests cost
USD 0.137902; throughput is 12.87 operational pages/minute and 79.77 operational
pages/API USD. This control does not measure model readability for rejected
images. It retains the whole-page table-only model-transcription label and zero
source-conserved pages. No resizing, retries, or partial success outputs repair
these errors. The larger-image comparison changes admitted coverage as well as
image resolution, so the lower 203 versus 299 exact text cells does not isolate
a resolution effect.

The matched Haiku2048 whole-page control has the same five local body-admission
failures. Its eleven admitted outputs contain three complete tables on two
exact positive pages, 244 structural cells and 201 exact text cells, with two
extra tables and one negative-page false positive. All eleven requests carry
positive charges totaling USD 0.0087591; throughput is 11.49 operational
pages/minute and 1255.84 operational pages/API USD. Compared with Sonnet 2048,
Haiku loses two exact text cells and introduces two extras at roughly one
sixteenth the API cost. Both are table-only comparators with zero conserved
pages and unchanged full-target denominators. Local concurrency during these
waves is disclosed by the run resource records; timing differences alone do
not establish model serving performance.

## Regional vision replay contract

The separate `vision_regions` processor uses source-only fixed detector
proposals and image-only crop transcriptions. Offline verification requires
identical trusted crop composition and transcription adapter code, replays
every retained detector proposal, reparses every crop response against its
global viewport, and checks retained regional tables, combined structure, and
exact Markdown bytes. Missing crops, reordered requests, out-of-page geometry,
overlapping returned tables, and aggregate slot admissions fail verification.
A runtime crop failure remains an atomic page error; successful prefixes are
not quality-scored. Zero proposals retain `coverage=unverified`, including on
negative pages. Every intended page and table target remains in the primary
denominator. Both whole-page and crop vision galleries preserve original
rotation and label the outputs as table-only model transcription with no
source conservation. This contract does not yet assert crop-run quality.

## Full 276 fixed Haiku detector and matrix expansion

The configuration was selected before its natural 16 score and ran all 276 pages
with fresh processing and API requests, without child replay. It yields 270/276
verified and source-conserved outputs versus 272/276 for native regional control.
All 220 annotated pages,56 unscored diagnostics,249 tables and 8897 anchor cells
remain primary:166 complete tables versus 120 native,6784 structural cells and
6329 exact text cells versus 4258/4258, and 136/172 exact positive pages versus 96.
Natural 64 contributes 11/93 complete tables,1754 structural cells,1299 exact
text cells,49 localized tables,44 missing tables and one extra/negative-page
false positive. The authored cohort contributes 155/156 complete tables but
eight false-positive negative pages: six prose and two decorative pages.
An authored mixed page loses one table and adds an extra table. Those regressions
remain in the results; authored wins cannot establish broad natural accuracy.

All 119 requests have positive charges totalingUSD 0.1275912. Whole-run elapsed
time is 1281.41 seconds and parent process CPU 1288.23 seconds, with 795222016
bytes sampled parent peak RSS. Throughput is 12.64 verified pages/minute and
2116.13 verified pages/API USD. Separate CPU detector worker measurements appear
above; parent CPU/RSS excludes that worker, parent elapsed time includes it,
and RSS peaks are not summed. Concurrent root tests and agent preprocessing
may affect these CPU timings.

Four missing-source-text failures are unchanged unscored diagnostics. Two
additional atomic failures have retained `length` finishes: one natural
multiple-table newspaper and one native senate diagnostic. The complete family
inventory follows, including all unscored diagnostic families. Exact positive
page and complete-table denominators remain different units.

| Family | Pages | Errors | Complete / expected tables | Structure / cells | Exact text / cells | Extra tables | Negative FP pages |
|---|---:|---:|---:|---:|---:|---:|---:|
| authored/ruled | 12 | 0 | 12/12 | 264/264 | 264/264 | 0 | 0 |
| authored/borderless | 12 | 0 | 12/12 | 264/264 | 264/264 | 0 | 0 |
| authored/mixed | 12 | 0 | 23/24 | 508/528 | 508/528 | 1 | 0 |
| authored/multiple | 12 | 0 | 24/24 | 528/528 | 528/528 | 0 | 0 |
| authored/dense | 12 | 0 | 12/12 | 1894/1894 | 1894/1894 | 0 | 0 |
| authored/wrapped | 12 | 0 | 12/12 | 264/264 | 264/264 | 0 | 0 |
| authored/blank | 12 | 0 | 12/12 | 264/264 | 264/264 | 0 | 0 |
| authored/merged | 12 | 0 | 12/12 | 252/252 | 252/252 | 0 | 0 |
| authored/rotated | 12 | 0 | 12/12 | 264/264 | 264/264 | 0 | 0 |
| authored/cropped | 12 | 0 | 12/12 | 264/264 | 264/264 | 0 | 0 |
| authored/decorative | 12 | 0 | 0/0 | 0/0 | 0/0 | 2 | 2 |
| authored/prose | 12 | 0 | 0/0 | 0/0 | 0/0 | 6 | 6 |
| authored/ocr-carrier | 12 | 0 | 12/12 | 264/264 | 264/264 | 0 | 0 |
| native/f1040.pdf | 2 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/pdf20-simple.pdf | 1 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/usrguide.pdf | 19 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/bill-hr815.pdf | 19 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/mhlw-doc.pdf | 2 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/bunka-kokugo-series-019-p4.pdf | 1 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/patent-us223898.pdf | 4 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/wdl6812-manuscript.pdf | 2 | 1 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/nics-background-checks-2015-11.pdf | 1 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/senate-expenditures.pdf | 1 | 1 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/pdfium-type3.pdf | 1 | 1 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/pdfium-smask-blend.pdf | 1 | 1 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/pdfium-jpx-lzw.pdf | 1 | 1 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| native/pdfium-links-highlights-annots.pdf | 1 | 0 | 0/0 | 0/0 | 0/0 | 0 | 0 |
| omni/multiple-table | 16 | 1 | 7/69 | 875/2921 | 610/2921 | 0 | 0 |
| omni/single-table | 24 | 0 | 4/24 | 879/926 | 689/926 | 0 | 0 |
| omni/no-table | 24 | 0 | 0/0 | 0/0 | 0/0 | 1 | 1 |

The 64 natural pages include 16 earlier-screen pages and 48 additional DEV pages.
This posthoc split retains 64 natural pages as the primary cohort. It is not
a heldout-silver test or an independently selected deployment claim.

| Natural diagnostic | Pages | Complete / tables | Exact text / cells | Errors | Extra tables |
|---|---:|---:|---:|---:|---:|
| Earlier screen16 | 16 | 2/53 | 258/2333 | 1 | 1 |
| Additional DEV48 | 48 | 9/40 | 1041/1514 | 0 | 0 |

## Hybrid reporting contract

The separate hybrid processor retains native and crop-vision children plus a
complete parent composition. Verification replays native vector quarantine and
its warnings, original native table boxes, and the exact raw-to-filtered detector
exclusion policy. Both nested children must equal their retained results and
pass the existing complete source / strict crop-response verifiers. The trusted
hybrid helper then rebuilds tables, original-word ledger, superseded words, all
accounting flags, and exact complete Markdown. Parent composition, every copied
field, and retained structure must match that replay. Accepted transcribed text
has empty original source IDs and explicit model provenance; conserved-page
counts use the actual helper flag, which remains true only when no model tables
are accepted. Failed parents retain child evidence but contribute no successful
prefix tables. Requests and actual model usage are audited in the fixed vision
child directory, and detector worker measurements remain separate from parent
CPU/RSS. Gallery labels preserve the mixed provenance and original rotation.
These checks prepare future hybrid runs; they do not assert quality before
those runs complete.

## Matched Haiku512 versus Haiku1024 source-ID images

The 1024-pixel generation-image arm retains 14/16 outputs versus 15/16 at 512,
336 versus 359 structural cells,247 versus 258 exact text cells,12 versus 14
localized tables, and two complete tables on one exact positive page in both
arms. All 53 tables and 2333 anchor cells remain primary. Both retain one extra
table and one negative false-positive page. Both dense pages still produce
zero admitted tables.

The larger-image arm has two atomic errors from the frozen model/input
admission, each after a retained earlier normal-stop call. These are not
output-token exhaustion. Successful prefixes remain unscored. All17 requests
have positive charges totalingUSD 0.0211337; throughput is 3.57 verified
pages/minute and 662.45 verified pages/API USD. The 512 arm costsUSD 0.0234843
for 18 requests and 3.24 pages/minute. Lower cost and fewer admitted outputs
are related here; this is not evidence that larger images improve quality.
The admission change prevents isolating image resolution from coverage.

## OCR300 and direct vision controls

The combined YOLO/whitespace OCR300/arrays/1024-pixel Haiku arm retains
15/16 source-conserved outputs, three complete tables on two exact positive
pages, and 387/2333 exact cells. The failed page hits a local frozen input
admission after an earlier normal-stop call; its partial output contributes
no quality. All seventeen charges remain included: USD 0.0166027, 2.60
operational pages/minute and 903.47 operational pages/API USD. The arm
changes OCR source resolution, image size and evidence representation together.
Its improvement over the 512-pixel arm cannot identify a DPI-only effect.
The [offline source inventory bounds](p002-source-inventory-ceilings.md) rise
from 1238 to 1880 literal-feasible anchors, chiefly on the dense pair.

JPEG50 whole-page Sonnet2048 completes all sixteen pages and recovers
540 exact cells, seven complete tables on two exact positive pages, and
twenty exact topologies. Both extra tables occur on dense positive pages;
all four negatives remain correct. Unlike JPEG90, all sixteen frozen
requests fit admission. Dense pages recover 247 cells but still miss
33/39 tables. The remaining fourteen retain all fourteen table structures
and 293/361 exact cells. This table-only transcription comparator does
not conserve source text or recover page prose.

JPEG50 Haiku2048 retains 14/16 atomic outputs, 208 exact cells and two
complete tables on two exact positive pages. Its two errors both have
normal-stop responses: an out-of-range normalized box and nonempty covered
merge slots. Four extra tables include one false-positive negative page.
All sixteen provider charges are retained; these failures are not token
budget exhaustion. Dense pages recover zero exact cells.

Sonnet detector crops1024 completes all sixteen pages with 982 exact cells,
25 exact topologies and five complete tables on three exact positive
pages. There are no extra tables or negative-page false positives. Dense
pages recover 692/1972 cells and one complete table, while 26/39 tables
remain missing. Remaining fourteen recover 290/361 cells, all fourteen
table structures, and four complete tables. Nineteen charges total
USD 0.230508, below whole-page Sonnet2048 JPEG50's USD 0.252816.
Crop success includes zero-proposal pages with coverage explicitly
unverified; successful execution never establishes detector recall.

These controls favor crop transcription for dense cell recovery in this
DEV screen, while complete-table quality remains mixed. The full sixteen
pages remain primary; the dense/remaining split is posthoc. Complete tables
and exact positive pages count different units: seven complete tables
can coexist with only two exact positive pages. No reference text enters
requests, source extraction or routing.

## Matched Haiku crop control

Haiku detector crops1024 retains 14/16 atomic outputs and 687/2333 exact
cells, compared with 208 in its whole-page2048 JPEG50 control. Four
complete tables occur on three exact positive pages, and fourteen tables
have exact topology. Three extra tables all occur on dense positives;
all four negative pages remain correct. The dense pair recovers 416 cells
but no complete table; remaining fourteen recover 271 cells and four
complete tables. Thirty-three of fifty-three reference tables remain missing.

Two normal-stop crop responses fail strict parsing: an out-of-range
normalized box and nonempty covered merge slots. Both pages contribute
zero quality, including any successful earlier region. All nineteen
provider charges remain included: USD 0.0090984, 8.57 operational pages/minute
and 1538.73 operational pages/API USD. This is a table-only model transcription
arm, with zero source-conserved pages and no page-prose claim.

The matched crops improve both models' dense cell recovery. Haiku is cheaper
and faster, while Sonnet retains all sixteen outputs, more exact topology
(25 versus 14), more exact cells (982 versus 687), and zero extra tables.
These are fixed DEV comparisons, without selecting responses or repairing
boxes, merged spans, text, or detector coverage against references.

## Whole-page Opus and supplementary macro recalls

Opus2048 JPEG50 completes all sixteen pages but recovers 300/2333 exact
cells and three complete tables on two exact positive pages. Fourteen
tables have exact topology; six extras all occur on the dense positives.
Remaining fourteen recover 293/361 exact cells with all fourteen table
structures, while the dense pair recovers seven cells and no complete
table, missing 37/39. All sixteen charges total USD 0.462612: 6.84
operational pages/minute and 34.59 operational pages/API USD. It improves
neither quality nor cost over Sonnet2048 JPEG50 in this fixed screen.

Supplementary positive-page macro recalls now give equal weight to each
of the twelve positive pages. A page's exact-cell recall is its exact
anchors divided by its reference anchors; complete-table recall is its
complete tables divided by its reference tables. Failed or missing positive
pages contribute zero. Four negatives remain in separate error and false-positive
metrics. This does not replace the primary 53-table/2333-anchor totals or
penalize extras; both totals and false positives remain necessary.

The Opus macro exact-cell recall is 62.01%, despite only 12.86% micro
recall, because its dense-page loss carries less weight in the macro.
Its macro complete-table recall is 20.83%. This describes page weighting,
not an improvement or a selected evaluation subset. Tests distinguish a
100-cell missed page from a one-cell recovered page, retain a failed
positive at zero even with retained partial tables, and exclude negatives
and unscored diagnostics from the macro only.

## Fixed-edge OCR with tiled detector fusion

The predeclared 2x2/larger-containment YOLO, whitespace fixed2048 OCR,
arrays/1024-image Haiku arm retains 15/16 source-conserved outputs,
285/2333 exact cells, three complete tables on two exact positive pages,
and eleven exact topologies. One extra table occurs on a dense positive;
all negatives remain correct. Thirty-nine reference tables remain missing.
The sole error is a frozen model/input admission, with no returned call
on that page. All twenty-seven charges total USD 0.0242193, for 2.84
operational pages/minute and 619.34 operational pages/API USD.

The dense pair recovers twelve exact cells and no complete table; remaining
fourteen recover 273 cells and three complete tables. Supplementary
positive-page macro recall is 51.53% exact cells and 20.83% complete tables.
All sixteen cached sources are measured: the literal inventory ceiling
is 861/2333 cells (dense 569, remaining 292), versus 1880 under OCR300.
Fixed2048 resolves the large dense pages at only 90.02 and 94.33 DPI.
These source bounds and the quality loss favor retaining adequate source
resolution for large pages. Tiling, fusion and OCR resolution change
together here; this comparison does not isolate the effect of fusion.

## Matched rowwrap prompt control

The fixed rowwrap prompt treatment retains 15/16 source-conserved outputs
and recovers 231/2333 exact cells, versus 258 for the otherwise matched
YOLO/Haiku512 base prompt. Complete tables remain two on one exact positive
page, exact topology remains twelve, and the one negative false-positive
page persists. Both dense pages contribute zero exact cells. The p98
newspaper error retains finish_reason=length with missing response content;
this classification comes from the provider response, not the generic
truncation message. Atomic output and all primary targets remain unchanged.

All eighteen charges total USD 0.0252378, with 3.22 operational pages/minute
and 594.35 operational pages/API USD. Supplementary positive-page macro
recall is 47.92% exact cells and 12.50% complete tables. This single frozen
prompt treatment gives no observed quality gain; it does not measure the
yet-unfinished column-prompt or source-derived row-context controls.

## Matched column prompt control

The fixed columns prompt retains 16/16 source-conserved outputs, 332/2333
exact cells, 545 structural cells and twelve exact topologies. Two complete
tables remain on one exact positive page. There are no extra tables or
negative-page false positives. Thirty-eight reference tables remain missing,
including 37/39 on the dense pair. All nineteen charges total USD 0.0273898,
for 3.38 operational pages/minute and 584.16 operational pages/API USD.
Supplementary positive-page macro recall is 48.82% exact cells and 12.50%
complete tables. No operational failures remain; p98 completes strictly.

Compared with the matched base512 arm, the primary exact-cell count rises
by 74 and one additional page completes, while the negative false positive
disappears. Dense pages gain 101 cells, offset by 27 fewer exact cells on
the remaining fourteen (231 versus 258). Complete tables and exact positive
pages do not improve. Rowwrap also retains 231 cells on the remaining group
but zero on the dense pair. Thus the columns prompt shows a modest dense
recovery improvement in this single frozen trial, with a smaller-page tradeoff,
and remains well below direct crop transcription. No retry, response selection
or reference-driven prompt adjustment contributes to these scores.

## Ordinal source-index control

The fixed ordinal control retains 16/16 source-conserved outputs and
311/2333 exact cells, 477 structural cells and twelve exact topologies.
Two complete tables occur on one exact positive page. The negative false
positive persists; thirty-seven reference tables remain missing. Dense
pages recover 80 cells and no complete table, while remaining fourteen
recover 231 cells and two complete tables. All nineteen charges total
USD 0.0247681, with 3.51 operational pages/minute and 645.99 operational
pages/API USD. Supplementary positive-page macro recall is 48.63% exact
cells and 12.50% complete tables. No failed outputs remain.

The adapter freezes source ordering once and expands returned integer
positions locally into original source IDs before unchanged strict matrix
validation. It cannot transcribe missing OCR strings or invent values.
All ordinal, matrix, evidence and frontier dependency bytes match trusted
current sources. The reporter initially refused a locally stale evidence
benchmark module; synchronizing its reviewed CPU/provenance diagnostics
restored exact identity without weakening the parser gate.

The control gains 53 exact cells over base512 and resolves its dense
length failure, but recovers fewer cells than the columns prompt (311
versus 332) and retains the negative false positive that columns avoids.
These single frozen arms do not establish a universal preference for
integer positions over source IDs. Neither improves complete-table or
exact-positive-page quality, and both remain below crop transcription
on this fixed DEV screen.

## Gated ordinal control

The independently configured semantic gate plus ordinal generation arm
retains 15/16 source-conserved outputs and 232/2333 exact cells, 314
structural cells and nine exact topologies. Two complete tables remain
on one exact positive page. Seven extra tables occur on positive pages;
all four negatives remain correct. Forty reference tables remain missing.
Both dense pages contribute zero exact cells. The p98 newspaper retains
an actual provider length finish after earlier successful calls; its
entire page output contributes zero quality.

All thirty-five returned charges, including the failed page's gate and
generation calls, total USD 0.02778538. Throughput is 3.06 operational
pages/minute and 539.85 operational pages/API USD. Supplementary positive-page
macro recall is 41.20% exact cells and 12.50% complete tables. The retained
model breakdown separates Perplexity gate and Haiku generation calls.

Compared with ungated ordinal generation, the negative false positive
disappears, but the arm loses 79 exact cells, one operational page and
three exact topologies. Positive-page extra fragments rise from zero to
seven. Complete-table and exact-positive-page quality stay unchanged.
The gate therefore trades negative-page precision for positive-page
coverage/assembly in this screen; zero negative errors alone is insufficient
to choose it as the better complete pipeline. The fixed full-corpus gated
control remains a separately configured expansion, without changing
thresholds against these references.


## Legacy hybrid Sonnet and request identity

The legacy renderer-v1 Sonnet hybrid run produces 15/16 verified atomic outputs,
289/2333 exact cells, 361 structural cells, fourteen exact topologies and four
complete tables on three exact positive pages. All four negatives remain correct;
all 39 dense reference tables remain missing. Five outputs conserve source text
because no model tables were accepted; other successful outputs have explicit
mixed provenance. All nineteen reported charges total USD 0.222808, including
the failed page, at 4.00 operational pages/minute and 67.32 pages/API USD.
Supplementary positive-page macro recall is 60.43% cells and 25.00% tables.

The standalone crop run's 982 exact cells versus hybrid's 289 must not be
attributed to the hybrid architecture. A source-only audit, conducted without
loading references, finds identical detector proposals and crop descriptors on
all sixteen pages, no native exclusions, and byte-identical retained model
requests for all nineteen crops. Eight response contents and eight per-region
canonical table outputs match exactly; the other fresh responses differ.
The dense p98 page succeeds standalone but the hybrid's fresh responses produce
cross-crop overlap. Its entire page is rejected atomically despite both responses
ending normally, losing all 692 dense exact cells. The other fourteen pages differ
by only one exact cell (290 versus 289). Dense p1 has zero proposals in both runs.
Hybrid source inventories contain 1,953 and 1,687 words on those two pages, but
those inventories are accounting inputs, absent from the image-only requests.
The standalone comparator has no source inventory. The ignored source-only audit
is retained at `regions-audit/hybrid-sonnet-request-identity.json`.

The frozen old helper's exact reviewed hash selects renderer v1 during verification.
Renderer v2 fixes source-free table/footer ties and geometric table ordering;
model data cannot choose a renderer. Unknown hashes fail verification. This
ordering correction changes Markdown placement, not canonical table quality;
new frozen hybrid runs use v2 and remain separately labeled.

## Fresh four-worker whole-page control

Four-worker Haiku2048/JPEG50 yields 13/16 verified table-only outputs, 216/2333
exact cells, 261 structural cells, nine exact topologies and four complete tables
on three exact positive pages. Three extra tables include one negative-page false
positive. Three normal-stop responses fail strict validation: an out-of-range
normalized bbox, invalid merged-span bounds, and a nonrectangular literal matrix.
There are no retries or successful partial outputs. All sixteen charges total
USD 0.0110033, giving 30.93 operational pages/minute and 1,181.46 pages/API USD.
Supplementary positive-page macro recall is 43.01% cells and 25.00% tables.

All sixteen request bodies match the serial control byte-for-byte. This single
fresh stochastic replicate does not establish that concurrency caused its quality
difference from serial (14/16 outputs, 208 cells and two complete tables).
Page-processing wall is 25.217 seconds versus serial's 67.562 seconds, excluding
freeze/client setup and command startup in both. Actual parent process CPU is
17.939 seconds. Concurrent per-page CPU intervals overlap and cannot be summed;
their 67.538-second sum is not whole-run process CPU.

## Smaller fixed crop controls

Haiku768/512/400 pixels with JPEG90 each verify all sixteen intended pages,
using the same detector proposals and strict parser. Every run retains nineteen
charged fresh calls. These are table-only model transcriptions, without source
conservation. All four negatives remain correct in each arm.

| Crop edge | Exact cells / 2333 | Structural cells | Exact topologies | Complete tables / 53 | Extra tables | API USD | Pages/min | Pages/API USD | Positive macro cells | Positive macro tables |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 768 | 403 | 533 | 13 | 3 | 0 | 0.0086524 | 9.87 | 1849.20 | 59.10% | 20.83% |
| 512 | 290 | 364 | 12 | 2 | 1 | 0.0080819 | 9.80 | 1979.73 | 58.29% | 16.67% |
| 400 | 225 | 359 | 12 | 3 | 2 | 0.0089904 | 8.49 | 1779.68 | 46.49% | 20.83% |

All three runs produce two exact positive pages; complete-table counts have a
different denominator. The 768 arm recovers 110 dense cells and 293 on the other
fourteen pages. Smaller images reduce observed exact-cell recovery versus the
1024 baseline's 687 cells, while eliminating its two strict format failures in
these fresh replicates. Higher operational coverage alone does not imply higher
quality. The 400 arm is slower and costs more than 512 in this sample; image size
alone does not determine stochastic output length or service latency. No prompts,
thresholds or reference-selected routing were changed. All sixteen pages and the
53-table/2,333-cell primary denominators remain fixed.


## Hybrid Haiku with corrected renderer

The fresh renderer-v2 hybrid Haiku run produces 14/16 verified atomic outputs,
289/2333 exact cells, 339 structural cells and eleven exact topologies. Three
complete tables occur on two exact positive pages. Four outputs conserve source
text because no model tables are accepted; other successes carry mixed native
and model provenance with complete source accounting. One extra table is a
negative-page false positive, and 41 reference tables remain missing. The dense
pair contributes zero; all 289 recovered cells are on the remaining fourteen.

Two normal-stop crop responses cause atomic child failure: p98 has invalid merged
span bounds; p9f92 has an out-of-range normalized bbox. Failed parent pages
contribute zero quality even where sibling crop calls succeeded. All nineteen
reported charges, including those pages, total USD 0.0091259. Throughput is 4.47
operational pages/minute and 1,534.10 pages/API USD. Supplementary positive-page
macro recall is 56.06% cells and 20.83% complete tables. Every frozen runtime
dependency matches trusted current bytes, and verified Markdown uses renderer v2.

The standalone Haiku1024 crop comparator recovered 687 cells in a different fresh
response sample, with its own two strict failures. The Sonnet request identity
audit above demonstrates how identical input requests can yield substantial
page-atomic quality differences; this Haiku result likewise cannot isolate a
causal hybrid-versus-transcription quality effect. The separately frozen full276
hybrid expansion will test broader coverage without changing the natural16
references, admissions, or parser.
