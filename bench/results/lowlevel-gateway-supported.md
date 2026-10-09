# L012 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 64/64 planned; completed manifest records: 96/96. Refused: 0 bodies / 0 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| convaiinnovations/laya | minimal-resolved | 24/24 | 10/16 | 0/8 | unmeasured | ~0 | n/a (zero cost) | n/a (zero cost) | 146.386 |
| convaiinnovations/laya | words-resolved | 24/24 | 8/16 | 0/8 | unmeasured | ~0 | n/a (zero cost) | n/a (zero cost) | 135.168 |
| convaiinnovations/laya-free | minimal-resolved | 24/24 | 10/16 | 0/8 | unmeasured | ~0 | n/a (zero cost) | n/a (zero cost) | 149.687 |
| convaiinnovations/laya-free | words-resolved | 24/24 | 8/16 | 0/8 | unmeasured | ~0 | n/a (zero cost) | n/a (zero cost) | 115.983 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 0.43233307, "measurement": "serial current process counters and VmHWM; no sampling; no provider call", "peak_rss_bytes": 54857728, "wall_seconds": 0.43532206400414}`.

Execution: `{"cpu_seconds": 25.820259589, "invocations": 1, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 143400960, "wall_seconds": 54.44438496802468}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 4/8 | 0/4 |
| wrap | 4/8 | 0/4 |

Per-family model results:

- convaiinnovations/laya / minimal-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- convaiinnovations/laya / words-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- convaiinnovations/laya-free / minimal-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 6}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- convaiinnovations/laya-free / words-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.

Request/refusal accounting:

- convaiinnovations/laya / minimal-resolved: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- convaiinnovations/laya / words-resolved: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- convaiinnovations/laya-free / minimal-resolved: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- convaiinnovations/laya-free / words-resolved: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{}`.
