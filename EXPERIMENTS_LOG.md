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

### 2026-10-09 06:05 UTC — training references and wider resolution/specialist exploration

- Added 16 additional OmniDocBench TRAINING references and geometry-derived synthetic pages, disjoint by source ID from DEV16. Known document parents stay grouped; unknown parent identity remains explicit. Astra is revising all 16 derivatives after paired visual inspection. Source recognition answers are excluded from generation. Research-only provenance and raw artifacts remain separate from committed metadata.
- Reopened SLANet with 336 CPU-only DPI/crop combinations. Best observed arm is 72 DPI with 12-point source-derived padding: 7/16 exact tables; every arm still proposes tables on all eight prose pages. Increasing DPI did not consistently improve quality. See [all results](bench/results/specialist-resolution.md).
- Frozen strict source-ID, shape, span and text agreement between SLANet and T005 accepts seven correct tables, zero wrong scored tables and zero prose false positives, deferring nine positives. Two accepted ambiguous pages remain unscored. A retained PPLX gate conjunction is an offline routing simulation, with no new cost or latency claim. See [agreement results](bench/results/specialist-agreement.md).
- Image matrix spans 200/300/400/500/600/800 px, separate width/height/longest-edge controls, RGB8/gray8/palette4 and four models. At the 06:04 snapshot, 839/936 unique regular batches completed with no failures; 624 independently frozen anisotropic batches are queued. Exact geometric aliases share quality only, never provider-cache or throughput credit. See [live snapshot](bench/results/image-axes-progress.md).
- Fixed raw-string metadata scanning of legal compact `>>stream` delimiters. Existing prototype measurements remain historical; new derivative metadata will use the corrected scanner. Thirteen metadata tests pass.

### 2026-10-09 06:08 UTC — expanded extent selection result

T005 source-only local-gap extent proposals plus the unchanged semantic prompt and
512 px source image completed 56 requests on reviewed DEV28. PPLX selected all
16/16 positive tables exactly, with zero incorrectly accepted tables and 0/8 prose
false tables. Luna selected 9/16 exactly, incorrectly accepted four positive
matrices, and produced 0/8 prose false tables. Four ambiguous pages stay unscored.
All source IDs are conserved. The two-model run cost USD 0.04573798. PPLX measured
2,771 requested pages/USD and 36.3 pages per summed HTTP minute; Luna measured
786 pages/USD and 154.1 pages per summed HTTP minute. Native preparation and
provider latency remain separate from end-to-end throughput. See
[complete results](bench/results/rolling-extent-admission.md).

This improvement came from candidate coverage/extent repair, not added confidence
thresholds. Preserve the earlier menus as ablations. Preparing an instruction-only
transfer of two already-frozen generic prompts to the expanded menu tests whether
Luna's residual selection errors respond to cross-cell or reading-order evidence.

### 2026-10-09 06:16 UTC — reviewed training derivatives and conditional image scope

- Selected 16 frozen v3.1 TRAINING derivatives after Astra reviewed every paired
  source/render. Ten source genres, five language categories and five layout
  categories are represented. All 5,117 extracted words remain within page bounds;
  no word centers lie inside true masks; all 16 metadata scans succeed. Versioned
  registries retain scalar/page PDF, image, string-byte and text/noise measurements.
  Photos, handwriting, French content and exact table internals remain approximate.
  The corpus remains research-only and parent-linked. See
  [review and gallery](bench/results/omnidoc-training.md).
- The complete regular size/axis matrix used 936 unique requests and USD
  0.53657136 effective for 4,320 transmitted case inputs. The 30 cases deliberately
  require reading document conventions printed on the page: this is conditional
  synthetic cue-reading, not natural-table extraction. Artwork is achromatic,
  limiting conclusions about grayscale. Scope now appears in regenerated reports.
- [Per-case analysis](bench/results/image-axis-interpretation.md) preserves older
  arms and complementary failures. A 30/30 oracle combination falls back to 27/30
  under a naive routing rule because three repaired cases accompany three lost
  justified abstentions. This is an arbitration hypothesis, not an achieved gain.
