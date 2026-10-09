# PDF-master experiment decision record

This is the versioned experiment index and current evaluation contract. The user explicitly authorized pushing the completed work to private
`justsml/pdf-master` on 2026-10-08. Public publication remains prohibited; the
no-local-GPU requirement remains active.
Financial reports, invoices/forms and scientific documents have equal priority.
Actual reconstruction quality, latency, bytes and cost lead model selection.
Confidence is an optional routing signal, not a prerequisite for useful decisions.

## Artifact and budget policy

Commit experiment code, tests, hypotheses, reviewed council proposals, compact
Markdown results and this log. Retain raw provider responses, source PDFs, rasters,
large JSON, caches and ledgers under ignored `bench/results/pdf-master-artifacts/`.
Record stable dataset/config/scorer hashes and paths with each run; never version
credentials. Generated artifacts can be reproduced from committed code and the
recorded source manifests. Existing user `mise.toml` is unrelated and remains untouched.

At the start of the council/image phase, cumulative provider/rental-reported spend
is USD 2.046954530, with USD 0.60 reserved for two unresolved HTTP 404 charges. Conservative
accounting is USD 2.646954530 of the user's USD 15 authorization. Existing per-request
reservations and native byte/question admissions remain enforced. Authored and
public/redistributable PDF evidence is authorized for the configured OpenRouter
models; proprietary business documents are outside these runs.

## Evidence status and present decision

The existing 96 authored decisions and eight region controls have been repeatedly
inspected. Their old calibration/test names are historical partition names, not
an unseen validation guarantee. Treat them as development/regression material.
Some old header/wrap labels express nonobservable author intent. None of those
results qualifies a production release or a fresh held-out claim.

The next decision: which native-evidence representation, low-resolution visual
side channel and bounded assembly-selection mechanism improves correctly
reconstructed records enough to justify its end-to-end cost? The current model
shortlist is Luna Decisions and Perplexity Decider; Jev remains a cheap reference.
No model is enabled in default extraction.

| Claim | Evaluation unit and score | Required comparison | Decision rule |
|---|---|---|---|
| Better assembly | Exact table/record match; correct source-ID cells and header/value edges; lost/duplicated/invented source IDs | Native baseline and best available candidate oracle | Prefer actual quality; a gate score alone is insufficient |
| Tiny visual signal helps | Paired outcomes on the same document/candidates | Text/native geometry; matched pixels; blank/shuffled-image controls | Benefit must beat input-format/placebo effects |
| Less image information suffices | Record quality versus image dimensions, bytes and CPU+HTTP time | Tiny gray/blurred/morphology images versus larger reference | Keep useful Pareto points, publish regressions |
| Provider caching is useful | Reported cache-read/write tokens, charges and API latency | Actual initial submission versus identical provider resubmissions | Confirm hits from provider usage; local replay is excluded |
| Generalizes | Fresh independently specified document/layout families | Candidate frozen before evaluator-only confirmation | No tuning may inspect confirmation cases or labels |

A clean confirmation set must be independently built and scored after candidate
selection. Its cases/labels must remain unavailable to optimization agents. If
that isolation fails, invalidate the confirmation claim and create a new split.
Development images and examples may be inspected freely and are labeled DEV.

## Experiment history

Rows below backfill prior work from its recorded reports, then append new work.
A hypothesis can be rejected or remain unresolved; those outcomes are retained.

