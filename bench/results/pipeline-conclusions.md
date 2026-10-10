# P001 conclusions: complete PDF-page pipeline experiments

The best completed DEV configuration uses original-format assembly evidence, column consensus, a cheap PPLX relational gate and selective Sonnet gate review. It achieves **168/168 exact scored pages, 35/35 exact positive tables and zero false-positive pages**, while producing complete outputs for **178/181 attempted pages**. It measures **72.36 complete pages/minute**, **1,725.88 complete pages/API USD**, and **USD 0.10313574** in provider-reported charges. This is a selected pipeline result on authored DEV data, not evidence that PPLX alone exceeds frontier model ability.

All **56 runs are complete: 31 balanced-pilot configurations and 25 full-cohort configurations**. The final readable-deduplication derivative ties the original format at 168/168 exact pages, 35/35 tables and 437/437 cell slots. It emits 178/181 outputs at 71.71 pages/minute and 1,754.59 pages/API USD, costing USD 0.1014482. Its retained source and candidate inventories match the original reviewed column configuration on all 178 comparable pages. The small cost difference is a single-run observation, not a demonstrated performance advantage. See the [complete comparison](pipeline-p001.md), [corpus design](pipeline-corpus-design.md) and [pipeline reproduction and demo](../PIPELINE_EXPERIMENTS.md#reproduce-the-complete-path).

| Full-cohort configuration | Exact / 168 | Positive / 35 | Negative FP / 133 | Outputs / 181 | Pages/min | Pages/API USD |
|---|---:|---:|---:|---:|---:|---:|
| Original + columns + PPLX gate + Sonnet review | 168 | 35 | 0 | 178 | 72.36 | 1,725.88 |
| Readable deduplication + columns + PPLX gate + Sonnet review | 168 | 35 | 0 | 178 | 71.71 | 1,754.59 |
| Original + columns + PPLX gate | 164 | 35 | 4 | 178 | 114.12 | 25,915.71 |
| Original + PPLX gate + Sonnet review | 167 | 34 | 0 | 178 | 72.38 | 1,658.72 |
| Direct Opus, original, 512 px | 167 | 34 | 0 | 175 | 13.02 | 56.32 |
| Direct Sonnet, original, 512 px | 166 | 34 | 0 | 174 | 15.94 | 107.68 |
| Direct Sonnet, compact + columns, 512 px | 159 | 33 | 2 | 166 | 13.57 | 113.44 |
| Direct Haiku, original, 512 px | 149 | 34 | 18 | 175 | 22.02 | 2,092.66 |
| Compact + PPLX gate, 256 px | 160 | 31 | 4 | 178 | 113.93 | 29,823.14 |
| Compact + PPLX gate, text only | 156 | 28 | 5 | 178 | 102.10 | 31,226.86 |
| Compact + columns + PPLX gate + Haiku review | 154 | 31 | 10 | 177 | 81.55 | Unknown |

Rates count complete outputs, including diagnostics; quality uses the scored denominator. High pages/USD can accompany poor quality.

| Hypothesis | Result | Verdict |
|---|---|---|
| Cheap gating plus selective review can suppress prose admissions | Original gate review removes the four negative false positives; 12 Sonnet reviews contribute USD 0.096634 of the best configuration's total | Useful DEV-selected policy; review scores are uncalibrated |
| Column consensus can repair missing candidate coverage | Original reviewed pipeline improves from 34 to 35 exact positives and 167 to 168 exact pages | Retain as an explicit, measured candidate-generation option |
| Lossless packet compression preserves decision quality | Compact loses three exact wrapped positives despite exact decoded evidence | Codec correctness does not establish model readability |
| Images add useful evidence | Compact text-only falls from 31 to 28 exact positives and increases negative FP pages from four to five | Keep the image arm for this selected policy |
| A cheaper reviewer substitutes for Sonnet | Compact column Haiku review has ten negative FP pages and one PPLX admission HTTP 500 with unresolved expense | Reject this substitution on present evidence; complete pages/USD is unknown |
| Preserve literal composed values while deduplicating evidence | Readable shared cells recover all three wrapped-table losses: 35/35 positives, zero negative FP pages | Retain alongside original evidence; repeat before claiming a cost win |
| A frontier selector makes dense indexed packets safe | Compact column Sonnet reaches 159/168 exact pages, with nine truncated responses and two negative FP pages | No safe replacement under the fixed 1,024-token answer limit; columns and encoding change together |

The compact regression has a clean mechanical audit. Frozen records match; all 178 retained sources and candidate menus match; all 59 admission requests and answers match. Across the 25 assembly requests, criteria and image blocks match, and every compact packet decodes exactly to its retained source and candidates. Only three selections change: all are wrapped companion cases with 19 words and three alternatives. The model switches from a four-row assembly containing multiword wrapped cells to a sparse seven-row assembly that treats continuation lines as separate records. Packet length falls about 39%, but literal assembled cell strings become several layers of dictionary references. This supports a representation-associated failure; provider variability remains unresolved. See the [packet design](pipeline-compact-packet.md).

Image sizes refer to the longest page-image edge. The three original-format direct frontier controls each retain the same **175 requests**, equal after removing only the model field, with identical source/candidate inventories and image hashes. Their comparison supports a matched-input distinction between Haiku's false admissions and Sonnet/Opus behavior. Comparisons against gated/column pipelines involve different routing, candidate generation and 256 px rather than 512 px images; they measure whole configurations. Sonnet also has one scored truncation. Column consensus addresses their shared scanned-table candidate limitation.

The cohort contains 181 DEV pages: 168 structurally scored and 13 diagnostic. The scored set has 35 correlated, single-table positives and 133 negatives, making overall accuracy strongly influenced by rejecting tables. It is predominantly authored/synthetic, with related families and repeated exploration on DEV. Semantic roles, general prose reading order, math interpretation and completeness of natural-document extraction are unscored. Source conservation alone does not prove semantic correctness. Three persistent diagnostic failures remain in the best pipeline: two pages without admitted source text and one incomplete span tiling. Therefore 168/168 must never become “181 perfect extractions.”

Wall time includes CPU preprocessing and API waiting. CPU time and 100 ms sampled RSS cover one local process, including OCR initialization; the best configuration measures 66.32 CPU seconds and 547,733,504 bytes peak sampled RSS. Remote GPU resources, deployment infrastructure and comprehensive operating costs are unmeasured. Pages/USD uses API charges only; unresolved HTTP expense cannot be replaced by zero or a complete subtotal. The readable variant measures 65.06 CPU seconds and 539,107,328 bytes peak sampled RSS. See the resource table in the [complete report](pipeline-p001.md).

The wave made 3,127 fresh paid attempts: 2,796 have positive provider-reported charges totaling **USD 7.728498482**, and 330 Luna attempts use **USD 0.09586** in labeled catalog estimates while preserving their reported zero. One PPLX HTTP 500 retains **USD 0.30** of unresolved reservation. Known charges plus estimates are USD 7.824358482; conservative wave accounting is **USD 8.124358482 of USD 50**. Cumulative conservative accounting is **USD 36.6672001068 of USD 150**, including USD 6.35 of old and new unresolved reservations. Actual total expense remains incomplete until those reservations are reconciled. No GPU hosts were rented for this wave.

The inspected HTTP 500 received one explicitly scoped replacement during the readable run: entry 17423 references failed entry 17158 and reports USD 0.00002982. The original reservation remains unchanged. No automatic retry loop or local response replay was used. All 857 retained Anthropic responses report zero cached input tokens; 2,269 retained decision-model responses omit cache-token data, so their provider cache status is unknown. This wave does not establish a cache discount.

Next priorities are independent confirmation of the frozen original/readable configurations, mixed vector/borderless pages, bounded packet admission for natural diagnostics, and row edits restricted to already admitted tables. Protected heldout files were not accessed. All paid jobs have finished. Validation: 300 targeted CPU tests, repository-wide Ruff, and strict mypy across source, tests and pipeline modules (201 files) passed.
