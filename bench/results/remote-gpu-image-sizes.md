# Fresh remote DEV image sizes

Fresh PDF source crops at 128/256/384/400/448/500/640 pixels, independently encoded as RGB8, gray8 and four-level two-bit PNGs. Each arm retains 24 authored supplied-region decisions (16 known, 8 ambiguous); 504 planned inputs per model. These are correlated treatments of the same 24 logical pages, not independent cases or full-page extraction scores.

Every fresh PNG was re-rendered from its frozen source PDF and literal state/questions verified before DEV references were read. All source and returned request hashes were checked. Verification establishes transport identity, not a model's actual use of images. Missing, failed and unattempted inputs stay in planned denominators. Native response probabilities are not correctness calibration.

Across included runs: 2016/2016 valid inputs; 0/672 ambiguous abstentions. Changing size/color is not an established remedy for insufficient-evidence decisions.

## Cloudflare/clef-flash

State: complete; 504/504 valid fresh inputs. Baseline: `flash-l015` (complete).

| Arm | Valid/planned | Known correct | Wrong known | Known abstain | Ambiguous abstain | Schema/worker errors | Regions/min | CPU s | RSS MiB | GPU alloc/reserved MiB | Marginal USD est. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| original fresh-gray-1024 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 680.623 | 3.989 | 18796.238 | 18341.221/18478.000 | 0.001 |
| original fresh-gray-512 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 912.696 | 2.797 | 18796.238 | 18286.152/18478.000 | 0.001 |
| original fresh-gray-768 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 786.128 | 3.239 | 18796.238 | 18303.213/18478.000 | 0.001 |
| original fresh-lowbit-1024 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 674.841 | 3.985 | 18796.238 | 18341.342/18478.000 | 0.001 |
| original fresh-lowbit-512 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 901.307 | 2.795 | 18796.238 | 18286.258/18478.000 | 0.001 |
| original fresh-lowbit-768 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 779.129 | 3.221 | 18796.238 | 18303.326/18478.000 | 0.001 |
| original fresh-rgb-1024 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 662.247 | 4.040 | 18796.238 | 18341.221/18478.000 | 0.001 |
| original fresh-rgb-512 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 672.631 | 3.429 | 18796.238 | 18286.152/18362.000 | 0.001 |
| original fresh-rgb-768 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 763.432 | 3.323 | 18796.238 | 18303.213/18478.000 | 0.001 |
| fresh-rgb-128 | 24/24 | 8/16 | 8 | 0 | 0/8 | 0/0 | 664.902 | 3.360 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-rgb-256 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 946.595 | 2.748 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-rgb-384 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 946.346 | 2.787 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-rgb-400 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 938.937 | 2.827 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-rgb-448 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 947.303 | 2.737 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-rgb-500 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 914.165 | 2.951 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-rgb-640 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 866.443 | 3.113 | 18797.047 | 18294.328/18512.000 | 0.001 |
| fresh-gray-128 | 24/24 | 8/16 | 8 | 0 | 0/8 | 0/0 | 950.218 | 2.731 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-gray-256 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 947.603 | 2.763 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-gray-384 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 947.940 | 2.786 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-gray-400 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 941.619 | 2.819 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-gray-448 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 948.887 | 2.750 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-gray-500 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 924.092 | 2.897 | 18797.047 | 18286.152/18512.000 | 0.001 |
| fresh-gray-640 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 874.729 | 3.063 | 18797.047 | 18294.328/18512.000 | 0.001 |
| fresh-lowbit-128 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 950.107 | 2.716 | 18797.047 | 18286.258/18512.000 | 0.001 |
| fresh-lowbit-256 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 950.227 | 2.758 | 18797.047 | 18286.258/18512.000 | 0.001 |
| fresh-lowbit-384 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 945.911 | 2.800 | 18797.047 | 18286.258/18512.000 | 0.001 |
| fresh-lowbit-400 | 24/24 | 8/16 | 8 | 0 | 0/8 | 0/0 | 945.015 | 2.802 | 18797.047 | 18286.258/18512.000 | 0.001 |
| fresh-lowbit-448 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 947.605 | 2.763 | 18797.047 | 18286.258/18512.000 | 0.001 |
| fresh-lowbit-500 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 927.020 | 2.907 | 18797.047 | 18286.258/18512.000 | 0.001 |
| fresh-lowbit-640 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 869.101 | 3.090 | 18797.047 | 18294.406/18512.000 | 0.001 |

