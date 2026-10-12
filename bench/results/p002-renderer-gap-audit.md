# P002 missing-text renderer audit

The four explicit `unsupported_no_text` native diagnostic pages in the fixed full276 run were compared at 150 DPI using installed hayro/pdfust, PyMuPDF, and PDFium. Original PDFs were preserved; no default renderer, extraction policy, or pipeline runner changed. This is a rendering and OCR-availability diagnostic, with no table-quality scoring or provider calls.

| Diagnostic ID | Source | Hayro native chars | PyMuPDF chars | PDFium chars | Hayro OCR boxes | PyMuPDF OCR boxes | PDFium OCR boxes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| p3537ba59f34ed944966f | Manuscript cover | 0 | 0 | 0 | 0 | 1 | 0 |
| pd1a2dc76a3752f9861ee | Type 3 fixture | 0 | 6 | 7 | 0 | 0 | 1 |
| pfb20031e973ad29c7e43 | Soft mask/blend fixture | 0 | 0 | 0 | 0 | 0 | 0 |
| peb29c108f12d92347139 | JPX/LZW fixture | 0 | 0 | 0 | 0 | 0 | 0 |

Every retained raster took the same OCR route: insert that PNG into an isolated image-only surrogate PDF at the recorded 150-DPI physical scale, then recognize with the installed native CPU engine at 150 DPI, four threads, concurrency one. This includes a hayro re-render of the surrogate, so it is not direct engine recognition of alternate renderer buffers and cannot establish original-source ownership. Complete OCR boxes, literal text, confidence, native text outputs, raster hashes, dimensions and warnings are retained in ignored `pipeline-p002/renderer-gap-audit/`. All four input hashes remained unchanged.

The Type 3 fixture isolates a rendering gap as well as missing Unicode extraction. Hayro's raster is entirely white and extraction emits the existing missing-Unicode warning. PyMuPDF and PDFium show small horizontal glyph strokes and faint marks. Both alternate native text outputs contain three `A` characters separated by line endings; their six-versus-seven character counts reflect differing line endings. PDFium-derived OCR recognizes one different symbol with reported confidence 0.954, while PyMuPDF-derived OCR recognizes none. The disagreement between character mapping, visible shapes, and OCR means alternate rendering does not demonstrate recovery of reliable text. It does show pixels absent from hayro, so a future explicitly labeled fallback could offer those pixels for inspection or recognition; it must not claim corrected Unicode or silently substitute model-transcribed text as native source text.

The manuscript page visually depicts an aged decorated cover rather than a readable paragraph. All renderers retain the cover image. PyMuPDF-derived OCR produces one symbol at confidence 0.507 with a box spanning a large part of the decoration; the other two produce no OCR boxes. This is not evidence of a useful text rescue. The blend fixture is graphical: hayro and PyMuPDF render a gray rectangle, while PDFium renders white. No renderer yields native text or recognized words. The JPX/LZW fixture is a solid red field in all three renderers, with no native or recognized text. These visual observations distinguish nontext fixtures from the Type 3 rendering/mapping limitation; none establishes semantic or table correctness.

Rasters have small rounding differences in dimensions, so pixel metrics resize only the second image to hayro dimensions using nearest-neighbor sampling. Original rasters remain untouched. Metrics are diagnostic differences with neither renderer treated as ground truth:

| Source | PyMuPDF mean channel difference | PDFium mean channel difference | Size normalization |
| --- | ---: | ---: | --- |
| Manuscript cover | 3.254 | 3.142 | 675×882 to 675×881 |
| Type 3 | 0.185 | 0.221 | 417×313 to 416×312 |
| Blend | 0.545 | 19.036 | 417×417 to 416×416 |
| JPX/LZW | 0 | 0 | 1275×1650 / 1651 to 1275×1649 |

Installed distribution versions were pdfust 0.13.0, PyMuPDF 1.28.2, and pypdfium2 5.12.1. The single CPU process used 10.453 s wall time, 30.480 s process CPU time, and 500,536 KiB Linux `getrusage(RUSAGE_SELF)` peak RSS. Wall/CPU scope starts after imports and includes all twelve render/text/PNG paths, twelve matched OCR passes and artifact writes. Process RSS includes imported libraries and native OCR resources. Native OCR initialization was separately recorded at 0.011 s wall and 0.012 s CPU. No subprocesses, utilization sampling, network, credentials, GPU, or paid calls were used. Two pixel-metric tests, Ruff, and focused mypy checks passed.

The isolated audit is reproducible with `bench.generalization_renderer_gap_audit` and its explicit DEV manifest, output directory, and `--ocr` opt-in. It intentionally examines only the four named missing-text diagnostics; it does not select a fallback based on references or alter any baseline behavior.
