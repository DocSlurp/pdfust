# P003 retained-state boundary repair runner

`bench/p003_boundary_run.py` repairs retained source-only natural region states
without repeating PDF extraction, OCR, detection, initial admission or matrix
generation. This branch made no provider calls. All hosted execution stays with
root's persistent `DecisionClient` and `P003/<run>/<page>/<region>/<batch>` tags.

Root can invoke the opt-in runner after merging its implementation:

```bash
.venv/bin/python -m bench.p003_boundary_run \
  --baseline <retained-natural16-region-baseline> \
  --output <new-ignored-artifact-directory> \
  --model typesafe/jev-1.13 --image-edge 0 --run-hosted
```

Image edge is independently selectable as 0, 256, 512 or 1024. Edge zero reads no
PDF. Other edges lazily open the frozen source PDF, verify its hash, restore the
baseline's effective rotation and render each eligible region with the existing
`region_image`. No page text extraction, OCR or detector is invoked. Crops retain
their global display viewport in native decision text, so the model can relate
word boxes to region pixels. Existing region admission is retained; there is no
extra table gate and repair cannot admit new tables.

Root may instead inject its coordinated client:

```python
from bench.p003_boundary_run import run

report = run(baseline_directory, new_output_directory, {
    "run_hosted": True,
    "model": "typesafe/jev-1.13",
    "image_edge": 512,
    "max_questions": 16,
    "minimum_join": 0.8,
    "minimum_margin": 0.25,
}, root_client)
```

A new output directory and unused persistent-ledger run ID are required. Native
requests always use `replay=False`; replayed provider responses are rejected.
Before every request, prior P003 accounted charges and outstanding reservations
are checked against the USD 50 wave cap plus the new USD 0.30 reservation. The
shared client separately enforces the cumulative authorized ceiling and preserves
failed-call reservations. Thresholds and question bounds are validated before
client construction or calls. No automatic retries are introduced.

## Atomic output and retained evidence

`frozen.json` preserves original source records and `manifest_sha256`. Its
`baseline` object records the original directory, relative `copied_directory`
(`baseline`), `file_sha256`, original `source_order`, and `original_config`.
Copies of original report, frozen manifest, page results, complete structures,
Markdown and authenticated baseline code remain byte-for-byte under `baseline/`.
The new runner/helper/validator code archive is separately stored under `code/`
with `code_sha256`. Independent evaluation must authenticate both archives;
artifact-supplied digest lists do not establish trust by themselves.

Each page consumes `region_plan.regions[].source` and `regions[].state` from the
retained result. Original complete state is checked against composition of all
region states before requests. Every request, complete response wrapper, menu,
updated regional state and raw-probability/confidence audit is retained. The
complete page is composed through `pipeline_regions.compose`, receives bounds
through `_table_bounds`, and renders with the original baseline source-order
policy. Region edits are staged until every region, composition and rendering
passes. A later failure discards earlier staged edits.

A failed repair retains the original complete structure, Markdown, tables,
regions, status and historical timing/calls. It explicitly records
`repair_status="failed_retained_baseline"` and `repair_errors`; effective
`status="ok"` means the original fallback remains a complete output, not that
repair succeeded. Baseline failures retain their original failure status and
`repair_status="baseline_failed_skipped"`. Pages with no eligible boundary
menus use `repair_status="not_applicable"`, never repair success.

Successful page repair uses `repair_status="completed"`; unchanged high-confidence
splits/abstentions can still represent a successfully completed decision attempt.
Per-region `repair_regions` retain `original_state`, image metadata,
`updated_state` and decoder `audit`. Staged regional work discarded by later page
failure is marked `discarded_atomic_failure`. Errors and unresolved reservations
remain visible even when no successful response wrapper exists.

Artifacts use `{page}-{region}-boundary-menu.json`,
`{page}-{region}-boundary-{batch}-request.json`, matching `-response.json`, and
`{page}-{region}-updated-state.json`. The response JSON is the full shared-client
wrapper containing `entry`, `result` and `replayed`. Original historical calls
remain in page `calls`/`baseline_provenance`; new admitted response calls are
separate `repair_calls`.

## Accounting and resource scope

`report.baseline_report` retains full original pipeline latency, resource, call
and cost provenance. `incremental_repair` records only new attempts matched by
this run's P003 ledger tags, including failed attempts and unresolved reservations.
`effective_usd` remains unknown when any reservation is unresolved; known partial
effective charges, known partial reported charges, missing reported charges and
reserved USD remain separate. Positive provider reporting and catalog estimates
continue to come from the unchanged shared client, not a second pricing path.

The resource interval starts after copying/freezing baseline and code artifacts.
It covers image rendering, request waiting, decoding, complete-page composition
and writing outputs. Freezing resources are explicitly unmeasured separately.
The existing CPU-only process monitor records `process_time` CPU and wall time,
with psutil RSS samples every 100 ms in one serial process and no worker
subprocesses. Hosted GPU resources remain unmeasured. These metrics are labeled
`incremental repair on retained artifacts`. `pages_per_minute` and
`pages_per_dollar` are `None`; incremental repair rates never become an end-to-end
PDF-pipeline throughput claim. No original baseline provider calls are repaid.

## Offline validation

Mock-client tests retain actual typed decision payloads and isolated fake ledgers.
They cover successful literal source conservation, immutable baseline copies,
separate historical/incremental accounting, failure after an earlier batch,
whole-page rollback after a completed region, original failed-page retention,
empty-menu applicability, crop viewport mapping without PDF reprocessing, opt-in
admission, changed original structure and wave reservations refusing transmission.
No tests call a provider or load credentials. Direct runner/native/boundary tests
passed: **29 tests in 0.27 seconds**, with Ruff passing. No additional CPU profiling
was run while root's natural baseline was active.
