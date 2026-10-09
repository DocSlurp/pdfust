# L001 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed requests: 310/392 planned.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| typesafe/jev-1.13 | minimal | 3/36 | 1/18 | 0/18 | 0/12 | 5.1492e-05 | 58261.5 | 19420.5 | 721.557 |
| typesafe/jev-1.13 | words | 0/36 | 0/18 | 0/18 | 0/12 | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | glyphs | 0/36 | 0/18 | 0/18 | 0/12 | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | canonical | 0/36 | 0/18 | 0/18 | 0/12 | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | operators | 0/36 | 0/18 | 0/18 | 0/12 | unknown | unknown | unknown | unknown |
| typesafe/jev-1.13 | rolling | 0/36 | 0/18 | 0/18 | 0/12 | unknown | unknown | unknown | 0 |
| typesafe/jev-1.13 | vectors | 6/36 | 0/18 | 0/18 | 0/12 | 0.00253361 | 2368.16 | 0 | 410.439 |
| liquid/d1 | minimal | 36/36 | 9/18 | 3/18 | 6/12 | 0.00074232 | 48496.6 | 12124.2 | 564.821 |
| liquid/d1 | words | 36/36 | 10/18 | 0/18 | 7/12 | 0.0029898 | 12040.9 | 3344.71 | 432.871 |
| liquid/d1 | glyphs | 36/36 | 11/18 | 0/18 | 11/12 | 0.043862 | 820.755 | 250.786 | 136.665 |
| liquid/d1 | canonical | 36/36 | 9/18 | 0/18 | 12/12 | 0.0386298 | 931.923 | 232.981 | 144.778 |
| liquid/d1 | operators | 36/36 | 11/18 | 0/18 | 6/12 | 0.0649129 | 554.589 | 169.458 | 118.554 |
| liquid/d1 | rolling | 36/36 | 10/18 | 2/18 | 7/12 | 0.0441752 | 814.936 | 226.371 | 134.732 |
| liquid/d1 | vectors | 36/36 | 9/18 | 0/18 | 10/12 | 0.0439657 | 818.82 | 204.705 | 136.988 |
| perplexity/pplx-decider-v1.1-27b | minimal | 36/36 | 9/18 | 0/18 | 9/12 | 0.00040416 | 89073.6 | 22268.4 | 298.026 |
| perplexity/pplx-decider-v1.1-27b | words | 36/36 | 17/18 | 0/18 | 11/12 | 0.00201894 | 17831.1 | 8420.26 | 357.458 |
| perplexity/pplx-decider-v1.1-27b | glyphs | 36/36 | 17/18 | 0/18 | 11/12 | 0.0239104 | 1505.62 | 710.989 | 61.149 |
| perplexity/pplx-decider-v1.1-27b | canonical | 36/36 | 11/18 | 0/18 | 8/12 | 0.0207578 | 1734.29 | 529.922 | 73.1421 |
| perplexity/pplx-decider-v1.1-27b | operators | 36/36 | 17/18 | 0/18 | 9/12 | 0.0351211 | 1025.03 | 484.04 | 35.8284 |
| perplexity/pplx-decider-v1.1-27b | rolling | 36/36 | 16/18 | 0/18 | 10/12 | 0.0240518 | 1496.77 | 665.23 | 62.3074 |
| perplexity/pplx-decider-v1.1-27b | vectors | 36/36 | 17/18 | 0/18 | 11/12 | 0.0239579 | 1502.64 | 709.579 | 61.2825 |
| perplexity/pplx-decider-v1.1-27b | crop256 | 36/36 | 16/18 | 0/18 | 10/12 | 0.0241825 | 1488.68 | 661.635 | 60.0125 |
| perplexity/pplx-decider-v1.1-27b | crop512 | 36/36 | 17/18 | 0/18 | 11/12 | 0.024189 | 1488.28 | 702.799 | 59.9438 |
| openai/gpt-6-luna-decisions | minimal | 36/36 | 0/18 | 18/18 | 12/12 | ~0.0012559 | 28664.7 | 0 | 476.279 |
| openai/gpt-6-luna-decisions | words | 36/36 | 9/18 | 0/18 | 12/12 | ~0.0031288 | 11506 | 2876.5 | 572.951 |
| openai/gpt-6-luna-decisions | glyphs | 36/36 | 9/18 | 0/18 | 12/12 | ~0.0333028 | 1080.99 | 270.248 | 456.562 |
| openai/gpt-6-luna-decisions | canonical | 36/36 | 9/18 | 0/18 | 12/12 | ~0.0289617 | 1243.02 | 310.755 | 471.029 |
| openai/gpt-6-luna-decisions | operators | 36/36 | 9/18 | 0/18 | 12/12 | ~0.0555538 | 648.02 | 162.005 | 340.302 |
| openai/gpt-6-luna-decisions | rolling | 36/36 | 9/18 | 1/18 | 11/12 | ~0.0335278 | 1073.74 | 268.434 | 483.366 |
| openai/gpt-6-luna-decisions | vectors | 36/36 | 9/18 | 0/18 | 12/12 | ~0.0333748 | 1078.66 | 269.665 | 460.851 |
| openai/gpt-6-luna-decisions | crop256 | 36/36 | 9/18 | 0/18 | 12/12 | ~0.0334288 | 1076.92 | 269.229 | 449.957 |
| openai/gpt-6-luna-decisions | crop512 | 36/36 | 9/18 | 0/18 | 12/12 | ~0.0335152 | 1074.14 | 268.535 | 358.803 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 3.539093162, "machine": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "measurement": "/proc/self/status VmHWM (current executable); sequential CPU process; lifetime RSS, no sampling; includes rendering all crops for every arm", "peak_rss_bytes": 109338624, "python": "3.14.7", "wall_seconds": 3.5681698879925534}`.

Execution: `{"cpu_seconds": 122.903289493, "invocations": 2, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 127811584, "wall_seconds": 554.8705363219779}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| history | 9/18 | 0/18 |

