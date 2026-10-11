# Wild-v1 DEV corpus: realistic documents and flattening levels

Wild-v1 derives realistic, human-looking documents from the P003 extension
synthetics (`bench.p003_extension_cases.plans()`). It keeps each plan's
structure: family, table shapes, merged spans, blank header rows, wrapped
descriptions and value kinds. Word-salad cells are replaced with semantically
coherent content, so invoice totals add up, dates are plausible and headers
mean something. Each document is then produced at several flattening levels,
the way such files actually appear in the wild.

This remains synthetic DEV research. It is not a natural-document test set.
Do not read, enumerate or derive anything from `bench/heldout-silver/` or
`bench/results/pdf-master-artifacts/silver-heldout-v1/`; route every path
through `bench.silver.guard_path`. No hosted inference and no local GPU
(pass `--disable-gpu` to Chromium). Everything runs on CPU.

## Layout

All generated artifacts are ignored by Git and live under
`bench/results/pdf-master-artifacts/wild-v1/`:

```
photos/{photo_id}.jpg          public-domain or CC0 photos, ≤1600 px long edge
photos/photos.json             license and provenance records
docs/{doc_id}/source.html      authored HTML (Chromium producer) or .odt/.html (LibreOffice)
docs/{doc_id}/assets/          rendered screenshots and charts used by the document
docs/{doc_id}/source.pdf       born-digital level L0
docs/{doc_id}/truth.json       ground truth (schema below)
variants/{doc_id}/{level}.pdf  flattened derivatives
variants/{doc_id}/variants.json
manifest.json                  corpus manifest written by the integrator
```

## Modules

| Module | Owner role | Responsibility |
|---|---|---|
| `bench/wild_photos.py` | photos | Acquire and license-check photos, write `photos.json` |
| `bench/wild_documents.py` | documents | Realistic templates, content, screenshots, charts, L0 PDFs, truth |
| `bench/wild_flatten.py` | flattening | Derive flattening levels from any L0 PDF |
| `bench/wild_corpus.py` | integrator | Build orchestration, manifest, gallery, baseline audit |

## photos.json

```json
{"version": 1, "photos": [{"id": "p01-harbor", "path": "photos/p01-harbor.jpg",
  "sha256": "...", "width": 1600, "height": 1067, "subject": "harbor at dusk",
  "tags": ["landscape", "outdoor"], "source_url": "https://commons.wikimedia.org/...",
  "author": "...", "license": "CC0 1.0 | Public domain", "license_url": "...",
  "retrieved_at": "2026-10-11T07:40:00Z"}]}
```

## truth.json

```json
{"version": 1, "doc_id": "w-invoice-ruled-01", "template": "vendor_invoice",
 "producer": "chromium | libreoffice", "base_plan_id": "e...", "family": "ruled",
 "page_count": 1,
 "metadata": {"title": "...", "author": "...", "subject": "...", "keywords": ["..."],
              "lang": "en-US", "created": "2026-03-14T09:30:00Z"},
 "outline": [{"level": 1, "title": "...", "page": 1}],
 "links": [{"text": "...", "href": "https://example.org/..."}],
 "blocks": [
   {"kind": "heading", "level": 1, "text": "..."},
   {"kind": "paragraph", "text": "..."},
   {"kind": "list", "ordered": false, "items": ["...", "..."]},
   {"kind": "table", "id": "t1", "rendering": "ruled | borderless | screenshot | chart_data",
    "header_rows": 1, "values": [["..."]], "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}],
    "caption": "..."},
   {"kind": "figure", "id": "f1", "figure_kind": "photo | screenshot | chart",
    "photo_id": "p01-harbor", "wrap": "left | right | none", "caption": "...",
    "text_in_image": ["..."]},
   {"kind": "sidebar | callout | footnote | header | footer", "text": "..."}
 ]}
```

`blocks` are in logical reading order. A table rendered only as a screenshot
uses `"rendering": "screenshot"`; its values exist only as pixels in the
born-digital PDF. Text that appears only inside images goes in `text_in_image`.

## Flattening levels

