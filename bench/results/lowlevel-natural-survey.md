# Natural DEV source survey

Six unadjudicated selectors from five redistributable PDFs are retained in `realdev/selectors.json`. Every selector has `evidence.task`, `question`, display-space `bbox`, exactly two `target.boxes`, and choices `join/split/unresolved`; source path, SHA-256 and zero-based page are explicit. They contain no expected decision or scorer gold. The JSON also retains crop-local native words, fresh source-order glyph rows, origin-selected target IDs and rendered-image paths. Target boxes select chunks, not necessarily single words. The meaning of joining a labeled entry must remain distinct from joining its lexical tokens.

## Selection and provenance

Selection used only the explicit `tests/assets/real_world/README.md` inventory/licensing, source PDF pages, newly extracted native words/glyphs, and newly CPU-rendered images. No test expectations, scorer gold, retained model outputs or heldout artifacts were read to select answers. I initially inspected page 0 of Senate, NICS, IRS, Japanese ministry and Edison patent, and pages 0–3 of the LaTeX guide. The selected LaTeX page is zero-based 2. All five final distinct crops below were actually viewed at 180 dpi with white backgrounds. Senate positive/negative candidates intentionally share one context image and are dependent controls.

This is a convenience sample of bundled regression sources, biased toward visually evident English entry boundaries, unfilled forms, ruled cells and document typography. It is not a random DEV sample, has no quality score, and does not establish prevalence. LaTeX hanging descriptions and IRS checkboxes are relation ambiguity controls; native words already preserve their individual strings. No clear natural overprint, ligature loss or producer-order failure was established in this bounded inspection. Japanese prose was not promoted because lexical join/split would require a stated Japanese segmentation policy; scans without substantive source text were likewise not useful controls.

The extension was the isolated worktree build containing the glyph snapshot and deterministic source-order fix, not the root extension or a frozen paid-wave artifact. Native extraction follows the library's normal fallback-font setup. Snapshot IDs are local to one fresh page interpretation; they are not stable document IDs or visibility proofs. Source glyphs are not model-generated tokens. Crop selection IDs use glyph origins inside boxes; boxes and origin tests are evidence selectors, not a definitive glyph visibility oracle.

## Selected regions

Paths below are relative to `/home/dan/code/oss/pylopdf/tests/assets/real_world/`. All coordinates are rotation-resolved display points; pages are zero-based.

### Senate transaction continuation and adjacent transaction

Source: `senate-expenditures.pdf`, page 0, SHA-256 `16921f0fc9b2c6039b23b694e0317917118ad7dd2b3a95a88518b7e144df527c`. US government public-domain report excerpt; source/mirror attribution retained in the inventory README. Context `[80,237,710,282]`; image `realdev/senate-description-wrap.png`.

`senate-description-wrap`, task `line_ownership`: boxes `[428.2,251.5,674.2,256.9]` and `[428.2,257.4,472.7,262.9]`. Native chunks are “AIRFARE FOR K FORD 3/21 WASHINGTON DC TO SAINT LOUIS, KANSAS CITY; 3/24 SAINT LOUIS TO” and “WASHINGTON DC”, physical lines `(block 2,line 7)` and `(2,8)`. Visible evidence: both appear below STAFF TRANSPORTATION beside transaction DHAW20190004 and amount 903.90, while the continuation has blank transaction-key/date/amount columns. This supports a continuation interpretation, without establishing the author's formal row semantics.

`senate-next-transaction`, task `line_ownership`: boxes `[428.2,257.4,472.7,262.9]` and `[428.2,263.3,506.5,268.8]`. Native chunks are “WASHINGTON DC” and “SENATOR'S TRANSPORTATION”, physical lines `(2,8)` and `(2,9)`. Visible evidence: the latter aligns with new transaction DHAW20190005 and amount 798.90. Shared x alignment and close line spacing alone cannot identify ownership; the neighboring columns are necessary evidence. Both cases preserve text and are candidates for a complete same-entry-versus-new-entry oracle after independent visual adjudication. They are not evidence of a lexical word extraction failure.

### NICS adjacent ruled numeric cells

Source: `nics-background-checks-2015-11.pdf`, page 0, SHA-256 `4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407`. FBI US government public-domain table; attribution in inventory README. Context `[110,59,185,98]`; image `realdev/nics-adjacent-numeric-cells.png`.

`nics-adjacent-numeric-cells`, task `character_boundary`: boxes `[126.8,80.2,144.5,86.4]` and `[159.2,80.2,176.9,86.4]`. Native words “18,870” and “23,022” already remain separate, both physical line `(0,4)`. The image shows a vertical rule and distinct Permit/Handgun headers between their columns. This is a source-derived separation control rather than a discovered regression. Existing vector-rule interpretation should likely settle it without a model. Oracle coverage is plausible for token separation with conserved source IDs; semantic association to a row label would require more context than this crop.

