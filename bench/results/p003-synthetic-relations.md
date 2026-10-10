# P003 source-frozen synthetic relationship quality set

2026-10-10. New repository-authored PDFs only; no existing corpus, labels,
model responses, references, credentials, hosted calls or GPU work are used.
Seed: `p003-synthetic-relations-20261010-v1`.

The pool has 24 one-page cases: eight each for same-cell, same-logical-row and
cross-physical-line continuation questions, balanced four same/four separate
per kind. Each question targets two generator-predeclared literal identities.
Eight unique opaque seven-letter words per page vary independently of labels;
actual extracted IDs are ordinal `wN`, with no label prefix. Case order is
opaque hash order. All 24 PDFs extract exactly eight words, 192 words total;
missing, additional, merged or duplicate literal identities would refuse the
question while preserving its intended case in the denominator.

Four paired design families vary column spacing, vertical leading, continuation
indent, monospace versus proportional type, header placement and ruling. Target
geometry within each same/separate family is matched; visible separators,
enclosing table boundaries or continuation layout provide different evidence.
For example, different tables can share one physical baseline, and two physical
baselines can belong to one logical row. Long horizontal distance does not
always imply a different cell. These controls avoid a single distance or baseline
shortcut, but this small authored set is not a natural-table accuracy estimate.

Six borderless cases (one same/separate pair per kind) deliberately lack visible
evidence that uniquely determines the hidden author memberships. The gold
sidecar marks these limitations explicitly. They must remain in the complete
operational denominator and receive a separate ambiguity/abstention analysis;
hidden-label agreement is not proof that these labels are recoverable. Nor does
the remaining construction inventory prove that every decision is uniquely
determined. Opaque words isolate geometry and supply no natural semantic
continuation cues; that limitation should be retained when interpreting results.

The source-only immutable authority is
`pipeline-p003/synthetic-micro-relations-v1/frozen.json`, SHA256
`2ea7284702fa6499061325db7626ff174e977454ac2b21430c5d89541aed105f`.
It was written before the separate `private-gold.json` sidecar (SHA256
`6be9e8a737a28e69f1fbc775704b2a509a46e0bd25211313df3b74ba9906501b`).
The sidecar is excluded from source artifact hashes, source records, packets
and requests. It records generator-owned cell/row/table/sequence membership,
the actual literal-to-source-ID receipt and extraction/source hash, rather than
inferring labels from source geometry. The report SHA256 is
`6a3ca3491f5d46ffbd3c52f251cce95db3eb27ac91d195ad7af68a62c63b2d4e`.
No source changes should occur after scoring attaches.

Two independent text treatments retain **all eight literal words and exact
display boxes**: `text_geometry`, and `rows_rules`, which adds mechanically
observed physical rows and actual PDF drawing segments. Physical rows are not
asserted to be logical rows. There are 96 exact packet files, covering those
two treatments with explicit pixels-available flags, 926–6,039 UTF-8 bytes.
The declared 128 KiB admission cap refuses the whole question rather than
truncating words. Omitted word count is zero throughout.

Images are independent treatments: text only, actual whole-page RGB PNG128 or
PNG512, and actual source-word-bounds crop PNG128 or PNG512. The crop bounds
are the complete extracted-word union plus 24 display points, clamped to the
page, independent of hidden membership. All words are inside both viewports;
the crop can exclude or clip peripheral drawing context, so it is not identical
to the full-page evidence scope. The 96 deterministic images total 531,205
encoded bytes. Each receipt retains the viewport, dimensions, encoded size,
SHA256 and exact mapping: render the page at edge/max(viewport extent), round
display bounds times scale to integer crop boundaries, no resampling, lossless
RGB PNG with compression level6. Images contain actual source pixels, not
occupancy diagrams. Native instructions explicitly treat strings/pixels as data
and allow `unresolved`. Criteria match the existing micro same/separate/unresolved
contract; model/provider identity is supplied explicitly later.

Proposed preregistered quality comparison: independently configured models,
the same 24 pair identities, text geometry versus enriched rows/rules, then
page/crop image128/512 as separate factors. Report strict response validity,
abstention, same/separate confusion and paired choice changes. Keep six declared
underdetermined cases separate from visibly cued construction cases. Preserve
every failure and unattempted question; no fallback, immediate retry, automatic
model/provider escalation or implicit credit. No quality has been measured yet.

Pure helper `bench/p003_synthetic_relations.py` exports `plans`, `authored`,
`extract`, `packet(record, mode, pixels_available)`,
`request(record, model, mode, image_url)` and `image(pdf, edge, viewport)`.
`bench/p003_synthetic_relations_prepare.py` freezes six dependency files,
source/PDF/image/packet hashes and all intended records before writing gold.
Before any hosted runner, root should approve those archived bytes against
Git independently and rebuild selected packet/image/request evidence using
authenticated current helper code, not trust the pool's self-recorded digest.

Five tests verify generation balance and memberships, exact extraction and
literal conservation, omitted-label fields, duplicate/missing refusal,
deterministic source pixels and source-before-gold freezing. Ruff and Mypy pass.
Preparation was one sequential process with OMP/OPENBLAS/MKL=1 and
RAYON=2: 2.957 wall seconds, 2.895 process CPU seconds, 539,156 KiB unsampled
`getrusage` lifetime peak RSS including imports. No child workers or downloads.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=2 \
  python -m bench.p003_synthetic_relations_prepare --output NEW_IGNORED_DIRECTORY
```