| ID | Hypothesis / experiment | Result and evidence | Decision |
|---|---|---|---|
| P001 | Spatial snapshots, tiny field ranker, semantic tags, encoding and mixed-scan routing | [Prior breadth-first study](bench/results/pdf-master-findings.md); native rules beat learned ranker on 160 synthetic fields; tags rarely yielded validated corpus tables | Keep native/source evidence; learned defaults not justified |
| P002 | Repair fragmented vector borders and extend geometric cascade | [Cascade](bench/results/geometry-cascade.md); 16/16 inspected transform regressions and 35/35 corpus spot cells; [prior report](bench/results/pdf-master-findings.md) records guarded 0/8→8/8 fragmented repair | Keep narrow repair; spot checks are not full-document accuracy |
| P003 | Infer semantic header relationships from geometry | [Header study](bench/results/header-relations.md), 112 generated PDFs, 48 wrong edges | Geometry alone cannot prove author intent |
| P004 | Small SLANet specialist and faster source matching | [SLANet](bench/results/specialist-cpu.md): crops 4/4 small tables, dense spot checks 17/35, one prose false positive; [matching](bench/results/cell-matching.md) preserves output with major matching-only speedup | Retain specialist/caching candidates, not universal table reconstruction |
| D001 | Native decision probabilities versus small chat/frontier text models | [Initial pilot](bench/results/decision-findings.md), commit `225a17d`, ledger entries 0–627 | DEV results only; explicit source spans help |
| D002 | Singleton, resolved spans, geometry ablation, three-way choice | Same initial report; Jev 14 → 24/36 after resolution; batch/raw 33/96 answer differences; removing singleton geometry preserved hard answers | Keep representations distinct and preserve losses |
| D003 | Eight more exact OpenRouter decision IDs | [Catalog](bench/DECISION_CATALOG.md), [comparison](bench/results/decision-alternatives.md), ledger entries 628–1349: seven work; Span returned HTTP 404; Luna 31/36 relationships and 8/8 regions; Perplexity 30/36 and 6/8 | Shortlist Luna and Perplexity on measured quality |
| D004 | Provider-pinned Clef avoids Workers AI state truncation | PrimeIntellect control probe returned HTTP 404, one failed/seven unattempted; USD 0.30 held in reserve, separate from Span's USD 0.30 | No control-quality score; preserve availability failure |
| D005 | Route by task using calibration accuracy, no confidence gate | [Task router](bench/decision_routing.py): 36/36 calibration → 29/36 historical test, below Luna at 31/36; eight scorer tests | Reject added routing complexity on current evidence |
| C001 | Council of Dans re-evaluation | Reviewed and promoted individually: [Inventor](bench/council/2026-10-08/inventor.md), [Performance](bench/council/2026-10-08/performance.md), [Evaluation](bench/council/2026-10-08/eval-architect.md) | Presented all three; proceed with native/assembly ceiling, evidence augmentation and tiny-image tests |
| M001 | Native candidate assembly and candidate-oracle ceiling | Planned after council review; requires meaningful record/source-ID labels | Do not spend on model selection if correct assembly is absent |
| M002 | Cached tiny screenshots, blur and morphology-only side channels | Planned DEV ablations; sizes/models/call cap freeze before paid run | Measure real reconstructed output, not confidence uplift |
| M003 | Clean evaluator-only confirmation | Not started; independent cases and prompt/config freeze required | No claim until split isolation and scorer validation pass |

## Current open failures

- Dense-report cell recovery is still unsolved by a region gate.
- Existing semantic labels include ambiguities; new labels need observable evidence.
- Source conservation in the old adapter does not constitute record reconstruction.
- Span and PrimeIntellect advertised endpoints returned HTTP 404; causes unconfirmed.
- Native probability fields are not guaranteed calibrated; this is secondary to
  measured ability and should not obscure quality improvements.

## Decisions

| Date | Decision | Evidence / revisit condition |
|---|---|---|
| 2026-10-08 | Keep work local, CPU-only locally; use authorized hosted budget | User instructions; remote ledger tracks reservations and actual reported cost |
| 2026-10-08 | Use actual output quality as primary model criterion | User steering; Luna/Perplexity gains despite uncertain confidence |
| 2026-10-08 | Reclassify exposed legacy partitions as DEV | Eval-expert audit; no future tuning may access fresh confirmation data |
| 2026-10-08 | Preserve all council alternatives distinctly | Council-of-Dans contract; user authorizes subsequent experiments |

## Active evidence-repair and retrieval wave

