# P002 source-ID generative assembly design

This offline adapter tests whether candidate recall limits complete table
assembly. Instead of selecting an existing candidate, a chat model may declare
rows, columns, merged anchors, and ownership directly from the retained source
word inventory and optional image. It emits no cell text. This is a proposed
mechanism, not measured evidence of improvement.

`bench.pipeline_generation.request(source, model, url=None, viewport=None,
max_tokens=4096)` prepares a chat request for the existing Sonnet, Haiku, or
Opus controls. It uses the shared `DecisionClient` schema envelope:

```json
{"answers":{"q0":{"tables":[{"rows":2,"columns":2,"cells":[
  {"row":0,"column":0,"row_span":1,"column_span":2,"source_ids":["w0"]},
  {"row":1,"column":0,"row_span":1,"column_span":1,"source_ids":["w1"]}
]}]}}}
```

There are no free-text answer fields. The adapter makes no requests, initializes
no clients, reads no credentials or model catalogs, and performs no inference.
Root alone reserves, sends, meters, and retains any subsequent requests.

## Source evidence and interpretation

Input projection admits only complete source `words` containing literal `id`,
`text`, and display `bbox`, plus `page_size`. Classification, annotations,
filenames, targets, upstream table hypotheses, and all extra word/page fields
are excluded. System instructions treat source text and image content as data,
including any embedded instructions. Every retained source word is included;
there is no selected-region truncation. Viewport accepts two positive image
dimensions or four finite display bounds, records coordinate context, and does
not filter words. Images must be bounded inline PNG/JPEG/WebP data URLs, keeping
file names out of evidence. Text blocks precede images.

`parse(source, result)` (also `parse_response`) admits one chat completion with
normal `stop` or `end_turn` finish and strict JSON. It returns the same complete
state used by `pipeline_assembly`, with row-major cell ownership, rectangular
literal values, explicit spans, and `unresolved_ids`. Values are rebuilt by
joining the exact retained word texts in the declared ID order. Covered merged
slots become `None`; each omitted uncovered slot becomes an explicit empty
1×1 anchor. Every unassigned source ID remains unresolved prose automatically.
An empty table array retains the entire source inventory as prose.

OCR remains fixed upstream. An image may inform topology and relationships,
but the adapter cannot recover missing OCR tokens, correct recognition text,
transcribe arbitrary image content, or invent cell values. It conserves words,
not independently verified meaning. Models can still misclassify prose as
records or choose incorrect boundaries and ordering; these errors require
separate evaluation.

## Admission and failure behavior

The source boundary reuses complete assembly admission: at most 4,096 words
and 16,000 aggregate source text/ID characters, with finite word geometry and
positive page extent. IDs must be nonempty and at most 128 characters. Source
JSON is limited to 128,000 characters, inline image URLs to 12 million
characters, and output-token requests to 1–16,384 (default 4,096). Larger
inputs refuse rather than silently dropping context.

Responses are limited to 256,000 characters, 32 tables, and 4,096 aggregate
table slots. Dimensions and spans must be genuine integers, with no booleans,
zero/negative extents, or out-of-range anchors. All tables together may assign
each known source ID only once. Unknown IDs, duplicate ownership, corrupt or
overlapping spans, covered-slot anchors, extra fields, malformed/duplicate-key
JSON, mixed field types, refusals, and abnormal/truncated finishes reject the
entire response. The adapter exposes no partial state. Root can retain the
failure and compare its separately defined baseline without treating invalid
output as a successful generated assembly.

All accepted states pass the existing complete assembly validator, including
exact source conservation and literal-value reconstruction. Thirty focused
CPU-only tests cover schema compatibility, metadata exclusion, image/text
ordering, merged and omitted slots, prose conservation, duplicate ownership,
unknown IDs, dimension/span limits, mixed types, malformed JSON, refusal,
truncation, and request limits. No provider behavior or quality was measured.

## Provenance audit note

During initial corpus discovery, an overly broad filename listing incidentally
returned two protected-path filenames. No protected file contents or
scoring data were read, and no further access followed. Discovery was corrected
to explicit safe input paths. This procedural lapse is recorded without
repeating protected names; subsequent corpus selection reads only the two
explicitly approved public DEV/training registries.
