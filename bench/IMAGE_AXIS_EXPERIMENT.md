# Image axes and representations: broad DEV grid

`python -m bench.decision_image_axes --directory <new-directory> --scope page`
freezes the 30 authored context assembly cases for all four models in
`decision_image_run.MODELS`. There are six target sizes (200, 300, 400, 500,
600, 800), three axes (width, height, longest), and three independently labeled
representations (RGB8, grayscale8, palette4). These cases have ten correlated
layout templates across three vocabularies; they do not establish real-world
or heldout accuracy. No arm is discarded based on earlier model quality.

The selected axis equals its requested size; the other dimension preserves
aspect ratio within pixel rounding. Actual width, height, total pixels,
source/actual aspect ratio, encoded PNG bytes/hash, bit depth and color type
are recorded in `actual-images.json`. The 8,000,000-pixel and 512-KiB image
limits are checked without silently changing dimensions. Native base rasters
are rendered by the existing CPU cache with its full-page rendering cap.
Targets that need a larger base are refused, rather than upscaled. `--scope
region` is a separately frozen scope and may honestly refuse tall targets for
thin regions.

The representation arm uses the same dimensions and Lanczos resampling.
Grayscale8 converts RGB to luminance. Palette4 uses 16-color median-cut
quantization without dithering and verifies the encoded four-bit PNG IHDR.
These are separate lossy representation choices, not equivalent encodings.
Clef transport may use the existing lossless WebP adapter; metadata records
that codec, original PNG bytes and decoded-pixel equality. PNG bit depth is
source representation metadata, not a claim about WebP encoding or internal
provider preprocessing.

To preserve the anisotropic angle, use a **different directory** with
`--distort-axis-sweep`. This adds widths 200/300/400/500 with fixed height 512,
and heights 200/300/400/500 with fixed width 512, for all three representations.
These configurations explicitly change aspect ratio and record
`anisotropic=true`. They are distinct from the aspect-preserving grid and
are not implicit fallback transforms. The full main grid is retained in
that manifest as well.

Preparation projects scorer metadata away from the existing context-case
factory immediately and never reads expected choices. Source PDFs, projected
evidence, image records and request bodies stay under ignored artifacts.
Every model sees the same original current-context assembly menus and prompt;
only images change. Postfreeze evaluation belongs to the existing runner.
All bodies are frozen and verified before any paid client is constructed.

Width and longest edge are identical for a landscape source; height and
longest edge are identical for portrait sources. The preparation deduplicates
exact request bytes and records every declared alias in `geometric_aliases`.
They are geometric/source/pixel identity observations, not separate paid
trials or provider cache measurements. Quality from a canonical request can
be mapped to its exact aliases, but aliases provide no independent latency,
throughput or charge observation. `batches` lists only unique request bodies;
`refusals` retains input/representation/provider admission failures. The
existing runner's canonical-arm summaries do not automatically expand aliases.

Root execution can load the frozen manifest, verify it, and call
`decision_image_run.run(directory, manifest, client=shared_client,
wave_name='image-axis-wave.json')` under the shared `exclusive_lock` for
`run.lock`. The named axes wave keeps its accounting separate from the older
image-resolution wave; the shared client's campaign cap remains authoritative.
The wrapper is deliberately preparation-only. No credentials, inference,
training or GPU calls occur during freezing. API costs/times remain separate
from local preprocessing.
