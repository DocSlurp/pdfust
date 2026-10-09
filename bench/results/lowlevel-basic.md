# L001 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 768/768 planned; completed manifest records: 768/768. Refused: 0 bodies / 0 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| typesafe/jev-1.13 | minimal | 72/72 | 22/48 | 1/24 | 14/24 | 0.00109015 | 66045.8 | 20180.7 | 686.054 |
| typesafe/jev-1.13 | words | 72/72 | 28/48 | 0/24 | 20/24 | 0.00167706 | 42932.3 | 16695.9 | 652.3 |
| typesafe/jev-1.13 | glyphs | 72/72 | 25/48 | 0/24 | 21/24 | 0.00726239 | 9914.09 | 3442.39 | 559.921 |
| typesafe/jev-1.13 | canonical | 72/72 | 24/48 | 0/24 | 23/24 | 0.00632646 | 11380.8 | 3793.59 | 619.738 |
| typesafe/jev-1.13 | operators | 72/72 | 27/48 | 0/24 | 17/24 | 0.0114906 | 6265.98 | 2349.74 | 564.835 |
| typesafe/jev-1.13 | rolling | 72/72 | 24/48 | 0/24 | 21/24 | 0.00744685 | 9668.51 | 3222.84 | 556.21 |
| typesafe/jev-1.13 | vectors | 72/72 | 25/48 | 0/24 | 22/24 | 0.00766811 | 9389.54 | 3260.26 | 613.868 |
| liquid/d1 | minimal | 72/72 | 23/48 | 0/24 | 16/24 | 0.00108216 | 66533.6 | 21253.8 | 533.639 |
| liquid/d1 | words | 72/72 | 24/48 | 2/24 | 19/24 | 0.00231588 | 31089.7 | 10363.2 | 530.088 |
| liquid/d1 | glyphs | 72/72 | 25/48 | 0/24 | 19/24 | 0.01885 | 3819.64 | 1326.26 | 327.981 |
| liquid/d1 | canonical | 72/72 | 24/48 | 0/24 | 24/24 | 0.0166298 | 4329.57 | 1443.19 | 311.522 |
| liquid/d1 | operators | 72/72 | 23/48 | 0/24 | 20/24 | 0.031132 | 2312.74 | 738.791 | 229.309 |
| liquid/d1 | rolling | 72/72 | 25/48 | 0/24 | 18/24 | 0.0194375 | 3704.18 | 1286.17 | 306.527 |
| liquid/d1 | vectors | 72/72 | 26/48 | 0/24 | 19/24 | 0.0198004 | 3636.3 | 1313.11 | 298.021 |
| perplexity/pplx-decider-v1.1-27b | minimal | 72/72 | 28/48 | 0/24 | 21/24 | 0.0005868 | 122699 | 47716.4 | 384.329 |
| perplexity/pplx-decider-v1.1-27b | words | 72/72 | 26/48 | 0/24 | 19/24 | 0.00147384 | 48852 | 17641 | 372.821 |
| perplexity/pplx-decider-v1.1-27b | glyphs | 72/72 | 24/48 | 0/24 | 17/24 | 0.010157 | 7088.68 | 2362.89 | 192.02 |
| perplexity/pplx-decider-v1.1-27b | canonical | 72/72 | 22/48 | 0/24 | 15/24 | 0.0088875 | 8101.27 | 2475.39 | 250.816 |
| perplexity/pplx-decider-v1.1-27b | operators | 72/72 | 24/48 | 0/24 | 15/24 | 0.0166672 | 4319.87 | 1439.96 | 152.987 |
| perplexity/pplx-decider-v1.1-27b | rolling | 72/72 | 25/48 | 0/24 | 12/24 | 0.0104119 | 6915.15 | 2401.09 | 194.635 |
| perplexity/pplx-decider-v1.1-27b | vectors | 72/72 | 30/48 | 0/24 | 17/24 | 0.0107705 | 6684.94 | 2785.39 | 209.067 |
| perplexity/pplx-decider-v1.1-27b | crop256 | 72/72 | 36/48 | 0/24 | 19/24 | 0.0106906 | 6734.91 | 3367.46 | 203.368 |
| perplexity/pplx-decider-v1.1-27b | crop512 | 72/72 | 38/48 | 0/24 | 19/24 | 0.010764 | 6688.96 | 3530.29 | 204.785 |
| openai/gpt-6-luna-decisions | minimal | 72/72 | 4/48 | 24/24 | 20/24 | ~0.0022137 | 32524.7 | 1806.93 | 565.875 |
| openai/gpt-6-luna-decisions | words | 72/72 | 22/48 | 10/24 | 12/24 | ~0.0032406 | 22218.1 | 6788.87 | 553.83 |
| openai/gpt-6-luna-decisions | glyphs | 72/72 | 23/48 | 1/24 | 22/24 | ~0.0154572 | 4658.02 | 1487.98 | 526.86 |
| openai/gpt-6-luna-decisions | canonical | 72/72 | 23/48 | 2/24 | 19/24 | ~0.0136158 | 5287.97 | 1689.21 | 457.444 |
| openai/gpt-6-luna-decisions | operators | 72/72 | 23/48 | 1/24 | 18/24 | ~0.0249683 | 2883.66 | 921.168 | 428.642 |
| openai/gpt-6-luna-decisions | rolling | 72/72 | 24/48 | 0/24 | 18/24 | ~0.0158748 | 4535.49 | 1511.83 | 535.658 |
| openai/gpt-6-luna-decisions | vectors | 72/72 | 26/48 | 0/24 | 22/24 | ~0.0162024 | 4443.79 | 1604.7 | 528.468 |
| openai/gpt-6-luna-decisions | crop256 | 72/72 | 25/48 | 0/24 | 22/24 | ~0.0158244 | 4549.94 | 1579.84 | 490.554 |
| openai/gpt-6-luna-decisions | crop512 | 72/72 | 25/48 | 0/24 | 23/24 | ~0.0162276 | 4436.89 | 1540.59 | 517.689 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 4.590087625000001, "machine": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "measurement": "/proc/self/status VmHWM (current executable); sequential CPU process; lifetime RSS, no sampling; includes rendering all crops for every arm", "peak_rss_bytes": 100085760, "python": "3.14.7", "wall_seconds": 4.578611534991069}`.

Execution: `{"cpu_seconds": 350.087274889, "invocations": 2, "measurement": "Summed exact retained pilot/resume wall and process CPU; maximum kernel current-process lifetime RSS; sequential HTTP; no sampling; excludes prep and inter-invocation downtime; remote CPU/RAM unmeasured", "peak_rss_bytes": 126242816, "wall_seconds": 798.3528456619824}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 12/24 | 0/12 |
| wrap | 12/24 | 0/12 |