- M004: isolated Luna and Perplexity worktrees; 30 DEV controls (ten correlated
  templates × three vocabularies) compare current/prior/context/native facts,
  raw versus observed-history summaries, complete assembly Choice and candidate
  order. Initial CPU native baseline reaches all 30: model lanes test evidence
  transport and do not establish an improvement over that native baseline.
- M005: standalone Rust connected color regions, variable RGB/luminance thresholds,
  4/8 connectivity, white interiors and vector grouping; CPU timing includes
  rasterization separately. Experiment only, no public API/default changes.
- E001: separate page-image embedding retrieval experiment requested by user.
  Search for expressions spanning lines; compare full-page and cropped imagery
  with normalized native text against near-wording, reverse-order and cross-cell
  distractors. Embedding similarity is retrieval evidence, not proof of a phrase
  or recovered cell ownership. OpenRouter catalog lists Gemini Embedding 2,
  Voyage multimodal 3.5 and Nemotron VL. Same persistent ledger/USD 15 cap applies.

First hosted evidence wave freezes two models (Luna, Perplexity), four context
projections, 64, 128, 256 and 512-pixel crop ladder with 128 px blur and blank controls,
maximum 600 new requests and USD 1 incremental accounted spend, including retained
failed-call reservations. Start with current/native and 128 px on the same 30,
then target remaining ablations at observed DEV failures. No clean confirmation
exists: these are controlled development regressions. The eval-expert optimization
phase's protected-holdout prerequisites are not met; no production candidate will
be qualified from this wave. Keep any subsequent prompt changes as new cohorts.

### M004 round-one update and next admission

Initial complete-assembly results:

- **Native facts:** Luna recovered 12/30 regions; Perplexity recovered 20/30.
- **128 px crops:** Luna recovered 12/30; Perplexity recovered 15/30.
- **Current words and geometry:** Luna recovered 12/30; Perplexity recovered 13/30.
- **Native CPU control:** 30/30. Neither model improved on this control.

Luna almost always chose A. Round two tested literal compact join/split criteria
and separately derived geometry facts, preserving the scorer, gold and candidates.
This tested evidence representation rather than confidence adjustment.

The wave request-count guard expanded from **600 to 1,000** to include paired
compact ablations and the separate embedding experiment. Incremental accounted
spending remained capped at **USD 1**, within the cumulative **USD 15** authorization.
All trials and failures were retained.

The user explicitly authorized [Langfuse integration](bench/LANGFUSE.md).
At that point, provider-reported usage and cost—including zero—were authoritative;
catalog prices were fallback estimates for missing charges. **The later cost-policy
update below supersedes how zero charges are used in comparisons.** Reservations
remain budget encumbrances, never reported charges. Telemetry contains request
hashes, shapes and compact outcomes, without credentials or embedded images.

## Completed wave and disposition

| ID | Completed result | Decision |
| --- | --- | --- |
| M001 / M004 | [Evidence repair](bench/results/evidence-repair.md): constructed/native control **30/30**; Perplexity **20 → 23 → 26/30** with compact/derived facts; Luna **12 → 10 → 7/30**, or **14/30** with verbalized facts. Source conservation held. | Retain Perplexity's derived-evidence DEV candidate. No production default or independent validation claim. |
| M002 | Tested 64, 128, 256 and 512 px, blur, blank images, raw history, history summaries and both together. No consistent win over matched native/placebo controls. Image caching and byte bounds were implemented. | No automatic screenshot route justified by this wave. |
| M005 | [Rust color regions](bench/results/color-regions.md): native paint boundaries **10/10**; pale raster regions **8/8** at threshold 8, but **0/8** at thresholds 18 and 36; outlines **2/2**, with four extras. | Prefer native paint evidence; keep the bounded raster prototype experimental. |
| E001 | [Image retrieval](bench/results/image-embedding-retrieval.md): Voyage whole-page first hits **6/6** at 512 px and **3/6** at 128 px. Gemini achieved **5/6** at both sizes. Every forced ranker returned hits for both absent queries. | Use for candidate finding; do not claim exact-phrase proof or recovered structure. |
| O001 | [Langfuse](bench/LANGFUSE.md): **16 priced models** registered and read back; **2,144 retained requests** exported/replayed without errors. Exact provider tokens/cost were verified. | Preserve reported usage and charges. Apply the newer zero-cost fallback policy to comparisons. |
| V001 | [Contamination audit](bench/results/evidence-contamination-audit.md): **732 projection-invariance checks**; no direct gold, fixture or private-intent field leak. | DEV tuning remains DEV. Keep authored ROI/oracle conditions and provenance limitations explicit. |
| M003 | No independently curated protected confirmation set was used in this wave. | Do not claim production readiness or generalization from these runs. |