| Fresh arm | Paired with original same-mode512 | Changed choices | Known gains/losses | Ambiguous abstention gains/losses |
|---|---:|---:|---:|---:|
| fresh-rgb-128 | 24 | 5 | 1/3 | 0/0 |
| fresh-rgb-256 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-384 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-400 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-448 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-500 | 24 | 1 | 0/1 | 0/0 |
| fresh-rgb-640 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-128 | 24 | 5 | 1/3 | 0/0 |
| fresh-gray-256 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-384 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-400 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-448 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-500 | 24 | 1 | 0/1 | 0/0 |
| fresh-gray-640 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-128 | 24 | 5 | 3/1 | 0/0 |
| fresh-lowbit-256 | 24 | 3 | 1/2 | 0/0 |
| fresh-lowbit-384 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-400 | 24 | 2 | 0/2 | 0/0 |
| fresh-lowbit-448 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-500 | 24 | 1 | 0/1 | 0/0 |
| fresh-lowbit-640 | 24 | 0 | 0/0 | 0/0 |

| Arm | Mean PNG bytes | Mean native input tokens | Mean native output tokens | Regions/marginal USD est. |
|---|---:|---:|---:|---:|
| original fresh-gray-1024 | 6469.875 | 816.417 | 0.000 | 32029.318 |
| original fresh-gray-512 | 2659.792 | 608.917 | 0.000 | 42950.419 |
| original fresh-gray-768 | 4469.667 | 679.417 | 0.000 | 36994.282 |
| original fresh-lowbit-1024 | 1755.792 | 817.417 | 0.000 | 31757.240 |
| original fresh-lowbit-512 | 738.625 | 609.917 | 0.000 | 42414.435 |
| original fresh-lowbit-768 | 1203.500 | 680.417 | 0.000 | 36664.912 |
| original fresh-rgb-1024 | 14445.250 | 816.417 | 0.000 | 31164.570 |
| original fresh-rgb-512 | 5948.833 | 608.917 | 0.000 | 31653.208 |
| original fresh-rgb-768 | 10066.125 | 679.417 | 0.000 | 35926.214 |
| fresh-rgb-128 | 985.333 | 591.417 | 0.000 | 31289.523 |
| fresh-rgb-256 | 2399.958 | 591.917 | 0.000 | 44545.641 |
| fresh-rgb-384 | 4156.042 | 591.917 | 0.000 | 44533.912 |
| fresh-rgb-400 | 4416.542 | 591.917 | 0.000 | 44185.290 |
| fresh-rgb-448 | 5087.458 | 594.917 | 0.000 | 44578.976 |
| fresh-rgb-500 | 5855.500 | 608.917 | 0.000 | 43019.535 |
| fresh-rgb-640 | 7985.125 | 642.917 | 0.000 | 40773.769 |
| fresh-gray-128 | 497.792 | 591.417 | 0.000 | 44716.122 |
| fresh-gray-256 | 1117.417 | 591.917 | 0.000 | 44593.079 |
| fresh-gray-384 | 1880.333 | 591.917 | 0.000 | 44608.936 |
| fresh-gray-400 | 1989.500 | 591.917 | 0.000 | 44311.495 |
| fresh-gray-448 | 2275.917 | 594.917 | 0.000 | 44653.487 |
| fresh-gray-500 | 2606.875 | 608.917 | 0.000 | 43486.677 |
| fresh-gray-640 | 3569.583 | 642.917 | 0.000 | 41163.714 |
| fresh-lowbit-128 | 191.042 | 592.417 | 0.000 | 44710.915 |
| fresh-lowbit-256 | 342.458 | 592.917 | 0.000 | 44716.563 |
| fresh-lowbit-384 | 512.708 | 592.917 | 0.000 | 44513.471 |
| fresh-lowbit-400 | 551.333 | 592.917 | 0.000 | 44471.292 |
| fresh-lowbit-448 | 624.625 | 595.917 | 0.000 | 44593.176 |
| fresh-lowbit-500 | 690.000 | 609.917 | 0.000 | 43624.485 |
| fresh-lowbit-640 | 954.125 | 643.917 | 0.000 | 40898.877 |

Timing includes adapter predict and native input preprocessing. CPU/RSS scope is the worker process and threads, excluding subprocesses; RSS is a lifetime high-water mark. CUDA peaks are maximum recorded attempt counters, not per-arm isolated allocations.
GPU samples available: 42/42; scope: device-wide, not per-worker; nominal interval: 1.0 seconds.
explicit hourly rate times retained adapter inference seconds /3600; marginal occupancy estimate only, excludes startup/downloads/idle/teardown and actual lifecycle billing. Full-page pages/USD and lifecycle billed cost are unknown.
Explicit supplied hourly rate: 1.275 USD/hour.
Token means require a reported field on every input; missing fields remain unknown. Native output-token fields describe the adapter's usage report, not generated explanation text. Token observations alone do not establish a processor resolution floor or provider billing.
Source-major order puts 128RGB first. Retained inference time includes first-predict lazy warmup; these single runs do not isolate steady-state latency. Initialization and idle time are excluded from the marginal estimate.
Local verification/report CPU: 4.594 s; RSS lifetime peak: 134.363 MiB.

## Cloudflare/clef

State: complete; 504/504 valid fresh inputs. Baseline: `clef-l015` (complete).

