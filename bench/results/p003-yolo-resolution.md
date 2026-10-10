# P003 matched CPU YOLO resolution experiment

All 16 retained ordinal DEV pages completed three source-only detector arms on 2026-10-10. The same cached full-page RGB PNG bytes were used at `imgsz=640`, `1024`, and `1280`. There were 48 completed predictions and no failed or retried arms. No references, fresh confirmation pages, hosted inference, credentials, downloads, or GPU inference were accessed.

Increasing model resolution changed acquisition substantially: the dense `p1bfa` page went from zero table proposals to four and sixteen. Several other pages lost proposals. Proposal counts and source coverage do not establish table correctness, completeness, or downstream cell quality; independent evaluation must precede a winner selection.

| Model size | All returned boxes | Table boxes | Source-word centers inside table-box union | Worker wall s | Worker CPU s | Maximum sampled worker RSS bytes |
|---|---:|---:|---:|---:|---:|---:|
| 640 | 296 | 19 | 2,205 | 5.716 | 11.133 | 1,404,334,080 |
| 1024 | 370 | 24 | 3,218 | 13.727 | 26.969 | 1,464,508,416 |
| 1280 | 457 | 37 | 3,268 | 21.284 | 41.892 | 1,589,166,080 |

The coverage denominator is all 10,778 retained source words, including prose, negatives, duplicated literal strings with distinct IDs, and OCR/extraction defects. Each source ID is counted once if its bbox center lies inside any returned table bbox, using inclusive boundaries. The union is solely a diagnostic membership calculation: raw proposals remain separate and overlapping proposals are not merged into new crops. These counts neither identify reference table words nor score availability of correct cell text.

| Page | 640 table boxes | 1024 | 1280 |
|---|---:|---:|---:|
| p42049db34e230ce77d75 | 0 | 0 | 0 |
| pc9c4bcc7f4f2a5dc3bab | 1 | 1 | 1 |
| pdb4e1fa3babeca265abb | 1 | 0 | 0 |
| p9cc5ebfad2ee46a13b5e | 1 | 0 | 0 |
| p6ef5d3c5c2edb1c109c4 | 2 | 2 | 2 |
| p1e230b0fd05df7dd5e23 | 1 | 1 | 1 |
| p391ea102f48e27fcdd65 | 2 | 2 | 2 |
| pda95432063a8a20bbe01 | 1 | 0 | 0 |
| pc848c2a56527f81021a7 | 1 | 1 | 1 |
| p98d10ef50dee4b24506a | 2 | 5 | 8 |
| p656361df32bd7d69a39e | 2 | 2 | 2 |
| p1bfa52a41a5e15015698 | 0 | 4 | 16 |
| p27ec5aaca0dd08c90360 | 1 | 1 | 0 |
| pe87ca2d41151f28dc44c | 1 | 1 | 1 |
| p9f92a30432da612d1bcc | 2 | 3 | 2 |
| pf012d6adb9592dab9a13 | 1 | 1 | 1 |

The existing [tiling diagnostic](pipeline-layout-tiles.md) remains a separate experiment: it used a 3,072-side source raster, 1,024-side whole frame, 12% overlapping 2×2/3×3 tiles, fixed model size 640, four intra-op threads, and 224 retained calls. None of its calls were repeated here. This experiment isolates resolution within a new matched two-thread, whole-page source-pixel pass; its 640 arm is the control for these specific inputs/settings, not a timing replica of that historical tiling pass.

The checkpoint is the existing local `hantian/yolo-doclaynet` YOLO26m at revision `49b97586dbd3bdae169e8f5e165710d0facf5f1e`, 44,145,625 bytes, SHA-256 `ab0e6bd7fdf2c13404ef97e80c97fee4e8c436620fc5fdcfbe866ec662312971`, with retained AGPL-3.0 provenance. The pinned existing environment `/home/dan/.cache/pylopdf-structure-bench/bin/python` reported Python 3.12.15, Torch 2.11.0+cu128, Ultralytics 8.4.174, and Pillow 12.3.0. Torch is a CUDA-capable build; CUDA visibility was disabled, every prediction explicitly used `cpu`, and model parameters were checked on CPU. GPU availability was not queried.

