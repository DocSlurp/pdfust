---
title: API overview
description: A compact map of pdfust Document, Page, Pixmap, Rect, permissions, warnings and exceptions.
---

# API overview

Full docstrings live in the package (`help(pdfust.Document)`); this page is a
map. All page numbers are 0-based except `get_toc` / `set_toc` (1-based,
pymupdf-compatible). All coordinates are top-left-origin display space.
The [API stability policy](stability.md) defines the public boundary and
deprecation lifecycle.

## Document { #document }

`pdfust.Document(filename=None, stream=None, password=None, max_decompressed_size=None, *, limits=None)` —
`pdfust.open()` is an alias constructor. Context-manager support included.
Password input stops at 127 UTF-8 bytes.

| Member | Purpose |
|---|---|
| `doc[i]` / `load_page(pno)` / iteration | `Page` views (negative indices; re-fetch after structural changes) |
| `page_count` / `len(doc)` | number of pages |
| `limits` / `complexity` | immutable open-time resource policy / cheap structural facts without stream decoding |
| `needs_pass` / `is_encrypted` / `authenticate(pw)` | encryption state & unlock with a 127-byte password boundary (pymupdf semantics) |
| `is_repaired` | whether opening repaired an incorrect final classic `startxref`; saving normalizes the xref data |
| `metadata` / `set_metadata(dict)` | eight standard Info fields (UTF-16BE aware); 1 MiB aggregate text boundary and atomic writes |
| `get_page_text(pno, option)` | `"text"` / `"words"` / `"blocks"` / `"dict"` |
| `get_text(pages=None)` | batched plain text for up to 4,096 pages sharing one interpreter font cache (`None` means every page) |
| `to_markdown(pages=None, table_strategy="lines", max_size=64 MiB)` | page-at-a-time two-pass Markdown with a bounded linear entry builder; max 4,096 pages and cumulative UTF-8 output (`None` opts out), with headings, CJK, emphasis, lists, columns, vertical order, and table controls |
| `render_page(..., max_size=64 MiB)` / `render_pages(..., workers=, max_size=512 MiB)` / `render_page_svg(..., max_size=64 MiB)` | bounded PNG bytes, ordered parallel batches capped at 4,096 pages and cumulative encoded output, or bounded UTF-8 SVG (`None` opts out) |
| `compress_images(dpi=150, quality=75)` | lossy, placement-aware downsampling and JPEG recompression of safe DCT or Flate raster XObjects; returns typed byte/count statistics |
| `set_fallback_font(font, kind=, index=, font_language="ja", max_font_size=64 MiB)` | bounded locale-aware CJK fallback for non-embedded Adobe Japan1, Korea1, GB1, or CNS1 fonts; `None` opts trusted font input out |
| `select` / `delete_page(s)` / `insert_pdf` / `new_page` / `copy_page` | page management; select/delete/insert batches are capped at 4,096 entries |
| `get_toc()` / `set_toc(toc)` | cycle-aware bounded outlines (1-based pages; 4,096 entries/nodes, 8,192 edges, 64 levels, 1 MiB text) |
| `get_page_labels()` / `set_page_labels(labels)` | page label ranges; fixed caps: 4,096 entries/nodes, 32 levels, 1 MiB label text |
| `get_form_fields()` / `set_form_field(name, value, fontfile=, fontbuffer=, fontindex=, font_language=, max_font_size=64 MiB)` | bounded AcroForm list & fill with 1 MiB caller name/value input plus native, bounded widget appearances and font input |
| `embfile_add(..., max_size=64 MiB) / embfile_names / embfile_get(name, max_size=64 MiB) / embfile_del` | attachments with symmetric input/decoded-output defaults plus 1 MiB caller text, bounded metadata, and inline FileSpec clone shapes; `max_size=None` explicitly opts out |
| `get_pdfa_claim(max_size=1 MiB)` | bounded XMP PDF/A declaration read; `max_size=None` explicitly opts out, and this is not validation |
| `save(...)` / `tobytes(..., max_size=512 MiB)` | atomic replacement after a complete same-directory streamed write / bounded PDF bytes; `garbage=` `deflate=` `object_streams=` and 127-byte-bounded `user_pw=` / `owner_pw=`; `max_size=None` opts out |
| `close()` | also via `with` |

