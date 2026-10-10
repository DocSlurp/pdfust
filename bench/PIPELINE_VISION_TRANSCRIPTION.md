# P002 image-only table transcription control

`pipeline_vision_transcription` provides a separate baseline for the ceiling
imposed by missing OCR text. Source-ID selection and ownership models can only
rearrange retained words. This control transcribes the raster directly, so it
can produce cell text that OCR never retained. It does not repair source-ID
assembly, claim source conservation, or change the scorer.

The module builds and validates data only. It contains no client, credential
lookup, filesystem reads, network request, inference, catalog lookup, or ledger
operation. The root experiment runner owns image rendering, frozen requests,
paid reservations, transport, charge accounting, complete response/error
retention, and offline scoring.

## API and evidence boundary

- `request(model, url, viewport, max_tokens=16384)` builds the chat request for
  the same declared Anthropic 5.5 control IDs as `pipeline_frontier`. `url` is a
  bounded PNG/JPEG/WebP base64 data URL with no filename parameters; `viewport`
  is `[x0, y0, x1, y1]` in display coordinates. The viewport is validated locally
  and does not enter model messages. The user content contains exactly one
  image; instructions are static. No OCR, source IDs, filename, family,
  candidate menu, private target, annotation, or score enters the request.
- `parse(result, viewport)` admits one normally completed chat response and
  returns `{"tables": [...], "text_provenance": "model-transcribed",
  "source_conserved": false}`. Provider envelope metadata is left to the runner;
  unknown answer keys are rejected. Failures raise an exception, without a
  partial table prefix or silent empty-table fallback.
- `markdown(parsed)` revalidates the canonical bounded result and emits HTML
  table blocks suitable for Markdown, escaping literal HTML and preserving
  merged spans. Cells receive `<td>` rather than inferred header roles.

The required answer is compact JSON at `answers.q0.tables`. Each table has
exactly `bbox`, `matrix`, and `mergedspans`: image-normalized bounds 0..1000,
a rectangular matrix of literal strings, and zero-based
`[row, column, rowspan, colspan]` entries for actual merges only. The top-left
anchor owns merged text; covered slots must be empty strings. Separate tables
remain separate, and an explicit empty list represents no visible tables.
Case, math, punctuation, and whitespace remain literal. Instructions forbid
calculating, completing, or correcting values. An unreadable cell is represented
as an empty string, which does not distinguish unreadability from true blank
content; retained images and responses are needed to diagnose that limitation.

Canonical tables expose `row_count`, `col_count`, rectangular `values`, flat
`cells` with empty `source_ids`, merged `spans`, and global display `bbox`.
Covered slots become `None`, as required by `generalization_scoring._cells`;
unmerged blank cells remain `""`. Every table and cell labels text as
`model-transcribed`, and both table and outer result set `source_conserved` to
false. These synthetic checks verified compatibility with the current scorer;
no natural-document accuracy claim is made by this adapter.

## Admissions and comparison

The parser rejects truncation, refusal, missing completions, malformed JSON,
duplicate JSON keys at any level, NaN/Infinity, numeric overflow, unknown keys,
nonrectangular/nonstring cells, invalid or overlapping spans, text in covered
slots, and out-of-range geometry. Admissions are 64 tables, 4096 slots per
table, 16384 aggregate slots, 1 MiB aggregate UTF-8 cell text, and 2 MiB response
content. Input image data URLs stop at 16 MiB. Request token limits are explicit,
1..65536, default 16384; optional temperature/reasoning controls are omitted.
No over-budget output is truncated or scored as a successful empty result.

Compare this arm with source-ID assembly on matched page renders and retain
both wins and losses. Do not convert text provenance into source conservation,
filter gold tables to OCR-visible words, or silently exclude failed dense-page
responses. Long responses can still exhaust the model token budget; preserve
those failures as observed limitations. Geometry only maps the model's table
bounds; cell boxes are not inferred or presented as measured evidence.
