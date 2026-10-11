# P003 frozen geometry and decision compositions

All 30 predeclared policies independently replayed from the approved source, vector control and ten retained same-model image runs before opening labels. Every policy retains all 24 cases, including 18 visually cued and six indeterminate. The same cases and component calls are reused across policies; these are not independent samples.

The vector baseline matches 14/24 author labels, all 14 within the cued 18, and abstains on all six indeterminate cases. Vector-first PPLX128 matches 19/24 versus the retained model’s 15/24; PPLX512 matches 20/24 under both. Vector-first Luna512 matches 16/24 versus the model’s 6/24, while preserving six indeterminate abstentions. This shows complementarity of these frozen outputs, not a demonstrated operational policy gain or calibrated confidence.

Vector-first uses a decisive vector choice and consults the same configured model when vector evidence abstains. Agreement-only requires equal decisive choices. Either-evidence accepts available decisive evidence but abstains on decisive conflicts. These are composite systems; vector-derived answers must not be credited as pure model decisions. Original model protocol failures and exact-alias secondary outcomes remain retained separately. No other model supplies a fallback.

| Component baseline | Author labels /24 | Cued /18 | Cell/row/wrap /8 | Decisive | Indeterminate abstain /6 | Actual effective/reported USD |
|---|---:|---:|---|---:|---:|---|
| Direct vector | 14 | 14 | 6/5/3 | 15 | 6 | no API |
| synth-clef-geometry-crop128-r0-c3 | 13 | 10 | 4/5/4 | 24 | 0 | 0.00528048/0.00528048 |
| synth-clef-geometry-crop512-r0-c3 | 14 | 11 | 4/5/5 | 24 | 0 | 0.00608688/0.00608688 |
| synth-clefflash-geometry-crop128-r0-c3 | 15 | 12 | 4/7/4 | 24 | 0 | 0.000836076/0.000836076 |
| synth-clefflash-geometry-crop512-r0-c3 | 13 | 10 | 4/5/4 | 24 | 0 | 0.000963756/0.000963756 |
| synth-clefomni-geometry-crop128-r0-c3 | 12 | 9 | 4/4/4 | 24 | 0 | 0.0032919/0.0032919 |
| synth-clefomni-geometry-crop512-r0-c3 | 12 | 9 | 4/4/4 | 24 | 0 | 0.0037959/0.0037959 |
| synth-lunadec-geometry-crop128-r0-c3 | 7 | 6 | 1/4/2 | 16 | 4 | 0.0015398/0 |
| synth-lunadec-geometry-crop512-r0-c3 | 6 | 6 | 1/3/2 | 13 | 6 | 0.002039/0 |
| synth-pplx-geometry-crop128-r0-c3 | 15 | 12 | 5/6/4 | 23 | 0 | 0.00041508/0.00041508 |
| synth-pplx-geometry-crop512-r0-c3 | 20 | 17 | 7/6/7 | 24 | 0 | 0.00048228/0.00048228 |

