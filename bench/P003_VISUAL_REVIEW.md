# P003 DEV visual diagnostics

`bench.p003_visual_review` renders actual frozen input PDFs beside actual extracted
matrices. It is an offline CPU diagnostic and must never supply its images or
reference annotations to a model. The initial workflow accepts only the explicit
DEV `natural16` corpus and independently evaluated complete-pipeline runs. It
rejects changed verified reports, mismatched corpus identities, and any selected
page whose score differs from replay. It does not authenticate a new run: the
independent evaluator must first produce `evaluation.json`.

Input masks are **table-level**: green requires the complete matched normalized
anchor map to equal the reference; red indicates strict reference disagreement.
This can reflect missing output, literal differences, merged spans or an accepted
alternative column schema; red alone does not establish extraction failure.
Output colors are **schematic cell-level**, keyed by row, column, row span and
column span with NFC/whitespace normalization from the existing scorer. They are
not invented physical cell coordinates. A negative page has no spatial success
mask. Exact absence is printed as a page verdict. Model confidence never controls
colors. Source IDs are printed when available; model-transcribed cells explicitly
report their absent source IDs.

Each page retains its unmarked full-page `original.png`, translucent
`input-overlay.png`, complete extracted `extracted-tables.png`, and readable
`comparison.png`. The first three annotated tables also have unmarked regional
`source-table-N.png` views. `strict-differences.png` previews twelve exact
expected/actual mismatches; `differences.json` preserves every mismatch. Reasons
such as percent whitespace or reference math markup explain representation
changes without changing primary colors or assigning semantic severity.

## One bounded refresh

Run from a checkout containing the module, using the existing main environment:

```bash
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.p003_visual_review \
  --run /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/parallel-mechanisms-generalization-v3/screen-crops-luna-1024-pinned-r3-c6 \
  --corpus /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002/screens/natural16 \
  --output /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/visual-review-v1
```

The default deterministic five-page sample includes dense, partial, small exact,
larger exact and negative pages. `--ids` admits up to six unique explicit IDs.
Refresh manually after a newly completed independently verified cohort, or at a
five-minute review interval while a queue is active. This command exits after one
batch; no daemon is installed. Use the same sample IDs for matched model views.
Runs with selector or partial-crop scoring need an explicit adapter before use;
they must not be treated as complete-pipeline runs.

Batches are immutable directories named by a hash of every selected input
receipt, evaluation, frozen configuration, corpus and renderer. Unchanged inputs
return the existing batch without rendering. Incomplete batches are left intact
for diagnosis rather than overwritten. Output grids exceeding 12,000 pixels in
height fail explicitly. Raw diagnostics remain ignored under
`bench/results/pdf-master-artifacts/pipeline-p003/visual-review-v1/`.

`provenance.json` records exact receipts, scorer counts and local CPU wall/time
and process-lifetime peak RSS via `resource.getrusage`. Scope is one CPU renderer,
no subprocesses, concurrency one, eight logical CPUs on the first machine.
Utilization sampling is explicitly unmeasured. The five-page font-corrected
refresh measured 6.55s wall, 6.41s CPU and 585.2 MiB process peak RSS. These are
local compositing resources, unrelated to hosted inference throughput/cost.

## First observed DEV outcomes

The reviewed run was `screen-crops-luna-1024-pinned-r3-c6`: GPT-6-Luna,
YOLO detector edge 1536, transcription crop edge 1024, complete pipeline.
The final diagnostic batch is `7f477a741e042a9e298d` under the ignored root above.

| Page ID | Exact cells | Complete tables | Observed issue |
| --- | ---: | ---: | --- |
| `p1bfa52a41a5e15015698` | 0/1036 | 0/26 | Dense newspaper: every annotated table missed |
| `p6ef5d3c5c2edb1c109c4` | 58/66 | 0/2 | Seven percent-spacing differences; reference LaTeX versus literal Unicode subscript |
| `p1e230b0fd05df7dd5e23` | 4/4 | 1/1 | Small exact table |
| `pe87ca2d41151f28dc44c` | 81/81 | 1/1 | Larger exact table |
| `p27ec5aaca0dd08c90360` | 0/0 | 0/0 | Correct negative page with empty output |

The initial preview font could not display the extracted Unicode subscript.
That was a visualization defect, not lost model content; the final batch uses
Noto Sans for English/math and Noto Sans CJK for CJK. Earlier batches are retained
for provenance. Strict scorer tests pin merged topology, NFC equivalence,
percent spacing, subscripts, and unmatched predictions. Full model comparison
and a new current-queue refresh await independently verified complete runs.

