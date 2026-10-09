# R001: native Clef true batching

Flash B2 delivers **844.58 region inputs/min**, about **8.1% above new-path B1**, while preserving all 216 source decisions. Its worker-inclusive rate improves only 0.9% (544.55 → 549.56 inputs/min). B4/B8/B16 are slower. Clef B2/B4 show small measured gains over B1 but change decisions; B8/B16 slow down and lose known-case accuracy. Clef timings overlap another environment bootstrap and are potentially contended.

This uses one model copy per invocation and the pinned publisher’s `encode_record`, `collate_records(records)` and joint-head forward. Source questions, option order and native response conversion remain unchanged. Complete inputs are preflighted at 16,384 tokens per record and a 65,536 padded-token batch admission; evidence is never truncated. Native usage reports actual per-record encoded length and the publisher’s zero generated tokens.

Each model/batch configuration completes all 216 source inputs: the same 24 authored pages repeated across nine image arms, one supplied two-chunk region per page. Every arm retains 16 known references and eight ambiguous controls. This is conditional grouping of supplied regions and candidate boundaries, not region detection or full-page extraction. Source PDF, observation, request and image hashes were verified before root-local DEV scoring. No scorer references went to the GPU host.

| Model | Batch size | Valid / planned | Known correct / 144 | Ambiguous abstain / 72 | Same choice as new B1 / 216 | Same choice as prior serial / 216 |
|---|---:|---:|---:|---:|---:|---:|
| Flash 9B | 1 | 216/216 | 96/144 | 0/72 | 216/216 | 216/216 |
| Flash 9B | 2 | 216/216 | 96/144 | 0/72 | 216/216 | 216/216 |
| Flash 9B | 4 | 216/216 | 96/144 | 0/72 | 216/216 | 216/216 |
| Flash 9B | 8 | 216/216 | 96/144 | 0/72 | 216/216 | 216/216 |
| Flash 9B | 16 | 216/216 | 96/144 | 0/72 | 216/216 | 216/216 |
| Clef 27B | 1 | 216/216 | 92/144 | 0/72 | 216/216 | 216/216 |
| Clef 27B | 2 | 216/216 | 92/144 | 0/72 | 214/216 | 214/216 |
| Clef 27B | 4 | 216/216 | 89/144 | 0/72 | 213/216 | 213/216 |
| Clef 27B | 8 | 216/216 | 89/144 | 0/72 | 212/216 | 212/216 |
| Clef 27B | 16 | 216/216 | 88/144 | 0/72 | 212/216 | 212/216 |

Both B1 runs reproduce every prior serial choice in the [native model report](remote-gpu-r001.md). Flash keeps exact choice parity at all batch sizes. Clef B2 preserves aggregate 92/144 known score but changes two decisions; larger sizes score 89/144, 89/144 and 88/144. No cause of the choice changes has been isolated. All ten configurations have zero schema/worker failures and zero ambiguous abstentions.

| Model | Batch size | Unique microbatches | Predict wall / CPU s | Warm region inputs/min | Est. warm inputs/USD | Worker wall / CPU s | Worker-inclusive inputs/min |
|---|---:|---:|---:|---:|---:|---:|---:|
| Flash 9B | 1 | 216 | 16.58 / 26.68 | 781.63 | 36782 | 23.80 / 32.75 | 544.55 |
| Flash 9B | 2 | 108 | 15.34 / 23.36 | 844.58 | 39745 | 23.58 / 29.37 | 549.56 |
| Flash 9B | 4 | 54 | 22.58 / 29.30 | 573.92 | 27008 | 29.58 / 35.13 | 438.11 |
| Flash 9B | 8 | 27 | 30.38 / 35.29 | 426.53 | 20072 | 37.02 / 41.21 | 350.11 |
| Flash 9B | 16 | 14 | 32.78 / 37.01 | 395.34 | 18604 | 39.09 / 42.90 | 331.58 |
| Clef 27B | 1 | 216 | 48.56 / 58.86 | 266.88 | 12559 | 61.42 / 67.42 | 211.00 |
| Clef 27B | 2 | 108 | 47.46 / 55.69 | 273.08 | 12851 | 57.95 / 64.13 | 223.64 |
| Clef 27B | 4 | 54 | 47.09 / 54.22 | 275.23 | 12952 | 56.79 / 62.97 | 228.20 |
| Clef 27B | 8 | 27 | 57.14 / 63.00 | 226.83 | 10674 | 66.16 / 71.53 | 195.88 |
| Clef 27B | 16 | 14 | 76.49 / 80.03 | 169.43 | 7973 | 86.00 / 89.26 | 150.70 |

Prediction time is measured once per unique microbatch and includes complete encoding, collation, forward and native response conversion. Individual case latency is unassigned; shared batch duration is never duplicated into individual timings or summed across responses. Worker wall includes one model load, source handling, durable output and device sampling, but excludes provisioning, download and idle time. B16 has thirteen full batches plus one eight-record tail; all other sizes divide 216 evenly.

