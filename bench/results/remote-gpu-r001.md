# R001: native GPU decision models on L015 DEV regions

Five image models completed all 216 inputs each without schema or worker failures: Clef-Flash 9B, Perplexity Decider v1.1 27B, Intern-Decision-4B, Qwen3.5-4B through stock vLLM, and Clef 27B. A separate Nimble-v3 text-only ablation completed 24 inputs. None abstained on the ambiguous controls. Rental billing remains pending.

Each image arm contains the same 24 authored source pages with one supplied two-chunk region per page: 16 known references and eight ambiguous controls. Nine image arms repeat those pages; 216 inputs are not 216 independent pages or complete-page extractions. This is conditional grouping of supplied regions and candidate boundaries. The three transport/vision controls passed separately and are excluded from all cohort denominators.

All staged request bodies and PNGs were checked against frozen L015 hashes, alongside source PDF and observation hashes, before DEV references were read locally. No references were staged remotely. Native distributions use the existing scorer; tied maxima abstain. Stock vLLM supplies generated choice labels, with no invented probabilities or confidence. The retained PPLX transport model field does not identify the other deployed engines; their identities come from pinned releases and run configuration.

Each cell below shows known-correct/16. Every image arm has 24/24 valid decisions and ambiguous-abstain **0/8**. These are small, correlated DEV cases rather than a general document-quality ranking.

| Arm | Flash 9B | PPLX 27B | Intern 4B | Qwen 4B stock | Clef 27B |
|---|---:|---:|---:|---:|---:|
| rgb-512 | 10/16 | 9/16 | 12/16 | 10/16 | 9/16 |
| rgb-768 | 11/16 | 12/16 | 12/16 | 10/16 | 11/16 |
| rgb-1024 | 11/16 | 12/16 | 12/16 | 10/16 | 12/16 |
| gray-512 | 10/16 | 9/16 | 12/16 | 9/16 | 9/16 |
| gray-768 | 11/16 | 12/16 | 12/16 | 9/16 | 11/16 |
| gray-1024 | 11/16 | 12/16 | 12/16 | 9/16 | 12/16 |
| lowbit-512 | 10/16 | 10/16 | 12/16 | 8/16 | 9/16 |
| lowbit-768 | 11/16 | 11/16 | 12/16 | 9/16 | 10/16 |
| lowbit-1024 | 11/16 | 12/16 | 12/16 | 9/16 | 9/16 |

Nimble-v3 text-geometry: **24/24 valid, 6/16 known-correct, 0/8 ambiguous-abstain**, with no schema or worker failures. Its declared projection removes only image parts from the first 24 RGB512 requests and overrides the transport model; literal source state and questions are preserved exactly. Original image and projected request hashes were verified through separate provenance. Complete visual references can be unrecoverable after image removal, so this is an evidence ablation rather than a matched vision ranking. Nimble-v3 is CC-BY-NC-4.0 and differs from the older Apache-2.0 Nimble release.

Compared with the [completed same-source hosted L015 run](lowlevel-images-large.md), these local decision heads do not exactly reproduce hosted choices. Backend arithmetic, prompt assembly and image preprocessing remain separate variables. The local PPLX processor uses its reference 65,536–4,194,304-pixel bounds; the hosted image path is not assumed identical.

| Matched model | Native known-correct / 144 | Hosted known-correct / 144 | Same choice / 216 |
|---|---:|---:|---:|
| Flash 9B | 96/144 | 89/144 | 209/216 |
| PPLX 27B | 99/144 | 109/144 | 204/216 |
| Clef 27B | 92/144 | 83/144 | 196/216 |

Both hosted and local versions have 0/72 ambiguous abstentions across the nine repeated arms. For example, PPLX RGB512 changes from hosted 12/16 to native 9/16; 768 matches 12/16 and 1024 changes 13/16 to 12/16. No cause has been established.

Rates below are fresh region inputs/minute over cumulative measured adapter `predict` wall time, including native preprocessing. Qwen includes serial loopback HTTP transport and stock generation. All calls yielded valid decisions; aliases/replays are excluded. Full-page pages/minute and pages/USD are unavailable.

