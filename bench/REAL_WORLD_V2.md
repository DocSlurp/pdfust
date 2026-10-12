# Real-world-v2 DEV corpus: licensed PDFs from real producers

Real-world-v2 adds 40 licensed PDFs to the DEV benchmark. They come from
producers that the local generators cannot emulate, and the set has verified
truth for selected pages. It targets the gaps in `bench/DATASET_REALISM_REVIEW.md`:

- Microsoft Word, PowerPoint and PDFMaker output
- pdfTeX/LaTeX, Beamer and powerdot slides
- InDesign, Distiller, LiveCycle Designer and Apple Quartz
- scanner OCR layers: Acrobat Paper Capture, CVISION, LuraDocument and Adlib
- AcroForms, an AES-256 file with an empty user password, and PDF 2.0
- CJK and RTL text, multi-page tables, slides and math-heavy papers

This is DEV data. The tooling never reads `bench/heldout-silver/`,
`bench/results/pdf-master-artifacts/silver-heldout-v1/` or the
`HELD-OUT-NOT-FOR-TRAINING/` Langfuse datasets. Every path goes through a
held-out guard.

## Layout and commands

All artifacts are ignored by Git and live under
`bench/results/pdf-master-artifacts/real-world-v2/`:

```
downloads/<id>-<random>/original.pdf   untrusted download, one fresh directory each
downloads/<id>-<random>/download.json  URL, retrieval time, transfer facts
pdfs/<id>.pdf                          kept file (original or qpdf page selection)
truth/<id>.json                        verified truth for selected pages
candidates/<id>/pN.*                   extractor candidates and 100 dpi renders
manifest.json                          sources, licenses, hashes, profiles
health.{json,md}                       extraction health table
requests.log                           every HTTP request (budget: 150)
discovery/                             license and metadata lookups
```

```
.venv/bin/python -m bench.real_world_v2 fetch [--id ID]   # sequential, 2 s apart, cached
.venv/bin/python -m bench.real_world_v2 profile           # producer, version, fonts, filters
.venv/bin/python -m bench.real_world_v2 health            # pdfust vs pdftotext vs PyMuPDF
.venv/bin/python -m bench.real_world_v2 candidates --id ID --page N
.venv/bin/python -m bench.real_world_v2 validate          # manifest + truth schemas, sha256
```

### How downloads are handled

1. Each download is written to a new `tempfile.mkdtemp` directory.
2. The body must start with `%PDF-`.
3. pypdf opens the file in an isolated `python -I` subprocess. Nothing from the
   download directory is ever executed.
4. When a document has more than 30 pages or 5 MB, `qpdf --pages . <range>`
   keeps a page range. This retains the original Info dictionary, trailer and
   AcroForm. Both hashes are recorded: `original_sha256` and `sha256`.

The User-Agent names the project URL and carries no email address. Wikimedia's
upload servers return HTTP 429 to anonymous clients.

The acquisition used 79 HTTP requests in total. Seven Wikimedia requests failed
with 429 and three CRS/NTRS/Gutenberg attempts failed. Discovery used:

- one arXiv OAI-PMH `ListRecords` call for licenses
- six arXiv `/abs/` pages, each confirming CC BY 4.0 or CC0
- seven Wikimedia Commons API searches, whose `imageinfo` metadata exposes
  pdfinfo Producer, version and encryption
- two GOV.UK API calls
- one EveryCRSReport JSON lookup
- one GitHub API listing

## Sources

Sources are counted after `profile`. The manifest records URL, retrieval time,
license, license URL, attribution, sha256 and kept page range for every
document.

**Producers (40 documents, 478 kept pages, 43 MB):**

| Producer | Documents |
|---|---:|
| Microsoft Word, direct or via Etymon PJ | 6 |
| PDFMaker for Word/PowerPoint | 3 |
| PowerPoint | 1 |
| arXiv pdfTeX, restamped by pikepdf | 6 |
| pdfTeX: Gutenberg book, Beamer | 2 |
| Skia/Chromium: Wikipedia exports | 3 |
| InDesign | 2 |
| LiveCycle Designer | 2 |
| Acrobat Paper Capture | 2 |
| Each of: Distiller, Ghostscript (LaTeX powerdot), Apple Quartz (Keynote), Google Slides, iText, Antenna House, JUST PDF, Adlib Express, CVISION PdfCompressor, LuraDocument, Acrobat Image Conversion | 1 |
| Hand-authored PDF 2.0 examples | 2 |

