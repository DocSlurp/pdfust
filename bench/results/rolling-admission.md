# A002 rolling candidate admission

All 28 DEV pages remain in each cohort: four native vector routes use zero model calls; 24 pages require admission.

| Model / arm | Borderless exact / 12 | Prose false table / 12 | Controls exact / 4 | Unresolved borderless / 12 | Unresolved prose / 12 |
| --- | ---: | ---: | ---: | ---: | ---: |
| perplexity/pplx-decider-v1.1-27b/text | 12/12 | 12/12 | 4/4 | 0/12 | 0/12 |
| perplexity/pplx-decider-v1.1-27b/image512 | 12/12 | 6/12 | 4/4 | 0/12 | 0/12 |
| openai/gpt-6-luna-decisions/text | 7/12 | 7/12 | 4/4 | 0/12 | 2/12 |
| openai/gpt-6-luna-decisions/image512 | 12/12 | 0/12 | 4/4 | 0/12 | 0/12 |

| Model / arm | Intended borderless values /144 | Intended borderless words /180 | Source IDs conserved |
| --- | ---: | ---: | --- |
| perplexity/pplx-decider-v1.1-27b/text | 144/144 | 180/180 | True |
| perplexity/pplx-decider-v1.1-27b/image512 | 144/144 | 180/180 | True |
| openai/gpt-6-luna-decisions/text | 84/144 | 105/180 | True |
| openai/gpt-6-luna-decisions/image512 | 144/144 | 180/180 | True |

HTTP median ms: 326.44388399785385; complete summed HTTP seconds: 32.785510525878635; elapsed measurements: 96 requests. Missing elapsed measurements remain unmeasured.
Unique retained requests: 96; complete effective USD: 0.01373948; known partial USD: 0.01373948; unknown-cost requests: 0.

Positive provider charges take precedence; zero/missing charges use catalog token rates when complete. Reservations are admission accounting. Missing prices/tokens remain unknown. API elapsed and CPU preparation remain separate.

Source IDs are conserved by every selection, including abstention. Textual slot ownership uses authored silver references; it is not independently annotated source-ID gold. Candidate coverage and automatic admission are distinct. No model confidence is calibrated correctness; no real-world or heldout claim.

CPU preparation: wall 1.933s; CPU 1.923s; peak RSS 55943168 bytes. Measurement: perf_counter/process_time; /proc/self/status VmHWM (current executable); sequential CPU; lifetime peak; no sampling.
