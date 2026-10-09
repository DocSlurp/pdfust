# L009 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 54/144 planned; completed manifest records: 82/216. Refused: 90 bodies / 134 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| convaiinnovations/laya | minimal-resolved | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| convaiinnovations/laya | words-resolved | 6/24 | 2/16 | 0/8 | unmeasured | ~0 | n/a (zero cost) | n/a (zero cost) | 82.4949 |
| convaiinnovations/laya | canonical-compact | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | 0 |
| convaiinnovations/laya-free | minimal-resolved | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| convaiinnovations/laya-free | words-resolved | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | unknown |
| convaiinnovations/laya-free | canonical-compact | 0/24 | 0/16 | 0/8 | unmeasured | unknown | unknown | unknown | 0 |
| liquid/d1 | minimal-resolved | 24/24 | 7/16 | 1/8 | unmeasured | 0.00014024 | 114090 | 35653.2 | 144.927 |
| liquid/d1 | words-resolved | 24/24 | 8/16 | 0/8 | unmeasured | 0.00026728 | 59862.3 | 18707 | 157.231 |
| liquid/d1 | canonical-compact | 24/24 | 8/16 | 0/8 | unmeasured | 0.0006572 | 24345.7 | 7608.03 | 131.745 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `{"cpu_seconds": 0.616997023, "measurement": "serial current process counters and VmHWM; no sampling; no provider call", "peak_rss_bytes": 56041472, "wall_seconds": 0.6196301160089206}`.

Execution: `{"cpu_seconds": 19.892690637, "invocations": 2, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 135028736, "wall_seconds": 47.83558578600059}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| boundary | 4/8 | 0/4 |
| wrap | 4/8 | 0/4 |

Accounting audit notes:

Reconciled two HTTP422 Gateway failures with exact route/body ledger entries after exposing client.gateway for the generic runner. Original response statuses, requests and charges are unchanged; neither was a local refusal.

Per-family model results:

- convaiinnovations/laya / minimal-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya / words-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 1}}`.
- convaiinnovations/laya / canonical-compact: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya-free / minimal-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya-free / words-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- convaiinnovations/laya-free / canonical-compact: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 0}}`.
- liquid/d1 / minimal-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 1, "inputs": 12, "known_exact": 3}}`.
- liquid/d1 / words-resolved: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.
- liquid/d1 / canonical-compact: `{"boundary": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}, "wrap": {"ambiguous_abstentions": 0, "inputs": 12, "known_exact": 4}}`.

Request/refusal accounting:

- convaiinnovations/laya / minimal-resolved: 0/16 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- convaiinnovations/laya / words-resolved: 4/16 request bodies and 6/24 records completed; 18 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 18}`.
- convaiinnovations/laya / canonical-compact: 1/16 request bodies and 3/24 records completed; 21 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 21}`.
- convaiinnovations/laya-free / minimal-resolved: 0/16 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- convaiinnovations/laya-free / words-resolved: 0/16 request bodies and 0/24 records completed; 24 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 24}`.
- convaiinnovations/laya-free / canonical-compact: 1/16 request bodies and 1/24 records completed; 23 page inputs refused; 0 HTTP durations unknown; reasons `{"persistent model stop": 23}`.
- liquid/d1 / minimal-resolved: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / words-resolved: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / canonical-compact: 16/16 request bodies and 24/24 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{"convaiinnovations/laya": {"reason": "failed or unsettled L009/ ledger request", "request_sha256": "7932212c7dc7cd4f8f80136e29412f3372af2f2a771e9f5aee2ac32efe8c09c7"}, "convaiinnovations/laya-free": {"reason": "failed or unsettled L009/ ledger request", "request_sha256": "6773af9103c2ed4176c74d2332b3318255d0c574af9835408efbced1cb4fa031"}}`.
