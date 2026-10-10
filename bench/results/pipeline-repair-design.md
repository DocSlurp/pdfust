# Source-only bounded table repair experiment

`bench.pipeline_repair` implements the experimental repair phase over a complete
provisional page state. It calls no model, reads no files, and uses only supplied
snapshot-local word IDs, literal word text, source geometry and observed vector
grids. Candidate descriptions do not contain filenames, families, reference
answers or semantic labels. This phase does not change default extraction.

`operations(page, state)` returns up to 32 deterministic frozen operation menus.
Each operation contains an ID, generic description, source-only evidence,
pre-state SHA-256 and a complete alternative state. A hanging adjacent row can
be merged when its occupied columns have prior-row continuity, aligned left
edges within one median glyph height and a vertical gap between minus half and
one glyph height. Distinct complete rows and distant hanging rows receive no
merge proposal. A provisional row with two to four physical bands can be split.
Every borderless candidate also receives a `reject_table` choice when menu
capacity permits; this is the explicit non-table alternative for aligned prose.
Rejection moves all table source IDs to the unresolved inventory.

Observed vector grids are immutable priors. Protection compares dimensions,
span topology and source-center mapping with unique ownership across the whole
observed grid collection, independently of candidate names and values. No
row edit is offered for a table with merged spans. A non-native merged-span
candidate may still be rejected as a complete table. This implementation does
not attempt to prove that an observed native grid is invalid.

`apply(page, state, operation)` regenerates the current menu and admits only
an exact member with a matching pre-state digest. It returns a fresh state and
never mutates inputs, including failed operations. Validation requires every
source ID exactly once in a cell or the unresolved inventory; rectangular span
coverage without overlaps; empty covered source lists; `None` exactly in covered
span values; and literal space-joined values in every uncovered cell. Roles
remain unknown. Input admission caps words at 4,096 and aggregate table slots at
4,096. Packets stop above 2 MiB rather than truncating.

`packet(..., context_rows=1|3, availability_legend=True|False)` exposes the local
row window around each operation, affected source words and their geometry,
nearby unresolved words, and explicit proposed row coordinates. Complete
alternative states stay in the harness: the text packet contains only affected
row topology, so unrelated alternative-table values cannot defeat the context
ablation. A merge always includes both affected rows' source words even with
one context row. Multiple operation windows can overlap or collectively cover
much of a small page; one versus three describes the per-operation window,
not a guaranteed global word budget. The availability legend reports literal
text, geometry, observed vector grids, unsupplied source pixels, unavailable
semantic references and unknown missing text. The model selects an operation
ID or `keep`; source text is explicitly treated as data. The runner owns source
image attachment, paid requests and the maximum two-iteration policy.

