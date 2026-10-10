# P002 natural-PDF generalization progress

Frozen runs with independently verified successful states, exact Markdown and explicit text provenance appear below. Missing/error pages remain in every scored denominator. Protocol groups use different frozen datasets and must not be pooled into one quality score.

## Authoritative natural16 DEV screen

Dataset SHA-256: `68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Pages/min | Pages/API USD | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| natural16-whole-reviewed | 9/16 | 7 | 0/12 | 0 | 0 | 2/2333 | 0 | 16804/16640 | 1 | 0 | 2.74509 | 181.398 | 0.0496148 |
| natural16-regions-reviewed | 9/16 | 7 | 0/12 | 0 | 0 | 2/2333 | 0 | 16804/16640 | 1 | 0 | 2.62157 | 251.199 | 0.0358282 |
| natural16-regions-80k | 16/16 | 0 | 0/12 | 0 | 1 | 320/2333 | 4 | 25948/16640 | 3 | 5 | 3.6026 | 109.434 | 0.146207 |
| natural16-raster-select-512 | 16/16 | 0 | 0/12 | 0 | 3 | 418/2333 | 92 | 25511/16640 | 5 | 5 | 3.91377 | 111.17 | 0.143924 |
| natural16-generate-sonnet | 16/16 | 0 | 1/12 | 2 | 10 | 419/2333 | 295 | 14588/16640 | 15 | 7 | 2.59737 | 13.3194 | 1.20126 |
| natural16-generate-whitespace | 15/16 | 1 | 1/12 | 2 | 7 | 447/2333 | 236 | 16144/16640 | 13 | 7 | 2.15636 | 12.0499 | 1.24482 |
| natural16-matrix-sonnet-512 | 14/16 | 2 | 1/12 | 2 | 9 | 327/2333 | 227 | 15229/16640 | 13 | 9 | 2.7044 | 14.4924 | 0.966024 |
| natural16-matrix-haiku-512 | 16/16 | 0 | 1/12 | 2 | 10 | 406/2333 | 240 | 14902/16640 | 14 | 3 | 1.98919 | 225.443 | 0.0709715 |
| natural16-yolo-matrix-sonnet-512 | 15/16 | 1 | 1/12 | 2 | 12 | 437/2333 | 341 | 13543/16640 | 15 | 3 | 3.88937 | 52.2889 | 0.286868 |

### natural16-whole-reviewed

Scope: complete source assembly; text: source-owned; source-conserved pages: 9/16.

Failure categories: `{"local_input_or_output_admission": 7}`.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 0/14 | 0/10 | 0 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `unmeasured`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 1 | 1 | 0.039142 | 0 / 1 / 0 |
| perplexity/pplx-decider-v1.1-27b | 16 | 16 | 0.0104728 | 0 / 0 / 16 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 0 | 2/2333 | 16804/16640 | 0/4 |

Whole-run wall 196.715s; CPU 374.167s; sampled RSS 588820480 bytes; verified output pages/min 2.74509; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 17; reported USD subtotal 0.0496148; missing reported charges 0; cost bases `{"provider-reported USD": 17}`. Reservation amount 0; estimate amount 0.


### natural16-regions-reviewed

Scope: complete source assembly; text: source-owned; source-conserved pages: 9/16.

Failure categories: `{"local_input_or_output_admission": 7}`.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 0 |
| remaining_fourteen | 0/14 | 0/10 | 0 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `unmeasured`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 1 | 1 | 0.028466 | 0 / 1 / 0 |
| perplexity/pplx-decider-v1.1-27b | 24 | 24 | 0.0073622 | 0 / 0 / 24 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 0 | 2/2333 | 16804/16640 | 0/4 |

Whole-run wall 205.984s; CPU 342.123s; sampled RSS 636424192 bytes; verified output pages/min 2.62157; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 25; reported USD subtotal 0.0358282; missing reported charges 0; cost bases `{"provider-reported USD": 25}`. Reservation amount 0; estimate amount 0.


### natural16-regions-80k

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 2 |
| remaining_fourteen | 0/14 | 0/10 | 2 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 5 | 5 | 0.122232 | 0 / 5 / 0 |
| perplexity/pplx-decider-v1.1-27b | 56 | 56 | 0.0239754 | 0 / 0 / 56 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 1 | 320/2333 | 25948/16640 | 0/4 |

Whole-run wall 266.475s; CPU 359.703s; sampled RSS 660725760 bytes; verified output pages/min 3.6026; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 61; reported USD subtotal 0.146207; missing reported charges 0; cost bases `{"provider-reported USD": 61}`. Reservation amount 0; estimate amount 0.


### natural16-raster-select-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

Posthoc density diagnostic only; all sixteen pages and all targets remain primary. The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.

| Posthoc group | Complete tables / expected | Exact positive pages / positive pages | Exact text cells |
|---|---:|---:|---:|
| two_dense_newspapers | 0/39 | 0/2 | 2 |
| remaining_fourteen | 0/14 | 0/10 | 90 |

Policy `gated`; assembly `select`; configured gate/selector `perplexity/pplx-decider-v1.1-27b`; review `anthropic/claude-sonnet-5.5`; generation `anthropic/claude-sonnet-5.5`. Actual request models are listed below; a configured default does not prove it was called.

| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | Cached prompt observations: positive / zero / missing |
|---|---:|---:|---:|---:|
| anthropic/claude-sonnet-5.5 | 5 | 5 | 0.121322 | 0 / 5 / 0 |
| perplexity/pplx-decider-v1.1-27b | 57 | 57 | 0.0226022 | 0 / 0 / 57 |

Per-model usage/cost are returned-call observations, including calls on failed pages. All-attempt ledger costs in the summary include failures; per-model failed-attempt charges remain unattributed when unavailable. Provider cache fields are literal observations, with absent fields marked missing and no local inference cache.

| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | Text edits / reference chars | Negative false-positive pages |
|---|---:|---:|---:|---:|---:|---:|
| omnidoc | 16/16 | 0 | 3 | 418/2333 | 25511/16640 | 0/4 |

Whole-run wall 245.288s; CPU 327.633s; sampled RSS 633634816 bytes; verified output pages/min 3.91377; exact positive pages/min 0. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 62; reported USD subtotal 0.143924; missing reported charges 0; cost bases `{"provider-reported USD": 62}`. Reservation amount 0; estimate amount 0.


### natural16-generate-sonnet

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

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

Whole-run wall 369.605s; CPU 314.827s; sampled RSS 598724608 bytes; verified output pages/min 2.59737; exact positive pages/min 0.162335. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 47; reported USD subtotal 1.20126; missing reported charges 0; cost bases `{"provider-reported USD": 47}`. Reservation amount 0; estimate amount 0.


### natural16-generate-whitespace

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"invalid_anchor_collection": 1}`.

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

