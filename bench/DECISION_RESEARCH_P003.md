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

## First re-evaluation, 18:55 UTC

Adding the PPLX gate plus rolling context to the OCR300 evidence bundle ties the
ungated baseline at three complete tables, 397 exact text anchors and 384 strict
span-aware anchors. It costs 19.06% more in this first fresh pair and measures
6.63% lower throughput. Identical source/detector fingerprints and image asset
sets rule out changed acquisition; individual page outputs still vary. This
combined gate treatment has no measured aggregate quality gain yet. Preserve
the comparison and continue other models rather than promoting this combination.

The next serial batch compares eight pinned transcription routes on the same
ordinary detector crops. Then run the broader typed-model gate screen, including
text-only alternatives and Gateway d1/Laya, with explicit route capability checks.
Additional acquisition and candidate reranking earn priority because decisions
cannot recover omitted regions or literal strings absent from their evidence.
Local row repair remains an incremental diagnostic on retained baseline states;
its rates must not be presented as newly measured end-to-end pipeline throughput.

## Second re-evaluation, 19:35 UTC

Eight transcription routes completed screening. Luna leads these new runs on
strict anchors (784), but the older authenticated matched-pixel Sonnet result
remains stronger (982 and five complete tables). Qwen HTTP 429 and Gemini HTTP 400
are availability/request failures, not quality rankings. Strict matrix and
atomic-cell representations merit fresh tests because malformed output remains
common among small models. Preserve all failed pages and their costs.

Whole-crop oracle ceilings favor testing the Luna/Sonnet candidate pool (1,088
strict anchors) over Luna/Haiku (796). Adding Haiku raises the ceiling to 1,097;
none of these pools exceeds five complete tables. Therefore region acquisition
and missing literal evidence remain first-class experiments alongside reranking.
Oracle scores use DEV labels only after candidates are frozen; they are not
routing inputs or achieved model-selected performance.

Thirteen gate arms use up to three concurrent root-controlled OpenRouter
requests, with one CPU worker per arm and measured contention. An initial queue
failed at CLI parsing because of an unsupported worker argument; no paid request
occurred. The corrected queue has a real parser integration test. Gateway arms
remain serial and do not overlap this queue. No automatic retry changes a failed
provider route into a successful run.

## P003 re-evaluation, 2026-10-10 19:55 UTC

Five additional gate arms produce 181 (Tev), 304 (d1), 124 (Solar timeout), 0 (Solar Flash), and 352 (Clef) strict anchors against the same 2,333-anchor denominator. None beats the 384 source-ID control. Queue SIGKILL interruptions have unconfirmed cause; completed artifacts remain independently verified and partial results are not scored as complete runs. Subsequent queues use a bounded monitored systemd user service.

A 29-arm incremental batch now tests whole-crop candidate choice and bounded boundary repair. Next prioritize the bounded YOLO/fixed-grid proposal union: offline coverage expands from 26 to 39 tables, but this is an opportunity, not achieved quality. Source inventory remains a ceiling on ownership-only techniques. Gate image/prompt loops will hold transcription fixed to isolate their effects.

The earlier best Sonnet crop result of 982 strict anchors is unstable: same-request repeats reached 289 and 287 due to dense-page atomic failures. Publish repeat variability and preserve strict admission. No new setting is a production recommendation.

## P003 decision roles and spatial assignment, 2026-10-10 20:07 UTC

The complete 29-arm incremental screen is independently scored. PPLX with 512 px images whole-crop selection recovers 981 strict anchors and 5 complete tables, versus 784/3 for the frozen Luna fallback and 784/3 for text-only PPLX. Incremental selector rates of 20.24 pages/min and 26,055 pages/API USD exclude BOTH candidate-generation costs. No other selector beats frozen Luna; no boundary repair arm beats its 384-anchor baseline. Clef Flash HTTP 429 attempts retain unknown charges and reservations. See `bench/results/p003-incremental-screen.md` for every arm.

Spatial ownership now directly assigns retained source strings to frozen rows/cells, with source conservation. Strict crop-boundary handling admits 7/16 pages; preserving straddling whole words in their original residual regions admits 9/16. An actual-data CPU geometry control exposed a residual-source ordering bug in composition. The minimal fix preserves exact source-ID order; prior paid runs retain their original failures, with a separately labeled exact-body offline replay planned. No identical model calls need to be repurchased for that postprocessing correction.

Removing large numeric/array/string bounds from the Gemini wire schema allows 15/16 outputs (287 strict anchors, 3 complete tables, 9.09 pages/min, 345.24 pages/API USD), where the original request returned HTTP 400. Types and closed objects and strict local parsing remain unchanged. This supports the schema-complexity hypothesis; it is not a controlled availability repeat. Fresh Sonnet crops recover 289 anchors and 4 complete tables, with one dense overlap failure.

An explicit offline partial-table contract retains only individually valid literal tables and discards every member of an overlap conflict. No clipping, ragged padding, invented values, or truncated-JSON salvage. On new screens it raises Haiku 393→403 anchors (3→4 complete tables), Gemma 31 264→265, Ministral 8 252→296, and fresh Sonnet 289→570. Original page failures remain failures; fragment scores and resources are separate, with no fresh inference rates.

## P003 spatial evidence and next layer, 2026-10-10 20:30 UTC

The complete nine-arm spatial queue finished. Independently verified full-pipeline treatments recover 452 strict anchors with Haiku matrix instructions, 289 with fresh Sonnet, 287 with Gemini simplified wire schema, 270 with probability-ranked union proposals, and 138 with smaller-region-first union proposals. All retain the 2,333-anchor / 53-table / 16-page denominator. More source proposals expand detection opportunity but these two overlap policies do not translate it into quality. Full scores, costs, throughput, CPU and RSS are in `bench/results/p003-spatial-screen.md`.

