# R001: GPU concurrency on conditional DEV regions

Qwen3.5-9B shared-server throughput rose from **240.15 to 954.96 region inputs/min** at one versus eight client processes: a 3.98× increase over measured global wall time. Known-case score changed from **99/144 to 97/144**, so this run does not establish an unchanged-quality speedup. All four configurations completed 216/216 source-verified inputs without schema or worker failures; none abstained on the 72 repeated ambiguous controls.

Each configuration repeats the same 24 authored pages across nine RGB/gray/lowbit image arms: one supplied two-chunk region per page, 16 known references and eight ambiguous controls per arm. These are conditional grouping decisions of supplied regions and candidate boundaries, not full-page extraction. The 216 inputs and aggregate 144/72 reference denominators repeat those 24 pages; they are not independent 216-page samples.

Every source PDF, observation, request and PNG hash was verified before root-local DEV references were read. Requests and images were hardlinked into disjoint source shards without changing opaque IDs or bodies. No references went to GPU workers. Each configuration transmitted each input once; there were no automatic retries or replays. The source-scored parser accepts stock vLLM generated labels without inventing probabilities.

| Client processes | Valid / planned | Known correct / 144 | Ambiguous abstain / 72 | Same choice as N1 / 216 | Global wall s | Inputs/min over global wall | Concurrent request span s | Inputs/min over span | Est. warm inputs/USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 216/216 | 99/144 | 0/72 | 216/216 | 53.97 | 240.15 | 53.84 | 240.73 | 11040 |
| 2 | 216/216 | 98/144 | 0/72 | 215/216 | 34.96 | 370.75 | 34.77 | 372.77 | 17095 |
| 4 | 216/216 | 98/144 | 0/72 | 215/216 | 19.51 | 664.25 | 19.38 | 668.72 | 30667 |
| 8 | 216/216 | 97/144 | 0/72 | 214/216 | 13.57 | 954.96 | 13.43 | 964.89 | 44250 |

N1 agrees on all 216 choices with the earlier serial Qwen9 cohort in the [native comparison report](remote-gpu-r001.md). N2 and N4 each change one previously correct join to split in RGB768; N8 additionally changes one previously correct join in gray768. The cause has not been isolated. All other choices match N1.

Global wall includes client worker startup, request handling and concurrent-helper sampling/cleanup; the model server is already initialized. It is a cold-client measurement, not cold model provisioning. The concurrent request span runs from the first source-attempt start to the last completion and includes lane imbalance. Summed per-request latency is retained as work data and is never used as parallel throughput. The quoted USD 1.3083333333/hour GPU-plus-disk allocation gives the warm estimate `span inputs/min × 60 ÷ hourly USD`. That estimate excludes server startup, weight downloads, provisioning idle time and cleanup, and is not billed lifecycle cost or full PDF pages/USD.

| Arm | N1 known / 16; inputs/min | N2 known / 16; inputs/min | N4 known / 16; inputs/min | N8 known / 16; inputs/min |
|---|---:|---:|---:|---:|
| rgb-512 | 11/16; 228.31 | 11/16; 233.32 | 11/16; 696.32 | 11/16; 1048.29 |
| rgb-768 | 12/16; 243.33 | 11/16; 380.35 | 11/16; 611.46 | 11/16; 714.87 |
| rgb-1024 | 11/16; 237.11 | 11/16; 364.91 | 11/16; 527.94 | 11/16; 702.52 |
| gray-512 | 11/16; 248.66 | 11/16; 418.13 | 11/16; 713.44 | 11/16; 1082.30 |
| gray-768 | 11/16; 244.14 | 11/16; 411.10 | 11/16; 671.49 | 10/16; 987.81 |
| gray-1024 | 11/16; 234.98 | 11/16; 385.89 | 11/16; 613.86 | 11/16; 863.18 |
| lowbit-512 | 10/16; 248.13 | 10/16; 421.92 | 10/16; 713.08 | 10/16; 1022.58 |
| lowbit-768 | 11/16; 254.09 | 11/16; 414.24 | 11/16; 623.88 | 11/16; 857.29 |
| lowbit-1024 | 11/16; 236.12 | 11/16; 385.30 | 11/16; 614.54 | 11/16; 839.98 |

