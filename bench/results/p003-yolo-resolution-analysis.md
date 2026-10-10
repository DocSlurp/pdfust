# P003 YOLO resolution acquisition audit

Increasing nominal inference size from 640 to 1,280 improves table-box coverage on this fixed DEV cohort. At the established IoU 0.1 admission threshold, matched reference tables increase from 16 to 29 of 53; at IoU 0.5 they increase from 14 to 23. The larger arm still misses 30 tables at IoU 0.5 and produces 14 extra proposals. These are acquisition measurements, without transcription or cell quality claims.

All arms retain all 16 pages, 53 reference tables and four negative pages. The same source raster, checkpoint, confidence threshold 0.25, class-aware NMS IoU 0.7 and predictor defaults were used; only nominal inference size changes. All 48 attempts completed. No per-page resolution winner was selected.

| Nominal size | IoU | Proposals | Matched | Missed | Extra | Negative FP pages /4 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 640 | 0.1 | 19 | 16 | 37 | 3 | 3 |
| 640 | 0.3 | 19 | 14 | 39 | 5 | 3 |
| 640 | 0.5 | 19 | 14 | 39 | 5 | 3 |
| 640 | 0.7 | 19 | 14 | 39 | 5 | 3 |
| 1024 | 0.1 | 24 | 17 | 36 | 7 | 1 |
| 1024 | 0.3 | 24 | 16 | 37 | 8 | 1 |
| 1024 | 0.5 | 24 | 16 | 37 | 8 | 1 |
| 1024 | 0.7 | 24 | 15 | 38 | 9 | 1 |
| 1280 | 0.1 | 37 | 29 | 24 | 8 | 0 |
| 1280 | 0.3 | 37 | 25 | 28 | 12 | 0 |
| 1280 | 0.5 | 37 | 23 | 30 | 14 | 0 |
| 1280 | 0.7 | 37 | 23 | 30 | 14 | 0 |

The four overlap thresholds were declared before scoring. Matching maximizes one-to-one match cardinality, then IoU; it uses no text or table shape cues. Duplicate proposals count as extras. Three pages lose original proposals at larger sizes, so these inventories are not nested.

| Nominal size | Source word-center union /10,778 | Available reference characters /15,772 | Missing reference characters | Inference wall s | Inference CPU s | Max sampled worker RSS MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 640 | 2205 | 9867 | 5905 | 5.716 | 11.133 | 1339.3 |
| 1024 | 3218 | 13710 | 2062 | 13.727 | 26.969 | 1396.7 |
| 1280 | 3268 | 13764 | 2008 | 21.284 | 41.892 | 1515.5 |

Character availability counts each source word once if its center lies in any table proposal. NFC-normalized, whitespace-free character multiplicities are compared within each page, without borrowing across pages. This optimistic bag ignores order, geometry and complete-word feasibility; it is a text necessity diagnostic, not attainable cells or complete-table quality. The 1,024-to-1,280 change adds only 54 available reference characters while improving box matching, which motivates testing localized structure rather than equating geometric coverage with recovered cells.

Recorded inference timings sum the 16 page calls per size. The CPU worker used two intra-op threads and one inter-op thread. RSS was sampled every 100 ms using `/proc/self/statm`, including endpoints; the table shows the maximum worker sample, excluding the parent. Initialization was separately 7.493 s wall / 12.001 s CPU; one warmup per size took 2.053 / 1.753 / 1.877 s wall. Source rendering, initialization and warmups are excluded from the inference sums. No API charges or full-pipeline throughput are attributed to this local detector experiment.

Before loading DEV references, the independent analyzer authenticated both archived helpers against Git `05f7a6a`, authenticated the original ordinal source using external `b773d57` authority, checked checkpoint/PDF/source identities, regenerated all 16 frozen PNG rasters byte-for-byte, checked all effective predictor arguments and thread settings, and rebuilt every retained raw-box projection. Raw boxes are confidence-filtered post-NMS outputs, not logits; the analyzer did not rerun the model. No fresh confirmation or protected heldout access occurred.

Frozen source SHA-256: `9a369b3971e628f4aa202a5de5fd3b35e914ba150c02fc560ace6fe08f323619`. Detailed hashes, per-page metrics and resource receipts remain in ignored `yolo-resolution-v1/independent-acquisition.json`.
