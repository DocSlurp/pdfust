# P002 natural16 source and candidate ceiling audit

The existing geometry alternatives cannot reconstruct the frozen natural16
references: their candidate pool contains **0/53 complete tables**, only **7/53
matching matrix shapes**, and **6/53 table boxes with IoU at least 0.5**.
Geometry overlap is a diagnostic, not cell correctness. A new raster-rule
alternative recovers three exact physical cell topologies and 106 literal cells,
while strict complete-table correctness remains zero because source/reference
text differs. Raster proposals remain unaccepted alternatives.

## Frozen evidence and separation

Inputs are the explicit `pipeline-p002/screens/natural16/manifest.json` and
`private-targets.json`, dataset identity
`68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.
There are 16 pages and 53 reference tables, including four negative pages.
Offline scoring uses `bench.generalization_scoring`, which interprets omitted
unit spans consistently. The authored/P001 scorer is not used for these natural
references. Official references remain unchanged.

Fifteen OCR/extracted sources are reused from the completed whole-page reviewed
run. That run attempted every page and produced nine outputs and seven errors:
six packets above 25000 characters and one source above 16000 characters. The
single missing source was recovered separately using native CPU OCR at 150 dpi,
four inference threads, without changing the completed run artifact. The
recovered page has 1942 extracted words. The OCR audit saved the full literal
source before a raw-recognition serialization error; its timing and memory are
unmeasured, and no second OCR request was made. Existing successful sources
retain OCR-region counts but not the original per-region recognition records.

Private references enter only the offline scorer and diagnostic matching after
source proposals. No reference geometry, text, page IDs, family labels or filenames
participate in candidate generation. No paid request, network inference or GPU
was used. Raw sources, scripts and complete reports remain ignored under
`pipeline-p002/regions-audit/natural16/`.

## Source text, geometry and granularity

Reference-token multiset overlap recovers 2769/3921 tokens (70.6%) somewhere on
the corresponding page, but only 1564/3921 (39.9%) inside reference table boxes.
These are optimistic lexical diagnostics: page tokens may be credited separately
to different tables and do not establish unique cell ownership. Differences
combine recognition substitutions, missing text, annotation spelling/math
representations, segmentation, and geometry. They do **not** prove that 29.4%
of visible source text is physically absent. Physical missing-text fraction is
unmeasured without independently transcribed word boxes and recognition records.

Only 1017/2333 reference anchor cells have all their token counts present within
their table box, ignoring order, case, punctuation and ownership. This also credits
empty cells and is an availability ceiling, not an extraction score. All reference
table boxes fit inside their source display rectangles, so the local overlap drop
is not explained by a gross page-size coordinate mismatch.

The failure modes differ by page:

- Dense newspaper pages have many neighboring small tables. OCR can merge text
  across physical columns; re-extracting the invisible layer supplies approximate
  token positions within recognized text regions. Page-wide words elsewhere can
  match table tokens without placing them in the correct cell.
- A two-column academic page has reference row counts 24 and 9 and matching
  physical band counts, with 202/206 reference tokens locally recoverable. Its
  available geometry proposals still lack the correct matrix shapes. Extent,
  column selection and sparse/wrapped continuation policies constrain the pool.
- Other examples have six logical rows versus fourteen physical text bands, or
  a five-row merged-header table versus twenty-seven physical bands. Physical
  lines are not logical cells; wrapped rows and headers require competing
  grouping and span hypotheses.
- The Cambridge slide has one physical row, two physical cells, and seven text
  bands in each cell. Text-only alternatives incorrectly infer text bands as
  rows. Clear raster rules supply the missing physical-cell evidence.
- Mathematical and scientific cells retain strict case, punctuation, Unicode
  and math representations in scoring. Joining available source tokens cannot
  invent the missing symbols or normalize a reference spelling into correctness.

## Packet admission at 256 words

Splitting into at most 256 residual words produces 47 regions. With complete
existing assembly plus column-consensus alternatives, **29/47 original packets**
and **27/47 readable packets** still exceed 25000 characters. Maximum sizes are
204522 and 68824 characters, respectively. The audit measures the full encoded
packet before admission, without truncating candidates or source.

Word bounds therefore do not bound packet size: repeated cell values, topology,
spans, complete unresolved ownership and multiple alternatives can dominate the
transport. A separate source-preserving selection packet or staged candidate
comparison is needed. Smaller word batches alone risk cutting physical tables
and wrapped rows. Raw per-region sizes and boundary flags are retained in
`audit-pages.json`; the summary is `audit-summary.json`.

## Raster-rule candidate: measured partial recovery

`bench.pipeline_dense_candidates.raster_vectors(image, display_bbox)` reads a
PIL image and returns physical vector-like cell geometry in the original display
space. `propose(image, display_bbox, snapshot)` returns the existing native
baseline plus the raster-rule assembly, with literal text and exact source
ownership validated by the existing assembly validator. The augmented state has
`mechanism="raster_rules"`; callers must retain that provenance and force a
semantic gate or compare it with alternatives. It must not inherit native-vector
fast-path acceptance merely because its geometry uses the vector schema.

The method finds long dark contiguous horizontal/vertical runs, collapses thin
stroke bands, forms intersection-connected components, requires complete outer
edges and rejects attached rules extending outside the proposed grid. Missing
internal dividers can merge rectangular cells; nonrectangular merged components
reject the grid. A lone rectangle has no internal partition and is not proposed.
Existing native grids retain priority over overlapping raster additions.
Admission is 2**22 image pixels, 512 rules and 4096 table slots. Images must
correspond exactly to their declared display crop. Rule coordinates and source
IDs are never translated or renumbered.

Screening all 16 pages at maximum image edge 1400 proposes five grids with zero
processing errors. Four match reference geometry at IoU >=0.5 and four match
matrix shapes; three have exact cell/span topology. The proposals align 143
structure cells and **106/2333 strict literal text cells**. Strict complete tables
remain **0/53**, so this is partial recovery, not an end-to-end quality claim.
One proposed 2x1 box on an academic page does not match a reference table and
requires semantic rejection. All four negative pages produce no raster grids.
The result repeats in a separate confirmation and a bounded resource run.

The Cambridge proposal correctly keeps seven text lines inside each of two
cells. One cell is exact; the other differs only at German `Fuβ` in the official
reference versus `Fuß` in OCR. The source screenshot visibly shows `Fuß`.
This is a suspected annotation-character issue, preserved as a strict mismatch.
The supplied source screenshot is
`/home/dan/code/oss/pylopdf/.scratch/pipeline-p002/natural-example.png`; the frozen
page is `pda95432063a8a20bbe01`, whose PDF path/hash and annotation provenance are
retained in the frozen manifest/reference files. No correction was applied to
those files. A separate 9x9 raster grid recovers 79/81 literal cells and exact
physical topology, demonstrating useful evidence despite zero complete tables.

## Verification, resources and next alternatives

51 relevant Python tests pass, including twelve raster checks for 1x2, 2x1,
multiline ownership, multiple separated grids, rectangular merged cells, rejection
of nonrectangular missing dividers, open-grid rejection, underline/axes/rectangle/
filled-bar/diagonal controls, existing native priority, and admission refusal.
Ruff and targeted mypy pass. Pure line art forming a complete subdivided rectangle
remains geometrically ambiguous and must be gated semantically.

The source/candidate audit took 3.714 wall / 3.591 CPU seconds, including cached
source reads, proposals, offline scoring and report writes. Raster screening took
2.800 wall / 3.143 CPU seconds; confirmation took 2.949 / 3.213 seconds. The
bounded resource run with `RAYON_NUM_THREADS=4` took 2.020 wall / 2.445 CPU seconds,
with **236101632 bytes sampled peak RSS**, sampled every 100 ms using
`psutil.Process`, one process with a sampler thread and no worker subprocesses.
Timing uses `perf_counter` and `process_time`. The retained `getrusage(SELF)` peak
was 489980 KiB; sampled active-process RSS is the more useful operation-specific
memory observation. These runs include PDF rendering, rule detection, composition,
scoring and output writes; shared-host variation prevents a performance-win claim.

The most useful next source-only alternatives are physical raster cells alongside
logical schema rows, record-anchor continuation hypotheses for sparse wrapped
rows, and bounded header-span hypotheses informed by retained word extents.
Raster recovery supports the first. Pixel skew, broken/faint/color rules and
partial-border tables remain unsupported by this minimal candidate. No accepted
method here repairs recognition errors or supplies missing symbols. Root's
source-ID generative fallback can explore topology beyond this candidate pool,
but must still abstain when the literal source cannot support the requested cells.