**Other dimensions:**

| Dimension | Counts |
|---|---|
| Header version | 1.3: 2, 1.4: 10, 1.5: 11, 1.6: 4, 1.7: 12, 2.0: 1. A further file is upgraded to 2.0 through a catalog `/Version` in an incremental update. |
| Licenses | US public domain 14, CC BY 4.0 10, CC BY-SA 4.0 6, OGL v3.0 2, public domain (old) 2, CC0 1, CC BY-SA 2.0/3.0 1 each, Gutenberg 1, Japan PDL 1.0 1, Japanese Copyright Act Art. 13 1 |
| Languages | English 32, Japanese 4, Greek 2, Chinese 2, and Arabic, Hebrew, Korean, German, Romanian and Bengali 1 each |
| Features | xref and object streams 17, tagged 21, linearized 5, incremental revisions (more than one `%%EOF`) 10, landscape slides 9, invisible `3 Tr` OCR layers 5, AcroForms 3, AES-256 empty-password 1, Type 3 fonts 2 (Chromium), JPX 2, CCITT 1, DCT 14 |

**Image-only or mostly image:**

- `eisenhower-1960-talking-paper-scan` has no text layer.
- `fda-50605s31-label-2002` is mostly page images.
- `commons-word-critical-librarianship` is a Word file whose pages are pasted
  images, with 63 text characters.

| ID | Producer | Version | Kept pages | License | Languages |
|---|---|---|---|---|---|
| arxiv-2403.11436-trs-codes | arXiv pdfTeX | 1.5 | 1-20 of 36 | CC BY 4.0 | en |
| arxiv-2409.11638-banstereoset | arXiv pdfTeX | 1.5 | 1-11 | CC0 | en, bn |
| arxiv-2412.08972-rulearena | arXiv pdfTeX | 1.5 | 1-12 of 23 | CC BY 4.0 | en |
| arxiv-2503.14372-resnet-control | arXiv pdfTeX | 1.5 | 1-6 | CC BY 4.0 | en |
| arxiv-2505.13772-krikri | arXiv pdfTeX | 1.5 | 1-14 of 26 | CC BY 4.0 | en, el |
| arxiv-2505.24490-outer-k-planar | arXiv pdfTeX | 1.5 | 1-13 | CC BY 4.0 | en |
| census-p60-259-2016 | InDesign CC 2015 | 1.6 | 1-30 of 72 | US PD | en-US |
| commons-ala-lc-japanese-romanization | Word 2019 | 1.7 | 1-10,35-36 of 37 | US PD (LoC) | en, ja |
| commons-bluebook-1962-iran-papercapture | Acrobat 10 Paper Capture | 1.6 | 1-2 | US PD | en-US |
| commons-gslides-helpdesk-2022 | Google Slides | 1.4 | 1-12 | CC BY-SA 4.0 | en |
| commons-iorga-sibiu-cvision | CVISION PdfCompressor 5 | 1.7 | 1-12 of 24 | PD (author d. 1940) | ro |
| commons-josm-fossgis-2012-beamer | pdfTeX Beamer | 1.5 | 1-21 | CC BY-SA 2.0 | de |
| commons-ko-wikiconf-2022-keynote | Keynote / Quartz (Korean macOS) | 1.3 | 1-13 | CC BY-SA 4.0 | ko |
| commons-miyagi-gazette-662-aes256 | Word + Acrobat, AES-256 | 1.7 | 1-12 of 34 | JP Copyright Act Art. 13 | ja |
| commons-nbs-jres-interferometers-papercapture | Acrobat 9 Paper Capture | 1.4 | 1-5 | US PD | en-US |
| commons-physrevx-11-041050-distiller | Distiller 10 (APS) | 1.4 | 1-10 of 53 | CC BY 4.0 | en |
| commons-pptx-whole-glam-2023 | PowerPoint 365 | 1.7 | 1-27 | CC BY 4.0 | en |
| commons-special-relativity-powerdot | Ghostscript 10 (powerdot) | 1.4 | 1-24 of 272 | CC BY-SA 3.0 | en |
| commons-word-critical-librarianship | Word 2016 | 1.7 | 1-11 | CC BY-SA 4.0 | en |
| crs-if10183 | iText 7 | 1.7 | 1-3 | US PD | en-US |
| eisenhower-1960-talking-paper-scan | Acrobat 11 Image Conversion | 1.6 | 1-6 of 9 | US PD | en-US |
| eurostat-key-figures-2021 | InDesign | 1.7 | 1-24 of 79 | CC BY 4.0 | en |
| fda-50605s31-label-2002 | Word 8.0 / Etymon PJ | 1.3 | 1-23 | US PD | en-US |
| gao-25-108401-highlights | PDFMaker 25 for Word | 1.7 | 1-2 | US PD | en-US |
| gutenberg-41568-whitehead | pdfTeX 1.40.10 | 1.4 | 1-20 of 228 | PD (Gutenberg) | en |
| ia-rational-education-1900s-scan | LuraDocument (Internet Archive) | 1.5 | 1-20 of 84 | PD | en |
| irs-fw4-2026 | LiveCycle Designer 6.5 | 1.7 | 1-5 | US PD | en-US |
| irs-fw9 | LiveCycle Designer 6.5 | 1.7 | 1-6 | US PD | en-US |
| irs-i1040tt | Antenna House + iText | 1.7 | 1-6 of 28 | US PD | en-US |
| jp-digital-pdl-outline | JUST PDF 4 | 1.4 | 1-12 | Japan PDL 1.0 | ja |
| naca-tr824-airfoil-summary | Adlib Express (OCR) | 1.4 | 1-12 of 261 | US PD | en-US |
| nist-cswp29-csf2 | PDFMaker 23 for Word | 1.6 | 1-30 of 32 | US PD | en-US |
| pdfa-pdf20-incremental | hand-authored | 1.7→2.0 | 1 | CC BY 4.0 | en |
| pdfa-pdf20-utf8-test | hand-authored | 2.0 | 1 | CC BY 4.0 | en, ja, el |
| uk-dcms-cultural-exports-2012 | Word | 1.5 | 1-20 | OGL v3.0 | en-GB |
| uk-dcms-rcewa-values-2012 | Word | 1.5 | 1 | OGL v3.0 | en-GB |
| usace-keynote-pdfmaker | PDFMaker 11 for PowerPoint | 1.5 | 1-2 | US PD | en-US |
| wikipedia-ar-algorithm | Skia/PDF m154 | 1.4 | 1-3 | CC BY-SA 4.0 | ar |
| wikipedia-he-algorithm | Skia/PDF m154 | 1.4 | 1-4 | CC BY-SA 4.0 | he |
| wikipedia-zh-pi | Skia/PDF m154 | 1.4 | 1-10 of 36 | CC BY-SA 4.0 | zh |