**Historical wave accounting:**

- **794 new requests:** USD 0.0219335368 provider-reported charges; no new unresolved failed-call charges.
- **Cumulative provider/rental-reported charges:** USD 2.0688880668.
- **Prior unresolved reservations:** USD 0.60.
- **Conservative accounted total:** USD 2.6688880668 of the USD 15 cap.
- **Ledger entries:** 1350–2143.

These are historical reported charges. Original zeroes remain in the retained
responses; the newer comparison policy estimates their cost from published prices.
Some repeated conditions replayed identical successful bodies locally. Their
historical latency and logical request cost are not fresh paid calls.

**Configuration:** OpenRouter initially used `.env.remote-hosts`. After the user
added an `.env` key, new clients preferred `.env`, with `.env.remote-hosts` as a
fallback. The already-running embedding client retained its startup key. No
credential values or hashes were logged. Both files are ignored, and Langfuse
also prefers `.env`.

**Validation at wave completion:** 1,562 tests passed, 16 were skipped and two
were expected failures. Workspace Ruff and mypy checks passed, including the new
runners/adapters. Inference ran on hosted services; local preprocessing, tests
and the standalone Rust experiment used CPU only.

**Private publication:** the user released the push hold and requested
`origin/main`. Repository privacy was verified before that push. Public upstream
and fork remotes remained disconnected, GitHub Actions remained disabled, and
unrelated `mise.toml` was excluded. The pre-push guard permits only the requested
private repository and `main` branch; it was not bypassed.

## Rate normalization requested by user

[Model-grouped rates and all aggregate scores](bench/results/model-experiment-rates.md)
cover 77 hosted experiment/probe rows. Rates use unique original requests,
provider-reported USD and summed HTTP time, with batched observations counted
once each. Partial-page decision inputs are explicitly distinguished from page
images; zero reported charges, failures, cache replays and query-indexing cost
separation are explicit. This is an offline reanalysis; no new inference or spend.

## New silver DEV wave and cost-policy update

2026-10-08 local date / 2026-10-09 UTC artifacts. The user requested initial
analysis, ranked combinations, and new-dataset readiness. The
[experiment plan](bench/EXPERIMENT_PLAN.md) prioritizes native/cascade followed
by Perplexity derived evidence, a compact-facts/derived fallback hypothesis,
Luna relationship selection, and batched Jev throughput. These combine measured
components; complete pipeline quality/cost is unmeasured. Earlier exposed
“test/heldout” transformations remain DEV regressions.

**S001 — Dataset expansion:** generated **104 new DEV files / 125 pages** (64 related layout variants,
40 related math encoding probes). Before hosted testing, generic Report/Reference
titles replaced visible family/encoding names; local metadata tags remain.
Sanitized dataset `2e3b8c00f83375cc5d5e804ebe473f9ea0926f0ac2e1153996058381fdf02d21`
completed 104/104, recovered 1,576/1,576 authored literal anchors, and reproduced
104/104 warm text/Markdown outputs with zero worker/metadata errors. Four
unmapped-Type3 warnings are retained. The original `50a400f840cb5aac` baseline
remains separate DEV provenance. Anchor recall does not score formulas, tables,
or layout. [CPU/RSS results and limitations](bench/results/silver-challenge.md).

