# Intern runtime isolation on authored PDF DEV inputs

The original host runs the native fast stack about **57.1× faster** than its old-FLA stack over the same216 region inputs, with identical216 categorical decisions. Every runtime still gives a decisive answer on all72 ambiguous inputs. Faster execution does not establish reliable evidence sufficiency.

CPU-only local verification used `bench.remote_report.evaluate` against frozen L015 source bodies/PDFs/observations, original source index and staged request/image hashes, before local DEV references. Each complete cohort has216 conditions:24 authored sources ×RGB/gray/lowbit ×512/768/1024;144 known and72 ambiguous. These repeated renderings are not216 independent cases. Engine is `internlm/Intern-Decision-4B`; the unchanged transport-model field does not identify the loaded engine.

| Runtime/output directory | Valid | Known correct/144 | Wrong known | Known abstentions | Ambiguous abstentions/72 | Summed inference s | Inference CPU s | Inputs/min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| intern-l015 | 216/216 | 108 | 36 | 0 | 0 | 945.584 | 967.717 | 13.7 |
| intern-new-runtime-l015 | 216/216 | 108 | 36 | 0 | 0 | 19.684 | 41.595 | 658.4 |
| intern-fast-host-l015 | 216/216 | 107 | 36 | 1 | 0 | 16.651 | 33.932 | 778.3 |
| intern-fla-l015 | 216/216 | 107 | 36 | 1 | 0 | 951.607 | 968.865 | 13.6 |
| intern-causal-l015 | 216/216 | 108 | 36 | 0 | 0 | 892.531 | 913.884 | 14.5 |
| TF combined | 216/216 | 108 | 36 | 0 | 0 | 905.073 | 924.451 | 14.3 |

Fast original-host and old-FLA cohorts agree on every choice: each scores12/16 known in eight arms and11/16 in lowbit768, where it abstains once. Original old stack, separate-host new runtime, causal ablation and Transformers-only upgrade score12/16 in all nine arms. Their single changed category relative to the fast original-host cohort removes that known abstention. Probabilities are uncalibrated; matching categorical outputs do not prove numerical equivalence. Causal attention changes the intended native attention contract and remains an architecture ablation, despite the similar score.

| Runtime | Initialization wall/CPU s | Worker wall/CPU s | Peak RSS GiB | CUDA allocated/reserved GiB |
|---|---:|---:|---:|---:|
| intern-l015 | 6.500/7.262 | 954.747/975.299 | 8.836 | 8.719/8.961 |
| intern-new-runtime-l015 | 11.146/12.036 | 31.468/54.011 | 8.868 | 8.681/8.857 |
| intern-fast-host-l015 | 8.864/9.645 | 26.646/43.848 | 8.874 | 8.681/8.857 |
| intern-fla-l015 | 8.683/9.238 | 963.148/978.423 | 8.907 | 8.659/9.152 |
| intern-causal-l015 | 8.380/9.137 | 903.779/923.329 | 8.880 | 8.659/8.836 |
| intern-tf517-continuation | 8.334/9.100 | 26.527/27.562 | 8.864 | 8.659/8.768 |

The Transformers-only run retains two phases. Phase1 reached its900s hard deadline:211 completed, one started-but-uncompleted ID `p0211`, supervisor wall900.390s; completed inference886.915s/CPU905.998s, initialization8.240s/CPU8.953s. Phase2 completed the five missing successful IDs `p0211`–`p0215`, with inference18.158s/CPU18.453s and a separate26.527s worker lifecycle. Its five successful IDs are disjoint from phase1’s211 successes; both phase outputs independently pass original source/hash verification. The original interrupted start remains retained. The combined905.073s inference sum excludes time spent in that interrupted attempt, so it is not total execution cost. Phase1 final worker CPU/RSS is unavailable; completed-attempt peaks remain in retained JSON. Two starts/initializations and separate lifecycles must not be collapsed into a single uninterrupted benchmark.

Retained environment snapshots report old Torch2.9.1+cu128/Transformers5.14.1 and fast Torch2.14.0+cu130/Transformers5.17.0. The directory name `tf517` is not evidence of5.17.2: its frozen environment also says5.17.0. Torch, CUDA, torchvision and Transformers change together in the fast stack. The same-host comparison reduces hardware confounding, while the slow Transformers-only cohort indicates that this upgrade alone did not reproduce the fast stack. It does not identify a single causal dependency.

Instrumented warm single-call cProfile diagnostics: old2.029316s wall/2.073812s CPU; new0.091973s wall/0.135126s CPU. Old `torch.conv3d` accounts for1.931s, about95% of old wall time. Disabling cuDNN on the old stack gives1.966680s wall/2.010555s CPU, with `torch.conv3d`1.871s; this one diagnostic does not show a useful order-of-magnitude improvement. These Python call profiles identify a bottleneck location, not a GPU kernel trace or a controlled single-dependency causal result. Each follows one warm prediction, uses OMP8, and is not a cohort throughput or quality test.

Inference includes native preprocessing plus prediction; serial summed durations support inputs/min, not full PDF pages/min. CPU covers the worker process/threads; RSS is Linux `getrusage(RUSAGE_SELF).ru_maxrss` lifetime high water including loading. CUDA values are allocator peaks, not total device memory. Device-wide GPU samples are nominally1s and separate from allocator counters. No exact lifecycle billing allocation was supplied for this isolation comparison; cost remains unmeasured.

Local verification/scoring: wall1.371s, CPU1.313s, peak RSS41.3MiB, one CPU process. Retained evaluation: `.scratch/council/lowlevel-eval/intern-runtime-evaluation.json`; reproducible scorer driver: `.scratch/council/lowlevel-eval/intern_runtime_score.py` via root Python/runpy. Runtime outputs: `.scratch/remote-gpu-20261009/r001/results/outputs/`; profiler and frozen environment snapshots: `results/final-host-55084071/outputs/`. No inference was run during this analysis.
