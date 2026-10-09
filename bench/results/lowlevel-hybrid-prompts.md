# Source-only geometry plus decision-model replay

The previously frozen divider policy handles decisive geometry; the model handles deferred regions. This offline replay measures paired decisions only. Actual cascade cost and latency are unmeasured. Missing model outcomes remain in the all-input column and are excluded from paired comparisons. Known scores inherit provisional authored references, not independent full-table validation.

| Model | Arm | Paired/all | Known direct → hybrid / paired | Ambiguous abstain direct → hybrid / paired | Gains | Losses | Whole bodies potentially skipped/all |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| typesafe/jev-1.13 | minimal@resolved | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | canonical@resolved | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | vectors@resolved | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | minimal@typed | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | canonical@typed | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | vectors@typed | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | minimal@both | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | canonical@both | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | vectors@both | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 0/8 |
| typesafe/jev-1.13 | minimal@singleton | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 2/16 |
| typesafe/jev-1.13 | vectors@singleton | 0/24 | 0 → 0 / 0 | 0 → 0 / 0 | 0 | 0 | 8/24 |
| liquid/d1 | minimal@resolved | 24/24 | 6 → 11 / 16 | 1 → 1 / 8 | 5 | 0 | 0/8 |
| liquid/d1 | canonical@resolved | 24/24 | 7 → 11 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | vectors@resolved | 24/24 | 8 → 12 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | minimal@typed | 24/24 | 8 → 12 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | canonical@typed | 24/24 | 8 → 12 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | vectors@typed | 24/24 | 8 → 12 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | minimal@both | 24/24 | 9 → 13 / 16 | 2 → 2 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | canonical@both | 24/24 | 7 → 11 / 16 | 1 → 1 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | vectors@both | 24/24 | 8 → 12 / 16 | 1 → 1 / 8 | 4 | 0 | 0/8 |
| liquid/d1 | minimal@singleton | 24/24 | 6 → 10 / 16 | 1 → 1 / 8 | 4 | 0 | 3/16 |
| liquid/d1 | vectors@singleton | 24/24 | 9 → 13 / 16 | 0 → 0 / 8 | 4 | 0 | 8/24 |
| perplexity/pplx-decider-v1.1-27b | minimal@resolved | 24/24 | 6 → 13 / 16 | 3 → 3 / 8 | 7 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | canonical@resolved | 24/24 | 8 → 12 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | vectors@resolved | 24/24 | 12 → 13 / 16 | 3 → 3 / 8 | 1 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | minimal@typed | 24/24 | 8 → 13 / 16 | 0 → 0 / 8 | 5 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | canonical@typed | 24/24 | 7 → 12 / 16 | 0 → 0 / 8 | 5 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | vectors@typed | 24/24 | 11 → 12 / 16 | 0 → 0 / 8 | 1 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | minimal@both | 24/24 | 6 → 14 / 16 | 4 → 4 / 8 | 8 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | canonical@both | 24/24 | 9 → 13 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | vectors@both | 24/24 | 9 → 12 / 16 | 2 → 2 / 8 | 3 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | crop512@resolved | 24/24 | 15 → 15 / 16 | 1 → 1 / 8 | 0 | 0 | 0/8 |
| perplexity/pplx-decider-v1.1-27b | minimal@singleton | 24/24 | 7 → 11 / 16 | 0 → 0 / 8 | 4 | 0 | 3/16 |
| perplexity/pplx-decider-v1.1-27b | vectors@singleton | 24/24 | 11 → 12 / 16 | 0 → 0 / 8 | 1 | 0 | 8/24 |
| perplexity/pplx-decider-v1.1-27b | crop512@singleton | 24/24 | 12 → 12 / 16 | 0 → 0 / 8 | 0 | 0 | 8/24 |
| openai/gpt-6-luna-decisions | minimal@resolved | 24/24 | 2 → 10 / 16 | 5 → 5 / 8 | 8 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | canonical@resolved | 24/24 | 6 → 11 / 16 | 3 → 3 / 8 | 5 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | vectors@resolved | 24/24 | 3 → 8 / 16 | 7 → 7 / 8 | 5 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | minimal@typed | 24/24 | 0 → 8 / 16 | 8 → 8 / 8 | 8 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | canonical@typed | 24/24 | 8 → 11 / 16 | 1 → 1 / 8 | 3 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | vectors@typed | 24/24 | 8 → 12 / 16 | 0 → 0 / 8 | 4 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | minimal@both | 24/24 | 2 → 10 / 16 | 7 → 7 / 8 | 8 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | canonical@both | 24/24 | 7 → 11 / 16 | 2 → 2 / 8 | 4 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | vectors@both | 24/24 | 6 → 10 / 16 | 6 → 6 / 8 | 4 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | crop512@resolved | 24/24 | 7 → 11 / 16 | 4 → 4 / 8 | 4 | 0 | 0/8 |
| openai/gpt-6-luna-decisions | minimal@singleton | 24/24 | 1 → 8 / 16 | 7 → 7 / 8 | 7 | 0 | 3/16 |
| openai/gpt-6-luna-decisions | vectors@singleton | 24/24 | 9 → 13 / 16 | 0 → 0 / 8 | 4 | 0 | 8/24 |
| openai/gpt-6-luna-decisions | crop512@singleton | 24/24 | 9 → 13 / 16 | 0 → 0 / 8 | 4 | 0 | 8/24 |

Interpreted strokes do not establish clip-resolved visibility. Loose selector centers, decorative rules and enclosure assumptions remain limitations. Partial batches cannot be removed without changing the original model input; the body count includes only wholly bypassable requests.

Routing resources: `{"cpu_seconds": 0.005959778000000027, "measurement": "perf_counter, process_time, process-lifetime VmHWM; no sampling", "peak_rss_bytes": 54538240, "scope": "serial saved-observation reads and geometry decisions; excludes freeze verification and scoring", "wall_seconds": 0.005990353995002806}`.
