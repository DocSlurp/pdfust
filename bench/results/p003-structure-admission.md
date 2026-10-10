# P003 source-only admission over explicit structure predictions

Date: 2026-10-10 UTC. This preparation makes no hosted request and uses no
credential, GPU, new model inference, reference, previous score or protected
input. It supplies a frozen native-choice protocol; root owns any subsequent
paid runner and independent evaluation.

## Candidate inventory and eligibility

All valid explicit TATR geometry candidates are frozen across original
detector, full-page, residual and residual-density acquisition arms, at all
three original thresholds. The source is the externally authenticated ordinal
DEV16 baseline. Eligibility means finite, complete accepted geometry only;
it does not claim semantic table correctness or calibrated detector scores.

| Arm | Candidates at 0.3 / 0.5 / 0.7 |
| --- | ---: |
| Original detector | 17 / 19 / 19 |
| Full page | 9 / 13 / 14 |
| Residual | 28 / 28 / 24 |
| Residual density | 15 / 16 / 14 |

The total is 216 candidates. Thirty-nine malformed/conflicting raw topology
views and 14 acquisition/page no-crop cases remain explicit exclusion receipts;
every arm retains its intended 16-page list. No threshold or arm is selected
using these counts. Candidate geometry overlaps remain in the local pool for
later conflict handling; candidates are never silently merged.

Source assignments use the already predeclared `max_overlap` policy: a word
needs uniquely maximal positive anchor overlap, exceeding the runner-up by
more than 1e-9. Ties remain unresolved. Every candidate's table is validated
individually against complete original source ownership. All strings and
source IDs remain local, including words not assigned to any candidate cell.
This assignment is a proposal, not a claim of true cells.

## Pure protocol and bounded evidence

`p003_structure_admission` exposes these pure seams:

- `source_table(source, topology, source_ids)` creates the exact source-owned
  candidate with fixed max-overlap placement;
- `packet(source, table, source_ids, pixels_available=...)` returns complete
  literal evidence plus hash/count metadata, or an explicit question refusal;
- `request(model, text, url)` builds the native bounded-choice HTTP body;
- `apply(source, candidates, decisions)` retains exact admitted candidates or
  returns their source IDs to unresolved.

The prompt asks only **retain / reject / unresolved**. It states that aligned
prose, lists, headings, boxes and formulas are not automatically tables, and
that proposed row/column ownership is not verified cell semantics. It gives
no gold example, model identity, score or historical response. Source strings
are data; the model cannot generate text, edit cells, repair shape, replace a
candidate or choose a fallback.

Packets declare explicit bbox, rows, columns, rectangular spans and nonempty
source-cell ID assignments. Word arrays contain **every owned source ID,
complete literal string and exact unrounded word bbox**. Full-source and
candidate hashes, page/crop word counts, omitted other-page counts and pixel
availability are explicit. Ownership omissions within the admitted crop are
zero; unrelated page context is deliberately omitted and counted. The entire
candidate/source snapshot remains local.

A complete packet larger than **128 KiB** becomes `no_question_refusal`;
words are never silently truncated. Five full-page candidates exceed this
limit in each treatment. The other 211 candidates prepare successfully for
each treatment. The largest admitted packet is 104,486 UTF-8 bytes; the
largest refused complete packet is 378,910 bytes. The byte cap is a wire
admission rule, not a promise about a provider's processed context; a later
runner must retain reported input tokens and evidence counts separately.

The three independent configured models are
`perplexity/pplx-decider-v1.1-27b`, `openai/gpt-6-luna-decisions` and
`cloudflare/clef-omni`. Their bodies are native `questions.q0.type=choice`
with the targeted instruction and exactly the three declared criteria. No
chat adapter, Gateway, client, key access or model fallback is used here.
All 1,899 prospective native bodies are archived and reconstructed exactly;
none was transmitted. Root need not execute the complete prepared cross
product to use this frozen pool.

## Matched source-pixel treatments

Treatments are independent `rgb128`, `rgb512` and `text`. Both image treatments
use the same retained source-JPEG hash/viewport and candidate bbox. A new
admission-only image helper maps that continuous viewport directly through
Pillow BICUBIC EXTENT at the declared edge, then emits **lossless RGB PNG**
(8-bit channels, PNG color type 2). This adds no second JPEG loss, while the
inherited original TATR source crop remains JPEG90. Exact crop viewport,
continuous source-pixel box, dimensions, codec, encoded bytes and SHA are
retained. The text-only treatment supplies no image.

