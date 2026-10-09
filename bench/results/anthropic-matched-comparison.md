# Matched Claude 5.5 comparison

Same reviewed DEV28, original source words and 512 px images, expanded row/extent candidates and semantic instructions. Claude uses strict chat JSON at medium effort; decision models use their native Choice endpoint. These are authored candidate-selection results, not unrestricted extraction or heldout generalization. Four ambiguous pages are unscored.

| Model/config | Exact tables | Wrong accepted tables | Prose false tables | USD / 28 pages | Pages/USD | Pages/HTTP minute |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| perplexity/pplx-decider-v1.1-27b | 16/16 | 0 | 0/8 | 0.010105 | 2,771.0 | 36.3 |
| anthropic/claude-haiku-5.5 | 16/16 | 0 | 0/8 | 0.053467 | 523.7 | 13.4 |
| anthropic/claude-sonnet-5.5 | 16/16 | 0 | 0/8 | 0.992892 | 28.2 | 26.2 |
| anthropic/claude-opus-5.5 | 15/16 | 0 | 0/8 | 2.037944 | 13.7 | 10.3 |
| openai/gpt-6-luna-decisions | 9/16 | 4 | 0/8 | 0.035633 | 785.8 | 154.1 |

PPLX ties Sonnet and Haiku on exact tables and prose rejection; it recovers one more valid table than Opus, which abstained once. None of the three Claude models accepts an incorrect scored table. This small single-run DEV comparison does not establish general superiority.

| Relative to Claude | Claude/PPLX cost ratio | PPLX API-rate ratio |
| --- | ---: | ---: |
| anthropic/claude-haiku-5.5 | 5.29× | 2.72× |
| anthropic/claude-sonnet-5.5 | 98.26× | 1.39× |
| anthropic/claude-opus-5.5 | 201.69× | 3.52× |

Rates count all 28 transmitted page inputs per model, including four unscored ambiguous pages. HTTP minutes sum original provider request durations; local preparation, telemetry and scheduling are excluded. PPLX/Luna rates are retained from the earlier run, so wall-clock conditions and provider routing differ. No repeated-run uncertainty estimate is available.

Sonnet defaults to high effort; this explicitly medium-effort result is not a default/high-effort baseline. Opus and Haiku default to medium. All Claude models had a 4,096 output-token cap, no temperature override, and no provider fallback. All 84 calls succeeded.

[Full Claude scores and resource measurements](anthropic-baseline.md), [parent PPLX/Luna result](rolling-extent-admission.md), [frozen setup and official sources](../ANTHROPIC_BASELINES.md).
