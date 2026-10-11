# Independent review of dual-score audit v2

The completed 26-run audit and six-file authority match Git `191cbb5` and current replay code. Seven focused audit tests pass. Independently re-admitting all 26 pinned report/evaluation/frozen/manifest sets confirms exact prior strict totals and page-score equality. No original primary score or target changed.

All 1,160 matched pairs are supported by the validated anchor-row span adapter. Every pair and aggregate satisfies `matched + substituted + missing = reference_units` and `matched + substituted + extra = prediction_units`. Missing and extra tables contribute unmatched normalized anchor characters; error pages contribute no predictions while keeping their reference tables. The 32 schema additions correspond to six distinct page/table cases, not 32 independent discoveries. Counting corpus-qualified entries gives seven because one academic page is shared between DEV16 and the larger corpus.

Reference units are alignment-dependent. Subtracting declared synthetic join separators gives a constant normalized anchor-character basis within each corpus:

| Corpus | Normalized anchor characters | Added reference join separators across runs |
|---|---:|---:|
| DEV16 | 16,640 | 0–85 |
| Natural64 | 27,350 | 0–57 |
| Confirmation48 | 21,342 | 0 |
| Full276 scored portion | 55,180 | 1–17 |

These counts explain all observed changes in reference-unit denominators. A matched synthetic separator is an alignment unit, not evidence that an additional literal source character was recovered. Report precision/recall as alignment-unit diagnostics, with synthetic spaces included. The per-pair `content.unit` declares this policy; the aggregate report has no `content.metric_scope` field, so its presentation must state the scope visibly.

The span adapter retains each complete anchor literal once in its top-left row and records covered slots and original spans. It does not validate semantic header ownership, vertical-span row meaning or physical column boundaries. Content recovery remains separate from schema acceptance; unsupported data must not receive fabricated zero scores. Exact schema additions follow a conservative lexical first-row-header proxy and still need source review. Blank padding or content preservation alone must not imply accepted topology.

This is a posthoc annotation-sensitivity audit of already authorized references, not a new tuning signal or an independent confirmation experiment. Overlapping corpora, repeated outputs and policy-based acceptance must remain visible. No inference, credential access, protected-reference access or frozen-output mutation occurred during this review.
