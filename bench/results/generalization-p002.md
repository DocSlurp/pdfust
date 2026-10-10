# P002 natural-PDF generalization progress

Only completed runs with verified frozen sources, complete retained states, exact Markdown and source ownership appear below. Missing/error pages remain in every scored denominator. Protocol groups use different frozen datasets and must not be pooled into one quality score.

## Authoritative natural16 DEV screen

Dataset SHA-256: `68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| natural16-whole-reviewed | 9/16 | 7 | 0/12 | 0 | 0 | 2/2333 | 0 | 16804/16640 | 1 | 0 | 0.0496148 |
| natural16-regions-reviewed | 9/16 | 7 | 0/12 | 0 | 0 | 2/2333 | 0 | 16804/16640 | 1 | 0 | 0.0358282 |
| natural16-regions-80k | 16/16 | 0 | 0/12 | 0 | 1 | 320/2333 | 4 | 25948/16640 | 3 | 5 | 0.146207 |

### natural16-whole-reviewed

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

## Corrected full corpus-r2 DEV baseline

Dataset SHA-256: `e0a86f712fb7eda5f5ceb64fa19eb72c055694106a006b086fd9d09284295537`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native-full-r2 | 270/276 | 6 | 96/172 | 120 | 120 | 4258/8897 | 4258 | 31739/55180 | 96 | 0 | 0 |

### native-full-r2

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

## Historical full-r1 snapshot — invalid scan carriers

Dataset SHA-256: `68dda47aa6b0e3fd61cb751d53c7d8ae11546dea4e97ab74e6f9cac6d528332b`.

| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | Structure cells / expected | Exact text cells | Text edits / reference chars | IoU >= 0.5 tables | Extra tables | Effective API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native-full-r1 | 258/276 | 18 | 96/172 | 120 | 120 | 4258/8897 | 4258 | 31739/55180 | 96 | 0 | 0 |

### native-full-r1

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

- natural16-generate-sonnet: queued/running; complete report not yet retained

## Interpretation

Exact topology and character edits separate structural assembly from text agreement. Text edits are positional table text errors, not independent raster OCR CER; character inventory observations are diagnostics only. Low IoU >= 0.1 correspondences are not detection recall or AP. The stricter localization count uses IoU >= 0.5; legacy prediction boxes derive from owned text extents and can lie inside annotated table borders.

Negative-page empty outputs can be exact without recovering a positive table. Authored DEV silver, independently annotated Omni pages, and unscored native diagnostics remain separate. A protocol screen is a predeclared DEV experiment, not a heldout estimate. Runs with different packet, OCR, generation, image or region settings are not isolated causal comparisons. Concurrent background workloads may affect timings.


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