`compress_images()` interprets every page to find each indirect raster object's
largest placement, then edits a lopdf clone atomically. `dpi=None` disables
downsampling but retains quality recompression. The conservative boundary is
direct, single-filter, 8-bit DeviceGray/DeviceRGB DCT or Flate streams without
masks or custom decode arrays. DCT decode parameters are excluded; Flate may
use no predictor or a consistent PNG predictor. Unsupported interpreted
indirect images and encodings that would not be smaller are skipped; inline
images are not considered. One call rejects more than 65,536 interpreted
indirect raster placements. Repeating the same settings is idempotent.

### Page import and output preservation

`insert_pdf()` and the `merge()` helper import pages with their content and
resources. They do not merge the source Catalog's AcroForm registry, outlines,
named destinations, page labels, optional-content configuration, or tagged-PDF
structure. A copied widget or link can retain its appearance without preserving
its document-level functionality. Validate those features separately when
combining documents; correct rendering alone does not establish preservation.
Page labels are index ranges; review or reset them after structural edits rather
than assuming they follow reordered pages.

Saving rewrites the PDF and does not preserve existing digital signatures. On
POSIX, new PDF and PNG output files use mode `0600`; replacing an existing
regular file preserves its mode. Atomic replacement protects existing output
from ordinary write failures, but does not provide an `fsync` durability promise.

## Page { #page }

| Member | Purpose |
|---|---|
| `number` / `parent` / `get_label()` | identity & display label |
| `get_text(option)` / `search_for(needle, max_hits=4096)` | extraction and bounded case-insensitive search; terms stop at 4,096 UTF-8 bytes and `None` opts trusted result sets out |
| `get_layout(table_strategy="lines")` | owned spatial snapshot: words, source IDs, merged cells, rectangle/anchor field queries, and declared header relationships; one combined CPU interpretation, no rasterization |
| `get_text_ocr(dpi=, engine=, tile_size=, overlap=, min_confidence=, rotation=, clip=)` | local PP-OCRv6 positioned words without editing; `rotation` corrects input clockwise and `clip` uses display coordinates |
| `apply_ocr(..., rotation=, clip=, skip_existing=True)` | recognize and insert an orientation-aware invisible searchable layer; skip existing text in the selected region by default |
| `find_tables(strategy="lines", clip=None)` | complete or conservatively refined vector-bordered grids and merged cells; `"text"` opts into borderless detection; `clip` is a display-coordinate region |
| `to_markdown(table_strategy="lines", max_size=64 MiB)` | single-page Markdown with the same table and UTF-8 output controls |
| `get_images()` | drawn images (`bbox`, JPEG passthrough / PNG); rejects partial output above 4,096 placements, 64,000,000 cumulative pixels, or 64 MiB of payloads |
| `get_drawings()` | interpreted vector fill/stroke paths with display-space line/cubic geometry and normalized paint/stroke properties; rejects partial output above 8,192 paths, 131,072 commands, or 131,072 aggregate dash values |
| `get_pixmap(scale=, dpi=, background=, clip=)` / `render(max_size=64 MiB)` / `render_svg(max_size=64 MiB)` | bounded PNG / UTF-8 SVG rendering; `clip` uses display coordinates |
| `rotation` / `set_rotation(deg)` | display rotation |
| `mediabox` / `cropbox` / `rect` / `set_mediabox` / `set_cropbox` | page boxes |
| `insert_image(rect, filename= / stream= / pixmap=, rotate=, keep_proportion=, overlay=, max_size=64 MiB, max_pixels=64,000,000)` | draw bounded JPEG/PNG or reuse an already bounded RGBA `Pixmap`; `None` opts trusted encoded input or PNG pixels out; `rotate` turns clockwise in 90-degree steps |
| `show_pdf_page(rect, src, pno=, keep_proportion=, overlay=)` | overlay a PDF page as vectors; `src` may be the same document |
| `insert_text(point, text, fontsize=, fontname=, fontfile=, fontbuffer=, fontindex=, font_language=, color=, overlay=, max_font_size=64 MiB, max_text_size=1 MiB)` | bounded UTF-8 and 4,096-line standard-14 WinAnsi or shaped subset text; installed script/locale providers are selected automatically and `font_language` resolves ambiguous Han; `None` opts the corresponding trusted input out |
| `insert_textbox(rect, text, fontsize=, fontname=, fontfile=, fontbuffer=, fontindex=, font_language=, color=, align=, expandtabs=, lineheight=, overlay=, max_font_size=64 MiB, max_text_size=1 MiB)` | bounded UAX #14 wrapping with Core 14, OpenType, or an installed script/locale provider; physical and wrapped layout stop at 4,096 lines, tab expansion is preflighted, and overflow draws nothing |
| `insert_ocr_text_layer(words, rotation=)` | orientation-aware invisible OCR layer; fixed caps: 4,096 words and 1 MiB UTF-8 text per call |
| `replace_text(search, replacement, default_char=, max_size=64 MiB)` | atomic copy-on-write simple-encoded replacement with bounded input/output |
| `annots()` / `get_links()` / `add_highlight_annot(...)` / `add_link_annot(rect, uri)` | bounded annotation/link reads and creation; rendering conservatively supplies missing appearances for bounded RGB Highlight, Underline, StrikeOut, and Squiggly dictionaries with valid `QuadPoints` without changing the source PDF |

