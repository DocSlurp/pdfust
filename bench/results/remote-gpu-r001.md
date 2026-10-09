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

Nimble-v3 text-geometry: warm serving estimate **2258 region inputs/USD**; **24/24 valid, 6/16 known-correct, 0/8 ambiguous-abstain**, with no schema or worker failures. Its declared projection removes only image parts from the first 24 RGB512 requests and overrides the transport model; literal source state and questions are preserved exactly. Original image and projected request hashes were verified through separate provenance. Complete visual references can be unrecoverable after image removal, so this is an evidence ablation rather than a matched vision ranking. Nimble-v3 is CC-BY-NC-4.0 and differs from the older Apache-2.0 Nimble release.

Compared with the [completed same-source hosted L015 run](lowlevel-images-large.md), these local decision heads do not exactly reproduce hosted choices. Backend arithmetic, prompt assembly and image preprocessing remain separate variables. The local PPLX processor uses its reference 65,536–4,194,304-pixel bounds; the hosted image path is not assumed identical.

| Matched model | Native known-correct / 144 | Hosted known-correct / 144 | Same choice / 216 |
|---|---:|---:|---:|
| Flash 9B | 96/144 | 89/144 | 209/216 |
| PPLX 27B | 99/144 | 109/144 | 204/216 |
| Clef 27B | 92/144 | 83/144 | 196/216 |

Both hosted and local versions have 0/72 ambiguous abstentions across the nine repeated arms. For example, PPLX RGB512 changes from hosted 12/16 to native 9/16; 768 matches 12/16 and 1024 changes 13/16 to 12/16. No cause has been established.

Warm serving estimates use `region inputs/min × 60 ÷ allocation USD/hour`, including the quoted GPU and disk allocation: Flash/Clef $1.275/h; original Intern and stock Qwens $1.3083333333/h; PPLX/JPT/Nimble/new-runtime Intern $1.375/h. They exclude initialization, downloads, idle time and cleanup, and are **not billed costs or end-to-end pages/USD**. One tested region comes from each authored page, so these are conditional page-region input equivalents, not full PDF pages. In rate cells, the first value is measured inputs/min and the second is estimated warm inputs/USD.

Rates below are fresh region inputs/minute over cumulative measured adapter `predict` wall time, including native preprocessing. Qwen includes serial loopback HTTP transport and stock generation. All calls yielded valid decisions; aliases/replays are excluded. Full-page pages/minute and pages/USD are unavailable.

| Arm | Flash rate; est. inputs/USD | PPLX rate; est. inputs/USD | Intern rate; est. inputs/USD | Qwen4 rate; est. inputs/USD | Clef rate; est. inputs/USD |
|---|---:|---:|---:|---:|---:|
| rgb-512 | 672.63; 31653 | 250.41; 10927 | 25.21; 1156 | 277.90; 12745 | 285.59; 13440 |
| rgb-768 | 763.43; 35926 | 309.39; 13501 | 15.29; 701 | 274.31; 12580 | 267.90; 12607 |
| rgb-1024 | 662.25; 31165 | 258.01; 11259 | 8.68; 398 | 267.65; 12274 | 233.11; 10970 |
| gray-512 | 912.70; 42950 | 349.73; 15261 | 25.58; 1173 | 270.66; 12412 | 310.58; 14615 |
| gray-768 | 786.13; 36994 | 316.10; 13794 | 15.58; 715 | 276.56; 12683 | 273.47; 12869 |
| gray-1024 | 680.62; 32029 | 266.06; 11610 | 8.80; 403 | 262.77; 12051 | 245.81; 11568 |
| lowbit-512 | 901.31; 42414 | 343.57; 14992 | 25.21; 1156 | 268.47; 12312 | 300.93; 14162 |
| lowbit-768 | 779.13; 36665 | 311.81; 13606 | 15.31; 702 | 274.98; 12611 | 268.72; 12646 |
| lowbit-1024 | 674.84; 31757 | 262.75; 11466 | 8.73; 401 | 278.76; 12784 | 236.53; 11131 |

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

Actual whole-wave rental charges and billed region inputs/USD remain pending. Provider inventory hourly quotes include the disk allocation; they are not observed invoice charges. The explicitly labeled warm serving estimates below use quoted allocation prices; no zero-cost assumption is made.

