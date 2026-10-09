# L015: fresh image resolution comparison

All 864 unique requests completed: 24 DEV source representatives × four models × three fresh crop sizes × three formats. Each arm contains 16 authored-known and eight ambiguous inputs. These are supplied-region grouping decisions, not complete-page extraction. No protected confirmation documents were accessed.

Images were freshly rendered from the same source PDFs at 512, 768 and 1024 longest-edge pixels. RGB, grayscale and two-bit palette are separate format arms. The source text projection and questions are fixed within this matrix; these pixels differ from the older retained-crop sweep, so L006 versus L015 is not an isolated size comparison.

## Quality and paired changes

| Model | Format | Known correct at 512 / 768 / 1024 (each /16) | Ambiguous abstentions (each /8) | 768 vs 512: gains / losses | 1024 vs 512: gains / losses |
|---|---|---|---|---|---|
| perplexity/pplx-decider-v1.1-27b | rgb | 12 / 12 / 13 | 0 / 0 / 0 | 0 / 0 | 1 / 0 |
| perplexity/pplx-decider-v1.1-27b | gray | 12 / 12 / 12 | 0 / 0 / 0 | 0 / 0 | 0 / 0 |
| perplexity/pplx-decider-v1.1-27b | lowbit | 12 / 12 / 12 | 0 / 0 / 0 | 0 / 0 | 0 / 0 |
| openai/gpt-6-luna-decisions | rgb | 7 / 7 / 11 | 2 / 1 / 1 | 0 / 0 | 4 / 0 |
| openai/gpt-6-luna-decisions | gray | 6 / 7 / 11 | 2 / 2 / 2 | 1 / 0 | 5 / 0 |
| openai/gpt-6-luna-decisions | lowbit | 6 / 7 / 10 | 0 / 1 / 1 | 1 / 0 | 4 / 0 |
| cloudflare/clef-flash | rgb | 9 / 11 / 10 | 0 / 0 / 0 | 2 / 0 | 2 / 1 |
| cloudflare/clef-flash | gray | 9 / 11 / 10 | 0 / 0 / 0 | 2 / 0 | 2 / 1 |
| cloudflare/clef-flash | lowbit | 8 / 11 / 10 | 0 / 0 / 0 | 3 / 0 | 2 / 0 |
| cloudflare/clef | rgb | 9 / 9 / 10 | 0 / 0 / 0 | 1 / 1 | 2 / 1 |
| cloudflare/clef | gray | 8 / 9 / 11 | 0 / 0 / 0 | 1 / 0 | 3 / 0 |
| cloudflare/clef | lowbit | 8 / 9 / 10 | 0 / 0 / 0 | 1 / 0 | 2 / 0 |

Luna gained four known RGB decisions at 1024, all wrap cases, with no known losses; ambiguous abstention fell from 2/8 to 1/8. Grayscale gained five known decisions and retained 2/8 abstention. Clef-Flash favored 768 on all three formats; its RGB/gray 1024 arms each had one known regression relative to 512. PPLX gained one boundary decision only for RGB1024. Clef improved most on gray1024 (three gains, no known losses). These are single observations on a small DEV cohort, not estimates of population gains.

## Cost, timing and resources

Total effective inference cost: USD 0.062818012, including USD 0.0131148 estimated for Luna from reported tokens and frozen rates. Other charges were positive provider-reported USD. All 216 Flash calls report Cloudflare as provider, but their observed input rates split between USD 0.09/M (86 calls) and USD 0.038/M (130 calls). Cache counters are unreported. Therefore the cheaper RGB768 aggregate is not evidence that increased resolution intrinsically lowers cost, nor evidence of a provider cache hit.

Preparation: 3.72 s wall, 3.73 s CPU, 130.3 MiB process-lifetime peak RSS. Two serial execution invocations: 917.61 s wall, 464.19 s CPU, 149.6 MiB maximum process-lifetime RSS. Wall includes HTTP waits, telemetry and checkpoint work; preparation is separate. Measurements use process counters and Linux VmHWM, no utilization sampling; provider CPU/RAM/GPU are unmeasured. Concurrent CPU-only validation ran for part of execution, so wall throughput is not an isolated-host benchmark. API-only rates below sum HTTP intervals and exclude local work.

Next experiments should pair Luna gray1024 with the frozen geometry gate and rolling row state; compare Flash768 against earlier lowbit256; and cross PPLX resolved prompt criteria with the fresh crop settings. Preserve all regressions and test source-driven routing rather than selecting a model using reference labels.

