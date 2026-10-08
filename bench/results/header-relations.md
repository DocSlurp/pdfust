# Experimental CPU header relationships

Reproduce: `.venv/bin/python -m bench.header_relations`.

Loaded native extension SHA-256: `dbc4c1c26cea0f34b00881c51942056259e383cddf46865fe9eaaf9d1293bfa6`. Full Python/platform/library and Rust source provenance is retained in decisions.json.

112 generated PDFs: 14 structural/semantic families × two scales × four right-angle rotations. No training, GPU, network, or inference service. Gold bands and edges are fixture declarations; text and spans are checked independently. Variants share templates and are not independent documents or held-out production accuracy.

| Method | Correct bands | Abstained | Edge TP / FP / FN | Precision | Recall | Median inference + graph µs |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| first_row | 40/112 | 32 | 240 / 208 / 544 | 0.536 | 0.306 | 45.3 |
| constraints | 56/112 | 48 | 672 / 48 / 112 | 0.933 | 0.857 | 55.0 |
| strict_unhinted | 0/112 | 112 | 0 / 0 / 784 | n/a | 0.000 | 1.4 |
| strict_declared | 112/112 | 0 | 784 / 0 / 0 | 1.000 | 1.000 | 37.9 |

Strict-unhinted accepts no semantic edges without role evidence. Strict-declared is schema-assisted: fixture declarations are explicitly supplied as caller bands, so its numbers measure source relationship materialization, not header prediction accuracy. Headerless declarations accept a zero-header band. This coverage/false-edge tradeoff cannot be solved by score threshold tuning alone.

| Method / edge kind | TP | FP | FN |
| --- | ---: | ---: | ---: |
| first_row / column | 240 | 208 | 416 |
| first_row / ancestor | 0 | 0 | 96 |
| first_row / row | 0 | 0 | 32 |
| constraints / column | 544 | 48 | 112 |
| constraints / ancestor | 96 | 0 | 0 |
| constraints / row | 32 | 0 | 0 |
| strict_unhinted / column | 0 | 0 | 656 |
| strict_unhinted / ancestor | 0 | 0 | 96 |
| strict_unhinted / row | 0 | 0 | 32 |
| strict_declared / column | 656 | 0 | 0 |
| strict_declared / ancestor | 96 | 0 | 0 |
| strict_declared / row | 32 | 0 | 0 |

Identifiability control: eight paired PDFs have identical bytes, words, cell boxes and geometry but different independently declared application roles (first row data versus header). Constraints make the same prediction on both, and therefore cannot be correct for both. Strict-unhinted abstains on both; explicit caller roles distinguish them. Input SHA-256 hashes and declarations are retained.

Exact extracted cells/spans: 112/112. Opening + first layout median: 8.661 ms. Inference timings exclude extraction, use one local pass, and are not robust throughput measurements.

Edges distinguish column-header/value, header ancestry, and row-header/value relationships; IDs refer only to retained snapshot cells. Merged headers and repeated labels retain separate IDs. No new cell text or geometry is synthesized. Abstention retains the complete original table.

| Family | Constraint correct band | Constraint abstentions | Edge TP / FP / FN |
| --- | ---: | ---: | --- |
| simple | 8/8 | 0/8 | 48 / 0 / 0 |
| hierarchy | 8/8 | 0/8 | 96 / 0 / 0 |
| repeated-labels | 8/8 | 0/8 | 176 / 0 / 0 |
| units | 8/8 | 0/8 | 96 / 0 / 0 |
| numeric-headers | 0/8 | 8/8 | 0 / 0 / 48 |
| date-headers | 0/8 | 8/8 | 0 / 0 / 32 |
| headerless-numeric | 0/8 | 8/8 | 0 / 0 / 0 |
| mixed-prose | 0/8 | 8/8 | 0 / 0 / 0 |
| row-headings | 8/8 | 0/8 | 64 / 0 / 0 |
| all-text-headers | 0/8 | 8/8 | 0 / 0 / 32 |
| headerless-mixed | 0/8 | 8/8 | 0 / 0 / 0 |
| headerless-type-shift | 0/8 | 0/8 | 0 / 48 / 0 |
| type-shift-declared-header | 8/8 | 0/8 | 48 / 0 / 0 |
| three-level | 8/8 | 0/8 | 144 / 0 / 0 |

Segmented/coalesced rule encoding audit after the connectivity fix: eight scale/rotation pairs produce identical RGBA pixel SHA-256 hashes. Both segmented and coalesced forms detect 8/8 native tables. Before the fix, segmented forms detected 0/8 and coalesced forms 8/8; pre-fix decisions and pixel hashes are retained in phase2-before-connectivity.json/md. This verifies representation invariance for these cases, not a header semantics improvement. Root cause: the middle left-border segment had no perpendicular intersection; joining touching/overlapping collinear fragments restores its component membership without changing any rule geometry.

Numeric/year/date headers and headerless numeric data are observationally ambiguous under these rules; the method abstains. All-text headers lack type contrast. The original fragmented-rule three-level fixture yielded no table in eight variants. The outer left border was split at rows without an intersecting horizontal rule; the middle collinear segment became disconnected under the extractor’s perpendicular-intersection component grouping (rust/src/extract.rs). Coalescing contiguous collinear rules changes only drawing segmentation and restores the 5×3 table. Current semantic fixtures coalesce rules; the separate post-fix encoding audit and Python regressions test both representations. The first unconditional connectivity patch regressed Form 1040 by merging independent form-rule networks. The final repair preserves every accepted perpendicular grid, skips repair unions involving those roots, and admits repaired candidates only outside retained table bboxes. Existing Form 1040 regressions and parallel-decoration snapshot checks guard this restriction. The original segmentation failure is fixed by connecting parallel interval neighbors within the existing snap tolerance, while preserving all original segments. The original 104-case results are preserved in phase1.md/json, so the improved denominator is not silently compared as the same corpus. A headerless table whose first data row is textual but whose following rows contain numbers falsely looks like a header: this is the key known accepted error, not cured by source IDs. Row scope uses a narrow stub vocabulary and does not prove semantic scope. Text-only inputs, missing cells, and broad domain lexicons need independent evaluation.

Corpus first-page audit (unscored for semantic edges):
- senate-expenditures.pdf: 1 native tables; 2×7: insufficient body support
- nics-background-checks-2015-11.pdf: 1 native tables; 58×25: ambiguous or unsupported header band
- f1040.pdf: 1 native tables; 2×7: insufficient body support

The existing corpus references check values, not independently annotated header ancestry. Senate has a ruled header with an unruled body; NICS has a large merged header. A header-only native grid does not supply full-document value relationships. No corpus edge accuracy is claimed. Existing structure-findings.md and spatial-latest.md already document these gaps; this run adds semantic edge scoring instead of repeating model experiments.

Next experiments: annotate source-ID column scopes for complete Senate/NICS regions; evaluate independent unseen document families; add typography and separator evidence to distinguish a first data row; compare explicit application schema hints versus conservative abstention. Keep evidence and source text when header semantics remain ambiguous.

Complete decisions, source cells, and generated PDFs remain in ignored `pdf-master-artifacts/headers/`. This is a benchmark prototype, not a default API policy.
