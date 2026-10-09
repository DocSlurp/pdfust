# L001 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 400/512 planned; completed manifest records: 424/544. Refused: 512 bodies / 544 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| typesafe/jev-1.13 | minimal@resolved | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | canonical@resolved | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | vectors@resolved | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | minimal@typed | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | canonical@typed | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | vectors@typed | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | minimal@both | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | canonical@both | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | vectors@both | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | minimal@singleton | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | vectors@singleton | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| liquid/d1 | minimal@resolved | 24/24 | 6/16 | 1/8 | unmeasured | 0.00030864 | 77760.5 | 19440.1 | 545.892 |
| liquid/d1 | canonical@resolved | 24/24 | 7/16 | 0/8 | unmeasured | 0.0054912 | 4370.63 | 1274.77 | 333.26 |
| liquid/d1 | vectors@resolved | 24/24 | 8/16 | 0/8 | unmeasured | 0.00654804 | 3665.22 | 1221.74 | 287.186 |
| liquid/d1 | minimal@typed | 24/24 | 8/16 | 0/8 | unmeasured | 0.00042144 | 56947.6 | 18982.5 | 536.805 |
| liquid/d1 | canonical@typed | 24/24 | 8/16 | 0/8 | unmeasured | 0.00783228 | 3064.24 | 1021.41 | 251.146 |
| liquid/d1 | vectors@typed | 24/24 | 8/16 | 0/8 | unmeasured | 0.0094332 | 2544.21 | 848.069 | 226.242 |
| liquid/d1 | minimal@both | 24/24 | 9/16 | 2/8 | unmeasured | 0.00036936 | 64977.3 | 24366.5 | 565.785 |
| liquid/d1 | canonical@both | 24/24 | 7/16 | 1/8 | unmeasured | 0.0077802 | 3084.75 | 899.72 | 285.772 |
| liquid/d1 | vectors@both | 24/24 | 8/16 | 1/8 | unmeasured | 0.00938112 | 2558.33 | 852.777 | 246.82 |
| liquid/d1 | minimal@singleton | 24/24 | 6/16 | 1/8 | unmeasured | 0.00016184 | 98863.1 | 12357.9 | 166.589 |
| liquid/d1 | vectors@singleton | 24/24 | 9/16 | 0/8 | unmeasured | 0.00232548 | 10320.4 | 3870.17 | 181.894 |
| perplexity/pplx-decider-v1.1-27b | minimal@resolved | 24/24 | 6/16 | 3/8 | unmeasured | 0.00017208 | 139470 | 34867.5 | 432.251 |
| perplexity/pplx-decider-v1.1-27b | canonical@resolved | 24/24 | 8/16 | 0/8 | unmeasured | 0.00293898 | 8166.1 | 2722.03 | 244.105 |
| perplexity/pplx-decider-v1.1-27b | vectors@resolved | 24/24 | 12/16 | 3/8 | unmeasured | 0.00356664 | 6729.02 | 3364.51 | 223.916 |
| perplexity/pplx-decider-v1.1-27b | minimal@typed | 24/24 | 8/16 | 0/8 | unmeasured | 0.00019002 | 126302 | 42100.8 | 424.748 |
| perplexity/pplx-decider-v1.1-27b | canonical@typed | 24/24 | 7/16 | 0/8 | unmeasured | 0.00307032 | 7816.77 | 2279.89 | 250.114 |
| perplexity/pplx-decider-v1.1-27b | vectors@typed | 24/24 | 11/16 | 0/8 | unmeasured | 0.00376356 | 6376.94 | 2922.76 | 222.733 |
| perplexity/pplx-decider-v1.1-27b | minimal@both | 24/24 | 6/16 | 4/8 | unmeasured | 0.0001665 | 144144 | 36036 | 378.934 |
| perplexity/pplx-decider-v1.1-27b | canonical@both | 24/24 | 9/16 | 0/8 | unmeasured | 0.0030468 | 7877.12 | 2953.92 | 244.825 |
| perplexity/pplx-decider-v1.1-27b | vectors@both | 24/24 | 9/16 | 2/8 | unmeasured | 0.00374004 | 6417.04 | 2406.39 | 123.165 |
| perplexity/pplx-decider-v1.1-27b | crop512@resolved | 24/24 | 15/16 | 1/8 | unmeasured | 0.00356448 | 6733.1 | 4208.19 | 227.551 |
| perplexity/pplx-decider-v1.1-27b | minimal@singleton | 24/24 | 7/16 | 0/8 | unmeasured | 9.392e-05 | 170358 | 53236.8 | 144.791 |
| perplexity/pplx-decider-v1.1-27b | vectors@singleton | 24/24 | 11/16 | 0/8 | unmeasured | 0.00127384 | 18840.7 | 8635.31 | 93.8632 |
| perplexity/pplx-decider-v1.1-27b | crop512@singleton | 24/24 | 12/16 | 0/8 | unmeasured | 0.00127312 | 18851.3 | 9425.66 | 117.575 |
| openai/gpt-6-luna-decisions | minimal@resolved | 24/24 | 2/16 | 5/8 | unmeasured | ~0.0006101 | 39337.8 | 3278.15 | 591.505 |
| openai/gpt-6-luna-decisions | canonical@resolved | 24/24 | 6/16 | 3/8 | unmeasured | ~0.0044108 | 5441.19 | 1360.3 | 552.928 |
| openai/gpt-6-luna-decisions | vectors@resolved | 24/24 | 3/16 | 7/8 | unmeasured | ~0.005273 | 4551.49 | 568.936 | 605.756 |
| openai/gpt-6-luna-decisions | minimal@typed | 24/24 | 0/16 | 8/8 | unmeasured | ~0.0007251 | 33098.9 | 0 | 349.058 |
| openai/gpt-6-luna-decisions | canonical@typed | 24/24 | 8/16 | 1/8 | unmeasured | ~0.0037422 | 6413.34 | 2137.78 | 624.488 |
| openai/gpt-6-luna-decisions | vectors@typed | 24/24 | 8/16 | 0/8 | unmeasured | ~0.0044434 | 5401.27 | 1800.42 | 581.663 |
| openai/gpt-6-luna-decisions | minimal@both | 24/24 | 2/16 | 7/8 | unmeasured | ~0.0005973 | 40180.8 | 3348.4 | 367.541 |
| openai/gpt-6-luna-decisions | canonical@both | 24/24 | 7/16 | 2/8 | unmeasured | ~0.0036144 | 6640.11 | 1936.7 | 476.991 |
| openai/gpt-6-luna-decisions | vectors@both | 24/24 | 6/16 | 6/8 | unmeasured | ~0.0043156 | 5561.22 | 1390.3 | 595.936 |
| openai/gpt-6-luna-decisions | crop512@resolved | 24/24 | 7/16 | 4/8 | unmeasured | ~0.0052814 | 4544.25 | 1325.41 | 532.213 |
| openai/gpt-6-luna-decisions | minimal@singleton | 24/24 | 1/16 | 7/8 | unmeasured | ~0.0004925 | 32487.3 | 2030.46 | 221.222 |
| openai/gpt-6-luna-decisions | vectors@singleton | 24/24 | 9/16 | 0/8 | unmeasured | ~0.0054072 | 4438.53 | 1664.45 | 169.053 |
| openai/gpt-6-luna-decisions | crop512@singleton | 24/24 | 9/16 | 0/8 | unmeasured | ~0.0054156 | 4431.64 | 1661.87 | 170.582 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 0.434396797, "measurement": "/proc/self/status VmHWM (current executable); sequential CPU; lifetime RSS; reuses frozen source extraction, no new rendering", "peak_rss_bytes": 60260352, "wall_seconds": 0.43655149298137985}`.

Execution: `{"cpu_seconds": 170.950675482, "invocations": 2, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 127885312, "wall_seconds": 414.7613666470279}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 4/8 | 0/4 |
| wrap | 4/8 | 0/4 |