## Current acquisition refresh

The first six independently verified acquisition arms have matched five-page
refreshes. Every current caption distinguishes actual detector inference size
640/1024/1280 from detector input raster edge 1536 and transcription crop 1024.
Font files, their SHA-256 digests, Pillow version and explicit renderer settings
participate in batch identity and retained provenance. Negative verdict labels
occupy their own line. `regional-TN.png` places a larger real annotated table
crop beside its matched extracted table, retaining the original prediction ID.
An extra predicted table has a red outline at its retained bbox; no box is
invented for missing cells. Exact differences also retain extra prediction cells.

| Verified acquisition arm | Immutable batch |
| --- | --- |
| Sonnet detector 640 | `31d909a4fca94ac578f5` |
| Sonnet detector 1024 | `df68e524b590fcc84c29` |
| Luna detector 1280 | `67df203e767cdb9a95a7` |
| Ministral14 detector 640 | `dbdaee345922942646cc` |
| Ministral14 detector 1280 | `1d311613ed5f6bcc948a` |
| Gemma31 detector 640 | `d4d096e72e04bb64b8cc` |

For dense-page inline review use each batch's
`p1bfa52a41a5e15015698/regional-T0.png` as well as its full original. Sonnet 640
misses all 26 newspaper tables; Sonnet 1024 returns five tables with 71/1036
strict exact cells, 22 missing tables and one extra table. Its matched first
region has four columns where the gold has three: the output separates the
ranking number from the team name. These visible cells are mostly red because
anchor positions differ, even where literal source information is retained.
Neither treatment yields a complete newspaper table.

## Coordinator-driven reporting

The reused reporter follows
`/home/dan/.agents/skills/progress-reporter/SKILL.md`. It does not schedule paid
work or change concurrency. One metadata-only checkpoint is produced with:

```bash
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.p003_progress_checkpoint \
  --status /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/parallel-acquisition-aux32-v1/status.json \
  --status /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/parallel-synthetic48-v2/status.json \
  --ledger /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/decisions/ledger.json \
  --output /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/progress-reports \
  --planned shared56=56
```

The reporter retains timestamped JSON/Markdown snapshots and `latest.md/html`.
It reads queue/ledger metadata only, hashes the read files and records their own
file timestamps using the open descriptor. It does not read raw request bodies
or credentials. Completed jobs, running jobs, queued declarations and
operational page outcomes stay separate from strict scoring. Evaluation-file
presence is explicitly weaker than independent freshness verification. Planned
queues without launch telemetry remain unknown rather than fabricated zeros.

Ledger accounted amounts are grouped by their retained reported, catalog
estimate or reservation status. A missing/non-finite charge prevents a complete
budget remainder. The USD 44.9319455668 conservative prior baseline stays
separate. Reporting model cost is unknown in available telemetry. Local reporter
CPU/RSS is retained separately from the workers' psutil 100 ms process-tree
measurements. A generated checkpoint is not user publication: coordinator last
publication remains unknown until confirmed, and the coordinator must publish
within five minutes or immediately on a material change. No autonomous timer or
post-session reporting is promised.

Repeated `--status` reads all active/completed queues in one checkpoint. Starting
jobs remain explicit. Synthetic relation question counters stay separate from PDF
page outcomes. Unknown cost bases suppress reliable budget remainders; known
subtotals and exposed conservative ledger placeholders remain separate. The fixed
prior baseline cites the root-authorized cumulative snapshot preserved in AGENTS.

## Accepted alternative newspaper column granularity

The user accepts either three columns (rank and team together) or four columns
(rank and team separately) for newspaper table T0. Sonnet detector1024 prediction
T1 preserves every ordered lexical token in all 21 rows, including the header,
under the single fixed prediction-column partition `[[0, 1], [2], [3]]`.
Letter runs, digit runs and punctuation are retained separately: `1 23` cannot
match `12 3`. This descriptive audit does not change the original strict score
and is separate from the root-owned versioned business-schema metric.

New immutable batch `18ef578699bf7fb67f49` labels this accepted alternative
granularity and strict reference disagreement. The readable image is
`p1bfa52a41a5e15015698/regional-T0.png`; original inputs and older batches remain
intact. `column-partition-audit.json` records the exact fixed partition and scope.

## Matched official TATR postprocessing

`bench.p003_tatr_visual_review` is a separate offline adapter for the independently
scored official postprocessor and the retained max-overlap baseline. It verifies
both report chains, source manifest, geometry report, placement report, selected
payload hashes and PDFs. Every structural match and strict exact cell count is
replayed before rendering. Both arms must own the exact same source words.

