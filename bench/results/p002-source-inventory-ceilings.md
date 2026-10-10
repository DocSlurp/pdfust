# P002 natural16 retained source inventory ceilings

This is an offline DEV diagnostic of the fixed sixteen-page inventory. It uses
all 53 reference tables and 2333 annotated anchor cells; covered merged slots
are excluded by the same canonical anchor function as the authoritative scorer.
No requests, routing, detector choices, or source extraction use reference text.
All sixteen retained page inventories are available in each measured arm. The
300-dpi arm also retains all sixteen inventories, including its failed output page.

| Cached source arm | Literal-join feasible anchors / 2333 | Tables with all anchors feasible / 53 | Whitespace-free feasible anchors / 2333 | Whitespace-free table bound / 53 |
|---|---:|---:|---:|---:|
| Legacy150 (`natural16-generate-sonnet`) | 1194 | 6 | 1451 | 14 |
| Whitespace150 (`natural16-generate-whitespace`) | 1238 | 6 | 1449 | 14 |
| Whitespace300 (`natural16-yolo-ocr300-matrix-haiku-1024`) | 1880 | 9 | 2110 | 23 |

There are 41 empty anchors, included in every cell bound and counted separately
in the retained JSON. Empty source-ID collections can produce these strings.
Feasibility permits arbitrary whole-page token order and unlimited reuse across
and within cells. It ignores geometry, region clipping, source-ID exclusivity,
parser slot admissions, topology, and simultaneous ownership. These are necessary
text bounds, not achievable accuracy or complete-table predictions.

The literal parser builds cell strings with ASCII-space joins of whole source
word strings (`pipeline_assembly._clean_table`). The authoritative scorer then
normalizes NFC and collapses Unicode whitespace. Because the inserted ASCII
space blocks cross-token canonical composition, normalized joins factor into
space-joined, nonempty normalized tokens. A dynamic program checks exact
segmentation under these semantics. Thus a cell rejected by this optimistic
literal-join check cannot be exact under that source-ID parser, even if a model
places every token perfectly. Whole tokens cannot be split or characters added.

A second, more permissive check canonically decomposes both gold and tokens to
NFD and removes all Unicode whitespace before segmentation. This allows repairs
the actual parser cannot perform, such as joining separate `12` and `kg` tokens
into `12kg`, and admits canonical composition across removed boundaries. It
preserves case, punctuation, numbers, and math. Even this relaxation leaves
882 legacy, 884 whitespace150, and 223 whitespace300 anchor strings infeasible.

The posthoc density split retains the primary sixteen-page denominator. The
remaining fourteen include four negatives; these are diagnostics, not newly
selected evaluation cohorts.

| Diagnostic | Expected anchors | Legacy literal / relaxed | Whitespace150 literal / relaxed | Whitespace300 literal / relaxed | Literal table bounds: legacy / 150 / 300 |
|---|---:|---:|---:|---:|---:|
| Two dense newspapers | 1972 | 912 / 1145 | 956 / 1143 | 1591 / 1794 | 3 / 3 / 6 of 39 |
| Remaining fourteen | 361 | 282 / 306 | 282 / 306 | 289 / 316 | 3 / 3 / 3 of 14 |

Both text supply and assembly limit current results. Legacy source text imposes
an optimistic ceiling of 1194 cells (51.2%), while the source-ID Sonnet run
actually recovers 295 exact cells. Whitespace changes the ceiling to 1238 (53.1%)
but recovers only 236 exact cells. The much lower observed quality cannot be
explained by unavailable text alone: topology, detection, token placement, and
exclusive ownership also lose feasible cells. Dense pages have a particularly
low text ceiling, and complete recovery of all their tables is impossible under
these inventories. The relaxed ceiling further shows that whitespace joining
alone cannot restore their missing literal content. These bounds do not identify
which model intervention will improve the remaining assembly loss.

Whitespace300 raises the literal ceiling by 642 cells over whitespace150,
including 635 on the dense pair and seven on the remaining fourteen. Its
1880-cell ceiling (80.6%) still leaves 453 exact strings unreachable, while
the actual combined YOLO/arrays/1024-pixel Haiku arm recovers 387 exact cells.
Text supply improves substantially, but assembly remains the larger observed
gap to this optimistic bound. This is an offline inventory comparison: the
run also changes image resolution and evidence representation, so its actual
score gain cannot be attributed to OCR DPI alone. Unlimited reuse and arbitrary
ordering make these bounds much more permissive than valid source ownership.

Reproduce with `.venv/bin/python -m bench.generalization_inventory_ceiling
--corpus <artifacts>/pipeline-p002/screens/natural16
--run <artifacts>/pipeline-p002/natural16-generate-sonnet
--run <artifacts>/pipeline-p002/natural16-generate-whitespace
--run <artifacts>/pipeline-p002/natural16-yolo-ocr300-matrix-haiku-1024
--output <artifacts>/pipeline-p002/regions-audit/inventory-ceilings.json` on one
line. The CLI verifies corpus identity and each retained result's exact equality
with its report, preserving source/report hashes and arm settings in ignored
JSON. Missing inventories remain unmeasured and expand the upper interval;
they are never counted as impossible strings. Six focused tests verify literal
joins, Unicode normalization, whole-token limits, reuse, empty/missing sources,
and merged-anchor denominators.

Dataset identity:
`68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.
Legacy report SHA256:
`ea7ec4d8931af39faadeba3049c5d8d050b9505b6c5362674408b8c9cfaf3ffe`.
Whitespace report SHA256:
`1e3f530410128362229f6c421840aef3564fd6ec7a9e58a9ad859963fb389c23`.
Whitespace300 report SHA256:
`539628cf1548302d9c668b38dfe731270bb7c687f5c237fa086efa9a530fc518`.
The single-process CPU-only replay took 0.735 wall / 0.732 process CPU seconds,
measured with `time.perf_counter` / `time.process_time` across corpus loading and
all three arms. RSS is unmeasured. Remote requests and charges are zero. Concurrent
root tests/inference preprocessing may affect elapsed time.
