# R001: native GPU decision models on L015 DEV regions

Cloudflare Clef-Flash 9B and Perplexity Decider v1.1 27B completed all 216 inputs each without schema or worker failures. Intern-Decision-4B is a partial checkpoint: 44 valid results and one active request. Flash is faster in this run; the different hosts, runtimes and kernels prevent attributing the difference to model size alone. Rental billing remains pending.

Each arm contains the same 24 authored source pages with one supplied two-chunk region per page: 16 known references and eight ambiguous controls. Nine image arms repeat those pages; 216 inputs are not 216 independent pages or complete-page extractions. This is conditional grouping with supplied targets, not region detection. The three transport/vision controls are separate and excluded from every cohort denominator below.

All 216 staged request bodies and PNGs were checked against frozen L015 hashes, alongside source PDF and observation hashes, before DEV references were read locally. Native distributions use the existing scorer and tied maxima abstain. The unchanged PPLX transport model field does not identify the Flash engine: its deployed release is the pinned native Clef-Flash 9B. No scorer references were staged remotely.

Known/ambiguous cells below show known-correct/16 and ambiguous-abstain/8. Hosted columns use the [completed same-source L015 run](lowlevel-images-large.md). Every Flash/PPLX arm has 24/24 valid responses. Intern gray1024 has 20/24 valid responses, covering 14 known and six ambiguous cases; its displayed 16/8 denominators remain planned, with four cases pending/unattempted. Other Intern arms are unattempted.

| Arm | Flash native known; abstain | Flash hosted known; abstain | PPLX native known; abstain | PPLX hosted known; abstain | Intern valid; known; abstain |
|---|---:|---:|---:|---:|---:|
| rgb-512 | 10/16; 0/8 | 9/16; 0/8 | 9/16; 0/8 | 12/16; 0/8 | 24/24; 12/16; 0/8 |
| rgb-768 | 11/16; 0/8 | 11/16; 0/8 | 12/16; 0/8 | 12/16; 0/8 | 0/24; unattempted |
| rgb-1024 | 11/16; 0/8 | 10/16; 0/8 | 12/16; 0/8 | 13/16; 0/8 | 0/24; unattempted |
| gray-512 | 10/16; 0/8 | 9/16; 0/8 | 9/16; 0/8 | 12/16; 0/8 | 0/24; unattempted |
| gray-768 | 11/16; 0/8 | 11/16; 0/8 | 12/16; 0/8 | 12/16; 0/8 | 0/24; unattempted |
| gray-1024 | 11/16; 0/8 | 10/16; 0/8 | 12/16; 0/8 | 12/16; 0/8 | 20/24; 11/16; 0/8 |
| lowbit-512 | 10/16; 0/8 | 8/16; 0/8 | 10/16; 0/8 | 12/16; 0/8 | 0/24; unattempted |
| lowbit-768 | 11/16; 0/8 | 11/16; 0/8 | 11/16; 0/8 | 12/16; 0/8 | 0/24; unattempted |
| lowbit-1024 | 11/16; 0/8 | 10/16; 0/8 | 12/16; 0/8 | 12/16; 0/8 | 0/24; unattempted |

Native Flash agrees with the hosted choice on 209/216 inputs; native PPLX agrees on 204/216. PPLX RGB512 drops from hosted 12/16 to native 9/16, while 768 matches 12/16 and 1024 changes 13/16 to 12/16. These are not exact reproductions of hosted decisions. Backend arithmetic, prompt assembly and image preprocessing remain separate variables; no explanation has been established. The local PPLX processor uses its reference 65,536–4,194,304-pixel bounds, rather than assuming the hosted image path is identical.

Rates are fresh region inputs/minute over cumulative measured adapter `predict` wall time, including native preprocessing. These calls all yielded valid decisions; no aliases/replays are included. A pending attempt invalidates the complete rate for its arm. Full-page pages/minute and pages/USD are unavailable.

| Arm | Flash inputs/min | PPLX inputs/min | Intern inputs/min |
|---|---:|---:|---:|
| rgb-512 | 672.63 | 250.41 | 25.21 |
| rgb-768 | 763.43 | 309.39 | unmeasured |
| rgb-1024 | 662.25 | 258.01 | unmeasured |
| gray-512 | 912.70 | 349.73 | unmeasured |
| gray-768 | 786.13 | 316.10 | unmeasured |
| gray-1024 | 680.62 | 266.06 | unmeasured |
| lowbit-512 | 901.31 | 343.57 | unmeasured |
| lowbit-768 | 779.13 | 311.81 | unmeasured |
| lowbit-1024 | 674.84 | 262.75 | unmeasured |

