# P002 CPU OCR source evidence

At 300 dpi, the fixed four-page natural diagnostic took 2.31 times the wall
time and 2.42 times the CPU time of 150 dpi, with a 9.1% higher sampled peak
RSS. It returned more text on three English pages and reduced invisible-layer
word merges. This is a measured quality/cost tradeoff; it does not select a new
default or establish general OCR accuracy.

## Frozen inputs and measurement

The metadata-selected mini subset of the exact natural16 screen was frozen
before recognition in ignored `pipeline-p002/ocr-evidence/selection-frozen.json`.
Selection takes one page each from other, one-and-more-column, double-column,
and single-column strata, preferring a previously unseen language then source
genre, with seeded SHA256 ties. It contains three English pages and one
simplified Chinese page. This greedy design covers four layouts and two
languages; it does not guarantee maximum language coverage. No annotations or
observed quality enter selection or extraction.

RTen PP-OCR uses four CPU threads, one engine per DPI process, admission
concurrency one, sequential pages, default 1408-pixel tiles/192-pixel overlap,
and confidence threshold 0.5. The machine has eight logical CPUs with all eight
in process affinity, running Linux 7.2.5-3-omarchy x86_64/glibc 2.44. Other
workspace activity was not isolated. No GPU, hosted service, network request,
or credential access was used.

Each page measurement includes opening the source, selected-page import,
bounded serialization, OCR render/recognition, invisible-layer insertion, and
re-extraction. RSS was sampled by psutil every 100 ms for this process,
including all RTen threads; CPU comes from `process_time`. Lifetime high-water
RSS is retained separately and is not a per-page memory delta. Engine
initialization took 0.023/0.022 seconds wall at 150/300 dpi and is reported
separately. These durations were shorter than the sampling interval, so the
initialization sampled RSS does not establish its actual peak. The helper now
also records an endpoint RSS sample for subsequent measurements.

| Fixed page | Metadata | 150 dpi wall / CPU seconds | 300 dpi wall / CPU seconds | 150 / 300 sampled RSS MiB |
|---|---|---:|---:|---:|
| `p42049db34e230ce77d75` | English, other layout | 8.54 / 25.98 | 18.30 / 59.44 | 463.23 / 505.48 |
| `p9f92a30432da612d1bcc` | Simplified Chinese, 1-and-more columns | 3.86 / 11.83 | 10.32 / 33.57 | 361.94 / 456.25 |
| `p6ef5d3c5c2edb1c109c4` | English, double columns | 5.81 / 17.69 | 11.66 / 37.04 | 415.84 / 466.36 |
| `pdb4e1fa3babeca265abb` | English, single column | 4.32 / 12.93 | 11.85 / 35.38 | 415.23 / 478.95 |
| Total wall/CPU; maximum RSS | Four fixed pages | 22.54 / 68.44 | 52.13 / 165.42 | 463.23 / 505.48 |

Complete outputs and source geometry are retained in ignored
`ocr-evidence/cpu-150.json` and `cpu-300.json`. The original PDF files remain
unchanged. No failures occurred among the eight measured calls.

## Recognition versus reconstructed word ownership

OCR returns text-run/line boxes, not independently localized boxes for every
word. The current pipeline inserts an invisible layer from those recognized
boxes and extracts words again. It preserved every non-whitespace character
in these eight calls, but changed some token boundaries:

| Fixed page | 150 dpi recognized boxes / whitespace tokens / re-extracted words | 300 dpi recognized boxes / whitespace tokens / re-extracted words | 150 / 300 recognized non-whitespace characters |
|---|---:|---:|---:|
| English, other | 133 / 505 / 489 | 142 / 541 / 540 | 2352 / 2549 |
| Chinese, 1-and-more | 125 / 145 / 144 | 128 / 145 / 145 | 1262 / 1262 |
| English, double | 145 / 532 / 532 | 151 / 544 / 544 | 2589 / 2614 |
| English, single | 33 / 347 / 347 | 39 / 365 / 365 | 1502 / 1599 |

At 150 dpi, reconstructed words include `Arunning` from `A running`,
`Holly,majority` from separately recognized tokens, and `20捐款数/元` from
`20` and `捐款数/元`. At 300 dpi the other-layout page retains one such merge;
the remaining pages match direct whitespace token counts. Character conservation
does not make these word boundaries suitable for independent cell ownership.
More recognized characters at 300 dpi are an observation, not proof that the
extra characters are correct.

`extract(page, mode='empty', dpi=150, engine=None,
tokenization='reextract')` returns `{'source': ..., 'diagnostics': ...}`.
Its explicit `tokenization='whitespace'` ablation splits the retained recognized
text directly. It preserves recognized whitespace boundaries and uses fresh
snapshot-local source IDs, with links to raw recognized line IDs. Bboxes use
uniform character-proportional subdivisions of the recognized line box and
are marked **approximate**. They are not glyph measurements or independently
recognized word geometry. Raw recognized text, boxes, and confidence remain
in diagnostics. This mode cannot restore missing spaces or characters in OCR,
and unspaced CJK runs remain intact. No default extraction behavior changes.

As a separately retained offline diagnostic, three plain annotated tables
have 369 reference non-whitespace characters in total; bbox-center-assigned
OCR has identical NFKC character bags at both scales. One formula-markup table
is excluded. This weak character-bag observation ignores cell placement,
ordering, and structural accuracy; it is not CER or a table-quality score.
Private references are loaded only after OCR for this diagnostic and never
enter source evidence.

## Optional mixed-page image regions

`mode='uncovered_images'` uses actual interpreted raster-placement bboxes and
native word geometry. It admits only image regions that do not intersect any
native word. All members of an overlapping placement group abstain; rejection
reasons are retained. Header/footer text outside an inset scan therefore does
not suppress its recognition. Any searchable text inside that scan suppresses
the whole placement; finer tile discovery is a separate future experiment.

Admission bounds are eight regions and 16 million aggregate clipped raster
pixels at the requested DPI. Full-page rendering cost is additionally bounded
at 64 million pixels, including clipped calls because current rendering may
still process the full page. There are at most 4096 source words/recognition
boxes, 4096 parent pages, and 32 MiB of selected-page serialized data. The
helper imports only the selected page into an owned in-memory document;
import materializes inherited resources, boxes, and rotation. Clone time and
memory stay inside extraction measurement. It verifies inherited display
geometry and the complete native word inventory before OCR, then verifies
that native ownership remains unchanged afterward. Native/OCR geometry
intersections refuse the complete result rather than expose duplicates.

No original document or source file is modified. Mixed-region discovery is
opt-in and has CPU-only fixture validation, not measured natural mixed-page
quality. Eleven focused tests cover abstention, region/pixel limits, original
state preservation, inherited attributes, direct whitespace geometry labeling,
and native/OCR source ownership.
