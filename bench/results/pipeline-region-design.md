# P002 source-only bounded region decomposition

`bench.pipeline_regions` proposes independent work units from literal positioned
words and native grid geometry. It does not decide whether aligned content is a
table. All word IDs, cell boxes and word boxes remain in original display
coordinates; `bbox` requests a padded image crop. The caller clips that request
to the page raster. Cropping does not translate or renumber any source.

## Declared hypotheses and minimal alternatives

1. Preserve each validated native grid as an atomic region before considering
   residual words. This avoids a recognized ruled grid swallowing a separate
   borderless table or nearby prose. Word centers must have one unique native
   cell owner; ambiguous words remain residual. Native input values, roles,
   annotations and filenames never enter proposals.
2. Split residual source first at empty vertical gaps greater than both 2.5 median
   glyph heights and 2.5 times the typical positive inter-band whitespace. Within each vertically connected block, split at the widest
   globally empty horizontal corridor only when it is at least six heights and
   16% of the block width, with at least three physical bands and a four-height
   median physical-band content width on each side. The corridor must also
   exceed the largest internal globally empty corridor by a factor of 1.8. Physical-band clustering permits half a median
   height of OCR drift and does not chain drift transitively.
3. If these geometry splits still exceed the configured budget, retain whole
   physical bands in bounded chunks. A single oversized band is partitioned by
   words. Both fallbacks expose `context_complete=False` and `capacity_rows` or
   `capacity_words` boundary metadata. Such boundaries may cut table topology;
   composition conserves source but does not claim reconstruction across them.

The minimal alternative is existing full-page/vertical-gap assembly; it retains
more page context but refuses pages above 4096 words or 16000 source characters
and does not independently gate multiple blocks. A second alternative is blind
fixed word batches, which fit admission but more often sever rows and grids.
The implemented ordering uses geometry first, capacity only when necessary.

## Interface and ownership contract

- `split(page, max_words=512, max_characters=8000, crop_padding=4.0)` returns a
  clean page source, `coordinate_space="display_global"`, and regions with
  `id`, `kind`, `bbox`, `source_ids`, `source`, `boundary`, and
  `context_complete`. Each region source retains the original `page_size`.
- Native grids remain atomic and may exceed configured chunk budgets up to the
  existing 4096-word/16000-character source admission. Oversized atomic grids
  reject the plan rather than silently losing or dividing topology.
- `unresolved_region(region)` supplies an explicit complete abstention.
- `compose(plan, states)` requires one validated assembly per region ID. It
  validates literal values, spans, local ownership, unchanged source geometry
  and aggregate ownership before returning a complete state. Missing, duplicate,
  invented or cross-region IDs reject the whole result. Region state dictionaries
  and plan snapshots are copied where necessary so mutation does not silently
  change the original page source. Results restore unresolved IDs to original
  source order. Tables retain region enumeration order; presentation ordering is
  the caller's responsibility.
- `validate_composed(page, state)` validates an aggregate without the old
  whole-page packet admission. Complete page admission is 65536 words and
  4 Mi source characters; region admission remains compatible with the old
  assembly validator. Region count is capped at 1024. Character limits count
  Unicode characters plus ID characters, matching existing source admission;
  they are not a promise that every candidate packet fits 25000 characters.

No gold structure, challenge family, filename routing, model, credentials,
network request or image interpretation is used. Invalid vector topology fails
before any source ownership is removed; callers can explicitly discard invalid
vector proposals and retry the complete literal source. Semantic table/prose
false positives remain decision-gate work. Empty pages compose to empty results.

## CPU verification

39 Python tests across region decomposition, existing assembly and existing
column consensus passed. The new region suite covers two native grids plus a
borderless block and prose, a merged native cell, 6000-word dense input above the
old packet/source limits, side-by-side and vertically separated blocks, OCR
position drift, prose abstention, oversized physical bands, atomic native budget
exceptions, malformed native spans, missing/duplicate outputs, source mutation,
bad configuration and an empty page. Ruff and targeted mypy passed.

Measurement used Python `time.perf_counter` and `resource.getrusage(CHILDREN)`
around one pytest subprocess, including imports, with no workers and CPU only:
wall 0.4587 s, user CPU 0.424087 s, system CPU 0.031817 s, peak RSS 53108 KiB.
CPU use was measured cumulatively rather than sampled. These are validation
resources on the current shared development host, not extraction-performance
claims or a quality comparison. No remote inference was used.