```bash
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.p003_tatr_visual_review \
  --official /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/official-tatr-postprocess-v1 \
  --corpus /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002/screens/natural16 \
  --output /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/visual-review-v1
```

Immutable batch `498697573be17b8ccc04` retains original full PDFs, both actual
matrices, paired regional views, exact difference transcripts and retained source
IDs. Detector inference size is 1280 and object threshold is 0.5 for both arms;
these are CPU postprocessing comparisons with zero new inference calls. Across
all 16 DEV pages the independent strict count is 438 baseline versus 569 official.
This is bounded postprocessing evidence, not a complete-pipeline improvement.

| Displayed page | Baseline strict cells | Official strict cells | Reference cells |
| --- | ---: | ---: | ---: |
| Academic `p6ef5d3c5c2edb1c109c4` | 0 | 56 | 66 |
| Dense newspaper `p98d10ef50dee4b24506a` | 119 | 191 | 936 |
| Chinese form `pf012d6adb9592dab9a13` | 12 | 3 | 22 |

The academic view visibly restores the variable/description boundary; it still
omits the final reference row and retains a reference math-markup difference.
The dense example preserves more date tokens in the intended month column,
while many literal spacing/text differences and unmatched tables remain. The
Chinese form changes from seven columns to two and loses strict matches; that
count alone does not establish that the alternative schema is wrong. Inspect
the actual values, source and exact differences rather than treating every red
cell as a semantic error.

`matched-regional-T0.png` is the readable paired comparison for each displayed
page. `matched-comparison.png` includes the full input and both full output grids.
Each arm's separate `source-word-projections.png` overlays only the retained
**approximate uniform-character OCR whitespace projections**, explicitly labelled
as neither physical cells nor recognized word boxes. Colors follow exact
cell-owned source IDs; conflicting ownership and unassigned words remain amber.
No physical cell boxes are inferred. This three-page refresh measured 19.69s wall,
19.42s CPU and 613,646,336 bytes process-lifetime peak RSS, single renderer,
concurrency one; sampled utilization is unmeasured.

## Dense Luna resolution comparison and pagination

A further matched refresh keeps the five fixed pages and adds the explicitly
labelled dense DEV newspaper `p98d10ef50dee4b24506a` for qualitative coverage.
It is not a new benchmark denominator or configuration selection. Luna640 and
Luna1280 both return no tables on this page (0/936 strict cells); Luna1024 retains
19 actual tables and 533/936 strict cells. The independent evaluator identifies
this page as the principal concentration of Luna1024's all-DEV strict gain.

Current immutable batches are `ef70401cee3c21c4e9b5` (640),
`93cd4f3a528d657b0c8c` (1024), and `e02b93d7cbcb10b31f4b` (1280). The readable
Luna1024 example is `p98d10ef50dee4b24506a/regional-T0.png`.
`original.png` always retains the full actual input, including pages with no output.

Large concatenated output grids are now paginated at whole-table boundaries;
every matrix keeps its original prediction index and exact verdict map.
`output-pages.json` records coverage, and `extracted-tables-page-N.png` retains
every output page. The overview states which page it shows. A single matrix
exceeding the canvas limit still fails explicitly. The initially incomplete
Luna1024 batch remains intact. Actual font-width wrapping replaces conservative
character counts, keeping intact prices such as `540.50` on one line when they
fit. This changes rendering only, retaining actual strings and primary scores.

## Retained detector metadata and Haiku refresh

Some legacy frozen configurations omit the detector inference-size field. The
caption now first uses the verified report's actual worker
`layout_detector_initialization.configuration.imgsz`, then a frozen declaration
when no worker value exists. Conflicting declarations fail explicitly. The
Haiku640 worker records 640; no caption infers this from the run name or the
1536-pixel detector raster.

The same six-page Haiku matrix cohorts are retained in `5f42775567ab2a8dcc62`
(640), `394051b62188b30ef85d` (1024), and `184543d37787446facb9` (1280).
On added dense page p98 the strict counts are 123, 0 and 0. Haiku1024 records
`Invalid merged span bounds` and zero returned tables there. Its 22 strict cells
in the analysis's **dense2 sum** belong to the other newspaper p1b, not p98.
Generation error outcomes receive zero credit in this complete-pipeline scope;
explicit diagram selected-crop scoring is a separate scope.

A font-measured matched TATR refresh is retained in `35f004fede3a408bc58d` with
the same three actual input IDs and unchanged independently verified scores.

