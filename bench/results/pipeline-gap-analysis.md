# P001 remaining pipeline gaps

The current normalized source and candidate inventory can represent 34 of 35
structurally scored positive DEV pages exactly. Admission and selection remain the
larger observed bottleneck: 38 of 133 negative pages also have a nonempty table
candidate. The remaining positive candidate gap is column placement after OCR,
with the correct text already present. This report does not change any proposer,
threshold or running job.

## Scope and freeze

The corpus contains 181 pages: 35 scored positives, 133 scored negatives and 13
pages with incomplete references that remain diagnostic only. Source snapshots and
complete alternatives for every page were frozen before opening private DEV
references. The source/candidate freeze SHA-256 is
`e169737634f2b21003d855b987b5bc8c52d3212d7900097b91a0dfe4249f5024`.
Dataset SHA-256 is
`3a1268f1d731a7c60a3fa91f1e90e887c3f41a84aec05beed81b797253afa9b2`.
Full artifacts remain ignored under `pipeline-p001-gap-audit` in this worktree.
No protected heldout data, credentials, network or new inference was used.

The raw arm preserves page display rotation and extractable text. The normalized
arm sets nonzero source `/Rotate` to zero in the owned document and reuses the
already retained 150-dpi, four-thread native OCR overlay for the one successfully
recognized empty page. It does not rerun OCR. Candidate coverage means an offline
oracle found an exact complete alternative; it is not model accuracy or a deployable
selection procedure.

| Source/candidate arm | Positive exact candidate | Negative nonempty candidate | Scored packet refusals |
|---|---:|---:|---:|
| Raw source | 31/35 | 41/133 | 2 |
| Rotation normalized plus retained OCR | 34/35 | 38/133 | 0 |

Every negative page has the no-table exact alternative. Consequently the normalized
oracle has 167/168 exact scored page assemblies available. This says little about
whether a model will choose those alternatives. Thirteen incomplete-reference
pages are excluded from these quality totals, but retained in failure accounting.

## Source and proposal bottlenecks

Three raw positive gaps are right-angle page rotations
(`p8d104fed6afa48613c22`, `pebc369da3589d49db78f`,
`p83c1cc5f249e59a2fcde`). Removing source page rotation supplies the missing
three-column alternatives without altering literal source content. These are
coordinate-frame failures; increasing model image resolution cannot create a
missing candidate.

The fourth raw gap, `p0489b6b5eb7453558f06`, has no extractable text. Its retained
OCR overlay supplies all characters needed by the target matrix, and the physical
corridor candidate has the correct 3-by-3 dimensions and unit spans. Five of nine
slots are correct. Two middle-column values are assigned into the left column,
leaving the corresponding center cells empty. OCR left edges for the center data
are 271.1127 and 271.3097; the seed label starts at 271.4304. A strict lower-bound
corridor assigns those slightly earlier data words to the preceding column.
The repeated-edge alternative retains only two columns because the sparse final
column has two supporting physical rows. It therefore omits the right header and
numeric value from the table. This is a placement and sparse-column coverage gap,
not a missing recognized-string problem.

The character check above compares exact non-whitespace character multisets in
reference cells and complete source words. A deficit proves that source inventory
cannot spell the reference literally; absence of a deficit does not prove correct
recognition, word grouping, placement or reading order. No spelling corrections,
reference text substitution or inferred values are permitted by this analysis.

The wrapped-record page `p4008d04284856d1d4944` already has an exact
`seed_sparse` candidate: its two continuation bands join the preceding description
cells while independent numeric rows remain separate. The physical candidate has
six rows; the correct rolling candidate has four. There is no candidate gap on
this fixture. Selection and repair must preserve that distinction rather than
merging any visually nearby row.

## Completed runs and selection errors

These rows use complete retained reports and the same offline scorer. Pilot rows
have 16 positives and 16 negatives and must not be compared as full-corpus rates.

| Run | Pages | Exact positives | False-positive negative pages |
|---|---:|---:|---:|
| `native-r1` | 181 | 16/35 | 0/133 |
| `native-text-r1` | 181 | 3/35 | 26/133 |
| `full-native-ocr` | 181 | 16/35 | 0/133 |
| `full-assembly-pplx` | 181 | 34/35 | 27/133 |
| `pilot-pplx-256` | 32 | 15/16 | 4/16 |
| `pilot-oriented-pplx-256` | 32 | 16/16 | 4/16 |
| `pilot-gated-pplx-relational` | 32 | 16/16 | 1/16 |
| `pilot-frontier-sonnet` | 32 | 16/16 | 0/16 |
| `pilot-adaptive-pplx` | 32 | 12/16 | 6/16 |
| `pilot-gated-luna-1024` | 32 | 16/16 | 1/16 |

Raw PPLX's single positive pilot failure has no exact retained rotated alternative.
The oriented run fixes that gap. The remaining four false positives show that
candidate geometry is insufficient to establish relational table semantics.
Relational admission reduces that pilot count to one; the completed Sonnet pilot
rejects all 16 negatives. These are observed pilot results, not calibrated
confidence or estimates of independent generalization.

