# P003 complete-source global gutter controls

All nine frozen full-page gutter profiles fail to recover a complete table on
natural16. The three least restrictive support profiles obtain 14 strict cells
and falsely predict tables on all four negative pages. Expanding source coverage
alone does not make global page-wide physical rows and gutter columns a useful
table representation for this cohort.

Every row retains 16 pages, 53 reference tables and 2,333 reference cells. No
profile was selected separately for a page using gold. Complete-grid refusals
produce empty table outputs with complete source IDs unresolved; these are
explicit acquisition/representation refusals rather than execution errors.

| Gap / word height | Support fraction | Prepared / refused pages | Strict | Text | Structure | Complete | Missing | Extra | Negative FP pages /4 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.5 | 0.1 | 14 / 2 | 14 | 14 | 295 | 0 | 45 | 6 | 4 |
| 0.5 | 0.25 | 7 / 9 | 0 | 0 | 178 | 0 | 48 | 2 | 1 |
| 0.5 | 0.5 | 1 / 15 | 0 | 0 | 2 | 0 | 52 | 0 | 0 |
| 1.0 | 0.1 | 14 / 2 | 14 | 14 | 295 | 0 | 45 | 6 | 4 |
| 1.0 | 0.25 | 8 / 8 | 0 | 0 | 165 | 0 | 48 | 3 | 1 |
| 1.0 | 0.5 | 1 / 15 | 0 | 0 | 2 | 0 | 52 | 0 | 0 |
| 1.5 | 0.1 | 12 / 4 | 14 | 14 | 202 | 0 | 47 | 6 | 4 |
| 1.5 | 0.25 | 6 / 10 | 0 | 0 | 68 | 0 | 50 | 3 | 1 |
| 1.5 | 0.5 | 1 / 15 | 0 | 0 | 2 | 0 | 52 | 0 | 0 |

The fixed language derives physical rows from all eligible source words, with
one global set of column separators supported by physical whitespace gaps.
There is no detector crop restriction, wrap inference or semantic table gate.
It preserves original source strings and whole-word ownership; crossing words
remain unresolved. A page-wide grid can therefore contain prose or incorrectly
join unrelated local tables even when source text is available. The negative
false positives and zero complete tables support prioritizing localized
structure and semantic admission over further tuning of these global profiles.

Version two raises only the physical-row admission from 256 to 1,024. The
32-column and 4,096-slot complete-output caps remain. It still retains 64
prepared states and 80 refusals across the nine full-cohort treatments; the
502-line source page is refused by every profile for grid capacity or absent
supported separators. Version one's earlier row-cap refusals remain separate
provenance. Neither version truncates rows, slots or source words.

Before loading targets, the independent analyzer checked all six archive
authorities against Git `79f2b0e`, authenticated the original ordinal baseline
with external `b773d57` authority, checked actual PDF hashes and complete page
inventories, rebuilt physical groups, all nine plans per page, all 144 source-safe
states and their hashes, and independently checked refusal totals. It then
scored each full treatment against separate DEV references. No execution
errors, API calls, fresh confirmation access or protected heldout access occurred.

The source freeze is `fullsource-tracks-v2`, SHA-256
`e0fedbd5415761c2ecbb867b57ef94e4f0fb182392460d5fad591f6d1323a49a`.
Detailed independently verified results remain in its ignored
`independent-evaluation.json`. Nine focused source/segment/availability tests
and Ruff passed. Recorded source preparation consumed 5.277 seconds elapsed,
5.231 seconds process CPU and 114.14 MiB sampled parent RSS, sampled every
100 ms with psutil; one CPU process, no subprocesses or local GPU. These
measurements cover source authentication and all 144 prepared/refused variants,
not a useful-output pipeline throughput claim. Original OCR/source acquisition
costs remain separate; APIUSD throughput is undefined for this zero-call control.