| Arm | Valid/planned | Known correct | Wrong known | Known abstain | Ambiguous abstain | Schema/worker errors | Regions/min | CPU s | RSS MiB | GPU alloc/reserved MiB | Marginal USD est. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| original fresh-gray-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 245.813 | 7.774 | 53032.203 | 52642.649/52838.000 | 0.002 |
| original fresh-gray-512 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 310.576 | 5.931 | 53032.203 | 52570.066/52838.000 | 0.002 |
| original fresh-gray-768 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 273.466 | 6.755 | 53032.203 | 52599.175/52838.000 | 0.002 |
| original fresh-lowbit-1024 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 236.533 | 7.975 | 53032.203 | 52642.812/52838.000 | 0.002 |
| original fresh-lowbit-512 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 300.935 | 6.104 | 53032.203 | 52570.187/52838.000 | 0.002 |
| original fresh-lowbit-768 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 268.718 | 6.855 | 53032.203 | 52599.373/52838.000 | 0.002 |
| original fresh-rgb-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 233.112 | 8.171 | 53032.203 | 52642.649/52838.000 | 0.002 |
| original fresh-rgb-512 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 285.593 | 6.374 | 53032.203 | 52570.066/52732.000 | 0.002 |
| original fresh-rgb-768 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 267.903 | 6.925 | 53032.203 | 52599.175/52838.000 | 0.002 |
| fresh-rgb-128 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 277.705 | 6.383 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-rgb-256 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 310.824 | 5.884 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-rgb-384 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 312.117 | 5.903 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-rgb-400 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 311.021 | 5.943 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-rgb-448 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 312.776 | 5.838 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-rgb-500 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 304.347 | 6.113 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-rgb-640 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 290.129 | 6.451 | 53030.184 | 52575.506/52732.000 | 0.002 |
| fresh-gray-128 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 313.706 | 5.806 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-gray-256 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 312.609 | 5.871 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-gray-384 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 312.020 | 5.903 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-gray-400 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 312.557 | 5.913 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-gray-448 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 311.738 | 5.864 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-gray-500 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 304.623 | 6.128 | 53030.184 | 52570.066/52732.000 | 0.002 |
| fresh-gray-640 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 291.879 | 6.356 | 53030.184 | 52575.506/52732.000 | 0.002 |
| fresh-lowbit-128 | 24/24 | 8/16 | 8 | 0 | 0/8 | 0/0 | 312.806 | 5.824 | 53030.184 | 52570.187/52732.000 | 0.002 |
| fresh-lowbit-256 | 24/24 | 8/16 | 8 | 0 | 0/8 | 0/0 | 312.988 | 5.854 | 53030.184 | 52570.187/52732.000 | 0.002 |
| fresh-lowbit-384 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 312.162 | 5.903 | 53030.184 | 52570.187/52732.000 | 0.002 |
| fresh-lowbit-400 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 312.307 | 5.922 | 53030.184 | 52570.187/52732.000 | 0.002 |
| fresh-lowbit-448 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 311.956 | 5.875 | 53030.184 | 52570.187/52732.000 | 0.002 |
| fresh-lowbit-500 | 24/24 | 9/16 | 7 | 0 | 0/8 | 0/0 | 305.421 | 6.135 | 53030.184 | 52570.187/52732.000 | 0.002 |
| fresh-lowbit-640 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 289.556 | 6.387 | 53030.184 | 52575.645/52732.000 | 0.002 |

| Fresh arm | Paired with original same-mode512 | Changed choices | Known gains/losses | Ambiguous abstention gains/losses |
|---|---:|---:|---:|---:|
| fresh-rgb-128 | 24 | 3 | 1/1 | 0/0 |
| fresh-rgb-256 | 24 | 3 | 1/1 | 0/0 |
| fresh-rgb-384 | 24 | 3 | 2/0 | 0/0 |
| fresh-rgb-400 | 24 | 2 | 1/0 | 0/0 |
| fresh-rgb-448 | 24 | 1 | 0/0 | 0/0 |
| fresh-rgb-500 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-640 | 24 | 1 | 1/0 | 0/0 |
| fresh-gray-128 | 24 | 2 | 1/1 | 0/0 |
| fresh-gray-256 | 24 | 3 | 1/1 | 0/0 |
| fresh-gray-384 | 24 | 3 | 2/0 | 0/0 |
| fresh-gray-400 | 24 | 2 | 1/0 | 0/0 |
| fresh-gray-448 | 24 | 1 | 0/0 | 0/0 |
| fresh-gray-500 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-640 | 24 | 2 | 1/0 | 0/0 |
| fresh-lowbit-128 | 24 | 1 | 0/1 | 0/0 |
| fresh-lowbit-256 | 24 | 1 | 0/1 | 0/0 |
| fresh-lowbit-384 | 24 | 2 | 2/0 | 0/0 |
| fresh-lowbit-400 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-448 | 24 | 1 | 1/0 | 0/0 |
| fresh-lowbit-500 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-640 | 24 | 2 | 2/0 | 0/0 |

