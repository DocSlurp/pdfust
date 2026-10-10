# P003 decision-model research contract

Start: 2026-10-10 18:27 UTC. Finish: 2026-10-11 02:27 UTC. New paid admissions
stop at 02:12 UTC independently in the shared client. Additional authorization:
USD 50; cumulative ceiling USD 200. Starting conservative cumulative accounting
is USD 44.9319455668, including prior unresolved reservations. Root alone runs
paid requests. No GPU rentals are planned initially; local work remains CPU-only.

## Questions and predeclared measurements

The previous synthetic success does not imply natural-document success. Focus
on all sixteen previously frozen natural DEV screening pages, including four
negatives and both dense pages. Broaden frozen finalists to all 64 natural DEV
pages and then the 276-page corpus when time permits. Protected silver stays
untouched. Reference annotations are loaded only by independent scoring, never
candidate generation, prompts, region selection or model routing.

Report every attempt, operational output, exact complete table, exact text cell,
strict topology, extra/missing table and negative-page false positive. Report
operational and attempted pages/minute and pages/API USD distinctly; keep API
cost separate from local compute and reservations. Measure parent CPU and RSS
at 100 ms, separate detector worker measurements, concurrency and initialization.
Local GPU use is false; remote hardware utilization is unmeasured.

Primary improvement: more fully correct natural tables and exact cells without
more failed or false-positive pages. A screen gain of at least one complete table
or 5% exact cells earns further investigation, not acceptance. Preserve interesting
tradeoffs and modest results for further exploration. No production promotion
from a single run. Select up to three finalists and run three fresh paired blocks
with alternating arm order before broader DEV measurement. Keep all repeat rows
and ranges; no significance claim from three small blocks. Stochastic transcript
variation must not be credited to unchanged geometry or deterministic assembly.

## Initial breadth

1. Reproduce the strongest source-owned evidence bundle: OCR300, compact arrays,
   ordinal cells and column-track instructions. Add gate-only rolling row context
   as a matched arm; this combination was deferred from P002.
2. Screen available image decision models on the identical region-gating task,
   preserving downstream Haiku assembly. Include previously moderate models and
   newly cataloged routes. Explicitly test text-only evidence for text-only routes.
3. Replace large table generation with bounded local row-boundary decisions.
   Decode split/join/unresolved answers under global ownership and geometry
   constraints. Test image support separately from text/geometry evidence.
4. Generate additional generic source-only region candidates when whole-page
   detection misses dense structure, then ask decision models to admit them.
   Detection coverage and extraction quality remain separate outcomes.
5. Compare economical multimodal chat models on unchanged crops as transcription
   controls. This tests the missing-source-text ceiling separately from placement.
6. Ablate prompt/context/image size and combine compatible improvements only
   after their individual effects are measured. Minimal geometry-only/no-model
   arms remain controls. Provider cache usage uses reported tokens only; local
   response reuse is an offline audit, never a fresh inference performance claim.

Review results after each layer and record reprioritization, including unrun
hypotheses. Raw snapshots, requests, responses and reports stay ignored under
`bench/results/pdf-master-artifacts/pipeline-p003/`; the shared financial ledger
remains `bench/results/pdf-master-artifacts/decisions/ledger.json`. Every paid tag
starts `P003/`. Preserve failed transmissions and unresolved reservations.

## Execution and provenance

`python -m bench.p003_run --manifest <DEV manifest> --output <new directory>
--preset ordinal|gated_ordinal|hybrid|vision_regions` uses the existing frozen
pipeline output contract. The runner records exact source hashes, source code,
runtime, configuration and per-page outputs before independent scoring. Gate
models and generation models are distinct fields. `--gate-row-evidence` changes
only gate evidence; `--image-edge` and `--ocr-dpi` are independent controls.
The unchanged strict validators retain page failures rather than repairing them
silently. Additional decision mechanisms get separate treatment identities.
