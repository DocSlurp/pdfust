# Prompt tuning progress

Generic instruction-only ablations; fixed source words, images and candidate menus. All rows are DEV; heldout remains sealed. Prompts cannot recover missing candidates.

| Cohort / prompt | Model | Tables exact | Prose FP | Prose unresolved | Values owned | USD | Pages/$ | API pages/min |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh / P001-semantic-record-schema | perplexity/pplx-decider-v1.1-27b | 4/16 | 0/8 | 0/8 | 131/245 | 0.001906 | 12,594 | 129.1 |
| fresh / P001-semantic-record-schema | openai/gpt-6-luna-decisions | 3/16 | 0/8 | 0/8 | 38/245 | 0.007161 | 3,352 | 172.0 |
| original / P001-semantic-record-schema | perplexity/pplx-decider-v1.1-27b | 12/12 | 0/12 | 0/12 | 144/144 | 0.001515 | 15,843 | 139.8 |
| original / P001-semantic-record-schema | openai/gpt-6-luna-decisions | 12/12 | 1/12 | 0/12 | 144/144 | 0.005840 | 4,110 | 69.8 |
| original / P002-wrap-boundaries | perplexity/pplx-decider-v1.1-27b | 12/12 | 4/12 | 0/12 | 144/144 | 0.001519 | 15,803 | 146.5 |
| original / P002-wrap-boundaries | openai/gpt-6-luna-decisions | 12/12 | 12/12 | 0/12 | 144/144 | 0.005861 | 4,095 | 149.0 |
| original / P003-header-data-corridors | perplexity/pplx-decider-v1.1-27b | 12/12 | 12/12 | 0/12 | 144/144 | 0.001526 | 15,723 | 139.0 |
| original / P003-header-data-corridors | openai/gpt-6-luna-decisions | 12/12 | 12/12 | 0/12 | 144/144 | 0.005897 | 4,070 | 112.7 |
| original / P004-conflicting-evidence | perplexity/pplx-decider-v1.1-27b | 12/12 | 6/12 | 0/12 | 144/144 | 0.001519 | 15,798 | 146.8 |
| original / P004-conflicting-evidence | openai/gpt-6-luna-decisions | 12/12 | 10/12 | 0/12 | 144/144 | 0.005861 | 4,095 | 113.0 |
| original / P005-lean-complete-candidate | perplexity/pplx-decider-v1.1-27b | 12/12 | 9/12 | 0/12 | 144/144 | 0.001472 | 16,303 | 146.4 |
| original / P005-lean-complete-candidate | openai/gpt-6-luna-decisions | 12/12 | 10/12 | 0/12 | 144/144 | 0.005626 | 4,266 | 133.3 |

Rates use unique provider requests; local replay adds no provider throughput. Positive reported charges win; reported zero falls back to catalog pricing with observed tokens. API time excludes local preparation. Unresolved prose is not a correct rejection. All selections conserve source IDs, which is not a correctness score.
