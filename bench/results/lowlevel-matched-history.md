# L005 lower-level DEV decisions

authored DEV description partition only; not independent documents or full tables.

Completed request bodies: 96/96 planned; completed manifest records: 288/288. Refused: 0 bodies / 0 records.

Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. Header/value/cell reconstruction is unmeasured. Probabilities are uncalibrated; the three encodings share each logical template.

| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all | USD | Pages/USD | Correct regions/USD | API pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| typesafe/jev-1.13 | rawbothcanonical | 36/36 | 9/18 | 0/18 | 12/12 | 0.00623734 | 1923.9 | 480.975 | 182.954 |
| typesafe/jev-1.13 | compactbothcanonical | 36/36 | 9/18 | 0/18 | 12/12 | 0.00196522 | 6106.18 | 1526.55 | 204.651 |
| liquid/d1 | rawbothcanonical | 36/36 | 9/18 | 0/18 | 12/12 | 0.0061436 | 1953.25 | 488.313 | 105.721 |
| liquid/d1 | compactbothcanonical | 36/36 | 9/18 | 0/18 | 12/12 | 0.00208356 | 5759.37 | 1439.84 | 150.583 |
| perplexity/pplx-decider-v1.1-27b | rawbothcanonical | 33/36 | 15/18 | 0/18 | 11/12 | unknown | unknown | unknown | 54.7976 |
| perplexity/pplx-decider-v1.1-27b | compactbothcanonical | 36/36 | 12/18 | 3/18 | 12/12 | 0.00076538 | 15678.5 | 5226.16 | 101.615 |
| openai/gpt-6-luna-decisions | rawbothcanonical | 36/36 | 12/18 | 0/18 | 12/12 | ~0.0076827 | 1561.95 | 520.65 | 138.064 |
| openai/gpt-6-luna-decisions | compactbothcanonical | 36/36 | 12/18 | 0/18 | 12/12 | ~0.0023748 | 5053.06 | 1684.35 | 155.493 |

Costs preserve positive provider charges; ~ marks frozen-catalog estimates. Unknown costs never become complete totals. Local replay is not another provider transmission; rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. API timing excludes preparation. Source conservation covers validated outputs only; invalid/failed inputs are listed separately.

Preparation: `null`.

Execution: `{"cpu_seconds": 41.551460261, "invocations": 2, "legacy_prior_invocations_unmeasured": false, "measurement": "sum of retained serial invocation wall/CPU counters; maximum process lifetime VmHWM across invocations; no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured", "peak_rss_bytes": 135282688, "wall_seconds": 121.27355563698802}`.

Native word/physical-line proxy:

| Family | Known exact/all | Ambiguous abstain/all |
|---|---:|---:|
| history | 9/18 | 0/18 |

Per-family model results:

- typesafe/jev-1.13 / rawbothcanonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- typesafe/jev-1.13 / compactbothcanonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- liquid/d1 / rawbothcanonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- liquid/d1 / compactbothcanonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 9}}`.
- perplexity/pplx-decider-v1.1-27b / rawbothcanonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 15}}`.
- perplexity/pplx-decider-v1.1-27b / compactbothcanonical: `{"history": {"ambiguous_abstentions": 3, "inputs": 36, "known_exact": 12}}`.
- openai/gpt-6-luna-decisions / rawbothcanonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.
- openai/gpt-6-luna-decisions / compactbothcanonical: `{"history": {"ambiguous_abstentions": 0, "inputs": 36, "known_exact": 12}}`.

History evidence strata: conventional joins are authored hypotheses; visible_identifier splits use explicit source IDs. Neither score measures full table reconstruction.

- typesafe/jev-1.13 / rawbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 0, "known_inputs": 9, "scored": 9}, "unresolved": {"ambiguous_abstentions": 0, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 9, "known_inputs": 9, "scored": 9}}`.
- typesafe/jev-1.13 / compactbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 0, "known_inputs": 9, "scored": 9}, "unresolved": {"ambiguous_abstentions": 0, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 9, "known_inputs": 9, "scored": 9}}`.
- liquid/d1 / rawbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 0, "known_inputs": 9, "scored": 9}, "unresolved": {"ambiguous_abstentions": 0, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 9, "known_inputs": 9, "scored": 9}}`.
- liquid/d1 / compactbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 0, "known_inputs": 9, "scored": 9}, "unresolved": {"ambiguous_abstentions": 0, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 9, "known_inputs": 9, "scored": 9}}`.
- perplexity/pplx-decider-v1.1-27b / rawbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 6, "known_inputs": 9, "scored": 6}, "unresolved": {"ambiguous_abstentions": 0, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 9, "known_inputs": 9, "scored": 9}}`.
- perplexity/pplx-decider-v1.1-27b / compactbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 6, "known_inputs": 9, "scored": 9}, "unresolved": {"ambiguous_abstentions": 3, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 6, "known_inputs": 9, "scored": 9}}`.
- openai/gpt-6-luna-decisions / rawbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 3, "known_inputs": 9, "scored": 9}, "unresolved": {"ambiguous_abstentions": 0, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 9, "known_inputs": 9, "scored": 9}}`.
- openai/gpt-6-luna-decisions / compactbothcanonical: `{"conventional": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 6, "known_inputs": 9, "scored": 9}, "unresolved": {"ambiguous_abstentions": 0, "ambiguous_inputs": 18, "inputs": 18, "known_exact": 0, "known_inputs": 0, "scored": 18}, "visible_identifier": {"ambiguous_abstentions": 0, "ambiguous_inputs": 0, "inputs": 9, "known_exact": 6, "known_inputs": 9, "scored": 9}}`.

Request/refusal accounting:

- typesafe/jev-1.13 / rawbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- typesafe/jev-1.13 / compactbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / rawbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- liquid/d1 / compactbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / rawbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- perplexity/pplx-decider-v1.1-27b / compactbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / rawbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.
- openai/gpt-6-luna-decisions / compactbothcanonical: 12/12 request bodies and 36/36 records completed; 0 page inputs refused; 0 HTTP durations unknown; reasons `{}`.

Persistent model stops: `{"perplexity/pplx-decider-v1.1-27b": {"reason": "failed or unsettled L005/ ledger request", "request_sha256": "9c17d0c47426a09fa114ff1faabeaec2bc1164449117fa3f74ca8546e7fad901"}}`.