- Full checks: 2,027 passed, 16 skipped, two expected failures with the explicit
  installed Rust compiler. Subsequent training/metadata changes pass 23 focused
  tests; image reporting passes five tests. Ruff and mypy are clean.

### 2026-10-09 06:26 UTC — bounded wave closure

Both image matrices completed: 936 regular plus 624 anisotropic requests, zero
failures, USD 0.85793760 effective across 7,200 transmitted case inputs. The two
expanded-menu prompt transfers completed another 112 requests for USD 0.09158180.
PPLX remains 16/16 exact with 0/8 prose false tables under both prompts. Luna reaches
10/16 with cross-cell instructions (four wrong accepts), versus 8/16 with reading
order (six wrong accepts). Source inventories remain conserved; ambiguous pages
remain unscored.

All 15 original prompt variants completed for both models. On reviewed DEV28,
Luna completed all 15; PPLX completed eight, plus 27/28 requests on a ninth.
One interrupted PPLX request (ledger 8342) retained no response and keeps its USD
0.30 reservation. The persistent failure guard leaves the remaining PPLX variants
unattempted; they are not scored as observed failures. Completion denominators
and unknown missing-response charges now appear explicitly. The internal prompt
cap increased from USD 1 to USD 1.40 to finish distinct Luna requests while keeping
that reservation; neither prior accounting nor the user's USD 15 cap was reset.

At closure the shared ledger contains 9,299 entries: USD 2.7781951488 positive
provider-reported charges, USD 1.00316290 catalog estimates and USD 1.50 unresolved
reservations. Prior provider/rental accounting is USD 1.024262108. Conservative
cumulative accounted total is **USD 6.3056201568 of USD 15**; excluding unresolved
reservations, reported/estimated costs total USD 4.8056201568. These categories
remain distinct. No further paid work is queued for this bounded wave.

Validation: full suite 2,027 passed, 16 skipped, two expected failures, followed
by 40 focused passes covering subsequent changes. Final Ruff and mypy pass.
The final [wave report](bench/results/tuning-wave-2026-10-09.md) links all successes,
regressions, scope limitations, CPU/RAM measurements, and future combinations.

### 2026-10-09 — A055 matched Anthropic 5.5 baselines

User requested current Anthropic baselines, including newly released Haiku 5.5.
Verified all three exact OpenRouter IDs against the live catalog and official
release/migration documentation; registered their Langfuse models/prices without
conflicts. Frozen 84 requests before loading scorer targets, using the identical
reviewed DEV28 sources, image512 bytes, candidate menus and semantic instructions
as the T005 extent union. Manifest SHA256:
`f2847cfbb929d0c114c2ecc606287f3059331b0dda08772c0186becad2351ed7`.

All models use explicit medium effort, a 4,096-token output cap and strict
`answers.q0.choice` JSON. Sonnet's default is high, so this medium setting is
explicit rather than described as default/maximum capability. Chat transport is
the only source-evidence change. Four ambiguous pages remain unscored; heldout and
TRAINING references are untouched. Full setup and reproduction:
[Anthropic baselines](bench/ANTHROPIC_BASELINES.md).

New wave cap USD 5 with USD 1.25 per-request reservations; every frozen body must
fit a conservative encoded-byte/output-token cost bound at the provider price
ceilings before any transmission. Existing generic requests retain their USD 0.30
reserve. Cumulative user cap stays USD 15; internal campaign cap increases from
USD 8 to USD 10 for this new work. Historical charges/reservations are unchanged.

A055 completed all **84/84 requests** without errors, retries or budget stops.
At explicit medium effort, Opus 5.5 recovered 15/16 exact tables and abstained on
one; Sonnet 5.5 and Haiku 5.5 recovered 16/16. All three had zero incorrectly
accepted scored tables and 0/8 prose false tables. Ambiguous pages remain unscored.
PPLX's matched retained 16/16 result ties Sonnet/Haiku and recovers one more table
than Opus, with substantially lower observed API cost. This single authored DEV
run does not establish general superiority or unrestricted extraction quality.

