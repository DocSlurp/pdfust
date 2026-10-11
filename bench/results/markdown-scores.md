# PDF-to-Markdown element score matrix

- Generated: 2026-10-11T18:38:07+00:00; scorer commit `12c38e9633cd`. The resource table records the checkout that produced each converter's outputs.
- Inputs: 27 synthetic PDFs with exact ground truth (`bench/markdown_score_cases.py`). Corpus pages are excluded because they lack structural truth.

Scores are 0-100. Each check scores 0-1, a category is the mean of its checks, and **Overall** is the unweighted mean of categories. Outputs are parsed as CommonMark + GFM tables + `$` math + raw HTML, the way a Markdown consumer reads them. Plain-text extractors (marked †) are floors: they emit no Markdown, so only text, order, and accidental syntax can score. The fixtures are small and each pins a specific behavior; treat a gap of a few points as noise, not a ranking.

| Tool | Overall | Text (76) | Order (3) | Headings (3) | Emphasis (7) | Code (4) | Lists (11) | Escaping (6) | Tables (6) | Math (6) | Images (7) | Links (7) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pymupdf4llm-legacy | **71** | 92 | 31 | 100 | 100 | 80 | 100 | 50 | 41 | 46 | 86 | 57 |
| pymupdf4llm-layout | **71** | 87 | 33 | 100 | 100 | 80 | 100 | 50 | 89 | 42 | 100 | 0 |
| marker-fast | **69** | 71 | 98 | 61 | 43 | 0 | 86 | 83 | 91 | 29 | 100 | 93 |
| pylopdf-text-tables | **48** | 99 | 64 | 100 | 29 | 0 | 93 | 50 | 83 | 12 | 0 | 0 |
| docling | **48** | 93 | 62 | 61 | 0 | 0 | 93 | 67 | 36 | 17 | 100 | 0 |
| docling-formulas | **48** | 93 | 62 | 61 | 0 | 0 | 93 | 67 | 36 | 17 | 100 | 0 |
| pylopdf | **45** | 99 | 67 | 100 | 29 | 0 | 93 | 50 | 50 | 12 | 0 | 0 |
| pymupdf † | **28** | 97 | 96 | 0 | 0 | 0 | 52 | 50 | 0 | 12 | 0 | 0 |
| pypdf † | **27** | 95 | 96 | 0 | 0 | 0 | 52 | 50 | 0 | 0 | 0 | 0 |
| markitdown | **26** | 84 | 33 | 0 | 0 | 0 | 52 | 50 | 69 | 0 | 0 | 0 |
| pdfplumber † | **21** | 92 | 33 | 0 | 0 | 0 | 52 | 50 | 0 | 0 | 0 | 0 |

Numbers in column headers are check counts.

## What each category checks

