# P001 complete-page DEV corpus and evaluation

The frozen cohort contains 181 physical pages: all 125 pages from the existing
104-file silver DEV challenge, 28 borderless companion pages, and all 28 existing
structure cases. This preserves the five bundled natural-document diagnostics
rather than removing a page to meet an approximate cohort size. References are
constructed from authored layout operators and explicit values before extraction.
They are repository-authored silver, not independently adjudicated gold.

There are 168 structurally scored pages: 35 complete-table positives and 133
zero-table negatives. The remaining 13 pages have incomplete structural references
and are diagnostic-only. Natural Senate expenditure and NICS reports have partial
record spot checks, not complete table references; those checks are not promoted
to complete-page scores. Natural form, math and Type 3 pages likewise remain
unscored. The cohort includes wrapped cells, covered merged slots, regular and
ragged borderless tables, a raster-only table, right-angle rotations, prose
columns, numeric prose, forms, decorative panels and multiple math encodings.

The predefined pilot has 32 pages, balanced at 16 positives and 16 negatives.
Construction-order quotas select two pages from each original merged-table family,
four wrapped and four plain companion borderless pages, two companion ruled
controls, one wrapped-record structure case and one 90-degree table. Negatives
select one each from twelve original non-table layout families, two math pages,
and two numeric-prose companion pages. Membership is fixed without observing
pipeline results. The full cohort still contains every sibling and source family;
this pilot is a DEV screen, not an independent evaluation or a natural-document
accuracy estimate.

`bench.pipeline_corpus.build(directory)` writes `manifest.json`,
`private-targets.json` and `private-provenance.json` into an explicit ignored
artifact directory. Manifest `pages` have opaque page IDs, absolute PDF paths,
PDF SHA-256, zero-based page numbers, family, label status and pilot membership.
Only ID, PDF path, PDF hash and page number may enter the pipeline input;
family, pilot membership, provenance and all targets are scoring-only data.
Source document bytes are retained by content hash. Dataset identity includes
construction references and pilot membership but excludes machine-specific paths.
The final dataset SHA-256 is
`3a1268f1d731a7c60a3fa91f1e90e887c3f41a84aec05beed81b797253afa9b2`.

Targets contain complete logical matrices and anchor spans; merged covered slots
are `None`, ordinary empty cells are empty strings. Values normalize whitespace
only, so physical wraps may join without changing words, punctuation or digits.
Coordinates are not exact semantic gold for borderless cells. Logical matrices
retain authored reading orientation across page rotations. No references come
from native table detector or model output.

`bench.pipeline_scoring.score_dataset(targets, predictions)` evaluates every
expected page. A prediction has `id`, `status`, and `tables` (or `observed`). Tables
contain `row_count`, `col_count`, `values`, and `spans`, whose entries use `row`,
`column`, `row_span`, and `column_span`. Maximum-weight one-to-one assignment
prioritizes complete tables, then intended-slot matches among equal shapes.
An exact page requires every complete value matrix and span topology, no extra
tables, and successful output. Missing outputs, errors and malformed matrices
remain in page, table and expected-cell denominators; malformed output receives
no partial credit. Unmatched shapes count as both missing and extra tables.
Extra/duplicate tables also enter a penalized table denominator and a separate
penalized cell denominator. Reports should publish complete tables / table
denominator, exact pages / scored pages, exact cell/spans / expected tables,
correct cells / expected slots, correct cells / penalized slots, missing tables,
extra tables, negative false-positive pages and errors together.

`conservation(source_ids, assigned_ids)` reports missing, duplicate and unknown
snapshot source IDs separately from structural scoring. Conservation does not
establish semantics, text visibility, correct reading order, formulas, form
relations, image interpretation, headings or complete document correctness.
These table/non-table references support a complete operational pipeline
experiment; they do not support a general extraction-accuracy claim.

CPU validation used the main workspace virtual environment with the isolated
worktree on `PYTHONPATH`, without rebuilding the Rust extension. Eleven Python
tests cover corpus identity and pilot balance, merged covered slots, whitespace
wrapping, duplicate/missing tables, unordered multi-table assignment, span errors,
negative false positives, malformed output, error denominators and conservation.
Ruff passes for the three Python files. One worker built the cohort in 0.165s
wall / 0.187s process CPU; current-executable peak RSS was 118,181,888 bytes.
Tools were `perf_counter`, `process_time` and Linux `/proc/self/status` `VmHWM`;
RSS includes imports and native generated-case construction, including a small
150-dpi scanned derivative. CPU covers process threads; no subprocess workload
was launched. Counters/high-water values were read at completion without periodic
sampling. These are preparation observations, not pipeline throughput claims.
No network, paid inference, GPU workloads or protected heldout inputs were used.