Every arm has 24/24 valid responses and 0/8 ambiguous abstentions. Arm rates use its own measured concurrent span; spans can overlap and cannot be added to recover global throughput. Fixed run order is N1 → N2 → N4 → N8, one run per configuration, without randomized repetitions.

| Client processes | Sampled observed union CPU s | Additive client-worker CPU s | Sampled simultaneous union peak RSS GiB | Device GPU samples available / total | Mean device utilization | Peak device VRAM MiB |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 51.02 | 2.47 | 5.53 | 54/54 | 78.41% | 63,060 |
| 2 | 36.24 | 2.62 | 5.82 | 35/35 | 77.03% | 63,060 |
| 4 | 22.44 | 2.66 | 5.87 | 20/20 | 85.05% | 63,060 |
| 8 | 16.58 | 2.74 | 6.18 | 14/14 | 84.71% | 63,060 |

One-second process sampling takes a de-duplicated union of supervisor descendants and the shared vLLM server tree. RSS is the simultaneous sampled sum, with shared pages potentially counted twice; child process high-water marks are not summed. Observed CPU excludes pre-observation counters and unsampled exit intervals, so it is a partial observation rather than a complete allocation CPU total. Client-worker CPU is a separate additive process total and excludes the external server. `nvidia-smi` utilization and memory describe the entire device at one-second intervals, including idle/client startup phases. Server PyTorch allocated/reserved peaks are unmeasured; the 63,060 MiB device peak includes its configured KV cache.

