# Rich PDF to Markdown feature study

- Run at: 2026-10-08 00:51 UTC
- Source commit: 615465ec20959cd4c4715cbf5ae639e7bad95578
- Environment: Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44 / Python 3.14.7
- Versions: pdfust 0.13.0, pymupdf 1.28.2, pymupdf4llm 1.28.2, pymupdf-layout 1.28.2, pypdf 6.15.0, pdfplumber 0.11.10, markdown-it-py 4.2.0, mdit-py-plugins 0.6.1, pdfust-fonts-ar not installed, pdfust-fonts-he not installed, pdfust-fonts-hi not installed, pdfust-fonts-jp not installed, pdfust-fonts-ko not installed, pdfust-fonts-th not installed, pdfust-fonts-zh-cn not installed, pdfust-fonts-zh-tw not installed
- Repetitions: 3
- OCR: disabled
- Details: Full JSON and output artifacts are generated locally and ignored by Git

Reproduce: `uv sync --group bench-rich && uv run python -m bench.features`.
Optional Docling/Marker runs: see `bench/MODEL_BENCHMARKS.md`; their original run metadata
and model fingerprints are retained separately in the JSON, alongside the earlier measurements.
Only summaries and the compact timing/hash baseline are committed. Full JSON, source copies,
raw outputs, structured sidecars, images, and logs are ignored local artifacts produced by the runners.
One warmup plus median fresh-document conversion timings. Imports/model initialization occur
before or during warmup. Page OCR is disabled; the Docling formula mode separately runs recognition.
Source generation, syntax parsing, hashing, artifact serialization, and validation
are outside the timer. Image embedding is enabled for PyMuPDF4LLM, so its output cost differs
from converters that omit images. Timings across these tools are not equivalent-work rankings.

PyMuPDF, pypdf, and pdfplumber provide plain-text baselines here; they are not Markdown converters.
The JSON sidecar retains exact versions/options, source inventories, warnings, and literal probes.
Raw `.out` files contain the full unmodified UTF-8 result, including multilingual fixture data.

Syntax counts establish what markup was emitted, not whether the feature was reconstructed correctly.
Text checks are strict substring probes of parsed text; they are not semantic or visual quality scores.
Internal links need a target that resolves; a fragment-looking URL alone is insufficient.
Math requires checking the reference expression, not counting symbols or math delimiters.
Review table cell positions, merged spans, alignment, and image/caption association in the raw outputs.

## text-structure-and-literals

headings, bold, italic, code, lists, nesting, Markdown escaping

Standard 14 font variants carry styling names, but no embedded font metadata. The final line contains literal Markdown punctuation, not source markup.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/text-structure-and-literals.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 1.385 | 3/4 | 1/0/1/0/2/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 1.419 | 3/4 | 1/0/1/0/2/0/0/0/0/0 | repeatable |
| pymupdf | text | 2.045 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.925 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 14.408 | 3/4 | 1/1/2/1/2/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 83.114 | 3/4 | 1/1/2/1/2/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 125.662 | 3/4 | 1/1/2/1/2/0/0/0/0/0 | repeatable |
| pypdf | text | 1.213 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 5.908 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |

## positioned-math

fractions, superscripts, LaTeX reconstruction

The fraction bar is a drawing; the PDF has no equation source. Human formula reference is supplied.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/positioned-math.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.512 | 1/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.466 | 1/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.967 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.683 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 4.428 | 1/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 81.057 | 1/1 | 0/0/0/0/0/0/1/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 90.757 | 1/1 | 0/0/0/0/0/0/1/0/0/0 | repeatable |
| pypdf | text | 1.295 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 2.633 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |

## math-actualtext

ActualText, math source hint

ActualText explicitly contains LaTeX, while painted glyphs say visual-formula. Recovering the hint and producing a math block are separate observations.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/math-actualtext.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.495 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.482 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.968 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.644 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 3.475 | 1/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 78.048 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 87.142 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 1.325 | 0/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 3.027 | 0/1 | -/-/-/-/-/-/-/-/-/- | repeatable |

## accessible-actualtext

ActualText, accessible text

ActualText differs intentionally from painted text; check which one survives.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/accessible-actualtext.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.299 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.415 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 1.298 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.653 | 1/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 3.013 | 1/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 76.672 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 78.485 | 0/1 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 1.269 | 0/1 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 2.903 | 0/1 | -/-/-/-/-/-/-/-/-/- | repeatable |