`get_drawings()` returns `DrawingInfo` dictionaries with `type="f"`, `"s"`,
or `"fs"`, self-contained line/cubic `items`, `rect`, RGB/opacity, fill rule,
width, cap, join, and dashes. Pattern paints retain their geometry with
`None` color and opacity. Clipping paths, clip-resolved visibility, group and
soft-mask structure, optional-content layer names, text, images, and annotations
are not returned; optional-content visibility is still applied. The result is
rejected rather than truncated above 8,192 paths or 131,072 commands.

Embedded-font `insert_text` requires one font containing every glyph.
`pdfust[ar]`, `[he]`, `[hi]`, `[jp]`, `[ko]`, `[th]`, `[zh-cn]`, and
`[zh-tw]` provide Noto Sans/Serif generation fonts. Kana, Hangul, Bopomofo,
Arabic, Hebrew, Devanagari, and Thai select an installed provider automatically.
Pure Han keeps the JP-first compatibility default; pass
`font_language="zh-CN"`, `"zh-TW"`, `"ko"`, or `"ja"` when the locale matters.
This is one whole-run font, not per-glyph fallback. Each line is shaped, but
bidirectional paragraph layout and wrapping remain outside this primitive.
RTL shaping renders correctly. Pure RTL lines and lines with one Latin or
numeric token bracketed by RTL text extract in logical Unicode order. Edge
tokens, multiple tokens, and general mixed-direction paragraphs remain in
producer visual order.

Complex shaping can require PDF `/ActualText` to preserve a logical string that
does not map one-to-one to glyphs. Generated PDFs include that data for external
viewers, but pdfust's current extractor does not yet consume `/ActualText`;
some reordered or context-dependent clusters, especially in longer
Devanagari runs, can therefore extract approximately after reopening.

`insert_textbox` adds wrapping without becoming a rich-text engine. It preserves
explicit newlines, expands tabs, breaks CJK at Unicode opportunities, and uses
grapheme-safe emergency breaks for overlong words. Alignment constants are
`TEXT_ALIGN_LEFT`, `TEXT_ALIGN_CENTER`, `TEXT_ALIGN_RIGHT`, and
`TEXT_ALIGN_JUSTIFY`. A negative return value is the vertical deficit; no page
content or font resource is added in that case.

`set_form_field` generates appearances for text, combo/list choice, checkbox,
and radio widgets. WinAnsi text auto-fits in Helvetica; pass an OpenType
`fontfile` or `fontbuffer` for subset-embedded Unicode. Installed locale/script
providers are selected with the same rules as `insert_text`, and
`font_language` resolves ambiguous Han. Existing
non-empty checkbox/radio appearances are preserved and missing states receive
vector marks. Missing appearances on other WinAnsi fields are completed at the
same time; `NeedAppearances` is cleared only when every fillable widget is
self-contained. Comb text fields honor inherited `MaxLen` and alignment, center
each Unicode grapheme in its position, and reject overlength values atomically.
Rich text, pushbutton actions, and signatures are not generated.

