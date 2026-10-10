# P002 independent natural-table evaluation

`bench.generalization_scoring` evaluates reference annotations offline. It imports
only the existing deterministic Hungarian assignment helper; it imports no
inference, extraction, corpus generation, assembly, provider or credential code.
The runner must receive source-only manifests and source-owned states. Private
references, raw annotation HTML, table polygons and annotation errors stay in
separate evaluation artifacts. Replacing private references must leave retained
model request bodies byte-for-byte unchanged. Record that audit alongside model
body hashes and the runner's source-field allowlist review.

## Reference and prediction interface

`parse_annotation_html(html)` returns the unchanged `annotation_html`,
`structural_scored`, `annotation_errors`, and `tables`. Each table has
`row_count`, `col_count`, a rectangular `values` matrix, and `spans` containing
zero-based `row`, `column`, `row_span`, and `column_span`. Empty anchor cells are
empty strings; covered span slots are `None`. A cell's four coordinates define
its structural identity, including unmerged 1-by-1 cells. Optional table `bbox`
uses display-coordinate `[x0, y0, x1, y1]`, shared with predictions. Only attach
boxes after converting original annotation polygons to the same page space.

Explicit rows and closing cell/table tags are required. Zero/negative/noninteger
spans, overlapping spans, spans beyond explicit rows, ragged tables, nested
tables, unbalanced inline markup, image-only cell content and script/style cell
content invalidate the annotation. The complete annotation is unscored, rather
than repaired or partially scored, and its original remains available for
review. The parser caps 4,096 grid slots and 256 tables. Annotation parse failure
is distinct from extraction failure. Native PDF diagnostic pages without
independent references remain unscored.

`score_dataset(targets, predictions)` accepts a `pages` reference object or page
list, plus P001 result rows with `id`, `status`, `tables` (or `observed`), or
`state.tables`. Duplicate or unknown IDs are rejected. Omitted predictions are
missing failures. Every frozen manifest page appears in the result. Structured
reference validation can also abstain on malformed directly supplied matrices.
Malformed successful prediction matrices invalidate the complete page output.

## Matching and separate metrics

Matching is maximum-weight one-to-one, so duplicate predictions cannot earn
multiple credits for one reference. Where both tables provide geometry, IoU at
least 0.1 admits a pair; geometry determines matching, with cell topology only a
small tie breaker. A pair with disjoint geometry never matches merely because
its contents or dimensions agree. `geometry_matches`, `geometry_iou_sum` and
`geometry_expected_tables` permit geometry recall and all-reference mean IoU;
missing and failed outputs contribute zero overlap. Report the 0.1 admission
threshold with results; it identifies candidate correspondences, not strict
localization success.

Without paired geometry, a single reference and single prediction are paired
explicitly as `single_table`. Multi-table matching requires character-multiset
Dice similarity at least 0.2, with topology as a small tie breaker, and is labeled
`text_assisted`. This cue is never a correctness metric. Neither fallback proves
geometric detection, and natural results should report their counts separately.
Shape alone cannot match unrelated multi-table outputs. Severe OCR errors may
prevent text-assisted multi-table matching; retain that limitation and prioritize
independent annotation boxes where available.

Metrics retain integer denominators rather than averaging only successful pages:

- `presence_correct` counts successful positive/negative page presence decisions;
  `positive_page`, `negative_page`, `false_positive_page`, missing and extra table
  counts disclose class balance and false alarms. Presence is count-based, not
  geometric localization.
- `correct_structure_cells` counts identical anchor rectangles, independently of
  text. Divide by `expected_cells` for recall or `predicted_cells` for precision.
  `penalized_cells` is the structural union denominator, including missing,
  extra, and altered rectangles.
- `exact_rows`, `exact_columns`, and `exact_table_spans` measure dimensions and
  full anchor topology independently of OCR. Unmatched targets receive zero.
- `correct_text_cells` and `exact_table_cells` compare normalized text at anchor
  row/column positions, ignoring span dimensions. Thus span errors can coexist
  with correct anchor text. `complete_tables` requires both topology and text.
  Divide complete tables by `table_denominator`, which counts every reference
  plus unmatched predictions. `exact_page` additionally requires no extras.
- `text_edit_distance` is exact character Levenshtein distance per aligned anchor
  position, charging all missing reference text and all extra prediction text.
  `reference_characters` includes every scored target, including failures.
  CER is distance/reference characters and can exceed one. A zero-character
  denominator is undefined, not zero. This is a positional table text measure:
  row/column displacement can penalize it even when page OCR words are correct.
  It is not a standalone raster OCR benchmark.

`pages`, `scored_pages`, `diagnostic_pages`, and `all_page_errors` disclose all
failure denominators. Diagnostic pages count operational errors without
fabricating structural or text quality scores. Do not report unscored annotations
as exact failures or silently remove failed scored pages.

## Text policy and limitations

Normalization is Unicode NFC plus collapsing Unicode whitespace to one ASCII
space and trimming ends. HTML entity decoding happens during annotation parsing.
Inline markup contributes literal text in source order (`x<sup>2</sup>` becomes
`x2`); line breaks contribute whitespace. Literal LaTeX commands and delimiters
remain literal. Case, accents, punctuation, minus signs, digits, ligatures,
mathematical symbols and OCR confusables are preserved. No regex strips markup
from prediction cell strings, no formula simplification converts LaTeX to plain
text, and no broad punctuation removal inflates equivalence. Consequently
semantically equivalent alternative formula encodings may score as different;
publish examples and the unchanged annotation for review.

The schema does not distinguish header-cell semantics, visual borders or pixel
visibility, and geometry evaluation is table-level rather than per-cell. Limits
are conservative reference/output bounds, not a security parser for arbitrary
HTML. Levenshtein scoring is CPU-only and quadratic in individual cell text
length; retain measurements when evaluating unusually long annotations.

## Leakage audit and validation

`audit_model_body(body)` traverses structured request dictionaries/lists and
reports explicit private-reference fields, including annotation, gold, targets,
answers and ground-truth keys. This catches schema contamination only. It cannot
prove the absence of paraphrased answers hidden inside arbitrary strings; source
words are allowed to overlap reference text. Audit serialized tool/message
content separately and inspect the runner import graph and source-only allowlist.
The evaluation module and private targets must never enter the inference path.

Focused Python tests cover rowspan/colspan, malformed/incomplete annotations,
inline math, wrong dimensions, missing/extra tables, duplicate tables, geometry
matching independent of OCR and table order, malformed predicted spans, failure
denominators, conservative normalization, P001 state adaptation and nested
request-field contamination. No protected heldout artifact is used.