### License notes

- **arXiv:** licenses were confirmed on each `/abs/` page, not only in OAI
  metadata.
- **Wikimedia Commons:** the license and author come from the file page's
  `extmetadata`. Files with no named author were skipped.
- **Wikipedia exports:** attribution points to the article history.
- **Eurostat:** the PDF itself states CC BY 4.0 under Commission Decision
  2011/833/EU.
- **Miyagi gazette:** official gazettes fall under Article 13 of the Japanese
  Copyright Act. Commons lists the file as public domain.
- **PDF Association examples:** these are hand-authored standards probes, not
  natural documents. Score them separately.

## Truth

Truth uses the wild-v1 `truth.json` block schema (`bench/WILD_CORPUS.md`).
`validate_truth` checks the following real-world fields:

- `pages`: 1-based pages within the kept file
- `truth_status`: `verified` or `partial`
- `truth_method`
- `uncertainty`
- `page` on every block

Paragraphs may be abbreviated only with `"partial": true`, which requires
`truth_status: "partial"`. Table matrices must always be complete and
rectangular. Merged cells use `spans`. Superscript footnote markers,
render-clipped text and page-break facts go in `cell_notes` rather than the
cell text. A table that crosses a page is one logical table with
`continues_on_pages`.

**Method.** For every covered page, `candidates` writes four candidates:
pdftotext `-layout`, PyMuPDF, pdfust `get_text`, and pdfust `to_markdown`.
It also renders the page at 100 dpi. Every disagreement and table cell was
reconciled on the image, with 200 dpi crops for small text and CJK. No truth
was copied from a single extractor. Several pages were completed by parallel
CPU-only agents under the same instructions; each records its own
`truth_method` and uncertainty.

As an automated cross-check, every table cell and unabbreviated text block was
searched in the whitespace-free pdftotext text of its pages. The only misses
are footnote markers, wrapped header cells, cross-page joins, column
interleaving, and raster-only chart values.

