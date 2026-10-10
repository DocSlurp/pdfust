# Native OCR physical scale audit

Fixed 2048-edge rendering removed arbitrary PDF physical-scale dependence on all
three constructed controls. Each case produced byte-identical RGBA renders,
identical OCR text sequences, and identical normalized output boxes at page scales
0.5, 1 and 2. Fixed 150 DPI changed pixel dimensions, whitespace segmentation and
normalized boxes. This supports an opt-in pixel-edge control; it does not establish
better recognition on natural PDFs or select a winning edge.

The plan was retained before outcomes (`plan.json` SHA-256
`5275476c443c21ed0dacabcb4a782b5ad3f8d725e060948e323ef3412998cc1a`).
It fixed two arms, 150 DPI and 2048 edge, and three physical scales. Sources are
an independently constructed 1200×1600 RGB English table with 21 rows, four columns
and 24-pixel Pillow packaged Aileron text; its clockwise-90-degree raster copy;
and a text-free colored rectangle/ellipse control. The rotated case uses explicit
270-degree OCR correction. The original PNG pixels are preserved across all PDF
carriers, whose unrotated base page is 600×800 points. Construction records retain
literal cell text and source pixel boxes. No reference corpus, hosted model,
network request, GPU, or OCR-derived target was used.

| Arm | Scale 0.5 raster | Scale 1 raster | Scale 2 raster |
| --- | --- | --- | --- |
| 150 DPI | 625×833 | 1250×1666 | 2500×3333 |
| 2048 edge | 1536×2048 | 1536×2048 | 1536×2048 |

The rotated case swaps width and height. All 18 calls completed. Both textual
controls returned 84 recognition entries at every setting. The frozen row-major
sequence target has 387 non-whitespace characters; raw OCR sequence CER is
279/387 = 72.09% for every textual call because OCR emits columns before rows.
An explicitly post-run diagnostic assigns each output to the nearest constructed
text-box center in normalized coordinates. It finds zero character edits, no empty
cells and no multiple assignments in all 12 textual calls. That diagnostic explains
the ordering error; it does not score inferred table structure. These sources remain
legible even at the smallest raster, so they demonstrate no character-recognition
improvement from increasing the pixel edge. All six negative calls returned no text.

At 150 DPI, scale 0.5 text differs from scale 1 through whitespace segmentation,
so direct box correspondence abstains. Scale 2 keeps the same text sequence but
has maximum normalized box-coordinate deviations of 0.006009 for the upright table
and 0.007052 for the rotated table. At fixed edge, both sequence and normalized
coordinates agree exactly across all scales. This compares output invariance,
not detector localization against semantic gold.

| Resource, nine calls per arm | 150 DPI | 2048 edge |
| --- | ---: | ---: |
| OCR wall seconds | 40.922 | 55.514 |
| OCR CPU seconds | 128.296 | 175.711 |
| Peak sampled process RSS MiB | 539.66 | 495.03 |
| Separate preview-render wall seconds | 0.545 | 0.309 |
| Separate preview-render CPU seconds | 0.542 | 0.307 |

Measurements cover one audit process, including native Rust threads, using
`process_time` CPU, `/proc/self/statm` RSS every 100 ms plus endpoints, and retained
`getrusage` lifetime peak RSS. Sampled peaks can miss brief allocations. Memory
includes retained preview rasters and the reused engine. OCR timing includes its
own internal rendering; preview rendering is a separate retained-artifact cost.
Engine initialization took 0.0141 wall / 0.0148 CPU seconds, with 68.13 MiB sampled
RSS and 395.59 MiB lifetime peak RSS, illustrating the short-interval sampling limit.
Four OCR threads and one admitted call were used. Other root experiments could run
concurrently, so these are resource observations rather than isolated-machine
throughput claims. Versions: jev-pdf 0.13.0, OCR models 0.1.0, Pillow 12.3.0.
Model hashes, source PDF/PNG hashes and recognition-code hash are retained locally.
Two preliminary runner API errors were corrected before this completed run; the
reported timing covers only the completed run.

Reproduce with `python -m bench.pipeline_ocr_scale_audit --freeze --output PATH`,
then the same command without `--freeze`. Existing plans are preserved. Five CPU
construction/mock tests cover frozen carriers, arm scaling, rotated source geometry,
result mappings, failures and abstaining geometry correspondence; Ruff passes.

Complete ignored artifacts are at
`bench/results/pdf-master-artifacts/pipeline-p002/ocr-scale-audit/`: nine PDFs,
source PNGs, construction records, frozen plan, all 18 renders, complete OCR text,
word boxes, costs and resources, `report.json`, and `provenance.json`. The post-run
cell diagnostic was added to the retained report without repeating inference;
its implementation is now part of the runner for reproduction. No edge was changed
in response to these results.