The reporter also accepts `--coordinator-metadata <ignored-receipt.json>` to
retain explicitly supplied publication time/precision, next deadline and service
observations. These are labelled coordinator-supplied rather than independently
verified service telemetry. An active launch wrapper does not imply that shared
question jobs have begun; planned queue cells remain `Job status not observed`
until the actual queue status exists. Root's 00:24:33 UTC systemd observation is
retained in ignored `progress-reports/coordinator-20261011T002433Z.json`; the
reported prior publication is approximately 00:24 UTC, with deadline 00:29 UTC.

For synthetic queues, the reporter reads the retained per-arm
`synthetic-alias-evaluation.json` metadata rather than treating absence of a
PDF `evaluation.json` as absence of an audit. Original independent verification
and secondary catalog-alias replay are counted separately, with each receipt's
hash, timestamp and recorded scope. These are evaluator-recorded verification
counts; the reporter does not rerun scoring or replace original strict outcomes.
Waiting launch wrappers remain distinct from observed queue jobs.

Shared-context arms use their separate
`synthetic-shared-alias-evaluation.json` receipts. Their recorded scope covers
24 relation questions (18 visually cued and six indeterminate) in shared context
groups of four or eight. These receipts do not certify table or full-page
extraction quality. The original identifier-failed protocol remains separate
from secondary replay of an independently attested returned model identifier.

## Source-only transparency check

`bench.p003_source_visual_check` reads only manifest source paths/families and
actual PDFs/PNGs; it does not load reference tables or model outcomes. Two random40
frozen previews contained all-zero RGB channels with ink encoded in alpha above
an otherwise transparent background. Discarding alpha or viewing against black
makes them appear entirely black. The saved files remain unchanged.

Diagnostic batch `e31a42a4f380a709a633` includes the actual PDFs rendered at1800px
width onto explicit opaque white, exact original512px PNG composites over white,
and `source-contact-sheet.png` for source IDs `r4fa2f36b57caf506679ba995` and
`r536e002b19beb540f99f33e9`. Direct image review confirmed readable English words,
USD values, parenthesized negatives, dates, a wrapped label and two separate
column tables. No expected values or quality colors were introduced.

```bash
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.p003_source_visual_check \
  --corpus /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/random-office-values40-v1 \
  --output /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/visual-review-v1 \
  --ids r4fa2f36b57caf506679ba995 r536e002b19beb540f99f33e9
```

The bounded source check admits one through six explicit IDs and retains PDF,
PNG, manifest, renderer and font hashes. It checks every dependency again before
recording successful provenance. The actual detector and transcription renderer
in `generalization_vision_regions.py` already passes an explicit white background;
this inspection required no pipeline-helper change.

## Pinned strict and secondary newspaper comparison

`bench.p003_secondary_visual_review` adds a separate immutable view from the
pinned `scoring-audit26-v1` declaration and per-arm audit. It checks the declaration,
original report/evaluation/frozen corpus/targets/PDF hashes, replays the strict
page through the original visual renderer, and records the trusted runtime
receipt, renderer/font hashes, wall/CPU time and lifetime peak RSS. Source pixels
are actual PDF renders over white; output cells retain strict colors and their
actual values. No original batch is changed.

For Sonnet detector 1024 target 0/prediction 1 on newspaper
`p1bfa52a41a5e15015698`, all 21 rows including the header satisfy accepted 3/4-column
schema equivalence under fixed partition `[[0,1],[2],[3]]`. Character evidence has
393 equal, zero missing/substituted and eight extra characters; all eight extras
are literal spaces. This explains content recall 1 and precision 0.98005 without
calling the table semantically wrong. A separate exact witness image exposes
quoted expected/actual strings and every changed character.

Target 8/prediction 3 is an actual partial-content control: source review confirms
missing Motor City and incorrect Grand Rapids values. The retained character
metric also counts removed dot leaders and punctuation differences, so its
242 equal/142 missing/17 substituted/one extra characters must not all be
interpreted as lost business values. Its schema equivalence is false; content
recall 0.60349 and precision 0.93077 remain representation metrics. Merged target 2
is unsupported by this adapter and receives no fabricated secondary labels.

A separate `accepted-schema-T0.png` uses green output cells and a whole-table
source outline with the explicit legend “accepted alternative schema (not strict
reference coordinates).” Green here represents the independently verified
whole-table schema equivalence, not original coordinate-wise strict matching.
The strict red comparison and every older batch remain separate and unchanged.
`partial-content-control-T8.png` visibly separates missing/altered business values
from dot leaders and fraction encodings that also contribute to character counts.
