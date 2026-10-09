# Frozen rolling candidate admission

All 28 DEV pages remain in each cohort: 4 native vector routes use zero model calls; 24 pages require admission.

| Model / arm | Borderless exact | Prose false table | Controls exact | Unresolved borderless | Unresolved prose |
| --- | ---: | ---: | ---: | ---: | ---: |
| perplexity/pplx-decider-v1.1-27b/image512 | 12/12 | 6/12 | 4/4 | 0/12 | 0/12 |
| openai/gpt-6-luna-decisions/image512 | 12/12 | 0/12 | 4/4 | 0/12 | 0/12 |

| Model / arm | Intended borderless values | Intended borderless words | Source IDs conserved |
| --- | ---: | ---: | --- |
| perplexity/pplx-decider-v1.1-27b/image512 | 144/144 | 180/180 | True |
| openai/gpt-6-luna-decisions/image512 | 144/144 | 180/180 | True |

HTTP median ms: 375.8931635020417; complete summed HTTP seconds: 22.081653370070853; elapsed measurements: 48 requests. Missing elapsed measurements remain unmeasured.
Unique retained requests: 48; complete effective USD: 0.00808632; known partial USD: 0.00808632; unknown-cost requests: 0.

Positive provider charges take precedence; zero/missing charges use catalog token rates when complete. Reservations are admission accounting. Missing prices/tokens remain unknown. API elapsed and CPU preparation remain separate.

Source IDs are conserved by every selection, including abstention. Textual slot ownership uses authored silver references; it is not independently annotated source-ID gold. Candidate coverage and automatic admission are distinct. No model confidence is calibrated correctness; no real-world or heldout claim.

CPU preparation: wall 1.820s; CPU 1.810s; peak RSS 931897344 bytes. Measurement: source-only request assembly; perf_counter/process_time; getrusage SELF process-lifetime RSS; single CPU process, no children, no periodic sampling.