Whole-run wall 417.369s; CPU 344.472s; sampled RSS 651649024 bytes; verified output pages/min 2.15636; exact positive pages/min 0.143758. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 49; reported USD subtotal 1.24482; missing reported charges 0; cost bases `{"provider-reported USD": 49}`. Reservation amount 0; estimate amount 0.


### natural16-matrix-sonnet-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 14/16.

Failure categories: `{"provider_content_filter": 2}`.

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

Whole-run wall 310.605s; CPU 360.122s; sampled RSS 647983104 bytes; verified output pages/min 2.7044; exact positive pages/min 0.193171. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 44; reported USD subtotal 0.966024; missing reported charges 0; cost bases `{"provider-reported USD": 44}`. Reservation amount 0; estimate amount 0.


### natural16-matrix-haiku-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 16/16.

Failure categories: `{}`.

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

Whole-run wall 482.609s; CPU 393.46s; sampled RSS 639729664 bytes; verified output pages/min 1.98919; exact positive pages/min 0.124324. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 47; reported USD subtotal 0.0709715; missing reported charges 0; cost bases `{"provider-reported USD": 47}`. Reservation amount 0; estimate amount 0.


### natural16-yolo-matrix-sonnet-512

Scope: complete source assembly; text: source-owned; source-conserved pages: 15/16.

