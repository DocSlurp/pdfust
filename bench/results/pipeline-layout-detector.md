# P002 CPU layout detector source-only diagnostic

The persistent pinned YOLO26m DocLayNet worker completed all 16 natural DEV screen pages on 2026-10-09. It retained every predicted class and partitioned all 7,351 cached extraction/OCR source IDs exactly once. These are source-only coverage and resource observations; no annotation references were consulted or scored. Detector table boxes remain proposals, and provide no cell topology or semantic truth.

## Configuration and resource scope

One serial persistent worker, CPU FP32, four Torch intra-op threads reasserted after initialization and prediction, one inter-op thread, `CUDA_VISIBLE_DEVICES=""`, inference size 640, confidence threshold 0.25, batch 1. Full-page source rasters have maximum side 1,600 and at most four million pixels. This machine is an Intel Core i7-7700K at 4.20 GHz with eight available logical CPUs; other research activity may run concurrently, so these observations are not isolated throughput claims.

Pinned model revision: `49b97586dbd3bdae169e8f5e165710d0facf5f1e`; SHA-256 `ab0e6bd7fdf2c13404ef97e80c97fee4e8c436620fc5fdcfbe866ec662312971`. Worker versions: Python 3.12.15, Torch 2.11.0+cu128, Ultralytics 8.4.174. The worker reports CPU execution and no local GPU usage. The checkpoint is retained as an opt-in experimental AGPL-3.0 model dependency, outside library defaults. No installation, network inference, or paid inference was used.

| Scope | Wall seconds | CPU seconds | RSS |
| --- | ---: | ---: | --- |
| Worker initialization, including warmup | 2.800 | 5.562 | 1,052,241,920 bytes sampled peak |
| Worker inference, 16 serial frames | 4.436 | 15.478 | 1,162,461,184 bytes maximum sampled per-call peak |
| Parent rendering, reading cached sources, partitioning, IPC, initialization and output | 9.255 | 1.824 | 367,256 KiB parent lifetime peak |

Worker CPU uses process_time; own-process RSS uses /proc/self/statm sampled every 100 ms plus call endpoints. Lifetime peak RSS uses getrusage separately. Parent CPU excludes worker CPU; parent wall includes worker waits. Parent RSS was not sampled. Peaks must not be summed. Cached-source timings omit the original OCR/extraction work and are not complete-pipeline latency.

## Complete source coverage

The 333 complete class predictions comprised 150 Text, 40 List-item, 38 Section-header, 23 Picture, 21 Table, 17 Page-header, nine Caption, seven Page-footer, six Formula and two Title boxes. The 21 table proposals occurred on 15 pages. All contained cached words, and no word center was contested by overlapping table proposals. There were no native vector grids in these image carriers.

Partitioning produced 23 detector regions and 48 residual regions. Detector regions owned 1,397 source IDs and residual regions owned 5,954 IDs. Four detector regions were capacity fragments from one dense page; each explicitly retains incomplete context and cannot claim complete-table topology. The page with no detected table retained all 489 words as residual source. The separate native-extraction-only pass also completed 16/16 but had zero source words: these inputs are lossless image PDF carriers.

| Page ID | Cached words | All boxes | Table proposals | Detector-owned words | Residual words |
| --- | ---: | ---: | ---: | ---: | ---: |
| p1bfa52a41a5e15015698 | 1942 | 42 | 2 | 127 | 1815 |
| p6ef5d3c5c2edb1c109c4 | 532 | 27 | 2 | 209 | 323 |
| p391ea102f48e27fcdd65 | 62 | 16 | 2 | 39 | 23 |
| p9f92a30432da612d1bcc | 144 | 44 | 2 | 22 | 122 |
| p656361df32bd7d69a39e | 77 | 5 | 2 | 69 | 8 |
| p98d10ef50dee4b24506a | 1645 | 28 | 2 | 558 | 1087 |
| pc848c2a56527f81021a7 | 662 | 13 | 1 | 92 | 570 |
| pc9c4bcc7f4f2a5dc3bab | 583 | 15 | 1 | 70 | 513 |
| p1e230b0fd05df7dd5e23 | 249 | 29 | 1 | 4 | 245 |
| pda95432063a8a20bbe01 | 55 | 5 | 1 | 39 | 16 |
| pe87ca2d41151f28dc44c | 346 | 9 | 1 | 81 | 265 |
| pf012d6adb9592dab9a13 | 43 | 32 | 1 | 6 | 37 |
| p27ec5aaca0dd08c90360 | 9 | 2 | 1 | 8 | 1 |
| p9cc5ebfad2ee46a13b5e | 166 | 12 | 1 | 47 | 119 |
| pdb4e1fa3babeca265abb | 347 | 13 | 1 | 26 | 321 |
| p42049db34e230ce77d75 | 489 | 21 | 0 | 0 | 489 |

## Reproduction and admission

Run `python -m bench.pipeline_layout_detector --manifest <natural16 manifest> --sources-directory <natural16-generate-sonnet directory> --output <new output directory>`. Retained raw artifacts are in ignored `bench/results/pdf-master-artifacts/pipeline-p002/detector-natural16-cached-v2/`; the earlier cached run had an incorrect diagnostic native-region counter, fixed before this run. Frozen manifest and source-PDF hashes are retained. Cached result files supply only the source snapshot; model prompts or responses are not forwarded to the detector.

Frames are bounded at four million decoded pixels and eight MiB serialized JSON lines. Responses are bounded at one MiB and 1,024 boxes, with finite positive geometry and confidence checks. A failed response refuses the complete call and closes/reaps the worker. Native grids retain priority; table proposals compete by confidence, smaller area, then deterministic input order; remaining source goes through geometric/residual splitting. Capacity chunks explicitly abstain on complete context.

Validation: nine adapter/partition tests and twelve existing region tests pass; Ruff lint and format checks pass. Tests cover persistent lifecycle, timeout/reaping, frame and geometry rejection, overlapping proposal ownership, residual conservation, capacity abstention, low-confidence proposals, duplicate source IDs, and native-grid priority.