| Arm | Mean PNG bytes | Mean native input tokens | Mean native output tokens | Regions/marginal USD est. |
|---|---:|---:|---:|---:|
| original fresh-gray-1024 | 6469.875 | 816.417 | 0.000 | 11567.667 |
| original fresh-gray-512 | 2659.792 | 608.917 | 0.000 | 14615.334 |
| original fresh-gray-768 | 4469.667 | 679.417 | 0.000 | 12868.998 |
| original fresh-lowbit-1024 | 1755.792 | 817.417 | 0.000 | 11130.981 |
| original fresh-lowbit-512 | 738.625 | 609.917 | 0.000 | 14161.647 |
| original fresh-lowbit-768 | 1203.500 | 680.417 | 0.000 | 12645.551 |
| original fresh-rgb-1024 | 14445.250 | 816.417 | 0.000 | 10969.955 |
| original fresh-rgb-512 | 5948.833 | 608.917 | 0.000 | 13439.665 |
| original fresh-rgb-768 | 10066.125 | 679.417 | 0.000 | 12607.203 |
| fresh-rgb-128 | 985.333 | 591.417 | 0.000 | 13068.482 |
| fresh-rgb-256 | 2399.958 | 591.917 | 0.000 | 14627.031 |
| fresh-rgb-384 | 4156.042 | 591.917 | 0.000 | 14687.861 |
| fresh-rgb-400 | 4416.542 | 591.917 | 0.000 | 14636.298 |
| fresh-rgb-448 | 5087.458 | 594.917 | 0.000 | 14718.877 |
| fresh-rgb-500 | 5855.500 | 608.917 | 0.000 | 14322.213 |
| fresh-rgb-640 | 7985.125 | 642.917 | 0.000 | 13653.125 |
| fresh-gray-128 | 497.792 | 591.417 | 0.000 | 14762.644 |
| fresh-gray-256 | 1117.417 | 591.917 | 0.000 | 14711.009 |
| fresh-gray-384 | 1880.333 | 591.917 | 0.000 | 14683.295 |
| fresh-gray-400 | 1989.500 | 591.917 | 0.000 | 14708.544 |
| fresh-gray-448 | 2275.917 | 594.917 | 0.000 | 14670.002 |
| fresh-gray-500 | 2606.875 | 608.917 | 0.000 | 14335.182 |
| fresh-gray-640 | 3569.583 | 642.917 | 0.000 | 13735.503 |
| fresh-lowbit-128 | 191.042 | 592.417 | 0.000 | 14720.277 |
| fresh-lowbit-256 | 342.458 | 592.917 | 0.000 | 14728.828 |
| fresh-lowbit-384 | 512.708 | 592.917 | 0.000 | 14689.999 |
| fresh-lowbit-400 | 551.333 | 592.917 | 0.000 | 14696.796 |
| fresh-lowbit-448 | 624.625 | 595.917 | 0.000 | 14680.299 |
| fresh-lowbit-500 | 690.000 | 609.917 | 0.000 | 14372.755 |
| fresh-lowbit-640 | 954.125 | 643.917 | 0.000 | 13626.146 |

Timing includes adapter predict and native input preprocessing. CPU/RSS scope is the worker process and threads, excluding subprocesses; RSS is a lifetime high-water mark. CUDA peaks are maximum recorded attempt counters, not per-arm isolated allocations.
GPU samples available: 119/119; scope: device-wide, not per-worker; nominal interval: 1.0 seconds.
explicit hourly rate times retained adapter inference seconds /3600; marginal occupancy estimate only, excludes startup/downloads/idle/teardown and actual lifecycle billing. Full-page pages/USD and lifecycle billed cost are unknown.
Explicit supplied hourly rate: 1.275 USD/hour.
Token means require a reported field on every input; missing fields remain unknown. Native output-token fields describe the adapter's usage report, not generated explanation text. Token observations alone do not establish a processor resolution floor or provider billing.
Source-major order puts 128RGB first. Retained inference time includes first-predict lazy warmup; these single runs do not isolate steady-state latency. Initialization and idle time are excluded from the marginal estimate.
Local verification/report CPU: 4.545 s; RSS lifetime peak: 159.898 MiB.

## perplexity-ai/pplx-decider-v1.1-27b

State: complete; 504/504 valid fresh inputs. Baseline: `pplx-l015` (complete).