Pinned releases: Flash `fde727a287004204b7518dcc983fe64379776712`; PPLX `6195aa55a72ae21e503c8a60198f7b390d42adb5`; Intern `0e5e6aa7d6d750e2b1504ba11a8136cb58aeb3cd`; Clef 27B `ed3eed331870db2eff4b0db01237128ede8a00ce`; Qwen `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; Nimble-v3 `8e927b9b4afdbb14479fac10a7364d1a695be208`. See the [self-hosted model notes](../HF_DECISION_MODELS.md). Requests, responses, local scorer results, samples and source-index remain ignored under `.scratch/remote-gpu-20261009/r001/` and `.scratch/council/lowlevel-inventor/`.

Frozen L015 manifest SHA256: `0ddd6c3c02e86a3cd52280446d19112e20ede72dba709c26a1ae07c11d0b3104`. Source-index SHA256: `52e9c5241455cb7877cf0976b4fb4969735b5a0d7841972bfcbc6bee1ad0c0a1`. This is one run per configuration on small authored, correlated cases; no universal quality or deployment-cost ranking is established.

## Additional JPT4 cohort

JPT-4B completed 216/216 inputs with no schema or worker failures. Source request and image bytes match the original L015 evidence; the separately declared transport projection changes only `body.model` to `kirp/jpt-4b`. Its native distribution is scored with the same parser and references. All arms retain 16 known cases and eight ambiguous controls.

| Arm | Known-correct / 16 | Ambiguous-abstain / 8 | Fresh region inputs/min | Est. warm inputs/USD |
|---|---:|---:|---:|---:|
| rgb-512 | 10/16 | 0/8 | 391.27 | 17073 |
| rgb-768 | 10/16 | 0/8 | 635.18 | 27717 |
| rgb-1024 | 9/16 | 0/8 | 608.56 | 26555 |
| gray-512 | 10/16 | 1/8 | 654.05 | 28540 |
| gray-768 | 9/16 | 0/8 | 624.31 | 27243 |
| gray-1024 | 9/16 | 0/8 | 628.55 | 27428 |
| lowbit-512 | 10/16 | 0/8 | 646.14 | 28195 |
| lowbit-768 | 9/16 | 0/8 | 634.87 | 27703 |
| lowbit-1024 | 9/16 | 0/8 | 611.62 | 26689 |

Across repeated arms, JPT4 scores 85/144 known cases and 1/72 ambiguous abstentions. Its load is 12.56 wall / 13.76 CPU s; prediction totals 21.96 wall / 43.79 CPU s. Worker totals are 35.10 wall / 57.93 CPU s: 590.05 warm region inputs/min and 369.19 worker-inclusive inputs/min. Process peak RSS is 9.32 GiB; initialization-plus-attempt CUDA run peaks are 8.99 GiB allocated / 10.35 GiB reserved. The device-wide one-second sampler has 35/35 available samples, mean utilization 21.11%, and peak device VRAM 11,285 MiB.

JPT4 is a separate noncommercial research candidate; its release license is CC-BY-NC-4.0. The pinned release is `78312f855b8bebf83ae7e9e8f05b5a0f73f519a9`; the retained environment records Torch 2.14.0, Transformers 5.17.0, FLA 0.5.2 and `llm2jev` commit `2b252d504972764211ef172c1155ac0fedc9c3de`. JPT4 uses the same PPLX/Nimble host, as recorded below. Costs and full-page throughput remain unavailable; these are conditional region decisions.

## Additional JPT9 and stock Qwen cohorts

JPT9, stock Qwen3.5-2B and stock Qwen3.5-9B each completed 216/216 inputs without schema or worker failures. Each arm has 24 valid results, 16 known cases and eight ambiguous controls; all three have **0/8 ambiguous abstentions in every arm**. Original source, image and request hashes were verified before local scoring. JPT9 changes only the declared transport model scalar to `kirp/jpt-9b`; the stock models reuse the exact original transport body while the server pins the deployed engine identity. Stock models return schema-constrained generated labels, without fabricated native decision probabilities.

| Arm | JPT9 known / 16 | JPT9 rate; est. inputs/USD | Qwen2 known / 16 | Qwen2 rate; est. inputs/USD | Qwen9 known / 16 | Qwen9 rate; est. inputs/USD |
|---|---:|---:|---:|---:|---:|---:|
| rgb-512 | 8/16 | 379.40; 16556 | 6/16 | 339.22; 15557 | 11/16 | 256.98; 11785 |
| rgb-768 | 8/16 | 608.97; 26573 | 7/16 | 342.78; 15720 | 12/16 | 252.21; 11566 |
| rgb-1024 | 8/16 | 594.49; 25942 | 7/16 | 347.06; 15916 | 11/16 | 242.74; 11132 |
| gray-512 | 8/16 | 610.70; 26649 | 7/16 | 344.66; 15806 | 11/16 | 256.75; 11774 |
| gray-768 | 8/16 | 603.27; 26325 | 7/16 | 345.48; 15844 | 11/16 | 246.61; 11309 |
| gray-1024 | 8/16 | 589.67; 25731 | 6/16 | 338.51; 15524 | 11/16 | 246.37; 11298 |
| lowbit-512 | 8/16 | 609.96; 26616 | 6/16 | 347.33; 15928 | 10/16 | 256.94; 11783 |
| lowbit-768 | 9/16 | 632.52; 27601 | 7/16 | 335.86; 15402 | 11/16 | 266.91; 12240 |
| lowbit-1024 | 8/16 | 552.10; 24092 | 7/16 | 353.80; 16225 | 11/16 | 245.79; 11272 |

Across the nine repeated arms, known scores are JPT9 **73/144**, Qwen2 **60/144**, and Qwen9 **99/144**. These totals count repeated source pages and do not represent independent samples.

| Worker scope | Load wall / CPU s | Predict wall / CPU s | Worker wall / CPU s | Warm inputs/min | Worker inputs/min | Worker peak RSS GiB |
|---|---:|---:|---:|---:|---:|---:|
| JPT9 native | 14.73 / 15.99 | 23.01 / 44.72 | 38.33 / 61.11 | 563.11 | 338.09 | 18.394 |
| Qwen2 client | transport only | 37.70 / 2.25 | 39.34 / 2.46 | 343.78 | 329.40 | 0.030 |
| Qwen9 client | transport only | 51.40 / 2.38 | 52.92 / 2.51 | 252.16 | 244.92 | 0.040 |

JPT9 initialization-plus-attempt CUDA peaks are 18.06 GiB allocated / 19.44 GiB reserved. JPT4, JPT9 and Nimble ran sequentially on the PPLX host (55084918, Spain, RTX PRO 6000 Blackwell Workstation, 32 effective CPU cores and 1,031,870 MiB host RAM). JPT9 shares JPT4’s retained Torch 2.14 / Transformers 5.17 / FLA 0.5.2 environment. Its release `9fda2c7f123d36c4789c46c93737e80fc3a6c9fe` is CC-BY-NC-4.0. This remains a noncommercial research comparison.

Qwen2/9 run sequentially on the Qwen4 host using the same BF16/eager vLLM configuration, prefix caching disabled and image processor cache zero. Their client load and RSS are not model load or memory. Separate server monitors measure recursive process-tree resources at one-second intervals, with shared pages potentially counted twice. Server startup is measured separately from download and client inference:

| Server | Startup s | Weight download s | Request window s | Fully contained sampled interval s | Observed server CPU s in those intervals | Sampled server RSS peak GiB in window |
|---|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen3.5-2B | 27.03 | 9.84 | 39.34 | 38.03 | 51.09 | 5.56 |
| Qwen/Qwen3.5-9B | 34.04 | 27.79 | 52.91 | 52.05 | 68.25 | 5.63 |

Boundary CPU intervals and pre-observation activity remain unmeasured; server PyTorch allocation/reservation peaks are unavailable. Download timing reflects this particular host/cache/network and is not an inference rate. All separate controls passed; they are excluded from cohort scores and rates. Qwen2 revision: `15852e8c16360a2fea060d615a32b45270f8a8fc`; Qwen9 revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Whole-wave billing and billed region inputs/USD remain pending.

The original Intern run above remains unchanged; the returned FLA-added and newer-stack comparisons appear below.

| Device-wide 1 s sampler | Available samples | Mean utilization | Peak device VRAM MiB |
|---|---:|---:|---:|
| JPT9 | 38/38 | 31.18% | 20,597 |
| Qwen2 | 40/40 | 37.88% | 62,606 |
| Qwen9 | 53/53 | 84.66% | 63,060 |

## Intern runtime comparison

The original Intern stack, the FLA-added run on its original host, and the newer stack on the PPLX host each completed 216/216 source-verified inputs with no schema or worker failures. All have 0/72 ambiguous abstentions. FLA-added agrees with the original choice on 215/216 inputs and scores 107/144 known cases; the newer stack agrees on 216/216 and preserves 108/144. Adding FLA alone did not improve measured runtime here. The newer stack changes host, Torch and Transformers together, so its speedup does not isolate the cause. Same-host follow-up remains pending.

| Arm | FLA-added known / 16 | FLA-added inputs/min | FLA-added est. warm inputs/USD | New-stack known / 16 | New-stack inputs/min | New-stack est. warm inputs/USD |
|---|---:|---:|---:|---:|---:|---:|
| rgb-512 | 12/16 | 17.50 | 802 | 12/16 | 407.70 | 17790 |
| rgb-768 | 12/16 | 15.76 | 723 | 12/16 | 713.94 | 31154 |
| rgb-1024 | 12/16 | 8.87 | 407 | 12/16 | 683.03 | 29805 |
| gray-512 | 12/16 | 26.93 | 1235 | 12/16 | 741.68 | 32364 |
| gray-768 | 12/16 | 15.84 | 726 | 12/16 | 712.97 | 31112 |
| gray-1024 | 12/16 | 8.81 | 404 | 12/16 | 697.86 | 30452 |
| lowbit-512 | 12/16 | 26.52 | 1216 | 12/16 | 736.11 | 32121 |
| lowbit-768 | 11/16 | 15.80 | 725 | 12/16 | 724.35 | 31608 |
| lowbit-1024 | 12/16 | 8.87 | 407 | 12/16 | 699.73 | 30534 |

| Stack | Load wall / CPU s | Predict wall / CPU s | Worker wall / CPU s | Warm inputs/min | Est. warm inputs/USD | Process RSS GiB | CUDA run peak allocated / reserved GiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original | 6.50 / 7.26 | 945.58 / 967.72 | 954.75 / 975.30 | 13.71 | 629 | 8.84 | 8.78 / 8.96 |
| FLA added, original host | 8.68 / 9.24 | 951.61 / 968.86 | 963.15 / 978.42 | 13.62 | 625 | 8.91 | 8.90 / 9.15 |
| New stack, PPLX host | 11.15 / 12.04 | 19.68 / 41.59 | 31.47 / 54.01 | 658.40 | 28730 | 8.87 | 8.73 / 8.86 |

New stack: Torch 2.14, Transformers 5.17 and FLA 0.5.2, without causal-conv1d, on host 55084918. Original stack: Torch 2.9.1 and Transformers 5.14.1 on host 55084071; the FLA-added comparison retains that host and base stack. The newer run preserves the pinned Intern model and source requests. Its three controls pass separately and do not enter the 216-input rate or score denominators.

| Intern device-wide 1 s sampler | Available samples | Mean utilization | Peak device VRAM MiB |
|---|---:|---:|---:|
| FLA added | 963/963 | 24.09% | 10,070 |
| New stack | 31/31 | 27.65% | 9,759 |

## SmolVLM diagnostic admission

SmolVLM2-2.2B-Instruct completed 216/216 source-verified region requests after explicit runtime changes and diagnostic admission despite failed semantic controls. Schema-valid output does not establish visual understanding. Separate controls returned valid labels on 3/3 requests but matched the expected circle/square/blank descriptions on **1/3**: `unresolved`, `split`, `split` versus `join`, `split`, `unresolved`. These controls remain outside the authored cohort.

| Attempt | Admission/outcome | Authored region inputs |
|---|---|---:|
| Original vLLM sweep | Pre-health failure: missing `num2words` in the SmolVLM processor | 0 |
| Retry after dependency installation | Pre-health failure: CUDA segfault during FlashInfer autotuning | 0 |
| Diagnostic runtime | Health/schema admission succeeded; semantic control gate failed (1/3 correct); explicit diagnostic override admitted cohort | 216 |

The retained final runtime uses Triton main attention, Torch SDPA for vision, and disabled FlashInfer autotuning. It preserves the pinned model and original source evidence. Neither earlier startup failure is discarded or scored as an authored-case prediction. This was not an earlier semantic-skip cohort; both previous attempts failed before health admission.

| Arm | Known-correct / 16 | Ambiguous-abstain / 8 | Region inputs/min | Est. warm inputs/USD |
|---|---:|---:|---:|---:|
| rgb-512 | 5/16 | 1/8 | 515.16 | 23625 |
| rgb-768 | 5/16 | 0/8 | 511.71 | 23467 |
| rgb-1024 | 5/16 | 1/8 | 505.13 | 23165 |
| gray-512 | 5/16 | 1/8 | 521.54 | 23918 |
| gray-768 | 4/16 | 1/8 | 508.80 | 23334 |
| gray-1024 | 4/16 | 1/8 | 496.97 | 22791 |
| lowbit-512 | 5/16 | 0/8 | 534.52 | 24513 |
| lowbit-768 | 6/16 | 1/8 | 509.19 | 23351 |
| lowbit-1024 | 4/16 | 1/8 | 496.66 | 22777 |

Across repeated arms, known-correct is **43/144** and ambiguous-abstain **7/72**, with zero cohort schema/worker failures. Prediction totals 25.37 wall / 2.30 client CPU s; client-worker totals 29.32 wall / 2.46 CPU s. Warm rate is 510.84 region inputs/min (23427 estimated warm inputs/USD); client-worker rate is 442.03 inputs/min. Client RSS peaks at 0.038 GiB and is not server/model memory. Transport initialization is not model load. Final server startup takes 14.03 s and weight download 10.10 s.

At one-second server-plus-recursive-child sampling, the 29.30 s request window has 28 fully contained intervals spanning 28.02 s and observing 19.65 CPU s. Sampled summed server RSS peaks at 3.68 GiB during requests; shared pages can be counted twice and CPU boundary intervals remain unmeasured. Server PyTorch allocation/reservation peaks are unavailable. Device-wide sampling has 30/30 available samples, mean utilization 46.40%, and peak device VRAM 62,534 MiB, including configured KV-cache allocation.

Release: `482adb537c021c86670beed01cd58990d01e72e4`. This uses the stock-Qwen GPU host and $1.3083333333/h GPU-plus-disk quote; warm inputs/USD excludes all three attempts’ startup/download time, idle and cleanup, and is not billed cost. Serial BF16/eager inference, no prefix caching, no image processor cache, and the common source-only transport remain as above. Full PDF throughput is unavailable.

## Recovered LFM, Qwen0.8 and MiniCPM diagnostic cohorts

All three completed 216/216 source-verified inputs with explicit diagnostic admission after semantic controls failed. Separate control accuracy is LFM 1/3, Qwen0.8 2/3 and MiniCPM 1/3; all control responses are schema-valid. Cohort schema/worker failures are zero. These controls are excluded from scores/rates and prevent treating schema acceptance as evidence of visual understanding.

LFM first failed before health admission during CUDA initialization, then reached a healthy server whose controls returned HTTP 400 because its Jinja chat template was missing. The completed diagnostic run pins that template and uses Triton main/Torch SDPA vision/disabled FlashInfer autotuning. Qwen0.8 and MiniCPM previously reached healthy servers but their semantic gates skipped authored requests. A subsequent diagnostic controller was interrupted by host reboot during Qwen0.8 startup, before controls/authored requests; MiniCPM was unattempted in that interrupted sweep. The final two runs use the original attention settings on the recovered host. Completed LFM evidence was preserved across the later interruption; no measurement spans the reboot and no failed attempt is erased.

**LiquidAI/LFM2-VL-1.6B**: known 80/144; ambiguous abstention 0/72 across repeated source pages. Release `2c2e7f9b0f48a478d7d497ef1864519dfd3994cd`.

| Arm | Known / 16 | Abstain / 8 | Inputs/min | Est. warm inputs/USD |
|---|---:|---:|---:|---:|
| rgb-512 | 9/16 | 0/8 | 704.34 | 32301 |
| rgb-768 | 9/16 | 0/8 | 698.16 | 32018 |
| rgb-1024 | 9/16 | 0/8 | 682.30 | 31290 |
| gray-512 | 9/16 | 0/8 | 706.64 | 32407 |
| gray-768 | 9/16 | 0/8 | 692.01 | 31736 |
| gray-1024 | 9/16 | 0/8 | 680.48 | 31207 |
| lowbit-512 | 8/16 | 0/8 | 698.49 | 32033 |
| lowbit-768 | 9/16 | 0/8 | 697.47 | 31986 |
| lowbit-1024 | 9/16 | 0/8 | 683.98 | 31367 |

Prediction: 18.68 wall / 2.33 client CPU s; worker 20.36 wall / 2.45 client CPU s, client RSS 0.039 GiB. Warm rate 693.65 inputs/min; worker-inclusive 636.59. Separate server startup 13.02 s, download 44.70 s. Client initialization/RSS do not measure model load/memory.

One-second server sampling: 20.35 s request window, 19.01 s fully contained intervals observing 15.78 server-plus-child CPU s; sampled summed RSS peak 3.35 GiB. Boundary CPU is unmeasured and shared RSS pages may be counted twice. Device sampling 21/21, mean utilization 36.86%, peak 63,390 MiB including KV allocation; server PyTorch CUDA peaks are unmeasured.

**Qwen/Qwen3.5-0.8B**: known 72/144; ambiguous abstention 0/72 across repeated source pages. Release `2fc06364715b967f1860aea9cf38778875588b17`.

| Arm | Known / 16 | Abstain / 8 | Inputs/min | Est. warm inputs/USD |
|---|---:|---:|---:|---:|
| rgb-512 | 8/16 | 0/8 | 520.46 | 23868 |
| rgb-768 | 8/16 | 0/8 | 508.18 | 23305 |
| rgb-1024 | 8/16 | 0/8 | 504.25 | 23125 |
| gray-512 | 8/16 | 0/8 | 521.76 | 23928 |
| gray-768 | 8/16 | 0/8 | 498.71 | 22871 |
| gray-1024 | 8/16 | 0/8 | 497.54 | 22817 |
| lowbit-512 | 8/16 | 0/8 | 541.60 | 24838 |
| lowbit-768 | 8/16 | 0/8 | 533.56 | 24469 |
| lowbit-1024 | 8/16 | 0/8 | 493.36 | 22625 |

Prediction: 25.27 wall / 2.34 client CPU s; worker 29.44 wall / 2.47 client CPU s, client RSS 0.040 GiB. Warm rate 512.78 inputs/min; worker-inclusive 440.20. Separate server startup 28.04 s, download 7.59 s. Client initialization/RSS do not measure model load/memory.

One-second server sampling: 29.42 s request window, 28.02 s fully contained intervals observing 22.29 server-plus-child CPU s; sampled summed RSS peak 5.47 GiB. Boundary CPU is unmeasured and shared RSS pages may be counted twice. Device sampling 30/30, mean utilization 23.17%, peak 62,844 MiB including KV allocation; server PyTorch CUDA peaks are unmeasured.

**openbmb/MiniCPM-V-4**: known 104/144; ambiguous abstention 0/72 across repeated source pages. Release `6f69a8235885be89608f3a71ffd40695b379e1e7`.

| Arm | Known / 16 | Abstain / 8 | Inputs/min | Est. warm inputs/USD |
|---|---:|---:|---:|---:|
| rgb-512 | 11/16 | 0/8 | 516.79 | 23700 |
| rgb-768 | 11/16 | 0/8 | 480.45 | 22033 |
| rgb-1024 | 12/16 | 0/8 | 475.74 | 21817 |
| gray-512 | 11/16 | 0/8 | 530.63 | 24335 |
| gray-768 | 11/16 | 0/8 | 483.03 | 22152 |
| gray-1024 | 12/16 | 0/8 | 479.60 | 21994 |
| lowbit-512 | 11/16 | 0/8 | 526.24 | 24133 |
| lowbit-768 | 12/16 | 0/8 | 480.72 | 22046 |
| lowbit-1024 | 13/16 | 0/8 | 477.78 | 21911 |

Prediction: 26.25 wall / 2.33 client CPU s; worker 30.36 wall / 2.46 client CPU s, client RSS 0.039 GiB. Warm rate 493.64 inputs/min; worker-inclusive 426.87. Separate server startup 15.02 s, download 91.05 s. Client initialization/RSS do not measure model load/memory.

One-second server sampling: 30.34 s request window, 30.02 s fully contained intervals observing 23.54 server-plus-child CPU s; sampled summed RSS peak 3.87 GiB. Boundary CPU is unmeasured and shared RSS pages may be counted twice. Device sampling 31/31, mean utilization 52.65%, peak 61,710 MiB including KV allocation; server PyTorch CUDA peaks are unmeasured.

All use the recovered stock-vLLM GPU host and quoted $1.3083333333/h GPU-plus-disk allocation, serial BF16/eager requests with no prefix/image-processor cache. MiniCPM enables its pinned remote model code. Estimates exclude failed attempts, initialization, downloads, idle and cleanup; billed costs remain pending. No full-page extraction throughput is established.