### IRS checkbox instruction continuation

Source: `f1040.pdf`, page 0, SHA-256 `3d31c226df0d189ced80e039d01cf0f8820c1019681a0f0ca6264de277b7e982`. IRS US government public-domain form. Context `[92,203,578,255]`; image `realdev/irs-checkbox-label-wrap.png`.

`irs-checkbox-label-wrap`, task `line_ownership`: boxes `[109.8,231.1,319.1,239.6]` and `[109.8,242.1,178.6,250.6]`. Native chunks “Married filing separately (MFS). Enter spouse’s SSN above” and “and full name here:” are physical lines `(8,11)` and `(8,13)`; right-column text occupies an intervening native line. The rendered form places both chunks under one left checkbox and beside one name field; the adjacent right checkbox has its own wrapped instruction. Native geometry is faithful, but a global next-line heuristic can cross columns. A same-checkbox-entry relation can preserve all text, provided the task states entry ownership; it is not a request to remove lexical spaces or concatenate into one word. The unfilled form supplies no value-reading or completed-field oracle.

### LaTeX required-argument hanging description

Source: `usrguide.pdf`, page 2, SHA-256 `79ce884d013bea5c13479385a7bd7a819fdbc138c49cbc0d7805e36f401e19f2`. LaTeX Project LPPL redistributable user guide. Context `[130,363,480,435]`; image `realdev/latex-required-argument-wrap.png`.

`latex-required-argument-wrap`, task `line_ownership`: boxes `[149.5,375.8,468.8,386.3]` and `[149.5,387.7,468.8,410.2]`. Native first chunk: “Given as R⟨token1⟩⟨token2⟩{⟨default⟩}, this is a ‘required’ delimited ar-”. Second chunk: “gument as for r, but it has a user-definable recovery ⟨default⟩ instead of \\NoValue.” Physical lines `(4,0)` versus `(4,1)/(4,2)`. The image shows a left R label and consistent hanging indentation, followed by a distinct v label. This is a promising labeled-entry ownership control, not a table-row assertion. A separate character-boundary query on `ar-`/`gument` would require an explicit discretionary-hyphen policy and is deliberately not selected: immutable source-text grouping cannot remove the printed hyphen by itself.

### Edison patent invisible OCR title

Source: `patent-us223898.pdf`, page 0, SHA-256 `e6f4d7747a8af8451d81aa3d5fe564aed5c8091091cb408c752b8a3cd7c28764`. 1880 US patent, public domain. Context `[240,60,360,106]`; image `realdev/patent-ocr-title-boundary.png`.

`patent-ocr-title-boundary`, task `character_boundary`: boxes `[293.1,70.7,309.4,86.9]` and `[312.5,70.7,350.2,86.9]`. Native words “ED” and “IS ON,” are split into three words ED / IS / ON, on the same physical line. The image visibly reads “T. A. EDISON.”. Source-order glyph rows explicitly contain spaces after ED and IS and a comma after ON, all draw mode `invisible`; this is a genuine visible/source-layer mismatch, not merely inferred geometry spacing. No Unicode callbacks were missing on the page.

A current text-preserving join/split candidate oracle is incomplete here: changing grouping does not remove encoded OCR spaces or correct the comma to a period. Do not claim a reachable gold or successful repair from this selector. It can probe abstention or motivate a separately specified OCR/source-alignment operation. Correct replacement spelling, punctuation and visibility provenance remain outside the retained source-glyph conservation contract.

## Resource measurement and reproduction

Run `realdev/select.py` using `/home/dan/code/oss/jev-pdf-lowlevel-native/.venv/bin/python` from that worktree. Explicit fixed source paths prevent artifact-directory walking. The selector generator uses six fresh Documents, bounded default snapshot caps, independent native text extraction and six 180-dpi CPU crop renders, with no workers or GPU. `realdev/resources.json` records 0.490 s wall, 0.505 s process CPU and 404,384 KiB process peak RSS using `time.perf_counter`, `time.process_time` and `resource.getrusage(RUSAGE_SELF)`; measurement is cumulative process scope, not per-crop peak or a performance comparison. Library crop rendering can still interpret/render the whole page internally. JSON retains full crop-local evidence and six selectors; no production files changed.

Next bounded use: independently adjudicate entry ownership with the displayed neighboring anchors, then freeze those decisions before comparing methods. Keep the patent as an explicitly incomplete-oracle abstention case. Treat the ruled NICS boundary as a deterministic control. Natural producer-order/overprint failures remain unknown from this survey; do not infer them from synthetic findings or extend these observations into corpus quality claims.
