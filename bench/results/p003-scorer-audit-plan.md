# Independent reference and scorer audit plan

Keep the existing strict scores and reference bytes unchanged. Add versioned business acceptance and tolerant alignment diagnostics beside them. The user accepts the newspaper rank/name presentation in either three or four columns; that establishes a documented schema ambiguity, without making missing rows, changed numbers or additional content correct.

A read-only inventory used only the already scored DEV16 and DEV276 targets and the frozen confirmation48 targets. It checked matching manifest/reference IDs and dataset identities, rectangular matrices, span bounds and overlap, literal types and representation features. No protected heldout paths were accessed. Confirmation observations below describe the reference contract; they do not select an inference configuration or change model evidence.

| References | Pages / structurally scored | Tables | Literal anchors | Covered null slots | Empty literals | Tables with merged anchors | LaTeX-like literals | Percent literals / spaced percent | Numeric whitespace literals |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DEV16 | 16 / 16 | 53 | 2,333 | 11 | 41 | 2 | 21 | 16 / 1 | 0 |
| DEV276 | 276 / 220 | 249 | 8,897 | 112 | 172 | 23 | 134 | 39 / 1 | 7 |
| Confirmation48 | 48 / 48 | 66 | 4,203 | 232 | 285 | 21 | 47 | 280 / 3 | 3 |

No dimension, span-bound, span-overlap or literal-type flags occurred. No stored literal required NFC conversion, and no HTML sub/sup markup was detected by this inventory. These checks establish internal reference consistency, not visual or semantic correctness. DEV16 overlaps DEV276 and must not be counted as independent evidence. The 56 unadjudicated DEV276 pages remain diagnostic, with no invented structural gold.

The ignored receipt `pipeline-p003/reference-audit-v1/inventory.json` records each original manifest/target SHA and the aggregate checks. Neither reference targets nor frozen prediction artifacts were rewritten.

## Proposed acceptance and alignment contracts

1. **Strict primary:** retain the exact existing geometry match, row/column/span identity and NFC/Unicode-whitespace-normalized literal comparison. Historical reports stay reproducible. Label red cells as strict disagreements; a visual annotation disagreement is not automatically lost source text.
2. **Schema equivalence:** allow a single globally consistent, monotone mapping of adjacent column groups over the entire matched table, including headers and all rows. The rank/name example may join or split a contiguous column boundary while preserving the ordered literal content. Preserve case, punctuation, numbers and math. Keep blank anchors distinct from covered slots. Reject a transformation when a merged or vertical span cannot be represented exactly. Do not choose a different column partition for each row.
3. **Tolerant content diagnostic:** align rows monotonically, permitting explicit missing/inserted rows, and align ordered cell groups monotonically within matched rows. Both prefix and suffix matches receive credit. Insertions, deletions and substitutions all incur cost; inserted middle columns and missing middle rows cannot shift later correct content into an all-wrong result, or disappear without penalty. Report reference content recovered and predicted content supported separately, together with missing/extra content and the actual alignment. A single similarity number must not hide a hallucinated column.
4. **Completion:** tolerant partial content is never promoted to a complete table. A business-accepted complete table needs all rows, representable spans and the complete ordered content under the declared schema-equivalence grammar. Partial predictions and operational failures retain their existing explicit scopes and full denominators.

A bounded dynamic program can implement monotone row/cell alignment with explicit adjacent joins/splits. Freeze edit weights, join separators, blank handling, span restrictions and resource caps before comparing models. If an alignment cap is exceeded, report the diagnostic as unavailable; do not truncate the table. Keep structural alignment separate from optional representation equivalence: the current strict normalizer does not interpret LaTeX, Unicode subscripts or rendered mathematics, and a general math-equivalence claim requires its own finite reviewed grammar.

Whitespace must not erase token boundaries. `1 23` differs from `12 3`; `10` differs from `1 0`. Joining rank `1.` and name `Hingham` must preserve both lexical tokens and punctuation, rather than obtaining equivalence through unrestricted removal of spaces. An empty inserted column is a structural difference even if it carries no text; disclose whether the business contract accepts it.

## Validation inventory

| Fixture | Required result |
|---|---|
| User-reviewed rank/name three vs four columns | Strict disagreement remains; schema equivalence succeeds only with one global adjacent mapping and complete ordered rows/header content. |
| Missing middle row with intact prefix and suffix | Both intact portions receive partial credit; the missing row remains a deletion and table completion fails. |
| Inserted middle column with intact later columns | Later correct content aligns; extra literals reduce prediction support and the column remains explicit. |
| First/last row or column missing | Symmetric boundary handling; neither prefix nor suffix alone gets complete credit. |
| Numeric token boundaries, decimal/sign/percent changes | `1 23` vs `12 3`, `-2` vs `2`, `1.2` vs `12`, and `10%` vs `10` remain content disagreements. |
| Row/column swaps or repeated labels | No free reordering, reuse of one matched literal, or arbitrary anchoring to duplicate strings. |
| Split/join valid only for selected rows | Global schema equivalence refuses; any tolerant local recovery is disclosed as partial. |
| Blank anchor vs covered span slot | Topology remains distinct; no deletion of an empty anchor to make dimensions agree. |
| Horizontal and vertical merged spans | Exact representable transformations only; crossed or unrepresentable spans refuse equivalence. |
| LaTeX reference vs Unicode subscript output | Strict remains unchanged; no math acceptance without a separately versioned supported representation rule. |
| Entire extra table / missing table / negative page | Existing geometry matching and full table/page denominators retain the false-positive or missing penalty. |
| Malformed output, failed generation, selected partial diagram crop | Existing operational/quality scopes stay explicit; no historical fallback or ineffective proposed state receives credit. |
| Identical input / fully different input / empty tables | Exact identity reaches full preservation; unrelated content does not; empty denominators are explicit. |
| Resource-cap refusal / very dense page | No partial diagnostic presented as complete; runtime and memory limits are reported. |

Run these scorer tests before applying a new diagnostic uniformly to the declared DEV generation, official TATR and rolling-control arms. Retain per-table alignments and unmatched output for independent visual review. Audit reference ambiguities from source images and the original annotation representation; record accepted alternatives in a versioned evaluation policy, rather than editing gold to fit a model.
