# CPU color-region experiment

Measured 2026-10-08, Linux x86_64, CPython 3.14, pdfust 0.13.0, standalone rustc 1.99.0 optimized std-only executable. CPU only; no wheel rebuild, hosted model, or public API change.

This pilot extracts contiguous raster color spaces and compares them with native fill/stroke paint bounds. Region geometry can support grouping headers, bands, and outlined white spaces; it does not establish table semantics, cell relationships, or pixel visibility for native paths.

## Controlled outcomes

Repository-authored MIT synthetic PDFs use pale blue invoice bands, scientific headers, alternating financial rows, black outlined white spaces, and prose without grouping decoration. A hit requires all four display-box coordinates within 2 PDF points of an authored group boundary. Extras are unmatched geometric candidates, not automatically false tables.

| Case | Expected | Native hits | Raster hits: 8 / 18 / 36 | Raster extras: 8 / 18 / 36 |
|---|---:|---:|---:|---:|
| invoice-bands | 2 | 2 | 2 / 0 / 0 | 0 / 0 / 0 |
| scientific-headers | 2 | 2 | 2 / 0 / 0 | 0 / 0 / 0 |
| financial-rows | 4 | 4 | 4 / 0 / 0 | 0 / 0 / 0 |
| outlined-spaces | 2 | 2 | 2 / 2 / 2 | 4 / 4 / 4 |
| prose-negative | 0 | 0 | 0 / 0 / 0 | 0 / 0 / 0 |

At threshold 8, raster components retain all eight pale fill boundaries and both outlined spaces. Thresholds 18 and 36 lose the pale groups: antialiased edge steps create a path to the near-white page background. Outline interiors survive, but stroke rings and text/antialias components contribute four extra candidates. Prose contributes zero retained candidates at the configured minimum area. Native paint bounds recover all ten authored boundaries directly.

## Timings

One fresh document per case; native extraction precedes the first raster render, so “cold render” means first rasterization with the hayro interpretation already initialized. Warm segmentation is the median of three subprocess calls on the same retained RGB raster. It includes process startup, stdin copying and JSON decoding; this is not a native FFI microbenchmark. Compilation is excluded. RSS was not measured.

| Case | Native paint grouping ms | First raster ms | RGB conversion ms | Warm segmentation ms: 8 / 18 / 36 |
|---|---:|---:|---:|---:|
| invoice-bands | 1.154 | 24.228 | 6.658 | 53.466 / 51.518 / 51.689 |
| scientific-headers | 1.317 | 19.905 | 5.84 | 53.986 / 51.869 / 50.029 |
| financial-rows | 1.079 | 14.793 | 3.413 | 52.516 / 52.366 / 50.051 |
| outlined-spaces | 1.249 | 15.045 | 3.54 | 51.331 / 51.07 / 50.128 |
| prose-negative | 0.993 | 14.781 | 3.439 | 50.429 / 49.862 / 50.621 |

These small vector PDFs favor native paint evidence. The raster path provides enclosed white-space evidence and can cover scanned/image-only inputs, but those inputs are not evaluated in this run. Neither path has demonstrated downstream table accuracy on real documents.

## Bounds and behavior

- Adjacent-pixel RGB Euclidean distance and encoded-sRGB Rec. 709 luminance gates both must pass. This is not perceptual Lab distance. Threshold chaining is intentional connected-component behavior; gradients can merge distant endpoint colors.
- Connectivity is explicitly 4 or 8. Bounds are exclusive pixel boxes. Outputs include area, mean RGB, final four-edge perimeter, darker-boundary fraction, and border contact. Darker-boundary support is evidence rather than a confidence probability.
- Border-connected components whose mean RGB channels are at least 248 are omitted. Enclosed white interiors remain. This policy can omit a pale region touching the page edge; disable it with `background_white=256`.
- Default limits: 4 million pixels, 65,536 total components (including filtered ones), 4,096 retained regions. Rust input RGB, byte membership flags, and a reusable u32 queue cost approximately eight bytes per pixel, plus bounded region/output storage. Python subprocess copies and the render raster add memory outside this Rust estimate.
- Pixel, component, result and allocation refusals expose no partial output. A checkerboard can hit component limits even when minimum-area filtering would remove its components. No recursive or unbounded flood-fill stack is used.
- Native grouping is capped at 1,024 candidates before its quadratic pass. It merges overlapping/touching compatible fill bounds or closed stroke bounds with matching opacity. Pattern paints are skipped. Bounding-box contact can disagree with true polygon contact and does not resolve clipping or overpaint.
- Render with `background=(255, 255, 255)` before `pixmap_rgb`; transparent pixmaps are rejected. Pixel-to-display mapping assumes full-page unclipped render and the supplied scale.

## Reproduction and validation

```bash
COLOR_REGIONS_RUSTC=/path/to/rustc python -m bench.color_regions
COLOR_REGIONS_RUSTC=/path/to/rustc python -m pytest tests/test_color_regions.py -q
```

The executable compiles independently from `bench/color_regions.rs`; the production Rust extension is untouched. Generated JSON stays in ignored `bench/results/pdf-master-artifacts/color-regions.json`, retaining input hashes, complete candidate outputs, expected boxes and run parameters. PDFs regenerate from the checked-in fixture recipe. All measurements use 96 dpi, 4-connectivity, minimum area 300 pixels, and white-background cutoff 248.

Validation: 13 Python integration tests pass; scoped Ruff and mypy pass. Tests cover variable thresholds/luminance gates, diagonal adjacency, enclosed white spaces with text holes, antialiased background text, final-component perimeter, empty/white images, pathological checkerboards, independent Rust refusal with empty stdout, invalid inputs, actual PDF native/raster grouping, and complete native candidate-cap refusal.

Proposed experiment-log row: `2026-10-08 | CPU color regions | bounded standalone Rust + native paint bounds | pale groups 8/8 at threshold 8, 0/8 at 18/36; outlines 2/2 with 4 extras; prose 0 | keep as optional spatial evidence, no default/API integration`.