| Worker scope | Load wall / CPU s | Predict wall / CPU s | Worker wall / CPU s | Warm inputs/min | Worker inputs/min | Process peak RSS GiB | CUDA peak allocated / reserved GiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Flash, 216 inputs | 5.12 / 5.97 | 17.31 / 30.82 | 24.20 / 36.97 | 748.85 | 535.49 | 18.36 | 17.91 / 18.04 |
| PPLX, 216 inputs | 18.57 / 19.60 | 44.36 / 66.10 | 63.56 / 86.09 | 292.15 | 203.91 | 5.94 | 48.83 / 49.01 |
| Intern, completed RGB512 slice (24 inputs) | 6.50 / 7.26 | 57.11 / 59.28 | unmeasured | 25.21 | unmeasured | 8.84 | 8.72 / 8.84 |

Worker-inclusive rates include model load, input handling and logging, but exclude paid bootstrap, weight download, provisioning idle time and cleanup. They are not full rental-lifecycle rates. Initialization for Intern is the single model load, shown alongside its completed RGB512 slice; its full worker run remains unfinished.

Process CPU covers worker threads and excludes subprocesses; it may exceed elapsed wall time. RSS uses Linux `resource.getrusage(RUSAGE_SELF).ru_maxrss`, a process-lifetime high-water mark. CUDA allocation/reservation peaks use the current-device PyTorch counters. Device-wide `nvidia-smi` utilization/VRAM sampling ran once per second: Flash 25/25 samples available, mean utilization 61.4%, peak device VRAM 19,184 MiB; PPLX 64/64, 58.42%, 50,879 MiB; Intern checkpoint 203/203, 23.70%, 9,874 MiB. Sample means include load/idle phases and are not per-worker utilization claims.

All hosts ran one worker, serial singleton requests, `OMP_NUM_THREADS=8` and `TOKENIZERS_PARALLELISM=false`, with no GPU request concurrency. Flash used RTX PRO 6000 Blackwell Max-Q, 97,887 MiB GPU memory, 12 effective CPU cores, 128,783 MiB host RAM, driver 595.71.05, Torch 2.11.0+cu130, Transformers 5.10.2 and FLA 0.5.2. PPLX used RTX PRO 6000 Blackwell Workstation, 97,887 MiB GPU memory, 32 effective CPU cores, 1,031,870 MiB host RAM, driver 590.48.01, Torch 2.14+cu130, Transformers 5.17 and FLA. Intern used RTX PRO 6000 Blackwell Workstation, 97,887 MiB GPU memory, 24 effective CPU cores, 128,792 MiB host RAM, driver 595.91.07, Torch 2.9.1+cu128 and Transformers 5.14.1 without FLA. Hosts/kernel paths differ; installed dependency freezes are retained with the returned artifacts.

Actual whole-wave rental charges and region inputs/USD remain pending. Provider inventory hourly quotes include the 150 GB disk allocation; they are not observed invoice charges. No zero-cost assumption or warm-only rental estimate is reported.

Pinned releases: Flash `fde727a287004204b7518dcc983fe64379776712`; PPLX `6195aa55a72ae21e503c8a60198f7b390d42adb5`; Intern `0e5e6aa7d6d750e2b1504ba11a8136cb58aeb3cd`. See the [self-hosted model notes](../HF_DECISION_MODELS.md). Requests, responses, local scorer results, samples and source-index remain ignored under `.scratch/remote-gpu-20261009/r001/` and `.scratch/council/lowlevel-inventor/`.

Frozen L015 manifest SHA256: `0ddd6c3c02e86a3cd52280446d19112e20ede72dba709c26a1ae07c11d0b3104`. Source-index SHA256: `52e9c5241455cb7877cf0976b4fb4969735b5a0d7841972bfcbc6bee1ad0c0a1`. This is a single run/checkpoint, with small authored and correlated cases; no universal quality or deployment-cost ranking is established.