## Complete per-arm rates and retained scoring

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| perplexity/pplx-decider-v1.1-27b | fresh-rgb-512 | 24/24 | 12/16 | 0/8 | unmeasured | 0.00027808 | 86306.1 | 43153 | 134.708 |
| perplexity/pplx-decider-v1.1-27b | fresh-rgb-768 | 24/24 | 12/16 | 0/8 | unmeasured | 0.00031192 | 76942.8 | 38471.4 | 131.973 |
| perplexity/pplx-decider-v1.1-27b | fresh-rgb-1024 | 24/24 | 13/16 | 0/8 | unmeasured | 0.00037768 | 63545.9 | 34420.7 | 147.261 |
| perplexity/pplx-decider-v1.1-27b | fresh-gray-512 | 24/24 | 12/16 | 0/8 | unmeasured | 0.00027808 | 86306.1 | 43153 | 141.385 |
| perplexity/pplx-decider-v1.1-27b | fresh-gray-768 | 24/24 | 12/16 | 0/8 | unmeasured | 0.00031192 | 76942.8 | 38471.4 | 140.062 |
| perplexity/pplx-decider-v1.1-27b | fresh-gray-1024 | 24/24 | 12/16 | 0/8 | unmeasured | 0.00037768 | 63545.9 | 31772.9 | 119.726 |
| perplexity/pplx-decider-v1.1-27b | fresh-lowbit-512 | 24/24 | 12/16 | 0/8 | unmeasured | 0.00027856 | 86157.4 | 43078.7 | 141.607 |
| perplexity/pplx-decider-v1.1-27b | fresh-lowbit-768 | 24/24 | 12/16 | 0/8 | unmeasured | 0.0003124 | 76824.6 | 38412.3 | 139.637 |
| perplexity/pplx-decider-v1.1-27b | fresh-lowbit-1024 | 24/24 | 12/16 | 0/8 | unmeasured | 0.00037816 | 63465.2 | 31732.6 | 138.235 |
| openai/gpt-6-luna-decisions | fresh-rgb-512 | 24/24 | 7/16 | 2/8 | unmeasured | ~0.0011964 | 20060.2 | 5850.89 | 165.991 |
| openai/gpt-6-luna-decisions | fresh-rgb-768 | 24/24 | 7/16 | 1/8 | unmeasured | ~0.0014364 | 16708.4 | 4873.29 | 187.365 |
| openai/gpt-6-luna-decisions | fresh-rgb-1024 | 24/24 | 11/16 | 1/8 | unmeasured | ~0.0017364 | 13821.7 | 6334.95 | 163.416 |
| openai/gpt-6-luna-decisions | fresh-gray-512 | 24/24 | 6/16 | 2/8 | unmeasured | ~0.0011964 | 20060.2 | 5015.05 | 197.452 |
| openai/gpt-6-luna-decisions | fresh-gray-768 | 24/24 | 7/16 | 2/8 | unmeasured | ~0.0014364 | 16708.4 | 4873.29 | 135.087 |
| openai/gpt-6-luna-decisions | fresh-gray-1024 | 24/24 | 11/16 | 2/8 | unmeasured | ~0.0017364 | 13821.7 | 6334.95 | 165.906 |
| openai/gpt-6-luna-decisions | fresh-lowbit-512 | 24/24 | 6/16 | 0/8 | unmeasured | ~0.0011988 | 20020 | 5005.01 | 131.009 |
| openai/gpt-6-luna-decisions | fresh-lowbit-768 | 24/24 | 7/16 | 1/8 | unmeasured | ~0.0014388 | 16680.6 | 4865.17 | 150.205 |
| openai/gpt-6-luna-decisions | fresh-lowbit-1024 | 24/24 | 10/16 | 1/8 | unmeasured | ~0.0017388 | 13802.6 | 5751.09 | 164.95 |
| cloudflare/clef-flash | fresh-rgb-512 | 24/24 | 9/16 | 0/8 | unmeasured | 0.000931692 | 25759.6 | 9659.84 | 133.495 |
| cloudflare/clef-flash | fresh-rgb-768 | 24/24 | 11/16 | 0/8 | unmeasured | 0.000824128 | 29121.7 | 13347.4 | 137.371 |
| cloudflare/clef-flash | fresh-rgb-1024 | 24/24 | 10/16 | 0/8 | unmeasured | 0.00111662 | 21493.5 | 8955.63 | 134.231 |
| cloudflare/clef-flash | fresh-gray-512 | 24/24 | 9/16 | 0/8 | unmeasured | 0.00100158 | 23962.1 | 8985.8 | 124.206 |
| cloudflare/clef-flash | fresh-gray-768 | 24/24 | 11/16 | 0/8 | unmeasured | 0.00108324 | 22155.7 | 10154.7 | 151.685 |
| cloudflare/clef-flash | fresh-gray-1024 | 24/24 | 10/16 | 0/8 | unmeasured | 0.0011968 | 20053.5 | 8355.61 | 129.438 |
| cloudflare/clef-flash | fresh-lowbit-512 | 24/24 | 8/16 | 0/8 | unmeasured | 0.000766256 | 31321.1 | 10440.4 | 86.7418 |
| cloudflare/clef-flash | fresh-lowbit-768 | 24/24 | 11/16 | 0/8 | unmeasured | 0.000972304 | 24683.6 | 11313.3 | 150.345 |
| cloudflare/clef-flash | fresh-lowbit-1024 | 24/24 | 10/16 | 0/8 | unmeasured | 0.00130483 | 18393.2 | 7663.82 | 128.016 |
| cloudflare/clef | fresh-rgb-512 | 24/24 | 9/16 | 0/8 | unmeasured | 0.00364224 | 6589.35 | 2471.01 | 113.059 |
| cloudflare/clef | fresh-rgb-768 | 24/24 | 9/16 | 0/8 | unmeasured | 0.00404832 | 5928.39 | 2223.14 | 93.4563 |
| cloudflare/clef | fresh-rgb-1024 | 24/24 | 10/16 | 0/8 | unmeasured | 0.00483744 | 4961.3 | 2067.21 | 88.7081 |
| cloudflare/clef | fresh-gray-512 | 24/24 | 8/16 | 0/8 | unmeasured | 0.00364224 | 6589.35 | 2196.45 | 112.88 |
| cloudflare/clef | fresh-gray-768 | 24/24 | 9/16 | 0/8 | unmeasured | 0.00404832 | 5928.39 | 2223.14 | 107.911 |
| cloudflare/clef | fresh-gray-1024 | 24/24 | 11/16 | 0/8 | unmeasured | 0.00483744 | 4961.3 | 2273.93 | 106.004 |
| cloudflare/clef | fresh-lowbit-512 | 24/24 | 8/16 | 0/8 | unmeasured | 0.003648 | 6578.95 | 2192.98 | 93.9506 |
| cloudflare/clef | fresh-lowbit-768 | 24/24 | 9/16 | 0/8 | unmeasured | 0.00405408 | 5919.96 | 2219.99 | 108.338 |
| cloudflare/clef | fresh-lowbit-1024 | 24/24 | 10/16 | 0/8 | unmeasured | 0.0048432 | 4955.4 | 2064.75 | 104.343 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 3.7325700729999998, "peak_rss_bytes": 136638464, "scope": "serial current process counters and Linux VmHWM, no sampling/provider/GPU", "wall_seconds": 3.715225964988349}`.

Execution: `{"cpu_seconds": 464.192502406, "invocations": 2, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 156868608, "wall_seconds": 917.6063656430051}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 4/8 | 0/4 |
| wrap | 4/8 | 0/4 |

