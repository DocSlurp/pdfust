# L006 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 1305/1728 planned; completed manifest records: 1305/1728. Refused: 423 bodies / 423 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| perplexity/pplx-decider-v1.1-27b | focus-rgb-64 | 1/24 | 1/16 | 0/8 | 0/24 | 1.084e-05 | 92250.9 | 92250.9 | 119.889 |
| perplexity/pplx-decider-v1.1-27b | focus-rgb-128 | 1/24 | 1/16 | 0/8 | 0/24 | 1.278e-05 | 78247.3 | 78247.3 | 98.0932 |
| perplexity/pplx-decider-v1.1-27b | focus-rgb-256 | 2/24 | 0/16 | 0/8 | 0/24 | 2.168e-05 | 92250.9 | 0 | 61.6596 |
| perplexity/pplx-decider-v1.1-27b | focus-rgb-400 | 1/24 | 1/16 | 0/8 | 0/24 | 1.088e-05 | 91911.8 | 91911.8 | 65.9615 |
| perplexity/pplx-decider-v1.1-27b | focus-rgb-500 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-rgb-512 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-gray-64 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-gray-128 | 1/24 | 0/16 | 0/8 | 0/24 | 1.272e-05 | 78616.4 | 0 | 93.5482 |
| perplexity/pplx-decider-v1.1-27b | focus-gray-256 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-gray-400 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-gray-500 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-gray-512 | 1/24 | 1/16 | 0/8 | 0/24 | 1.278e-05 | 78247.3 | 78247.3 | 134.789 |
| perplexity/pplx-decider-v1.1-27b | focus-lowbit-64 | 1/24 | 1/16 | 0/8 | 0/24 | 1.086e-05 | 92081 | 92081 | 123.544 |
| perplexity/pplx-decider-v1.1-27b | focus-lowbit-128 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-lowbit-256 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | 0 |
| perplexity/pplx-decider-v1.1-27b | focus-lowbit-400 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-lowbit-500 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | focus-lowbit-512 | 0/24 | 0/16 | 0/8 | 0/24 | unknown | unknown | unknown | unknown |
| openai/gpt-6-luna-decisions | focus-rgb-64 | 24/24 | 7/16 | 0/8 | 0/24 | ~0.0010092 | 23781.2 | 6936.19 | 205.479 |
| openai/gpt-6-luna-decisions | focus-rgb-128 | 24/24 | 7/16 | 0/8 | 0/24 | ~0.0010188 | 23557.1 | 6870.83 | 185.202 |
| openai/gpt-6-luna-decisions | focus-rgb-256 | 24/24 | 6/16 | 0/8 | 0/24 | ~0.001062 | 22598.9 | 5649.72 | 177.652 |
| openai/gpt-6-luna-decisions | focus-rgb-400 | 24/24 | 8/16 | 1/8 | 0/24 | ~0.0011292 | 21254 | 7084.66 | 176.529 |
| openai/gpt-6-luna-decisions | focus-rgb-500 | 24/24 | 7/16 | 1/8 | 0/24 | ~0.0011964 | 20060.2 | 5850.89 | 197.898 |
| openai/gpt-6-luna-decisions | focus-rgb-512 | 24/24 | 7/16 | 1/8 | 0/24 | ~0.0011964 | 20060.2 | 5850.89 | 187.221 |
| openai/gpt-6-luna-decisions | focus-gray-64 | 24/24 | 7/16 | 0/8 | 0/24 | ~0.0010092 | 23781.2 | 6936.19 | 161.378 |
| openai/gpt-6-luna-decisions | focus-gray-128 | 24/24 | 6/16 | 1/8 | 0/24 | ~0.0010188 | 23557.1 | 5889.28 | 199.566 |
| openai/gpt-6-luna-decisions | focus-gray-256 | 24/24 | 8/16 | 0/8 | 0/24 | ~0.001062 | 22598.9 | 7532.96 | 213.161 |
| openai/gpt-6-luna-decisions | focus-gray-400 | 24/24 | 7/16 | 1/8 | 0/24 | ~0.0011292 | 21254 | 6199.08 | 162.4 |
| openai/gpt-6-luna-decisions | focus-gray-500 | 24/24 | 7/16 | 1/8 | 0/24 | ~0.0011964 | 20060.2 | 5850.89 | 176.472 |
| openai/gpt-6-luna-decisions | focus-gray-512 | 24/24 | 8/16 | 1/8 | 0/24 | ~0.0011964 | 20060.2 | 6686.73 | 191.418 |
| openai/gpt-6-luna-decisions | focus-lowbit-64 | 24/24 | 6/16 | 3/8 | 0/24 | ~0.0010116 | 23724.8 | 5931.2 | 157.829 |
| openai/gpt-6-luna-decisions | focus-lowbit-128 | 24/24 | 8/16 | 1/8 | 0/24 | ~0.0010212 | 23501.8 | 7833.92 | 200.191 |
| openai/gpt-6-luna-decisions | focus-lowbit-256 | 24/24 | 7/16 | 1/8 | 0/24 | ~0.0010644 | 22547.9 | 6576.48 | 194.092 |
| openai/gpt-6-luna-decisions | focus-lowbit-400 | 24/24 | 6/16 | 1/8 | 0/24 | ~0.0011316 | 21208.9 | 5302.23 | 169.221 |
| openai/gpt-6-luna-decisions | focus-lowbit-500 | 24/24 | 7/16 | 1/8 | 0/24 | ~0.0011988 | 20020 | 5839.17 | 158.599 |
| openai/gpt-6-luna-decisions | focus-lowbit-512 | 24/24 | 7/16 | 1/8 | 0/24 | ~0.0011988 | 20020 | 5839.17 | 171.545 |
| cloudflare/clef-flash | focus-rgb-64 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00130536 | 18385.7 | 6128.58 | 147.528 |
| cloudflare/clef-flash | focus-rgb-128 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00132804 | 18071.7 | 6023.91 | 148.591 |
| cloudflare/clef-flash | focus-rgb-256 | 24/24 | 9/16 | 0/8 | 0/24 | 0.00132912 | 18057.1 | 6771.4 | 128.477 |
| cloudflare/clef-flash | focus-rgb-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00132912 | 18057.1 | 6019.02 | 131.338 |
| cloudflare/clef-flash | focus-rgb-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00136584 | 17571.6 | 5857.2 | 140.635 |
| cloudflare/clef-flash | focus-rgb-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00136584 | 17571.6 | 5857.2 | 116.646 |
| cloudflare/clef-flash | focus-gray-64 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00130536 | 18385.7 | 6128.58 | 146.146 |
| cloudflare/clef-flash | focus-gray-128 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00132804 | 18071.7 | 6023.91 | 150.041 |
| cloudflare/clef-flash | focus-gray-256 | 24/24 | 9/16 | 0/8 | 0/24 | 0.00132912 | 18057.1 | 6771.4 | 145.009 |
| cloudflare/clef-flash | focus-gray-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00132912 | 18057.1 | 6019.02 | 138.254 |
| cloudflare/clef-flash | focus-gray-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00136584 | 17571.6 | 5857.2 | 136.227 |
| cloudflare/clef-flash | focus-gray-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00136584 | 17571.6 | 5857.2 | 134.751 |
| cloudflare/clef-flash | focus-lowbit-64 | 24/24 | 9/16 | 0/8 | 0/24 | 0.00130752 | 18355.4 | 6883.26 | 125.838 |
| cloudflare/clef-flash | focus-lowbit-128 | 24/24 | 9/16 | 0/8 | 0/24 | 0.0013302 | 18042.4 | 6765.9 | 110.024 |
| cloudflare/clef-flash | focus-lowbit-256 | 24/24 | 12/16 | 0/8 | 0/24 | 0.00133128 | 18027.8 | 9013.88 | 145.003 |
| cloudflare/clef-flash | focus-lowbit-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00133128 | 18027.8 | 6009.25 | 133.111 |
| cloudflare/clef-flash | focus-lowbit-500 | 24/24 | 10/16 | 0/8 | 0/24 | 0.001368 | 17543.9 | 7309.94 | 130.094 |
| cloudflare/clef-flash | focus-lowbit-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.001368 | 17543.9 | 5847.95 | 113.519 |
| cloudflare/clef | focus-rgb-64 | 24/24 | 7/16 | 0/8 | 0/24 | 0.00348096 | 6894.65 | 2010.94 | 114.439 |
| cloudflare/clef | focus-rgb-128 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00354144 | 6776.9 | 2258.97 | 124.242 |
| cloudflare/clef | focus-rgb-256 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00354432 | 6771.4 | 2257.13 | 103.895 |
| cloudflare/clef | focus-rgb-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00354432 | 6771.4 | 2257.13 | 104.112 |
| cloudflare/clef | focus-rgb-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00364224 | 6589.35 | 2196.45 | 111.595 |
| cloudflare/clef | focus-rgb-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00364224 | 6589.35 | 2196.45 | 49.1038 |
| cloudflare/clef | focus-gray-64 | 24/24 | 7/16 | 0/8 | 0/24 | 0.00348096 | 6894.65 | 2010.94 | 113.745 |
| cloudflare/clef | focus-gray-128 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00354144 | 6776.9 | 2258.97 | 109.248 |
| cloudflare/clef | focus-gray-256 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00354432 | 6771.4 | 2257.13 | 117.333 |
| cloudflare/clef | focus-gray-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00354432 | 6771.4 | 2257.13 | 98.5287 |
| cloudflare/clef | focus-gray-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00364224 | 6589.35 | 2196.45 | 106.238 |
| cloudflare/clef | focus-gray-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00364224 | 6589.35 | 2196.45 | 109.315 |
| cloudflare/clef | focus-lowbit-64 | 24/24 | 7/16 | 0/8 | 0/24 | 0.00348672 | 6883.26 | 2007.62 | 106.173 |
| cloudflare/clef | focus-lowbit-128 | 24/24 | 9/16 | 0/8 | 0/24 | 0.0035472 | 6765.9 | 2537.21 | 106.15 |
| cloudflare/clef | focus-lowbit-256 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00355008 | 6760.41 | 2253.47 | 100.966 |
| cloudflare/clef | focus-lowbit-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00355008 | 6760.41 | 2253.47 | 103.445 |
| cloudflare/clef | focus-lowbit-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.003648 | 6578.95 | 2192.98 | 117.465 |
| cloudflare/clef | focus-lowbit-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.003648 | 6578.95 | 2192.98 | 110.481 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `null`.

