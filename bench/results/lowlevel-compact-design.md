# Lossless compact source packet loop

Commit 41a242a adds bench/lowlevel_compact.py and six passing tests. Ruff and
mypy pass. No hosted calls, credentials, model response files or held-out sources
were accessed. The reported Jev HTTP400 and endpoint limit motivate a new packet
experiment; this audit does not establish the HTTP400 cause. The existing failed
request is not retried or rewritten.

compact(projected_state) replaces glyph dictionaries with a reversible table:
ordered fields, variable columns, constants shared by every row, shared font
fields/font records, a declared font-index column and row arrays. Source_order
is retained whenever present; canonical source already excludes it. No precision
changes, source normalization or character omission occurs. Original source
values and dictionary order reconstruct exactly through expand(packet).

Text operators use the same columns/rows scheme. Repeated literal operands are
interned in references.operands, and that column holds their integer reference.
Operands retain nested original bytes_hex/parser_text/source status values; they
are not font-decoded or interpreted. Shared indexes must be valid non-boolean
integers. Inconsistent source row fields/order refuse. Tests verify exact encoded
JSON round trips, multiple font identities, empty tables, source immutability,
invalid references and complete byte admission.

adaptive_requests(source_observations, pure_builder, max_bytes=32000,
max_batch=3) selects the largest consecutive prefix fitting the complete JSON
body, including model ID, questions and instructions. It then shrinks batches
without discarding source fields. A singleton that cannot fit refuses atomically;
there is no truncation. The byte cap is a conservative engineering restriction,
not a measurement of provider tokens or a proven maximum tokenizer ratio. Parent
must keep this pure builder separate from provider transmission.

The final encoding retained all glyphs and operators on all 108 PDFs. Initial
operator tables without operand interning left six history singleton bodies
above 32,000 bytes; that packet design was rejected for the bounded Jev arm.
Operand interning reduced the largest final history operator singleton to
27,209 bytes and admitted all sources.

## Source-preserving measurements

Basic: 24 logical cases / 72 PDFs / 109,204 source bytes. History: 12 logical
cases / 36 PDFs / 140,484 source bytes. Each source was observed before scorer
metadata; all canonical/vector/operator compact states reconstructed the exact
serialized projected source JSON. Cases remain correlated DEV controls.

| Cohort/arm | Raw projected bytes | Compact projected bytes | Largest compact singleton body | Adaptive batches | Largest complete batch body |
|---|---:|---:|---:|---:|---:|
| Basic canonical | 301,965 | 89,376 | 2,518 | 24 triples | 7,414 |
| Basic vectors | 373,581 | 134,127 | 3,715 | 24 triples | 11,005 |
| Basic operators | 671,911 | 311,017 | 8,633 | 24 triples | 20,611 |
| History canonical | 729,294 | 152,709 | 6,446 | 12 triples | 19,198 |
| History vectors | 861,288 | 213,918 | 8,717 | 12 triples | 26,011 |
| History operators | 1,595,853 | 572,280 | 27,209 | 14 singletons + 11 pairs | 30,418 |

Body measurements use the existing both prompt factor: resolved task-specific
criteria plus native observations object. Source order in this diagnostic is
the authoring cohort order, not root's frozen ID ordering; adaptive batch counts
can change with ordering. Complete body limits hold regardless of ordering.

The source batch builder first validates individual original source bodies, then
assembles compact native observations and remaps only question scope keys.
Constructing a large raw three-page body first can hit the old 200KB guard before
compaction is possible. Parent should compact projected states before enforcing
the final body admission. Do not swallow unrelated validation errors or fall back
to dropping source operators.

## Separate geometry hint factor

relation_hint(state) adds source_geometry_hint with the frozen deterministic
divider policy, its source-derived choice, and explicit visibility/selector
limitations. It preserves every original vector mark. Without vector evidence
the hint is unresolved; that is not a claim that dividers are absent from the PDF.
No expected labels, family names or confidence values are consulted.

Compact vectors+hint body maxima: basic singleton 4,024/triple 11,932 bytes;
history singleton 9,031/triple 26,953. All sources fit 24 basic triples and 12
history triples. Treat this as a distinct additive evidence factor. A model
copying the deterministic hint does not demonstrate independent structural
reasoning; report agreement, correct preservation and overrides separately.

## Next frozen L004 comparison

Use canonical compact, vector compact, operator compact and vector compact plus
source geometry hint with exact requested model IDs. Keep parent-request lineage,
new body hashes, source hashes, byte counts and adaptive group memberships. The
original HTTP400 is retained; compact transmissions are a new experiment.

Round-trip identity shows source conservation, not representation-independent
model quality. Measure raw/compact decision flips, invalid responses, unresolved
frequency, exact source group ownership, full-source versus admitted-evidence
answerability, per-encoding nuisance flips, HTTP errors, provider tokens/costs,
latency and bytes. Different adaptive batches are a second intervention; compare
matched singletons when attributing changes specifically to compaction. Further
lexical or geometry compression must be a separate lossy experiment if proposed.

The serial local process, including native glyph/operator/vector/crop preparation
and repeated packet construction, took 15.781s wall, 15.654s CPU and 414,089,216
bytes peak RSS. Measurement: perf_counter/process_time/getrusage lifetime RSS,
current process only, no sampling; concurrent workspace work was uncontrolled.
These are preparation resources, not compact-only latency or remote inference.
Full local data and driver remain ignored here as compact-data.json/run_compact.py.
