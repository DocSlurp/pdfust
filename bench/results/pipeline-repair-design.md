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
