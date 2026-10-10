# Independent geometry-diagram selector runner

`bench.p003_geometry_diagram_run` is a root-only hosted adapter for the frozen
`geometry-diagram-v2` pool. Each arm declares exactly one OpenRouter model
(PPLX, Luna Decisions or Clef Omni), filled/outline rendering and edge
128/400/512. Transport capacity defaults to three; one is also admitted.
No model fallback, replay, inline retry or Gateway transport is available.

The image contains only neutral rectangles from retained source-word boxes.
It supplies neither original PDF pixels nor word glyphs. Candidate strings are
retained transcription outputs, so outputs are **not source-conserved**.
Instructions explicitly describe this limitation. The notice changes both the
state and instructions; this is not a pure pixel-only causal control.

Preparation requires externally supplied trusted code maps for the diagram
pool, historical selector, source baseline and each of the two generation
baselines. It authenticates original frozen/report/code identities, reruns the
pure preparer with current independently authenticated helpers, and checks the
complete frozen contract, all page inventories, diagrams, sources and request
bytes. Archived code is never executed. The approved historical Sonnet parser
compatibility is the same explicit error-message-only digest used by the pool.

Every selected request, its compact native wire bytes, image and source are
frozen before client construction. `frozen.json` archives code hashes, all
artifact hashes, full 16 records, source manifest identity, external authority
paths, complete pool and copied historical baselines/selector. Historical
costs/errors remain in those immutable archives and are excluded from fresh
selection accounting. The output directory must be new.

```sh
python -m bench.p003_geometry_diagram_run \
  --pool <geometry-diagram-v2> \
  --pool-trusted-code <geometry-diagram-v2.json> \
  --selector-trusted-code <choice-pplx-128-rgb-r2-c6.json> \
  --source-trusted-code <b773d57.json> \
  --input-trusted-code <screen-crops-luna-1024-pinned-r0.json> \
  --input-trusted-code <p002-sonnet1024.json> \
  --model perplexity/pplx-decider-v1.1-27b \
  --mode filled --image-edge 128 --transport-concurrency 3 \
  --output <fresh-output> --run-hosted
```

Omitting `--run-hosted` prepares only, constructs no client and reports no
throughput. Root alone may launch paid execution. The first transport failure
stops all remaining calls without further reservations. Malformed returned
answers are archived and allow the next distinct crop question to proceed.
Typed choices require the complete menu, finite raw probabilities, existing
rounding tolerance and raw maximum choice; there is no confidence gate.

Selection retains exact canonical bytes of one complete candidate. Duplicate
pools, question refusals, abstentions and errors contribute zero tables for
that crop. Independently selected disjoint complete crops remain in partial
page predictions, with operational status `error` and
`selection_status=selected_partial_crops`. Conflicting positive table boxes
cause atomic rejection of the positive composition, with no arbitrary winner.
Complete coverage is `ok/selected_complete_crops`; crop-free pages are
`ok/no_detector_crops` with zero model credit. An original baseline failure is
`error/not_applicable_baseline_failure`, with no rescue or baseline output.

Each crop has request/wire/response/result artifacts. Each page has state,
structure, Markdown and result artifacts. Results expose `selection_status`,
`crop_count`, `selected_decision_crop_count`, `accepted_crop_count`,
`complete_crop_coverage`, receipts and exact chosen candidate hashes. Independent
quality scoring must include retained partial-page tables over all 16 pages,
not discard them merely because operational status is `error`.

`report.incremental_selection` contains measured execution CPU/wall/RSS,
all prefix ledger attempts and charges, and explicitly incremental intended
and operationally complete pages/minute and pages/dollar. Full pipeline rates
are undefined. Acquisition, candidate generation and historical selection are
excluded. Missing attempted ledger entries make cost unknown. Preparation has
separate `frozen.preparation_resources`; execution RSS uses 100 ms psutil
sampling and process CPU, while preparation RSS is lifetime getrusage including
imports. Two crop-free pages count as operationally complete but never as
model-credited pages; both counts are explicit.

## CPU-only verification

26 helper/runner/strict selector tests passed, including exact candidate bytes,
abstention, malformed envelope/probabilities, transport short circuit, duplicate
zero credit, partial predictions, conflict rejection and four-coordinate page
viewports. Ruff passed for the new runner and tests.

The actual authenticated frozen DEV16 pool was rebuilt without references,
network or credentials. It has 19 crops, three duplicate pools and 16 prepared
native questions. A fake client selected alias A for all 16 requests: 11 pages
had complete selected crop coverage, three duplicate-only pages failed closed,
and two crop-free pages retained empty outputs. All 16 pages were saved; 25
strict tables were emitted. These are mechanical checks, not model quality.

Final ignored artifact: `p003-geometry-diagram-run-mock-v5` in the decision
worktree. Freeze SHA256:
`2d69beadee34f88ae80ec7bc91affe1e5dfce5370f0f86c1a3a6ac1bc37bff91`.
Mock report SHA256:
`2879e35b89eb74fb6c15cf2843abb135a1a61ecff9351db46768fa8c2a127170`.

Contended preparation: 2.995 s wall, 2.841 s CPU, lifetime peak RSS
539,156 KiB. Fake execution: 0.103 s wall, 0.097 s CPU, sampled RSS
51,736,576 bytes. Fake execution timing is not hosted throughput. Earlier local
mock freezes are retained separately; only v5 matches the final runner code.
