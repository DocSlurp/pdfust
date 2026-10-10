# jev-pdf

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/justsml/jev-pdf/blob/main/LICENSE)

**PDF editing, rendering, extraction, and generation for Python — a
pymupdf-style API on a pure-Rust core, MIT licensed, with no mandatory Python
dependencies.**

[Documentation](https://pylopdf.haya.works/) ·
[Getting started](https://pylopdf.haya.works/getting-started/) ·
[API reference](https://pylopdf.haya.works/api/) ·
[pymupdf migration guide](https://pylopdf.haya.works/migration/) ·
[Benchmarks](https://pylopdf.haya.works/benchmarks/)

jev-pdf combines the 2026 Rust PDF ecosystem behind one Python API:
[lopdf](https://github.com/J-F-Liu/lopdf) for editing,
[hayro](https://github.com/LaurenzV/hayro) (the pure-Rust PDF renderer adopted
by Typst) for rendering and positioned extraction, and
[krilla](https://github.com/LaurenzV/krilla) with
[HarfRust](https://github.com/harfbuzz/harfrust) for shaped, subset-embedded
text and form appearances.

## Why jev-pdf?

| | jev-pdf | pymupdf | pypdf | pypdfium2 | pdf_oxide | pikepdf |
|---|---|---|---|---|---|---|
| License | **MIT** | AGPL / commercial | BSD | Apache/BSD | MIT/Apache-2.0 | MPL-2.0 |
| Wheel size (MiB) | **~5.0–5.8** | ~17.5–24.7 | small (pure Python) | ~2.7–5.0 | ~9.7–10.9 | ~1.9–4.6 |
| Editing (merge / split / rotate / outlines) | ✅ | ✅ | ✅ | limited | ✅ | ✅ (structure-focused) |
| Rendering (PNG / SVG) | ✅ | ✅ | ❌ | ✅ (PNG) | ❌ | ❌ (docs point to other tools) |
| Text extraction | ✅ (positioned text, tables, Markdown) | ✅ (advanced) | ✅ | ✅ | ✅ (advanced, table detection / Markdown) | ❌ (docs point to other tools) |
| Encryption (AES-256) | ✅ read & write | ✅ | ✅ | read only | undocumented | ✅ (via qpdf) |
| Locale-aware multilingual fonts | ✅ (optional extras) | ✅ | — | manual | — | — |
| Implementation | **pure Rust** | C/C++ | Python | C++ (PDFium) | Rust | C++ (qpdf) |

Wheel sizes are the ranges of published files for pylopdf 0.10.0, pymupdf
1.28.0, pypdfium2 5.12.1, pdf-oxide 0.3.75, and pikepdf 10.10.0 on 2026-07-25.

- **AGPL-free**: covers the common pymupdf use cases under the MIT license
- **Small and self-contained**: fits size-constrained environments such as AWS
  Lambda and Cloudflare Workers
- **One wheel per platform**: abi3 covers CPython 3.10–3.14, plus a native
  `cp314t` wheel for free-threaded Python
- **Familiar**: the API is modeled after
  [pymupdf](https://github.com/pymupdf/PyMuPDF), with a
  [migration guide](https://pylopdf.haya.works/migration/)

## Install

```bash
pip install "jev-pdf @ git+https://github.com/justsml/jev-pdf.git"
```

Optional extras:

```bash
pip install "jev-pdf[jp] @ git+https://github.com/justsml/jev-pdf.git"    # Japanese rendering fallback and text generation
pip install "jev-pdf[ko] @ git+https://github.com/justsml/jev-pdf.git"    # Korean
pip install "jev-pdf[zh-cn] @ git+https://github.com/justsml/jev-pdf.git" # Simplified Chinese
pip install "jev-pdf[zh-tw] @ git+https://github.com/justsml/jev-pdf.git" # Traditional Chinese
pip install "jev-pdf[ar] @ git+https://github.com/justsml/jev-pdf.git"    # Arabic generation (also: he, hi, th)
pip install "jev-pdf[ocr] @ git+https://github.com/justsml/jev-pdf.git"   # offline PP-OCRv6 recognition, pure Rust,
                             # no system executables or network at runtime
```

The locale-specific CJK extras provide both non-embedded PDF fallback and
generation fonts. The `ar`, `he`, `hi`, and `th` extras provide generation
fonts for Arabic, Hebrew, Devanagari, and Thai. Choose `jp`, `ko`, `zh-cn`, or
`zh-tw` explicitly for the required regional glyph conventions; there is no
generic CJK font extra.

The repository is private; source installation requires authorized GitHub access
and a Rust toolchain. No `jev-pdf` package has been published. From a local
checkout, install with `uv sync` or `pip install .`; use `pip install ".[ocr]"`
for the optional OCR data package.

The public import is `jev_pdf`. The complete `pylopdf` import remains compatible
in the same wheel, with identical public classes, functions and constants.
Optional `pylopdf-fonts-*` and `pylopdf-ocr-models` data package names are unchanged.
Use a fresh environment or uninstall the separately installed `pylopdf`
distribution before migrating: both distributions provide the same `pylopdf`
module files. The new wheel supplies compatibility without requiring the old
distribution.
Upstream pylopdf documentation remains linked above as API background; the
private repository's README records this distribution and import migration.

## Quickstart

```python
import jev_pdf

doc = jev_pdf.open("input.pdf")              # or jev_pdf.open(stream=pdf_bytes)

# Extract: plain text, positioned words, search, tables, Markdown
text = doc.get_page_text(0)
words = doc[0].get_text("words")             # (x0, y0, x1, y1, word, block, line, word_no)
hits = doc[0].search_for("tax")              # case-insensitive, list[Rect]
tables = doc[0].find_tables()                # bordered grids incl. merged cells
markdown = doc.to_markdown()                 # RAG / LLM preprocessing
layout = doc[0].get_layout()                 # owned CPU snapshot; no rasterization
fields = layout.extract_fields([
    jev_pdf.FieldSpec("invoice_number", anchor="Invoice number", value_type="text"),
])                                          # ambiguous assignments abstain

# Render: PNG / SVG / raw pixels
png: bytes = doc.render_page(0, dpi=300)
batch = doc.render_pages([0, 1, 2], scale=2, workers=4)
svg: str = doc.render_page_svg(0)
pix = doc[0].get_pixmap(dpi=144)             # immutable RGBA8 for NumPy / PIL

# Edit: reorganize pages, merge documents
doc.delete_pages([1, 2])
doc.select([2, 0])                           # keep / reorder / duplicate
merged = jev_pdf.Document()
merged.insert_pdf(jev_pdf.open("a.pdf"))
merged.insert_pdf(jev_pdf.open("b.pdf"), from_page=0, to_page=2)

# Generate: images, overlays, shaped subset-embedded multilingual text
page = doc[0]
page.insert_image((72, 72, 200, 200), filename="logo.png")
page.show_pdf_page(page.rect, letterhead)    # vector overlay from another PDF
page.insert_text((40, 80), "社外秘", fontsize=20, color=(0.8, 0, 0))
page.insert_text((40, 120), "简体中文", fontsize=20, font_language="zh-CN")
page.replace_text("DRAFT", "FINAL")
page.add_highlight_annot(page.search_for("important"))

# Headers / footers / page numbers (standard-14 fonts)
for i, p in enumerate(doc):
    p.insert_text((p.rect.width - 90, p.rect.height - 30), f"Page {i + 1}", fontsize=9)

# Forms (AcroForm)
doc.set_form_field("customer", "Taro Yamada")
doc.set_form_field("agree", True)

# OCR: add a searchable text layer offline (pip install "jev-pdf[ocr] @ git+https://github.com/justsml/jev-pdf.git")
engine = jev_pdf.OcrEngine(threads=4)
page.apply_ocr(engine=engine)                # skips pages with existing text

# Save: optimized, or AES-256 encrypted
doc.save("out.pdf", garbage=True, deflate=True, object_streams=True)
doc.save("locked.pdf", user_pw="secret", permissions=jev_pdf.Permissions.PRINT)

# Encrypted input and fast probing
doc = jev_pdf.open("locked.pdf", password="secret")
info = jev_pdf.peek_metadata("input.pdf")    # page count / encryption, no full parse
```

The [getting started guide](https://pylopdf.haya.works/getting-started/)
walks through each area; the
[API reference](https://pylopdf.haya.works/api/) documents every method,
default, and resource boundary.

## Features

- **Editing** — merge, split, select/reorder, rotate, page boxes, blank and
  copied pages, table of contents, page labels, metadata, file attachments,
  AES-256 encrypted save, atomic file replacement
- **Extraction** — plain and positioned text (`words` / `blocks` / `dict`),
  case-insensitive search, bordered and opt-in borderless table detection with
  merged-cell reconstruction, image and vector-drawing extraction, Markdown
  conversion, vertical and rotated CJK reading order
- **Rendering** — PNG and SVG via hayro, page-region clips, DPI control,
  background fills, ordered parallel `render_pages`
- **Generation** — JPEG-passthrough/PNG image insertion, vector page overlays
  (`show_pdf_page`), HarfRust-shaped `insert_text` / `insert_textbox` with
  subset embedding and UAX #14 wrapping, highlight and link annotations,
  AcroForm filling with regenerated appearances, bounded simple-font text
  replacement
- **OCR** — offline PP-OCRv6 engine (`[ocr]` extra), positioned words,
  idempotent invisible searchable layers, clockwise rotation correction
- **Untrusted input policy** — `DocumentLimits.web()` bounds file size, pages,
  objects, decompression, glyph and output budgets in one opt-in profile;
  policy refusals raise typed `LimitError`; fixed implementation caps and
  allocation failures can raise `PdfError` without partial results ([security model](https://pylopdf.haya.works/security/))
- **WebAssembly** — a static PyEmscripten wheel runs on Cloudflare Python
  Workers, verified end-to-end every release
  ([guide](https://pylopdf.haya.works/wasm/))
- **Concurrency** — heavy operations release the GIL, distinct `Document`
  objects work in parallel, and a native `cp314t` wheel supports
  free-threaded Python 3.14
  ([contract](https://pylopdf.haya.works/concurrency/))

## Limitations

pylopdf documents its boundaries instead of guessing. Multicolumn reading
order follows deterministic whitespace-gutter rules; borderless table
detection is opt-in because aligned prose is geometrically ambiguous. CJK text
generation selects one font per run (not per-glyph fallback). Pure RTL lines
and lines with one Latin or numeric token bracketed by RTL text are restored to
logical Unicode order. Edge tokens, multiple tokens, and general mixed
bidirectional paragraph layout remain in producer visual order. Ruby, warichu,
and mixed-orientation Japanese typography are not interpreted semantically.
Typesetting, PDF/A output, and digital signatures are intentionally out of
scope — see the ecosystem recipes below. The
[API stability policy](https://pylopdf.haya.works/stability/) defines
what may change before and after v1.0.

## Ecosystem recipes

pylopdf stays a lightweight core; adjacent concerns pair with established
libraries. These recipes are covered by integration tests and detailed in the
[ecosystem guide](https://pylopdf.haya.works/ecosystem/).

**Typesetting and PDF/A output —
[typst](https://typst.app/)** (via
[typst-py](https://pypi.org/project/typst/)):

```python
import typst
import jev_pdf

pdf_bytes = typst.compile("report.typ")         # typesetting: typst
doc = jev_pdf.open(stream=pdf_bytes)            # editing / extraction: jev_pdf
pdf_a: bytes = typst.compile("report.typ", pdf_standards="a-2b")
```

**Digital signatures (PAdES) —
[pyHanko](https://pypi.org/project/pyHanko/)** (MIT), which signs with an
incremental update so pylopdf's bytes remain untouched:

```python
import io
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers

signer = signers.SimpleSigner.load("key.pem", "cert.pem")
out = signers.sign_pdf(
    IncrementalPdfFileWriter(io.BytesIO(doc.tobytes())),
    signers.PdfSignatureMetadata(field_name="Signature1"),
    signer=signer,
)
```

Validating existing PDFs against PDF/A remains
[veraPDF](https://verapdf.org/)'s job.

## Benchmarks

A reproducible benchmark suite ships with the repository — same corpus, same
tasks, medians, and wins and losses published as-is:
[latest results](https://github.com/justsml/jev-pdf/blob/main/bench/results/latest.md),
[free-threaded extraction](https://github.com/justsml/jev-pdf/blob/main/bench/results/free-threaded-latest.md),
and the [native OCR report](https://github.com/justsml/jev-pdf/blob/main/bench/results/ocr-latest.md)
with strict and NFKC character error rates on licensed Japanese fixtures.

```bash
uv sync --all-extras --group bench && uv run python bench/run.py
```

Measure end-to-end Markdown and `words` / `blocks` / `dict` extraction separately:

```bash
uv sync && uv run python bench/layout.py
# Save a baseline before optimizing, then compare the candidate checkout:
uv run python bench/layout.py --output /tmp/layout-baseline.json
uv run python bench/layout.py --baseline /tmp/layout-baseline.json
```

The runner writes `bench/results/layout-latest.md` and a JSON sidecar. It uses
four existing corpus PDFs and synthetic ASCII / Unicode OCR-text documents with
tables at 1, 8, and 16 pages. Fresh-document timings include opening and closing;
reused-document timings repeat each task after warmup. Complete output hashes
must match before reporting a baseline speedup. Use the same environment and
repetition count for both runs. `--synthetic-only` runs without the corpus, and
`--repetitions` defaults to five. Fixture generation and output hashing are
outside the timed region.

Compare rich-content conversion behavior separately:

```bash
uv sync --group bench-rich && uv run python -m bench.features
```

The [feature map](bench/FEATURE_MAP.md) describes Markdown policies and review
criteria for math, Unicode/emoji, images, table spans/alignment, links, reading
order, and document metadata. The study retains input PDFs and complete outputs
from five libraries with explicit options, including PyMuPDF4LLM's legacy,
layout, and HTML table modes. Parsed syntax probes help find losses and changes;
they do not certify semantic correctness. [Initial findings](bench/FINDINGS.md)
document concrete differences. OCR and formula-recognition models
remain separate workloads. Results are written to `bench/results/features-latest.{md,json}`.
The [optional CPU model study](bench/MODEL_BENCHMARKS.md) adds Docling with
formula enrichment off/on and Marker in OCR-disabled fast mode on the same
inputs. It retains structured artifacts and image files alongside Markdown in
`bench/results/features-models.{md,json}`, with separate run provenance and
model fingerprints.
Only Markdown summaries and the compact layout timing/hash baseline are stored
in Git. Full feature JSON, source copies, raw outputs, model sidecars, images,
and logs are generated locally and ignored; run the documented commands to
inspect them.

## Experimental relationship decisions (opt-in)

The ongoing [P003 decision-model comparison](bench/results/decision-p003.md)
reports fresh natural-document quality, pages/minute, pages/API USD, and CPU/RAM
measurements. It separates source-ID assembly, image transcription, admission
gates, and incremental repair so their different output contracts stay visible.

First P003 transcription screens on the same 16 natural DEV pages (53 tables,
2,333 reference cells), using fixed 1024 px detector crops:

| Model | Outputs / 16 | Complete tables / 53 | Strict cells / 2,333 | Pages/min | Pages/API USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Haiku 5.5 | 15 | 3 | 393 | 8.49 | 1,822.07 |
| GPT-6 Luna | 16 | 3 | 784 | 4.19 | 1,234.11 |
| Gemma 4 26B A4B | 12 | 3 | 201 | 1.08 | 4,945.25 |
| Gemma 4 31B | 14 | 3 | 264 | 2.60 | 5,755.63 |
| Ministral 14B | 13 | 2 | 263 | 4.95 | 3,130.72 |
| Ministral 8B | 12 | 2 | 252 | 6.84 | 3,860.07 |

These are single serial runs. Pages/API USD counts operational outputs, including
empty negative pages, and does not imply correct extraction. Qwen 3.5 9B and
Gemini 3.5 Flash Lite had provider-route failures; their failed attempts and
unresolved reservations are included in the [full P003 report](bench/results/decision-p003.md).
Luna costs include independently verified BYOK upstream charges. The earlier
matched Sonnet run recovered 982 strict cells and five complete tables; identical-request repeats and a new P003 run fall near 289 when dense-page outputs overlap. The best run is not a stable baseline.

A separate [29-arm decision-role screen](bench/results/p003-incremental-screen.md)
uses frozen Luna/Sonnet candidates. Rates below measure only candidate selection,
including artifact processing; both original extractions are excluded. All
quality scores retain the same sixteen-page denominator.

| Selector | Strict cells / 2,333 | Complete tables / 53 | Incremental pages/min | Incremental pages/API USD |
| --- | ---: | ---: | ---: | ---: |
| Frozen Luna fallback, no selector | 784 | 3 | Not measured | No new calls |
| PPLX, text only | 784 | 3 | 25.39 | 29,625 |
| PPLX, 512 px source crop | **981** | **5** | 20.24 | 26,055 |
| Luna Decisions, 512 px source crop | 682 | 3 | 21.34 | 6,470 |

PPLX image selection costs USD 0.00061408 in additional provider-reported charges.
It improves the Luna fallback while remaining just below the existing Sonnet
candidate; this does not establish a cheaper complete pipeline. None of fifteen
bounded row-boundary repair arms improves its 384-cell source-ID baseline.
Model/role combinations, failures, CPU/RAM, provider cache counters, and full
quality scores remain visible in the linked report.

The next [spatial and representation screen](bench/results/p003-spatial-screen.md)
retains all 16 pages and measures complete-pipeline costs under concurrent load:

| Model and treatment | Outputs / 16 | Complete tables / 53 | Strict cells / 2,333 | Pages/min | Pages/API USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Haiku 5.5, explicit matrix instructions | 15 | 3 | 452 | 6.74 | 1,604.79 |
| Sonnet 5.5, fresh same-crop run | 15 | 4 | 289 | 4.88 | 64.63 |
| Gemini 3.5 Flash Lite, simplified wire schema | 15 | 3 | 287 | 9.09 | 345.24 |
| PPLX admission + Haiku, union ranked by table probability | 13 | 2 | 270 | 0.78 | 295.66 |
| PPLX admission + Haiku, union ranked by smaller region first | 15 | 1 | 138 | 0.94 | 333.88 |

More admitted regions did not produce better tables. Source-preserving placement
on frozen model topology also remains below the 384-cell ordinal baseline:
uniform geometry recovers 276 cells, source-derived bands 328, PPLX ownership 280,
and Luna Decisions ownership 232. The latter two are independently verified
offline replays of original responses after a composition-order fix; they have
no new inference throughput or cost claim.

Fresh broader P003 runs on 64 natural DEV pages (93 tables, 3,847 reference
cells; includes the original 16 pages) narrow the quality gap:

| Pipeline | Outputs / 64 | Complete tables / 93 | Strict cells / 3,847 | Extra tables | Pages/min | Pages/API USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Haiku source IDs, OCR300 | 62 | 11 | 1,309 | 11 | 2.69 | 1,013.32 |
| GPT-6 Luna, 1024 px crops | 63 | 12 | 1,348 | 0 | 5.54 | 1,985.15 |
| Sonnet 5.5, 1024 px crops | 64 | 14 | 1,839 | 4 | 3.20 | 140.43 |

All retain 64 pages in quality denominators. Ordinal and Luna produce no table
false positives on the 24 negative pages; Sonnet produces one. Sonnet recovers
more cells and complete tables, at substantially higher API cost. The ordinal run has two raster-admission
failures; Luna has one invalid rectangular-matrix response. Rates count usable
outputs under concurrent load, with full generation costs and unpriced local
compute. This broader DEV sample is not held-out confirmation.

The completed [57-arm image and decision screen](bench/results/p003-mixed-evidence.md)
finds 1,087 strict cells / 5 complete tables at 128 px RGB, versus 981 / 5 at
512–768 px and 685 / 4 at 1024–1200 px. These are retained pipeline scores:
abstentions can leave original candidate output in place. Most of the smaller
image's gain comes from one dense page, so it needs fresh confirmation.

The [repeat and blank-image audit](bench/results/p003-current-queue-audit.md)
separates quality actually supported by model choices. Abstained or failed
crops receive no model credit; all 16 pages, 53 tables and 2,333 cells remain
in the denominators.

| PPLX selector treatment | Model-confirmed strict cells | Complete tables | Selected / abstained calls | Incremental pages/min | Incremental pages/API USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 128 px RGB, fresh repeat | **984** | **5** | 15 / 1 | 4.83 | 26,746 |
| 128 px blank-image control | 11 | 0 | 2 / 14 | 3.94 | 26,746 |

These rates count retained-page processing, including no-question and abstained
pages, under six contending host jobs and three paid transports. Both original
candidate generations are excluded. They are neither complete extraction rates
nor counts of fully decided pages. Each model is evaluated separately; transport
failures do not trigger another model. A [fresh 48-page source-frozen sample](bench/results/p003-confirmation-corpus.md)
contains 32 additional natural pages from distinct known document parents and
16 new synthetic layouts. Its confirmation results are pending.

The [CPU render-reuse experiment](bench/results/p003-render-reuse.md) preserves
all 266 compared image byte streams exactly while reducing measured rendering
CPU time by 6.09–6.18 times through page reuse across crops and image sizes.
This is a preprocessing result, not a complete-pipeline speedup or provider
cache saving.

The [P002 generalization study](bench/results/generalization-p002.md)
expands coverage to 276 DEV pages: 156 authored stress pages, 64 independently
annotated OmniDocBench page images, and 56 native-PDF diagnostics. A fixed
16-page natural screen contains 53 tables and 2,333 reference cells; two dense
newspaper pages contain 39 of those tables. It exposes substantially harder
localization, OCR, and assembly failures than the earlier authored study.

The first fixed 276-page expansion compares 249 reference tables across 220
scored pages; another 56 native-PDF pages are operational diagnostics. The
configuration was selected before running the additional natural pages.

| Configuration | Outputs / 276 | Complete tables / 249 | Exact text cells / 8,897 | Exact positive pages / 172 | Negative false-positive pages / 48 | Pages/min | Pages/API USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Native regional extraction + CPU OCR | 272 | 120 | 4,258 | 96 | 0 | 36.78 | No API calls |
| Native grids + YOLO + Haiku source-ID matrix, 512 px | 270 | 166 | 6,329 | 136 | 9 | 12.64 | 2,116.13 |
| Native grids + Haiku image crops, 1024 px, physical-order control | 268 | 157 | 6,604 | 129 | 1 | 18.33 | 6,743.87 |
| Native grids + Sonnet image crops, 1024 px, physical-order control | 271 | 157 | 6,119 | 128 | 16 | 16.73 | 323.13 |
| Native grids + Haiku image crops, 1024 px, corrected logical order, fresh run | 269 | **170** | **6,615** | **141** | 2 | 18.20 | 6,977.17 |

The 512 px Haiku source-ID run costs USD 0.1275912 in reported API charges. It recovers 155/156
authored tables and 11/93 natural tables, with eight authored and one natural
negative-page false positives. Four unsupported diagnostics and two truncated
responses remain failures. These results support further gated and hybrid
experiments; they do not establish reliable extraction across natural PDFs.

The image-crop hybrid costs USD 0.0397398 and recovers 1,813/3,847 natural
reference cells, versus 1,299 for source-ID assembly. Its physical-order control
also exposes a native-table rotation bug: all twelve authored rotated tables
lose logical cell ordering. Every other authored family is exact. These raw
scores retain that regression; the separately labeled correction below verifies
reading direction without changing the model's evidence or inventing cell text.

The [frozen offline orientation correction](bench/results/p002-native-orientation.md)
restores all twelve rotated tables: Haiku reaches **169/249 complete tables and
6,863/8,897 exact cells**, and Sonnet reaches 169/249 and 6,378/8,897. All original
failures and extra tables remain. These corrected quality counts reuse retained
responses; they do not replace the original fresh-run throughput measurements.

The subsequent fresh corrected Haiku run costs USD 0.0385543 and recovers all
156 authored tables and all 5,050 authored cells, with no authored false positives.
The 64 natural pages remain much harder: 14/93 complete tables and 1,565/3,847
exact cells, with two negative-page false positives and three atomic failures.
The four unsupported native diagnostics also remain failures. Its natural-cell
count falls by 248 relative to the original physical-order run despite unchanged
model input treatment; do not attribute response variation to native orientation.

The matched full Sonnet hybrid costs USD 0.838664. It produces more operational
outputs but fewer exact cells and more negative-page false positives than Haiku
in this fresh run. Higher model price does not establish a better pipeline.
See the [design findings and pipeline diagram](bench/GENERALIZATION_FINDINGS.md)
for the resulting priorities and remaining limitations.

To process a document with retained Markdown, structured output, page failures
and provenance, use the [experimental document CLI](bench/GENERALIZATION_USAGE.md):

```sh
.venv/bin/python -m bench.extract_document /absolute/path/document.pdf --output /new/output/directory
```

The default runs locally on CPU. Explicit `--mode hybrid-haiku` or
`--mode hybrid-sonnet` enables metered hosted image transcription under the
project ledger. Model-transcribed tables remain labeled separately from
source-owned cells; partial documents retain visible page failures.

Selected natural-screen comparisons (all 16 intended pages remain scored):

| Configuration | Outputs / 16 | Complete tables / 53 | Exact text cells / 2,333 | Pages/min | Pages/API USD |
|---|---:|---:|---:|---:|---:|
| PPLX + selective Sonnet, regional geometry | 16 | 0 | 4 | 3.60 | 109.43 |
| Pixel grids + PPLX + selective Sonnet | 16 | 0 | 92 | 3.91 | 111.17 |
| Sonnet source-ID assembly, 512 px | 16 | 2 | 295 | 2.60 | 13.32 |
| Haiku source-ID matrix, 512 px | 16 | 2 | 240 | 1.99 | 225.44 |
| YOLO + Sonnet source-ID matrix, 512 px | 15 | 2 | 341 | 3.89 | 52.29 |
| YOLO + Haiku source-ID matrix, 512 px | 15 | 2 | 258 | 3.24 | 638.72 |
| YOLO + Haiku, OCR300 + arrays + 1024 px | 15 | 3 | 387 | 2.60 | 903.47 |
| Sonnet whole-page image transcription, 1200 px | 15 | 3 | 299 | 6.51 | 106.65 |
| Haiku whole-page image transcription, 1200 px | 13 | 2 | 245 | 6.41 | 1,527.90 |
| Opus whole-page image transcription, 2048 px JPEG50 | 16 | 3 | 300 | 6.84 | 34.59 |
| Sonnet whole-page image transcription, 2048 px JPEG50 | 16 | **7** | 540 | 9.70 | 63.29 |
| Haiku whole-page image transcription, 2048 px JPEG50, serial | 14 | 2 | 208 | 12.43 | 1,190.19 |
| Haiku whole-page image transcription, 2048 px JPEG50, four workers | 13 | 4 | 216 | **30.93** | 1,181.46 |
| Sonnet detector-crop transcription, 1024 px JPEG90 | 16 | 5 | **982** | 6.88 | 69.41 |
| Haiku detector-crop transcription, 400 px JPEG90 | 16 | 3 | 225 | 8.49 | 1,779.68 |
| Haiku detector-crop transcription, 512 px JPEG90 | 16 | 2 | 290 | 9.80 | **1,979.73** |
| Haiku detector-crop transcription, 768 px JPEG90 | 16 | 3 | 403 | 9.87 | 1,849.20 |
| Haiku detector-crop transcription, 1024 px JPEG90 | 14 | 4 | 687 | 8.57 | 1,538.73 |
| Sonnet detector-crop transcription, 2048 px JPEG50 | 15 | 3 | 292 | 10.21 | 81.31 |
| Haiku detector-crop transcription, 2048 px JPEG50 | 14 | 2 | 268 | 7.88 | 1,016.28 |
| Sonnet multiscale detector + 1024 px crops | 14 | 4 | 293 | 4.15 | 48.46 |
| Haiku multiscale detector + 1024 px crops | 15 | 2 | 581 | 5.52 | 1,135.80 |
| YOLO + Haiku source-ID matrix, generation row context, 512 px | 15 | 2 | 225 | 3.13 | 416.14 |
| YOLO + gated Haiku ordinal cells, gate row context, 512 px | 16 | 2 | 336 | 3.33 | 558.89 |
| YOLO + Haiku, OCR300 + arrays + ordinal cells + column instructions, 512 px | 16 | 3 | 395 | 2.55 | 846.06 |

The 1024-pixel JPEG90 Sonnet and Haiku crop configurations beat the measured whole-page Opus configuration in
complete tables and exact cells at lower API cost. This compares complete input
strategies, not model ability on identical images. Sonnet crops produce no extra
tables; Haiku crops produce three on dense positive pages and fail two pages
strict output validation. Opus produces six extras on dense positives. None of
these three configurations produces a table on the four negative pages.
Supplementary positive-page macro exact-cell recall is 66.97% for Sonnet crops,
52.90% for Haiku crops and 62.01% for Opus whole-page input. Thus Haiku's higher
micro cell count does not establish a win under equal page weighting.

Repeatability is a material limitation: the Sonnet hybrid run sent all 19 crop
requests byte-for-byte identically to the standalone crop run, but recovered
289 exact cells instead of 982. A fresh malformed response on one dense page
caused atomic rejection of the page that previously contributed 692 exact cells.
The detector proposals also matched on all sixteen pages. This difference is
response variation and strict failure handling, not evidence that native/image
composition reduces model accuracy. The single-run crop result is promising,
but not a stable reliability estimate.

The matched smaller-crop controls recover 0, 2 and 110 exact cells on the dense
pair at 400, 512 and 768 pixels, versus 416 at 1024. Remaining-page counts are
225, 288 and 293, versus 271 at 1024 where two strict failures discard output.
Thus 768 pixels is a useful measured compromise, but no single image edge wins
every criterion. These are single fresh runs, without an outcome-based size selector.

These are exploratory runs with concurrent research workloads; the four-worker
arm is explicitly separate from serial controls. Rates count
complete emitted outputs and API charges, including failed calls; they do not
count only correct tables. Timing covers page processing and excludes freezing
artifacts and client setup. The detailed report includes topology, missing/extra
tables, positive and negative pages, CPU/RAM, provider usage, and failures.
Source-ID assembly preserves literal evidence but cannot repair missing OCR text.
Image transcription is a separately labeled table-only comparator. No model is
enabled by default, and public benchmark pretraining contamination is unknown.
Image-transcribed text has no source-conservation guarantee. Whole-page JPEG90
at 2048 pixels refused five requests before inference; JPEG50 at that edge admitted
all sixteen inputs. Their observed rates therefore include different coverage,
not just a change in model speed or image resolution.
The [source inventory audit](bench/results/p002-source-inventory-ceilings.md)
finds that even an optimistic rearrangement of standard OCR words can form only
1,194/2,333 reference cells under the literal source-assembly rules. Whitespace
OCR at 300 DPI raises this bound to 1,880; actual assembly recovers 387. Both OCR
and assembly need improvement. A fixed 2048-pixel OCR edge reduces dense pages
to about 90–94 DPI and lowers the bound; pixel caps must account for text density.
The [stage profile](bench/results/pipeline-native-fastpath.md)
attributes 62.83% of page wall time to API calls, 29.07% to source extraction
including OCR, and 6.37% to layout detection. Parent and worker CPU/RAM are
reported separately; GPU use is unmeasured for hosted inference.
An [offline partial-table experiment](bench/results/p002-partial-salvage.md)
quarantines every invalid or conflicting table and keeps isolated valid tables
as explicitly partial evidence. It recovers 629 cells from the failed Sonnet
hybrid page, while adding one extra table. Complete-page scores and errors stay
unchanged; this supports reviewable partial artifacts, not automatic acceptance.
See the [plan](bench/GENERALIZATION_PLAN.md) and [corpus provenance](bench/GENERALIZATION_CORPUS.md).

The [P001 complete-pipeline study](bench/results/pipeline-p001.md) now measures
PDF input through source discovery, candidate assembly, model decisions, validated
table JSON and Markdown. Its frozen DEV corpus has 181 pages: 168 with table
structure references and 13 diagnostic pages. See the [experiment contract](bench/PIPELINE_EXPERIMENTS.md)
for the 32-page balanced pilot, resource measurements, cost rules and limitations.
All 56 configurations are complete. The [findings and accounting](bench/results/pipeline-conclusions.md)
explain the winning combinations and measured regressions. These results are exploratory;
general prose, math and form semantics are not gold-scored.

The experimental path normalizes page rotation, extracts positioned words and
vector rules, applies CPU OCR when no text is available, and keeps validated
native grids. On remaining pages it asks whether a table exists before selecting
a complete source-derived assembly. Optional independent review checks uncertain
admission decisions. Column-consensus alternatives retain sparse columns and
tolerate OCR placement drift. Every accepted output validates cell spans and assigns each
extracted word exactly once to a cell or remaining prose. Merged spans are emitted
as HTML tables inside Markdown. The [reproduction commands and offline demo](bench/PIPELINE_EXPERIMENTS.md#reproduce-the-complete-path)
show PDF input through final Markdown and JSON; no hosted model is enabled by default.

Selected completed full-corpus configurations (181 input pages; 35 scored table pages, 133
scored non-table pages and 13 diagnostics):

| Complete pipeline configuration | Outputs / 181 | Exact table pages / 35 | False-table pages / 133 | Exact scored pages / 168 | Output pages/min | Output pages/USD |
|---|---:|---:|---:|---:|---:|---:|
| Native vector grids + CPU OCR | 178 | 16 | 0 | 149 | 1,524.9 | Unpriced CPU |
| PPLX assembly, 256 px | 175 | 34 | 27 | 140 | 53.0 | 10,170 |
| PPLX vector-first cascade, 256 px | 177 | 34 | 27 | 140 | 58.7 | 10,893 |
| PPLX independent gate, 256 px | 178 | 34 | 4 | 163 | 117.9 | 28,641 |
| PPLX gate + Sonnet review, 256 px | 178 | 34 | 0 | 167 | 72.4 | 1,659 |
| PPLX column consensus + gate, 256 px | 178 | 35 | 4 | 164 | 114.1 | 25,916 |
| PPLX column consensus + gate + Sonnet review, 256 px | 178 | 35 | 0 | 168 | 72.4 | 1,726 |
| PPLX columns + compact evidence + gate, 256 px | 178 | 32 | 4 | 161 | 107.5 | 27,063 |
| PPLX columns + readable deduplication + Sonnet review, 256 px | 178 | 35 | 0 | 168 | 71.7 | 1,755 |
| PPLX columns + compact evidence + Sonnet review, 256 px | 178 | 32 | 0 | 165 | 69.0 | 1,751 |
| PPLX columns + compact evidence + Haiku review, 256 px | 177 | 31 | 10 | 154 | 81.6 | Unknown |
| PPLX gate, compact geometry/text only | 178 | 28 | 5 | 156 | 102.1 | 31,227 |
| PPLX adaptive row edits | 178 | 28 | 30 | 131 | 151.6 | 69,429 |
| Luna gate, 1024 px | 178 | 34 | 6 | 161 | 105.8 | 6,321 (estimate) |
| Clef Flash gate, 512 px | 178 | 22 | 5 | 150 | 58.5 | 10,958 |
| Haiku 5.5 assembly, 512 px | 175 | 34 | 18 | 149 | 22.0 | 2,093 |
| Sonnet 5.5 assembly, 512 px | 174 | 34 | 0 | 166 | 15.9 | 108 |
| Sonnet 5.5 columns + compact evidence, 512 px | 166 | 33 | 2 | 159 | 13.6 | 113 |
| Opus 5.5 assembly, 512 px | 175 | 34 | 0 | 167 | 13.0 | 56 |

These are single serial runs on authored DEV silver, with different routing and
image settings. Rates count complete emitted outputs, include all pipeline
waiting/bookkeeping, and price API usage only; quality is reported separately.
PPLX denotes `perplexity/pplx-decider-v1.1-27b`; Luna denotes `openai/gpt-6-luna-decisions`.
Luna's reported zero is preserved and replaced only in effective-cost calculations
by a labeled catalog estimate. Full errors, cells/spans, family scores, CPU/RSS,
candidate ceilings and all controls are in the [complete report](bench/results/pipeline-p001.md).
The [matched pilot comparison](bench/results/pipeline-pilot-findings.md) separately
records Sonnet and Opus at 32/32 exact pilot pages and a conditional-review tie;
it does not establish superiority on independent documents.

The private DEV experiments below ask hosted models to group **two selected
source-text chunks**. They evaluate word boundaries and description-row
ownership on small authored controls; they do not measure complete PDF
extraction. No hosted model is enabled by the package API. See the
[experiment protocol](bench/DECISION_MODELS.md) for explicit hosted execution and
the persistent spending ledger.

Snapshot: 2026-10-09. Configurations are selected examples from completed DEV
arms, including Luna's tied-highest completed known-score fraction in the
basic/prompt/focus matrices;
they are not universal model recommendations. Known scores use provisional
authored references. Ambiguous abstention is scored separately, and source
conservation alone does not establish correct grouping.

| Model / tested evidence | Scored / planned page inputs | Known score / known inputs | Ambiguous abstain / ambiguous inputs | Pages/minute (API only) | Pages/USD |
|---|---:|---:|---:|---:|---:|
| Jev 1.13 · words ([basic](bench/results/lowlevel-basic.md)) | 72/72 | 28/48 | 0/24 | 652.3 | 42,932 |
| d1 · glyphs + vector rules ([basic](bench/results/lowlevel-basic.md)) | 72/72 | 26/48 | 0/24 | 298.0 | 3,636 |
| d1 · short literal criteria + typed minimal text ([prompts](bench/results/lowlevel-prompt-factors.md)) | 24/24 | 9/16 | 2/8 | 565.8 | 64,977 |
| PPLX v1.1 · resolved criteria + crop512 ([prompts](bench/results/lowlevel-prompt-factors.md)) | 24/24 | 15/16 | 1/8 | 227.6 | 6,733 |
| Luna · crop512, singleton ([prompts](bench/results/lowlevel-prompt-factors.md)) | 24/24 | 9/16 | 0/8 | 170.6 | ~4,432 |
| Clef Flash · bounded focus + lowbit256 ([images](bench/results/lowlevel-images-focus.md)) | 24/24 | 12/16 | 0/8 | 145.0 | 18,028 |
| Clef · bounded focus + RGB128 ([images](bench/results/lowlevel-images-focus.md)) | 24/24 | 8/16 | 0/8 | 124.2 | 6,777 |
| Gateway d1 · short typed text ([Gateway text](bench/results/lowlevel-gateway-text.md)) | 24/24¹ | 7/16 | 1/8 | 144.9 | 114,090 |
| Gateway Laya · supported short text ([compatibility](bench/results/lowlevel-gateway-supported.md)) | 24/24¹ | 10/16 | 0/8 | 146.4 | n/a zero cost |
| Gateway Laya-free · same short text ([compatibility](bench/results/lowlevel-gateway-supported.md)) | 24/24¹ | 10/16 | 0/8 | 149.7 | n/a zero cost |

Here, a **page input means one supplied region decision on one source page**,
not complete-page extraction. The 72-input basic arms contain three
render-equivalent encodings of each of 24 logical cases; their observations are
correlated. Prompt/image arms use 24 representatives. ¹ The displayed Gateway text scores
include eight identical-input aliases per arm: their rate numerators count only
16 fresh page inputs. Other displayed rows have no replay/alias rate numerator.
API-only time sums retained HTTP intervals and excludes source extraction,
rendering, preparation and between-call waiting. It is not end-to-end pages/minute.

Costs prefer positive provider-reported charges. `~` marks estimates from
reported tokens and frozen serving rates; reported zeros remain in the ledger.
The Clef rows use observed Cloudflare charges, not cheaper rates from a different
serving route. Missing cost/time makes the corresponding complete rate unknown;
zero effective cost gives no finite pages/USD rate. Gateway aliases/routes are
not independent model architectures. Accepted image requests do not establish
that their pixels affected the decision: Gateway visual sensitivity remains
under investigation.

For the same original L001 crop512 evidence, the completed frontier comparison
uses 72 encoded page inputs, 48 authored-known cases and 24 ambiguous cases.
The generic chat/structured-output transport differs from native decision APIs;
these rows compare source evidence and grouping outcomes, not identical API
protocols. See [all frontier arms](bench/results/lowlevel-frontier-basic.md).

| Model / same crop512 evidence | Scored / planned page inputs | Known score / known inputs | Ambiguous abstain / ambiguous inputs | Pages/minute (API only) | Pages/USD |
|---|---:|---:|---:|---:|---:|
| Opus 5.5 | 72/72 | 46/48 | 14/24 | 19.2 | 64.8 |
| Sonnet 5.5 | 72/72 | 37/48 | 10/24 | 70.6 | 150.8 |
| PPLX v1.1 · original native-decision crop512 | 72/72 | 38/48 | 0/24 | 204.8 | 6,689 |
| Luna · original native-decision crop512 | 72/72 | 25/48 | 0/24 | 517.7 | ~4,437 |
| Haiku 5.5 · **incomplete** after HTTP 429 | 12/72 | 6/48 planned | 1/24 planned | 26.8 partial | 2,227 partial |

The [Gateway RGB512 route](bench/results/lowlevel-gateway-vision.md) accepted
24/24 requests and returned 8/16 known scores, 0/8 ambiguous abstentions, 88.5
API page inputs/minute and 73,746 page inputs/USD. It is excluded from the visual
comparison: image-token accounting is invariant across sizes, and actual visual
sensitivity remains unverified pending a sanity control.

The full reports retain failures and every tested arm. Jev's later prompt sweep
stopped after a retained failure. PPLX's bounded-focus image sweep completed only
eight successful inputs before HTTP 429 and a persistent stop; those partial
arms are not substituted for its completed resolved-crop result above. The original
Gateway text matrix stopped both Laya aliases on HTTP 422; a separate supported
text-state experiment completed all 96 configurations with 64 distinct bodies.
Its completed short-text scores appear above. Expanded string-glyph packets also
failed HTTP 422 in a separate follow-up, so compatibility is not explained by
compression alone. All original failures remain retained and are not retried.

The following comparisons change evidence or representation while keeping their
own cohorts explicit:

| Experiment / cohort | Known score; ambiguous abstention | Pages/minute (API only) | Pages/USD | Observation / full report |
|---|---|---:|---:|---|
| Jev raw → lossless compact; history, 36 scored inputs per arm, 12 fresh | 9/18 → 9/18; 0/18 → 0/18 | 183.0 → 204.7 | 1,924 → 6,106 | Reported charges −68.5%; [matched history](bench/results/lowlevel-matched-history.md) |
| d1 raw → lossless compact; same history cohort | 9/18 → 9/18; 0/18 → 0/18 | 105.7 → 150.6 | 1,953 → 5,759 | Reported charges −66.1%; [matched history](bench/results/lowlevel-matched-history.md) |
| Luna raw → lossless compact; same history cohort | 12/18 → 12/18; 0/18 → 0/18 | 138.1 → 155.5 | ~1,562 → ~5,053 | Estimated charges −69.1%; aggregate scores match, individual decisions can change; [matched history](bench/results/lowlevel-matched-history.md) |
| PPLX raw → compact; raw 33/36 scored, compact 36/36 | 15/18 → 12/18; 0/18 → 3/18 | 54.8 → 101.6 | unknown → 15,678 | Raw HTTP 429 leaves three correlated failed inputs and one unknown charged request; [matched history](bench/results/lowlevel-matched-history.md) |
| Offline geometry + Jev words; 72 paired inputs | 28/48 → 40/48; 0/24 → 0/24 | cascade unmeasured | cascade unmeasured | Zero paired losses; original batches cannot be skipped whole; [hybrid replay](bench/results/lowlevel-hybrid-basic.md) |
| Offline geometry + PPLX typed/resolved minimal text; 24 paired inputs | 6/16 → 14/16; 4/8 → 4/8 | cascade unmeasured | cascade unmeasured | Adds source-rule evidence; [hybrid prompts](bench/results/lowlevel-hybrid-prompts.md) |
| Clef Flash lowbit size sweep: 64/128/256/400/500/512; 24 scored per size | 9/9/12/8/10/8 out of 16; 0/8 at every size | 110.0–145.0 | 17,544–18,355 | Larger crops did not improve scores monotonically; [all 18 image arms per model](bench/results/lowlevel-images-focus.md) |
| Fresh RGB 512 → 768 → 1024; PPLX, 24 inputs per size | 12 → 12 → 13/16; 0 → 0 → 0/8 | 134.7 → 132.0 → 147.3 | 86,306 → 76,943 → 63,546 | [Fresh-source resolution matrix](bench/results/lowlevel-images-large.md); grayscale and two-bit scored separately |
| Fresh RGB 512 → 768 → 1024; Luna, 24 inputs per size | 7 → 7 → 11/16; 2 → 1 → 1/8 | 166.0 → 187.4 → 163.4 | ~20,060 → 16,708 → 13,822 | [Fresh-source resolution matrix](bench/results/lowlevel-images-large.md); grayscale and two-bit scored separately |
| Fresh RGB 512 → 768 → 1024; Clef Flash, 24 inputs per size | 9 → 11 → 10/16; 0 → 0 → 0/8 | 133.5 → 137.4 → 134.2 | 25,760 → 29,122 → 21,494 | [Fresh-source resolution matrix](bench/results/lowlevel-images-large.md); grayscale and two-bit scored separately |
| Fresh RGB 512 → 768 → 1024; Clef, 24 inputs per size | 9 → 9 → 10/16; 0 → 0 → 0/8 | 113.1 → 93.5 → 88.7 | 6,589 → 5,928 → 4,961 | [Fresh-source resolution matrix](bench/results/lowlevel-images-large.md); grayscale and two-bit scored separately |

Matched history holds source values, singleton batching and prompt criteria
fixed; 24 encoding aliases per arm are excluded from rates. Equal aggregate
scores are not proof of equal decisions or general quality preservation. Offline
hybrids reuse prepaid model responses: their observed score gains are not
measured cascade cost/latency savings. The 64–512 sweep downsamples retained
512-edge crops; resizing and grayscale/lowbit conversion change pixel evidence,
although PNG encoding itself is lossless. Its reported rates are observed ranges
across the six sizes, not the throughput of one chosen configuration.

Fresh-source larger images helped some models: Luna gray1024 reached 11/16 known
and 2/8 ambiguous abstentions; Clef-Flash reached 11/16 known at 768 in all three
formats. These are single DEV observations. Flash's reported serving rates changed
within the wave, so its cost differences do not isolate image resolution or prove
provider cache hits. The linked report retains every paired gain and loss.

The [natural-document follow-up](bench/LOWLEVEL_NATURAL.md) uses 24 overlapping
regions on **one** Senate expenditure page, with source-aware single-review
references. Its region/minute and region/USD rates must not be presented as
24 independent PDF pages. None of these studies establishes full-table,
header/value, reading-order or production-document extraction quality.

The [self-hosted model shortlist](bench/HF_DECISION_MODELS.md) includes native
decision heads, small Qwen/SmolVLM/LFM/MiniCPM vision baselines through vLLM,
and separately labeled noncommercial JPT/Nimble research releases.
[Remote GPU results](bench/results/remote-gpu-r001.md) retain matched image
conditions, native-versus-hosted differences, CPU/RAM/VRAM and failure records.

| Model | RGB correct at 512 / 768 / 1024 px, each /16 | RGB ambiguous abstention, each /8 | Page-region inputs/min | Estimated warm inputs/USD |
|---|---:|---:|---:|---:|
| Intern-Decision 4B, newer stack | 12 / 12 / 12 | 0 | 658.40 | 28,730 |
| Clef-Flash 9B | 10 / 11 / 11 | 0 | 748.85 | 35,240 |
| Perplexity Decider 27B | 9 / 12 / 12 | 0 | 292.15 | 12,748 |
| Clef 27B | 9 / 11 / 12 | 0 | 266.74 | 12,552 |
| Qwen3.5-0.8B, vLLM diagnostic | 8 / 8 / 8 | 0 | 512.78 | 23,515 |
| Qwen3.5-2B, vLLM | 6 / 7 / 7 | 0 | 343.78 | 15,766 |
| Qwen3.5-4B, vLLM | 10 / 10 / 10 | 0 | 272.36 | 12,490 |
| Qwen3.5-9B, vLLM | 11 / 12 / 11 | 0 | 252.16 | 11,564 |
| SmolVLM2 2.2B, vLLM diagnostic | 5 / 5 / 5 | 1 / 0 / 1 | 510.84 | 23,427 |
| LFM2-VL 1.6B, vLLM diagnostic | 9 / 9 / 9 | 0 | 693.65 | 31,810 |
| MiniCPM-V-4, vLLM diagnostic | 11 / 11 / 12 | 0 | 493.64 | 22,639 |
| JPT-4B, noncommercial | 10 / 10 / 9 | 0 | 590.05 | 25,748 |
| JPT-9B, noncommercial | 8 / 8 / 8 | 0 | 563.11 | 24,572 |

Rates cover 216 serial supplied-region decisions over 24 representative DEV
pages and nine image treatments, including preprocessing during inference.
Estimated warm inputs/USD divides measured throughput by the actual allocation's
hourly GPU and disk rate. It excludes model loading, downloads, idle time and
cleanup; whole-wave provider billing is reported separately. These are conditional
page-region decisions, **not full-page extraction pages/minute or pages/USD**.
The Intern newer-stack table initially changes hosts; a same-host follow-up also
finished the 216 inputs in 26.65 seconds. [Quality and runtime isolation](bench/results/remote-gpu-intern-runtime.md) are
reported separately. The complete report retains every color/size result and resource scope.
Nimble-v3's separate noncommercial text-only ablation scored 6/16 known cases
and abstained on 0/8 ambiguous cases. No reference answers are sent to workers,
and the protected set remains untouched.

The [blind prompt comparison](bench/results/remote-gpu-prompts.md) found
model-specific gains: PPLX sufficiency wording reaches 13/16 known cases;
identity wording reaches 12/16 known and 3/8 ambiguous abstentions. Clef's neutral
wording reaches 12/16, while all four variants reduce Flash's known-case score.
The [fixed combination comparison](bench/results/remote-gpu-combinations.md)
records the cost of agreement: at 768/1024 px, unanimity reduces known errors
but also loses correct decisions, and majority voting does not recover ambiguity.
These remain exploratory, correlated DEV results.

The [prompt × resolution screen](bench/results/remote-gpu-prompt-sizes.md)
completed 480 decisions per native model. PPLX at RGB 640 px with identity wording
scored 12/16 known cases and abstained on 4/8 ambiguous cases; the same image with
original wording scored 10/16 and 0/8. These are paired exploratory observations,
not an independent validation of the best configuration.

The [frozen geometry gate](bench/results/ambiguity-geometry.md) correctly resolves
8/16 answerable authored cases with no wrong decisions, while abstaining on the
remaining eight and all eight ambiguous cases. Its natural-document trial
abstains everywhere, including 52 answerable conditions. Structural cues help
when present, but this conservative gate alone does not reconstruct natural rows.

The [fresh-size sweep](bench/results/remote-gpu-image-sizes.md) adds 128, 256,
384, 400, 448, 500 and 640 px in three independent color treatments. Intern
preserves 12/16 known correctness at every size ≥256 in every color mode;
128 px loses accuracy. All 672 ambiguous inputs across the four models remain
decisive. Image size alone does not solve evidence insufficiency.

The [measured-evidence comparison](bench/results/remote-gpu-ambiguity-evidence.md)
completed 288 corrected inputs per native model, crossing geometry, pixels and
combined cues with two image sizes and two prompts. Some known-answer scores
improved, often at the cost of fewer ambiguity abstentions; no general quality
improvement was established. Failed input packaging and its corrected runs remain
separately reported.

The [natural-region comparison](bench/results/remote-gpu-natural.md) retains
agreement with provisional full-source references separately from agreement with
the supplied crop's evidence. The [concurrency comparison](bench/results/remote-gpu-concurrency.md)
measures Qwen9 at 240.15 supplied-region inputs/min with one client and 954.96
with eight, over actual elapsed time. Known correctness changes from 99/144 to
97/144 across repeated DEV arms. Those eight clients share one model allocation;
throughput is not computed from summed overlapping request latency.

The [single-copy batching comparison](bench/results/remote-gpu-batching.md)
completed 2,160 decisions. Flash batch size 2 preserved all 216 choices and reached
844.58 warm region inputs/minute (estimated 39,745 inputs/USD), an 8.1% warm gain
but only a 0.9% gain including worker startup. Larger batches were slower; larger
Clef batches also changed decisions and reduced accuracy.

The [natural prompt transfer](bench/results/remote-gpu-natural-transfer.md)
shows a useful but incomplete Flash tradeoff: identity wording improves
insufficient-evidence abstention from 5/44 to 19/44, while known correctness falls
from 35/52 to 32/52. The [Qwen9 natural comparison](bench/results/remote-gpu-natural-qwen.md)
retains its failures and measured concurrent resource use alongside throughput.

Diagnostic small-model cohorts have valid transports but failed semantic shape
controls; those failures and all runtime repairs remain visible in the reports.
No experimental hosted or remote-GPU path is enabled by default in extraction.

[Whole-wave billing and cleanup](bench/results/remote-gpu-costs.md): USD 9.727
provider-posted GPU, disk and transfer charges; all rented instances retired.
Conservative campaign accounting is USD 28.54 of the USD 100 cap, including
USD 6.05 in older unresolved reservations.

## Architecture

```
jev_pdf.Document (Python, pymupdf-style API)
   └─ _Document (PyO3)
        ├─ lopdf 0.44   … editing: open → modify → save
        ├─ hayro 0.7    … rendering and positioned extraction
        └─ krilla 0.8 + HarfRust 0.12
                         … shaped, subset-embedded text and form appearances
```

```
rust/          # PyO3 bindings
src/pylopdf/   # Python high-level API
tests/         # pytest (Rust behavior is verified through Python tests)
```

Every release installs each published wheel — five `abi3-py310`, five CPython
3.14t, the sdist, and the PyEmscripten wheel — on architecture-matched runners
and exercises creation, saving, extraction, and rendering before publishing
with build provenance.

## Contributing

Bug reports and focused contributions are welcome. See
[CONTRIBUTING.md](https://github.com/justsml/jev-pdf/blob/main/CONTRIBUTING.md)
for development commands, test expectations, and the rules for sharing PDF
regression files:

```bash
uv sync                    # build + install dependencies
uv run pytest              # tests
uv run ruff check .        # lint
uv run mypy src tests      # type check
```

Report security vulnerabilities privately through
[GitHub Security Advisories](https://github.com/justsml/jev-pdf/security/advisories/new).

## License

[MIT](https://github.com/justsml/jev-pdf/blob/main/LICENSE). Bundled Rust
dependencies keep their own permissive licenses (lopdf and HarfRust are MIT;
hayro and krilla are MIT/Apache-2.0) — see
[NOTICE.md](https://github.com/justsml/jev-pdf/blob/main/NOTICE.md).

This private continuation derives from pylopdf by Yusuke Hayashi. Original
author attribution, MIT license and bundled dependency notices are preserved.