## two-column-order

columns, reading order

Content stream alternates columns. Logical reference is all left lines, then all right lines.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/two-column-order.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 5.924 | 0/0 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 6.425 | 0/0 | 0/0/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf | text | 1.195 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.026 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 18.857 | 0/0 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 97.609 | 0/0 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 118.471 | 0/0 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 2.867 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 20.102 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## unicode-cmap-and-emoji

UTF-16BE ToUnicode, non-BMP scalars, emoji, combining marks

Invisible text with ToUnicode CMaps: supplementary scalars use UTF-16 surrogate pairs. Includes a skin-tone/ZWJ emoji, flag regional indicators, variation selector, and decomposed accent. This tests Unicode decoding; it does not test rendering a color emoji font.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/unicode-cmap-and-emoji.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.569 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.545 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 1.070 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.068 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 4.232 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 88.404 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 85.227 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 1.501 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 4.552 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |

## table-bordered

tables, table alignment, cell emphasis, cell escaping, empty cells, merged cells

Three rows/columns; last numeric cell is genuinely empty. Alignment is visual geometry, not PDF semantics. Bold/italic use non-embedded Standard 14 fonts. The merged case spans the first two header slots.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/table-bordered.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.926 | 5/5 | 0/0/0/0/0/1/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.878 | 5/5 | 0/0/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf | text | 2.624 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 2.202 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 8.691 | 3/5 | 1/0/1/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 140.731 | 3/5 | 1/3/1/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 147.085 | 5/5 | 1/0/0/0/0/0/0/0/1/0 | repeatable |
| pypdf | text | 1.401 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 3.437 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |

## table-borderless

tables, table alignment, cell emphasis, cell escaping, empty cells, merged cells

Three rows/columns; last numeric cell is genuinely empty. Alignment is visual geometry, not PDF semantics. Bold/italic use non-embedded Standard 14 fonts. The merged case spans the first two header slots.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/table-borderless.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.560 | 5/5 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.574 | 5/5 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 1.858 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.568 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 5.323 | 5/5 | 1/3/1/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 136.005 | 3/5 | 1/3/1/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 160.592 | 5/5 | 1/0/0/0/0/0/0/0/1/0 | repeatable |
| pypdf | text | 1.462 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 3.694 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |

## table-merged

tables, table alignment, cell emphasis, cell escaping, empty cells, merged cells

Three rows/columns; last numeric cell is genuinely empty. Alignment is visual geometry, not PDF semantics. Bold/italic use non-embedded Standard 14 fonts. The merged case spans the first two header slots.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/table-merged.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.725 | 5/5 | 0/0/0/0/0/1/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.956 | 5/5 | 0/0/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf | text | 1.946 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.868 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 9.337 | 3/5 | 1/0/1/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 136.256 | 3/5 | 1/2/1/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 159.337 | 5/5 | 1/0/0/0/0/0/0/0/1/0 | repeatable |
| pypdf | text | 1.179 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 3.563 | 5/5 | -/-/-/-/-/-/-/-/-/- | repeatable |

## links-and-outline

URI links, internal links, named destinations, bookmarks

Link targets exist only in annotations, not visible text. A bookmark is not body text. Preserving an internal link requires both a generated destination and a link that resolves to it.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/links-and-outline.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.801 | 4/4 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.815 | 4/4 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 1.043 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.032 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 6.385 | 4/4 | 1/0/0/0/0/0/0/0/0/1 | repeatable |
| pymupdf4llm-layout | markdown | 158.102 | 4/4 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 181.490 | 4/4 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 1.494 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 3.123 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |

## images-and-vectors

raster images, vector graphics, captions, image-only pages, OCR

One 2x2 RGB image enlarged on the page and one stroked rectangle. No OCR text. An image reference does not establish source-image preservation or correct caption association.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/images-and-vectors.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.683 | 2/2 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.649 | 2/2 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.824 | 2/2 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.699 | 2/2 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 6.692 | 2/2 | 0/0/0/0/0/0/1/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 78.488 | 2/2 | 1/0/0/0/0/0/2/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 81.712 | 2/2 | 1/0/0/0/0/0/2/0/0/0 | repeatable |
| pypdf | text | 0.673 | 2/2 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 2.088 | 2/2 | -/-/-/-/-/-/-/-/-/- | repeatable |

