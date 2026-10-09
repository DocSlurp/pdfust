# Remote GPU prompt screen

Four generic prompt variants were frozen before inference. Each retains the original RGB512 image and literal source state. All source, projection and returned request hashes were verified before local DEV references were opened. No case-specific wording was tuned.

| Model / prompt | Valid/planned | Known correct | Ambiguous abstention | Known abstentions | Partition exact | Conserved | Inference s | CPU s | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Flash / original RGB512 | 24/24 | 10/16 | 0/8 | 0 | 10/24 | 24/24 | 2.141 | 3.429 | 18796.2 |
| Flash / sufficiency | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 2.059 | 3.392 | 18796.5 |
| Flash / alternatives | 24/24 | 7/16 | 0/8 | 0 | 7/24 | 24/24 | 1.484 | 2.812 | 18796.5 |
| Flash / identity | 24/24 | 8/16 | 1/8 | 1 | 9/24 | 24/24 | 1.490 | 2.820 | 18796.5 |
| Flash / neutral | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 1.454 | 2.795 | 18796.5 |
| Clef / original RGB512 | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 | 5.042 | 6.374 | 53032.2 |
| Clef / sufficiency | 24/24 | 11/16 | 0/8 | 3 | 11/24 | 24/24 | 4.845 | 6.152 | 53031.4 |
| Clef / alternatives | 24/24 | 11/16 | 1/8 | 1 | 12/24 | 24/24 | 4.312 | 5.660 | 53031.4 |
| Clef / identity | 24/24 | 8/16 | 1/8 | 7 | 9/24 | 24/24 | 4.377 | 5.756 | 53031.4 |
| Clef / neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 4.141 | 5.455 | 53031.4 |
| PPLX / original RGB512 | 24/24 | 9/16 | 0/8 | 4 | 9/24 | 24/24 | 5.751 | 8.049 | 6079.2 |
| PPLX / sufficiency | 24/24 | 13/16 | 0/8 | 0 | 13/24 | 24/24 | 5.542 | 7.912 | 6080.0 |
| PPLX / alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 4.049 | 6.435 | 6080.0 |
| PPLX / identity | 24/24 | 12/16 | 3/8 | 3 | 15/24 | 24/24 | 4.175 | 6.579 | 6080.0 |
| PPLX / neutral | 24/24 | 10/16 | 0/8 | 1 | 10/24 | 24/24 | 3.976 | 6.371 | 6080.0 |

| Model / variant | Known gains / losses | Ambiguous abstention gains / losses | Choice changes | Unpaired |
|---|---:|---:|---:|---:|
| Flash / sufficiency | 1 / 3 | 0 / 0 | 8 | 0 |
| Flash / alternatives | 3 / 6 | 0 / 0 | 13 | 0 |
| Flash / identity | 0 / 2 | 1 / 0 | 6 | 0 |
| Flash / neutral | 4 / 6 | 0 / 0 | 14 | 0 |
| Clef / sufficiency | 4 / 2 | 0 / 0 | 11 | 0 |
| Clef / alternatives | 2 / 0 | 1 / 0 | 5 | 0 |
| Clef / identity | 3 / 4 | 1 / 0 | 13 | 0 |
| Clef / neutral | 5 / 2 | 0 / 0 | 8 | 0 |
| PPLX / sufficiency | 5 / 1 | 0 / 0 | 10 | 0 |
| PPLX / alternatives | 2 / 3 | 0 / 0 | 9 | 0 |
| PPLX / identity | 5 / 2 | 3 / 0 | 10 | 0 |
| PPLX / neutral | 3 / 2 | 0 / 0 | 10 | 0 |

| Model / prompt | Tie abstentions | Missing / failed / malformed | CUDA allocated / reserved GiB |
|---|---:|---:|---:|
| Flash / original RGB512 | 0 | 0 / 0 / 0 | 17.86 / 17.93 |
| Flash / sufficiency | 0 | 0 / 0 / 0 | 17.86 / 18.02 |
| Flash / alternatives | 0 | 0 / 0 / 0 | 17.85 / 18.02 |
| Flash / identity | 0 | 0 / 0 / 0 | 17.85 / 18.02 |
| Flash / neutral | 0 | 0 / 0 / 0 | 17.86 / 18.02 |
| Clef / original RGB512 | 0 | 0 / 0 / 0 | 51.34 / 51.50 |
| Clef / sufficiency | 0 | 0 / 0 / 0 | 51.33 / 51.47 |
| Clef / alternatives | 0 | 0 / 0 / 0 | 51.33 / 51.47 |
| Clef / identity | 0 | 0 / 0 / 0 | 51.33 / 51.47 |
| Clef / neutral | 0 | 0 / 0 / 0 | 51.32 / 51.47 |
| PPLX / original RGB512 | 2 | 0 / 0 / 0 | 48.76 / 48.86 |
| PPLX / sufficiency | 0 | 0 / 0 / 0 | 48.75 / 48.82 |
| PPLX / alternatives | 0 | 0 / 0 / 0 | 48.75 / 48.82 |
| PPLX / identity | 2 | 0 / 0 / 0 | 48.75 / 48.82 |
| PPLX / neutral | 1 | 0 / 0 / 0 | 48.75 / 48.82 |

Known and ambiguous denominators remain planned counts, including missing or malformed responses. Tied native maxima conservatively become unresolved; confidence calibration is unvalidated. Partitions and conservation use the source-candidate contract; amount/header/cell reconstruction is unmeasured.

Inference wall/CPU covers adapter preprocessing and native prediction. RSS is process-lifetime high water for the inference process; baseline and screen use separate processes. Loading is excluded from per-request time. Regions run serially. CUDA allocation/reservation peaks are retained in JSON when reported; device-wide utilization is outside this table. No inference cost is inferred from latency.

Source manifest SHA256: `0ddd6c3c02e86a3cd52280446d19112e20ede72dba709c26a1ae07c11d0b3104`. Prompt provenance SHA256: `030bd4185a5971b761b151c2e7471d8428ec51c3c2d2bdfe8472812f3adab59c`.