Pixels cover only the predicted candidate bbox; owned literal words outside
it remain explicitly textual context. This does not equate a candidate crop
with a complete page image. The largest prospective compact native body is
669,597 bytes, including its encoded image; no image or word truncation is
performed to reduce body size.

## Source conservation and failure behavior

Only an explicit `retain` can admit the exact original source-owned table.
Reject, unresolved, missing/failed decision and no-question refusal yield no
table for that candidate. All its unplaced/rejected source words remain
unresolved. The apply helper validates the resulting entire source inventory
with `pipeline_repair.validate`; literal values are rebuilt from source IDs
through `_clean_table`.

If multiple retained candidates overlap in bbox or assigned source IDs, all
conflicting candidates are refused with receipts. No higher-scoring table,
other threshold, model or generation replaces them. Root may declare separate
acquisition/mixed-pool runs, but must preserve this conflict rule and complete
page denominator rather than implicitly merge candidates.

## Frozen artifact contract

Main-root ignored pool: `pipeline-p003/structure-admission-v3/`.

- `source-inventory.json` contains all 16 intended source records/snapshots,
  original/effective rotations and original baseline-output hashes, including
  pages with zero candidates. Actual snapshots are under `sources/`.
- `frozen.json` contains policies, models, treatments, targeted instruction,
  byte cap, arm paths and exact helper/dependency code hashes before outputs.
- `report.json` contains candidate inventory, every exclusion, complete source
  trust receipts and resource measurements.
- Each candidate folder contains full source, explicit topology/table/ownership,
  per-treatment question status, pixels, prepared packets and native bodies.
- Independently supplied baseline trust-map bytes are copied locally; the
  report retains their original path/hash and baseline directory.

Baseline source is `screen-ordinal-ocr300-512-r0`; independent source trust is
`trusted-code/b773d57.json`. Preparation reauthenticates this baseline for each
arm, checks source/PDF/original-result provenance, verifies corrected inference
wrappers against their frozen hashes, and replays every topology from raw
queries. New admissions are not self-attested by their own hash fields;
a runner must receive a root-approved external pool code map and source
trust map, reconstruct source/candidate/evidence and validate all bytes before
constructing any client.

Request file SHA authenticates the pretty sorted archival JSON. The distinct
`request_sha256` authenticates compact serialization of the **reconstructed
helper body** in insertion order. A runner must send that reconstructed body;
parsing sorted archival JSON is a semantic comparison, not the wire-byte
construction. All native bodies remain semantically identical to v2, where
the shared historical body helper was used; v3 removes that broad dependency
and adds the complete intended-page source inventory.

Report SHA-256:
`3a937272fad9a0b1443f72707443ddb2ac7416b675f442c6c2952b34f7c9148b`.
Frozen configuration SHA-256:
`9604c24e256075d3935d2c4e7580435af153496a2992a54463c29c66d374b04f`.
Full-source inventory SHA-256:
`8c2d897ed4e0d2dc4e7676901fa4e29ab04edae36a9bdbef70d9d13578edcc88`.
Archival manifest SHA-256:
`70efbdd403d131d07e703399d5684f360e28ccdef97ac4bc8f0b7e7588059e42`.
The archive retains 3,421 files totaling 246,122,192 bytes, with no uploaded
source or committed raw artifact.

An initial v1 preparation failed before request files because the historical
transcription crop helper rejects edge 128. Its failure receipt and partial
local artifacts remain archived. The new admission-only helper supports both
declared edges without modifying shared transcription/runtime code. There
were no hosted retries or additional model forwards. V2/v3 successful native
bodies were compared independently; no reference was read between versions.

## CPU verification

V3 preparation took 29.702 seconds wall and 29.416 seconds self CPU in one
contended CPU process, including repeated baseline authentication and all
packet/pixel/body serialization. Linux lifetime peak self RSS was 539,156
KiB. Imports, previous OCR/detection/TATR inference and the subsequent complete
body replay are outside these timing receipts; RSS was not sampled.

Seven CPU tests cover exact literals/coordinates, proposed-cell declarations,
complete oversize refusal, each configured native body/instruction, exact
retain semantics, all failed/refused routes, overlap refusal, malformed
admission/foreign ownership, and matched lossless RGB128/512 pixel provenance.
Ruff and strict module mypy pass. All 1,899 bodies and packet metadata were
rebuilt against the frozen candidate/source/pixels, with compact wire hashes
and preserved v2 semantic identity checked independently.