Settings are confidence 0.25, batch 1, maximum 1025 output boxes with complete-output refusal above 1024, and requested FP32 quantization. Effective predictor arguments are retained for every call: quantize 32, IoU 0.7, class-aware NMS (`agnostic_nms=False`), `rect=True`, no augmentation, and `half=None`. Only `imgsz` varies across arms. Full returned class IDs, labels, confidences and pixel boxes are archived, together with exact display-space boxes. These are complete YOLO confidence-filtered, post-NMS detections, not pre-NMS logits; this experiment performs no extra NMS. Invalid geometry is refused rather than clipped or repaired.

A root-supplied independent `b773d57.json` code map authenticated the complete ordinal source baseline. Each PDF was hash checked; rendered page rect had to equal retained `source.page_size`, and original/effective rotation had to agree with the actual PDF. All pages had rotation 0. No rotation normalization was applied. Rendering requested maximum edge 1536 against the original display viewport, with white background and lossless RGB PNG compression6. One raster has actual maximum edge 1535 from renderer rounding; the other 15 have maximum1536. Actual dimensions and viewport are preserved and used in pixel-to-display mapping. Each image is below 4M pixels; the 16 images total 26,476,474 pixels and 12,037,648 encoded bytes. Source snapshots, model identity, both new code files and all 16 inputs were frozen before the first inference.

One serialized owned worker used two Torch intra-op threads and one inter-op thread. The Ultralytics CPU thread constant was also set to 2 to prevent its device-selection setup from resetting the requested bound. Bounds were verified after all three warmups and every prediction. Initialization includes imports, model load, predictor setup, and separately retained white-image warmups at all three sizes. It took 7.493 wall s / 12.001 CPU s with sampled peak RSS1,427,607,552 bytes. Parent authentication/render/encoding preparation took 4.720 wall s / 4.700 CPU s and 539,156 KiB lifetime peak RSS. Import overhead is excluded from the parent timer but included in its lifetime RSS.

Worker CPU is `process_time`; own-process RSS uses `/proc/self/statm` every 100 ms plus scope endpoints, with `getrusage` lifetime peak additionally retained. Parent preprocessing and worker initialization/predictions are separate scopes; their memory peaks must not be summed. Input decoding, hash checks, model execution, projection, and sampler closure are included in each call's worker metrics. Artifact JSON writing is outside those call scopes. Parent waiting/IPC and subsequent validation are not included in prediction sums. Prediction order was frozen page order, then 640/1024/1280, sharing a warmed model; other campaign work could contend, so timings are descriptive rather than uncontended capacity estimates.

The final ignored archive is `bench/results/pdf-master-artifacts/pipeline-p003/yolo-resolution-v1` in the main workspace. It contains 87 files totaling 15,619,002 bytes. All 48 output hashes, complete raw-box projections and thread bounds were independently rechecked locally after the freeze. Eight focused tests verify identical non-resolution settings, offset viewport mapping with all classes retained, refusal of nonfinite/bool/out-of-frame outputs, and complete box/pixel caps. Ruff and mypy checks of both new modules passed.

| Receipt | SHA-256 |
|---|---|
| `frozen.json` | `9a369b3971e628f4aa202a5de5fd3b35e914ba150c02fc560ace6fe08f323619` |
| `report.json` | `2707346213d06b49e07155bc0cb9035d65b4a65de86a828da7e610429029e1e8` |
| Canonical sorted file inventory | `5d9dd9619185506860a53ec9e20ea8ff3ba6dbb8140b85323fdb4f09c2cf0061` |

To reproduce explicitly, run `python -m bench.p003_yolo_resolution --baseline <ordinal DEV 16 baseline> --trusted-code <external b773 map> --output <new directory> --run-cpu`. Preparation without `--run-cpu` freezes inputs and performs no model inference. Existing paths refuse overwrite or implicit repeat. Only the worker PID created by this runner can be affected by its subprocess timeout; no campaign process groups or retained historical PIDs are used. All intended pages/arms remain explicit on bounded preparation or inference failure, and no retry is automatic.
