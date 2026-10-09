# Qwen 9 natural PDF DEV transfer

Qwen 3.5-9B matches 30/48 admitted full-record references and abstains on 0/44 insufficient description-only conditions. All 96 outputs are valid generated labels; no trained decision probabilities or confidence are inferred. The authored ambiguity behavior does not establish natural evidence sufficiency.

Exact original L 011 source/stage request and PNG bytes, every worker ID and body hash were verified before root-local reviewed references. References are one provisional source-aware review of 24 overlapping regions from one Senate page, not independent document gold. Full-source and admitted-scope agreement differ when neighboring record context is omitted.

| Arm | Valid/planned | Full-source matches | Admitted-scope matches | Abstentions | Summed request latency s | Client CPU s |
|---|---:|---:|---:|---:|---:|---:|
| record-512 | 24/24 | 16/24 | 16/24 | 2 | 10.865 | 0.280 |
| record-1200 | 24/24 | 14/24 | 14/24 | 0 | 10.903 | 0.287 |
| description-512 | 24/24 | 16/24 | 1/24 | 0 | 10.905 | 0.295 |
| description-1200 | 24/24 | 18/24 | 1/24 | 0 | 10.902 | 0.285 |

Record-512 returns 16 split,6 join,2 unresolved; record-1200 returns 15 split and 9 join. Both description arms make only decisive decisions, matching 1/24 scope references each. The 2 answerable description references and 22 insufficient references per resolution yield 52 known-scope conditions and 44 ambiguous-scope conditions overall. Of 52 known conditions,31 are correct,19 wrong and 2 abstentions;0/44 ambiguous conditions abstain. All full-source references are known, so a full-source match on a cropped description must not be presented as sufficient admitted evidence.

Loaded stock engine: `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; worker reports vLLM 0.31.0. Eight concurrent client lanes query an existing warm server. Global worker wall 5.760 s gives 999.98 region inputs/min; first-start-to-last-completion span 5.667 s gives 1016.33 inputs/min. Summed request latency 43.574 s measures overlapping client latency and is not the throughput denominator. Additive child client CPU is 1.210 s; server/GPU inference CPU is not included. Aggregate client peak RSS and server GPU peaks are unavailable in this output; per-client lifetime RSS maxima must not be summed.

No model-hour rental rate or complete lifecycle cost was assigned to this run; costs remain unknown. No full-page extraction rate is claimed. CPU-only scoring uses the explicit `allow_exploratory_stock` opt-in and strict label schema, retains malformed/missing outputs in denominators and never fabricates probabilities. Concurrent serial-time cost estimates are disabled.

Retained evaluation: `.scratch/council/lowlevel-eval/qwen9-natural-evaluation.json`. Source: `bench/results/pdf-master-artifacts/decisions/lowlevel-v1/natural-source`; packets: `.scratch/remote-gpu-20261009/r001/stage/natural`; output: `results/outputs/qwen9-natural`. No inference was run during this analysis.
