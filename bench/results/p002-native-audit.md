# P002 native source audit

Fourteen separately constructed DEV cases: 14/14 image-region inventories match authored construction; 14/14 callers preserved. Real OCR: True; extraction errors: 0. This is a source contract audit, not OCR or table quality.

One CPU worker, OCR threads=1, fixed 150 DPI. Wall 147.08s, process CPU 146.50s, peak RSS 445259776 bytes via /proc/self/status VmHWM (current executable). Kernel high-water mark, one process including native OCR; source construction is outside elapsed/CPU timing but included in RSS. GPU and network inference were unused.

| Case | Native words | Uncovered regions | Preserved | OCR errors |
|---|---:|---:|---|---:|
| native-only | 4 | 0 | True | 0 |
| mixed-inset | 4 | 1 | True | 0 |
| two-image-tables | 4 | 2 | True | 0 |
| rotation-90 | 0 | 1 | True | 0 |
| rotation-180 | 0 | 1 | True | 0 |
| rotation-270 | 0 | 1 | True | 0 |
| crop-offset | 0 | 1 | True | 0 |
| inherited-multipage | 0 | 0 | True | 0 |
| japanese-raster | 0 | 1 | True | 0 |
| native-intersection | 6 | 0 | True | 0 |
| overlapping-images | 0 | 0 | True | 0 |
| decorative-raster | 0 | 1 | True | 0 |
| empty-page | 0 | 0 | True | 0 |
| raster-table | 0 | 1 | True | 0 |

References encode only authored region counts and are joined after extraction. Rotated pages use display coordinates; sideways OCR is intentionally uncorrected. Decorative rasters remain eligible because source discovery cannot distinguish decoration from text. Native intersection and overlapping images abstain. Whitespace uses approximate character advance; re-extracted word geometry belongs to a constructed invisible layer.

All 56 mode/tokenization calls completed. Mixed inset and two-image cases returned six and twelve recognized boxes respectively; Japanese raster returned six. Uncorrected 90-degree source yielded zero boxes, 270-degree source yielded two full-page versus three clipped boxes, and decoration yielded one hypothesis. Recognition count is not correctness.

Native diagnostic corpus: all 56 designated manifest pages were interpreted; six had empty native text. Three retained tables projected 1,478 complete slots with zero ownership/geometry refusals. Two page interpretations warned about unmapped Type 3 glyphs. Maximum plain text was 5,653 UTF-8 bytes in this run. The two-row NICS header is now recovered from exact anchors even when the geometric divider is absent across the header. CPU-only native audit: wall 2.22s, CPU 2.37s, peak RSS 106,012,672 bytes via the same executable kernel high-water mark; one process, serial pages.

Environment: Python 3.14.7, pdfust 0.13.0, x86_64, 8 logical CPUs. OCR engine PP-OCRv6 packaged RTen models; one dedicated thread. Raster text uses Noto Sans CJK Regular from the system font package. Complete inputs, outputs, source hashes, warnings and native observations stay under ignored `pipeline-p002/native-stress/`.