| Category | Checks |
|---|---|
| Text | Each expected string appears in the rendered text (NFC, collapsed whitespace; Unicode, RTL, ActualText). |
| Order | Consecutive reference tokens appear in order (two-column, rotated, and tagged pages). |
| Headings | Heading-text F1 (false headings cost precision) plus relative levels across 26/18/14 pt tiers. |
| Emphasis | 1 for an exact `**`/`*`/`<b>` span; 0.5 when the style also covers neighbouring text. |
| Code | Courier tokens in inline code; a code block exists and keeps relative indentation. |
| Lists | Each item is a list item (0.5), with the right ordered/bullet type (+0.25) and depth (+0.25). |
| Escaping | Literal `*`, `[]`, `#`, `<tag>`, `\` survive rendering, and no false emphasis is created. |
| Tables | Best position-aware cell F1 over emitted GFM/HTML tables; a merged slot accepts repeat/empty/colspan. |
| Math | 1: exact LaTeX in math markup, or exact `<sup>`/`^`/Unicode scripts; 0.75: bare exact LaTeX; 0.5: `\frac` structure; 0.25: equation only as an image. |
| Images | References emitted, assets resolve (decodable data URI or existing file), image precedes caption. |
| Links | URI label with exact href; internal links resolve to an emitted anchor (0.5 if unresolved). |

## Resource use

Wall and CPU time sum all cases after one unmeasured warmup conversion; initialization is separate. CPU time is `time.process_time()` across all threads of the converter process. Peak RSS is `getrusage(RUSAGE_SELF).ru_maxrss` for the whole converter process, including model loading. There is one measured conversion per case. Timings are not equivalent-work comparisons, because some tools embed images or run layout models.

| Tool | Version | Options | Source | Init (ms) | Wall (ms) | Median (ms) | CPU (ms) | RSS (MiB) | Errors |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| pymupdf4llm-legacy | pymupdf4llm 1.28.2, pymupdf 1.28.2, pymupdf-layout 1.28.2 | `use_layout(False); embed_images=True` | `12c38e9633cd` | 464 | 219 | 6.9 | 348 | 158 | 0 |
| pymupdf4llm-layout | pymupdf4llm 1.28.2, pymupdf 1.28.2, pymupdf-layout 1.28.2 | `use_layout(True); embed_images=True; use_ocr=False` | `12c38e9633cd` | 463 | 2549 | 78.1 | 15972 | 370 | 0 |
| marker-fast | marker-pdf 2.0.0, surya-ocr 0.22.1, torch 2.14.1+cpu | `mode=fast; disable_ocr=True; use_llm=False; pdftext_workers=1; torch threads 4` | `12c38e9633cd` | 4099 | 7299 | 255.7 | 1391 | 594 | 0 |
| pylopdf-text-tables | pylopdf 0.13.0 | `Document.to_markdown(table_strategy='text')` | `12c38e9633cd` | 18 | 285 | 9.0 | 296 | 92 | 0 |
| docling | docling 2.135.0, docling-core 2.100.0, torch 2.14.1+cpu | `do_ocr=False; do_formula_enrichment=False; embedded images; CPU 4 threads` | `12c38e9633cd` | 5313 | 25690 | 794.5 | 97125 | 1426 | 0 |
| docling-formulas | docling 2.135.0, docling-core 2.100.0, torch 2.14.1+cpu | `do_ocr=False; do_formula_enrichment=True; embedded images; CPU 4 threads` | `12c38e9633cd` | 5827 | 25682 | 792.4 | 96857 | 1579 | 0 |
| pylopdf | pylopdf 0.13.0 | `Document.to_markdown(table_strategy='lines')` | `12c38e9633cd` | 18 | 283 | 9.1 | 294 | 92 | 0 |
| pymupdf | pymupdf 1.28.2 | `Page.get_text() plain text` | `12c38e9633cd` | 73 | 31 | 1.0 | 31 | 59 | 0 |
| pypdf | pypdf 6.15.0 | `Page.extract_text() plain text` | `12c38e9633cd` | 63 | 39 | 1.1 | 39 | 42 | 0 |
| markitdown | markitdown 0.1.8, pdfminer.six 20260107 | `MarkItDown(enable_plugins=False).convert()` | `12c38e9633cd` | 206 | 379 | 11.5 | 1513 | 100 | 0 |
| pdfplumber | pdfplumber 0.11.10 | `Page.extract_text() plain text` | `12c38e9633cd` | 56 | 141 | 3.7 | 141 | 42 | 0 |

Machine: Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44; converters ran sequentially, one process per tool.

## Per-case scores

Mean of all checks in each case, per tool.

| Case | pymupdf4llm-legacy | pymupdf4llm-layout | marker-fast | pylopdf-text-tables | docling | docling-formulas | pylopdf | pymupdf | pypdf | markitdown | pdfplumber |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| text-structure-and-literals | 76 | 76 | 76 | 57 | 61 | 61 | 57 | 51 | 51 | 51 | 51 |
| positioned-math | 50 | 62 | 50 | 50 | 62 | 62 | 50 | 50 | 50 | 50 | 50 |
| math-actualtext | 88 | 0 | 88 | 88 | 88 | 88 | 88 | 88 | 0 | 0 | 0 |
| accessible-actualtext | 100 | 0 | 100 | 100 | 100 | 100 | 100 | 100 | 0 | 0 | 0 |
| two-column-order | 93 | 100 | 93 | 93 | 87 | 87 | 100 | 93 | 93 | 93 | 93 |
| unicode-cmap-and-emoji | 100 | 100 | 0 | 100 | 75 | 75 | 100 | 100 | 100 | 100 | 100 |
| table-bordered | 63 | 63 | 80 | 100 | 100 | 100 | 100 | 83 | 83 | 63 | 83 |
| table-borderless | 83 | 63 | 80 | 83 | 83 | 83 | 83 | 83 | 83 | 63 | 83 |
| table-merged | 61 | 63 | 81 | 100 | 86 | 86 | 100 | 83 | 83 | 63 | 83 |
| links-and-outline | 71 | 57 | 100 | 57 | 57 | 57 | 57 | 57 | 57 | 57 | 57 |
| images-and-vectors | 100 | 100 | 100 | 50 | 100 | 100 | 50 | 50 | 50 | 50 | 50 |
| image-only | 100 | 100 | 100 | 0 | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| table-borderless-aligned | 86 | 100 | 100 | 100 | 86 | 86 | 86 | 86 | 86 | 86 | 86 |
| rotated-columns | 0 | 0 | 100 | 100 | 100 | 100 | 100 | 93 | 93 | 7 | 7 |
| footnotes-and-page-furniture | 100 | 100 | 50 | 100 | 50 | 50 | 100 | 100 | 100 | 100 | 100 |
| rtl-visual-glyph-order | 67 | 67 | 0 | 100 | 100 | 100 | 100 | 67 | 67 | 0 | 0 |
| tagged-reading-order | 0 | 0 | 100 | 0 | 0 | 0 | 0 | 100 | 100 | 0 | 0 |
| omml-equations | 91 | 93 | 0 | 91 | 64 | 64 | 91 | 73 | 73 | 73 | 73 |
| score-headings | 100 | 100 | 79 | 100 | 79 | 79 | 100 | 50 | 50 | 50 | 50 |
| score-inline-emphasis | 100 | 100 | 75 | 50 | 50 | 50 | 50 | 50 | 50 | 50 | 50 |
| score-lists | 100 | 100 | 94 | 96 | 96 | 96 | 96 | 58 | 58 | 58 | 58 |
| score-code-block | 73 | 73 | 33 | 33 | 33 | 33 | 33 | 33 | 33 | 33 | 33 |
| score-links | 88 | 50 | 94 | 50 | 50 | 50 | 50 | 50 | 50 | 50 | 50 |
| score-table-bordered | 100 | 100 | 67 | 100 | 100 | 100 | 100 | 67 | 67 | 97 | 67 |
| score-table-borderless | 67 | 100 | 67 | 100 | 67 | 67 | 67 | 67 | 67 | 97 | 67 |
| score-math-scripts | 80 | 80 | 60 | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| score-images | 80 | 100 | 100 | 40 | 100 | 100 | 40 | 40 | 40 | 40 | 40 |

Reproduce with the commands in the `bench/markdown_scores.py` docstring. Inputs, raw outputs, image assets, `truth.json`, and `scores.json` stay in the ignored `bench/results/pdf-master-artifacts/markdown-scores/` directory.
