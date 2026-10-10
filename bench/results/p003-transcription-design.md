# P003 strict transcription structure investigation

Keep strict atomic admission. The inspected failures require fresh generation changes rather than permissive parsing. P003's Haiku pinned crop screen has one bound of 1010, not floating-point roundoff. Historical covered-slot conflicts contain distinct nonempty strings, and short rows place labels into slots claimed covered by a merge; blanking or padding can conceal ownership errors.

Investigation date: 2026-10-10. Only the exact 16 DEV IDs from the retained standalone natural16 report were used, including negatives. Eight authorized run directories were inspected: P003 `screen-crops-haiku-1024-pinned-r0`; P002 `natural16-vision-crops-haiku-1024`, `natural16-hybrid-haiku-1024`, `full276-hybrid-haiku-1024`, `full276-hybrid-haiku-1024-logical`, `natural16-vision-crops-sonnet-1024`, `natural16-hybrid-sonnet-1024`, and `full276-hybrid-sonnet-1024`. Full276 runs were restricted to those exact 16 paths and their `vision/` child responses, never the remaining pages. No reference, annotation, heldout, family rule, source text, or prior response enters the proposed prompt variants or repairs. Existing retained responses are used only for diagnostics.

## Empirical malformed-output inventory

Every run has nineteen complete retained crop responses, all with `finish_reason=stop`. Counts below are the unchanged strict adapter's first refusal mechanism per response; structurally valid responses can still contain semantic errors. No semantic error rate is inferred without reference or independent visual review.

| Run (natural16 subset) | Strict-valid responses /19 | Atomic operational pages /16 | Response failure mechanisms | Composition failure |
| --- | ---: | ---: | --- | --- |
| P003 Haiku pinned r0 | 18 | 15 | 1 normalized bounds | 0 |
| P002 Haiku standalone | 17 | 14 | 1 bounds; 1 nonempty covered slots | 0 |
| P002 Haiku pilot hybrid | 17 | 14 | 1 bounds; 1 span exceeds matrix | 0 |
| P002 Haiku full hybrid | 18 | 15 | 1 ragged matrix | 0 |
| P002 Haiku full logical hybrid | 17 | 14 | 1 bounds; 1 nonempty covered slots | 0 |
| P002 Sonnet standalone | 19 | 16 | 0 | 0 |
| P002 Sonnet pilot hybrid | 19 | 15 | 0 | 1 cross-crop table overlap |
| P002 Sonnet full hybrid | 19 | 15 | 0 | 1 cross-crop table overlap |

Across 152 responses, 144 pass strict response admission and eight fail: four normalized-coordinate excursions, two nonempty covered-slot conflicts, one invalid merged span, and one nonrectangular matrix. Two further page failures occur during composition despite strict-valid individual responses. This yields 118 operational page observations out of 128, not 118 independent pages. Historical source-only request identity audits already establish matched inputs for the P002 repeat sets; the P003 screen is a separate frozen treatment and is not assumed request-identical to P002.

Bound excursions are right edges 1008 or 1010. They exceed 1000 by 8 or 10 normalized units, many orders larger than one machine step. The invalid span declares width three in a two-column matrix. The ragged response contains ten rows with widths `[3,2,2,2,2,3,3,3,3,3]`; its five-row merges claim first-column continuation slots that already contain distinct literal labels. The two covered-slot refusals likewise collide with distinct nonempty strings, rather than harmless duplicate declarations. Matrix padding, deleting text, shrinking spans, rescaling units, or choosing a winner among overlapping tables therefore lacks a uniquely justified interpretation.

Atomic page failure can discard valid earlier crop responses: the P003 screen has 602 grid slots in strict-valid crop responses but only 592 on its complete page outputs. Haiku pilot hybrid has 568 strict-valid-response slots but 386 complete-page slots. Sonnet pilot/full hybrids have 1,316/1,313 strict-valid-response slots but 372 complete-page slots in each due to overlap failure. These are observed generated grid slots, including merge continuations, **not correct cells or quality denominators**. They show the operational consequence of atomic rejection.

The original natural16 benchmark's published 16-page, 53-table and 2,333-owned-cell denominators remain unchanged for any future scored replay; a failed page contributes zero predictions. No failed response, page, omitted crop, or rejected topology may leave the denominator. A representation change can also create extra predictions, which must retain false-positive penalties. This diagnostic neither rescored references nor validated rescue quality.

## Pure helper and strict standards

`bench/p003_transcription_design.py` exports `prompt_variant(representation)`, `parse_atomic(result, viewport)`, and `repair(result, viewport)`. It performs no transport, image extraction, credential access, model selection, or shared runtime mutation. Prompt variants return provider-independent `instructions` and a strict `schema`; root owns wrapping them in a fresh request and recording the treatment.

All variants require literal image-only transcription, region-relative normalized coordinates, actual tables only, all header/body rows, physical line breaks within cells, no calculations or inferred corrections, and empty strings for empty/unreadable cells. Source text stays data. Output remains model-transcribed with `source_conserved=False`; an empty unreadable cell is allowed by the protocol, not proof that no text exists. Charts, prose, captions, footnotes and decorations are excluded. All strict global/table content, table-count, slot-count, UTF-8 text, normal completion, refusal, exact-key, geometry and duplicate-JSON-key admissions remain applicable.

| Treatment | Contract | Intended failure mechanism |
| --- | --- | --- |
| `matrix_strict` | Existing bbox/matrix/mergedspans representation; targeted explicit region units, equal row lengths and empty covered slots | Baseline-compatible prompt intervention for units/placeholder discipline |
| `atomic_cells` | bbox, row_count, col_count, cells; each cell has row,column,row_span,column_span,text | Removes obligation to emit merged continuation placeholders; explicit anchors avoid positional shortening |
| `topology` | bbox, row_count, col_count, mergedspans; no cell text | First-stage plan for a separately implemented coarse-to-fine experiment |