One RTX PRO 6000 Blackwell Workstation GPU (97,887 MiB) serves all clients on host 55085144, 24 effective CPU cores, driver 580.178.04. vLLM 0.31.0 uses Torch 2.13+cu130 and Transformers 5.17, BF16 eager inference, maximum model length 8,192, maximum concurrent sequences eight, GPU memory utilization 0.65, prefix caching disabled and image processor cache zero. The model is `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Client concurrency shares one model allocation; it does not load eight model copies.

Actual whole-wave billing remains pending. These small authored cases establish a measured serving tradeoff in this configuration; they do not establish natural-document quality, calibration, or end-to-end PDF throughput. Native Flash/Intern replica comparisons follow below; mixed-model GPU pairs are separate experiments.

Frozen L015 manifest SHA256: `0ddd6c3c02e86a3cd52280446d19112e20ede72dba709c26a1ae07c11d0b3104`. Source-index SHA256: `52e9c5241455cb7877cf0976b4fb4969735b5a0d7841972bfcbc6bee1ad0c0a1`. Source-only worker packet manifest SHA256: `e041da275ec775450373acc28380b1f04095a96affd0c9fa07fca1dc5828a7de`. Raw attempts, child statuses, source-scored evaluations and process/device samples stay ignored under `.scratch/remote-gpu-20261009/r001/` and `.scratch/council/lowlevel-inventor/`.

## Native model replicas

Independent native model replicas improve Intern throughput modestly and do not improve Flash throughput meaningfully on this small cohort. More device utilization alone is not a win: Flash uses four times the model memory for slightly lower global throughput at four replicas. These trials motivate the separate one-copy native batching test.

| Model | Replicas | Known / 144 | Ambiguous abstain / 72 | Same choice as N1 / 216 | Worker elapsed s | Inputs/min, elapsed | Inputs/min, request span | Estimated warm inputs/USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flash | 1 | 96/144 | 0/72 | 216/216 | 24.99 | 518.66 | 686.25 | 32294 |
| flash | 2 | 96/144 | 0/72 | 216/216 | 24.71 | 524.55 | 709.38 | 33382 |
| flash | 4 | 96/144 | 0/72 | 216/216 | 25.76 | 503.09 | 701.92 | 33032 |
| intern | 1 | 108/144 | 0/72 | 216/216 | 34.39 | 376.88 | 605.76 | 26433 |
| intern | 2 | 108/144 | 0/72 | 216/216 | 26.36 | 491.67 | 948.49 | 41389 |
| intern | 4 | 108/144 | 0/72 | 216/216 | 25.74 | 503.53 | 1040.41 | 45400 |
| intern | 8 | 108/144 | 0/72 | 216/216 | 27.78 | 466.55 | 1031.64 | 45017 |

All cohorts completed 216/216 valid inputs. Each replica independently loads the model, with OMP_NUM_THREADS=2. Flash uses its Torch 2.11 / Transformers 5.10.2 Max-Q host; Intern uses the Torch 2.14 / Transformers 5.17 stack on the PPLX Workstation host. The bounds reserve at most 84 GiB in aggregate using prior per-replica peaks of 20 GiB for Flash and 10 GiB for Intern. Fixed order is 1 → 2 → 4 replicas, then 8 for Intern, without randomized repeats.

Elapsed rates include model initialization in each fresh process. Request-span rates begin with the first attempt, after at least one replica has loaded, and include startup imbalance. Neither rate is an end-to-end PDF extraction claim. Warm inputs/USD uses the measured span and quoted allocation rates of USD 1.275/hour for Flash and USD 1.375/hour for Intern; provisioning, downloads, idle time and cleanup are excluded.

| Model | Replicas | Observed union CPU s | Simultaneous sampled peak RSS GiB | Mean device utilization | Peak device VRAM MiB |
|---|---:|---:|---:|---:|---:|
| flash | 1 | 23.92 | 13.59 | 55.36% | 19,184 |
| flash | 2 | 47.52 | 30.39 | 73.28% | 38,271 |
| flash | 4 | 95.29 | 35.59 | 78.08% | 76,614 |
| intern | 1 | 38.42 | 5.62 | 23.11% | 9,759 |
| intern | 2 | 53.40 | 9.50 | 40.85% | 19,568 |
| intern | 4 | 99.36 | 31.65 | 43.46% | 39,037 |
| intern | 8 | 206.75 | 50.80 | 48.54% | 77,986 |

CPU/RSS and device observations use the same one-second sampling and scope limitations as the shared-server table above. Replicated processes can count shared RSS pages more than once. This is measured concurrent process usage, not a sum of lifetime peaks.

| Arm | Flash N1 / N2 / N4, known each /16 | Intern N1 / N2 / N4 / N8, known each /16 |
|---|---:|---:|
| rgb-512 | 10 / 10 / 10 | 12 / 12 / 12 / 12 |
| gray-1024 | 11 / 11 / 11 | 12 / 12 / 12 / 12 |
| gray-512 | 10 / 10 / 10 | 12 / 12 / 12 / 12 |
| gray-768 | 11 / 11 / 11 | 12 / 12 / 12 / 12 |
| lowbit-1024 | 11 / 11 / 11 | 12 / 12 / 12 / 12 |
| lowbit-512 | 10 / 10 / 10 | 12 / 12 / 12 / 12 |
| lowbit-768 | 11 / 11 / 11 | 12 / 12 / 12 / 12 |
| rgb-1024 | 11 / 11 / 11 | 12 / 12 / 12 / 12 |
| rgb-768 | 11 / 11 / 11 | 12 / 12 / 12 / 12 |

Every arm remains 0/8 on ambiguous abstentions. Frozen source/packet verification precedes reference scoring. The complete evaluated records and per-arm concurrent timings are retained in `.scratch/remote-gpu-20261009/r001/native-concurrency-evaluation.json`; the retained scoring script is `score_native_concurrency.py` in that directory.
