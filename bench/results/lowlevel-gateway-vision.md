# L009 lower-level DEV decisions

VISUAL INPUT UNVERIFIED: TypeSafe top-level images forwarding is undocumented; these scores/costs do not establish vision quality or resolution effects. authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 432/432 planned; completed manifest records: 432/432. Refused: 0 bodies / 0 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| liquid/d1 | focus-rgb-64 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 136.383 |
| liquid/d1 | focus-rgb-128 | 24/24 | 9/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 27654.9 | 136.912 |
| liquid/d1 | focus-rgb-256 | 24/24 | 9/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 27654.9 | 151.296 |
| liquid/d1 | focus-rgb-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 132.603 |
| liquid/d1 | focus-rgb-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 136.23 |
| liquid/d1 | focus-rgb-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 88.503 |
| liquid/d1 | focus-gray-64 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 152.623 |
| liquid/d1 | focus-gray-128 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 147.512 |
| liquid/d1 | focus-gray-256 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 142.797 |
| liquid/d1 | focus-gray-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 131.293 |
| liquid/d1 | focus-gray-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 140.458 |
| liquid/d1 | focus-gray-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.00032544 | 73746.3 | 24582.1 | 149.122 |
| liquid/d1 | focus-lowbit-64 | 24/24 | 9/16 | 0/8 | 0/24 | 0.0003264 | 73529.4 | 27573.5 | 140.111 |
| liquid/d1 | focus-lowbit-128 | 24/24 | 9/16 | 1/8 | 0/24 | 0.0003264 | 73529.4 | 27573.5 | 144.549 |
| liquid/d1 | focus-lowbit-256 | 24/24 | 9/16 | 0/8 | 0/24 | 0.0003264 | 73529.4 | 27573.5 | 147.519 |
| liquid/d1 | focus-lowbit-400 | 24/24 | 8/16 | 0/8 | 0/24 | 0.0003264 | 73529.4 | 24509.8 | 147.958 |
| liquid/d1 | focus-lowbit-500 | 24/24 | 8/16 | 0/8 | 0/24 | 0.0003264 | 73529.4 | 24509.8 | 137.594 |
| liquid/d1 | focus-lowbit-512 | 24/24 | 8/16 | 0/8 | 0/24 | 0.0003264 | 73529.4 | 24509.8 | 139.702 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 13.709500233, "measurement": "serial current process counters and VmHWM; no sampling; no provider call", "peak_rss_bytes": 70627328, "wall_seconds": 13.768164506007452}`.

Execution: `{"cpu_seconds": 190.153610849, "invocations": 4, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 147222528, "wall_seconds": 416.49245042997063}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 4/8 | 0/4 |
| wrap | 4/8 | 0/4 |

Per-family model results:

- liquid/d1 / focus-rgb-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-rgb-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-rgb-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-rgb-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-rgb-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-rgb-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-gray-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-gray-128: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-gray-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-gray-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-gray-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-gray-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-lowbit-64: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-lowbit-128: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-lowbit-256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-lowbit-400: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-lowbit-500: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / focus-lowbit-512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.

Request/refusal accounting:

- liquid/d1 / focus-rgb-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-rgb-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-rgb-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-rgb-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-rgb-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-rgb-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-gray-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-gray-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-gray-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-gray-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-gray-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-gray-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-lowbit-64: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-lowbit-128: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-lowbit-256: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-lowbit-400: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-lowbit-500: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / focus-lowbit-512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{}`.