Independent no-new-inference controls establish 276 strict anchors / 1 complete table for uniform spatial placement, 328 / 2 for source-derived bands, 280 / 1 for corrected PPLX ownership receipts, and 232 / 0 for corrected Luna Decisions receipts. Every string remains uniquely owned or explicitly unresolved. All fall below the original ordinal 384 / 3; fixing composition does not establish a model benefit. The restricted row-boundary oracle likewise proves no gain is possible within its legal 1–3-row merge language on these frozen states; see `bench/results/p003-boundary-ceiling.md`.

Chunked local evidence removes the remaining whole-crop inventory exclusions: all 11 pages with model topology now admit preparation, with five pages explicitly not applicable and at most 280 fresh ownership calls. Complete source words stay local; each question batch includes all whole targets and complete row menus for geometrically intersecting tables, plus separately selectable nearby words or source-band hints. Crossed generated baseline tables may become explicitly logged residual prose only in that opt-in treatment. Native grids remain protected. Next compare compact/neighbor/band evidence and geometry-first decisions only on disputed assignments.

The 57-arm mixed queue starts two new 64-page DEV baselines alongside frozen-generation gates and candidate selectors. It crosses PPLX selector images at 128/256/400/512/768/1024/1200 px with RGB JPEG, same-pixel RGB PNG, grayscale8 PNG, and 16-color palette PNG; separately tests difference-only candidate evidence across five decision models and a 20-arm gate prompt/model screen. The randomized order is conditioned only on starting the two longer 64-page baselines among the first three arms (seed 194), not on scores. Palette indices are 4 bit, not 4-bit RGB channels.

First independently verified selector results: 128 px palette achieves 1,086 strict anchors / 4 complete tables at 22.04 incremental artifact pages/min and 26,746 pages/API USD; 400 px palette gives 1,081 / 5 at 25.99 and 26,562. Each is a single DEV run using the same frozen Luna/Sonnet pool; both generation costs are excluded from those rates. Repeats and matched encoding controls are required before attributing the gain to image reduction.

Gateway d1 image and Laya text stop on their first actual requests (HTTP 400 and 422 respectively); each has two bypass-only operational pages, fourteen circuit-related failures, no returned decisions, unknown charges and a retained USD 0.30 reservation. Their schema/availability diagnosis is separate from quality. A bounded diagnostic change now stores fixed reason categories without provider messages or echoed source data; categories are hints, not established causes.

## P003 broader corpus and spatial mechanisms, 2026-10-10 21:10 UTC

Fresh natural64 baselines retain 64 intended pages, 93 tables and 3,847 cell anchors. Luna returns 63 usable pages, 1,348 strict anchors, 1,358 text anchors, 1,731 structure anchors and 12 complete tables, with zero extra tables and zero negative-page false positives. Ordinal OCR300 returns 62 usable pages, 1,309 strict anchors, 1,329 text anchors, 1,806 structure anchors and 11 complete tables, with 11 extra tables but zero negative-page false positives. Full-generation rates are 5.54 pages/min and 1,985.15 pages/API USD for Luna; 2.69 and 1,013.32 for ordinal, under concurrent load. This broader DEV set includes the original 16 pages and is not held out.

Two ordinal errors are the existing 64-million-pixel raster admission at fixed DPI. The next queue explicitly tests the existing fixed-edge OCR acquisition at 2,048 and 3,072 px. No admission limit is relaxed; old failures remain recorded. A separate offline partial-table audit on natural64 Luna raises strict fragments from 1,348 to 1,828 but adds four extra tables and leaves complete-table count at twelve. Its original failed page remains an operational failure. It has no fresh API rate or cost claim.

The source-only pair-relation prototype conserves word IDs and rejects conflicting or missing pair evidence during complete-link partitioning. Atomic coverage needs 7,508 question batches, making segment compression and uncertainty subgraphs more practical next steps than immediate paid exhaustive inference. A separate CPU Table Transformer experiment now explores explicit row/column geometry conditional on existing detector crops.

The source-frozen valid-region candidate adapter excludes malformed whole crops while admitting valid crops from otherwise failed pages. Independent DEV oracles find no gain from adding fresh Sonnet to the original Luna/Sonnet pool: both remain 1,088 strict anchors and five complete tables. This preserves a useful general admission mechanism without claiming a quality improvement. Investigate compatible row combinations and geometry rather than repurchasing equivalent crop decisions.

Render reuse preserves all 266 crop/image comparisons exactly and reduces local rendering CPU by 6.09–6.18 times in two contended paired passes. It is a separate prototype, not an implicit change to active image experiments. Provider cache usage reporting now separates original retained transcript counters from zero new replay calls and correctly reads nested result usage.

The next predeclared queue contains 62 arms: two complete 276-page baselines; three stronger-model natural64 baselines; fixed-edge OCR; direct-cell versus row-then-anchor decisions; compact, neighbor and band evidence; ambiguity-only placement; small-image repeats, blank/blur controls, opaque candidate order/alias seeds, 500 px controls; and matrix/atomic transcription formats. Plan SHA256 cb78a6179c038254fdaa82dd3ffbbaf3e3503dd6d3c1ab5059498f5f40b1a8a7, seed 194. Six active arms may overlap, with at most three pipeline/candidate workers and three paid transports. Real process and shared-ledger tests pass; waiting reserves no money. All rates must state this contention policy. The USD 50 wave cap and 02:12 UTC paid cutoff remain unchanged.