Execution: `{"cpu_seconds": 587.619070456, "invocations": 4, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 150454272, "wall_seconds": 1319.8968876840372}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 4/8 | 0/4 |
| wrap | 4/8 | 0/4 |

Per-family model results:

- perplexity/pplx-decider-v1.1-27b / focus-rgb-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- openai/gpt-6-luna-decisions / focus-rgb-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-rgb-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-rgb-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-rgb-400: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- openai/gpt-6-luna-decisions / focus-rgb-500: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-rgb-512: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- openai/gpt-6-luna-decisions / focus-gray-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-gray-128: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-gray-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-gray-400: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-gray-500: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-gray-512: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-lowbit-64: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-lowbit-128: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-lowbit-256: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-lowbit-400: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-lowbit-500: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / focus-lowbit-512: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-rgb-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-rgb-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-rgb-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef-flash / focus-rgb-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-rgb-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-rgb-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-gray-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-gray-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-gray-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef-flash / focus-gray-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-gray-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-gray-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-lowbit-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef-flash / focus-lowbit-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef-flash / focus-lowbit-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- cloudflare/clef-flash / focus-lowbit-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / focus-lowbit-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}}`.
- cloudflare/clef-flash / focus-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-rgb-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-rgb-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-rgb-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-rgb-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-rgb-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-rgb-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-gray-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-gray-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-gray-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-gray-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-gray-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-gray-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-lowbit-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-lowbit-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-lowbit-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-lowbit-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-lowbit-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / focus-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.