`Table.confidence` is a deterministic 0–1 ranking heuristic, not a calibrated
probability. `Table.diagnostics` is a `TableDiagnostics` tuple containing the
strategy and, for borderless text tables, em-normalized alignment error,
minimum gutter and row-gap variation. Complete vector grids score 1.0,
sparse-rule hybrid grids score 0.95, and both have `None` for those text-only
metrics. `TableFinder.strategy` and
`TableFinder.clip` preserve the settings used.

### Spatial fields and header relationships { #spatial-fields }

`Page.get_layout()` collects words and vector table evidence in one CPU
interpretation. It populates the same bounded caches used by `get_text` and
`find_tables`. A snapshot owns its data: subsequent edits, cache eviction, and
closing the document do not change it. Source IDs are local to that snapshot.
Normal text extraction still skips table-rule collection. With
`table_strategy=None`, spatial extraction also skips table detection.

```python
with pdfust.open("invoice.pdf") as document:
    layout = document[0].get_layout(table_strategy=None)

# Rectangles are top-left display coordinates, with rotation already applied.
# Selection uses word centers and half-open bounds, not pixel visibility.
words = layout.select((300, 80, 550, 110))
results = layout.extract_fields([
    pdfust.FieldSpec("invoice_number", anchor="Invoice number", value_type="text"),
    pdfust.FieldSpec("total", region=(300, 600, 550, 630)),
])
for result in results:
    print(result.name, result.status, result.value)
    # selected.word_ids and selected.anchor_ids point back to layout.words.
```

An anchor matches an exact, case-insensitive sequence of words on one line;
trailing colons are ignored. `direction="right"` (default) and `"below"` use
display coordinates. `max_distance` bounds the search in PDF points. A `region`
with an anchor scopes both its label and candidate values; a region alone is an
authoritative value rectangle. For anchor queries, `value_type="number"`,
`"date"`, or `"text"` filters candidates by a simple lexical shape; it does not
validate a locale-specific number, calendar date, or business meaning.

Without a placement model, one eligible candidate is required. Multiple anchors
or candidate values produce `ambiguous`; absent matches produce `missing`.
Source words selected by multiple fields produce `conflict` for every affected
field. These states return `value=None`. Candidate spans remain available for
review, except when the anchor itself is missing or ambiguous. Labels declared
in the same batch form barriers so a query cannot reach through a neighboring
label to steal its value. Callers should scope searches when other labels are
not known. Rectangles preserve source text without model decisions.

For known table boundaries, `layout.grid(columns=[...], rows=[...])` accepts
all display-coordinate boundaries, including the outer edges. It needs no table
detector and groups wrapped words within those explicit cells. A native table
comes from `layout.tables`; native grids are normalized to their dominant
right-angle text orientation while every cell retains its display-space box.

```python
with pdfust.open("report.pdf") as document:
    layout = document[0].get_layout()
table = layout.tables[0]
for record in table.records(header_rows=2, row_header_columns=1):
    for field in record:
        print(field.name, field.value)
        # field.headers preserves outer-to-inner header cells and their IDs.
        # field.row_headers retains the declared row-label cells.
        # field.cell retains its source words, bbox, and merged spans.
print(table.to_bullets(header_rows=2, row_header_columns=1))
```

Header bands are explicit; `records()` does not guess that row one is a header.
Bands cutting through merged cells are rejected. Repeated labels remain distinct
by cell ID. Multiple fields may reference the same merged value cell; they are
not independent values. The default detector does not reconstruct every complex
header, extend a short header into a borderless body, or establish semantic
scope from language. `table_strategy="text"` retains the existing opt-in
borderless detector and its ambiguity with aligned prose. Correcting or supplying
boundaries remains necessary when detection fails.

`PlacementModel(weights, bias, threshold=0.9, margin=0.2)` is an optional,
six-feature logistic ranker. It uses only existing candidates and cannot rewrite
their text. An accepted candidate must exceed both the score threshold and the
margin over the runner-up. It cannot override a duplicated anchor or source-ID
conflict. Scores are not calibrated correctness probabilities. No pretrained
model is enabled by default, and no tensor runtime, download, or GPU is required.

