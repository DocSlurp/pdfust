# Frozen rolling candidate admission

All 28 DEV pages remain in each cohort: 0 native vector routes use zero model calls; 28 pages require admission.

| Model / arm | Borderless exact | Prose false table | Controls exact | Unresolved borderless | Unresolved prose |
| --- | ---: | ---: | ---: | ---: | ---: |
| perplexity/pplx-decider-v1.1-27b/image512 | 4/16 | 0/8 | 0/0 | 7/16 | 0/8 |
| openai/gpt-6-luna-decisions/image512 | 4/16 | 0/8 | 0/0 | 0/16 | 0/8 |

Ambiguous pages are excluded from all correctness and binary presence denominators. Their decisions and source conservation remain observable:

| Model / arm | Ambiguous pages | Decisions (unscored) |
| --- | ---: | --- |
| perplexity/pplx-decider-v1.1-27b/image512 | 4 | {'rolling': 4} |
| openai/gpt-6-luna-decisions/image512 | 4 | {'not_table': 4} |

| Model / arm | Intended borderless values | Intended borderless words | Source IDs conserved |
| --- | ---: | ---: | --- |
| perplexity/pplx-decider-v1.1-27b/image512 | 128/245 | 170/294 | True |
| openai/gpt-6-luna-decisions/image512 | 128/245 | 170/294 | True |

HTTP median ms: 398.13656150363386; complete summed HTTP seconds: 41.16834687096707; elapsed measurements: 56 requests. Missing elapsed measurements remain unmeasured.
Unique retained requests: 56; complete effective USD: 0.02598488; known partial USD: 0.02598488; unknown-cost requests: 0.

Positive provider charges take precedence; zero/missing charges use catalog token rates when complete. Reservations are admission accounting. Missing prices/tokens remain unknown. API elapsed and CPU preparation remain separate.

Source IDs are conserved by every selection, including abstention. Textual slot ownership uses authored silver references; it is not independently annotated source-ID gold. Candidate coverage and automatic admission are distinct. No model confidence is calibrated correctness; no real-world or heldout claim.

CPU preparation: wall 2.495s; CPU 2.483s; peak RSS 61079552 bytes. Measurement: perf_counter/process_time; /proc/self/status VmHWM (current executable); sequential CPU; lifetime peak; no sampling.