Request/refusal accounting:

- perplexity/pplx-decider-v1.1-27b / focus-rgb-64: 1/24 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-128: 1/24 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-256: 2/24 request bodies and 2/24 records completed; 22 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 22}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-400: 1/24 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-500: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-rgb-512: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-64: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-128: 1/24 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-256: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-400: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-500: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-gray-512: 1/24 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-64: 1/24 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-128: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-256: 1/24 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-400: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-500: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- perplexity/pplx-decider-v1.1-27b / focus-lowbit-512: 0/24 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- openai/gpt-6-luna-decisions / focus-rgb-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-rgb-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-rgb-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-rgb-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-rgb-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-gray-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-gray-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-gray-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-gray-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-gray-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-lowbit-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-lowbit-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-lowbit-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-lowbit-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-lowbit-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / focus-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-rgb-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-rgb-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-rgb-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-rgb-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-rgb-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-gray-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-gray-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-gray-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-gray-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-gray-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-lowbit-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-lowbit-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-lowbit-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-lowbit-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-lowbit-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / focus-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-rgb-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-rgb-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-rgb-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-rgb-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-rgb-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-gray-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-gray-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-gray-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-gray-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-gray-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-lowbit-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-lowbit-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-lowbit-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-lowbit-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-lowbit-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / focus-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{"perplexity/pplx-decider-v1.1-27b": {"reason": "failed or unsettled L006/ ledger request", "request_sha256": "58843eaded211c89d9833b6d43fe166d047638f8e547036e901af9c473145644"}}`.
