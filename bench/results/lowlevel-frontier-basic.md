# L003 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 141/648 planned; completed manifest records: 141/648. Refused: 25 bodies / 25 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are unreported; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic/claude-opus-5.5 | minimal | 6/72 | 1/48 | 1/24 | 0/24 | 0.025228 | 237.831 | 39.6385 | 25.9792 |
| anthropic/claude-opus-5.5 | words | 24/72 | 8/48 | 6/24 | 1/24 | 0.12714 | 188.768 | 62.9228 | 22.6128 |
| anthropic/claude-opus-5.5 | glyphs | 12/72 | 4/48 | 4/24 | 0/24 | 0.177272 | 67.6926 | 22.5642 | 15.8034 |
| anthropic/claude-opus-5.5 | canonical | 9/72 | 3/48 | 1/24 | 0/24 | 0.126032 | 71.4104 | 23.8035 | 17.023 |
| anthropic/claude-opus-5.5 | operators | 12/72 | 5/48 | 1/24 | 0/24 | 0.301904 | 39.7477 | 16.5616 | 15.8068 |
| anthropic/claude-opus-5.5 | rolling | 21/72 | 8/48 | 4/24 | 0/24 | 0.307624 | 68.2652 | 26.0058 | 18.3441 |
| anthropic/claude-opus-5.5 | vectors | 9/72 | 8/48 | 1/24 | 0/24 | 0.116432 | 77.2983 | 68.7096 | 25.3464 |
| anthropic/claude-opus-5.5 | crop256 | 15/72 | 12/48 | 1/24 | 0/24 | 0.2249 | 66.6963 | 53.357 | 18.6936 |
| anthropic/claude-opus-5.5 | crop512 | 72/72 | 46/48 | 14/24 | 22/24 | 1.11132 | 64.7876 | 41.3921 | 19.1537 |
| anthropic/claude-sonnet-5.5 | minimal | 21/72 | 3/48 | 6/24 | 1/24 | 0.027566 | 761.808 | 108.83 | 80.5268 |
| anthropic/claude-sonnet-5.5 | words | 21/72 | 4/48 | 4/24 | 0/24 | 0.035664 | 588.829 | 112.158 | 87.5919 |
| anthropic/claude-sonnet-5.5 | glyphs | 15/72 | 4/48 | 2/24 | 0/24 | 0.090762 | 165.267 | 44.0713 | 89.3077 |
| anthropic/claude-sonnet-5.5 | canonical | 3/72 | 1/48 | 0/24 | 0/24 | 0.025024 | 119.885 | 39.9616 | 73.7244 |
| anthropic/claude-sonnet-5.5 | operators | 6/72 | 2/48 | 0/24 | 0/24 | 0.069132 | 86.7905 | 28.9302 | 89.3625 |
| anthropic/claude-sonnet-5.5 | rolling | 6/72 | 3/48 | 1/24 | 0/24 | 0.034986 | 171.497 | 85.7486 | 84.6829 |
| anthropic/claude-sonnet-5.5 | vectors | 3/72 | 3/48 | 0/24 | 0/24 | 0.0179 | 167.598 | 167.598 | 91.0763 |
| anthropic/claude-sonnet-5.5 | crop256 | 12/72 | 5/48 | 0/24 | 0/24 | 0.071506 | 167.818 | 69.9242 | 67.5154 |
| anthropic/claude-sonnet-5.5 | crop512 | 72/72 | 37/48 | 10/24 | 13/24 | 0.477432 | 150.807 | 77.4979 | 70.5619 |
| anthropic/claude-haiku-5.5 | minimal | 12/72 | 3/48 | 1/24 | 0/24 | 0.0017973 | 6676.68 | 1669.17 | 33.7572 |
| anthropic/claude-haiku-5.5 | words | 9/72 | 2/48 | 1/24 | 0/24 | 0.0019099 | 4712.29 | 1047.18 | 26.9729 |
| anthropic/claude-haiku-5.5 | glyphs | 9/72 | 5/48 | 1/24 | 0/24 | 0.00381 | 2362.2 | 1312.34 | 26.575 |
| anthropic/claude-haiku-5.5 | canonical | 3/72 | 2/48 | 0/24 | 0/24 | 0.0013456 | 2229.49 | 1486.33 | 24.7577 |
| anthropic/claude-haiku-5.5 | operators | 6/72 | 1/48 | 0/24 | 0/24 | unknown | unknown | unknown | 24.3905 |
| anthropic/claude-haiku-5.5 | rolling | 6/72 | 1/48 | 1/24 | 0/24 | 0.0029156 | 2057.9 | 342.983 | 22.1833 |
| anthropic/claude-haiku-5.5 | vectors | 12/72 | 5/48 | 2/24 | 0/24 | 0.0062043 | 1934.14 | 805.893 | 26.7092 |
| anthropic/claude-haiku-5.5 | crop256 | 12/72 | 6/48 | 1/24 | 1/24 | 0.0050804 | 2362.02 | 1181.01 | 29.7556 |
| anthropic/claude-haiku-5.5 | crop512 | 12/72 | 6/48 | 1/24 | 1/24 | 0.0053892 | 2226.68 | 1113.34 | 26.8352 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 0.7832808330000001, "measurement": "serial current process perf_counter/process_time; lifetime VmHWM; no sampling; copies frozen source/observations; no new PDF interpretation or network inference", "peak_rss_bytes": 59351040, "wall_seconds": 1.003417053987505}`.

Execution: `{"cpu_seconds": 57.574299397000004, "measurement": "serial invocation perf_counter/process_time totals; maximum process lifetime VmHWM; no sampling; HTTP waiting included, preparation separate; provider CPU/RAM unmeasured", "peak_rss_bytes": 146169856, "wall_seconds": 947.4496457909117}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 12/24 | 0/12 |
| wrap | 12/24 | 0/12 |