The atomic-cell parser requires every logical slot be covered exactly once. Ordinary blank physical cells need explicit records. A merge is one record at its top-left anchor, with no continuation records. It rejects gaps, duplicate ownership, partial overlap, out-of-range spans, invalid dimensions/types, nonliteral text, excessive inventory and extra keys. It accepts arbitrary anchor arrival order because ownership is coordinate keyed. After complete partition admission, it mechanically expands covered slots to empty strings and calls the unchanged strict adapter, preserving existing canonical tables, merged anchors, display-coordinate mapping and Markdown rendering. This conversion creates only structurally declared continuation placeholders; it never fills missing cells. It does not resolve cross-table or cross-crop overlap: existing composition admission still applies.

`repair` is a separately labeled offline diagnostic. It records exact original/replacement edits and original content SHA-256, never changes a matrix string or its index, and revalidates the complete rewritten response through the existing strict adapter. Only these narrowly specified operations are admitted:

- Normalize a floating endpoint exactly one representable step below zero or above 1000 to that endpoint. This is an explicit protocol tolerance, not proof of correct image geometry; no threshold was selected from data.
- Remove an exact duplicate merged-span declaration, retaining its first identical declaration.
- Remove a `[row,column,1,1]` identity span only when its anchor names an existing matrix slot.

Substantive bound excursions, ragged rows, nonempty covered strings, conflicting overlaps, invalid span types/bounds, missing text, abnormal finishes, malformed JSON and refusals remain errors. Partial edits never become a successful result if final strict validation fails. The diagnostic returns provenance `counterfactual_postprocessing=True`, `new_provider_request=False`, `reference_guided=False`, and `quality_validated=False`.

Across all 152 complete retained responses, this helper leaves all 144 strict-valid responses canonically unchanged and refuses all eight invalid responses. **Zero responses or pages are rescued; every quality denominator stays unchanged.** No retained failure exhibits a one-ULP endpoint, exact duplicate span, or identity span. This makes the conservative repair helper useful as a protocol test seam, not a claimed improvement.

## Feasible fresh experiments

First run `matrix_strict` and `atomic_cells` against the same nineteen detector crops, same image bytes, pinned serving route, model, completion limit and page/crop order. Freeze prompts and parsers before calls; include all sixteen pages and negatives, not just previous failures. Root should use independent fresh repeats, retain exact request/response hashes and normal-stop/malformed counts, and separately report response admission, page composition, complete outputs, strict cells, complete tables, false positives, cost and wall/CPU/RSS. Atomic-cell output is more verbose for ordinary grids, so preserve token/latency measurements and charged failures. An order-of-magnitude byte or token reduction is not assumed.

The topology-first variant is a design seam, **not an implemented incremental processor or topology parser**. A bounded follow-up needs these frozen standards before paid calls: validate the whole topology using empty literal matrices through existing strict admission; freeze exact normalized bounds, dimensions, spans and a plan hash; refuse ambiguity instead of amending topology from text stages. Enumerate all physical anchors from that fixed plan. Transcribe fixed eight-row anchor batches, including headers in their own ordinary first batch, with the complete region image and explicit requested anchor coordinates. Each response must return exactly the requested `(row,column,text)` identities once, with no omitted anchor, duplicate, extra anchor, geometry change or new span. Anchors crossing a row boundary belong only to their anchor row; continuation slots are not requests. Retain per-batch attempts and failed/missing batches; assemble only after every frozen anchor is supplied and strict whole-table/page validation passes.

For a first bounded sweep, cap this plan at sixteen batches (128 logical rows) per region and preserve an explicit failed/unsupported outcome above the cap; do not silently fall back to a different treatment or omit the region from evaluation. This adds calls and can freeze wrong topology, so compare total cost and end-to-end quality, not just local completion reliability. It can separate topology mistakes from literal transcription mistakes when intermediate stages are retained. Crop tiling, automatic retries and result-guided plan edits should remain separate experiments; each changes evidence or selection and needs its own frozen protocol.

An operation-log experiment should likewise declare dimensions and require exactly one cell-ownership operation per physical anchor. Allowing overwrite/delete/move operations makes operation order a semantic repair policy; a bounded append-only coordinate-keyed log is equivalent to the implemented atomic-cell partition and simpler to audit.

## Provenance and validation

Complete diagnostic records with SHA-256 of every raw response, first strict refusal, malformed geometry/shape summaries, repair outcome and resource measurements remain ignored at `pipeline-p003/transcription-design/natural16-strict-malformation-inventory.json`, SHA-256 `077d93f172250f4a29228644b0fcc463ce3665cce8be6cd186b6890d8b375417`. The artifact was copied to the root worktree. Local replay used one serial CPU-only Python process: 0.6792 wall seconds, 0.6766 process CPU seconds, 37,084 KiB kernel peak RSS via `resource.RUSAGE_SELF`. Timed work excludes imports; RSS includes them. No periodic RSS/utilization sampler or subprocess was used; sampled utilization is unmeasured. No network, GPU or inference spending occurred.

29 synthetic tests pass for atomic/matrix canonical equivalence, complete partition admission, literal duplicate/blank retention, strict aggregate admission, prompt schemas, unchanged inputs, exact identity repairs, one-ULP tolerance, substantive repair refusal, abnormal finishes and duplicate JSON keys. Ruff and strict mypy pass for both new files. Shared runtime and existing parsing rules remain unchanged.