Reported charges: Opus USD 2.037944, Sonnet USD 0.992892, Haiku USD 0.0534666;
total **USD 3.0843026**. All charges were positive provider-reported values. Each
model processed 493,021 input tokens; no prompt crossed Haiku's pricing threshold
and no completion reached the cap. All 84 provider cache counters report zero
cache-read tokens. Langfuse indexed generation/model/cost verification succeeded
for all three models. Conservative cumulative accounting is **USD 9.3899227568
of USD 15**, including USD 1.50 earlier unresolved reservations.

Local execution: 383.07 s wall, 26.50 s process CPU, 108.96 MiB peak RSS; provider
HTTP time summed to 352.51 s. Remote CPU/RAM are unmeasured. Final validation:
2,049 passed, 16 skipped, two expected failures; Ruff and mypy pass.
[Baseline details](bench/results/anthropic-baseline.md) and
[matched configuration comparison](bench/results/anthropic-matched-comparison.md).

## 2026-10-09 — L001, decisions before word assembly

The user requested `$council-of-dans`, broad implementation/measurement loops and
complete hypothesis/output/verdict records. Three parallel medium-reasoning
gpt-6.1-sol agents supplied distinct architecture, invention and evaluation plans,
then implemented in isolated worktrees. All proposals completed. See
[L001 plan and hypothesis matrix](bench/LOWLEVEL_DECISIONS.md) and its linked
individual council proposals.

Implemented a private bounded Rust pre-clustering glyph snapshot, decoded text
operator sidecar, 24 logical / 72 render-equivalent authored controls, nine
source-only evidence arms, strict source-partition materialization and shared
ledger runner. No default extraction path calls a model. Models are Jev 1.13,
d1, PPLX decider and Luna decisions; only the latter two receive crop arms,
matching current gateway modalities. Langfuse price registration verified all
models with no conflicts. Starting conservative accounting was USD 9.3899227568;
L001 has its own USD 1.50 persistent cap within the unchanged USD 15 authorization.

Preflight verdicts: reject the unpaid first crop freeze because discarded alpha
produced black images; white compositing plus regression checks corrected it.
Supersede the next unpaid freeze because native words leaked paint-order
nuisances into the canonical glyph arm. Retain both artifacts. Paid initial
requests use `lowlevel-v1/basic-final/`; all 24 pilot transmissions passed schema
checks and cost USD 0.009940746. The full frozen 768-request matrix is in progress.

The independent source audit proves text-only inputs cannot distinguish the
initial ruled join/split/unknown variants. Do not mistake those missing dividers
for a model reasoning deficit. Native word atoms omit two of four authored
field-split possibilities; glyph atoms retain all four, but every hosted arm
already gets those same glyph-derived chunks, so this is capability coverage,
not a measured W-versus-G model improvement. The 12 logical / 36-page history
follow-up freezes ordinary numbered items separately. Tentative continuation
labels remain distinct from observable new-item evidence and unknown cases.

CPU verdict: preserve the experimental hook but do not claim speedup. Snapshot
plus normal extraction took 2.09× original104 time and 1.68× the small controls,
with approximately 0.84 MiB additional median process peak RSS; all text hashes
and mapped-character conservation checks passed. Five process blocks, matched
release builds and full ranges are in the
[performance report](bench/results/lowlevel-native-performance.md). An invalid
RSS-launcher pilot is retained, explicitly excluded and completely rerun.

The audit also reproduced a native paint-order word-clustering defect on
identical rendered pages; an isolated deterministic repair is under regression
test. A separately frozen, source-only vector-divider policy correctly handles
all 12 logical row controls: eight decisive choices and four abstentions. It
does not classify business headers or history-only cases. This is a reason to
test deterministic routing before paying for every region, not evidence of
production safety or realized cascade savings. See
[geometry results](bench/results/lowlevel-geometry.md).

## 2026-10-09 — expanded lower-level research, USD 100 authorization