The reproducible CPU pilot is `CUDA_VISIBLE_DEVICES='' uv run python -m bench.spatial`.
It retains fitted weights, inputs, decisions, and separate training, policy-selection,
and evaluation sets in `bench/results/spatial-artifacts/`. To try the fitted pilot
on its intended fixture family:

```python
import json
from pathlib import Path

state = json.loads(Path("bench/results/spatial-artifacts/placement-model.json").read_text())
model = pdfust.PlacementModel(**state["model"])
results = layout.extract_fields([
    pdfust.FieldSpec("account", anchor="Account", value_type="number"),
], model=model)
```

The pilot's simple distance/alignment rule outperformed the learned ranker on
held-out synthetic cases. Those fixtures do not establish real-document accuracy.
Fit and evaluate coefficients and thresholds on an independent document family
before enabling them; nearby aligned text can still be semantically wrong.
The features are reciprocal forward gap and cross-axis offset (normalized by
anchor height), presence of a value-type constraint, capped candidate word count,
below/right direction, and relative text height, in that order.

Fixed limits are 65,536 snapshot words, 256 field queries, 256 anchor matches or
candidate spans per field, and 4,096 explicit grid cells (`spatial_count`).
`to_bullets(max_size=...)` defaults to 64 MiB of UTF-8 (`spatial_output_size`).
Existing document interpretation/text limits still apply. The initial snapshot
interprets the selected page; selection does not seek directly to a PDF byte range.
Ordinary extraction limitations still apply to clipping, occlusion, mixed writing
directions, missing Unicode, and image-only content. This API never invokes OCR
implicitly.

## Module level { #module-level }

| Name | Purpose |
|---|---|
| `peek_metadata(filename=None, stream=None, password=None, *, max_file_size=None)` | fast metadata/page-count probe with optional input-size rejection and a 127-byte password boundary; `repaired` reports bounded classic-`startxref` recovery |
| `Permissions` | encryption permission flags (IntFlag) |
| `Rect` | rectangle NamedTuple with `width` / `height` |
| `TextPage` / `TextBlock` / `TextLine` / `TextSpan` | `get_text("dict")` TypedDict hierarchy |
| `ImageInfo` / `ImageCompressionResult` / `DrawingInfo` / `AnnotationInfo` / `LinkInfo` / `FormFieldInfo` | TypedDict contracts for mapping-shaped page, document-operation, and form results |
| `PageLabelInfo` / `PageLabelSpec` | normalized page-label output / setter input contracts |
| `DocumentMetadata` / `MetadataUpdate` / `MetadataProbe` | metadata output / partial update / fast-probe contracts |
| `DocumentLimits` / `DocumentComplexity` | immutable untrusted-input budgets, including `max_interpretation_size` for the PDF snapshot and `max_text_glyphs` for positioned layout / cheap structural TypedDict |
| `OcrEngine` / `OcrWord` | reusable pure-Rust PP-OCR engine / positioned result contract |
| `OcrRotation` / `DrawingItem` / `WordEntry` / `BlockEntry` / `FormFieldType` | runtime-importable OCR-rotation, vector-command, tuple and literal type aliases |
| `TableFinder` / `Table` / `TableDiagnostics` | owned table geometry, cell text (`None` for merged continuations), strategy and confidence evidence; `Table.to_markdown(max_size=64 MiB)` preflights escaped UTF-8 output |
| `PdfError` / `LimitError` / `PasswordError` / `OcrError` / `DocumentClosedError` / `EncryptedDocumentError` / `StalePageError` | exception hierarchy; limit failures expose a stable `.code` (ValueError-compatible base) |
| `Pixmap` | Immutable RGBA8 pixels: `samples` / `width` / `height` / `stride` / `n` / `tobytes(max_size=64 MiB)` / streaming, failure-atomic PNG-only `save(path)`; cp314t also supports read-only zero-copy `memoryview()` |
| `PdfustWarning` | recoverable interpretation warnings (xref repair, font resolution, image decode) |

The `TypedDict` contracts affect static typing only; values remain ordinary
pymupdf-style dictionaries. `LinkInfo` requires `kind` and `from`, with
destination-specific optional keys. `PageLabelSpec` requires `startpage`;
`style`, `prefix`, and `firstpagenum` retain their runtime defaults.
