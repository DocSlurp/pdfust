# P003 DEV visual diagnostics

`bench.p003_visual_review` renders actual frozen input PDFs beside actual extracted
matrices. It is an offline CPU diagnostic and must never supply its images or
reference annotations to a model. The initial workflow accepts only the explicit
DEV `natural16` corpus and independently evaluated complete-pipeline runs. It
rejects changed verified reports, mismatched corpus identities, and any selected
page whose score differs from replay. It does not authenticate a new run: the
independent evaluator must first produce `evaluation.json`.

Input masks are **table-level**: green requires the complete matched normalized
anchor map to equal the reference; red indicates an incomplete or missing table.
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
