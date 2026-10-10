# P002 capacity-row stitching: useful seam, no measured natural gain

The frozen natural16 audit finds **11/53 reference tables interrupted by capacity
regions across three pages**. Twelve reference tables span any region boundaries.
That supports testing continuation proposals, but the current local candidate
pool cannot benefit yet: ten source-compatible stitch hypotheses produce no new
complete matrices, matrix shapes or optimistic literal-cell matches. Keep this
method experimental and out of automatic assembly selection.

## Frozen contract and source-only method

References are the frozen natural16 dataset
`68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`,
scored offline with `bench.generalization_scoring`. Sources are retained OCR/native
snapshots from `pipeline-p002/regions-audit/natural16/`. Initial intersection
counts use word centers inside reference boxes **only in the diagnostic**;
reference boxes, IDs, families and values never enter proposal logic.

`bench.pipeline_row_stitch.propose(plan, region_states)` accepts one validated
assembly per region and returns a complete unchanged baseline plus explicit
single-boundary alternatives. It recomputes source-only geometric blocks using
the region splitter's existing literal-word method. Only consecutive
`capacity_rows` regions belonging to one such block are considered. Native and
word-capacity boundaries are excluded.

A pair requires at least two logical rows and two columns on each side, matching
column counts, at least two unmerged occupied samples per column, repeated left
or right edges within 0.75 median glyph heights, separated column profiles, and
downward-progressing logical rows. The join gap admits at most three median
heights or twice typical internal whitespace, with at most half a height of
position overlap. Boundary row signatures must share at least two occupied
columns and at least 0.6 Jaccard overlap. These rules provide physical support;
they do not prove shared table semantics.

The keep alternative concatenates literal cells and shifts second-table span
anchors by the first table's row count. A repeated first-row literal signature
also offers a separate drop alternative when no first-row span crosses into
later rows. Drop moves that row's IDs explicitly to unresolved ownership; it
never silently deduplicates source strings or discards words. The state exposes
`stitched_regions`, `repeated_header_unresolved_ids`, and a keep/drop mechanism.
Cells remain literal source-derived values. Every complete output is validated
by `validate_composed`, including native tables and unresolved words elsewhere.
Inputs are not mutated. Alternatives are bounded at 24 and joined grids at
4096 slots; complete source admission remains the region composer's existing
65536-word boundary.

## Measured alternatives and decision

The minimal baseline is separate complete region tables, preserving all source
IDs. The treatment adds independently compatible pair joins while retaining that
baseline. Screening freezes existing assembly plus column-consensus proposals
for each 256-word region, deduplicates identical source ownership/topology, and
tries every compatible adjacent pair. Targets enter only later scoring.

| Diagnostic | Baseline pool | Pool plus stitch hypotheses |
| --- | ---: | ---: |
| Exact complete reference tables | 0 / 53 | 0 / 53 |
| Matching matrix dimensions | 7 / 53 | 7 / 53 |
| Optimistic best literal cell matches | 67 | 67 |
| New source-compatible stitch hypotheses | 0 | 10 |

The literal-cell diagnostic chooses each reference table's best single hypothesis
independently. It can reuse competing or overlapping candidates and is therefore
an oracle ceiling, not a realizable complete pipeline quality score. No source
conservation or composition errors occurred. The hypotheses comprise four pairs
on one newspaper page, two on another and four on an academic page. None restore
a correct reference shape. The two-column academic example's interrupted tables
produce no compatible pair because local extent/columns/row grouping are already
wrong. Boundary concatenation cannot repair those antecedent errors.

No threshold search or target-specific exception was introduced after observing
this no-gain result. A second confirmation run is unnecessary for an unchanged
quality result that is not being accepted into default selection. The module is
retained as an isolated, tested experimental seam for better future local
hypotheses. Capacity stitching alone is rejected as the next natural-quality
optimization. Root's raster physical-cell alternatives and source-supported
cross-region topology hypotheses have stronger measured justification.

## Verification, resources and limitations

59 tests across stitching, raster rules, regions, assembly and column consensus
pass. Eight stitch checks cover aligned continuation with position drift,
keep/drop repeated headers with unique ownership, incompatible edges/separate
blocks, word-capacity abstention, sparse profiles, missing outputs, bounded
alternatives, immutability and merged-span row offsets. Ruff and targeted mypy
pass.

The full natural16 stitch screen took 5.549 wall / 5.524 CPU seconds, including
cached source reads, local proposal enumeration, matching, composition and report
writes. One CPU-only process used a sampler thread, no worker subprocesses and
no model calls. `psutil.Process` RSS sampled every 100 ms peaked at 34066432 bytes;
wall and CPU use `perf_counter` and `process_time`. These are audit resource
measurements on a shared host, not an extraction-speed claim.

Raw counts, every page's before/after diagnostics and the runnable audit script
remain ignored at `pipeline-p002/regions-audit/natural16/` as
`continuation-audit.json`, `stitch-screen-pages.json`,
`stitch-screen-summary.json`, `continuation-audit.py` and `stitch-audit.py`.
Rerun with root `.venv/bin/python`, root on `PYTHONPATH`, and the script's explicitly
recorded region-worktree module path.

The method joins whole logical rows only. It does not repair a row fragmented by
a `capacity_words` boundary, synthesize spans across a cut, reconstruct rotated
rows, infer semantic headers, or combine multiple joins into one Cartesian
alternative. Identical repeated labels may identify distinct tables; the
unchanged baseline and semantic decision gate remain necessary. Recomputed
block membership assumes the existing source-only splitter, rather than arbitrary
caller-supplied crop regions. Better local columns and row boundaries are required
before this stitch seam can raise the measured natural candidate ceiling.