Failure categories: `{"provider_content_filter": 1}`.

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

Whole-run wall 231.4s; CPU 304.83s; sampled RSS 612708352 bytes; verified output pages/min 3.88937; exact positive pages/min 0.259291. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 19; reported USD subtotal 0.286868; missing reported charges 0; cost bases `{"provider-reported USD": 19}`. Reservation amount 0; estimate amount 0.

Separate CPU detector worker: initialization wall 2.56802s, CPU 5.28494s; 16 measured requests, request CPU total 14.4786s; maximum sampled request RSS 1189687296 bytes. Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. Parent elapsed time includes initialization and requests; RSS peaks are not summed.

## Corrected full corpus-r2 DEV baseline

Dataset SHA-256: `e0a86f712fb7eda5f5ceb64fa19eb72c055694106a006b086fd9d09284295537`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Pages/min | Pages/API USD | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native-full-r2 | 270/276 | 6 | 96/172 | 120 | 120 | 4258/8897 | 4258 | 31739/55180 | 96 | 0 | 39.3111 | unmeasured | 0 |
| native-regional-full-r2 | 272/276 | 4 | 96/172 | 120 | 120 | 4258/8897 | 4258 | 31739/55180 | 96 | 0 | 36.7759 | unmeasured | 0 |

### native-full-r2

Scope: complete source assembly; text: source-owned; source-conserved pages: 270/276.

Failure categories: `{"invalid_table_topology": 1, "local_input_or_output_admission": 1, "other_failure": 4}`.

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

Whole-run wall 412.098s; CPU 1232.85s; sampled RSS 725770240 bytes; verified output pages/min 39.3111; exact positive pages/min 13.9773. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 0; reported USD subtotal 0; missing reported charges 0; cost bases `{}`. Reservation amount 0; estimate amount 0.


### native-regional-full-r2

Scope: complete source assembly; text: source-owned; source-conserved pages: 272/276.

Failure categories: `{"missing_source_text": 4}`.

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

Whole-run wall 443.769s; CPU 1345.78s; sampled RSS 709750784 bytes; verified output pages/min 36.7759; exact positive pages/min 12.9797. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 0; reported USD subtotal 0; missing reported charges 0; cost bases `{}`. Reservation amount 0; estimate amount 0.

## Historical full-r1 snapshot — invalid scan carriers

Dataset SHA-256: `68dda47aa6b0e3fd61cb751d53c7d8ae11546dea4e97ab74e6f9cac6d528332b`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Pages/min | Pages/API USD | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native-full-r1 | 258/276 | 18 | 96/172 | 120 | 120 | 4258/8897 | 4258 | 31739/55180 | 96 | 0 | 38.3011 | unmeasured | 0 |

### native-full-r1

Scope: complete source assembly; text: source-owned; source-conserved pages: 258/276.

Failure categories: `{"invalid_table_topology": 1, "local_input_or_output_admission": 1, "other_failure": 16}`.

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

Whole-run wall 404.166s; CPU 1266.32s; sampled RSS 700555264 bytes; verified output pages/min 38.3011; exact positive pages/min 14.2516. Measurement: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses. Per-run concurrency 1; logical CPUs 8.

Ledger attempts 0; reported USD subtotal 0; missing reported charges 0; cost bases `{}`. Reservation amount 0; estimate amount 0.

## Pending completed reports

- natural16-generate-haiku: interrupted after 4/16 retained pages; 12 missing pages remain failures; unresolved USD 0.30 reservation and unknown rate prevent a completed cost comparison
- YOLO matrix and image-only vision transcription controls: queued; different settings are separate treatments

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
