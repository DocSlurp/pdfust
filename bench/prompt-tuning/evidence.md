# Evidence-focused admission prompt registry

Five generic variants change only `questions.q0.instructions` in the frozen A002
admission request. Candidate criteria, IDs, strings, geometry, complete matrices,
image bytes/mapping, model, other questions, and request metadata remain exact.
The transformer deep-copies the body. Registry lookup performs no file access,
scoring, credential access, network request, OCR, or inference.

| Variant | Hypothesis |
|---|---|
| E001_balanced_evidence | Consistent standards across text, geometry and pixels improve admission without privileging one representation. |
| E002_cross_cell_relations | Explicit row-record relationships distinguish tables from independent aligned prose. |
| E003_reading_order | Local reading continuity exposes mistaken joins and prose columns. |
| E004_counterevidence | Comparing a strong candidate with a competing explanation improves both acceptance and rejection. |
| E005_image_geometry_consistency | Mapping retained boxes to page appearance exposes conflicts while respecting uncertain or overlapping geometry. |

Every variant preserves complete-candidate selection, `not_table` and
`unresolved`. Source text stays data. Candidates are hypotheses; first bands do
not automatically become headers. No prompt repairs an offered candidate or
invents words, IDs, cells, spans, or missing content. No fixture-specific names,
expected outputs, gold labels, cohort frequencies, known failures, or image
answers inform these instructions. The reading-order variant supplements the
structural registry's wrap focus with column-prose continuity; the visual
consistency variant addresses retained-box versus pixel disagreement.

Use `variants()` and `transform(body, variant)` from
`bench.prompt_variants_evidence`. The transformer accepts either a registry
record or its name. Keep the original unmodified prompt as a separately labeled
control; these variants do not silently replace that baseline. Freeze each
transformed body's hash before hosted evaluation, and retain full outputs,
errors, token usage, positive reported charges or labeled estimates, and
per-page agreement/abstention. Compare table admission and complete structural
selection separately. An increase in abstention is not automatically a quality
improvement. Prompt byte/token length and text/image arm differences belong in
the cost comparison. Public and authored DEV observations do not establish
independent confirmation or calibrated confidence.

This registry has not yet been scored. Hosted evaluation remains the parent
runner's responsibility and spending authorization; this work makes no paid
requests.
