# Initial rich-content observations

These findings describe the versions and options in
[the feature report](results/features-latest.md). They are examples from the
bundled inputs, not universal library rankings. The study completed 207
case/configuration measurements; all outputs repeated
exactly over the three measured runs plus warmup.

| Feature | What the retained outputs show | Evidence |
|---|---|---|
| External and internal links | pdfust's Markdown omits both kinds, although its source inventory resolves all three links. PyMuPDF4LLM legacy preserves the external URI; its layout mode omits it. None of the measured Markdown modes emits the internal destinations. | [Link case](results/features-latest.md#links-and-outline) |
| Images and vector graphics | pdfust keeps captions and emits no image references. PyMuPDF4LLM emits embedded images; its layout mode also emits the simple vector rectangle as an image. A reference does not prove original-image passthrough or caption association. | [Image case](results/features-latest.md#images-and-vectors) |
| Font styling and literal punctuation | pdfust retains embedded-font body bold/italic in the Office export, but lacks styling from the unembedded Standard 14 variants. Literal stars and angle brackets become Markdown emphasis/HTML in the punctuation case, so syntax counts can overstate preserved formatting. | [Office case](results/features-latest.md#omml-equations), [literal case](results/features-latest.md#text-structure-and-literals) |
| Table escaping and spans | pdfust escapes literal pipes/backslashes and repeats the merged anchor in its pipe table. PyMuPDF4LLM's pipe-table modes lose the strict literal pipe/backslash probes; its HTML mode retains all five text probes but does not emit a `colspan` for this merged header. HTML output alone does not establish correct spans. | [Merged table](results/features-latest.md#table-merged) |
| Borderless tables versus prose | pdfust's text strategy detects the regular aligned label table, but also converts the two-column prose case into a table and changes the reference reading order. The default bordered strategy preserves the column reference order. This supports keeping text-table detection opt-in. | [Aligned table](results/features-latest.md#table-borderless-aligned), [prose columns](results/features-latest.md#two-column-order) |
| Math structure | The positioned fraction and Office equation do not become the supplied LaTeX reference in any mode. Layout-based PyMuPDF4LLM can emit an equation image. When ActualText already contains LaTeX, PyMuPDF text and PyMuPDF4LLM legacy retain that source hint; pdfust and the layout modes omit it. Recovering a hint is different from reconstructing an equation. | [Positioned math](results/features-latest.md#positioned-math), [ActualText math](results/features-latest.md#math-actualtext) |
| Unicode and emoji | Every configuration retains all four strict Unicode-CMap probes, including supplementary scalars and emoji sequences. In the Office PDF, pdfust and pypdf return a composed accent where PyMuPDF returns the source's decomposed sequence. This is a canonical Unicode difference, not proof of missing readable content. | [Unicode case](results/features-latest.md#unicode-cmap-and-emoji), [Office case](results/features-latest.md#omml-equations) |
| RTL and embedded numbers | pdfust retains all three supplied logical strings, including the bracketed numeric token. The other configurations differ on at least one strict probe. This fixture tests visual glyph ordering with invisible text, not Arabic shaping or arbitrary mixed-direction paragraphs. | [RTL case](results/features-latest.md#rtl-visual-glyph-order) |
| Tagged reading order | Outputs choose different orders on the contrived tagged page. The stream order coincides with the tag order, so matching that reference does not prove that a tool consumed structure tags. A counterfactual untagged or reordered-stream control remains necessary for that attribution. | [Tagged case](results/features-latest.md#tagged-reading-order) |

The Type 3 corpus case separately retains pdfust's known missing-Unicode
warning and empty extraction result. Color emoji in the Office PDF and invisible
surrogate-pair text are different source representations; results from one
should not be generalized to the other.

The [feature map](FEATURE_MAP.md) lists the review criteria and remaining gaps.
Automatic probes are useful for catching differences, while table geometry,
formula equivalence, internal-link resolution, and image placement still need
source-aware review. The [performance baseline](results/layout-latest.md)
provides before/after timings with exact-output guards for future optimizations.

## Docling and Marker on the same inputs

The [combined report](results/features-models.md) adds 69 measurements: Docling
2.135.0 with formula enrichment off/on and Marker 2.0.0 in CPU fast mode with
OCR disabled. Together the studies cover seven libraries, 12 configurations,
and 276 case/configuration measurements. All Markdown outputs repeated exactly
over warmup and three measured conversions. This is repeatability, not proof
of content preservation. Original timings and resumed runs retain separate
provenance; structured artifacts were serialized outside the timer.

| Feature | What these configured runs show | Evidence |
|---|---|---|
| Internal destinations | Marker preserves the external URI and both internal links. Their emitted `#page-1-0` target exists as an explicit span ID beside the second page's destination heading. Docling omits these link annotations from Markdown. | [Link case](results/features-models.md#links-and-outline) |
| Unicode and invisible text | Docling retains three of four strict Unicode-CMap probes but loses the emoji sequence's ZWJ. Marker emits an image rather than any of the four text probes on this invisible-text fixture; that does not establish its behavior on all visible Unicode text. | [Unicode case](results/features-models.md#unicode-cmap-and-emoji) |
| Merged cells and literal pipes | Docling retains all five literal probes but collapses the three physical columns into two, combining body cells; its structured tree reports no merged span. Marker keeps three pipe-table columns but replaces the literal pipe inside one cell with a space. | [Merged table](results/features-models.md#table-merged) |
| Dense real-world table | Docling's pipeline logs that 952 of 1,363 PDF cells were dropped from an inferred 2×2 grid; its final structured table collapses to one cell. Conversion still returns successfully. The local pipeline log records this warning; success cannot be confused with complete extraction. | [Dense table](results/features-models.md#corpus-nics-background-checks-2015-11), local `bench/results/features-models.log` |
| Formula enrichment and OMML export | Enabling Docling's formula enrichment changes none of the 23 Markdown outputs. The positioned fraction is an embedded image, with a formula item nested inside its picture in the structured tree; the Office equation remains flattened text. Marker's OCR-off mode also disables equation recognition and produces empty Markdown on this Office export. These results do not test Marker with equation OCR enabled or establish a general limit on either library's formula models. | [Positioned math](results/features-models.md#positioned-math), [Office case](results/features-models.md#omml-equations) |
| ActualText math hint | Both added libraries retain the literal LaTeX already supplied in ActualText. Retaining the source hint is different from reconstructing fraction structure from painted glyphs. | [ActualText math](results/features-models.md#math-actualtext) |
| Column and RTL policy | Docling interprets the two-column prose as a table and misses its supplied reference order, but retains all three RTL probes. Marker misses the column reference and emits an image rather than the invisible RTL strings. | [Columns](results/features-models.md#two-column-order), [RTL](results/features-models.md#rtl-visual-glyph-order) |

The local Marker image references have four real JPEG assets saved beside the Markdown.
Docling embeds picture payloads in its output. Marker sidecars contain its
Markdown renderer output and metadata, while Docling sidecars contain its
native document tree; they are not interchangeable structured schemas.
The ignored local log retains the interrupted run and the benchmark's corrected PIL
artifact-serialization error. Successful rows were preserved and remaining
rows resumed; no failed or interrupted timing was silently presented as a win.
