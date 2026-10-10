# P003 whole-crop candidate choice

`bench/p003_candidate_choice.py` tests whether a cheap typed decision model can
rank independent valid table transcriptions against the same source image. P002's
identical-input Haiku responses varied substantially; choosing among repeats is a
different mechanism from asking the same generator for another unrestricted
matrix. This implementation performs no inference. Selector quality and provider
cost remain unmeasured.

Root integration uses only canonical transcription states already produced by the
strict `pipeline_vision_transcription.parse` path:

```python
from bench.p003_candidate_choice import freeze_pool, pool_record, request, parse, select

pool = freeze_pool(global_crop_viewport, valid_complete_candidates, seed=20261010)
retained_pool_manifest = pool_record(pool)
# A duplicate-only pool needs no selector: request() labels it not applicable.
body = request(pool, selector_model, original_inline_crop)
# Root makes and retains its explicitly authorized typed decision request.
answer = parse(pool, retained_provider_result)
selected_bytes, audit = select(pool, answer)
```

Inputs are two to four strictly valid **complete candidate inventories for one
image**, including a valid empty inventory when no table was generated. Each
candidate can contain multiple non-overlapping tables inside the original crop
viewport. The helper replays the existing strict transcription validator, checks
whole-viewport geometry and rejects malformed topology, wrong provenance,
nonliteral cells, overlaps, unknown fields or out-of-crop tables. It neither
repairs invalid JSON nor silently drops individual invalid tables.

Canonical JSON preserves every literal string, array order, table, row, column,
blank and merged span. It changes only deterministic object-key encoding. Exact
canonical duplicates are collapsed, retaining local original input-index lists.
An explicit seeded permutation assigns opaque A/B/C/D names. Neither generation
model names, request order, original input indexes, dataset labels, gold, quality
scores nor prior performance enters comparison evidence. The local pool manifest
retains immutable canonical bytes, hashes, permutation seed and original-index
mapping for audit. Candidate identity is checked again during replay.

The native `model/state/questions` request contains one typed `q0` choice among
the frozen aliases and `unresolved`. Its shared state contains compact complete
table matrices, table display boxes and merged spans, followed by the original
high-detail inline image. The image's global display viewport is explicit. No
fabricated per-cell pixel bounds are supplied. Criteria ask the selector to compare
table count and placement, row/column alignment, literal text, blank cells and
merged spans against the image, while considering omitted/extra content. A
clean-looking partial candidate can still be inadequate. `unresolved` means no
supplied complete alternative faithfully represents the crop or the image cannot
resolve their differences. Source text and pixels remain untrusted data.

The parser requires exactly `answers.q0`, typed `choice`, exact alias/unresolved
probabilities, finite values in [0,1], and a declared maximum-probability choice.
Independently two-decimal rounded options admit total-mass error up to option
count × 0.005 + 1e-9: three options have the existing 0.015 tolerance; five options
have 0.025. Normalized probabilities, original raw probabilities, rounding delta
and raw confidence remain separate. The scores/confidence are uncalibrated. There
is **no extra confidence or margin gate**: an admitted raw argmax chooses its
candidate, even with low confidence; abstention is an explicit provider choice.

Selection returns the exact frozen canonical JSON **bytes** of one candidate and
an audit identifying its hash and original input indexes. It cannot blend strings,
splice tables, reorder spans, change cell values, recover missing text or invent
structure. An unresolved choice returns `None`; root must retain that unresolved
outcome rather than label it as a successful candidate extraction. All selected
text remains `model-transcribed` and `source_conserved=False`.

Initially, partial-table comparisons are intentionally excluded. Independent
choices for cropped subsets can conflict on table ownership, missing rows,
repeated headings and boundaries. This helper ranks complete same-image
inventories atomically; any future per-table selector needs its own complete
coverage/non-overlap admission and provenance contract. Formal validity is not a
claim that a candidate contains all visible content.

Input pool bytes are bounded to 8 MiB, complete comparison JSON to 128 KiB, and
inline crop URL to the existing 16 MiB boundary. Exceeding evidence limits refuses
the complete comparison rather than truncating candidates. Exact-duplicate-only
pools remain locally usable but do not warrant a paid comparison request.

Generation requests/errors/costs/latencies are separate external pool provenance.
Root should retain every attempted generator result, including invalid outputs
excluded before freezing, and report each candidate's validation disposition.
The selector's request/response, latency and charge are a separate new stage.
Offline ranking of a retained frozen pool is not a new end-to-end pipeline run
and must not produce PDF pages/minute from selector latency alone. Report the
pool-generation expense and total complete-pipeline cost when comparing to a
single-generator route; do not call replayed candidates free.

For measured follow-up, use the same frozen image and candidate pool for paired
selectors, preserve all pages including negatives and failures, include the
unselected candidate controls, and randomize alias order by explicit seeds. Repeat
identical-pool selection to measure selector variation separately from generator
variation. No reference-dependent pool filtering or alias ordering is allowed.

Offline validation: **14 tests passed in 0.08 seconds**, with Ruff passing. Tests
cover strict candidate geometry/topology/provenance, seeded opaque order,
deduplication, literal Unicode/whitespace and merged-slot preservation, exact
selected byte identity, explicit abstention, low-confidence raw argmax, complete
probability shape/rounding, modified pool/answer rejection and atomic size refusal.
No network activity, credentials, gold or protected data was accessed.
