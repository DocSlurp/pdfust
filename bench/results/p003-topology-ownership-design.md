# P003 topology-first source ownership

The P002 failure evidence separates structure and source vocabulary. Geometry and
row context can place existing strings, but missing OCR text remains absent.
Whole-crop transcription can supply visible strings beyond that inventory, with
model-transcribed provenance. This experiment targets the placement component
without silently turning source-owned values into transcriptions.

Three distinct modes address different ceilings:

1. **Frozen topology, source-owned choices (implemented pure helper).** An
   image-only topology hypothesis fixes all table bounds, rows, columns and
   merges. Native choices assign each original word to a table/logical row, then
   a physical anchor. All admitted logical rows are choices, removing the
   geometry-candidate shortlist as a placement ceiling. Outside and unresolved
   choices preserve original inventory. This cannot recover absent source text.
2. **Frozen transcription candidate selection (existing candidate picker).**
   Screenshot-guided ranking selects one exact complete candidate without edits.
   It can recover a string absent from OCR only when a candidate already contains
   it. An edit protocol restricted to source IDs shares the source vocabulary
   ceiling; rewriting malformed or missing strings would change the experiment.
3. **Frozen topology, literal image transcription.** Independently transcribing
   requested physical anchors can recover missing OCR strings. It requires
   separate model-transcribed provenance, costs and strict complete anchor
   coverage. Existing topology scaffolding describes this mode; this module does
   not implement or claim its text recovery.

`bench/p003_topology_ownership.py` is pure and has no model client, PDF loading,
credential, evaluator, network, or GPU access. `topology_request` wraps the
existing strict topology scaffold. `parse_topology` validates no-text predictions
through the unchanged transcription adapter using empty structural matrices,
then rejects overlapping tables. These empty values are validation scaffolding,
not inferred visible blanks. Semantically wrong topology remains possible.

`freeze(source,result,viewport,url)` retains only original source IDs, complete
literal strings and display boxes, admitted no-text topology, crop viewport and
actual decoded image SHA-256 in an immutable snapshot. Annotations, source model
names, quality labels and prior generated strings do not enter evidence. The crop
uses original page display coordinates, while table bounds in the topology
response are normalized relative to this exact crop; the strict adapter maps them
back into display space. Source strings keep their original global identities and
order throughout all batches.

`batches(plan,model,url)` builds row choices. `collect(plan,bodies,results)` requires
complete row answers before `batches(...,rows=receipt)` constructs physical anchor
choices. Merged anchors spanning the selected row remain eligible even when their
anchor row is earlier. Covered continuation slots are never ownership choices.
`assemble(plan,row_bodies,row_results,cell_bodies,cell_results)` replays both stages
and commits the entire source state once, or raises without modifying any input.
The runner must retain its original whole-page output on any crop/stage failure.

Every original word has one table anchor or remains unresolved in the source
state. Outside and explicit abstention inventories are separately retained; the
combined unresolved list preserves original source order. Cell strings join exact
owned source words in original order with the existing assembler's inferred
spaces. Complete source tiling expands ordinary physical anchors into unit spans,
a mechanical representation conversion required by the unchanged source
validator. Model topology does not prove semantic rows, correct text, pixel
visibility, genuinely empty cells, or calibrated probabilities.

Admission is explicit: at most 16 tables, 128 logical rows across all tables, 32
columns per table, 4096 aggregate slots, 256 words, 16,000 UTF-8 bytes for complete
source JSON, and 128,000 bytes for local text plus question menus. Each stage has
at most sixteen batches and each batch at most sixteen typed questions. Full
source/menus are refused above caps; no subset is silently emitted. Source caps
should be checked before any new paid topology generation. Worst case is 32
ownership calls plus one fresh topology call; a retained fixed topology has
historical generation costs and at most 32 new ownership calls. Smaller batches
can exceed the sixteen-batch cap and are refused. Root must compare total calls,
image bytes, cost and incremental latency rather than assuming a token advantage.

Typed responses must cover exact batch IDs and exact option probabilities, with
finite values in [0,1], maximum-probability choice and the existing 0.015 rounding
budget. Raw probabilities, mass delta and confidence remain uncalibrated
provenance. There are no extra confidence gates. Explicit unresolved is the
abstention mechanism. Frozen body/evidence/image/criteria mutation, duplicate or
missing batches, wrong receipt snapshot, malformed topology and partial responses
fail the whole operation.

Sixteen synthetic CPU-only tests exercise merged continuation ownership, complete
literal inventory, annotation exclusion, exact source order, raw confidence and
rounding, malformed late batches, duplicate/missing identities, crop mutation,
invalid bounds/spans, overlapping tables, empty inventory and bounded refusal.
No gold or source artifact was used to generate protocol evidence.