| Arm | Flash 9B inputs/min | PPLX 27B inputs/min | Intern 4B inputs/min | Qwen 4B stock inputs/min | Clef 27B inputs/min |
|---|---:|---:|---:|---:|---:|
| rgb-512 | 672.63 | 250.41 | 25.21 | 277.90 | 285.59 |
| rgb-768 | 763.43 | 309.39 | 15.29 | 274.31 | 267.90 |
| rgb-1024 | 662.25 | 258.01 | 8.68 | 267.65 | 233.11 |
| gray-512 | 912.70 | 349.73 | 25.58 | 270.66 | 310.58 |
| gray-768 | 786.13 | 316.10 | 15.58 | 276.56 | 273.47 |
| gray-1024 | 680.62 | 266.06 | 8.80 | 262.77 | 245.81 |
| lowbit-512 | 901.31 | 343.57 | 25.21 | 268.47 | 300.93 |
| lowbit-768 | 779.13 | 311.81 | 15.31 | 274.98 | 268.72 |
| lowbit-1024 | 674.84 | 262.75 | 8.73 | 278.76 | 236.53 |

| Worker scope | Load wall / CPU s | Predict wall / CPU s | Worker wall / CPU s | Warm inputs/min | Worker inputs/min | Process peak RSS GiB | CUDA run peak allocated / reserved GiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Flash 9B, 216 inputs | 5.12 / 5.97 | 17.31 / 30.82 | 24.20 / 36.97 | 748.85 | 535.49 | 18.36 | 17.91 / 18.04 |
| PPLX 27B, 216 inputs | 18.57 / 19.60 | 44.36 / 66.10 | 63.56 / 86.09 | 292.15 | 203.91 | 5.94 | 48.83 / 49.01 |
| Intern 4B, 216 inputs | 6.50 / 7.26 | 945.58 / 967.72 | 954.75 / 975.30 | 13.71 | 13.57 | 8.84 | 8.78 / 8.96 |
| Clef 27B, 216 inputs | 7.63 / 8.35 | 48.59 / 62.86 | 60.77 / 71.45 | 266.74 | 213.25 | 51.79 | 51.41 / 51.60 |
| Nimble-v3 text, 24 inputs | 15.02 / 26.78 | 27.83 / 23.96 | 42.92 / 50.79 | 51.74 | 33.55 | 16.32 | 18.85 / 19.18 |

Worker-inclusive rates include model load, input handling and logging, but exclude paid bootstrap, weight download, provisioning idle time and cleanup. They are not full rental-lifecycle rates. Process CPU covers worker threads and excludes subprocesses; it may exceed elapsed wall time. RSS uses Linux `resource.getrusage(RUSAGE_SELF).ru_maxrss`, a process-lifetime high-water mark. CUDA run peaks take the maximum across initialization and every completed attempt because counters reset between calls. For Nimble, initialization reaches 18.85 GiB allocated, exceeding the final status counter.

Qwen’s model runs in a separate vLLM server. Its **client** measures 47.58 s predict wall / 2.34 s CPU, 49.13 s worker wall / 2.50 s CPU, and 0.040 GiB process peak RSS; warm rate is 272.36 inputs/min and client-worker rate is 263.78. Client initialization only configures transport and is not model load. The server log reports 2.422 s model loading and 8.61 GiB model-load memory; first logged startup to server start spans approximately 23 s at one-second timestamp precision, not a complete provisioning stopwatch.

Qwen server-plus-recursive-child sampling ran once per second. During the 49.12 s request window, 48 fully contained sampling intervals cover 48.05 s and observe 71.36 CPU s; boundary intervals and pre-observation CPU remain unmeasured. Sampled summed server RSS peaks at 6.34 GiB in that window (6.36 GiB over the entire retained sampling period); shared pages can be counted more than once. These server measurements must not be replaced by the small client RSS. Server PyTorch allocation/reservation peaks are unmeasured. Device-wide sampling peaks at 63,102 MiB, including the configured vLLM KV-cache reservation.

| Device-wide 1 s sampler | Available samples | Mean GPU utilization | Peak device VRAM MiB |
|---|---:|---:|---:|
| Flash 9B | 25/25 | 61.40% | 19,184 |
| PPLX 27B | 64/64 | 58.42% | 50,879 |
| Intern 4B | 955/955 | 24.37% | 9,874 |
| Qwen 4B stock | 50/50 | 57.12% | 63,102 |
| Clef 27B | 61/61 | 75.80% | 53,544 |
| Nimble-v3 text | 43/43 | 9.05% | 20,315 |

Sample means include load/idle phases and describe the whole device, not per-worker utilization. All hosts ran serial singleton requests, `OMP_NUM_THREADS=8` and `TOKENIZERS_PARALLELISM=false`, with no GPU request concurrency.

Flash and Clef 27B ran sequentially on the same RTX PRO 6000 Blackwell Max-Q host: 97,887 MiB GPU memory, 12 effective CPU cores, 128,783 MiB host RAM, driver 595.71.05, Torch 2.11.0+cu130, Transformers 5.10.2 and FLA 0.5.2. PPLX and Nimble ran sequentially on one RTX PRO 6000 Blackwell Workstation host: 97,887 MiB GPU memory, 32 effective CPU cores, 1,031,870 MiB host RAM, driver 590.48.01, Torch 2.14+cu130, Transformers 5.17 and FLA 0.5.2. Nimble additionally uses PEFT 0.21 and DecisionIndex commit `87d4650`.