| Arm | Valid/planned | Known correct | Wrong known | Known abstain | Ambiguous abstain | Schema/worker errors | Regions/min | CPU s | RSS MiB | GPU alloc/reserved MiB | Marginal USD est. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| original fresh-gray-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 266.057 | 7.984 | 6079.246 | 50000.556/50190.000 | 0.002 |
| original fresh-gray-512 | 24/24 | 9/16 | 4 | 3 | 0/8 | 0/0 | 349.733 | 6.495 | 6079.246 | 49928.034/50190.000 | 0.002 |
| original fresh-gray-768 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 316.103 | 6.865 | 6079.246 | 49948.040/50190.000 | 0.002 |
| original fresh-lowbit-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 262.753 | 7.902 | 6079.246 | 50000.728/50190.000 | 0.002 |
| original fresh-lowbit-512 | 24/24 | 10/16 | 4 | 2 | 0/8 | 0/0 | 343.572 | 6.578 | 6079.246 | 49928.149/50190.000 | 0.002 |
| original fresh-lowbit-768 | 24/24 | 11/16 | 4 | 1 | 0/8 | 0/0 | 311.806 | 7.032 | 6079.246 | 49948.185/50190.000 | 0.002 |
| original fresh-rgb-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 258.013 | 8.106 | 6079.246 | 50000.556/50190.000 | 0.002 |
| original fresh-rgb-512 | 24/24 | 9/16 | 3 | 4 | 0/8 | 0/0 | 250.413 | 8.049 | 6079.246 | 49928.034/50036.000 | 0.002 |
| original fresh-rgb-768 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 309.393 | 7.087 | 6079.246 | 49948.040/50190.000 | 0.002 |
| fresh-rgb-128 | 24/24 | 10/16 | 3 | 3 | 0/8 | 0/0 | 260.052 | 7.864 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-rgb-256 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 354.602 | 6.407 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-rgb-384 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 353.508 | 6.433 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-rgb-400 | 24/24 | 10/16 | 4 | 2 | 0/8 | 0/0 | 353.772 | 6.419 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-rgb-448 | 24/24 | 11/16 | 4 | 1 | 0/8 | 0/0 | 353.044 | 6.451 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-rgb-500 | 24/24 | 10/16 | 5 | 1 | 0/8 | 0/0 | 342.271 | 6.607 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-rgb-640 | 24/24 | 10/16 | 4 | 2 | 0/8 | 0/0 | 325.988 | 6.841 | 6079.164 | 49935.094/50062.000 | 0.002 |
| fresh-gray-128 | 24/24 | 11/16 | 4 | 1 | 0/8 | 0/0 | 355.164 | 6.392 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-gray-256 | 24/24 | 11/16 | 4 | 1 | 0/8 | 0/0 | 354.980 | 6.412 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-gray-384 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 354.024 | 6.433 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-gray-400 | 24/24 | 10/16 | 4 | 2 | 0/8 | 0/0 | 353.889 | 6.446 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-gray-448 | 24/24 | 11/16 | 4 | 1 | 0/8 | 0/0 | 353.521 | 6.439 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-gray-500 | 24/24 | 10/16 | 5 | 1 | 0/8 | 0/0 | 342.895 | 6.586 | 6079.164 | 49928.034/50062.000 | 0.002 |
| fresh-gray-640 | 24/24 | 10/16 | 4 | 2 | 0/8 | 0/0 | 327.426 | 6.801 | 6079.164 | 49935.094/50062.000 | 0.002 |
| fresh-lowbit-128 | 24/24 | 9/16 | 4 | 3 | 0/8 | 0/0 | 354.909 | 6.413 | 6079.164 | 49928.149/50062.000 | 0.002 |
| fresh-lowbit-256 | 24/24 | 8/16 | 6 | 2 | 0/8 | 0/0 | 354.526 | 6.417 | 6079.164 | 49928.149/50062.000 | 0.002 |
| fresh-lowbit-384 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 353.950 | 6.412 | 6079.164 | 49928.149/50062.000 | 0.002 |
| fresh-lowbit-400 | 24/24 | 11/16 | 4 | 1 | 0/8 | 0/0 | 354.081 | 6.437 | 6079.164 | 49928.149/50062.000 | 0.002 |
| fresh-lowbit-448 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 353.148 | 6.441 | 6079.164 | 49928.149/50062.000 | 0.002 |
| fresh-lowbit-500 | 24/24 | 8/16 | 6 | 2 | 0/8 | 0/0 | 342.828 | 6.576 | 6079.164 | 49928.149/50062.000 | 0.002 |
| fresh-lowbit-640 | 24/24 | 11/16 | 4 | 1 | 0/8 | 0/0 | 327.403 | 6.786 | 6079.164 | 49935.189/50062.000 | 0.002 |

