# Source-only geometry plus decision-model replay

The previously frozen divider policy handles decisive geometry; the model handles deferred regions. This offline replay measures paired decisions only. Actual cascade cost and latency are unmeasured. Missing model outcomes remain in the all-input column and are excluded from paired comparisons. Known scores inherit provisional authored references, not independent full-table validation.

| Model | Arm | Paired/all | Known direct → hybrid / paired | Ambiguous abstain direct → hybrid / paired | Gains | Losses | Whole bodies potentially skipped/all |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| typesafe/jev-1.13 | minimal | 72/72 | 22 → 37 / 48 | 1 → 1 / 24 | 15 | 0 | 0/24 |
| typesafe/jev-1.13 | words | 72/72 | 28 → 40 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| typesafe/jev-1.13 | glyphs | 72/72 | 25 → 37 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| typesafe/jev-1.13 | canonical | 72/72 | 24 → 36 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| typesafe/jev-1.13 | operators | 72/72 | 27 → 39 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| typesafe/jev-1.13 | rolling | 72/72 | 24 → 36 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| typesafe/jev-1.13 | vectors | 72/72 | 25 → 37 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| liquid/d1 | minimal | 72/72 | 23 → 37 / 48 | 0 → 0 / 24 | 14 | 0 | 0/24 |
| liquid/d1 | words | 72/72 | 24 → 36 / 48 | 2 → 2 / 24 | 12 | 0 | 0/24 |
| liquid/d1 | glyphs | 72/72 | 25 → 37 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| liquid/d1 | canonical | 72/72 | 24 → 36 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| liquid/d1 | operators | 72/72 | 23 → 35 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| liquid/d1 | rolling | 72/72 | 25 → 37 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| liquid/d1 | vectors | 72/72 | 26 → 38 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | minimal | 72/72 | 28 → 39 / 48 | 0 → 0 / 24 | 11 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | words | 72/72 | 26 → 36 / 48 | 0 → 0 / 24 | 10 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | glyphs | 72/72 | 24 → 35 / 48 | 0 → 0 / 24 | 11 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | canonical | 72/72 | 22 → 32 / 48 | 0 → 0 / 24 | 10 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | operators | 72/72 | 24 → 35 / 48 | 0 → 0 / 24 | 11 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | rolling | 72/72 | 25 → 36 / 48 | 0 → 0 / 24 | 11 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | vectors | 72/72 | 30 → 35 / 48 | 0 → 0 / 24 | 5 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | crop256 | 72/72 | 36 → 36 / 48 | 0 → 0 / 24 | 0 | 0 | 0/24 |
| perplexity/pplx-decider-v1.1-27b | crop512 | 72/72 | 38 → 38 / 48 | 0 → 0 / 24 | 0 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | minimal | 72/72 | 4 → 26 / 48 | 24 → 24 / 24 | 22 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | words | 72/72 | 22 → 35 / 48 | 10 → 10 / 24 | 13 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | glyphs | 72/72 | 23 → 35 / 48 | 1 → 1 / 24 | 12 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | canonical | 72/72 | 23 → 36 / 48 | 2 → 2 / 24 | 13 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | operators | 72/72 | 23 → 37 / 48 | 1 → 1 / 24 | 14 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | rolling | 72/72 | 24 → 37 / 48 | 0 → 0 / 24 | 13 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | vectors | 72/72 | 26 → 38 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | crop256 | 72/72 | 25 → 37 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |
| openai/gpt-6-luna-decisions | crop512 | 72/72 | 25 → 37 / 48 | 0 → 0 / 24 | 12 | 0 | 0/24 |

Interpreted strokes do not establish clip-resolved visibility. Loose selector centers, decorative rules and enclosure assumptions remain limitations. Partial batches cannot be removed without changing the original model input; the body count includes only wholly bypassable requests.

Routing resources: `{"cpu_seconds": 0.018037771000000036, "measurement": "perf_counter, process_time, process-lifetime VmHWM; no sampling", "peak_rss_bytes": 59981824, "scope": "serial saved-observation reads and geometry decisions; excludes freeze verification and scoring", "wall_seconds": 0.018117708998033777}`.
