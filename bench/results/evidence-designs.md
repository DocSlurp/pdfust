# D001 evidence preparation, 2026-10-08

Four source-only native decision arms freeze 125 physical DEV pages into 500
requests. A separate file holds authored gate labels. No model was called and
no charge was incurred in this preparation.

| Configuration | Wall seconds | CPU seconds | Peak RSS MiB | Questions per request |
| --- | ---: | ---: | ---: | --- |
| Gate only | 3.232 | 3.214 | 107.06 | 1 |
| Header/continuation diagnostic | 3.135 | 3.177 | 107.71 | 1–10 |

Measurements use perf_counter/process_time and `/proc/self/status` VmHWM for
one sequential CPU Python process; peak RSS is process lifetime with no
sampling. Source-side extraction only, no inference. Gate-only mean request
sizes were geometry 8,807 bytes, neighbors 10,028, blob 11,545 and hybrid
10,226. Image evidence is a source line/word-box schematic, not native pixels.

One physical page exceeded the complete 4,096 axis-line evidence admission.
Its four frozen arms explicitly refuse source evidence and instruct unresolved;
retain the page in denominators and avoid paid calls for it. Extractor warnings
also surfaced unmapped glyphs, an existing source limitation. No word or line
truncation conceals these limitations. All remaining 124 pages retain complete
admitted source word evidence. Preparation is not an extraction-quality result.

Eight Python tests passed, including label/metadata perturbation invariance in
all four arms, native adapter invariance, word-ID conservation, schematic
text invariance and unresolved-aware gate denominators. Ruff checks pass.
Full requests and manifests remain ignored under
`bench/results/pdf-master-artifacts/evidence-designs/`.