Per-family model results:

- perplexity/pplx-decider-v1.1-27b / fresh-rgb-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-rgb-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-rgb-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-gray-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-gray-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-gray-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-lowbit-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- perplexity/pplx-decider-v1.1-27b / fresh-lowbit-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- openai/gpt-6-luna-decisions / fresh-rgb-512: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / fresh-rgb-768: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / fresh-rgb-1024: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- openai/gpt-6-luna-decisions / fresh-gray-512: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / fresh-gray-768: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / fresh-gray-1024: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- openai/gpt-6-luna-decisions / fresh-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / fresh-lowbit-768: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- openai/gpt-6-luna-decisions / fresh-lowbit-1024: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 8}}`.
- cloudflare/clef-flash / fresh-rgb-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef-flash / fresh-rgb-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 7}}`.
- cloudflare/clef-flash / fresh-rgb-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}}`.
- cloudflare/clef-flash / fresh-gray-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef-flash / fresh-gray-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 7}}`.
- cloudflare/clef-flash / fresh-gray-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}}`.
- cloudflare/clef-flash / fresh-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef-flash / fresh-lowbit-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 7}}`.
- cloudflare/clef-flash / fresh-lowbit-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}}`.
- cloudflare/clef / fresh-rgb-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / fresh-rgb-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef / fresh-rgb-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}}`.
- cloudflare/clef / fresh-gray-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / fresh-gray-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef / fresh-gray-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 7}}`.
- cloudflare/clef / fresh-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- cloudflare/clef / fresh-lowbit-768: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}}`.
- cloudflare/clef / fresh-lowbit-1024: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}}`.

Request/refusal accounting:

- perplexity/pplx-decider-v1.1-27b / fresh-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-rgb-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-rgb-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-gray-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-gray-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-lowbit-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / fresh-lowbit-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-rgb-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-rgb-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-gray-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-gray-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-lowbit-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / fresh-lowbit-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-rgb-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-rgb-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-gray-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-gray-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-lowbit-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef-flash / fresh-lowbit-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-rgb-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-rgb-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-gray-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-gray-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-lowbit-768: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- cloudflare/clef / fresh-lowbit-1024: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{}`.