**S002 — Protected holdout:** the custodian independently constructed and parse/render-validated a
sealed 20-file / 26-page set; inventory
`c1f887661e3dd40faa15510001decba1c2cb0a1112bdbb1566286a6541e0fe8e`.
It shares a serializer, not DEV template builders. Optimization agents must
not access its files or labels. Protection is procedural, with configuration
freeze required before evaluator-only scoring. No held-out quality was measured.

**M006 — Image sweep:** planned native image sweep across Luna Decisions, Perplexity Decider 1.1,
Clef Flash and Clef. Final requested arms are RGB8, grayscale8 and 16-color
palette PNG with 4-bit indices independently at 128, 512 and 1200 px: nine real arms
and nine matched blanks. There is no grayscale-plus-palette arm. The
first assembly sweep uses the existing 30 controls; a separate silver 125-page
gate measures table presence only. Structural gold and a generic new-dataset
candidate/gold adapter remain prerequisites for complete assembly scoring.
[Official model survey](bench/IMAGE_MODEL_SURVEY.md). This entry records plans
and CPU baseline only; no new model calls or image scores are recorded here.
Provider-cache probes will use actual repeated transmissions, separately from
free local replay.

The user's new cost instruction supersedes the earlier rule that preserved zero
as the effective comparison cost: positive reported charges take precedence;
zero/missing charges fall back to published rates times observed provider tokens
as labeled estimates. Original zeroes and the spending ledger stay unchanged.
Missing tokens/rates remain unknown, partial sums remain partial, and reservations
remain budget encumbrances. [Updated grouped rates](bench/results/model-experiment-rates.md)
mark estimates with `~`; historical reported-spend entries above remain records
of what the provider reported, not repriced campaign spend. Future hosted results
and actual incremental spend will be appended separately by the root runner.

**S001 — Instrumentation follow-up:** the sanitized DEV baseline was rerun using
Linux `/proc/self/status` VmHWM to avoid inherited launcher RSS across exec.
Current run `20261009T035110-o22uv9uy` completed in 22.154 s, measured worker CPU
4.756 s and median/max worker peak RSS 104.21/105.21 MiB. All 104 files / 125 pages,
1,576 anchors and 104 warm matches are unchanged; errors remain 0 and four unmapped
Type3 warnings remain. Prior baseline runs stay retained.

The user's continual-experiment steering adds two separate experiments:

- **R001 — Row and cell placement:** assign retained source IDs to row/header/cell
  slots, using 128, 512 and 1200 px screenshots.
- **R002 — Coordinate edit log:** select bounded assign, move, join and split
  operations, with atomic validation, undo and source conservation.

Both must distinguish candidate availability from model selection. They supplement
the image and provider-cache experiments. See the [experiment plan](bench/EXPERIMENT_PLAN.md).

## Report formatting repair

Restored missing word spacing in the historical wave summary and used properly
separated lists, bold labels, inline code and descriptive links. The image-report
generator now groups results by model and separates quality from usage and cost,
so each table is narrower. Preparation metadata uses an indented code block.
Batching prose now reflects provider-dependent limits.

Regenerated the [initial image matrix](bench/results/image-resolution-matrix.md)
and [bounded Clef matrix](bench/results/image-resolution-clef.md). Their complete
machine-readable summaries are unchanged, including scores, usage and costs.
Validation: eight image-runner tests passed; formatter and Ruff checks passed.
This repair made no hosted requests.

## Two-hour larger-corpus wave

The user authorized adding 10–20 sampled OmniDocBench rows, pushing to private
`origin/main`, and continuing iterative tuning for up to two hours. The
[shared tuning record](bench/TUNING_WAVE.md) tracks hypotheses, gates, resource
limits, council proposals and reprioritization. Three parallel agents use
separate worktrees; the coordinator owns hosted requests and shared accounting.
The protected 20-file holdout remains untouched.

