# L010 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 54/144 planned; completed manifest records: 82/216. Refused: 90 bodies / 134 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| convaiinnovations/laya | minimal-resolved-serialized | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| convaiinnovations/laya | words-resolved-serialized | 6/24 | 4/16 | 0/8 | unmeasured | ~0 | n/a (zero cost) | n/a (zero cost) | 92.4598 |
| convaiinnovations/laya | canonical-compact-serialized | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | 0 |
| convaiinnovations/laya-free | minimal-resolved-serialized | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| convaiinnovations/laya-free | words-resolved-serialized | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| convaiinnovations/laya-free | canonical-compact-serialized | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | 0 |
| liquid/d1 | minimal-resolved-serialized | 24/24 | 5/16 | 2/8 | unmeasured | 0.00011184 | 143062 | 35765.4 | 160.771 |
| liquid/d1 | words-resolved-serialized | 24/24 | 8/16 | 0/8 | unmeasured | 0.00019024 | 84104.3 | 26282.6 | 161.875 |
| liquid/d1 | canonical-compact-serialized | 24/24 | 8/16 | 0/8 | unmeasured | 0.00039312 | 40700 | 12718.8 | 154.963 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 0.633674155, "measurement": "serial current process counters and VmHWM; no sampling; no provider call", "peak_rss_bytes": 55042048, "wall_seconds": 0.6364570730074774}`.

Execution: `{"cpu_seconds": 19.961253324999998, "invocations": 2, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 137371648, "wall_seconds": 43.62541831296403}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 4/8 | 0/4 |
| wrap | 4/8 | 0/4 |

Per-family model results:

- convaiinnovations/laya / minimal-resolved-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya / words-resolved-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}}`.
- convaiinnovations/laya / canonical-compact-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya-free / minimal-resolved-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya-free / words-resolved-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya-free / canonical-compact-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- liquid/d1 / minimal-resolved-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 3}, "wrap": {"ambiguous_abstentions": 2, "inputs": 12, "known_exact": 2}}`.
- liquid/d1 / words-resolved-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / canonical-compact-serialized: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.

Request/refusal accounting:

- convaiinnovations/laya / minimal-resolved-serialized: 0/16 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- convaiinnovations/laya / words-resolved-serialized: 4/16 request bodies and 6/24 records completed; 18 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 18}`.
- convaiinnovations/laya / canonical-compact-serialized: 1/16 request bodies and 3/24 records completed; 21 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 21}`.
- convaiinnovations/laya-free / minimal-resolved-serialized: 0/16 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- convaiinnovations/laya-free / words-resolved-serialized: 0/16 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- convaiinnovations/laya-free / canonical-compact-serialized: 1/16 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- liquid/d1 / minimal-resolved-serialized: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / words-resolved-serialized: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / canonical-compact-serialized: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{"convaiinnovations/laya": {"reason": "failed or unsettled L010/ ledger request", "request_sha256": "b8af4cc049401a2bef4ad49a29cf00416c2ae118c7a2b4f501658678c843ad4f"}, "convaiinnovations/laya-free": {"reason": "failed or unsettled L010/ ledger request", "request_sha256": "871fbd19193d1420ebe1505c5835554c2a521e579075325f9dfc8c0ddb436b38"}}`.