The warm estimate is `inputs/min × 60 ÷ USD 1.275/hour` using the quoted GPU-plus-disk allocation. It excludes startup/download/idle/cleanup and is not observed billing or full PDF pages/USD. One tested supplied region comes from each authored page, so these are conditional page-region input equivalents. [Whole-wave provider charges and cleanup](remote-gpu-costs.md) are recorded separately.

New B1 differs from the prior serial path by reusing its complete preflight encoding directly; the older adapter encoded once for preflight and again inside publisher `systemone`. Therefore prior-serial → new B1 speed differences also include removal of duplicate encoding. B1 → B2/4/8/16 is the matched comparison within this worker. Only one ascending-size sweep per model is available, without randomized repetitions.

Flash’s five configurations completed before **21:28:57 UTC**. At that time a separate PPLX recovery bootstrap began on the same host, using CPU/network/disk in an isolated environment while Clef’s sweep continued. No other GPU inference ran during the sweep apart from a possible small BF16 bootstrap check. Clef measurements are potentially affected by this contention; they do not establish clean isolated gains or a causal batch-size ranking.

**Flash 9B known-case scores by arm**. Every cell is correct/16; all arms are valid24/24 and abstain0/8.

| Arm | B1 | B2 | B4 | B8 | B16 |
|---|---:|---:|---:|---:|---:|
| rgb-512 | 10/16 | 10/16 | 10/16 | 10/16 | 10/16 |
| rgb-768 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |
| rgb-1024 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |
| gray-512 | 10/16 | 10/16 | 10/16 | 10/16 | 10/16 |
| gray-768 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |
| gray-1024 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |
| lowbit-512 | 10/16 | 10/16 | 10/16 | 10/16 | 10/16 |
| lowbit-768 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |
| lowbit-1024 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |

**Clef 27B known-case scores by arm**. Every cell is correct/16; all arms are valid24/24 and abstain0/8.

| Arm | B1 | B2 | B4 | B8 | B16 |
|---|---:|---:|---:|---:|---:|
| rgb-512 | 9/16 | 9/16 | 9/16 | 9/16 | 9/16 |
| rgb-768 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |
| rgb-1024 | 12/16 | 12/16 | 11/16 | 11/16 | 11/16 |
| gray-512 | 9/16 | 10/16 | 9/16 | 9/16 | 9/16 |
| gray-768 | 11/16 | 11/16 | 11/16 | 11/16 | 11/16 |
| gray-1024 | 12/16 | 12/16 | 11/16 | 11/16 | 11/16 |
| lowbit-512 | 9/16 | 9/16 | 9/16 | 8/16 | 8/16 |
| lowbit-768 | 10/16 | 10/16 | 10/16 | 10/16 | 10/16 |
| lowbit-1024 | 9/16 | 8/16 | 8/16 | 9/16 | 8/16 |

Per-arm prediction rates are unassigned because some B16 batches contain inputs from two arms. Giving each arm the full shared duration or allocating it by case count would invent an individual timing attribution. Complete-cohort rates above use each actual microbatch once.

| Model | Batch size | Process peak RSS GiB | CUDA run peak allocated / reserved GiB | Device samples available / total | Mean device utilization | Peak device VRAM MiB |
|---|---:|---:|---:|---:|---:|---:|
| Flash 9B | 1 | 18.36 | 17.91 / 18.04 | 24/24 | 59.08% | 19,184 |
| Flash 9B | 2 | 18.36 | 18.08 / 18.43 | 24/24 | 59.42% | 19,576 |
| Flash 9B | 4 | 18.36 | 18.38 / 18.59 | 30/30 | 55.00% | 19,746 |
| Flash 9B | 8 | 18.35 | 18.97 / 19.39 | 37/37 | 57.81% | 20,566 |
| Flash 9B | 16 | 18.36 | 20.17 / 22.10 | 40/40 | 64.58% | 23,340 |
| Clef 27B | 1 | 51.79 | 51.41 / 51.60 | 62/62 | 74.82% | 53,544 |
| Clef 27B | 2 | 51.79 | 51.63 / 51.75 | 58/58 | 76.34% | 53,694 |
| Clef 27B | 4 | 51.79 | 52.05 / 52.36 | 57/57 | 84.00% | 54,324 |
| Clef 27B | 8 | 51.79 | 52.87 / 53.76 | 66/66 | 75.97% | 55,754 |
| Clef 27B | 16 | 51.78 | 54.53 / 57.18 | 86/86 | 74.90% | 59,879 |

CPU covers the single worker process and threads, excluding subprocess CPU. RSS uses Linux `resource.getrusage(RUSAGE_SELF).ru_maxrss`, a lifetime high-water mark; the separate bootstrap process is excluded. CUDA run peaks are the maximum over initialization and all unique batches, retained in worker status and `batches.jsonl`; generic per-record scorer peaks are not used. Device-wide `nvidia-smi` sampling is once per second over each worker invocation, including load/idle phases and any external device activity, not per-process utilization. More utilization does not imply more useful throughput here: Flash B16 has higher mean sampled utilization than B1 while producing fewer inputs/min.