Per-family model results:

- typesafe/jev-1.13 / minimal: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}}`.
- typesafe/jev-1.13 / words: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- typesafe/jev-1.13 / glyphs: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- typesafe/jev-1.13 / canonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- typesafe/jev-1.13 / operators: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- typesafe/jev-1.13 / rolling: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- typesafe/jev-1.13 / vectors: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- liquid/d1 / minimal: `{"history": {"ambiguous_abstentions": 3, "inputs": 36, "known_exact": 9}}`.
- liquid/d1 / words: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 10}}`.
- liquid/d1 / glyphs: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}}`.
- liquid/d1 / canonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- liquid/d1 / operators: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}}`.
- liquid/d1 / rolling: `{"history": {"ambiguous_abstentions": 2, "inputs": 36, "known_exact": 10}}`.
- liquid/d1 / vectors: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- perplexity/pplx-decider-v1.1-27b / minimal: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- perplexity/pplx-decider-v1.1-27b / words: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 17}}`.
- perplexity/pplx-decider-v1.1-27b / glyphs: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 17}}`.
- perplexity/pplx-decider-v1.1-27b / canonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}}`.
- perplexity/pplx-decider-v1.1-27b / operators: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 17}}`.
- perplexity/pplx-decider-v1.1-27b / rolling: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 16}}`.
- perplexity/pplx-decider-v1.1-27b / vectors: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 17}}`.
- perplexity/pplx-decider-v1.1-27b / crop256: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 16}}`.
- perplexity/pplx-decider-v1.1-27b / crop512: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 17}}`.
- openai/gpt-6-luna-decisions / minimal: `{"history": {"ambiguous_abstentions": 18, "inputs": 36, "known_exact": 0}}`.
- openai/gpt-6-luna-decisions / words: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- openai/gpt-6-luna-decisions / glyphs: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- openai/gpt-6-luna-decisions / canonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- openai/gpt-6-luna-decisions / operators: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- openai/gpt-6-luna-decisions / rolling: `{"history": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 9}}`.
- openai/gpt-6-luna-decisions / vectors: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- openai/gpt-6-luna-decisions / crop256: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- openai/gpt-6-luna-decisions / crop512: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.

Request/refusal accounting:

- typesafe/jev-1.13 / minimal: 1/12 requests completed; 33 page inputs refused; reasons `{"persistent model stop": 33}`.
- typesafe/jev-1.13 / words: 0/12 requests completed; 36 page inputs refused; reasons `{"persistent model stop": 36}`.
- typesafe/jev-1.13 / glyphs: 0/12 requests completed; 36 page inputs refused; reasons `{"persistent model stop": 36}`.
- typesafe/jev-1.13 / canonical: 0/12 requests completed; 36 page inputs refused; reasons `{"persistent model stop": 36}`.
- typesafe/jev-1.13 / operators: 0/14 requests completed; 36 page inputs refused; reasons `{"persistent model stop": 36}`.
- typesafe/jev-1.13 / rolling: 1/12 requests completed; 33 page inputs refused; reasons `{"persistent model stop": 33}`.
- typesafe/jev-1.13 / vectors: 2/12 requests completed; 30 page inputs refused; reasons `{"persistent model stop": 30}`.
- liquid/d1 / minimal: 12/12 requests completed; 9 page inputs refused; reasons `{"wave cap": 9}`.
- liquid/d1 / words: 12/12 requests completed; 6 page inputs refused; reasons `{"wave cap": 6}`.
- liquid/d1 / glyphs: 12/12 requests completed; 15 page inputs refused; reasons `{"wave cap": 15}`.
- liquid/d1 / canonical: 12/12 requests completed; 12 page inputs refused; reasons `{"wave cap": 12}`.
- liquid/d1 / operators: 14/14 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- liquid/d1 / rolling: 12/12 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- liquid/d1 / vectors: 12/12 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- perplexity/pplx-decider-v1.1-27b / minimal: 12/12 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- perplexity/pplx-decider-v1.1-27b / words: 12/12 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- perplexity/pplx-decider-v1.1-27b / glyphs: 12/12 requests completed; 6 page inputs refused; reasons `{"wave cap": 6}`.
- perplexity/pplx-decider-v1.1-27b / canonical: 12/12 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- perplexity/pplx-decider-v1.1-27b / operators: 14/14 requests completed; 7 page inputs refused; reasons `{"wave cap": 7}`.
- perplexity/pplx-decider-v1.1-27b / rolling: 12/12 requests completed; 9 page inputs refused; reasons `{"wave cap": 9}`.
- perplexity/pplx-decider-v1.1-27b / vectors: 12/12 requests completed; 9 page inputs refused; reasons `{"wave cap": 9}`.
- perplexity/pplx-decider-v1.1-27b / crop256: 12/12 requests completed; 6 page inputs refused; reasons `{"wave cap": 6}`.
- perplexity/pplx-decider-v1.1-27b / crop512: 12/12 requests completed; 6 page inputs refused; reasons `{"wave cap": 6}`.
- openai/gpt-6-luna-decisions / minimal: 12/12 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- openai/gpt-6-luna-decisions / words: 12/12 requests completed; 9 page inputs refused; reasons `{"wave cap": 9}`.
- openai/gpt-6-luna-decisions / glyphs: 12/12 requests completed; 6 page inputs refused; reasons `{"wave cap": 6}`.
- openai/gpt-6-luna-decisions / canonical: 12/12 requests completed; 12 page inputs refused; reasons `{"wave cap": 12}`.
- openai/gpt-6-luna-decisions / operators: 14/14 requests completed; 6 page inputs refused; reasons `{"wave cap": 6}`.
- openai/gpt-6-luna-decisions / rolling: 12/12 requests completed; 9 page inputs refused; reasons `{"wave cap": 9}`.
- openai/gpt-6-luna-decisions / vectors: 12/12 requests completed; 12 page inputs refused; reasons `{"wave cap": 12}`.
- openai/gpt-6-luna-decisions / crop256: 12/12 requests completed; 3 page inputs refused; reasons `{"wave cap": 3}`.
- openai/gpt-6-luna-decisions / crop512: 12/12 requests completed; 12 page inputs refused; reasons `{"wave cap": 9, "wave cap exhausted before transmission": 3}`.

Persistent model stops: `{"typesafe/jev-1.13": {"reason": "failed or unsettled L001 ledger request", "request_sha256": "ecc0f4a99af8933d77d6a41da4d1154b9975851ac557026b83719b46d55202ff"}}`.
