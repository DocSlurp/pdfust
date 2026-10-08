# PDF encoding and routing audit

One grid, 13 equivalent encodings, four visibility controls, two scans and two raster negatives.
This is metamorphic coverage, not independent document-family accuracy. Five CPU repetitions include open, extraction, Python materialization and close; render/image inspection excluded.

| Case | Cohort | Exact source grid | Words | Open + extract ms |
| --- | --- | ---: | ---: | ---: |
| literal | equivalent | True | 12 | 8.822 |
| glyph-tj | equivalent | True | 12 | 8.250 |
| array-tj | equivalent | True | 12 | 8.220 |
| hex | equivalent | True | 12 | 8.176 |
| shuffled | equivalent | True | 12 | 8.190 |
| flate | equivalent | True | 12 | 9.245 |
| contents-array | equivalent | True | 12 | 8.248 |
| inherited-resources | equivalent | True | 12 | 8.160 |
| form-xobject | equivalent | True | 12 | 8.160 |
| translated-crop | equivalent | True | 12 | 8.165 |
| rotation-90 | equivalent | True | 12 | 8.214 |
| rotation-180 | equivalent | True | 12 | 8.283 |
| rotation-270 | equivalent | True | 12 | 8.120 |
| clip-empty | visibility | True | 12 | 8.903 |
| white-cover | visibility | True | 12 | 8.635 |
| invisible-text | visibility | True | 12 | 9.745 |
| duplicate-paint | visibility | False | 24 | 9.290 |
| pure-scan | ocr-routing | False | 0 | 9.752 |
| mixed-scan | ocr-routing | False | 6 | 10.734 |
| logo | ocr-negative | False | 5 | 8.453 |
| raster-illustration | ocr-negative | False | 5 | 8.286 |

Visibility controls have deliberately different visible semantics. Exact source-grid recovery on those controls is not correctness: clipping, covering paint and invisible text need separate policy.
Duplicate paint must remain observable; blanket deduplication can erase legitimate overprints.

The mixed-scan control has digital text but no extracted table. A page-empty OCR gate skips it. Image presence routes both scans but also both raster negatives. A fixed 20% area gate rejects the small logo but still routes a full-page illustration. These are work-routing signals, not table detections; a regional detector or other evidence is still needed.
Image area is a capped sum, not an overlap-aware coverage measure. `get_images()` currently decodes image payloads; its probe timings are in the full report and are not a cheap metadata-only route.

Inputs, output matrices, hashes and all timing samples remain in ignored `pdf-master-artifacts/encodings/`.
Reproduce: `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m bench.encoding_audit`.
