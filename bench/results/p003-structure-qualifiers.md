# P003 source-only structure placement qualifiers

Date: 2026-10-10 UTC. These derivatives use the already frozen CPU Table
Transformer predictions and original source-owned detector crops. No
reference, target, score, new model inference, hosted API, GPU or credential
was used. The existing nine base placement arms are unchanged.

## Frozen policies

`p003_structure_qualifiers.qualify(source, source_ids, topology)` admits the
complete source at two MiB and at most 4,096 words per crop, validates exact
source identities and positive finite word geometry, and validates complete
rectangular anchor tiling against ordered physical edges. It retains every
physical duplicate and literal source string. A refused topology yields
explicit unresolved suggestions rather than guessed geometry.

Word receipts contain all positively intersecting anchor candidates, exact
word-area overlaps, overlap margins, crossed physical row/column edges, and
center-to-nearest-boundary distances divided by the actual word-box height.
Actual glyph heights and font sizes are unavailable; measured word height
is not promoted to either, and none of these scores is a probability.

Two independent deterministic assignment policies were fixed before scoring:

- **Adaptive:** the best anchor must contain the word center, cover at least
  half its area, and beat the runner-up by at least
  `min(0.25, 0.5 * word_height / anchor_height)`. Ties remain unresolved.
- **Row consensus:** physical bands first assign one row from mean per-word
  vertical overlap, requiring score at least 0.5 and runner-up margin at
  least 0.15. Each word then chooses among anchors spanning that row,
  requiring word-area overlap at least 0.5 and margin at least 0.15.
  An ambiguous band or cell leaves the word unresolved.

Physical bands are built in increasing vertical-center order, using source
order for ties. A word joins a band only if it is compatible with **every**
existing member: center drift at most 0.35 times their smaller word height
and vertical intersection at least 0.5 times that height. A word compatible
with multiple bands starts a separate band. This prevents a single bridge
word from chaining distinct baselines. Each group's retained IDs are ordered
by original local source order; group construction does not change strings
or deduplicate overprints.

Adjacent physical-band wrap hypotheses retain normalized vertical gap,
horizontal intersection, indentation and whether the bands independently
choose the same predicted row. Eligibility requires nonnegative gap at most
2.5 smaller word heights, horizontal overlap/minimum width at least 0.5, and
left-edge displacement at most two word heights. **No hypothesis joins rows
or cells automatically.** Across-column mixtures and accidental proximity
remain possible; these are evidence for later decisions, not logical-cell
labels. A whole-row consensus can also misassign small outlying cells, so
both policies stay separate rather than selecting a winner by page.

`place(source, candidates, policy)` emits the standard source-owned state
schema. Crop ownership must be disjoint. Overlapping accepted table boxes
are all refused, and their words return to unresolved. Source words outside
these fixed detector crops also remain unresolved. All literal source IDs
appear exactly once in cells or unresolved, validated by
`pipeline_repair.validate`; `_clean_table` derives values exclusively from
those retained source IDs. Topology shape and spanning anchors are unchanged.

## Source-only inventory

All 16 pages remain in the denominator, including two pages without detector
proposals. The fixed 20 detector crops own 2,205 of 10,778 retained page words;
the 8,573 words outside crop ownership cannot be recovered by these placement
derivatives. Thresholds 0.3/0.5/0.7 reuse the same frozen raw logits. The two
policies produce six full treatments, or 96 page artifacts.

| Threshold | Adaptive unresolved | Row-consensus unresolved | Policy disagreements | Row-edge crossing words | Column-edge crossing words | Physical bands | Wrap hypotheses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.3 | 9,987 | 9,982 | 21 | 241 | 149 | 169 | 61 |
| 0.5 | 10,031 | 10,028 | 123 | 1,181 | 491 | 283 | 68 |
| 0.7 | 10,030 | 10,027 | 113 | 1,167 | 480 | 283 | 68 |

Counts in the evidence columns are per threshold, independent of assignment
policy. Refused-topology words contribute to crop ownership counts and
unresolved output, but not geometric crossing/band counts. All six treatments
retain 17 nonoverlapping table candidates: the 0.3 geometry pass already
refused three spans; the other thresholds refuse one span and two overlapping
table candidates. Differences in unresolved counts do not establish quality.
No geometric threshold or policy was chosen using a reference result.

## Bounded future decision seam

`packet(source, qualifiers, target_ids, pixels_available=..., max_bytes=24000)`
returns a UTF-8 string and hash/count metadata. It includes a separate targeted
instruction, complete literal target strings/IDs/boxes, all their supplied
anchor choices and ambiguity receipts, full-source and qualifier hashes, and
pixel availability. At most 16 targets are admitted. Same-band context is
included in preserved source order while bounded; every omitted crop/page
word count is explicit. A complete target payload exceeding the declared
byte cap raises an error; target text is never silently truncated.

The model's later task is only to choose a supplied anchor slot or unresolved;
it may not rewrite text. A caller attaching crop pixels must retain the exact
source crop viewport and image hash separately so global display coordinates
can be interpreted consistently. Model identity, gold, scores and historical
responses do not enter these packets. No decision transport or automatic
application is enabled here.

Eight text-only diagnostic packets are archived, selecting the first at most
16 adaptive-versus-consensus disagreements per crop/threshold by source order.
Their largest complete packet is 22,031 bytes, below the 24,000-byte cap. They
are source-only seam examples rather than an inference experiment or chosen
scoring treatment. The full crop inventory remains local when context words
are omitted.

## Freeze and checks

Main-root ignored artifacts: `pipeline-p003/structure-qualifiers-v2/`.
The runner independently authenticates the original ordinal baseline using
the external trusted map, validates every source/original-result hash, and
replays all threshold topology views from raw model queries. Code hashes and
all treatment policies are written before derivative outputs. Complete source,
qualifier evidence, predicted states, conflict receipts, eight example
packets, helper copies and archival hashes are retained.

Report SHA-256:
`0a73bc41a7baae17dedc479eb9cf37e27c03cfe8f2ec82027e44e809d206e4b1`.
Frozen configuration SHA-256:
`a18f4fdda6a146a1a95ea7c6941e69f049fb803c944d1d11911f3ebf828a0962`.
Artifact manifest SHA-256:
`9ffc6f8a6447b21c7f18580f2ef53af171c2968087a7d159999203fe6e5f2f0c`.
Earlier v1 remains archived: v2 renamed two evidence fields to explicitly
say center-to-boundary distance. All 96 predicted source-owned states were
checked identical between versions; no reference had been read.

The v2 derivative pass took 3.149 seconds wall and 3.130 seconds self CPU in
one contended CPU process. Linux lifetime peak self RSS was 539,156 KiB,
including preceding baseline authentication/imports; wall/CPU timing excludes
those preceding phases. RSS was not sampled. Original OCR/detection and CPU
structure inference are excluded. No remote cost or throughput is inferred.

Seven CPU tests check line-supported boundary ties, physical duplicates,
complete-link bridge refusal, nonapplied wrap hypotheses, overlapping-table
refusal, exact source conservation, literal evidence/explicit omissions/byte
refusal, and malformed positive-word/anchor geometry. Ruff and strict module
mypy pass. Independent scoring must authenticate the frozen code and replay
`place` for every source/threshold/policy, preserving unresolved/conflicting
cases and the complete 16-page denominator.

```sh
python -m bench.p003_structure_qualifiers \
  --geometry <pipeline-p003>/structure-geometry-v1 \
  --output <fresh-qualifier-directory>
```
