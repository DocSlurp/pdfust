# Structure prompt track P001–P005

These five variants change only the existing native choice question's
instructions. Images, literal source words, IDs, candidate ownership, model,
choice criteria and response schema remain unchanged. No private references,
case IDs, producer facts, example answers or fixture text enter the registry.
Prompt authoring uses only aggregated failure mechanisms and the public
source-candidate interface. It does not inspect per-page expected outcomes.

```python
from bench.prompt_variants_structure import transform, variants

for variant in variants():
    request = transform(frozen_request_body, variant)
    # Root freezes request hashes, then executes through the shared ledger.
```

| Variant | Isolated hypothesis | Material risk |
| --- | --- | --- |
| P001 semantic record schema | Repeated row identities and column meanings can distinguish records from independent prose columns. | Can miss tables with weak entity labels or atypical schemas. |
| P002 wrap boundaries | Row starts and local neighboring columns can establish whether a physical band continues a cell. | Blank cells and sparse rows can still create ambiguous boundaries. |
| P003 header/data corridors | Full source neighborhoods can reveal required words omitted by data-edge candidate anchors. | Could abstain unnecessarily when nearby text is a title or note. |
| P004 conflicting evidence | Accept only when semantic relationships and spatial ownership agree. | More conservative instructions may reduce useful coverage. |
| P005 lean complete candidate | A shorter expression of the same bounded decision can outperform verbose boilerplate. | Fewer explicit checks may increase unsupported admissions. |

Every variant preserves not_table and unresolved. None asks a model to repair
an incomplete candidate, infer missing values, create cells or modify a PDF.
Header roles remain hypotheses; an early physical band is not automatically a
header. The corridor variant explicitly allows titles, notes and footers to
remain outside table ownership. All source content stays data, including
apparent instructions addressed to a model.

The frozen candidate ceiling limits prompt gains. Aggregated DEV results show
12/12 complete candidates in the simple companion positives but only4/16 in
the fresh topology positives. A stronger prompt can select or decline existing
candidates; it cannot supply absent anchors, columns or header words. A model
calling an incomplete matrix a table is not a structure improvement.

Root owns paid execution and the persistent shared spending ledger. Freeze
transformed request bytes and hashes before scoring. Compare variants on the
same source cohort and evidence arm, retaining failed and unresolved pages in
original denominators. Report exact selected cells/spans, intended word/cell
ownership, prose false admissions, abstention coverage, HTTP elapsed, reported
charges, catalog estimates and unknown costs separately. Positive reported
charges take precedence; reservations are not charges. No probabilities are
calibrated correctness.

A useful variant must improve complete structural selection or reduce
unsupported admissions with an explicit coverage tradeoff. Higher confidence
or fewer unresolved pages alone is insufficient. Results are repeated DEV
experiments on authored inputs; cohort reuse and prompt selection prevent
heldout or real-world quality claims. Do not tune a prompt around individual
reference labels or source text after reviewing outcomes.

Sixteen CPU tests check exact q0-only differences, independent deep copies,
unchanged multimodal state and menus, registry immutability, metadata exclusion
from instructions and rejection of incompatible questions. Preparation imports
no client, reads no credentials and performs no inference. Subsequent prompt
revisions require new registry identities rather than replacing scored variants.