## image-only

raster images, vector graphics, captions, image-only pages, OCR

One 2x2 RGB image enlarged on the page and one stroked rectangle. No OCR text. An image reference does not establish source-image preservation or correct caption association.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/image-only.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.225 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.219 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.252 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.240 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 5.479 | 0/0 | 0/0/0/0/0/0/1/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 65.922 | 0/0 | 0/0/0/0/0/0/2/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 63.922 | 0/0 | 0/0/0/0/0/0/2/0/0/0 | repeatable |
| pypdf | text | 0.559 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 1.226 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## table-borderless-aligned

borderless tables, aligned labels

Four complete rows with fixed left edges and regular leading. Contrast with the ragged, centered case.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/table-borderless-aligned.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.633 | 6/6 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.720 | 6/6 | 0/0/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf | text | 0.899 | 6/6 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.891 | 6/6 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 6.087 | 6/6 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 144.430 | 6/6 | 1/0/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 137.081 | 6/6 | 1/0/0/0/0/0/0/0/1/0 | repeatable |
| pypdf | text | 1.160 | 6/6 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 3.586 | 6/6 | -/-/-/-/-/-/-/-/-/- | repeatable |

## rotated-columns

rotation, columns, reading order

The two-column fixture rotated 90 degrees; logical column order is unchanged.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/rotated-columns.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 4.607 | 0/0 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 4.636 | 0/0 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.903 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.912 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 18.027 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 102.591 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 117.857 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 4.572 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 17.154 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## footnotes-and-page-furniture

footnotes, superscripts, headers, footers, page numbers

The superscript marker and footnote are positioned text, without a semantic footnote association. One page tests retention; repeated-header removal requires a separate multipage policy.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/footnotes-and-page-furniture.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.740 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.783 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.754 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.693 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 5.417 | 4/4 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 82.075 | 4/4 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 116.045 | 4/4 | 1/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 2.683 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 9.985 | 4/4 | -/-/-/-/-/-/-/-/-/- | repeatable |

## rtl-visual-glyph-order

RTL, bidi, embedded numeric token

Invisible visual-order Hebrew and Arabic glyph runs; logical reference strings are supplied. This tests extraction order, not Arabic shaping or paragraph-level bidi layout.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/rtl-visual-glyph-order.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.660 | 3/3 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.583 | 3/3 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.880 | 2/3 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.914 | 2/3 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 3.779 | 2/3 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 90.926 | 2/3 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 83.850 | 2/3 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 1.977 | 2/3 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 5.935 | 0/3 | -/-/-/-/-/-/-/-/-/- | repeatable |

## tagged-reading-order

tagged PDF, logical reading order

Contrived tagged page: structure-tree order SECOND/FIRST differs from visual FIRST/SECOND. Stream order also matches tag order, so matching the reference does not prove tags were used.

Source: Repository-authored synthetic PDF; repository MIT license

Local input after running: `feature-outputs/tagged-reading-order.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.858 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.656 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 1.123 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.135 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 6.485 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 93.109 | 0/0 | 2/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 82.806 | 0/0 | 2/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 0.862 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 2.700 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## corpus-usrguide

LaTeX producer, embedded fonts, displayed math, superscripts, code

Original page 23 contains a displayed fraction and superscripts; source expression requires human review.

Source: tests/assets/real_world/usrguide.pdf; source and license in that directory's README

Local input after running: `feature-outputs/corpus-usrguide.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 11.724 | 0/0 | 0/0/1/0/3/0/0/1/0/0 | repeatable |
| pdfust-text-tables | markdown | 11.543 | 0/0 | 0/0/1/0/3/0/0/1/0/0 | repeatable |
| pymupdf | text | 6.586 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 7.349 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 78.934 | 0/0 | 0/0/17/36/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 153.277 | 0/0 | 0/0/13/35/1/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 231.829 | 0/0 | 0/0/13/35/1/0/0/0/0/0 | repeatable |
| pypdf | text | 29.247 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 96.008 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## corpus-senate-expenditures

rotation, merged headers, hybrid tables

Independent rotated report with merged header and missing row rules.