| Fresh arm | Paired with original same-mode512 | Changed choices | Known gains/losses | Ambiguous abstention gains/losses |
|---|---:|---:|---:|---:|
| fresh-rgb-128 | 24 | 1 | 1/0 | 0/0 |
| fresh-rgb-256 | 24 | 4 | 3/0 | 0/0 |
| fresh-rgb-384 | 24 | 4 | 2/0 | 0/0 |
| fresh-rgb-400 | 24 | 2 | 1/0 | 0/0 |
| fresh-rgb-448 | 24 | 3 | 2/0 | 0/0 |
| fresh-rgb-500 | 24 | 3 | 1/0 | 0/0 |
| fresh-rgb-640 | 24 | 2 | 1/0 | 0/0 |
| fresh-gray-128 | 24 | 4 | 2/0 | 0/0 |
| fresh-gray-256 | 24 | 2 | 2/0 | 0/0 |
| fresh-gray-384 | 24 | 3 | 2/0 | 0/0 |
| fresh-gray-400 | 24 | 1 | 1/0 | 0/0 |
| fresh-gray-448 | 24 | 2 | 2/0 | 0/0 |
| fresh-gray-500 | 24 | 2 | 1/0 | 0/0 |
| fresh-gray-640 | 24 | 1 | 1/0 | 0/0 |
| fresh-lowbit-128 | 24 | 4 | 0/1 | 0/0 |
| fresh-lowbit-256 | 24 | 4 | 0/2 | 0/0 |
| fresh-lowbit-384 | 24 | 3 | 2/0 | 0/0 |
| fresh-lowbit-400 | 24 | 2 | 1/0 | 0/0 |
| fresh-lowbit-448 | 24 | 3 | 2/0 | 0/0 |
| fresh-lowbit-500 | 24 | 3 | 0/2 | 0/0 |
| fresh-lowbit-640 | 24 | 3 | 1/0 | 0/0 |

| Arm | Mean PNG bytes | Mean native input tokens | Mean native output tokens | Regions/marginal USD est. |
|---|---:|---:|---:|---:|
| original fresh-gray-1024 | 6469.875 | unmeasured | unmeasured | 11609.753 |
| original fresh-gray-512 | 2659.792 | unmeasured | unmeasured | 15261.071 |
| original fresh-gray-768 | 4469.667 | unmeasured | unmeasured | 13793.575 |
| original fresh-lowbit-1024 | 1755.792 | unmeasured | unmeasured | 11465.582 |
| original fresh-lowbit-512 | 738.625 | unmeasured | unmeasured | 14992.219 |
| original fresh-lowbit-768 | 1203.500 | unmeasured | unmeasured | 13606.066 |
| original fresh-rgb-1024 | 14445.250 | unmeasured | unmeasured | 11258.770 |
| original fresh-rgb-512 | 5948.833 | unmeasured | unmeasured | 10927.111 |
| original fresh-rgb-768 | 10066.125 | unmeasured | unmeasured | 13500.780 |
| fresh-rgb-128 | 985.333 | unmeasured | unmeasured | 11347.727 |
| fresh-rgb-256 | 2399.958 | unmeasured | unmeasured | 15473.556 |
| fresh-rgb-384 | 4156.042 | unmeasured | unmeasured | 15425.792 |
| fresh-rgb-400 | 4416.542 | unmeasured | unmeasured | 15437.321 |
| fresh-rgb-448 | 5087.458 | unmeasured | unmeasured | 15405.549 |
| fresh-rgb-500 | 5855.500 | unmeasured | unmeasured | 14935.474 |
| fresh-rgb-640 | 7985.125 | unmeasured | unmeasured | 14224.912 |
| fresh-gray-128 | 497.792 | unmeasured | unmeasured | 15498.048 |
| fresh-gray-256 | 1117.417 | unmeasured | unmeasured | 15490.036 |
| fresh-gray-384 | 1880.333 | unmeasured | unmeasured | 15448.332 |
| fresh-gray-400 | 1989.500 | unmeasured | unmeasured | 15442.420 |
| fresh-gray-448 | 2275.917 | unmeasured | unmeasured | 15426.379 |
| fresh-gray-500 | 2606.875 | unmeasured | unmeasured | 14962.692 |
| fresh-gray-640 | 3569.583 | unmeasured | unmeasured | 14287.690 |
| fresh-lowbit-128 | 191.042 | unmeasured | unmeasured | 15486.927 |
| fresh-lowbit-256 | 342.458 | unmeasured | unmeasured | 15470.223 |
| fresh-lowbit-384 | 512.708 | unmeasured | unmeasured | 15445.105 |
| fresh-lowbit-400 | 551.333 | unmeasured | unmeasured | 15450.808 |
| fresh-lowbit-448 | 624.625 | unmeasured | unmeasured | 15410.089 |
| fresh-lowbit-500 | 690.000 | unmeasured | unmeasured | 14959.758 |
| fresh-lowbit-640 | 954.125 | unmeasured | unmeasured | 14286.685 |

