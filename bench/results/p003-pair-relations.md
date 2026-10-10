# P003 bounded source pair relations: CPU preparation

Date: 2026-10-10 UTC. This prototype freezes a new relation candidate language
from complete source words and geometry. It does not reuse generated cell
strings, reference boxes, page-family labels, or prior model decisions. No
references, credentials, GPU, model weights, or hosted calls were used.

The authenticated DEV16 baseline is
`pipeline-p003/screen-ordinal-ocr300-512-r0`, with the independently supplied
`pipeline-p003/trusted-code/b773d57.json` map. Authentication replays retained
source ownership and verifies source PDF hashes before preparation. All 16
pages, including negatives, are prepared. Historical generation remains a
separate prerequisite and is not repeated.

## Frozen inventory and pure protocol

`bench.p003_pair_relations.freeze(source)` retains every source word as an
atomic group, including physical duplicates. Geometry chooses two nearest
neighbors per direction with overlapping projections: left/right for
vertical overlap, above/below for horizontal overlap. Euclidean center
distance and original source order break ties. An interval sweep produces
the same inventory as exhaustive comparison, tested on deterministic
synthetic boxes including degenerate boxes. Admission caps are 4,096 words,
2 MiB complete source bytes, and 32,768 edges. Refusal never returns a partial
inventory. The initial 1 MiB byte cap refused a 4,086-word source snapshot;
the declared cap was raised using source size only, without reference access.

`batches(source, plan, model, image_url=None)` constructs native decision
bodies with independent same-cell, same-row, and same-column questions. Each
question offers yes/no/uncertain. Five complete edges yield at most fifteen
questions. Row and column judgments are independent; ordinary same-cell
membership implies both. Multiline cells are allowed in the instructions;
ambiguous table membership and spans require uncertainty. No question asks
the model to produce text or geometry.

The packet includes all target groups, at most 64 incident neighbor groups,
literal source strings and global boxes, page size, complete source/plan
hashes, explicit omitted context counts, and pixel availability. Missing
candidate pairs are unknown, not negatives. Evidence is explicitly partial.
Optional images use the existing native state text/image-part convention;
the caller must authenticate that pixels cover the full source-page viewport.
The helper does not render or authenticate pixel provenance itself. Complete
encoded requests exceeding 256 KiB are refused. Model identity is a transport
field and does not appear in decision evidence.

`collect(source, plan, bodies, results)` reconstructs exact bodies and checks
all question identities, typed choices, finite complete probability
distributions, and maximum-probability choice consistency. It preserves the
reported distributions without treating them as calibrated correctness.
Missing/failed complete batches fail collection; direct `decode` can accept
an explicitly incomplete answer map for diagnostic abstention, recording the
number of missing edges.

## Conservative decoder and geometry control

`decode(source, plan, answers)` processes positive edges in frozen source
order. A merge requires positive support for **every** cross-cluster pair;
an omitted, uncertain, or negative cross pair blocks it. A same-cell merge
also fails on an explicit negative row or column judgment. Row/column
partitions start from accepted cell groups, preserving the ordinary-cell
membership hierarchy. Components cannot exceed 32 atomic groups. Every
blocked merge is retained in the receipt. This is greedy complete-link
partitioning, not a global optimum, and is deliberately stricter than
single-positive-edge connected components.

Literal cell-group text is reconstructed in original source order. All
remaining singleton source IDs are unresolved. Conservation is checked:
each physical source ID occurs exactly once in a retained cell group or the
unresolved list. The output scope is **relation partitions only**. Table
membership, blank cells, rectangular spans, and a complete row/column grid
are not claimed. Long cells can be missed because the sparse graph lacks a
complete clique. Directed span membership is not implemented.

`geometry_control(plan)` is an untuned heuristic: row/column overlap of at
least 0.8 gives positive axis support; horizontal word gaps no larger than
half the greater word height give same-cell support on a shared physical
line. Other relations remain uncertain. This control can group prose; it is
not a table detector. No accuracy or rescue-quality score is reported.

## Actual preparation counts

Across 10,778 complete source words, the frozen graph contains 37,510 edges.
Requesting every independent axis judgment would require 112,530 questions
and **7,508 native batches**. Per-page batch counts range from 5 to 2,868;
maximum text-only body size is 17,632 bytes. Reported provider input tokens
are unavailable because no requests were made; bytes are not token counts.
Models with known small effective contexts would require an additional
declared packet treatment before an actual experiment.

The two largest source pages contain 6,786 words and 23,687 edges, or 63.1%
of edges. These pages were selected by source counts alone. The geometric
control returns 3,164 cell groups and 4,447 unresolved words, while refusing
21,124 proposed axis/cell merges. Those are structural observations, not
correctness measurements. Complete per-page inventories, receipts and
counts are retained in ignored `pipeline-p003/pair-relations-v1/`.

This full atomic graph would increase decision overhead. It should not be
submitted as a paid full-page sweep. The next source-only preparation should
freeze an alternative mechanical-segment grouping or a bounded uncertainty
subgraph, preserving atomic fallback and explicit omitted-edge coverage.
Useful questions include adjacent segment same-cell/wrap relations and
competing separator assignments; an automatic merge of all words on one
physical line would bake in an unverified cell boundary. Only after defining
a complete table-state adapter and freezing candidate states should DEV
references be read for a separately labeled opportunity ceiling. The zero
gain of the previous fixed-topology pools does not bound this language.

## Validation and reproduction

Seven CPU tests cover physical duplicates, partial packet disclosure,
contradictory triangles, complete triangles, missing responses, cross-axis
conflicts, stale source rejection, typed distribution/body replay, and exact
sweep/exhaustive edge equivalence. Ruff and strict mypy pass for the new
modules. The prepare-only CLI has no client or inference execution path:

```sh
python -m bench.p003_pair_prepare \
  --baseline /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/screen-ordinal-ocr300-512-r0 \
  --trusted-code /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/b773d57.json \
  --output bench/results/pdf-master-artifacts/pipeline-p003/pair-relations-v1
```

Preparation archives the two new helpers plus their pure parsing,
source-validation and canonical-hash dependencies before creating candidates.
The independently trusted baseline map remains separate from these recorded
hashes; recording a digest is not independent approval. Resource measurements
use `perf_counter`, `process_time`, and Linux `getrusage` lifetime peak RSS for
one CPU process, without sampling. Peak RSS includes baseline authentication;
other root experiment workers were active, so wall time is contended. Final
timing and report digest are supplied in the commit receipt.
