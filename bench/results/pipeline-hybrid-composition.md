# Experimental native/vision composition contract

The pure `bench.pipeline_hybrid_composition` helper freezes source-only composition
rules before any ROI inference outcomes. It makes no accuracy claim and performs
no inference, loading of references, PDF rendering, or default library change.

`sanitize_vectors(source)` projects page geometry, every literal source word, optional
retained line identity, and native grid geometry. It discards upstream values,
annotations and diagnostics. `native_boxes(source, native_state)` returns full
retained physical native grid bounds, including empty cells; runtime table bounds
inferred from owned text cannot shrink them. Native ownership and literal values
are verified with bounded complete-page validation, then independently reconstructed
from source grid cells. This permits runtime canonical table bbox annotations while
rejecting a state that silently changes native ownership.

`exclude_native_proposals(detection, boxes)` returns a copied filtered response and
exclusion diagnostics. Any Table proposal with positive-area native intersection
is excluded whole; touching edges and other classes are retained. The original raw
response remains unchanged for orchestration to retain separately. Each exclusion
records the complete proposal, intersecting native boxes, reason and uncertain
coverage. A large overlapping proposal could also include an unknown adjacent table;
filtering therefore retains residual source words as prose and does not synthesize
a supposedly safe partial crop.

`compose(source, native_state, transcription)` accepts the strict canonical output
of `pipeline_vision_transcription.parse` in global display coordinates. It validates
all transcription strings, spans, covered slots, provenance and boxes using the
existing strict renderer. Positive-area overlap with any native grid or another
transcribed table refuses the entire composition. Combined inventory is capped at
32 tables and 4096 aggregate slots. Source admission uses the existing 65536-word,
4 MiB complete-page limit, without applying the legacy whole-page prompt text cap.

On success, the result contains `status='ok'`, `route='hybrid_composition'`, `viewport`,
`tables`, `unresolved_ids` for prose, `superseded_ids`, `source_ledger`, `markdown`,
`source_inventory_complete=True`, `accounting_complete=True`, rules and diagnostics.
Native tables have `text_provenance='native-source'`; transcribed canonical tables
remain unchanged with `text_provenance='model-transcribed'`. Every original source
ID occurs exactly once in the ledger, owned by native, prose, or superseded, with a
table index for table-related ownership. Only words fully contained by a transcribed
bbox are superseded. Crossing and outside words remain literal prose unless already
native-owned. Crossing cases are retained in `crossing_words_retained` diagnostics.
Model strings have no original source IDs and receive no fuzzy correction.

`source_conserved=False` whenever an accepted transcribed table exists, even if no
source word is superseded. Complete source accounting is distinct from preserving
literal source text in output. With zero transcribed tables, verified native source
conservation is true and Markdown matches the existing native baseline exactly.
Tables interleave with prose using their first owned/superseded original word; a
transcribed table without such words uses a deterministic page-geometry fallback.
This ordering does not establish semantic reading order. Native and transcribed
cells and prose are escaped with the existing renderer conventions; raw model HTML
is never injected. Newlines in model cell strings retain the vision renderer's
`<br>` conversion.

A rejected transcription returns `status='abstained'`, no table prefix, no ledger,
`markdown=None`, `accounting_complete=False`, and a retained refusal diagnostic.
`diagnostic_baseline` holds the verified native baseline with `diagnostic_only=True`;
that artifact is not a successful hybrid output. Invalid source/native inventory
raises before output. `markdown(composed)` reads only a successful trusted compose
result; retained JSON must first be replayed through compose to attest provenance.

The root runner must retain original source, native child result, raw transcription
responses and strict structures, raw/filtered detector responses, exclusion records
and complete composed artifacts. The reporter can replay every pure stage; root
counts atomic abstention as a failed page. This helper does not verify hosted request
provenance by itself.

Fifteen focused CPU tests cover mixed ownership, crossing words, escaped literal
strings, merged spans, exact empty-transcription baseline, full grid bounds despite
runtime text bbox annotations, invalid/transcribed overlaps, nonfinite/out-of-page
boxes, atomic errors, source-only proposal exclusion, no metadata leakage, large
source inventory and aggregate capacity. No corpus scoring or paid request was
performed for this contract.