### Measured combinations and planning update

The new [28-page borderless/prose challenge](bench/results/borderless-challenge.md)
exposed native candidate coverage of only 2/12 borderless positives. The
[rolling-row candidate assembler](bench/results/rolling-rows.md) reached 12/12,
but also proposed tables on all 12 prose negatives and lost merged spans.
[Paired admission](bench/results/rolling-admission.md) combined native vectors,
rolling candidates and Luna with a 512-pixel source image: 12/12 borderless exact,
0/12 prose false tables and 4/4 merged controls. This is authored DEV evidence;
a fresh robustness set already exposes lower candidate coverage. No extraction
default changed.

The [shared plan](bench/TUNING_WAVE.md#evidence-to-experiment-planning-rule) now
explicitly maps observed failures to compatible prior techniques, combined
experiments, removal ablations and failure gates. Next combinations target
OCR-box overlap, prose admission, merged-span preservation and payload admission.

The user renamed the private repository and package to **jev-pdf**. Remote
`origin` and `private` now target `justsml/jev-pdf`, verified private; the guard
continues to permit only private `main` pushes. Package identity uses `jev-pdf`
and `jev_pdf`, preserving compatible `pylopdf` imports and original notices.
Historical artifact directories remain unchanged. No package was published.

### 2026-10-09 05:16 UTC — P001 prompt sweep and fresh-layout correction

- Frozen 15 generic q0-only prompt variants from three independent worktree
  agents; both 24-page hosted cohorts and Luna/PPLX use identical source evidence
  and candidate menus. Dedicated 05:05–06:05 UTC tuning window, USD 1 incremental
  admission cap under the shared USD 15 cumulative cap.
- The unchanged Luna 512 selector falls to 3/16 exact tables and 2/8 prose false
  positives on fresh topology DEV. Candidate coverage is only 4/16. This directly
  motivates complementary candidate topology work, not confidence tuning alone.
- A004 OCR overlap ablation improves 1200 px borderless exactness from 6/12 to
  10/12 to 12/12 at allowances 0, 0.25, 0.5 word heights; all 12 prose false
  positives remain. No new OCR/model spend. Defaults unchanged.
- Package/repository renamed jev-pdf, private visibility and scoped pre-push guard
  retained. Editable migration passes 1,919 tests, 16 skips and two expected
  failures; no release publication. Provider-page rate regression now excludes
  local replays from throughput and preserves real HTTP time before later replays.

### 2026-10-09 05:22 UTC — quarantine fresh DEV answer cues

Source-only audit found class-specific explanatory sentences in fresh24 PDFs.
These directly cue the model's table/prose answer. Prior fresh admission scores
are **excluded from primary conclusions**, preserved with charges for audit.
Stopped new cued requests at the next batch boundary. A new source-neutralized
cohort will remove the explanatory band with body geometry unchanged, then freeze
all requests before scoring. Original28 has no class-specific title/footer; its
semantic templates remain narrow DEV evidence. Heldout untouched.

### 2026-10-09 05:30 UTC — realism fixes and combined OCR route

- User requested Astra re-review: separate worktree agent audits original104 and
  applies v2 meaningful-table/continuous-prose/explicit-ambiguity fixes. Original
  probe artifacts stay immutable. Scorer now leaves ambiguous truth unscored.
- Neutral deletion arm's authored negatives may be table-like; stopped further
  fresh/neutral prompt expansion. They remain diagnostics, not admission accuracy.
- OCR1200 + bounded overlap + baseline Luna512 recovers 12/12 borderless tables,
  rejects 12/12 prose controls and preserves 4/4 native merged grids. PPLX recovers
  12/12 but falsely accepts 6/12 prose pages. 48 calls cost USD 0.00808632 effective.
- Aggregate-selected semantic prompt now being transferred to OCR inventories;
  source-only presence gating prepared as separate decomposition experiment.
