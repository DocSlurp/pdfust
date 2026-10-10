# P002 OCR orientation and dense source audit

Preserve display rotation for OCR. Forcing `/Rotate` to zero changes correctly compensated image sources into sideways rasters. Native normalization can remain a separately labeled path; physical sideways scans with `/Rotate=0` need raster orientation correction regardless of page normalization.

The opt-in candidate policy was committed as `5f88071` before the real mini-audit. It retains all four right-angle passes and selects by confidence-weighted alphanumeric inventory only: at least 16 alphanumeric characters, three boxes, 0.75 mean confidence, and 0.15 relative score margin. Weak evidence and ties abstain. No text dictionary, expected rotation, reference value, or family label enters selection. Candidate confidence is not calibrated correctness.

Eight new independently constructed DEV sources each ran with preserved and zeroed page rotation. The three compensated image transforms have identical upright display rasters to the zero-rotation control; Python tests compare their pixels. Physical sideways scans and a mixed native header/sideways inset have zero page rotation. All 16 frozen selected angles match construction, joined after selection, and selected recognized inventories recall all six exact authored tokens. This small authored result does not establish natural-page orientation reliability.

| Source | Normalize rotation | Fixed-0 authored token recall | Selected correction | Selected recall | All four passes wall (s) |
|---|---|---:|---:|---:|---:|
| compensated-90 | False | 1.000 | 0 | 1.000 | 2.76 |
| compensated-90 | True | 0.333 | 90 | 1.000 | 3.14 |
| compensated-180 | False | 1.000 | 0 | 1.000 | 3.26 |
| compensated-180 | True | 0.833 | 180 | 1.000 | 3.33 |
| compensated-270 | False | 1.000 | 0 | 1.000 | 3.37 |
| compensated-270 | True | 0.000 | 270 | 1.000 | 3.42 |
| physical-90 | False | 0.000 | 270 | 1.000 | 3.47 |
| physical-90 | True | 0.000 | 270 | 1.000 | 2.97 |
| physical-180 | False | 0.833 | 180 | 1.000 | 2.73 |
| physical-180 | True | 0.833 | 180 | 1.000 | 2.67 |
| physical-270 | False | 0.333 | 90 | 1.000 | 2.72 |
| physical-270 | True | 0.333 | 90 | 1.000 | 2.77 |
| mixed-physical-90 | False | 0.000 | 270 | 1.000 | 2.90 |
| mixed-physical-90 | True | 0.000 | 270 | 1.000 | 2.76 |
| upright-control | False | 1.000 | 0 | 1.000 | 2.81 |
| upright-control | True | 1.000 | 0 | 1.000 | 2.72 |

All 64 OCR passes, including losing candidates: wall 47.93s, process CPU 47.61s, peak RSS 197,316,608 bytes via /proc/self/status VmHWM (current executable). One Python process, one worker, one dedicated OCR thread, fixed 150 DPI; kernel executable high-water mark, no periodic sampler. Source construction precedes timing but remains in RSS; engine initialization is included. No network inference or GPU was used.

Real mixed-header integration additionally ran both whitespace and invisible-layer re-extraction with four candidates. Both selected correction 270, preserved the complete caller bytes and original native words, and retained eight source tokens (two native plus six OCR). Re-extraction inserts each selected region using its correction angle. Whitespace boxes are explicitly approximate and now follow that baseline direction. All candidate outputs and timings remain retained; abstaining regions expose no OCR tokens.

Source admissions bound four passes to 64 million cumulative clipped pixels, each full-page raster to 64 million pixels, each region candidate inventory to 16,384 boxes and 1 MiB text, and source output to the existing 4,096-word cap. Full-page raster cost is still paid for clipped interpretation.

The dense comparison freezes the two explicitly requested source IDs, DPI 150/300, fixed correction 0, empty mode, whitespace tokenization, one thread and one worker before observation. It uses native-free PDF carrier sources and reads no text or table references. Inventories and confidence are observations, not recall or table quality. Complete input links, outputs and costs are retained in `pipeline-p002/orientation-mini/dense-results.json`.

Procedural note: the initial broad filename lookup in the earlier resumed native audit repeated a protected-path filename-only discovery incident. It printed the protected AGENTS filename, without reading protected contents, constructing datasets, extracting/scoring heldout pages, or using them to select settings. All subsequent discovery and this orientation/dense audit use explicit named files and the supplied manifest IDs. No further protected paths were accessed.