Accounting audit notes:

Corrected 12 within-freeze singleton alias replay overwrites. Each original ledger tag matches this exact arm/body and no identical body exists in either preceding initial/history freeze. Original results retained byte-for-byte in results-before-alias-accounting-repair.json. Shared ledger and quality responses unchanged.

Per-family model results:

- typesafe/jev-1.13 / minimal@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / canonical@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / vectors@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / minimal@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / canonical@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / vectors@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / minimal@both: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / canonical@both: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / vectors@both: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / minimal@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- typesafe/jev-1.13 / vectors@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- liquid/d1 / minimal@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}}`.
- liquid/d1 / canonical@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / vectors@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / minimal@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / canonical@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / vectors@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / minimal@both: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / canonical@both: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / vectors@both: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / minimal@singleton: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / vectors@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- perplexity/pplx-decider-v1.1-27b / minimal@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 3, "inputs": 12, "known_exact": 1}}`.
- perplexity/pplx-decider-v1.1-27b / canonical@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- perplexity/pplx-decider-v1.1-27b / vectors@resolved: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 7}}`.
- perplexity/pplx-decider-v1.1-27b / minimal@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}}`.
- perplexity/pplx-decider-v1.1-27b / canonical@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}}`.
- perplexity/pplx-decider-v1.1-27b / vectors@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 7}}`.
- perplexity/pplx-decider-v1.1-27b / minimal@both: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}, "wrap": {"ambiguous_abstentions": 4, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / canonical@both: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- perplexity/pplx-decider-v1.1-27b / vectors@both: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 5}}`.
- perplexity/pplx-decider-v1.1-27b / crop512@resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 7}, "wrap": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / minimal@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- perplexity/pplx-decider-v1.1-27b / vectors@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 7}}`.
- perplexity/pplx-decider-v1.1-27b / crop512@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- openai/gpt-6-luna-decisions / minimal@resolved: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 3, "inputs": 12, "known_exact": 0}}`.
- openai/gpt-6-luna-decisions / canonical@resolved: `{"boundary": {"ambiguous_abstentions": 3, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}}`.
- openai/gpt-6-luna-decisions / vectors@resolved: `{"boundary": {"ambiguous_abstentions": 4, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 3, "inputs": 12, "known_exact": 3}}`.
- openai/gpt-6-luna-decisions / minimal@typed: `{"boundary": {"ambiguous_abstentions": 4, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 4, "inputs": 12, "known_exact": 0}}`.
- openai/gpt-6-luna-decisions / canonical@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 5}}`.
- openai/gpt-6-luna-decisions / vectors@typed: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / minimal@both: `{"boundary": {"ambiguous_abstentions": 3, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 4, "inputs": 12, "known_exact": 0}}`.
- openai/gpt-6-luna-decisions / canonical@both: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / vectors@both: `{"boundary": {"ambiguous_abstentions": 4, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / crop512@resolved: `{"boundary": {"ambiguous_abstentions": 3, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / minimal@singleton: `{"boundary": {"ambiguous_abstentions": 4, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 3, "inputs": 12, "known_exact": 1}}`.
- openai/gpt-6-luna-decisions / vectors@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / crop512@singleton: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.

Request/refusal accounting:

- typesafe/jev-1.13 / minimal@resolved: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / canonical@resolved: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / vectors@resolved: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / minimal@typed: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / canonical@typed: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / vectors@typed: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / minimal@both: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / canonical@both: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / vectors@both: 0/8 request bodies and 0/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / minimal@singleton: 0/16 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- typesafe/jev-1.13 / vectors@singleton: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- liquid/d1 / minimal@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / canonical@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / vectors@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / minimal@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / canonical@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / vectors@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / minimal@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / canonical@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / vectors@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / minimal@singleton: 16/16 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- liquid/d1 / vectors@singleton: 24/24 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / minimal@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / canonical@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / vectors@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / minimal@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / canonical@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / vectors@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / minimal@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / canonical@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / vectors@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 21, "wave cap exhausted before transmission": 3}`.
- perplexity/pplx-decider-v1.1-27b / crop512@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / minimal@singleton: 16/16 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / vectors@singleton: 24/24 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- perplexity/pplx-decider-v1.1-27b / crop512@singleton: 24/24 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / minimal@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / canonical@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / vectors@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / minimal@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / canonical@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / vectors@typed: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / minimal@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / canonical@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / vectors@both: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / crop512@resolved: 8/8 request bodies and 8/8 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / minimal@singleton: 16/16 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / vectors@singleton: 24/24 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.
- openai/gpt-6-luna-decisions / crop512@singleton: 24/24 request bodies and 24/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"wave cap": 24}`.

Persistent model stops: `{"typesafe/jev-1.13": {"reason": "failed or unsettled L001 ledger request", "request_sha256": "ecc0f4a99af8933d77d6a41da4d1154b9975851ac557026b83719b46d55202ff"}}`.