The adaptive PPLX pilot misses four positives despite retaining exact complete
alternatives. All four route through local repair and take two edits. High reported
choice scores accompany incorrect edits, so a score threshold alone cannot justify
calling these decisions reliable. The observed failure is routing/selection within
a bounded edit workflow, not insufficient source content. Global complete-assembly
selection is the stronger retained result for this pilot.

`full-assembly-pplx` subsequently completed all 181 page attempts and retained
175 complete outputs. It achieves 34/35 exact positives and 433/437 correct
reference cell slots. Its single positive failure is the same OCR placement gap
identified independently in the frozen source oracle; all available exact positive
alternatives are selected correctly. Its 27 negative false-positive pages are
selection/admission failures, since the complete no-table alternative is available.
Offline provenance groups these as ten companion prose pages, fifteen DEV silver
two-column/three-column/reading-order pages and two structure multicolumn pages.
No case metadata enters the candidate or model evidence.

Twenty-one of these 27 wrong complete-assembly choices report maximum choice scores
at least 0.8; the largest is 0.978. These scores are not calibrated correctness.
They come from assembly decisions, so they must not be treated as a direct estimate
of the planned separate admission gate's confidence behavior. A relational
admission/review arm still needs its own complete positive and negative results.
All six output failures in this full run are diagnostic-only: the two empty OCR
pages, malformed native span tiling and three complete-packet refusals listed below.

## Unsupported and diagnostic pages

`full-native-ocr` writes complete outputs for 178/181 pages. Its remaining three
failures are diagnostic-only: two pages still have no recognized text
(`p3f7bfc297070e135c969`, `p7236903ef4ab098324dd`) and one native
58-by-25 grid has an uncovered physical row in its observed spans
(`pfe3eba53239267b4e870`). Strict span validation correctly rejects the hole
rather than inventing a merged region. OCR does not repair native grid topology.

Three normalized diagnostic pages exceed the complete 25,000-character packet
limit: `p5005dd1ec0a0e6595b89` (326 words),
`p6333ca96842cead34e25` (637 words), and
`pf2ab4d0b6b137ba48d77` (1,098 words). The zero-word pages above cannot
become successful page conversions simply by selecting a no-table alternative.
Keep unsupported states and diagnostic pages visible even though they do not
contribute to scored structural totals.

## Next source-only hypotheses, declared before implementation

1. Offer a separate optional column-consensus proposer. Preserve native topology
   and all unresolved source IDs. Retain columns from a multi-fragment seed band,
   including a final column absent in one data row. Use nearest consensus edges or
   centers and geometric separators, with an em-normalized allowance for scan/OCR
   edge drift, rather than strict floor lookup of seed starts. Keep physical and
   conservative continuation alternatives; admission remains separate. Construct
   fresh tests for sparse rows, drifting edges, empty cells and aligned prose.
   The proposal must never use fixture text, IDs, families or target geometry.
2. Keep relational table admission separate from column/row assembly. Evaluate the
   already planned independent review on uncertain admission decisions against
   both full positive coverage and negative false positives. Decisions remain
   uncalibrated; abstention must not erase unsupported source failures.
3. Prefer complete-alternative selection over local repair when a bounded repair
   cannot reach an already retained global alternative. Measure edit reachability
   and wrong-edit regressions before adapting the route further. A continuation
   predicate must distinguish sparse wrapped text from independent records.
4. Treat native-span repair as its own source-geometry experiment. Derive any
   proposed physical row boundaries from native cell boxes and rules; preserve an
   explicit unsupported alternative for contradictory geometry. Do not fill holes
   solely because a reference matrix expects a row.
5. Reduce packet repetition without removing source evidence: a complete shared
   table/ownership dictionary with alternatives referring to entries can reduce
   duplicated values, spans and unresolved IDs. Preserve the exact whole-page
   source inventory and fail explicitly if the new complete packet still exceeds
   its bound. This addresses diagnostic scale, not currently measured positive
   candidate coverage.

## Resource scope

The full two-arm source/proposal audit plus offline scoring took 6.66 seconds wall
and 6.82 seconds process CPU. `getrusage(RUSAGE_SELF)` lifetime peak RSS was
538,996,736 bytes, measured without sampling in one sequential process and no
subprocesses. Linux high-water can include inherited process history; it is not
used as a module-specific memory comparison. Per-stage memory is unmeasured.
`full-native-ocr` separately reports 7.00 seconds wall, 17.83 seconds CPU and
465,768,448 bytes peak process RSS sampled every 100 ms. Neither figure includes
paid inference. Hosted GPU resources remain unmeasured.

The completed hosted assembly run reports 198.00 seconds wall, 98.14 seconds local
process CPU and 558,686,208 bytes sampled peak RSS. Its elapsed time includes
transport and hosted inference; local process CPU includes extraction, rendering
and response handling. Remote inference resource usage is unmeasured. These figures
are not a CPU-only comparison against the independent source audit.
