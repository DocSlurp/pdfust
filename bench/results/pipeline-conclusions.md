# P001 conclusions: completed DEV experiments

The best completed DEV configuration uses original-format assembly evidence, column consensus, a cheap PPLX relational gate and selective Sonnet gate review. It achieves **168/168 exact scored pages, 35/35 exact positive tables and zero false-positive pages**, while producing complete outputs for **178/181 attempted pages**. It measures **72.36 complete pages/minute**, **1,725.88 complete pages/API USD**, and **USD 0.10313574** in provider-reported charges. This is a selected pipeline result on authored DEV data, not evidence that PPLX alone exceeds frontier model ability.

This draft uses the 54 completed runs in root `.scratch/pipeline-p001/aggregate.json` and verified retained reports. See the [P001 comparison](pipeline-p001.md) and [corpus design](pipeline-corpus-design.md). Direct compact Sonnet and the readable derivative remain **pending** here. Their outcomes and final cumulative accounting must be added after the wave drains.

| Full-cohort configuration | Exact / 168 | Positive / 35 | Negative FP / 133 | Outputs / 181 | Pages/min | Pages/API USD |
|---|---:|---:|---:|---:|---:|---:|
| Original + columns + PPLX gate + Sonnet review | 168 | 35 | 0 | 178 | 72.36 | 1,725.88 |
| Original + PPLX gate + Sonnet review | 167 | 34 | 0 | 178 | 72.38 | 1,658.72 |
| Direct Opus, original, 512px | 167 | 34 | 0 | 175 | 13.02 | 56.32 |
| Direct Sonnet, original, 512px | 166 | 34 | 0 | 174 | 15.94 | 107.68 |
| Direct Haiku, original, 512px | 149 | 34 | 18 | 175 | 22.02 | 2,092.66 |
| Compact + PPLX gate, 256px | 160 | 31 | 4 | 178 | 113.93 | 29,823.14 |
| Compact + PPLX gate, text only | 156 | 28 | 5 | 178 | 102.10 | 31,226.86 |
| Compact + columns + PPLX gate + Haiku review | 154 | 31 | 10 | 177 | 81.55 | Unknown |

Rates count complete outputs, including diagnostics; quality uses the scored denominator. High pages/USD can accompany poor quality.

| Hypothesis | Result | Verdict |
|---|---|---|
| Cheap gating plus selective review can suppress prose admissions | Original gate review removes the four negative false positives; 12 Sonnet reviews contribute USD 0.096634 of the best configuration's total | Useful DEV-selected policy; review scores are uncalibrated |
| Column consensus can repair missing candidate coverage | Original reviewed pipeline improves from 34 to 35 exact positives and 167 to 168 exact pages | Retain as an explicit, measured candidate-generation option |
| Lossless packet compression preserves decision quality | Compact loses three exact wrapped positives despite exact decoded evidence | Codec correctness does not establish model readability |
| Images add useful evidence | Compact text-only falls from 31 to 28 exact positives and increases negative FP pages from four to five | Keep the image arm for this selected policy |
| A cheaper reviewer substitutes for Sonnet | Compact column Haiku review has ten negative FP pages and one HTTP 500 with unresolved expense | Reject this substitution on present evidence; complete pages/USD is unknown |

The compact regression has a clean mechanical audit. Frozen records match; all 178 retained sources and candidate menus match; all 59 admission requests and answers match. Across the 25 assembly requests, criteria and image blocks match, and every compact packet decodes exactly to its retained source and candidates. Only three selections change: all are wrapped companion cases with 19 words and three alternatives. The model switches from a four-row assembly containing multiword wrapped cells to a sparse seven-row assembly that treats continuation lines as separate records. Packet length falls about 39%, but literal assembled cell strings become several layers of dictionary references. This supports a representation-associated failure; provider variability remains unresolved. See the [compact audit](pipeline-compact-packet.md).

The three direct frontier controls each retain the same **175 requests**, equal after removing only the model field, with identical source/candidate inventories and image hashes. Their comparison supports a matched-input distinction between Haiku's false admissions and Sonnet/Opus behavior. Comparisons against gated/column pipelines involve different routing, candidate generation and 256px rather than 512px images; they measure whole configurations. Sonnet also has one scored truncation. Column consensus addresses their shared scanned-table candidate limitation.

The cohort contains 181 DEV pages: 168 structurally scored and 13 diagnostic. The scored set has 35 correlated, single-table positives and 133 negatives, making overall accuracy strongly influenced by rejecting tables. It is predominantly authored/synthetic, with related families and repeated exploration on DEV. Semantic roles, general prose reading order, math interpretation and completeness of natural-document extraction are unscored. Source conservation alone does not prove semantic correctness. Three persistent diagnostic failures remain in the best pipeline: two pages without admitted source text and one incomplete span tiling. Therefore 168/168 must never become “181 perfect extractions.”

Wall time includes CPU preprocessing and API waiting. CPU time and 100ms sampled RSS cover one local process, including OCR initialization; the best configuration measures 66.32 CPU seconds and 547,733,504 bytes peak sampled RSS. Remote GPU resources, deployment infrastructure and comprehensive operating costs are unmeasured. Pages/USD uses API charges only; unresolved HTTP expense cannot be replaced by zero or a complete subtotal. See the [performance analysis](pipeline-perf-analysis.md).

Next priorities are readable deduplication with paired quality checks, bounded packet admission for natural diagnostics, and row edits restricted to already admitted tables. Freeze the selected configuration before any custodian-only heldout confirmation. Keep pending outcomes and cumulative accounting visibly unfinished until their complete artifacts are available.