| Model | Crop edge | Policy | Author labels /24 | Cued /18 | Cell/row/wrap /8 | Decisive/abstained | Indeterminate abstain /6 | Conflicts | Selected vector/model/agreement |
|---|---:|---|---:|---:|---|---|---:|---:|---|
| perplexity/pplx-decider-v1.1-27b | 128 | vector_first | 19 | 16 | 7/6/6 | 24/0 | 0 | 4 | 15/9/0 |
| perplexity/pplx-decider-v1.1-27b | 128 | agreement_only | 10 | 10 | 4/5/1 | 10/14 | 6 | 4 | 0/0/10 |
| perplexity/pplx-decider-v1.1-27b | 128 | either_evidence_conflicts_abstain | 15 | 12 | 5/6/4 | 20/4 | 0 | 4 | 1/9/10 |
| perplexity/pplx-decider-v1.1-27b | 512 | vector_first | 20 | 17 | 7/6/7 | 24/0 | 0 | 0 | 15/9/0 |
| perplexity/pplx-decider-v1.1-27b | 512 | agreement_only | 14 | 14 | 6/5/3 | 15/9 | 6 | 0 | 0/0/15 |
| perplexity/pplx-decider-v1.1-27b | 512 | either_evidence_conflicts_abstain | 20 | 17 | 7/6/7 | 24/0 | 0 | 0 | 0/9/15 |
| cloudflare/clef | 128 | vector_first | 17 | 14 | 7/6/4 | 24/0 | 0 | 6 | 15/9/0 |
| cloudflare/clef | 128 | agreement_only | 9 | 9 | 3/3/3 | 9/15 | 6 | 6 | 0/0/9 |
| cloudflare/clef | 128 | either_evidence_conflicts_abstain | 12 | 9 | 4/4/4 | 18/6 | 0 | 6 | 0/9/9 |
| cloudflare/clef | 512 | vector_first | 18 | 15 | 7/6/5 | 24/0 | 0 | 6 | 15/9/0 |
| cloudflare/clef | 512 | agreement_only | 9 | 9 | 3/3/3 | 9/15 | 6 | 6 | 0/0/9 |
| cloudflare/clef | 512 | either_evidence_conflicts_abstain | 13 | 10 | 4/4/5 | 18/6 | 0 | 6 | 0/9/9 |
| cloudflare/clef-flash | 128 | vector_first | 17 | 14 | 7/6/4 | 24/0 | 0 | 4 | 15/9/0 |
| cloudflare/clef-flash | 128 | agreement_only | 11 | 11 | 3/5/3 | 11/13 | 6 | 4 | 0/0/11 |
| cloudflare/clef-flash | 128 | either_evidence_conflicts_abstain | 14 | 11 | 4/6/4 | 20/4 | 0 | 4 | 0/9/11 |
| cloudflare/clef-flash | 512 | vector_first | 17 | 14 | 7/6/4 | 24/0 | 0 | 6 | 15/9/0 |
| cloudflare/clef-flash | 512 | agreement_only | 9 | 9 | 3/3/3 | 9/15 | 6 | 6 | 0/0/9 |
| cloudflare/clef-flash | 512 | either_evidence_conflicts_abstain | 12 | 9 | 4/4/4 | 18/6 | 0 | 6 | 0/9/9 |
| cloudflare/clef-omni | 128 | vector_first | 17 | 14 | 7/6/4 | 24/0 | 0 | 7 | 15/9/0 |
| cloudflare/clef-omni | 128 | agreement_only | 8 | 8 | 3/2/3 | 8/16 | 6 | 7 | 0/0/8 |
| cloudflare/clef-omni | 128 | either_evidence_conflicts_abstain | 11 | 8 | 4/3/4 | 17/7 | 0 | 7 | 0/9/8 |
| cloudflare/clef-omni | 512 | vector_first | 17 | 14 | 7/6/4 | 24/0 | 0 | 7 | 15/9/0 |
| cloudflare/clef-omni | 512 | agreement_only | 8 | 8 | 3/2/3 | 8/16 | 6 | 7 | 0/0/8 |
| cloudflare/clef-omni | 512 | either_evidence_conflicts_abstain | 11 | 8 | 4/3/4 | 17/7 | 0 | 7 | 0/9/8 |
| openai/gpt-6-luna-decisions | 128 | vector_first | 17 | 16 | 6/6/5 | 19/5 | 4 | 7 | 15/4/0 |
| openai/gpt-6-luna-decisions | 128 | agreement_only | 4 | 4 | 1/3/0 | 5/19 | 6 | 7 | 0/0/5 |
| openai/gpt-6-luna-decisions | 128 | either_evidence_conflicts_abstain | 10 | 9 | 3/4/3 | 12/12 | 4 | 7 | 3/4/5 |
| openai/gpt-6-luna-decisions | 512 | vector_first | 16 | 16 | 6/5/5 | 17/7 | 6 | 6 | 15/2/0 |
| openai/gpt-6-luna-decisions | 512 | agreement_only | 4 | 4 | 1/3/0 | 5/19 | 6 | 6 | 0/0/5 |
| openai/gpt-6-luna-decisions | 512 | either_evidence_conflicts_abstain | 10 | 10 | 4/3/3 | 11/13 | 6 | 6 | 4/2/5 |

All composition component_error counters are zero in this frozen pool. Abstention and conflict remain explicit, and no merged probability is created. Six indeterminate cases are three opposing-label twins whose actual source drawings and pixels are identical; label agreement there does not demonstrate recovery of missing evidence. Agreement-only abstains on all six for every model/edge.

All ten original paid runs actually occurred. Their charges are shown once per component baseline above and must not be summed again for each policy. A hypothetical vector-first deployment could suppress 15 of 24 model requests, but no actual saving was measured and no price is assigned to that counterfactual. Fresh throughput, fresh pages/minute and pipeline rates are unavailable. CPU replay timings are separate from retained model timings; no new GPU work, hosted calls or source assignments occurred.

Authority SHA256: `424d4885e1cdd14c28f4b6f6a968589808c8bf2abe967d415412ffec97e07025`; composition freeze SHA256: `0f5b3e905645ec1c18e9c9eb3406c114d57390baf0efc43c50a6765637965bc4`; generator-gold SHA256: `db0f5953579379fbf74ffba9faebf8c6acad1e622b70c4fae389d137d357e2ca`. All 29 archived code blobs matched the independently approved authority and current replay dependencies. The source evidence, components and complete composition plan reproduced byte-identical SHA256 values before labels. Original response/request/report bytes were checked before replay; nothing was rewritten.

Five focused tests cover complete denominators, duplicate/missing cases, decisive conflicts without invented probabilities and authority rejection before replay. This is a single retained-output comparison; no configuration is selected from these scores.
