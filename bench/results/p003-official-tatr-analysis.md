# Official TATR postprocessing on matched frozen CPU predictions

All 144 page states were independently reconstructed before DEV references were opened:16 pages × 3 acquisition sizes × 3 globally declared thresholds. The same 80 frozen CPU forwards, projected objects and source-owned words are used; only postprocessing changes. Full denominators remain 16 pages, 53 tables, 2333 cells and 4 negatives. No model call, generated-string fallback or per-page winning treatment is introduced.

Official postprocessing recovers262–267 strict cells at YOLO640,380–382 at 1024 and521–569 at 1280. Each fixed treatment recovers 3 complete tables. At size 1280, gains coexist with 9–10 extra tables on positive pages; negative-page FP remains 0. This is an observed DEV comparison, with no new threshold selected for fresh confirmation.

| YOLO size | Threshold | Strict | Text | Structure | Complete | Missing | Extra | Negative FP /4 | Errors /16 | Exact positive pages | Dense2 strict /1972 | Other14 strict /361 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 640 | 0.3 | 262 | 263 | 342 | 3 | 39 | 3 | 3 | 1 | 2 | 0 | 262 |
| 640 | 0.5 | 263 | 264 | 344 | 3 | 39 | 3 | 3 | 1 | 2 | 0 | 263 |
| 640 | 0.7 | 267 | 268 | 648 | 3 | 37 | 2 | 2 | 0 | 2 | 4 | 263 |
| 1024 | 0.3 | 380 | 392 | 796 | 3 | 36 | 7 | 1 | 0 | 2 | 117 | 263 |
| 1024 | 0.5 | 382 | 393 | 800 | 3 | 36 | 7 | 1 | 0 | 2 | 119 | 263 |
| 1024 | 0.7 | 382 | 393 | 799 | 3 | 36 | 6 | 0 | 0 | 2 | 119 | 263 |
| 1280 | 0.3 | 521 | 533 | 1154 | 3 | 29 | 9 | 0 | 0 | 2 | 260 | 261 |
| 1280 | 0.5 | 569 | 581 | 1131 | 3 | 30 | 10 | 0 | 0 | 2 | 308 | 261 |
| 1280 | 0.7 | 539 | 548 | 1136 | 3 | 30 | 9 | 0 | 0 | 2 | 277 | 262 |

Matched previous maximum-overlap controls use the same source ownership and raw structure predictions. Official containment/refinement changes topology and assignment jointly; this comparison does not isolate a single operation.

| Size | Threshold | Previous strict | Official strict | Delta | Previous extra | Official extra |
|---:|---:|---:|---:|---:|---:|---:|
| 640 | 0.3 | 191 | 262 | 71 | 3 | 3 |
| 640 | 0.5 | 204 | 263 | 59 | 3 | 3 |
| 640 | 0.7 | 202 | 267 | 65 | 3 | 2 |
| 1024 | 0.3 | 193 | 380 | 187 | 6 | 7 |
| 1024 | 0.5 | 193 | 382 | 189 | 6 | 7 |
| 1024 | 0.7 | 306 | 382 | 76 | 6 | 6 |
| 1280 | 0.3 | 317 | 521 | 204 | 7 | 9 |
| 1280 | 0.5 | 438 | 569 | 131 | 8 | 10 |
| 1280 | 0.7 | 451 | 539 | 88 | 8 | 9 |

Two size 640 states, thresholds 0.3 and 0.5, encounter a reproduced ValueError on one dense page. Both entire pages retain zero tables and remain errors in the complete denominator. The verifier reproduces the same failure type, full source-unresolved state and immutable output; no failed partial structure or historical table receives credit.

Producer measurement for the full nine-treatment postprocessing pass: 217.616s wall, 216.582s parent CPU, 384.684MiB sampled peak RSS, 100ms psutil sampling. This excludes source authentication, rendering/acquisition and the prior 80 model forwards. It is not fresh pipeline throughput. No new API spend occurs; prior inference resources and costs are not allocated to these nine derivative arms.

Strict cell equality preserves punctuation and math notation after NFC/Unicode-whitespace normalization. A strict mismatch can therefore be a representation difference rather than missing information; no visual or semantic secondary metric replaces these counts.

Frozen SHA `81da8260d1a0d13ab183b5cd50d22aa9b92345005fef250331f1522cd34ba195`; report SHA `a108ab555a73a305bf4e7bacd2e0524bd4ac4dae246a770e74d73ca7aae276e6`. Independently supplied six-file Git authority authenticates every copied and executed helper. The only loaded retained external implementation is the explicitly reviewed pinned upstream MIT postprocess.py with exact source and license hashes. Original source/PDF/pixels/ownership, model-logit probabilities, projections and all 432 prior placement states are independently authenticated before derivative replay. Complete per-page matches and resources are retained in ignored official-tatr-postprocess-v1/independent-evaluation.json. Fresh confirmation and protected heldout sources are not accessed.
