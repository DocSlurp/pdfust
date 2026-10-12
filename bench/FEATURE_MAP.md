# PDF to Markdown feature map

This is a practical map of content families and conversion policies, with a
reproducible study of 23 inputs. It is not an exhaustive implementation of the
PDF specification. A PDF can retain text mappings, annotations, tags, and
graphics while losing the original paragraphs, equations, and document tree.
The [pypdf extraction guide](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
describes why extraction involves choices about that structure.

Run the performance baseline and feature study separately:

```bash
uv sync --group bench-rich
uv run python bench/layout.py --output /tmp/layout-baseline.json
# After a change, on the same machine and with the same font extras:
uv run python bench/layout.py --baseline /tmp/layout-baseline.json
uv run python -m bench.features
```

The initial feature study compares pdfust, PyMuPDF, PyMuPDF4LLM, pypdf, and
pdfplumber; the combined model study adds Docling and Marker.
It includes pdfust's opt-in text tables, PyMuPDF's explicit ActualText flag,
PyMuPDF4LLM's legacy and model-backed layout paths, and HTML table output.
Options and installed versions are recorded. PyMuPDF, pypdf, and pdfplumber are
plain-text baselines here, not Markdown converters. These modes are not an
equivalent-work speed ranking: some embed images, infer layout, or retain only
text. The study keeps the input PDF, complete UTF-8 output, warnings, errors,
repeatability hashes, and parsed Markdown/HTML observations for each run.

## Mapping and review criteria

| PDF content or signal | Markdown representation or policy | What a meaningful check needs | Study cases |
|---|---|---|---|
| Text and glyph Unicode | UTF-8 text | Text mappings, complete content, spaces, and literal punctuation survive | text-structure-and-literals; Unicode cases |
| UTF-16BE strings / ToUnicode CMaps | Unicode scalars, not raw UTF-16 bytes | Surrogate pairs, non-BMP characters, combining marks, ZWJ, variation selectors, and regional indicators | unicode-cmap-and-emoji; omml-equations |
| Font weight and style | `**bold**`, `*italic*` | The correct span receives the marker; punctuation must not manufacture emphasis | text-structure-and-literals; omml-equations |
| Font sizes / tagged headings | `#` through `######` | Hierarchy and body text remain sensible; font size alone is a heuristic | text-structure-and-literals; corpus-usrguide |
| Monospaced text and indentation | Inline code or fenced code | Content and indentation survive; monospace is not sufficient proof of source code | text-structure-and-literals; corpus-usrguide |
| Bullets, numbering, indentation | Lists and nested lists | Ordering and nesting are preserved; a hyphen in ordinary text is not a list | text-structure-and-literals |
| Literal markup punctuation | Escaped Markdown or safe literal blocks | Rendered text retains literal stars, brackets, backslashes, and angle brackets | text-structure-and-literals |
| Columns, page rotation, glyph order | Logical prose order | Source-order, geometric-order, and author-tagged-order references are distinguished | two-column-order; rotated-columns; tagged-reading-order |
| RTL and mixed numeric runs | Logical Unicode order | Hebrew/Arabic text and a numeric token retain their own directions | rtl-visual-glyph-order |
| Borders and aligned text cells | GFM pipe tables or HTML tables | Compare actual cells and row/column positions, not only the existence of a table | table-bordered; table-borderless; table-borderless-aligned |
| Center/right cell placement | GFM delimiter-row alignment or HTML attributes | Compare column alignment with known source geometry | table-bordered; table-borderless |
| Merged cells, multiline cells, genuine empties | Explicit span policy or HTML `rowspan` / `colspan` | Repeated anchor text, missing values, and genuinely empty cells remain distinguishable | table-merged; corpus-senate-expenditures |
| Bold/italic text and literal pipes in cells | Inline formatting and escaped table text | Cell boundaries and literal text remain intact | table-bordered; table-merged |
| Fractions, superscripts, radicals, equation layout | Renderer-specific LaTeX/MathML, HTML baseline markup, or a referenced equation image | Formula structure matches a human reference; flattened symbols are insufficient | positioned-math; corpus-usrguide; omml-equations |
| ActualText accessibility/source hints | Replacement text according to a declared policy | Contrast painted glyphs with the actual replacement value | accessible-actualtext; math-actualtext |
| Raster images | Image references plus real assets or embedded data | Correct image content, crop, placement, and caption association; a syntactic image alone proves none of these | images-and-vectors; image-only |
| Vector diagrams | Rendered assets or a supported vector reference | Visual content survives, rather than being mistaken for text/table borders | images-and-vectors; positioned-math |
| Image-only pages and invisible OCR text | Optional OCR, or a deliberate empty-text result | Distinguish absence of text from extraction failure and from skipped OCR | image-only; unicode-cmap-and-emoji |
| URI link annotations | `[label](url)` | Correct label and exact destination are associated | links-and-outline |
| Direct / named internal destinations | Stable generated links and destination anchors | Follow the emitted link to its actual generated target; a fragment-looking URL is not enough | links-and-outline |
| Bookmarks / document outline | Optional navigation metadata or generated TOC | Body headings and bookmarks are not silently conflated | links-and-outline |
| Footnote markers and page-bottom text | Footnote extension or an explicit linear-text policy | Marker-to-note association, ordering, and content survive | footnotes-and-page-furniture |
| Headers, footers, page numbers | Retain/remove policy and optional page boundaries | Body text is retained; repetition-based removal needs multiple pages | footnotes-and-page-furniture |
| Form fields and other annotations | Optional structured sidecar or explicit text policy | Separate widget values, visible labels, comments, and appearance text | corpus-f1040; source inventories |
| Metadata and attachments | Optional sidecars/assets | They are document objects, not automatically page-body text | UTF-16 metadata case; inventories record attachment names |

GFM supports table alignment and inline formatting, but pipe tables do not encode
merged spans; raw HTML or an explicit expansion policy is needed. See the
[GFM table specification](https://github.github.com/gfm/#tables-extension-).
Math and footnotes require a chosen renderer/extension rather than a universal
plain-Markdown interpretation. The study parses dollar math as an observation;
that does not certify an equation as correct.

OMML is the Office document equation format. In the bundled DOCX-to-PDF export,
the equation becomes positioned PDF glyphs and drawing rules; reading that PDF
does not recover the original OMML tree automatically. The source archive and
export provenance are retained in [the rich-fixture README](assets/rich/README.md).
[Docling's formula enrichment](https://docling-project.github.io/docling/usage/enrichments/)
is a separate model-based reconstruction stage. The
[optional model study](MODEL_BENCHMARKS.md) adds Docling with enrichment off and
on, plus Marker in CPU fast mode with OCR disabled, on the same inputs.

## Interpreting the artifacts

Start with [the feature summary](results/features-latest.md), then run the study
to generate the ignored local input PDFs and corresponding raw `.out` results.
Only summaries and the compact timing/hash baseline are committed. The local JSON sidecar includes the
literal values behind text probes, reference reading order, link destinations,
HTML spans/superscripts, output hashes, and pdfust's source-object inventory.
That inventory is an observation through pdfust's APIs, not an independent
ground-truth parser. The synthetic fixture definitions and original source
documents establish their known content.

Syntax counts are diagnostic, not quality scores. For example, literal dollar
signs in a PDF can accidentally become a math token; unescaped asterisks can
become emphasis; a detected table can misclassify two-column prose. A zero count
of pipe tables can also be correct when the converter emitted an HTML table.
Review complete output and the source geometry before deciding which behavior
is preferable.

The performance report uses exact input and full-output hashes before showing
a before/after speedup. Output changes require review rather than being scored
as optimizations. Faster text-only output cannot establish a win over a pipeline
that also reconstructs tables, extracts images, or runs OCR.

## Remaining coverage gaps

The studies do not measure full page OCR inference, Marker's OCR/formula-enabled modes,
arbitrary skew, ruby/warichu, general mixed-direction paragraphs, nested radical
and matrix equations, linked-image accessibility alt text, repeated-header removal,
multi-page table continuation, XFA forms, attachment export, optional-content layers,
clipping/soft-mask visibility, or exhaustive malformed-input behavior. Multiline
table content is present in the independent corpus but is not isolated as a
synthetic ground-truth case. These are explicit follow-up dimensions, not implied
support claims. The [PyMuPDF4LLM API](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html)
documents why layout, image, OCR, and table-mode options must be recorded separately.
