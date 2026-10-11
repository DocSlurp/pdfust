# Independent secondary content audit of random40 extraction

All six complete-pipeline receipts and their report/evaluation/frozen/manifest pins were re-admitted against the fixed six-run plan. Current six scorer digests match the audit receipt; every strict total equals the prior independent evaluation. All matched-pair and run-level alignment accounting identities hold. Original outputs and strict scores remain unchanged.

The table uses all 40 authored synthetic pages and all 36 expected tables. The secondary span-aware content comparison preserves each anchor literal once and reports span topology independently; it is a content diagnostic, not acceptance of altered merge/header meaning. An erroneous or omitted page contributes missing content, not retained-output credit.

| Model | Detector size | Strict complete /36 | Content-complete matched /36 | Full content precision | Full content recall | Matched units | Substituted | Missing | Extra | Operational errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Luna | 640 | 35 | 35 | 1.000000 | 1.000000 | 24692 | 0 | 0 | 0 | 0 |
| Luna | 1280 | 28 | 28 | 1.000000 | 0.937973 | 23182 | 0 | 1533 | 0 | 1 |
| Haiku matrix | 640 | 33 | 36 | 0.995645 | 1.000000 | 24692 | 0 | 0 | 108 | 0 |
| Haiku matrix | 1280 | 26 | 27 | 1.000000 | 0.924378 | 22846 | 0 | 1869 | 0 | 2 |
| Sonnet | 640 | 36 | 36 | 0.995645 | 1.000000 | 24692 | 0 | 0 | 108 | 0 |
| Sonnet | 1280 | 29 | 29 | 1.000000 | 0.904941 | 22362 | 0 | 2349 | 0 | 2 |

Luna640 aligns every reference and prediction text unit with no substitution, omission or added literal content. Its extra blank row and altered span topology still prevent one table from being content-complete under the whole-table row/coverage rule: 35/36 remains distinct from perfect aggregate text precision/recall.

Haiku640 recovers matched-table content in 36/36 rather than 33/36 strict complete tables. All three non-strict matched tables have different span topology, so recovered text does not establish correct merge semantics. Sonnet640 is already 36/36 strict complete. Both Haiku640 and Sonnet640 add a 108-unit table on a negative page; full precision is therefore below one even though every expected table’s content is recovered. These false positives remain failures in the primary report.

The 1280 arms retain missing content from absent/error pages and altered structures. No rule repairs their raw outputs or selects a smaller detector result as fallback. The original independently verified primary table remains [p003-random40-analysis.md](p003-random40-analysis.md).

Units are normalized Unicode alignment units, including declared synthetic join spaces. Reference totals vary with the alignment path (24,692–24,715 here); they are not a constant literal-character recovery denominator. Both run-level identities are checked: matched + substituted + missing = reference units, and matched + substituted + extra = prediction units. Empty rows contain no character units, while whole-table content completeness can still refuse them. Case, punctuation and numeric token boundaries are retained; span-anchor projection does not prove topology equality.

Pinned six-run plan SHA `79de964dfeff948b6e6ee597738001c21008c1a4bf6545e35dc0887686860abe`. Source report: ignored `pipeline-p003/random40-dual-score-v1/report.json`, version `p003-dual-score-audit-v2`. This evaluation-only annotation sensitivity review makes no new inference calls, changes no targets, and supplies no configuration tuning from fresh confirmation results.