The user raised the cumulative research cap to USD 100 (not USD 100 additional).
Previous charges and unresolved reservations remain in the shared ledger. L001
now has a USD 5 persistent admission ceiling, L004 USD 5, and L003 USD 15.
All experiments remain DEV-only, CPU preprocessing with hosted inference; protected
heldout files remain untouched. No local GPU or training was used.

Initial evidence screening completed **768 successful requests**, with effective
cost **USD 0.356243372**. Positive provider charges are preferred; Luna's reported
zero remains preserved with separate catalog estimates. Complete model-grouped
scores and rates: [initial matrix](bench/results/lowlevel-basic.md). PPLX crop512
recovered 38/48 authored known partitions versus 30/48 with vectors and 26/48
with words; it abstained on none of 24 ambiguous page inputs. These are only
24 logical authored controls with three encodings, and supplied target regions.
They do not establish full-table extraction quality or production generalization.

Prompt-factor results: PPLX crop512 with resolved literal instructions recovered
15/16 known partitions on the 24 selected representatives, versus 13/16 with the
original prompt on those same pages; it abstained on 1/8 ambiguous cases. Singleton
batching alone did not improve it. All requested arms, including losses and
refusals, remain in [prompt factors](bench/results/lowlevel-prompt-factors.md).
The independent audit found missing-evidence collisions in text-only wrap arms:
identical admitted states have different author labels, so incorrect forced
answers there cannot diagnose absent model understanding.

History results: PPLX words/glyphs/operators each reached 17/18 authored known
choices, with 0/18 ambiguity abstentions. Nine known pages are tentative conventions,
and nine expose explicit new identifiers; do not combine them into a hard-grounded
accuracy claim. Rolling summaries did not consistently help. See
[history matrix](bench/results/lowlevel-history-v2.md). Jev encountered HTTP 400
on a 115,568-byte rolling request. The original request, failure, unresolved USD 0.30
reservation and persistent L001 stop are retained. Endpoint inspection suggests a
32,000-token prompt boundary; the cause remains unconfirmed.

A new L004 experiment freezes lossless compact tables of glyphs and interned
operator operands under a 32,000-byte full-body guard. All basic and history source
observations remain byte-identical to their original freezes. The new resolved
prompt, typed transport and adaptive batching change jointly: this is a practical
packet comparison, not an isolated compaction effect. A matched singleton raw/compact
control is planned. History contains no vector rules; its geometry hint is a
constant defer cue, while the separate basic controls test actual divider evidence.
See [compact packet design](bench/results/lowlevel-compact-design.md).

A native paint-order regression was fixed with forward-gap run boundaries and a
bounded disjoint-interval fast path. All 24 four-glyph paint permutations preserve
word order; overprints remain distinct. Original104 and initial72 text hashes
remain unchanged, and all 36 history variants now agree on words and text. Frozen
paid model inputs stay pre-fix. [Repair and CPU diagnostics](bench/results/lowlevel-word-order.md).

The natural-source survey inspected six regions across five licensed DEV PDFs.
The Edison patent's invisible OCR layer disagrees with visible text, beyond a
source-conserving grouping oracle; a separate provenance-preserving visual-repair
experiment is being built. [Natural-source findings](bench/results/lowlevel-natural-survey.md).

The user explicitly requested every available image-capable decision model. The
refreshed OpenRouter decisions catalog lists PPLX Decider V1.1, GPT-6 Luna Decisions,
Clef Flash and Clef. All four enter the next matched image sweep. OpenRouter's
serving notes describe approximately 2K text-state truncation for Clef; use a
shared bounded target-local packet for the fair four-model comparison, with richer
context as a separately labeled treatment. Preserve RGB, grayscale and reduced
bit-depth as distinct image treatments at each selected resolution.

Validation at this checkpoint: **2,190 passed, 14 skipped, two expected failures**
(54.95 seconds) after rebuilding the final native repair. Whole-workspace Ruff and
mypy on source/tests plus new runners passed. Full local log is retained under
`lowlevel-v1/pytest-expanded.log`. Further experiment modules will receive their
own focused checks before integration.