| Level | Meaning | Expected text layer |
|---|---|---|
| `L0_tagged` | Born-digital, tagged structure, XMP/Info metadata, outline, links | native |
| `L1_untagged` | Re-distilled: structure tree, MarkInfo and outline removed; text kept | native |
| `L2_stripped` | L1 plus Info/XMP metadata removed, as after a generic "print to PDF" | native |
| `L3_outlined` | Glyphs converted to vector paths; visually identical, no extractable text | none |
| `L4_raster` | Clean 200 dpi page images only | none |
| `L5_raster_ocr` | 300 dpi page images plus an invisible Tesseract OCR text layer | ocr |
| `L6_phone_scan` | Skew, perspective, uneven lighting, noise, colour cast, JPEG q≈60 | none |
| `L7_photocopy` | Grayscale/bitonal, speckle, slight rotation, 300 dpi | none |
| `L8_mixed` | First page native, later pages raster; single-page docs rasterize the main table region or lower half | partial |

`variants.json` records each level's command lines, tool versions, input and
output SHA-256, page count, whether a text layer exists, and CPU/wall/RSS.

## Families and templates

Each extension family maps to realistic document types:

| Family | Example templates |
|---|---|
| ruled | vendor invoice, quarterly financial summary |
| borderless | product spec sheet, conference agenda |
| wrapped | expense report, travel itinerary with long descriptions |
| unnamed | lab data appendix whose first table row is blank |
| merged_headers | grant budget with grouped quarter headers |
| mixed | research report page with a ruled and a borderless table |
| column_pairs | side-by-side plan comparison sheet |
| negative | policy memo, newsletter, intake form; no data tables |

Mixed media is cross-cutting: photos with text wrapping around them, pasted
UI screenshots (spreadsheet, dashboard, email), vector and raster charts,
sidebars, footnotes, headers and footers, and multi-column newsletter layouts.

## Languages and difficult Unicode

Every document declares `"languages"` (BCP 47 tags, primary first) and a
`"unicode_features"` list in `truth.json`. Coverage across the corpus:

| Profile | Languages / scripts | What it stresses |
|---|---|---|
| Latin diacritics | de, fr, es, pl, vi, tr | Precomposed vs combining marks (NFC/NFD), ß, İ/ı, Vietnamese stacked marks |
| CJK | ja, zh-CN, zh-TW, ko | Full-width digits/punctuation, vertical-friendly text, mixed kana/kanji, Hangul |
| RTL | ar, he | Bidi runs with embedded Latin, numbers and currency; Arabic shaping and tatweel |
| Indic / SE Asian | hi, th | Devanagari conjuncts and matras; Thai with no inter-word spaces |
| Cyrillic / Greek | ru, uk, el | Lookalike letters (Cyrillic а vs Latin a) |
| Code-switched | en + any above | Names, addresses and product terms in another script inside English documents |

`unicode_features` values: `ligature` (ﬁ ﬂ ﬀ from fonts or literal),
`nbsp`, `narrow_nbsp`, `zero_width` (ZWSP, ZWJ, ZWNJ, word joiner),
`soft_hyphen`, `combining_marks`, `nfd_text`, `fullwidth`,
`unicode_minus` (U+2212 vs hyphen), `dashes` (en/em/figure dash),
`smart_quotes`, `currency` (€ £ ¥ ₹ ₩ ₪ ฿ ₫), `math_symbols` (± × ÷ ≤ ≥ µ ° ‰),
`superscripts` (², footnote markers), `emoji` (including ZWJ sequences and skin-tone
modifiers), `bidi_controls` (LRM, RLM, isolates), `rtl_numbers`,
`thousands_separators` (1.234,56 / 1 234,56 / 1,23,456), `date_formats`
(2026-03-14, 14.03.2026, 2026年3月14日), `private_use` (icon-font glyphs).

Truth strings are stored exactly as authored (no normalization). Scorers must
report both exact and NFKC-normalized comparisons, and must never fold away
differences silently.

An additional encoding level exercises a common real-world failure:

| Level | Meaning | Expected text layer |
|---|---|---|
| `L9_broken_tounicode` | L1 with every font's `/ToUnicode` CMap removed; glyphs render, extracted text is garbage or empty | broken |

## OCR language models

System Tesseract ships only `eng` and `osd`. The integrator uses
`wild-v1/tessdata/` when present: `tessdata_fast` models (Apache-2.0, from
github.com/tesseract-ocr/tessdata_fast) for ara, chi_sim, chi_tra, deu, ell,
fra, heb, hin, jpn, jpn_vert, kor, pol, rus, spa, tha, tur, ukr and vie, plus
copies of the system `eng`, `osd`, `pdf.ttf` and configs. It sets
`TESSDATA_PREFIX` for the build steps.