All configurations report 151,614 actual input tokens over 216 records, unchanged across batch sizes and both models. Publisher collation pads each batch to its longest record: total logical sequence slots are 151,614 / 159,840 / 164,532 / 167,352 / 174,736 for B1/2/4/8/16, respectively (0%, 5.4%, 8.5%, 10.4%, 15.3% padding overhead). This is an exact collation count from recorded input lengths, not a hardware memory estimate or an established explanation for the observed slowdown.

Host 55084862: RTX PRO 6000 Blackwell Max-Q Workstation, 97,887 MiB GPU memory, 12 effective CPU cores, 128,783 MiB host RAM, driver 595.71.05. Native environment: Torch 2.11.0+cu130, Transformers 5.10.2, FLA 0.5.2; one model copy and one sequential microbatch stream, `OMP_NUM_THREADS=8`, `TOKENIZERS_PARALLELISM=false`. Flash revision `fde727a287004204b7518dcc983fe64379776712`; Clef revision `ed3eed331870db2eff4b0db01237128ede8a00ce`; publisher helper SHA256 `0e304cf7c6500e8bb59bef7e2afd2c6373f82596dfb3b57d1aa93c175e2dc3a3`.

The first control pilot used an older manifest lacking the required model field: all three attempts failed before GPU forward, with failures retained. Corrected batch controls returned all three circle/square/blank decisions correctly. Control attempts are excluded from all 216-input scores and rates. The executed adapter/worker prototype is bound by retained hashes: `remote_clef_batch.py` = `ec9892aa5c5dde26ee35ad2ed21a3891231e33a7105100830d5d2c4aa644104a`; `remote_batch.py` = `3e177d2b22ca8cc8460446dcbfc58e766e4995e10aa41f232a5ec3554b579b3b`. The subsequently committed tested version changes formatting/type annotations, not evidence or response semantics.

Frozen source manifest SHA256 `0ddd6c3c02e86a3cd52280446d19112e20ede72dba709c26a1ae07c11d0b3104`; source-index SHA256 `52e9c5241455cb7877cf0976b4fb4969735b5a0d7841972bfcbc6bee1ad0c0a1`. Requests, responses, unique-batch metrics, scorer outputs and samples remain ignored under `.scratch/remote-gpu-20261009/r001/` and `.scratch/council/lowlevel-inventor/`. No default extraction API uses this worker or the experimental decision models.

## Clef B1/B2 repeats after bootstrap

Two additional source-verified 216-input runs followed completion of the environment bootstrap and all other GPU inference. The original contended sweep above is retained separately. A small archive transfer overlapped the first model load only; no other GPU inference overlapped these repeats. Each uses a fresh worker, one model copy and the unchanged source requests, with a 100-second hard deadline.

| Repeat | Valid / planned | Known / 144 | Abstain / 72 | Same choice as corresponding first sweep / 216 | Same choice as prior serial / 216 |
|---|---:|---:|---:|---:|---:|
| B1 | 216/216 | 92/144 | 0/72 | 216/216 | 216/216 |
| B2 | 216/216 | 92/144 | 0/72 | 216/216 | 214/216 |

Both repeats reproduce every choice of their corresponding initial batch size, including B2’s two changed choices relative to serial/B1. Thus their nine-arm score tables above also remain unchanged. All four B1/B2 invocations score 92/144 known cases and 0/72 ambiguous abstentions, with no schema or worker failures.

| Repeat | Load wall / CPU s | Predict wall / CPU s | Warm inputs/min | Est. warm inputs/USD | Worker wall / CPU s | Worker-inclusive inputs/min |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 7.42 / 8.34 | 48.15 / 58.36 | 269.18 | 12667 | 60.97 / 66.95 | 212.56 |
| B2 | 7.28 / 8.22 | 46.76 / 54.67 | 277.18 | 13044 | 57.29 / 63.04 | 226.21 |

| Repeat | Process peak RSS GiB | CUDA run peak allocated / reserved GiB | Device samples available / total | Mean device utilization | Peak device VRAM MiB |
|---|---:|---:|---:|---:|---:|
| B1 | 51.79 | 51.41 / 51.60 | 61/61 | 75.80% | 53,544 |
| B2 | 51.79 | 51.63 / 52.13 | 58/58 | 80.62% | 54,092 |

Repeat warm rates rise from the initial 266.88/273.08 to 269.18/277.18 inputs/min for B1/B2 (about 0.9%/1.5%). Within the repeat, B2 is about 3.0% faster over unique batch prediction time and 6.4% faster over worker wall. These small one-repeat differences do not isolate a contention effect or establish a universal batch-size optimum. Input/response identity, sampling scope, padding, quote-based estimates and full-page limitations are the same as above. No timings are pooled across the original and repeat invocations; [whole-wave billed costs](remote-gpu-costs.md) are reported separately.