Per-family model results:

- typesafe/jev-1.13 / minimal: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 9}}`.
- typesafe/jev-1.13 / words: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 16}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- typesafe/jev-1.13 / glyphs: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- typesafe/jev-1.13 / canonical: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- typesafe/jev-1.13 / operators: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 15}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- typesafe/jev-1.13 / rolling: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- typesafe/jev-1.13 / vectors: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- liquid/d1 / minimal: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 10}}`.
- liquid/d1 / words: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- liquid/d1 / glyphs: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- liquid/d1 / canonical: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- liquid/d1 / operators: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- liquid/d1 / rolling: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- liquid/d1 / vectors: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 14}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- perplexity/pplx-decider-v1.1-27b / minimal: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 15}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}}`.
- perplexity/pplx-decider-v1.1-27b / words: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 14}}`.
- perplexity/pplx-decider-v1.1-27b / glyphs: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}}`.
- perplexity/pplx-decider-v1.1-27b / canonical: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 8}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 14}}`.
- perplexity/pplx-decider-v1.1-27b / operators: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}}`.
- perplexity/pplx-decider-v1.1-27b / rolling: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}}`.
- perplexity/pplx-decider-v1.1-27b / vectors: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 19}}`.
- perplexity/pplx-decider-v1.1-27b / crop256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 24}}`.
- perplexity/pplx-decider-v1.1-27b / crop512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 14}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 24}}`.
- openai/gpt-6-luna-decisions / minimal: `{"boundary": {"ambiguous_abstentions": 12, "inputs": 36, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 12, "inputs": 36, "known_exact": 2}}`.
- openai/gpt-6-luna-decisions / words: `{"boundary": {"ambiguous_abstentions": 4, "inputs": 36, "known_exact": 11}, "wrap": {"ambiguous_abstentions": 6, "inputs": 36, "known_exact": 11}}`.
- openai/gpt-6-luna-decisions / glyphs: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 12}}`.
- openai/gpt-6-luna-decisions / canonical: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 12}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 11}}`.
- openai/gpt-6-luna-decisions / operators: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 10}}`.
- openai/gpt-6-luna-decisions / rolling: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 11}}`.
- openai/gpt-6-luna-decisions / vectors: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 14}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- openai/gpt-6-luna-decisions / crop256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- openai/gpt-6-luna-decisions / crop512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 13}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.

Request/refusal accounting:

- typesafe/jev-1.13 / minimal: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- typesafe/jev-1.13 / words: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- typesafe/jev-1.13 / glyphs: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- typesafe/jev-1.13 / canonical: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- typesafe/jev-1.13 / operators: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- typesafe/jev-1.13 / rolling: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- typesafe/jev-1.13 / vectors: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / minimal: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / words: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / glyphs: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / canonical: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / operators: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / rolling: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / vectors: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / minimal: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / words: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / glyphs: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / canonical: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / operators: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / rolling: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / vectors: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / crop256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / crop512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / minimal: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / words: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / glyphs: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / canonical: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / operators: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / rolling: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / vectors: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / crop256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / crop512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{}`.