Timing includes adapter predict and native input preprocessing. CPU/RSS scope is the worker process and threads, excluding subprocesses; RSS is a lifetime high-water mark. CUDA peaks are maximum recorded attempt counters, not per-arm isolated allocations.
GPU samples available: 108/108; scope: device-wide, not per-worker; nominal interval: 1.0 seconds.
explicit hourly rate times retained adapter inference seconds /3600; marginal occupancy estimate only, excludes startup/downloads/idle/teardown and actual lifecycle billing. Full-page pages/USD and lifecycle billed cost are unknown.
Explicit supplied hourly rate: 1.375 USD/hour.
Token means require a reported field on every input; missing fields remain unknown. Native output-token fields describe the adapter's usage report, not generated explanation text. Token observations alone do not establish a processor resolution floor or provider billing.
Source-major order puts 128RGB first. Retained inference time includes first-predict lazy warmup; these single runs do not isolate steady-state latency. Initialization and idle time are excluded from the marginal estimate.
Local verification/report CPU: 4.504 s; RSS lifetime peak: 170.613 MiB.

## internlm/Intern-Decision-4B

State: complete; 504/504 valid fresh inputs. Baseline: `intern-new-runtime-l015` (complete).

| Arm | Valid/planned | Known correct | Wrong known | Known abstain | Ambiguous abstain | Schema/worker errors | Regions/min | CPU s | RSS MiB | GPU alloc/reserved MiB | Marginal USD est. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| original fresh-gray-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 697.862 | 4.598 | 9081.258 | 8934.407/9070.000 | 0.001 |
| original fresh-gray-512 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 741.684 | 4.297 | 9081.258 | 8886.676/9070.000 | 0.001 |
| original fresh-gray-768 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 712.973 | 4.442 | 9081.258 | 8901.655/9070.000 | 0.001 |
| original fresh-lowbit-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 699.733 | 4.594 | 9081.258 | 8934.511/9070.000 | 0.001 |
| original fresh-lowbit-512 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 736.112 | 4.327 | 9081.258 | 8886.723/9070.000 | 0.001 |
| original fresh-lowbit-768 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 724.353 | 4.421 | 9081.258 | 8901.733/9070.000 | 0.001 |
| original fresh-rgb-1024 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 683.032 | 4.656 | 9081.258 | 8934.407/9070.000 | 0.001 |
| original fresh-rgb-512 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 407.697 | 5.820 | 9081.258 | 8886.676/9008.000 | 0.001 |
| original fresh-rgb-768 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 713.941 | 4.439 | 9081.258 | 8901.655/9070.000 | 0.001 |
| fresh-rgb-128 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 411.213 | 5.807 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-rgb-256 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 735.631 | 4.294 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-rgb-384 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 733.609 | 4.302 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-rgb-400 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 732.899 | 4.302 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-rgb-448 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 729.242 | 4.325 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-rgb-500 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 723.936 | 4.347 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-rgb-640 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 717.120 | 4.398 | 9081.695 | 8891.895/9054.000 | 0.001 |
| fresh-gray-128 | 24/24 | 11/16 | 5 | 0 | 0/8 | 0/0 | 739.381 | 4.265 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-gray-256 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 737.651 | 4.292 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-gray-384 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 738.519 | 4.288 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-gray-400 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 738.560 | 4.289 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-gray-448 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 737.620 | 4.296 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-gray-500 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 731.832 | 4.327 | 9081.695 | 8886.676/9054.000 | 0.001 |
| fresh-gray-640 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 725.567 | 4.375 | 9081.695 | 8891.895/9054.000 | 0.001 |
| fresh-lowbit-128 | 24/24 | 10/16 | 6 | 0 | 0/8 | 0/0 | 742.623 | 4.249 | 9081.695 | 8886.723/9054.000 | 0.001 |
| fresh-lowbit-256 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 735.088 | 4.295 | 9081.695 | 8886.723/9054.000 | 0.001 |
| fresh-lowbit-384 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 739.965 | 4.283 | 9081.695 | 8886.723/9054.000 | 0.001 |
| fresh-lowbit-400 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 734.987 | 4.297 | 9081.695 | 8886.723/9054.000 | 0.001 |
| fresh-lowbit-448 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 737.850 | 4.290 | 9081.695 | 8886.723/9054.000 | 0.001 |
| fresh-lowbit-500 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 734.327 | 4.312 | 9081.695 | 8886.723/9054.000 | 0.001 |
| fresh-lowbit-640 | 24/24 | 12/16 | 4 | 0 | 0/8 | 0/0 | 724.732 | 4.359 | 9081.695 | 8891.961/9054.000 | 0.001 |

| Fresh arm | Paired with original same-mode512 | Changed choices | Known gains/losses | Ambiguous abstention gains/losses |
|---|---:|---:|---:|---:|
| fresh-rgb-128 | 24 | 1 | 0/1 | 0/0 |
| fresh-rgb-256 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-384 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-400 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-448 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-500 | 24 | 0 | 0/0 | 0/0 |
| fresh-rgb-640 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-128 | 24 | 1 | 0/1 | 0/0 |
| fresh-gray-256 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-384 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-400 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-448 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-500 | 24 | 0 | 0/0 | 0/0 |
| fresh-gray-640 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-128 | 24 | 2 | 0/2 | 0/0 |
| fresh-lowbit-256 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-384 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-400 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-448 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-500 | 24 | 0 | 0/0 | 0/0 |
| fresh-lowbit-640 | 24 | 0 | 0/0 | 0/0 |

