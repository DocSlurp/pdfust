# P002 source-only multiscale CPU layout diagnostic

Fixed whole-page, 2×2, and 3×3 overlapping source-pixel detector calls completed all 16 natural DEV screen pages on 2026-10-09. Every arm conserved all 7,351 cached OCR/extraction source IDs exactly once. More tiles produced more table proposals and more source coverage, alongside many incomplete fragments and overlapping proposals. No reference annotations were read or scored; this diagnostic does not choose a quality winner.

## Fixed configuration

One serial persistent pinned YOLO26m DocLayNet CPU worker, FP32, four intra-op threads reasserted after prediction, one inter-op thread; CUDA_VISIBLE_DEVICES empty. The source page raster has maximum side 3,072 pixels. The whole-page detector input is resized to maximum side 1,024; 2×2 and 3×3 grids have 12% overlap relative to nominal tile width/height. Each detector frame has at most four million pixels. Every prediction uses the existing model size 640 and confidence 0.25. Class-aware confidence-ranked NMS uses IoU > 0.5, with source call order breaking exact confidence ties.

The fixed crops depend only on source page dimensions. Complete raw outputs, class labels, confidences, pixel/display boxes, tile viewports, and per-call measurements are retained. NMS removes overlapping same-class proposals, but does not reconstruct tables split across tiles. Table proposals touching an interior tile edge within 2% of a tile extent or owning a source word extending outside their tile explicitly abstain on complete context. Native grids retain priority; capacity fragments also abstain. Detector geometry is not semantic truth.

This uses the model, Python, Torch and Ultralytics versions recorded in [the whole-page diagnostic](pipeline-layout-detector.md). Machine: Intel Core i7-7700K at 4.20 GHz, eight available logical CPUs, no GPU usage. Other research may run concurrently. No network requests, installations, paid inference or reference-informed crops were used.

## Source-only outcomes

| Arm | Detector calls per page | All NMS boxes | Table proposals | Nonempty detector regions | Detector-owned source IDs | Incomplete boundary regions | Empty table proposals | Contested word centers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| whole | 1 | 266 | 19 | 21 | 1269 | 0 | 0 | 0 |
| whole_2x2 | 5 | 694 | 47 | 37 | 1777 | 8 | 10 | 363 |
| whole_3x3 | 10 | 1010 | 100 | 61 | 1935 | 39 | 39 | 955 |
| whole_2x2_3x3 | 14 | 1268 | 116 | 65 | 1948 | 41 | 51 | 1024 |

Whole-page detector regions also include four capacity fragments. Combined tiling yields 65 nonempty detector regions, of which 41 have explicit tile-boundary abstention. The 116 proposals are not 116 established tables: fragmentation and duplicate source coverage require downstream abstention and review. Residual words remain present in every arm. Empty proposals arise when their source is absent or already assigned to a competing proposal.

| Page ID | Whole table proposals | Whole + 2×2 | Whole + 3×3 | Whole + both grids |
| --- | ---: | ---: | ---: | ---: |
| p1bfa52a41a5e15015698 | 0 | 11 | 31 | 33 |
| p6ef5d3c5c2edb1c109c4 | 2 | 4 | 6 | 8 |
| p391ea102f48e27fcdd65 | 2 | 3 | 10 | 11 |
| p9f92a30432da612d1bcc | 2 | 3 | 4 | 5 |
| p656361df32bd7d69a39e | 2 | 7 | 11 | 16 |
| p98d10ef50dee4b24506a | 2 | 5 | 18 | 19 |
| pc848c2a56527f81021a7 | 1 | 1 | 3 | 3 |
| pc9c4bcc7f4f2a5dc3bab | 1 | 1 | 4 | 4 |
| p1e230b0fd05df7dd5e23 | 1 | 2 | 2 | 3 |
| pda95432063a8a20bbe01 | 1 | 3 | 1 | 3 |
| pe87ca2d41151f28dc44c | 1 | 1 | 3 | 3 |
| pf012d6adb9592dab9a13 | 1 | 2 | 4 | 4 |
| p27ec5aaca0dd08c90360 | 1 | 1 | 1 | 1 |
| p9cc5ebfad2ee46a13b5e | 1 | 2 | 1 | 2 |
| pdb4e1fa3babeca265abb | 1 | 1 | 1 | 1 |
| p42049db34e230ce77d75 | 0 | 0 | 0 | 0 |

## Resources and practical limits

| Arm | Worker wall seconds | Worker CPU seconds | Maximum sampled worker RSS bytes |
| --- | ---: | ---: | ---: |
| whole | 4.231 | 15.754 | 1167306752 |
| whole_2x2 | 21.491 | 77.002 | 1188769792 |
| whole_3x3 | 42.512 | 157.569 | 1193029632 |
| whole_2x2_3x3 | 59.772 | 218.817 | 1193029632 |

Initialization including warmup took 2.571 wall seconds, 5.285 CPU seconds, and 1,059,856,384 bytes sampled worker RSS. Parent rendering, tile encoding, cached-source reading, partitions, IPC and waiting took 80.167 wall seconds and 20.437 parent CPU seconds across the pages; maximum sampled parent per-page RSS was 280,395,776 bytes. Initialization is measured separately from the per-page parent scope. RSS uses /proc/self/statm every 100 ms plus endpoints; CPU uses process_time and lifetime RSS uses getrusage. Worker and parent scopes are separate. Peaks must not be summed.

Arm measurements reuse retained calls from one 224-call pass; they are sums for their constituent calls, not four independent complete pipeline executions. Cached source ownership excludes original OCR/extraction cost. Model inference is roughly fourteen times whole-page wall time for the combined arm, while memory remains roughly 1.2 GB per worker. The substantial boundary/empty/overlap counts prevent treating increased proposals as increased table accuracy.

## Reproduction and validation

Run `python -m bench.pipeline_layout_tiles --manifest <natural16 manifest> --sources-directory <natural16-generate-sonnet directory> --output <new directory>`. Raw frames' results, source snapshot hashes, exact partitions, worker initialization, and measurements remain in ignored `bench/results/pdf-master-artifacts/pipeline-p002/detector-natural16-tiles/`. Frozen input PDFs are hash-checked; retained source IDs must match the page IDs. No raw artifacts are committed.

Five tiling tests plus nine worker/partition and twelve existing region tests pass; Ruff lint and format checks pass. Tests cover overlapping full-page coverage, frame pixel bounds, deterministic class-aware NMS, source conservation, interior-edge and crossing-word abstention, viewport offsets, all fourteen calls, and white compositing of transparent source pixels.
