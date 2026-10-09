# YOLO26m matched CPU/GPU DEV comparison

Fixed pixel-only inputs: 125 synthetic silver DEV pages and 16 frozen OmniDocBench DEV images. The model receives image paths only; labels are loaded exclusively for this report. No training or hosted inference occurred. Public benchmark contamination is unknown.

| Arm | Median 141-page pass | Pages/s | CPU user+system/pass | Cold load | First-predict warmup | Lifetime RSS | CUDA allocated / reserved |
|---|---|---|---|---|---|---|---|
| cpu-fp32 | 40.105s | 3.52 | 153.437s | 0.077s | 1.343s | 1472.8 MiB | n/a |
| gpu-fp32 | 4.030s | 34.99 | 4.013s | 0.081s | 1.508s | 1957.3 MiB | 174.9 / 190.0 MiB |
| gpu-fp16 | 4.193s | 33.63 | 4.175s | 0.077s | 3.417s | 2492.9 MiB | 109.5 / 120.0 MiB |

cpu-fp32 full-pass times: 44.917s, 40.105s, 38.191s. Single-page warmup does not warm all page shapes.

gpu-fp32 full-pass times: 4.324s, 3.955s, 4.030s. Single-page warmup does not warm all page shapes.

gpu-fp16 full-pass times: 13.382s, 4.142s, 4.193s. Single-page warmup does not warm all page shapes.

| Arm | Cohort | TP | FN | FP | TN |
|---|---|---|---|---|---|
| cpu-fp32 | silver-dev | 0 | 10 | 5 | 110 |
| cpu-fp32 | omnidoc-dev | 4 | 0 | 3 | 9 |
| gpu-fp32 | silver-dev | 0 | 10 | 5 | 110 |
| gpu-fp32 | omnidoc-dev | 4 | 0 | 3 | 9 |
| gpu-fp16 | silver-dev | 0 | 10 | 5 | 110 |
| gpu-fp16 | omnidoc-dev | 4 | 0 | 3 | 9 |

| Compared with CPU FP32 | Bit-exact pages | Equal ordered class/count | Within 0.1px / 0.001 confidence | Max box delta* | Max confidence delta* |
|---|---|---|---|---|---|
| gpu-fp32 | 47/141 | 141/141 | 141/141 | 0.001465px | 0.000004 |
| gpu-fp16 | 47/141 | 139/141 | 47/141 | 14.463867px | 0.054745 |

GPU FP32 steady-pass speedup: **9.95×**. *Numeric maxima compare only pages with equal ordered class/count. Same-class detections use greedy nearest-box matching; this is not an optimal assignment. Presence accuracy does not establish table structure, OCR, reading order, or full-record quality.

Silver labels cover authored bordered-table presence (correlated templates, not adjudicated gold); OmniDocBench labels cover any annotated table in page images. These are distinct tasks and are not pooled.

cpu-fp32 nvidia-smi host-wide samples (0.5s target interval plus query overhead, whole worker including load/warmup): 237 observations, mean utilization 0.0%, max memory 431 MiB, mean power 11.3 W. Includes desktop/other processes; not per-model attribution.

gpu-fp32 nvidia-smi host-wide samples (0.5s target interval plus query overhead, whole worker including load/warmup): 31 observations, mean utilization 20.5%, max memory 964 MiB, mean power 121.8 W. Includes desktop/other processes; not per-model attribution.

gpu-fp16 nvidia-smi host-wide samples (0.5s target interval plus query overhead, whole worker including load/warmup): 53 observations, mean utilization 5.7%, max memory 902 MiB, mean power 114.1 W. Includes desktop/other processes; not per-model attribution.

Preparation: 2.964s wall, 3.085s lifetime CPU, 100.2 MiB lifetime RSS; sequential native rendering at 120 DPI. Original OmniDocBench images are unchanged. Preprocessing is measured separately from model passes.

Configuration: image size 640, batch size 1, confidence threshold 0.25, minimum-rectangle padding, TF32 disabled, CPU 4 threads + interop 1; three sequential passes per arm. Torch `2.11.0+cu128`, Ultralytics `8.4.174`; machine `Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44`, 8 logical CPUs. Cold model load follows imports and input hash verification; first prediction separately includes device transfer and predictor initialization. Complete process startup timings remain in telemetry artifacts. RSS is process-lifetime getrusage SELF with no sampling; pass CPU is SELF user/system deltas. CUDA allocator peaks include warmup; nvidia-smi memory is a separate host-wide measure. Four CPU threads are reasserted after predictor initialization, which otherwise resets them.

[Pinned model card](https://huggingface.co/hantian/yolo-doclaynet/blob/49b97586dbd3bdae169e8f5e165710d0facf5f1e/README.md): AGPL-3.0, model SHA256 `ab0e6bd7fdf2c13404ef97e80c97fee4e8c436620fc5fdcfbe866ec662312971`. [Ultralytics prediction settings](https://docs.ultralytics.com/modes/predict/) define the explicit FP32/FP16 quantize arms. OmniDocBench retains its noncommercial research restriction. No model weights, raw page images, labels, predictions, or telemetry are committed.

Reproduce after input preparation with the cached model environment: `.venv/bin/python -m bench.gpu_comparison --prepare`, then `.venv/bin/python -m bench.gpu_comparison --run --device cpu` and `--run --device 0` sequentially; optional `--run --device 0 --half` is a distinct FP16 arm. Finish with `--report`. Retained artifacts are under ignored `gpu-comparison/`.


GPU FP32 is the useful acceleration arm on this cohort. FP16 changes detection topology on two pages and lacks a median speed advantage. Both arms retain the same presence decisions, including all ten silver misses; the layout detector cannot replace native bordered-table extraction here. Initial overlapping timing runs and the initial auto-reset CPU-thread arm are retained separately and excluded from this matched summary. No nvidia-smi/worker errors or kernel NVRM Xid events were observed during the bounded comparison.