### Gateway expansion requested by the user

A full live Vercel catalog comparison found one additional named decision-model
family: Laya (`convaiinnovations/laya` and `convaiinnovations/laya-free`). Gateway
also advertises d1 image input, absent from OpenRouter's d1 modalities. Add both to
L009; do not count aliases as separate architectures. Catalog capability conflicts
and the missing local Gateway credential are documented in
[Gateway candidates and protocol plan](bench/VERCEL_DECISIONS.md). OpenRouter runs
continue while the adapter and local credential are prepared.

### L005–L009 preparation and initial execution

L005 freezes identical singleton raw and compact canonical evidence, isolating
representation from batching and prompt. Its 288 records contain only 96 distinct
request bodies because encoding aliases remain identical. Report aliases separately.
The all-model L006 focus sweep freezes 1,728 requests on 24 logical layouts: four
image-capable OpenRouter decision models, six longest-edge sizes (64, 128, 256, 400,
500, 512) and three independent image formats (RGB8, gray8, two-bit palette). A
separate richer-context comparison has 864 requests for PPLX and Luna. All crops
derive from the retained 512-pixel PNG, so no native-render optimum is claimed.

All 24 L006 smoke calls passed across PPLX, Luna, Clef Flash and Clef. PPLX earlier
returned HTTP 429 in L004 and L005; their original failed requests and USD 0.30
reservations remain. Subsequent L006 fresh PPLX transmissions have a ten-second
minimum interval after the previous completion. This delay is local scheduling,
not API latency; execution wall time includes it, API-only rates exclude it. No
failed body was automatically retried.

L007 freezes 24 source-selected RGB bodies (128/512 pixels, four models, three
source-geometry strata) for three actual provider transmissions each, at most 72
calls. It disables local response replay and reports provider cache counters,
missing counters and routing changes explicitly. Execution waits for corresponding
L006 originals to succeed. Repeated requests do not establish a provider cache hit.

The user added the Gateway credential locally. L009 freezes 216 text requests for
Laya, Laya Free and d1, plus 432 matched d1 image requests. d1 text and image pilots
succeeded. Both Laya aliases returned HTTP 422 on a compact-canonical request;
supported text calls succeeded. New transport tests verify reservation-before-HTTP,
route-isolated replay, retained raw responses and reported-cost priority. Gateway
failed-row reconciliation was corrected using the exact route/body ledger entries;
the original result bytes are retained. No failure was silently removed.

An accounting audit corrected 12 within-freeze singleton alias rows in L002 that
had overwritten the fresh-call flag when replaying a later identical input. Original
results are retained byte-for-byte; shared ledger and quality responses are unchanged.
Updated tables count distinct transmitted inputs in cost/latency numerators and
separate planned/completed request bodies from manifest records. Missing HTTP time
now makes the complete API throughput unknown rather than using a partial denominator.

### L005 matched result and Gateway compatibility follow-up

On identical singleton history evidence, Jev, d1 and Luna preserved aggregate
known/ambiguous scores while lossless compact representation reduced estimated
charges by 68.5%, 66.1% and 69.1%. Ambiguity handling remains poor. PPLX has an
incomplete raw arm after HTTP 429; retain its missing denominator and unknown cost.

L010 freezes exact JSON serialization of the L009 state with unchanged questions.
Its first 12 calls produced ten successes and two Laya-alias HTTP 422 failures.
Serialization alone did not fix compatibility. L006 PPLX also hit HTTP 429 after
eight successful image calls despite ten-second spacing; its stop remains while
other models continue. See the regularly updated [progress table](bench/results/lowlevel-progress.md).

L011 prepares a natural Senate expenditure page: 24 adjacent description pairs,
full-record versus description-only context, fresh 512/1200 crops. Requests were
frozen before separate source-aware screenshot references. These provisional
references are not blind gold; narrower context has its own uncertainty labels.
The fixed-edge comparison jointly changes context and glyph resolution.

### L013 offline geometry/model composition

