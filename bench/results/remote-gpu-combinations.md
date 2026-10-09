# Fixed remote DEV decision combinations

R001 matched RGB512/768/1024, 24 authored source pages per size: 16 known relations and 8 ambiguous relations. All five native/stock runs passed the approved DEV scorer before combination. These are supplied-region decisions, not complete PDF extraction.

Rules were declared before this analysis: Intern+Flash+PPLX unanimity or unresolved; three-vote majority including unresolved, with three-way ties unresolved; Flash then PPLX agreement or unresolved; and Intern+Flash agreement or unresolved. Both agreement rules pay both calls on every input.

| Size | Rule/model | Known correct /16 | Wrong known | Known abstentions | Ambiguous abstentions /8 | Calls/input | Serial sum s | Mean s/input |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | intern | 12 | 4 | 0 | 0 | 1 | 57.111 | 2.380 |
| 512 | flash | 10 | 6 | 0 | 0 | 1 | 2.141 | 0.089 |
| 512 | pplx | 9 | 3 | 4 | 0 | 1 | 5.751 | 0.240 |
| 512 | clef | 9 | 7 | 0 | 0 | 1 | 5.042 | 0.210 |
| 512 | qwen4 | 10 | 6 | 0 | 0 | 1 | 5.182 | 0.216 |
| 512 | unanimity3 | 7 | 2 | 7 | 2 | 3 | 65.003 | 2.708 |
| 512 | majority3 | 10 | 3 | 3 | 0 | 3 | 65.003 | 2.708 |
| 512 | flash_pplx_consensus | 7 | 2 | 7 | 1 | 2 | 7.891 | 0.329 |
| 512 | intern_flash_consensus | 8 | 2 | 6 | 2 | 2 | 59.252 | 2.469 |
| 768 | intern | 12 | 4 | 0 | 0 | 1 | 94.162 | 3.923 |
| 768 | flash | 11 | 5 | 0 | 0 | 1 | 1.886 | 0.079 |
| 768 | pplx | 12 | 4 | 0 | 0 | 1 | 4.654 | 0.194 |
| 768 | clef | 11 | 5 | 0 | 0 | 1 | 5.375 | 0.224 |
| 768 | qwen4 | 10 | 6 | 0 | 0 | 1 | 5.249 | 0.219 |
| 768 | unanimity3 | 9 | 2 | 5 | 2 | 3 | 100.703 | 4.196 |
| 768 | majority3 | 12 | 4 | 0 | 0 | 3 | 100.703 | 4.196 |
| 768 | flash_pplx_consensus | 9 | 2 | 5 | 1 | 2 | 6.540 | 0.273 |
| 768 | intern_flash_consensus | 9 | 2 | 5 | 2 | 2 | 96.048 | 4.002 |
| 1024 | intern | 12 | 4 | 0 | 0 | 1 | 165.911 | 6.913 |
| 1024 | flash | 11 | 5 | 0 | 0 | 1 | 2.174 | 0.091 |
| 1024 | pplx | 12 | 4 | 0 | 0 | 1 | 5.581 | 0.233 |
| 1024 | clef | 12 | 4 | 0 | 0 | 1 | 6.177 | 0.257 |
| 1024 | qwen4 | 10 | 6 | 0 | 0 | 1 | 5.380 | 0.224 |
| 1024 | unanimity3 | 9 | 2 | 5 | 2 | 3 | 173.667 | 7.236 |
| 1024 | majority3 | 12 | 4 | 0 | 0 | 3 | 173.667 | 7.236 |
| 1024 | flash_pplx_consensus | 9 | 2 | 5 | 1 | 2 | 7.756 | 0.323 |
| 1024 | intern_flash_consensus | 9 | 2 | 5 | 2 | 2 | 168.086 | 7.004 |

Latency sums use retained measured inference durations. They estimate serial composition of existing calls; no ensemble was freshly timed. Initialization, downloads, idle time, fleet provisioning and teardown are excluded. Local GPU resources are available in original worker reports but are not combined into a hypothetical fleet profile. Costs and pages/USD remain unknown.

| Size | Known disagreements | Ambiguous disagreements caught | Shared wrong known | Shared decisive ambiguity missed | Oracle union known /16: trio | Oracle union known /16: all five |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 7 | 2 | 2 | 6 | 14 | 14 |
| 768 | 5 | 2 | 2 | 6 | 14 | 14 |
| 1024 | 5 | 2 | 2 | 6 | 14 | 14 |

The fixed rules expose the following tradeoffs:

- 512: unanimity retains 7 known correct decisions versus the best single model's 12, with 2 wrong known decisions and 7 known abstentions. Majority gives 10 known correct and 0 ambiguous abstentions. Flash+PPLX catches 1 ambiguous cases; Intern+Flash catches 2 at the serial latency shown above.
- 768: unanimity retains 9 known correct decisions versus the best single model's 12, with 2 wrong known decisions and 5 known abstentions. Majority gives 12 known correct and 0 ambiguous abstentions. Flash+PPLX catches 1 ambiguous cases; Intern+Flash catches 2 at the serial latency shown above.
- 1024: unanimity retains 9 known correct decisions versus the best single model's 12, with 2 wrong known decisions and 5 known abstentions. Majority gives 12 known correct and 0 ambiguous abstentions. Flash+PPLX catches 1 ambiguous cases; Intern+Flash catches 2 at the serial latency shown above.

Agreement leaves correlated decisive errors. Disagreement is therefore an incomplete sufficiency gate; fewer wrong decisions must be read alongside lost correct decisions and remaining decisive ambiguous answers. Majority does not provide an automatic abstention benefit. Adding models to an oracle union does not establish an executable routing policy.

The following diagnostic priorities preserve original packets and use no source-ID routing:

1. Review the 2 known cases wrong across all five models and all sizes for clipped or missing structural evidence and limits of the supplied-region assembly contract. Keep original references and inputs; do not write case-specific prompt fixes.
2. The 6 ambiguous cases with stable decisive trio agreement justify fresh, independent DEV sufficiency controls. Evaluate the blinded generic prompt screen across its whole cohort; selecting only these misses would bias the comparison.
3. Test an independently frozen architecture or cheap gate under identical evidence and wording. More pixels or another correlated model is a hypothesis to test, not a demonstrated remedy. Review groups are diagnostic observations, not a trained policy or inputs for models.

Oracle unions use references to identify any correct model and are unattainable ceilings, not executable selectors or reported quality scores. The 72 RGB treatments reuse 24 logical pages; pooled counts are correlated size treatments, not 72 independent cases. No protected held-out set was accessed.

Reproduce locally with `python -m bench.remote_combinations --source-dir <L015 freeze> --source-index <R001 source-index.json> --outputs <R001 outputs> --packets <R001 packets/manifest.json> --markdown bench/results/remote-gpu-combinations.md --json <ignored evaluation path>`. The command verifies hashes and scores DEV references through `bench.remote_report`; it makes no inference calls.
