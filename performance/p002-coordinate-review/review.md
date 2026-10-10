# P002 hybrid and multiscale coordinate review

This CPU-only review found and corrected one concrete hybrid output ordering bug.
Two valid disjoint model tables with no fully contained source words receive the
same fallback anchor as a following footer. The old `(anchor, markup)` tuple sort
emits that footer first and reverses upper/lower tables according to their cell
text. Empty native grids likewise used the end-of-source fallback after a footer.
These are presentation failures even when table content, geometry and source
accounting remain valid.

Default hybrid renderer v2 keeps source-owned anchor indices first, uses the next
geometric source anchor for unowned tables, and breaks equal anchors by display
y/x and stable insertion order. HTML text never participates in ordering.
Geometry here is a display-space fallback; it does not establish semantic column
order or logical reading direction on rotated or multilingual pages. The patch
changes no source validation, vector quarantine, native ownership, overlap
refusal, detector exclusion, span validation, provenance or inventory accounting.

`compose(..., render_version=1)` retains exact old rendering and the complete old
rules dictionary for historical verification only. Source/model-controlled
fields cannot choose the renderer. The reporter must select v1 solely from the
approved original frozen helper hash and matching archived bytes. Version 2
records `rules.version=2` and `rules.renderer_version=2`; new inference requires a
new frozen identity. No existing result, PDF, response or reference was rewritten.

Reviewed old hybrid commit: `c821fa3`, module SHA-256
`6e1edda5cd94b675611e30cef8c228f87968c3b9ffdf8f9b7b135d544e18ae68`.
Corrected helper SHA-256:
`a329f11f29f1e452d402c4efd70787d49258e07c0188a94fbb1162521445eaf1`.
Reviewed unchanged multiscale helper SHA-256:
`0c5e4ab29f05bbc5ccec652f5ce82275d26c60399820aa39017bc83f649afa79`.

The new isolated coordinate tests cover all four right-angle rotations with and
without CropBox on page index 1 of a two-page PDF. They compare all five actual
submitted whole/tile rasters pixel-for-pixel against the original selected page
render, check unchanged source bytes and preserved rotation, replay every mapping,
and verify crop transcription's global output bbox. Affine-transformed hybrid
fixtures preserve native ownership, superseded words and crossing prose when
native/model boxes touch. Strict `length` and `content_filter` finishes retain
mock charges and all five raw detections but admit no tables or stale success
artifacts. Ordering regressions cover opposite lexical order, reversed proposal
order, empty native grids and a following footer. Renderer-version type checks
reject booleans and unknown versions.

An independent offline comparison loaded the exact old helper bytes and compared
complete old/new-v1 composition dictionaries on every available source from
`native-regional-full-r2`: all 272 matched, with four missing-source diagnostics
explicitly excluded. Default v2 native-only Markdown was unchanged for all 272.
A synthetic model-table success and an atomic overlapping-table refusal also
matched old/new-v1 dictionaries exactly. This checks compatibility, not corpus
quality. No references were needed or read during this review.

On Linux 7.2.5-3-omarchy x86_64, glibc 2.44, Python 3.14.7: the new tests plus the
existing hybrid suite passed 37 tests in 8.73 s; external subprocess elapsed time
was 8.9715 s. Kernel waited-child accounting reported 8.406231 user CPU seconds,
0.631472 system CPU seconds and maximum RSS 261,312 KiB. The 272-source legacy
comparison took 2.5490 s wall and 2.5393 s process CPU, with lifetime maximum RSS
50,924 KiB. RSS is kernel peak accounting without sampling, not aggregate memory.
Both measurements used CPU-only processes; no provider client, credentials,
network inference, GPU or protected corpus paths were accessed. Ruff and mypy
pass for the changed helper and new tests.