Per-family model results:

- anthropic/claude-opus-5.5 / minimal: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-opus-5.5 / words: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 8}, "wrap": {"ambiguous_abstentions": 5, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-opus-5.5 / glyphs: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 3, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-opus-5.5 / canonical: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-opus-5.5 / operators: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-opus-5.5 / rolling: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 8}, "wrap": {"ambiguous_abstentions": 3, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-opus-5.5 / vectors: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 5}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 3}}`.
- anthropic/claude-opus-5.5 / crop256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 6}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 6}}`.
- anthropic/claude-opus-5.5 / crop512: `{"boundary": {"ambiguous_abstentions": 2, "inputs": 36, "known_exact": 22}, "wrap": {"ambiguous_abstentions": 12, "inputs": 36, "known_exact": 24}}`.
- anthropic/claude-sonnet-5.5 / minimal: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 5, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-sonnet-5.5 / words: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 4, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-sonnet-5.5 / glyphs: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 2}}`.
- anthropic/claude-sonnet-5.5 / canonical: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}}`.
- anthropic/claude-sonnet-5.5 / operators: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-sonnet-5.5 / rolling: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 1}}`.
- anthropic/claude-sonnet-5.5 / vectors: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}}`.
- anthropic/claude-sonnet-5.5 / crop256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 2}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 3}}`.
- anthropic/claude-sonnet-5.5 / crop512: `{"boundary": {"ambiguous_abstentions": 4, "inputs": 36, "known_exact": 14}, "wrap": {"ambiguous_abstentions": 6, "inputs": 36, "known_exact": 23}}`.
- anthropic/claude-haiku-5.5 / minimal: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-haiku-5.5 / words: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}}`.
- anthropic/claude-haiku-5.5 / glyphs: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 1}}`.
- anthropic/claude-haiku-5.5 / canonical: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}}`.
- anthropic/claude-haiku-5.5 / operators: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-haiku-5.5 / rolling: `{"boundary": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}}`.
- anthropic/claude-haiku-5.5 / vectors: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 2, "inputs": 36, "known_exact": 5}}`.
- anthropic/claude-haiku-5.5 / crop256: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 5}}`.
- anthropic/claude-haiku-5.5 / crop512: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 1, "inputs": 36, "known_exact": 3}}`.

Request/refusal accounting:

- anthropic/claude-opus-5.5 / minimal: 2/24 request bodies and 2/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / words: 8/24 request bodies and 8/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / glyphs: 4/24 request bodies and 4/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / canonical: 3/24 request bodies and 3/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / operators: 4/24 request bodies and 4/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / rolling: 7/24 request bodies and 7/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / vectors: 3/24 request bodies and 3/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / crop256: 5/24 request bodies and 5/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-opus-5.5 / crop512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / minimal: 7/24 request bodies and 7/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / words: 7/24 request bodies and 7/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / glyphs: 5/24 request bodies and 5/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / canonical: 1/24 request bodies and 1/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / operators: 2/24 request bodies and 2/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / rolling: 2/24 request bodies and 2/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / vectors: 1/24 request bodies and 1/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / crop256: 4/24 request bodies and 4/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-sonnet-5.5 / crop512: 24/24 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / minimal: 4/24 request bodies and 4/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / words: 3/24 request bodies and 3/24 records completed; 15 page inputs refused; 0 HTTP durations unknown; reasons `{"model stopped": 15}`.
- anthropic/claude-haiku-5.5 / glyphs: 3/24 request bodies and 3/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / canonical: 1/24 request bodies and 1/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / operators: 3/24 request bodies and 3/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / rolling: 2/24 request bodies and 2/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / vectors: 4/24 request bodies and 4/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / crop256: 4/24 request bodies and 4/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- anthropic/claude-haiku-5.5 / crop512: 4/24 request bodies and 4/24 records completed; 60 page inputs refused; 0 HTTP durations unknown; reasons `{"model stopped": 60}`.

Persistent model stops: `{}`.