The previously frozen divider-v1 policy runs on source drawings and target
selectors before loading references. It handles decisive geometry and defers the
remaining cases to retained model outputs. The all-input and paired denominators
remain separate; every gain/loss is retained. This is an offline composition
experiment, not a fresh cascade cost or latency measurement.

On all 72 initial encoded observations (24 logical authored cases), Jev words
improves from 28/48 to 40/48 known choices with zero paired regressions. Unknown
abstention remains 0/24. PPLX crop512 stays 38/48 with 0/24 unknown abstention.
Luna minimal improves 4/48 to 26/48 while preserving 24/24 unknown abstentions.
The original three-observation batches mix decisive and deferred pages, so none
can be skipped whole: do not claim one-third fewer requests or dollars from this
replay. Fresh singleton routing is a separate follow-up.

[Complete hybrid table](bench/results/lowlevel-hybrid-basic.md) records all 32
model/arm combinations. Geometry clipping/decoration and loose-selector caveats
still apply. Latest integrated suite: 2,274 passed, 14 skipped, two expected
failures; the subsequent hybrid scorer has a focused regression covering losses,
missing outcomes and mixed batches.

The same fixed routing policy on the frozen prompt matrix reaches 14/16 known
choices and 4/8 ambiguous abstentions with PPLX minimal typed/resolved input,
versus 6/16 known before geometry. PPLX resolved crop512 remains 15/16 and 1/8.
This suggests a cheap text-plus-rules branch worth retaining alongside vision;
it does not establish production precision or fresh cascade cost. All 48 prompt
combinations are in [the paired table](bench/results/lowlevel-hybrid-prompts.md).

Gateway d1 completed all 72 text configurations in each state representation
(48 distinct bodies per representation). JSON-string state changes minimal
known choices from 7/16 to 5/16, increases ambiguous abstention 1/8 to 2/8, and
leaves words/canonical at 8/16 with 0/8 abstentions. Keep both representation
results and their reported costs; serialization is not universally beneficial.

### Natural visual agreement and row-ownership execution

L008 freezes 108 labeled image/model configurations but sends only 84 distinct
bodies: six crops have identical 512/native images. No image is upscaled. Seven
source-aware literal references are primary; the contextual zero/O case is
separate, and the unavailable degraded transcription receives no invented label.
Requests contain only native word text, one crop and generic choice instructions.

L011 freezes 480 route/model/image requests over 24 overlapping natural row pairs
from one Senate page. Four OpenRouter vision models and Gateway d1 receive the
same source chunks and pixels. Full-record and description-only scope references
are reported separately. A full outer border encloses multiple business records,
so the reference notion is semantic record ownership rather than arbitrary outer
rectangle membership. No post-reference request edits were made.

The L007 pilot initially refused the 11.1MB shared ledger under a generic 8MB
artifact reader before making any provider call. Ledger admission is now an
explicit 64MiB boundary, independent of small request/response limits. OCR/natural
runners use the same adequate ledger admission. No historical accounting was
removed to fit the smaller limit.

### L012 supported text representations and L003 scheduling

L012 freezes all 24 original source observations with minimal/words text for the
two Laya aliases: 96 configurations, 64 distinct bodies. This explicitly declared
compatibility subset keeps exact L009 bodies and replays existing successful
responses locally. It does not delete canonical failures, clear old stops or retry
failed bodies. Report L009/L010 complete-inventory failures alongside L012 results;
accepted representations remain worth exploring. No unsupported inference about
the cause of HTTP 422 follows from the subset.

A bounded HTTP diagnostic now retains only fixed error types, known field paths
and numeric Retry-After seconds. Raw error messages and reflected input remain
excluded. Earlier failures cannot retroactively gain diagnostics.

L003 execution now prioritizes the already frozen crop512 arm, then words, to
complete a matched frontier slice sooner. Request bytes, manifest order, references
and complete 648-request denominators remain unchanged; execution history records
the priority. Haiku remains stopped after its HTTP 429. Other unrun arms are
pending, not discarded or treated as failures of model quality.