## Limitations and follow-up evidence

A large title crossing both blocks prevents a horizontal split; a very wide
column gutter can instead split one real table into two work units. Native
ownership uses word centers, so words crossing cell edges remain sensitive to
geometry. Capacity cuts need neighboring read-only context or an explicit
cross-boundary topology protocol before claiming complete dense-table
reconstruction. This module supplies neither semantic header inference nor
cross-region table stitching. Those gaps are visible in boundary metadata and
must be reported alongside any pipeline quality results. Native table assignment
reuses the existing word-by-cell intersection procedure; high-cardinality grids
need profiling before making performance claims.


## Frozen P002 authored audit and measured correction

The frozen P002 manifest contains 156 authored pages, with 156 expected tables
including separately labeled OCR carriers. This CPU audit performs no OCR and
uses native extraction only. Private construction targets enter scoring after
literal source extraction and candidate generation; neither their boxes nor
family labels enter the region proposer. Complete-table equality checks dimensions,
normalized literal values and full span topology. A region-wise target-aware
selection is composed and validated to measure attainable candidate coverage;
this is an oracle diagnostic, not deployment quality or a learned decision gate.
A separate candidate-pool count takes each signature's maximum multiplicity
within a region, then sums across regions before matching target multiplicities.
The first provisional pool count did not sum duplicate signatures across regions;
its underestimated count is retained in the raw `before` audit and superseded by
`before-corrected` below.

Acceptance was exact source conservation, no new errors, no regression in
complete-table coverage across authored slices, and recovery of avoidable splits.
The minimal full-page proposal arm remains a reference. Baseline and every
sequential treatment are retained under the ignored
`bench/results/pdf-master-artifacts/pipeline-p002/regions-audit/` directory.

| Arm | Complete candidate tables / 156 | Validated oracle-composed complete tables | Authored pages with split target tables | Wall / CPU seconds |
| --- | ---: | ---: | ---: | ---: |
| Native tables only | 108 | 108 | n/a | included in runs |
| Full-page assembly plus column consensus | 132 | 132 | n/a | included in runs |
| Initial regions, corrected pool metric | 116 | 116 | 16 | 4.228 / 4.128 |
| Relative vertical whitespace only | 116 | 116 | 16 | 4.895 / 4.772 |
| Relative whitespace plus corridor contrast | 132 | 132 | 0 | 5.600 / 5.110 |
| Frozen combined-treatment confirmation | 132 | 132 | 0 | 5.356 / 5.152 |

The original absolute threshold severed ordinary 33-point rows containing
8-point glyphs. Adding typical inter-band whitespace preserved those rows, but
then exposed a second failure: wide table column gaps were mistaken for
independent blocks. Requiring the proposed corridor to exceed internal corridors
and requiring sustained median content width fixes both causes without names,
family conditions or target-derived thresholds. The combined treatment recovers
16 complete tables: eight borderless and eight residual tables on mixed pages.
No other authored slice loses complete-table coverage. Missing remaining tables
are outside this region correction's coverage: rotated construction targets and
OCR-only carriers still require separate extraction/normalization work.

All 156 pages retain valid source conservation and have zero split/proposal or
region-candidate errors in these audits. The same frozen sources were reused
for matched comparisons, avoiding extraction warm/cold differences; the initial
uncached run is separately retained (10.860 wall / 10.759 CPU seconds). RSS is
process peak from `resource.getrusage(SELF)`, 427412 KiB in screening runs
and 489980 KiB in the separate frozen confirmation run. Wall uses
`perf_counter`, CPU uses `process_time`; one CPU-only process, no workers or
subprocesses, no RSS sampling. These timings include source-cache reads, native,
full-page and region proposals, scoring, and report writes. They measure audit
cost, not an extraction-speed improvement. Shared-host background load and one
screening run per arm plus one combined confirmation do not support a precise performance comparison.

Rerun with the root Python environment and the region worktree on `PYTHONPATH`:
`python bench/results/pdf-master-artifacts/pipeline-p002/regions-audit/audit.py <arm>`.
The harness, per-page sources, before/after page reports and summary JSON remain
ignored. Four regression cases cover sparse leading with three, four and five
regular table columns and independently separated two-column tables. The existing
side-by-side, OCR-drift and source-conservation tests still pass.
