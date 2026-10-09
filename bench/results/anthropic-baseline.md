# Matched Anthropic 5.5 source-candidate admission baselines

Ambiguous and diagnostic cohorts are excluded from binary/exact model claims. Earlier fresh class-cue admission results are invalid for primary claims.

| Cohort/model | Eligible tables exact | Accepted wrong tables | Eligible prose false table | Table unresolved / missing | Ambiguous proposals |
| --- | ---: | ---: | ---: | --- | ---: |
| cohort0/anthropic/claude-opus-5.5 | 15/16 | 0 | 0/8 | 1 / 0 | 0 |
| cohort0/anthropic/claude-sonnet-5.5 | 16/16 | 0 | 0/8 | 0 / 0 | 0 |
| cohort0/anthropic/claude-haiku-5.5 | 16/16 | 0 | 0/8 | 0 / 0 | 1 |

Unique requests 84; complete effective USD 3.0843026; known partial USD 3.0843026; unknown charge requests 0.

Positive reported charges take precedence; zero/missing charges use retained complete catalog token rates. Reservations remain admission accounting. Missing tokens/rates stay unknown. No inference occurs by default.

All selected and unresolved source IDs are conserved. Candidate oracle coverage is not achieved selection; authored DEV outcomes are not independent generalization or calibrated confidence.

| Model | Requested / planned pages | Successful requests | Effective USD | Pages/USD | Pages/HTTP minute |
| --- | ---: | ---: | ---: | ---: | ---: |
| anthropic/claude-opus-5.5 | 28/28 | 28 | 2.037944 | 13.73933729287949 | 10.320287298184729 |
| anthropic/claude-sonnet-5.5 | 28/28 | 28 | 0.992892 | 28.200448789999314 | 26.217363186803578 |
| anthropic/claude-haiku-5.5 | 28/28 | 28 | 0.0534666 | 523.6914260491596 | 13.370958355360537 |

Rates count paid requested pages; native zero-call pages are excluded. HTTP-minute rates use summed request durations, not end-to-end throughput.
API HTTP elapsed milliseconds (complete measured sum): 352511.2806440011.
Local preparation CPU/RSS metadata: {'wall_seconds': 0.09885145400767215, 'cpu_seconds': 0.09838956600000001, 'peak_rss_bytes': 53325824, 'measurement': 'perf_counter/process_time; /proc/self/status VmHWM (current executable); sequential CPU; lifetime RSS; no sampling'}.
HTTP durations describe provider requests; they do not measure remote CPU/RAM.

Request settings: {"max_tokens": 4096, "provider": {"allow_fallbacks": false, "max_price": {"completion": 20, "prompt": 4}, "require_parameters": true}, "reasoning": {"effort": "medium"}}


| Model | Input USD/M tokens | Output USD/M tokens |
| --- | ---: | ---: |
| anthropic/claude-opus-5.5 | 4.0 | 20.0 |
| anthropic/claude-sonnet-5.5 | 2.0 | 10.0 |
| anthropic/claude-haiku-5.5 | 0.10 | 0.5 |

Local execution CPU/RSS metadata: {"wall_seconds": 383.0731969969929, "cpu_seconds": 26.503148548, "peak_rss_bytes": 114249728, "measurement": "perf_counter/process_time; /proc/self/status VmHWM (current executable); single CPU process including HTTP wait; lifetime RSS; no sampling; remote CPU/RAM unmeasured"}
Original source text, image blocks, q0 instructions and criteria are preserved; only API transport changes. One source page per request; model confidence is unreported. First failure stops that model, without retries. Prices and provider provenance are retained in evaluation.json catalog_provenance.

## Additional retained metrics

| Model | Exact cell matrices | Exact spans | Owned target values | Owned target words | Input tokens | Output tokens | Cache-read tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic/claude-opus-5.5 | 15/16 | 15/16 | 231 | 290 | 493,021 | 3,293 | 0 |
| anthropic/claude-sonnet-5.5 | 16/16 | 16/16 | 235 | 294 | 493,021 | 685 | 0 |
| anthropic/claude-haiku-5.5 | 16/16 | 16/16 | 235 | 294 | 493,021 | 8,329 | 0 |

All 84 costs were positive provider-reported charges. Every request supplied cache counters and reported zero cache-read tokens. Maximum input was 64,561 tokens, below Haiku's 100,000-token pricing threshold; no output reached the 4,096-token cap. Local CPU/RAM measurements include orchestration, not remote inference. All three Langfuse model/price registrations and one indexed generation per model were verified.

[Matched PPLX/Luna comparison](anthropic-matched-comparison.md).
