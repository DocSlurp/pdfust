# R001 row-at-a-time DEV pilot

Ten correlated templates across three vocabulary families. The prespecified default rotates vocabulary across templates; --all30 adds correlated repetitions. These observations do not establish real-world extraction quality.

Source-backed headers are fixed. Fragment choices form complete records; invalid responses return no assembly. Candidate oracle coverage is a harness ceiling, separate from fragment selection and record correctness. Full-source targets include convention notes omitted from region images; transformed-image evidence exactness is not validated.

Image scope: `page`. Full-page images expose source convention notes; region crops omit them. Match scope and resolution before comparing R001 with R002.

Selected case indices: `[0, 11, 22, 3, 14, 25, 6, 17, 28, 9]`. Unique charged/replayed request identities: 80; effective USD: 0.01105488.

Positive provider-reported charges take precedence; other costs use retained token/catalog estimates with cache assumptions preserved in JSON. Reservations remain budget admissions. Local replay is not a new provider request. API-only pages/min excludes local preprocessing and is not end-to-end throughput. Lost-source counts cover validated outputs; failures and unattempted inputs are reported separately.

| Model | Arm | Inputs / scored | Errors / unattempted | Fragment accuracy | Exact regions | Record F1 | Lost source | Unassigned fragments | Oracle fragments | Tokens in / out | Effective USD | Pages/USD | API-only pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions | geometry | 10 / 10 | 0 / 0 | 0.733 | 4 | 0.400 | 0 | 0 | 30 / 30 | 14603 / 0 | ~0.001460 | 6848 | 180.4 |
| openai/gpt-6-luna-decisions | image128 | 10 / 10 | 0 / 0 | 0.700 | 3 | 0.300 | 0 | 0 | 30 / 30 | 15193 / 0 | ~0.001519 | 6582 | 182.5 |
| openai/gpt-6-luna-decisions | image512 | 10 / 10 | 0 / 0 | 0.800 | 6 | 0.600 | 0 | 0 | 30 / 30 | 17113 / 0 | ~0.001711 | 5844 | 191.6 |
| openai/gpt-6-luna-decisions | image1200 | 10 / 10 | 0 / 0 | 0.833 | 7 | 0.700 | 0 | 0 | 30 / 30 | 26063 / 0 | ~0.002606 | 3837 | 162.4 |
| perplexity/pplx-decider-v1.1-27b | geometry | 10 / 10 | 0 / 0 | 0.733 | 4 | 0.400 | 0 | 0 | 30 / 30 | 37260 / 30 | 0.000745 | 13419 | 166.8 |
| perplexity/pplx-decider-v1.1-27b | image128 | 10 / 10 | 0 / 0 | 0.733 | 4 | 0.400 | 0 | 0 | 30 / 30 | 38838 / 30 | 0.000777 | 12874 | 179.0 |
| perplexity/pplx-decider-v1.1-27b | image512 | 10 / 10 | 0 / 0 | 0.700 | 3 | 0.300 | 0 | 0 | 30 / 30 | 42228 / 30 | 0.000845 | 11840 | 159.0 |
| perplexity/pplx-decider-v1.1-27b | image1200 | 10 / 10 | 0 / 0 | 0.800 | 6 | 0.600 | 0 | 0 | 30 / 30 | 69558 / 30 | 0.001391 | 7188 | 138.3 |

Preparation resources: `{"cpu_seconds": 2.765721398, "measurement": "serial CPU current process; perf_counter/process_time; current-exec VmHWM bytes; no sampling", "peak_rss_bytes": 132198400, "wall_seconds": 2.747299212991493}`.