| Document | Pages | Tables (rows × cols) | Status |
|---|---|---|---|
| uk-dcms-rcewa-values-2012 | 1 | 12×8 ruled | verified |
| uk-dcms-cultural-exports-2012 | 8–9 | 12×4 crossing the page break, 12×9 | verified |
| gao-25-108401-highlights | 1 | sidebar + main column, infographic text_in_image | verified |
| nist-cswp29-csf2 | 20, 29 | 23×3 with merged Function cells, 4×3 | verified |
| eurostat-key-figures-2021 | 2–3 | 31×2, map page | verified |
| arxiv-2412.08972-rulearena | 6 | 41×14, 2 header rows, spans | verified |
| census-p60-259-2016 | 14, 18 | 46×9, 3 header rows; three-column prose page | verified |
| irs-fw4-2026 | 3, 5 | worksheet + 17×13, 16×13, 16×13 wage brackets; `form_fields` | verified |
| crs-if10183 | 1 | two-column prose; two raster charts as `chart_data` | verified |
| commons-miyagi-gazette-662-aes256 | 1, 10 | table of contents; 4×4 with row spans | verified |
| commons-ala-lc-japanese-romanization | 2–3, 11–12 | table of contents + prose; kana charts 29×6 (header span) and 16×5 | verified |

### Truth findings

The table below lists defects that were reconciled visually.

| Area | Finding |
|---|---|
| Two-column and sidebar layouts | pdfust `to_markdown` merges columns line by line on GAO p1 (sidebar + main), CRS p1, the RuleArena paper and census p18. pdftotext `-layout` also interleaves CRS. |
| Clipped Word cell | On UK p9, "23.2" sits beyond the cell border and page edge, so it is not rendered, but it is needed for the TOTAL. PyMuPDF drops it, pdftotext keeps it in the row, and pdfust Markdown emits it as a stray paragraph after the table. |
| Text outside the visible page | pdfust extracts off-page and outside-CropBox titles on Eurostat p2–3; PyMuPDF omits them. |
| Ligatures | pdfust drops the "fi" ligature in "Sofia" (unmapped glyph warning). |
| Fake bold in Japanese Word output | Repeated glyph draws come out as `宮宮城城県県…` in pdfust. |
| Kana chart | pdftotext and pdfust read "ha"/"he" plus the superscript note "i" as "hai"/"hei". All three extractors return hiragana ぺ in the katakana pe slot, where the page shows ペ. |
| Tables | pdfust finds none of the three W-4 wage tables. It drops spaces in shaded cells (`0.9190.9210.32`) and repeats merged-cell values. PyMuPDF splits decimals in census Table 1 (`0. 0049`). |

## Extraction health

`health` runs pdfust, pdftotext and PyMuPDF on every kept file. Each tool runs
sequentially in its own isolated subprocess. The table reports:

- non-space characters
- errors
- whitespace-free character-bigram F1 of pdfust against each other tool
- wall time, plus CPU time and peak RSS from `getrusage` (self + children) at
  process exit

**Results (2026-10-12):**

- No tool raised an error on any of the 40 files, including the AES-256 gazette.
- Agreement with pdftotext is ≥ 0.93 on 34 documents.
- **Lowest agreement:** Arabic Wikipedia 0.77, Hebrew 0.85, USACE PowerPoint
  slides 0.89, census InDesign 0.91, RCEWA Word table 0.92, and the Blue Book
  Paper Capture OCR scan 0.93.
- The RTL scores reflect visual-versus-logical order differences, and
  pdftotext emits about 9% more non-space characters.
- pdfust finished each file in 0.08–0.62 s wall time with 84–286 MiB peak RSS
  (Python + pdfust, including interpreter start).

Higher RSS was the Census InDesign file at 286 MiB and the 1040 Tax Table at
204 MiB. These are local CPU measurements on dev04, one process at a time.

## Not obtained

- **LuaTeX and XeTeX output:** arXiv compiles with pdfTeX, and no
  clearly licensed LuaTeX/XeTeX PDF was found within the request budget.
- **A natural (non-example) PDF 2.0 file.**
- **Vertical CJK with Identity-V, ABBYY FineReader layers, and JBIG2 scans:**
  none appeared in the Commons metadata samples.
- **Filled AcroForm values:** all three forms are blank.
- **Direct downloads:** crsreports.congress.gov returned 403, so the
  EveryCRSReport mirror of the same CRS product was used instead. The
  Gutenberg file needed a second attempt after a 503.
