# R001 row-at-a-time DEV pilot

Ten correlated templates across three vocabulary families. The prespecified default rotates vocabulary across templates; --all30 adds correlated repetitions. These observations do not establish real-world extraction quality.

Source-backed headers are fixed. Fragment choices form complete records; invalid responses return no assembly. Candidate oracle coverage is a harness ceiling, separate from fragment selection and record correctness. Full-source targets include convention notes omitted from region images; transformed-image evidence exactness is not validated.

Image scope: `page`. Full-page images expose source convention notes; region crops omit them. Match scope and resolution before comparing R001 with R002.

Selected case indices: `[0, 11, 22, 3, 14, 25, 6, 17, 28, 9]`. Unique charged/replayed request identities: 2; effective USD: 0.00021578.

Positive provider-reported charges take precedence; other costs use retained token/catalog estimates with cache assumptions preserved in JSON. Reservations remain budget admissions. Local replay is not a new provider request. API-only pages/min excludes local preprocessing and is not end-to-end throughput. Lost-source counts cover validated outputs; failures and unattempted inputs are reported separately.

| Model | Arm | Inputs / scored | Errors / unattempted | Fragment accuracy | Exact regions | Record F1 | Lost source | Unassigned fragments | Oracle fragments | Tokens in / out | Effective USD | Pages/USD | API-only pages/min |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions | geometry | 10 / 0 | 1 / 9 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 1436 / 0 | ~0.000144 | 0 | 0.0 |
| openai/gpt-6-luna-decisions | image128 | 10 / 0 | 0 / 10 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 0 / 0 | unknown | unknown | unknown |
| openai/gpt-6-luna-decisions | image512 | 10 / 0 | 0 / 10 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 0 / 0 | unknown | unknown | unknown |
| openai/gpt-6-luna-decisions | image1200 | 10 / 0 | 0 / 10 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 0 / 0 | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | geometry | 10 / 0 | 1 / 9 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 3609 / 3 | 0.000072 | 0 | 0.0 |
| perplexity/pplx-decider-v1.1-27b | image128 | 10 / 0 | 0 / 10 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 0 / 0 | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | image512 | 10 / 0 | 0 / 10 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 0 / 0 | unknown | unknown | unknown |
| perplexity/pplx-decider-v1.1-27b | image1200 | 10 / 0 | 0 / 10 | unknown | 0 | unknown | 0 | 0 | 30 / 30 | 0 / 0 | unknown | unknown | unknown |

Preparation resources: `{"cpu_seconds": 2.651876549, "measurement": "serial CPU current process; perf_counter/process_time; current-exec VmHWM bytes; no sampling", "peak_rss_bytes": 132018176, "wall_seconds": 2.635129607995623}`.