| Arm | Mean PNG bytes | Mean native input tokens | Mean native output tokens | Regions/marginal USD est. |
|---|---:|---:|---:|---:|
| original fresh-gray-1024 | 6469.875 | 862.833 | 1.000 | 30452.158 |
| original fresh-gray-512 | 2659.792 | 655.333 | 1.000 | 32364.377 |
| original fresh-gray-768 | 4469.667 | 725.833 | 1.000 | 31111.534 |
| original fresh-lowbit-1024 | 1755.792 | 863.833 | 1.000 | 30533.823 |
| original fresh-lowbit-512 | 738.625 | 656.333 | 1.000 | 32121.239 |
| original fresh-lowbit-768 | 1203.500 | 726.833 | 1.000 | 31608.113 |
| original fresh-rgb-1024 | 14445.250 | 862.833 | 1.000 | 29805.053 |
| original fresh-rgb-512 | 5948.833 | 655.333 | 1.000 | 17790.397 |
| original fresh-rgb-768 | 10066.125 | 725.833 | 1.000 | 31153.796 |
| fresh-rgb-128 | 985.333 | 637.833 | 1.000 | 17943.845 |
| fresh-rgb-256 | 2399.958 | 638.333 | 1.000 | 32100.245 |
| fresh-rgb-384 | 4156.042 | 638.333 | 1.000 | 32012.016 |
| fresh-rgb-400 | 4416.542 | 638.333 | 1.000 | 31981.038 |
| fresh-rgb-448 | 5087.458 | 641.333 | 1.000 | 31821.484 |
| fresh-rgb-500 | 5855.500 | 655.333 | 1.000 | 31589.943 |
| fresh-rgb-640 | 7985.125 | 689.333 | 1.000 | 31292.510 |
| fresh-gray-128 | 497.792 | 637.833 | 1.000 | 32263.878 |
| fresh-gray-256 | 1117.417 | 638.333 | 1.000 | 32188.410 |
| fresh-gray-384 | 1880.333 | 638.333 | 1.000 | 32226.303 |
| fresh-gray-400 | 1989.500 | 638.333 | 1.000 | 32228.058 |
| fresh-gray-448 | 2275.917 | 641.333 | 1.000 | 32187.053 |
| fresh-gray-500 | 2606.875 | 655.333 | 1.000 | 31934.473 |
| fresh-gray-640 | 3569.583 | 689.333 | 1.000 | 31661.124 |
| fresh-lowbit-128 | 191.042 | 638.833 | 1.000 | 32405.370 |
| fresh-lowbit-256 | 342.458 | 639.333 | 1.000 | 32076.552 |
| fresh-lowbit-384 | 512.708 | 639.333 | 1.000 | 32289.399 |
| fresh-lowbit-400 | 551.333 | 639.333 | 1.000 | 32072.142 |
| fresh-lowbit-448 | 624.625 | 642.333 | 1.000 | 32197.105 |
| fresh-lowbit-500 | 690.000 | 656.333 | 1.000 | 32043.340 |
| fresh-lowbit-640 | 954.125 | 690.333 | 1.000 | 31624.672 |

Timing includes adapter predict and native input preprocessing. CPU/RSS scope is the worker process and threads, excluding subprocesses; RSS is a lifetime high-water mark. CUDA peaks are maximum recorded attempt counters, not per-arm isolated allocations.
GPU samples available: 56/56; scope: device-wide, not per-worker; nominal interval: 1.0 seconds.
explicit hourly rate times retained adapter inference seconds /3600; marginal occupancy estimate only, excludes startup/downloads/idle/teardown and actual lifecycle billing. Full-page pages/USD and lifecycle billed cost are unknown.
Explicit supplied hourly rate: 1.375 USD/hour.
Token means require a reported field on every input; missing fields remain unknown. Native output-token fields describe the adapter's usage report, not generated explanation text. Token observations alone do not establish a processor resolution floor or provider billing.
Source-major order puts 128RGB first. Retained inference time includes first-predict lazy warmup; these single runs do not isolate steady-state latency. Initialization and idle time are excluded from the marginal estimate.
Local verification/report CPU: 4.514 s; RSS lifetime peak: 173.625 MiB.

A treatment's size and color effects must be assessed across the full frozen matrix. This report does not select a representation per reference or treat paired improvements as an operational oracle. No protected held-out inputs were accessed.

Reproduce with `python -m bench.remote_image_size_report --directory <fresh-freeze> --run flash=<fresh-output>=<original-output>=1.275 --markdown bench/results/remote-gpu-image-sizes.md --json <ignored-output>`. Repeat `--run` for each model with its explicit baseline and supplied hourly rate. This CPU-only command verifies every fresh PNG before DEV scoring and makes no inference calls.