Source: tests/assets/real_world/senate-expenditures.pdf; source and license in that directory's README

Local input after running: `feature-outputs/corpus-senate-expenditures.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 10.555 | 0/0 | 1/0/0/0/0/1/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 11.567 | 0/0 | 1/0/0/0/0/2/0/0/0/0 | repeatable |
| pymupdf | text | 5.350 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 5.027 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 899.848 | 0/0 | 0/8/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 378.157 | 0/0 | 0/13/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 946.745 | 0/0 | 0/0/0/0/0/0/0/0/1/0 | repeatable |
| pypdf | text | 87.026 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 262.146 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## corpus-nics-background-checks-2015-11

dense tables, numeric alignment

Independent dense 25-column report; exact row/cell correctness requires review.

Source: tests/assets/real_world/nics-background-checks-2015-11.pdf; source and license in that directory's README

Local input after running: `feature-outputs/corpus-nics-background-checks-2015-11.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 44.912 | 0/0 | 0/2/0/0/0/1/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 50.564 | 0/0 | 0/2/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf | text | 6.094 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 5.699 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 2484.910 | 0/0 | 0/27/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 2326.888 | 0/0 | 2/19/0/0/0/1/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 4911.334 | 0/0 | 2/2/0/0/0/0/0/0/1/0 | repeatable |
| pypdf | text | 88.213 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 249.994 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## corpus-pdfium-type3

Type 3 fonts, missing Unicode mapping

Glyph programs have no ToUnicode; pdfust has a documented upstream-linked extraction gap.

Source: tests/assets/real_world/pdfium-type3.pdf; source and license in that directory's README

Local input after running: `feature-outputs/corpus-pdfium-type3.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 0.253 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 0.229 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 0.276 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 0.268 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 2.422 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 74.821 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 77.023 | 0/0 | 0/0/0/0/0/0/0/0/0/0 | repeatable |
| pypdf | text | 0.985 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 1.335 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## corpus-f1040

form fields, widgets, form labels

IRS form with widget annotations. Field metadata and visible labels are different source objects.

Source: tests/assets/real_world/f1040.pdf; source and license in that directory's README

Local input after running: `feature-outputs/corpus-f1040.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 19.051 | 0/0 | 1/0/0/0/0/1/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 19.625 | 0/0 | 1/0/0/0/0/3/0/0/0/0 | repeatable |
| pymupdf | text | 23.140 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 27.572 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 1878.959 | 0/0 | 0/1565/0/0/0/3/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 1110.355 | 0/0 | 0/103/0/0/0/3/0/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 3269.465 | 0/0 | 0/0/0/0/0/0/0/0/9/0 | repeatable |
| pypdf | text | 74.822 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 231.598 | 0/0 | -/-/-/-/-/-/-/-/-/- | repeatable |

## omml-equations

OMML producer, fractions, superscripts, Unicode

Repository-authored DOCX with native OMML exported through LibreOffice. The embedded PDF glyph layout is the input, not the original OMML XML.

Source: bench/assets/rich/README.md; generated source and export provenance

Local input after running: `feature-outputs/omml-equations.pdf`

| Adapter | Kind | Median ms | Text probes | H/B/I/code/list/table/image/math/HTML/link | Result |
|---|---|---:|---:|---|---|
| pdfust | markdown | 1.761 | 7/8 | 1/1/4/0/0/0/0/0/0/0 | repeatable |
| pdfust-text-tables | markdown | 1.767 | 7/8 | 1/1/4/0/0/0/0/0/0/0 | repeatable |
| pymupdf | text | 1.240 | 8/8 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf-actualtext | text | 1.222 | 8/8 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pymupdf4llm-legacy | markdown | 9.067 | 8/8 | 1/2/4/0/0/0/0/0/0/0 | repeatable |
| pymupdf4llm-layout | markdown | 85.675 | 7/8 | 1/2/1/0/0/0/1/0/0/0 | repeatable |
| pymupdf4llm-html-tables | markdown | 89.068 | 7/8 | 1/2/1/0/0/0/1/0/0/0 | repeatable |
| pypdf | text | 8.335 | 7/8 | -/-/-/-/-/-/-/-/-/- | repeatable |
| pdfplumber | text | 17.470 | 7/8 | -/-/-/-/-/-/-/-/-/- | repeatable |