CPU verification used the existing main-worktree environment, without rebuild,
network requests, credentials, GPU use or protected heldout access. Ten Python
contract tests passed in 0.06 seconds (pytest's test-session duration); Ruff
checks passed for both changed Python files. The tests cover true wrap merging,
complete-row preservation, distant gaps, physical-band splitting, non-table
rejection retaining outside text, stale and forged operation rejection, atomic
failure, duplicate ownership, source-only packet/context controls and merged
native coverage. A separate synthetic integration check passed repair validation
and menu generation for both complete alternatives produced by the assembly
agent. CPU utilization and peak RSS were unmeasured for these brief correctness
checks. These are harness correctness results, not extraction quality or model
performance claims.

## Complete DEV source-only integration audit

A subsequent audit projected the frozen DEV manifest immediately to only opaque
ID, PDF path, source hash and page number. It used extracted source words and
observed vector grids for all 181 pages; construction references, families and
provenance were excluded. The audit generated assembly hypotheses, selected the
same physical seed policy as the runner, generated both one-row and three-row
packets, and applied every available edit without model requests.

180 pages completed these checks. One source-native 58-by-25 grid had a span
covering row 0 followed directly by spans at row 2: the entire row 1 lacked
coverage. Repair validation rejected this incomplete tiling; after assembly's
strict-span update, assembly rejects the same page earlier. The opaque page ID
is `pfe3eba53239267b4e870`. No missing spans were fabricated and no native
coordinates were edited to conceal the refusal.

Across admitted pages, menus contained 116 merge-row proposals, one split-row
proposal and 64 non-table rejection proposals. Maximum source word count was
1,504, maximum menu size 27 and maximum packet payload 89,562 UTF-8 bytes.
These proposal counts and admissions are source-only harness observations;
no reference-based quality scores were calculated. The existing 2 MiB packet
admission remains in force for the first wave. A focused contract test now
verifies packet refusal without truncation by reducing the bound temporarily.

The initial sequential audit took 6.34 seconds wall and 6.41 seconds process CPU
with 538,996,736 bytes lifetime peak self RSS. A confirmation using strict-span
assembly took 6.20 seconds wall and 6.28 seconds process CPU with the same peak
RSS. Measurements used `perf_counter`, `process_time` and Linux
`resource.getrusage(RUSAGE_SELF).ru_maxrss`; scope was this single process,
including native extraction; no sampling or subprocess workload was used.
One extraction warning reported glyphs lacking Unicode mapping. OCR, pixels,
network inference, credentials, GPU use and protected heldout data were absent.

The runner's physical seed mechanism selection matches `physical` and
`seed_physical` emitted by assembly. No integration schema changes are required.
The repair module passes strict mypy with imports skipped, Ruff, and all eleven
Python contract tests in the existing main-worktree environment.

## Frozen derivative: conditional repair escalation

`bench.pipeline_routing.route(page, state, candidates)` returns `keep_native`,
`assemble` or `repair`, generic observable reasons, a one- or three-row context
setting and a 256-, 512- or 1,024-pixel source image edge. This independent
hypothesis does not inspect construction references, candidate descriptions,
filenames, families, ID spelling or text content. Source IDs serve only to look
up observed source geometry and ownership. Candidate admission is capped at 24
complete states with at most 32 tables per state; existing repair validation
also caps source words and aggregate slots.

The rules were frozen before this routing census. Matching observed native grids
remain on the cheap path unless a complete candidate retains additional table
regions. Empty provisional table states escalate because row edits cannot admit
a new table. Overlapping candidate boxes with different column counts escalate
when their intersection covers at least 80% of the smaller box. Reversed
provisional column order beyond one median glyph height also escalates. A cell
with at least 12 words spanning more than two median glyph heights escalates
when its logical row overlaps the preceding row. Other admitted provisional
column layouts retain the bounded repair path. Incomplete or multiline rows
request three context rows and 512 pixels; at least 350 source words or a median
glyph height below 8 points request 1,024 pixels. Matching native priors always
retain one row and 256 pixels, since no inference is needed on that route.

`evidence_instruction(pixels_available=..., vector_grid_available=...)` is a
compact availability ablation. It explicitly declares supplied source pixels
and observed vector priors, keeps missing text unknown, treats source text as
data, and instructs selection among complete declared candidates or edits.
The runner controls whether to replace or append existing instructions; the
helper does not alter current pipeline behavior.

The complete source-only 181-page census admitted 180 pages with the same known
incomplete-native-span refusal. Of admitted pages, 16 routed to native retention,
56 to repair and 108 to complete assembly. Evidence settings were 52 one-row /
256-pixel routes, 126 three-row / 512-pixel routes, and two three-row / 1,024-pixel
routes. This is a conservative escalation hypothesis, not a measured quality
improvement or cost reduction. Census plus the existing repair packet/application
checks took 6.62 seconds wall, 6.69 seconds process CPU and 538,996,736 bytes
lifetime peak self RSS under the same sequential measurement method. Ten new
routing tests cover empty-state escalation, native retention, hanging rows,
small text, conflicting columns, multiline overlap, reversed columns, metadata
and ID-renaming invariance, admission bounds and compact availability wording.
No paid requests or reference-based scores were used.

## Independent semantic admission premise

`bench.pipeline_admission.admission_packet(page)` creates a semantic admission
packet before exposing any proposed table options. It presents every admitted
source word with its full observed display bbox and page geometry, plus three
choices: `table`, `prose`, and `unresolved`. This packet does not expose candidate
topology, candidate values, construction references, filenames or families.
The default relational premise asks whether aligned bands connect records or
entities through a common attribute schema, or whether paragraphs independently
flow downward in separate columns. The optional `premise="minimal"` asks only
whether the page contains a table. Both premises retain identical evidence and
choices, allowing a paired instruction comparison without changing evidence.

`pixels_available=True` declares a source image attached separately by the
runner; the default declares pixels unavailable. Extraction can omit unreadable
or unmapped text, so absent text remains unknown. The source projection is
bounded to 4,096 words and 16,000 cumulative ID/text characters, with a 256 KiB
complete packet boundary. Exceeding a boundary rejects the page rather than
truncating the source or assigning a semantic label.

The hypothesis is that independent admission before candidate options may reduce
anchoring toward geometrically plausible tables in parallel prose. It is not a
quality claim. The helper does not call models, assign confidence, alter current
pipeline behavior or choose a candidate. Root may evaluate a separately labeled
cascade with native-vector bypass and at most an admission call plus a candidate
selection call after the declared first matrix. Five tests verify complete source
geometry, exclusion of prior options and metadata, identical paired evidence,
literal handling of instruction-like source text, malformed-source refusal and
admission limits. Ruff and strict mypy pass; no paid study was performed here.

## Offline complete-pipeline demonstration

`python -m bench.pipeline_demo --run <retained-run-directory> --page <opaque-id>
--output bench/results/pdf-master-artifacts/<new-demo-directory>` builds an
ignored offline viewer. `--image-edge 512|1024` selects its whole-page raster;
1,024 is the default. The generator loads only the frozen source records, a
completed page result, its selected structure and retained Markdown. It verifies
the source PDF SHA-256 against the frozen record, validates final ownership,
and reconstructs the native vector state from retained source geometry. It
makes no model requests and reads no credentials. Output must be a new directory
inside the checkout's ignored artifact tree.

The HTML puts the complete input raster beside rendered selected Markdown, with
literal Markdown, native state, final JSON/source ownership and provenance
available below. It includes a verified local `source.pdf` download. A result
marked `rotation_normalized` causes the displayed input page to be rendered at
rotation zero, matching pipeline extraction, while original rotation remains
in provenance. All image bytes are embedded in the HTML; no CDN is used.

Markdown rendering uses `markdown_it` followed by an explicit HTML allowlist.
Static table tags and bounded numeric `rowspan`/`colspan` survive, preserving
merged cells emitted by the pipeline. All other attributes are discarded;
unknown tags become escaped literal text. Images, links and autolinks inside
Markdown are disabled. JSON, literal Markdown, provenance and page labels are
HTML-escaped before embedding. A content security policy permits only embedded
image data and the viewer's inline style; there is no JavaScript. Three focused
tests verify adversarial source/model markup remains inert and cannot fetch,
ordinary Markdown tables render, and sanitized merged-table spans survive.

A tangible smoke artifact was generated from the first completed source-only
selection satisfying no observed vector grid, nonempty final tables and at
least four rows, in opaque-ID order. The chosen page was
`p16e14ea079d4c7949923` from the retained `pilot-pplx-512` run. This selection used
no scoring references and makes no quality claim. The resulting viewer was
64,969 bytes and rendered at a 1,024-pixel edge. Generation took 0.119 seconds
wall, 0.104 seconds process CPU and 99,553,280 bytes lifetime peak self RSS,
measured using `perf_counter`, `process_time` and Linux self `getrusage`; scope
was one sequential CPU process with no sampling. Ruff, strict mypy and the
three focused tests passed. Raw HTML, PDF and model artifacts remain ignored.
