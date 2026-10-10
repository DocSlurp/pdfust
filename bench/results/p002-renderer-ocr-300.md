# P002 alternate-renderer native OCR at 300 DPI

This bounded CPU-only follow-up runs the unchanged OCR route on all four known native `unsupported_no_text` diagnostics at 300 DPI. It extends the prior [150-DPI audit](p002-renderer-gap-audit.md), without repeating that arm, consulting references, making model requests, or changing the default renderer. Original PDFs and the earlier artifacts remain untouched. The result provides no reliable text-rescue claim and does not justify automatic renderer substitution.

Every renderer's PNG is inserted into an isolated image-only surrogate PDF at its recorded 300-DPI physical scale, then passed to installed native OCR at 300 DPI. The surrogate is re-rendered by hayro; this is not direct recognition of an alternate renderer's buffer. Coordinates describe the surrogate raster geometry rather than original native source ownership. All twelve original PNGs, renderer-native text outputs, complete OCR boxes/literals/confidences, image dimensions/hashes, warnings, and timing records are retained under `pipeline-p002/renderer-gap-audit-300/`.

| Diagnostic | Hayro native chars / OCR boxes | PyMuPDF native chars / OCR boxes | PDFium native chars / OCR boxes |
| --- | ---: | ---: | ---: |
| Manuscript cover `p3537ba59f34ed944966f` | 0 / 5 | 0 / 4 | 0 / 6 |
| Type 3 `pd1a2dc76a3752f9861ee` | 0 / 0 | 6 / 1 | 7 / 1 |
| Blend `pfb20031e973ad29c7e43` | 0 / 0 | 0 / 0 | 0 / 0 |
| JPX/LZW `peb29c108f12d92347139` | 0 / 0 | 0 / 0 | 0 / 0 |

The Type 3 page remains blank in hayro. Both alternate rasters now produce one OCR literal `二`: PyMuPDF confidence 0.934 and PDFium 0.898. Their native text mappings still contain three `A` characters separated by line endings. At 150 DPI, PyMuPDF produced no OCR boxes and PDFium produced one different symbol. Higher resolution improves recognition agreement between the alternate rasters, but disagreement with the PDF's character mapping prevents any claim that the original Unicode text has been recovered. Reported confidence does not measure semantic or Unicode correctness.

The decorated manuscript cover produces more isolated OCR symbols at 300 DPI, including high reported confidences. Literal outputs in engine order are hayro `1`, `L`, `中`, `7`, `中`; PyMuPDF `中`, `7`, `d`, `唱`; and PDFium `L`, `中`, `7`, `é`, `d`, `唱`. None is a recovered paragraph or table. Together with the earlier visual audit, these observations show that increased raster resolution can expose spurious OCR admissions on decorative content. The blend and solid-color JPX/LZW fixtures remain empty across all three renderers.

The fixed installed OCR settings were four CPU threads, concurrency one, tile size 1408 pixels, overlap 192 pixels, minimum recognition confidence 0.5, and rotation zero. There was no orientation search, text rewrite, OCR layer insertion into original PDFs, or source-text substitution. Installed versions: jev-pdf 0.13.0, PyMuPDF 1.28.2, pypdfium2 5.12.1, and pylopdf-ocr-models 0.1.0. Installed model hashes are retained in `model-hashes.json`.

The single Linux CPU process took 42.300 s wall and 123.105 s process CPU, with 619064 KiB `getrusage(RUSAGE_SELF)` lifetime peak RSS. Wall/CPU start after imports and include all twelve renderer/native-text/PNG paths, twelve surrogate OCR passes, comparisons, and artifact writes. RSS includes imported libraries and OCR buffers; no subprocesses or utilization sampling were used. OCR initialization was separately 0.023 s wall / 0.023 s CPU. Compared with the prior 150-DPI matched route (10.453 s wall / 30.480 s CPU / 500536 KiB RSS), the higher-resolution arm costs substantially more CPU and memory without establishing a reliable rescue.

All four source hashes remained unchanged. Six focused tests, Ruff, and scoped mypy passed. The explicit CLI parameter permits only 150 or 300 DPI and preserves the existing 150-DPI default.

```sh
python -m bench.generalization_renderer_gap_audit \
  --manifest bench/results/pdf-master-artifacts/pipeline-p002/corpus-r2/manifest.json \
  --output bench/results/pdf-master-artifacts/pipeline-p002/renderer-gap-audit-300 \
  --ocr --dpi 300
```

| Identity | SHA-256 |
| --- | --- |
| Executed audit helper | `b03b83b084443be21afb0d1a75109e1f0f8e6f914579ece6e8280e52aba42fea` |
| Complete 300-DPI audit JSON | `e800ecb4e8b79e1f854a55e2576bb8711a3b1790effab83db6787d7fa5804c4e` |
| Manuscript PDF | `da04b715cd876a00f79728faed5501e0697e4e0783201470a7f20eec67bd6e85` |
| Type 3 PDF | `dc213b3d2952f06517ac487d9892b11628f4b5bedc2ad8278a4c05c1b40be8f6` |
| Blend PDF | `9947d9c15d853823cedc1e87378dea89a665570e4f233b7a0ba215e5859134ab` |
| JPX/LZW PDF | `ba14897a4139944e56674fefe176a56f29326e69ff2baf3e07ba096b520def78` |
| OCR detector | `57c5778be784d7aace438a4ea1926864a7b5fd3d49c8e577799f8a83e8dcb022` |
| OCR recognizer | `b6eef947901c5ff0bf6ee62d8b46f58b1423666f0ae0c87b2f42127502925f8f` |
| OCR dictionary | `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d` |