Intern used RTX PRO 6000 Blackwell Workstation, 97,887 MiB GPU memory, 24 effective CPU cores, 128,792 MiB host RAM, driver 595.91.07, Torch 2.9.1+cu128 and Transformers 5.14.1 without FLA. Qwen used another RTX PRO 6000 Blackwell Workstation, 97,887 MiB GPU memory, 24 effective CPU cores, driver 580.178.04, vLLM 0.31.0, Torch 2.13+cu130 and Transformers 5.17. Its BF16 server runs eager mode, prefix caching disabled, image processor cache zero, maximum sequence length 8,192, maximum sequences eight, and GPU memory utilization 0.65. Requests remain serial. Different hosts, kernels and serving paths prevent attributing speed differences to parameter count alone. Dependency freezes and bootstrap provenance are retained with returned artifacts.

Actual whole-wave rental charges and region inputs/USD remain pending. Provider inventory hourly quotes include the disk allocation; they are not observed invoice charges. No zero-cost assumption or warm-only rental estimate is reported.

Pinned releases: Flash `fde727a287004204b7518dcc983fe64379776712`; PPLX `6195aa55a72ae21e503c8a60198f7b390d42adb5`; Intern `0e5e6aa7d6d750e2b1504ba11a8136cb58aeb3cd`; Clef 27B `ed3eed331870db2eff4b0db01237128ede8a00ce`; Qwen `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; Nimble-v3 `8e927b9b4afdbb14479fac10a7364d1a695be208`. See the [self-hosted model notes](../HF_DECISION_MODELS.md). Requests, responses, local scorer results, samples and source-index remain ignored under `.scratch/remote-gpu-20261009/r001/` and `.scratch/council/lowlevel-inventor/`.

Frozen L015 manifest SHA256: `0ddd6c3c02e86a3cd52280446d19112e20ede72dba709c26a1ae07c11d0b3104`. Source-index SHA256: `52e9c5241455cb7877cf0976b4fb4969735b5a0d7841972bfcbc6bee1ad0c0a1`. This is one run per configuration on small authored, correlated cases; no universal quality or deployment-cost ranking is established.

## Additional JPT4 cohort

JPT-4B completed 216/216 inputs with no schema or worker failures. Source request and image bytes match the original L015 evidence; the separately declared transport projection changes only `body.model` to `kirp/jpt-4b`. Its native distribution is scored with the same parser and references. All arms retain 16 known cases and eight ambiguous controls.

| Arm | Known-correct / 16 | Ambiguous-abstain / 8 | Fresh region inputs/min |
|---|---:|---:|---:|
| rgb-512 | 10/16 | 0/8 | 391.27 |
| rgb-768 | 10/16 | 0/8 | 635.18 |
| rgb-1024 | 9/16 | 0/8 | 608.56 |
| gray-512 | 10/16 | 1/8 | 654.05 |
| gray-768 | 9/16 | 0/8 | 624.31 |
| gray-1024 | 9/16 | 0/8 | 628.55 |
| lowbit-512 | 10/16 | 0/8 | 646.14 |
| lowbit-768 | 9/16 | 0/8 | 634.87 |
| lowbit-1024 | 9/16 | 0/8 | 611.62 |

Across repeated arms, JPT4 scores 85/144 known cases and 1/72 ambiguous abstentions. Its load is 12.56 wall / 13.76 CPU s; prediction totals 21.96 wall / 43.79 CPU s. Worker totals are 35.10 wall / 57.93 CPU s: 590.05 warm region inputs/min and 369.19 worker-inclusive inputs/min. Process peak RSS is 9.32 GiB; initialization-plus-attempt CUDA run peaks are 8.99 GiB allocated / 10.35 GiB reserved. The device-wide one-second sampler has 35/35 available samples, mean utilization 21.11%, and peak device VRAM 11,285 MiB.

JPT4 is a separate noncommercial research candidate; its release license is CC-BY-NC-4.0. The pinned release is `78312f855b8bebf83ae7e9e8f05b5a0f73f519a9`; the retained environment records Torch 2.14.0, Transformers 5.17.0, FLA 0.5.2 and `llm2jev` commit `2b252d504972764211ef172c1155ac0fedc9c3de`. Host assignment remains to be reconciled with run provenance. Costs and full-page throughput remain unavailable; these are conditional region decisions.
