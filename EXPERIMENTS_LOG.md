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

### L006 first complete image-factor comparisons

Luna, Clef Flash and Clef each completed all 432 requests (24 logical layouts ×
18 treatments). PPLX completed eight, then hit HTTP 429; its remaining 423 are
unattempted. The complete 1,728-body matrix remains in the report.

RGB known scores at 64/128/256/400/500/512 pixels are Luna 7/7/6/8/7/7 out of
16, Clef Flash 8/8/9/8/8/8, and Clef 7/8/8/8/8/8. Bigger crops did not produce
monotonic quality gains. RGB/gray/low-bit remain separate treatments at every
size; do not infer that every format is equivalent. Clef Flash low-bit256 reaches
12/16, versus RGB256 9/16: three paired ruled-wrap join recoveries, zero losses,
and still 0/8 unknown abstentions. This is one pass and requires a repeated
nearby-resolution/quantization control before selecting an optimum. Model/context
limits and this small authored cohort prevent generalization to arbitrary pages.

[All scores, pages/USD and API pages/min](bench/results/lowlevel-images-focus.md).
The useful follow-up is a source-frozen 192/224/256/288/320-pixel sweep around the
Clef Flash result with independent quantization levels and repeated transmissions,
plus a geometry-first branch. Retain unmodified RGB/gray controls and provider
cache counters; repetitions alone do not demonstrate cache hits. This follow-up
is proposed, not executed.

### Conditional geometry gate resource measurement

Five serial fresh-document passes over the exact 72 authored source PDFs retained
all source-only routing choices. Drawing interpretation/projection/grouping plus
open/close median was 22.937 ms wall and 52.942 ms CPU for 72 pages, about 0.319 ms
wall/page. Full glyph/operator/crop snapshot preparation was 4.614 s wall and
4.625 s CPU, about 64.08 ms/page. The 201× stage wall ratio is not an end-to-end
extraction or hosted-cascade speedup: supplied target selectors and all boundary
discovery costs are excluded. One serial caller still uses the library default
eight native workers; CPU greater than wall is expected. Mixed-process peak
RSS 146.9 MiB is not an independent gate/full memory comparison.

[Full phase measurements and reproducibility](bench/results/lowlevel-geometry-performance.md).

L014 freezes four source-equivalent Laya compatibility bodies on a new eligible
source: expanded glyph dictionaries serialized as JSON versus compact JSON.
Expansion preserves all values/order and questions; prior failed sources are
excluded by transport status alone. No scorer labels are read. This diagnostic
uses a separate USD 1.50 admission cap and retains failures/reservations.

### Gateway image transport correction and complete frontier slice

All 432 L009 Gateway image calls were accepted, but identical reported token usage
across sizes triggered a protocol audit. The earlier TypeSafe top-level images
field has no documented forwarding contract. Liquid direct-API image support
does not establish that Gateway forwards the same field. These results are now
**visual input unverified**, including the ten Gateway rows in the L011 pilot;
they cannot establish d1 vision quality or image-size effects. Original bodies,
responses, charges and scores remain retained. An endpoint-specific native
`/v1/decisions` adapter and image-only controls precede any new d1 vision claim.

Matched L003 crop512 is complete for Opus and Sonnet: Opus 46/48 known and 14/24
ambiguous abstentions, 19.15 API pages/min and 64.79 pages/USD; Sonnet 37/48 and 10/24,
70.56 API pages/min and 150.81 pages/USD. Matched PPLX 38/48 and 0/24, 204.78 API pages/min
and 6,688.96 pages/USD. PPLX exceeds Sonnet by one known decision only; it does not
beat Sonnet on ambiguity handling or Opus on quality. Haiku remains incomplete
after HTTP 429. These rates are supplied-region decisions per tested source page,
not whole-page extraction throughput. All full denominator tables are retained.

L012 minimal/words completed all 64 unique Laya-alias bodies, 96 configurations.
Both aliases score 10/16 known for minimal, 8/16 for words, with 0/8 unknown
abstentions; promotional catalog cost is zero, so pages/USD is undefined rather
than infinite. L014 ordinary expanded glyph dictionaries still return HTTP 422
for both aliases; compact encoding alone is not the cause. Safe diagnostics
contained no recognized machine-readable type/location, leaving cause unresolved.

### L017 image-consumption sanity and L016 admission hold

Hypothesis: the documented Gateway native Decisions transport may expose the
image evidence that the earlier TypeSafe packet failed to demonstrate. The four
TypeSafe controls returned unresolved for circle, square, blank and no image.
The native circle request returned HTTP 400; remaining native controls were
stopped. This is a transport failure, not an image-quality score. Original wire
bodies, responses, unresolved reservation and endpoint identities remain retained.

Verdict: Gateway vision remains unverified. L016 has 216 verified native-wire
bodies with PNGs identical to L015, but no paid PDF calls are admitted until
positive visual controls pass. The [protocol audit](bench/results/lowlevel-gateway-native-audit.md)
records the catalog/documentation conflict and a fresh no-image diagnostic plan.

### Self-hosted decision-model research and README comparisons

Three coordinated agents inspected public model cards, actual inference paths,
Hub metadata, licenses and runtime limits. The [eight-model shortlist](bench/HF_DECISION_MODELS.md)
prioritizes Intern-Decision-4B, Clef-Flash, Perplexity v1.1 and AutoTrust JEV-27B-VL,
with NeoHorse, GEV, Clef and the Apache-2.0 Nimble release providing further
comparisons. Revision pins and dated adoption observations are retained. GPU
classes are planning estimates; no weights were downloaded, no remote host was
created and no self-hosted throughput or quality was measured.

Hypothesis: direct access to trained decision heads, processor image budgets and
question sharing can reduce repeated work while retaining our source evidence.
Verdict: feasible candidates found; test native runtime parity before optimizing
precision, batching or prefix reuse. Reference labels remain outside model inputs.

README now contains model and experiment comparisons, matched frontier scores,
page-input rates, incomplete-run denominators and links to all retained reports.
Whole-page extraction performance is not inferred from supplied-region decisions.

### L015 complete: larger fresh crops can recover misses

Hypothesis: larger fresh source crops can restore visual evidence lost in the
older downsampled crops. All 864 unique requests completed across four models,
24 DEV representatives, three sizes and three independent color formats.

| RGB size | Luna known /16 | Flash known /16 | PPLX known /16 | Clef known /16 |
|---|---:|---:|---:|---:|
| 512 | 7 | 9 | 12 | 9 |
| 768 | 7 | 11 | 12 | 9 |
| 1024 | 11 | 10 | 13 | 10 |

Luna RGB1024 gained four wrap decisions without known-case losses relative to
512; ambiguous abstention declined from 2/8 to 1/8. Luna gray1024 gained five
known decisions and retained 2/8 abstention. Flash preferred 768 across formats;
RGB/gray1024 each had one known-case regression versus 512. Larger is therefore
useful for some models, with no universal monotonic improvement.

Effective inference cost was USD 0.062818012, including USD 0.0131148 estimated
for Luna. Flash reported two serving rates within this wave; its cheaper RGB768
aggregate does not prove a resolution cost saving or a provider cache hit.
All quality scores, paired losses and pages/minute/pages/USD are retained in
[the complete report](bench/results/lowlevel-images-large.md).

Next priorities: Luna gray1024 plus geometry and rolling-row evidence; Flash768
versus earlier lowbit256; PPLX resolved criteria crossed with fresh crops. These
configurations are DEV candidates, not protected-set-selected winners.

A reporting correction now marks encoding consistency unmeasured when only one
representative encoding per logical case was planned, instead of displaying a
false zero. Frozen request bytes and references were unchanged. A regression test
covers that distinction. Full suite: 2,337 passed, 14 skipped, two expected
failures; subsequent changes: 43 focused tests, whole-workspace Ruff and mypy
across 157 files pass. Conservative cumulative accounting is USD 18.81584162
of the authorized USD 100, including USD 6.05 unresolved reservations.

### R001: remote native decision heads, small vLLM baselines and research licenses

Hypothesis: self-hosted native decision heads can expose processor, batching and
kernel choices that hosted APIs hide. Small schema-constrained vision models
provide a distinct generative baseline; noncommercial JPT and Nimble v3 are
included for research and learning, with their release licenses recorded.

The coordinator reserved USD 18 in the existing shared ledger for a bounded
four-worker wave, including a USD 2 cleanup margin. The cumulative authorization
remains USD 100. An independent systemd supervisor enforces a two-hour deadline,
checks credit and conservative runtime estimates, and removes only exact owned
instances. Source-only packets cover the same 216 L015 page/size/color conditions;
DEV scoring targets stay on the coordinator and protected files remain untouched.

The first RTX PRO 6000 96 GB worker loaded pinned Intern-Decision-4B and passed
circle, square and blank-image controls (3/3). Initialization took 6.52 seconds,
with 9.18 GB CUDA peak allocation and 9.46 GB process peak RSS. The reference
Torch fallback is recorded as its own runtime treatment. PDF quality remains
pending; these controls establish basic image consumption, not PDF ability.

Native Intern, Clef, PPLX, JPT and stock Qwen/vLLM adapters preserve source
questions and return actual runtime fields. The worker retains complete attempts,
CPU/RSS, CUDA peaks and one-second device-wide utilization samples, with a hard
process deadline and three-failure stop. Small-model generated labels do not gain
invented probability vectors. Raw operational receipts and source evidence remain
ignored; subsequent checkpoints will record wins, failures, cost and cleanup.

R001 checkpoint: native Clef-Flash and PPLX completed all 216 conditions, with
RGB512/768/1024 known scores of 10/11/11 and 9/12/12 out of 16 respectively.
Both abstained on 0/8 ambiguous cases. Measured inference-only throughput was
748.85 and 292.15 supplied-region inputs/minute. Native PPLX512 falls below its
hosted 12/16 result; source parity does not imply backend/prompt/processor parity.
All nine arm scores and measured resources are in the
[R001 report](bench/results/remote-gpu-r001.md).

The original Intern run, Qwen4 vLLM, Clef27 and text-only Nimble also completed;
scoring updates follow. A second Intern run adds FLA alone with Torch/Transformers
pinned, retaining the original fallback measurements. The vLLM baseline disables
prefix and multimodal processor caches; these are local runtime settings, not
provider cache hits. A separately frozen, blind prompt screen contains four
generic instruction variants over the same 24 RGB512 source packets, without
consulting references or case-specific outputs.

Operational failures remain retained: one unavailable offer created no resource;
a host image build failed DNS resolution and its instance deletion was verified;
initial native controls omitted required transport model IDs and failed before
inference; an early Qwen CLI admission and server-start readiness failure were
fixed before its later runs. Provider-posted wave charges reached USD 2.551 at
this checkpoint and are still accruing. The original USD 18 reservation remains
in force; posted charges are not added again to that reservation.

R001 second checkpoint: nine vision releases now have complete 216-input DEV
cohorts, plus Nimble-v3's 24-input text ablation. Small stock Qwen 2B/4B/9B and
noncommercial JPT 4B/9B are included without replacing the native decision heads.
All nine-arm scores and measured CPU/RSS/VRAM are retained. README now links the
full comparison and labels warm inputs/USD as allocation-rate estimates that
exclude bootstrap, loading and idle time; billed lifecycle cost remains separate.

The frozen four-variant prompt screen completed on Flash, Clef, PPLX and Intern.
PPLX sufficiency wording improves known correctness from 9/16 to 13/16; identity
wording reaches 12/16 known and 3/8 ambiguous abstentions. The same variants hurt
Flash. Intern's sufficiency/neutral variants preserve its 12/16 aggregate but
change individual successes and failures. These are DEV-selected observations,
not a new confirmation set. Fixed majority/unanimity policies and their paired
misses are documented separately, including the unavailable oracle ceiling.

The newer Intern runtime preserves all 216 original decisions while reducing
prediction wall time from 945.58 to 19.68 seconds. Host, Torch and Transformers
change together; this is not yet an isolated causal result. FLA alone on the
original host remains slow and changes one answer. A same-host follow-up adds
causal-conv1d, then changes Transformers while retaining the host and Torch.

Fresh source-PDF crops are frozen for 128, 256, 384, 400, 448, 500 and 640 px,
with independent RGB8, gray8 and two-bit treatments (504 inputs/model).
Every PNG is re-rendered during verification before scoring; source text and
questions remain fixed. Flash, Clef, PPLX and Intern are the first native runs.

SmolVLM and LFM hit FlashInfer startup crashes on the rented Blackwell runtime.
An explicit Triton/SDPA attention treatment retains the failed attempts. LFM's
snapshot downloader also omitted its publisher's Jinja template; the downloader
now retains that pinned file. Qwen 0.8B and MiniCPM produced valid but incorrect
visual-control answers. An opt-in diagnostic admission distinguishes semantic
control failures from transport/schema failures and does not bypass the latter.
At the second billing checkpoint the provider has posted USD 4.700; charges are
still accruing within the original USD 18 fleet reservation and USD 100 cap.

R001 third checkpoint: all 13 vision releases completed their 216-input image
cohorts; Nimble-v3 remains a separate text ablation. SmolVLM, LFM, Qwen0.8 and
MiniCPM received explicitly labeled semantic-control diagnostic admission after
valid transport/schema responses. The vLLM host temporarily went offline and
rebooted; completed LFM artifacts were recovered. Qwen0.8/MiniCPM were resumed
under a new output directory. No timing crosses the interruption. A prepared
failover environment installation was cancelled before inference when the original
host recovered; its incidental bootstrap cost remains in rental accounting.

All 2,016 fresh-size inputs completed. Intern scores 12/16 known cases for every
size ≥256 across RGB/gray/two-bit; 128 loses accuracy. All 672 ambiguous decisions
remain decisive. Native reported token counts are retained rather than guessed;
PPLX's unreported tokens remain unknown. Native natural-region runs also completed
384 inputs on the existing overlapping Senate regions. Full-source and
admitted-scope reference agreement are reported separately.

Following the user's utilization request, the planned prompt × size matrix runs
two native models per GPU within measured VRAM admission: Flash+Clef use six CPU
threads each; PPLX+Intern use eight each. The first launcher incorrectly resolved
a virtualenv executable symlink to system Python and failed before inference;
the corrected launcher preserves the virtualenv path and writes separate v2
outputs. No failed records are removed. Per-model timings include shared-GPU
contention; whole-pair CPU/RAM sampling is retained separately.

The shared-server Qwen9 concurrency screen completed 216 inputs at each of
1/2/4/8 clients: global elapsed 53.97/34.96/19.51/13.57 seconds, a 3.98× throughput
increase from one to eight. Known correctness is 99/98/98/97 out of 144 repeated
known inputs; all four remain 0/72 on ambiguity. Device utilization averages
78.41/77.03/85.05/84.71 percent over sampled full windows. Native replica screens
and a true native batching implementation are separate follow-ups; increasing
replicas is not assumed to improve throughput.

The user requested concrete ambiguity mechanisms while completing planned work.
Parallel source-only implementations now measure font-scaled gaps and alignment,
neighboring anchors/rolling leading, interpreted separators/enclosures, whitespace
valleys, rule crossings and color boundaries. Threshold policies are frozen before
reference scoring. These cues are advisory evidence, not calibrated probabilities;
a gap alone cannot establish cell identity. The next matrix crosses geometry,
pixels and combined evidence with fixed source images and prompt wording.

The provider has posted USD 7.601 at this checkpoint. The original USD 18 wave
reservation is still in force within the cumulative USD 100 authorization; posted
charges are not double-counted. The independent cleanup deadline remains active.

R001 fourth checkpoint: completed the 1,920 native prompt × resolution decisions
and an exploratory 480-decision Qwen9 extension. The frozen geometry policy
resolved 8/16 authored known cases with no wrong decisions and abstained on all
eight ambiguous cases; all natural conditions were abstained. No policy thresholds
changed after scoring. Its compact evidence omits choices, references and IDs.

The new evidence matrix contains 288 inputs per model: geometry, pixel and
combined numeric cues at RGB 256/500 px with original/identity wording. The first
launcher-level status was misread as all five completing. Source-scored audit
confirmed only Intern and Qwen completed 288 each; Flash, Clef and PPLX each
stopped after three adapter refusals before model inference. A 640 px
source-only pixel probe is separately declared preprocessing. All payloads and
features were reverified before local scoring. One host's initial tar extraction
started before its transfer finished and failed before inference; extraction was
repeated only after transfer completion. Model requests were not retried.

The same-host Intern fast-stack cohort completed 216 inputs in 26.65 worker seconds.
A lightweight single-source cProfile diagnostic measured 2.029 seconds on the old
stack versus 0.092 seconds on the new one; old torch.conv3d accounted for 1.931
seconds. Disabling cuDNN on the old stack still took 1.967 seconds. These are
instrumented diagnostics, not full-corpus throughput or a single-dependency causal
claim. An earlier CPU+CUDA profiler grew beyond its useful diagnostic window and
was stopped, with the failed attempt retained.

Provider-posted R001 charges reached USD 8.802. Completed-host artifacts are being
synced before exact-host retirement; the Clef host remains warm for native batching.
The USD 18 reservation remains separate until final provider reconciliation.

R001 evidence packaging repair: the v1 matrix appended a text segment after the
image. Cloudflare requires one literal text segment and PPLX disallows text after
the image, so these transport failures are not model-quality failures. V2 retains
the exact original state text as a prefix, followed by a newline and the same
source-only numeric JSON, then the unchanged image. All 288 corrected bodies
passed the actual native adapters' CPU-only input admission. Feature values,
questions and image bytes are unchanged, but presentation versions are reported
separately. Failed v1 outputs remain retained. The coordinator retired the original
PPLX host before this status audit; a bounded recovery environment on the remaining
Clef host avoids another rental allocation. Its CPU/network/disk bootstrap began
at 21:28:57 UTC during the Clef batch sweep, so those timings carry an explicit
contention caveat. Flash's five batch configurations completed beforehand.

Native replica comparisons completed seven 216-input cohorts with identical
choices across replica counts within each model. Flash N1/N2/N4 achieved
518.66/524.55/503.09 region inputs per elapsed minute, despite greater utilization
and model memory. Intern N1/N2/N4/N8 achieved 376.88/491.67/503.53/466.55.
Single-copy true batching is tested separately. Its initial control invocation
used the historical missing-model control manifest and failed before encoding;
the corrected retained control manifest passed all three semantic checks.

The fixed natural identity transfer completed 96 inputs each for Flash and Clef.
Flash's scope-known correctness changed 35/52 to 32/52, wrong decisions 13 to 8,
known abstentions 4 to 12, and insufficient-scope abstention 5/44 to 19/44. Clef
did not improve ambiguity. Qwen9's separate original-prompt natural cohort
completed 96 inputs, with 32/52 scope-known correct and 0/44 ambiguity abstention.
References remain provisional overlapping regions from one page.

R001 recovery checkpoint: all four native models completed the 288-input v2
evidence presentation. PPLX additionally completed a fresh 216-input runtime
control; PPLX and Intern each completed all 48 original and 48 identity controls
at the exact 256/500 px images on the recovery host. The pure-adapter admission
repair resolved the three native v1 transport failures. V1 Intern/Qwen and v2
remain separately labeled presentations; no failed attempt is discarded.

Single-copy batching completed ten 216-input configurations. Flash preserved
every decision at every batch size. B2 improved warm throughput by 8.1% over
new-path B1, but worker-inclusive throughput by only 0.9%; larger batches slowed.
Clef B2 retained its aggregate score but changed two decisions; B4/B8/B16 lost
known-case accuracy. Initial Clef timings overlap environment bootstrap. Two
bounded B1/B2 repeats after all other work finished check that timing concern,
retaining both passes. No new model/evidence experiments are admitted after those
repeats; final artifact sync and exact-host retirement follow.

R001 cleanup and accounting: all five created instances are deleted and provider
absence was verified at 2026-10-09 21:43:17 UTC, before the independent deadline.
All outputs were synced before retirement; 53 compressed archives have a retained
SHA256 index. The scoped task SSH private key was removed. The all-charge-type
provider receipt reports USD 9.713, including GPU, disk and bandwidth. R001's
USD 18 reservation was replaced, not supplemented, by that charge; USD 8.287
was released. Prior rows remain byte-equivalent as parsed records. Conservative
cumulative accounting is USD 28.5288416248 of USD 100, including the unchanged
USD 6.05 older unresolved reservations. Posted charges are not invoice-finality
claims. See `bench/results/remote-gpu-costs.md`.

R001 settlement follow-up: a later provider check raised the posted whole-wave
charge from USD 9.713 to USD 9.727 (USD 0.014 additional settlement after deletion).
The original receipt is immutable and retained in ledger amendment history. The
newer positive charge replaces the old amount; conservative campaign accounting
is now USD 28.5428416248, including unchanged older reservations. The released
R001 reservation is USD 8.273. No instances remain.

R001 final verdict: the corrected evidence matrix completed 1,152 native inputs
with no schema or worker failures. Same-host recovery controls pair PPLX and
Intern at the exact image sizes and wording. Added geometry/pixel measurements
produce mixed known-answer changes, while ambiguity abstention remains 0–2/8;
this is not a general evidence-sufficiency solution. V1 Intern/Qwen retain their
separate valid results and the three native input-refusal cohorts remain visible.
The v1 PPLX failed-run hourly metadata was corrected to its actual USD 1.375 host
quote; no inference rate or cost was assigned to those refused requests.

All work for this bounded GPU wave is complete. The next-wave breadth-preserving
plan is documented but unexecuted in `bench/EXPERIMENT_PLAN.md`. Local validation:
259 targeted CPU tests passed; Ruff and strict mypy passed for the new benchmark
helpers/tests. A documentation-only cherry-pick conflict was resolved by keeping
the explicit OMP_NUM_THREADS values, followed by a clean diff check.

## P001 — complete PDF pipeline, active DEV screening (2026-10-09)

The user authorized another USD 50, raising the cumulative cap to USD 150.
The shared ledger retains all prior charges and unresolved reservations; P001 has
its own USD 50 ceiling. Three gpt-6.1-sol/medium worktrees implemented and audited
corpus/scoring, full-page assembly, and bounded row edits. Only root sends paid
requests. Hosted APIs avoid idle GPU rentals in this wave; local work is CPU-only.

The frozen corpus contains 181 physical pages, 168 scored (35 positive and 133
negative), plus 13 diagnostic pages. The predefined pilot has 16 positive and 16
negative pages. Dataset SHA-256:
`3a1268f1d731a7c60a3fa91f1e90e887c3f41a84aec05beed81b797253afa9b2`.
Source projection strips filenames, family labels and private references from
model evidence. Final outputs preserve every extracted source ID once, with
explicit table cells/spans and remaining source text. This invariant is separate
from semantic correctness. Protected held-out files remain untouched.

Initial complete-pipeline observations: PPLX/512 recovered 15/16 positive pages
with four false-positive negative pages; Clef Flash/512 recovered 5/16 with none.
PPLX/256 and Luna/256 or /512 also recovered 15/16 with four false-positive pages.
All calls are fresh transmissions; provider cache usage remains in retained
responses. PPLX/512 completed 54.6 output pages/minute and 10,206 output pages/USD
at USD 0.00313544 reported charge. Output throughput does not mean all outputs
were semantically correct. Positive reported charges take precedence; Luna's
reported zeros use labeled current-catalog estimates from reported tokens.

Next frozen derivatives test source `/Rotate` normalization, independent semantic
admission before candidate choices, and adaptive evidence/repair routing. See
[the P001 plan](bench/PIPELINE_EXPERIMENTS.md) and
[the complete comparison](bench/results/pipeline-p001.md) for all successes,
failures, candidate ceilings, family slices, CPU/RSS and cost scopes.

P001 second checkpoint: orientation normalization recovered the missing rotated
pilot table, reaching 16/16 positives. Independent admission reduced PPLX negative
false-positive pages from four to one. Minimal, relational and reading-order
premises all retained that one error; more evidence alone did not resolve it.
Luna's 1024-pixel gate also reached 16/16 positives and one negative false positive.
Bounded row edits recovered 10–11/16 positives with 5–6 false-positive pages;
adaptive repair routing recovered 10–12/16 with 4–6 false-positive pages. Those
losses remain in the comparison and are not promoted.

The normalized text-only PPLX arm retained 16/16 positives and four false-positive
pages, matching its 256-pixel assembly arm with less input cost. Clef Flash lost
all positive tables without pixels, compared with 5/16 at 512 pixels before
normalization. The latter comparison changes orientation as well as images and
is not a pure matched pixel ablation. Image utility is model-dependent.

Matched 512-pixel Anthropic candidate-selection controls completed: Haiku scored
29/32 exact pages (16 positive, three negative false positives); Sonnet and Opus
each scored 32/32. Their sources, candidate sets and images match byte-for-byte.
They constrain the same source-derived menu, not unrestricted frontier extraction.
The selective PPLX gate plus Sonnet review reached 32/32 using one review call,
61.28 output pages/minute and 3,128 output pages/USD, versus direct Sonnet's 18.23
and 110 and Opus's 13.01 and 56. This compares complete configurations with
different image sizes and routing, not equal-input model ability. Review thresholds
were chosen after observing DEV misses; this is exploratory, not confirmation.

The expanded full-corpus runs include CPU OCR, rotation normalization, independent
admission, review, all three frontier controls and the lower-performing adaptive
and Flash arms. Source-only OCR recovered literal text on one of three empty-text
pages; the other two remain unsupported. The recovered table exposes a proposal
placement gap, motivating a separately versioned column-consensus experiment.
CPU OCR uses four RTen threads; no local GPU or rented host is used.

An offline HTML demo shows a wrapped borderless table reconstructed from its PDF
with native baseline, final JSON/Markdown and source ownership. Source and raw
outputs remain ignored artifacts. Three worktrees independently audit candidate
gaps, paired-input fairness and output integrity. Targeted validation at this
checkpoint: 207 CPU tests passed; new pipeline modules pass Ruff and strict mypy.

P001 full-corpus checkpoint: model-only normalized PPLX assembly recovered 34/35
positive tables but produced tables on 27/133 negative pages (140/168 exact scored
pages). Independent relational admission retained 34/35 positives and reduced
negative false positives to four (163/168 exact). Adding a second reading-order
view worsened this to nine false positives. Luna's 1024-pixel gate retained 34/35
with six false positives; Flash/512 retained 22/35 with five. The adaptive local
repair route retained 28/35 with 30 false-positive pages. Speed and cheap calls
do not compensate for these quality losses.

Conditional Sonnet review completed the full cohort at 34/35 positives and zero
negative false positives: 167/168 exact scored pages, 178/181 operational outputs,
12 Sonnet reviews and 78 PPLX calls. Its positive provider charges total
USD 0.10731194; complete output rates are 72.38 pages/minute and 1,658.72 pages/USD.
The three operational failures are diagnostic-only (two pages without recognized
text and one malformed native span grid). The remaining scored miss has correct
OCR strings but no exact baseline placement alternative. These are correlated
authored DEV results, not generalization estimates.

The independent gap audit found 21/27 wrong direct-assembly selections had top
choice scores at least 0.8. In contrast, the separate admission task exposes the
prose ambiguity more usefully. Choice scores remain task-dependent, uncalibrated
signals. Gate review is assessed by resulting extraction quality, not confidence.

Three worktrees produced another experiment layer: optional source-only column
consensus (complete candidate ceiling rises from 34/35 to 35/35), lossless compact
packets (one of three formerly oversized diagnostic assembly packets now fits),
and stricter Markdown/report verification. Original candidates and configurations
remain retained. The new options are separately frozen and tested before combined
arms. At this checkpoint 240 targeted CPU tests pass; all 12 pipeline modules
pass strict mypy and Ruff. No local GPU or rented host is used.

The full Sonnet control finished at 166/168 exact scored pages, 34/35 positives
and zero false-positive tables, with 174/181 complete outputs. Its one additional
scored failure exhausted the 1,024-token answer limit entirely on provider-reported
reasoning tokens; the response was correctly rejected as truncated. The failed
attempt remains charged. Haiku completed 149/168 exact scored pages with 18
negative false positives. All 175 retained Sonnet/Haiku requests match after
removing only the model field; source inventories, candidate menus and images
also match. Reviewed PPLX uses different routing and 256-pixel images, so its
better complete-pipeline rate is not an equal-input model-ability claim.

Three independent read-only audits verified frozen inputs/code, source ownership,
retained JSON/report equality and exact Markdown reproduction. Their ten-run
snapshot contains 1,770 successful outputs from 1,810 page attempts. Compact
encoding roundtrips all 180 admitted source/candidate snapshots exactly; its
effect on model selection remains an experiment, not an assumed improvement.
Validation at this checkpoint: 258 targeted tests pass, repository-wide Ruff
passes, `mypy src tests` passes for 187 files and all 12 pipeline modules pass.

P001 full frontier controls are complete. Opus reaches 167/168 exact scored
pages, 34/35 exact positives and zero negative false positives, at 13.02 output
pages/minute and 56.32 pages/USD (USD 3.107012). It abstains on the OCR table
whose exact assembly is absent. All 175 retained request bodies across Opus,
Sonnet and Haiku match after removing only the model field; source inventories,
candidate menus and image hashes match as well. The frontier transport uses a
1,024-token answer ceiling, with all reported reasoning tokens charged.

The vector-first PPLX cascade retains 34/35 positives but still makes 27 false
tables, matching direct assembly's 140/168 exact scored pages. Native grids alone
do not solve prose admission. The separate column-consensus gated arm now selects
35/35 exact tables and 437/437 cell slots, with the same four negative false
positives as its baseline gate. This is actual selected quality, not the earlier
candidate oracle. It emits 178/181 outputs at 114.12 pages/minute and 25,915.71
pages/USD, costing USD 0.00686842.

Combining column consensus with the original-format independent gate and selective
Sonnet review reaches 168/168 exact scored pages: 35/35 tables, 437/437 cells,
35/35 span structures and zero negative false positives. It emits 178/181 outputs
at 72.36 pages/minute and 1,725.88 pages/USD. Total provider-reported cost is
USD 0.10313574: 79 PPLX calls cost USD 0.00650174 and 12 Sonnet reviews cost
USD 0.096634. The two empty OCR sources and invalid native grid remain explicit
diagnostic failures. This DEV-selected combined pipeline improves on the original
frontier pipelines with different candidates/routing; it is not evidence that PPLX
alone is a stronger model. Compact evidence and cheaper review controls continue.

Standalone wrapped-table and OCR-table demos were generated from complete full
runs and visually checked in the collaborative browser. The OCR example now places
the recovered strings in their correct columns, preserving its intentionally empty
last cell. Raw demos remain local ignored artifacts. The plan documents mixed
vector/borderless pages and narrower uses of rolling-row edits as next experiments;
those additional coverage claims are not implied by this single-table DEV cohort.


### P001 final layer and completion — 2026-10-10 UTC

All 56 configurations finished: 31 balanced 32-page pilots and 25 full 181-page
runs. Three parallel worktree agents developed and audited source-only assembly,
corpus/scoring, and bounded edits. Paid requests remained root-coordinated and
serial for comparable end-to-end timing. No local GPU or remote rental was used.
The complete comparison is in `bench/results/pipeline-p001.md`; conclusions,
limitations and final accounting are in `bench/results/pipeline-conclusions.md`.

Lossless compact evidence is a measured regression: original gated PPLX has
34/35 exact tables, while compact has 31/35. Source/candidate inventories and
admission answers match; three wrapped companions change from four complete rows
to seven sparse rows. Packet length falls about 39%, but indirect indexed cell
references obscure composed strings. Columns plus compact recovers the OCR table
but retains these three losses. Text-only compact falls further to 28/35 and five
negative false-positive pages, versus 31/35 and four with 256-pixel images.

The cheaper Haiku-review substitution worsens negative false positives to ten;
one PPLX admission HTTP 500 also leaves its total expense unknown. Direct Sonnet
with columns and compact packets reaches 159/168 exact scored pages, 33/35 tables,
two negative false-positive pages and 166/181 outputs. Nine responses truncate
under the fixed 1,024-token answer limit. Its complete attempted cost is
USD 1.463274, including unsuccessful calls; successful-call subtotals alone are
not its cost. Both losses remain published.

The final derivative retains literal coordinates and composed cell values while
deduplicating shared cells. With columns, PPLX admission and selective Sonnet
review, it recovers 35/35 exact tables, 437/437 cells and 35/35 span structures,
with zero negative false positives: 168/168 scored pages and 178/181 outputs.
It costs USD 0.1014482 (79 PPLX calls plus 12 Sonnet reviews), measuring 71.71
output pages/minute and 1,754.59 pages/API USD. CPU time is 65.06 seconds; sampled
peak RSS is 539,107,328 bytes. All 178 comparable source/candidate inventories
match the original reviewed column arm. This ties original-format quality; the
small single-run cost change is not established as repeatable. Two empty OCR
sources and one invalid native grid remain diagnostic failures.

An inspected provider HTTP 500 received exactly one scoped replacement in the
readable run. Ledger entry 17423 records `retry_of_index=17158`; its positive
reported charge is USD 0.00002982. The old USD 0.30 reservation remains unchanged.
Tests cover exact request matching, fresh reservations, one-use consumption and
rejection of unrelated failures. Gateway rejects this optional OpenRouter-only
permission. No automatic retry or local response replay was enabled.

Final P001 accounting: 3,127 attempts; USD 7.728498482 positive reported charges,
USD 0.09586 catalog estimates for 330 reported-zero Luna attempts, and USD 0.30
unresolved reservation. Known charges plus estimates are USD 7.824358482;
conservative wave accounting is USD 8.124358482 of USD 50. Cumulative conservative
accounting is USD 36.6672001068 of USD 150, including USD 6.35 of retained old/new
unresolved reservations. Actual total expense remains incomplete. All 857
Anthropic responses report zero cached input tokens; 2,269 retained decision-model
responses omit that field and remain unknown. All paid jobs have finished.

Validation: 300 targeted CPU tests passed; repository-wide Ruff and strict mypy
for source, tests and pipeline modules (201 files) passed. Reports verify frozen
source/code, complete JSON source ownership, and byte-exact Markdown reproduction.
Wrapped-table and corrected OCR-table offline demos were visually checked. The
heldout set was untouched. Single-table authored DEV results do not establish
natural-document, semantic, multipage or mixed-table generalization. Next tests
are documented; no additional paid run is started by this completion checkpoint.


## P002: broad generalization wave — 2026-10-10

User authorized up to five hours and up to four parallel workers; runtime capacity
allows three worker agents alongside root. Work starts at 02:19 UTC, with final
reporting due by 07:19 UTC. This wave has a USD 50 ceiling within the existing
USD 150 cumulative authorization. Starting conservative accounting is
USD 36.6672001068. Plan: `bench/GENERALIZATION_PLAN.md`.

Frozen new DEV corpus: 276 pages, comprising 156 authored stress pages, 64 fresh
metadata-stratified OmniDocBench raster carriers and 56 licensed native diagnostic
pages. The official source annotations remain separate from model evidence.
Revision r2 corrects 12 authored RGBA carriers accidentally flattened onto black;
all page IDs and references remain stable and the first snapshot is preserved.
A separate metadata-selected natural16 screen has 12 positive and four negative
pages, with 53 reference tables. No official annotations are edited to fit output.

The old whole-page reviewed pipeline emits nine of 16 natural-page outputs;
seven fail source/packet admission. It recovers no complete reference tables and
only one geometrically matched table. Independent region processing alone still
emits nine outputs with seven oversized packets. Raising only the bounded readable
packet admission to 80,000 characters produces 16/16 outputs but still no complete
reference tables. It recovers one exact topology and 320/2,333 correct structure
cells, but only four exact text cells. Thus removing a runtime blocker does not
establish extraction quality. The live PPLX catalog advertises 262,144 context
tokens; the new limit retains complete evidence and preserves the old default.

Geometry-only candidate audits found zero exact natural tables in the original
menu. The source-only generative alternative therefore asks a bounded chat model
to assign existing IDs to rows, columns and spans; values are rebuilt locally and
all unused words remain in prose. Invented IDs, overlap, duplicate ownership and
truncated answers fail validation. Direct Sonnet generation is running as a
separate measured control; it cannot repair missing OCR characters.

The raster-rule prototype independently recovers three exact natural topologies,
106 exact text cells and 143 structure cells from pixels plus OCR source words.
One 9x9 table has 79/81 exact cells. These are candidate diagnostics, not accepted
end-to-end extraction. The full pipeline will require semantic admission before
accepting pixel grids. A Cambridge source/reference disagreement (visible/OCR
German eszett versus annotated Greek beta) is retained as suspected annotation
noise, not normalized away or claimed correct against official gold.

Corrected native-r2 baseline: 270/276 complete outputs, six failures. Natural images
have no native vector tables; authored tables account for 120 exact tables. CPU
OCR and source limits remain explicit. All raw data, frozen requests, outputs,
resources and reports live under ignored `pipeline-p002/`; only code and aggregate
summaries are committed. A procedural discovery incident listed two protected
filenames; no protected contents or scores were read and further discovery uses
explicit DEV paths. See the plan for the retained audit note.

At the first integration checkpoint 291 targeted CPU tests and Ruff pass. Source
and report paths retain complete output ownership, literal cell values, exact
Markdown reproduction, all-attempt costs, and separate positive/negative scores.
Private main checkpoint 3ef1e4a was pushed; no public remote or package publication.


### P002 layer 2: natural evidence, topology, and recovery (2026-10-10 04:12 UTC)

The source-ID Sonnet arm completes all sixteen natural pages, recovers two complete
tables on one exact positive page, ten exact topologies, and 295 exact text cells.
It also produces seven extra tables and one negative false-positive page. The
whitespace OCR treatment preserves recognized spaces but reduces aggregate exact
text cells to 236 and has one invalid anchor collection. Keeping recognized spaces
alone is insufficient. Compact matrix answers lower Sonnet charges from USD
1.201256 to USD 0.966024 but lose structural/text coverage; two returned
`content_filter` finishes are charged failures, not output-token truncations.
Haiku matrices complete all sixteen pages for USD 0.0709715, with two complete
tables, 240 text cells, three extras, and no negative false-positive pages.
All rates and cohort denominators are in `bench/results/generalization-p002.md`.

Posthoc density inspection finds 39/53 tables and 1972/2333 cells on two newspaper
pages. Both remain in every primary score. Whole-page downsampling, OCR coverage,
and fragmented candidate regions limit their recovery. CPU YOLO table proposals
plus source-ID Sonnet improve text cells to 341 and reduce charges to USD 0.286868,
with two complete tables and one provider refusal. Multi-scale 2x2 and 3x3 detector
experiments preserve every source ID and retain boundary flags. More proposals
also introduce fragments and overlapping ownership candidates; counts are not
quality scores. Tiling and direct image transcription are separately frozen next
arms. YOLO weights remain a research-only optional AGPL dependency.

Raster contrast/polarity and bounded gap repair improve controlled shapes from
7/22 to 19/22 but fail to improve complete natural tables and trigger inventory
refusals on dense pages. Original baseline output equivalence holds on 46 inputs;
the original detector remains default. Capacity row stitching offers ten joins
without increasing complete natural candidate coverage; it remains outside the
pipeline default. Lossless array evidence reduces packet bytes 15–16%; optional
quarter-unit coordinates reduce bytes 57–58% with maximum 0.125-unit error. Those
are serialization measurements, not token charges or model-quality results.

Confirmed operational fixes: native merged spans now use retained slot anchors,
covering all 1478 diagnostic native table slots; region processing handles the
oversized source page. Full-r2 native coverage improves from 270/276 to 272/276,
with identical 120 complete authored tables and zero natural-image tables. Four
remaining diagnostics have no extracted or recognized text; their images and
warnings remain visible. Page rotation is preserved for OCR by the new native-only
normalization mode. Frozen orientation probes choose all sixteen construction
angles correctly, with four-pass costs charged and uncertain choices abstaining.
These authored probes do not establish a calibrated orientation probability.
OCR admissions now distinguish 4096 recognized boxes per call from 65536 complete
page words and a 4 MiB character boundary. Original 150/300 DPI dense observations
are preserved; higher resolution more than doubles word inventory on one page
while taking about 2.3–2.5 times longer. Accuracy is separately evaluated.

The user interruption terminated the first Haiku anchor run after four pages.
Twelve intended pages remain missing in that run, its whole-run resource data is
unavailable, and one unresolved USD 0.30 reservation remains in the ledger. Fresh
runs have distinct identities and no local response replay. At 04:12 UTC P002
reported charges total USD 4.28593154, with USD 0.30 interrupted and USD 0.30 active
reservations; this is a checkpoint, not final accounting. No GPU was rented or used.

A resumed worker's scoped file listing also exposed the protected directory's
AGENTS.md filename. No protected file contents, documents, or scores were read.
This second filename-only procedural incident is documented alongside the first;
subsequent workers receive explicit file paths and no broad file discovery.
Tests, code snapshots, exact Markdown verification, and separate model-transcribed
provenance remain required. Raw PDFs, images, requests, responses, and ledgers stay
ignored locally. Only code and aggregate reports are pushed to private main.

### P002 checkpoint: 2026-10-10 04:41 UTC

Natural16 comparisons now include strict whole-page image transcription and
matched YOLO matrix controls. Sonnet at 1200 pixels admits 15/16 outputs and
recovers 3/53 complete tables, 299/2333 exact text anchors, no extra tables, and
2/12 exact positive pages: 6.51 output pages/min and 106.65 pages/API USD at
USD 0.140648. Haiku admits 13/16, recovers 2 complete tables and 245 anchors for
USD 0.0085084, or 6.41 pages/min and 1527.90 pages/API USD. These are table-only,
model-transcribed controls with zero source-conservation claims. Source-owned
YOLO + Haiku costs USD 0.0234843 versus Sonnet's USD 0.286868, but returns 258
rather than 341 exact text anchors and adds one negative-page false table. Both
have two complete tables and one failed page. Failures and charges stay included.

Whole-page 2048-pixel JPEG90 controls reject five requests before inference,
including both dense newspapers; those results cannot answer whether larger images
improve their extraction. A separately measured source-only codec comparison finds
JPEG quality 50 fits all sixteen at the same 2048 dimensions. Quality 70 fits
fourteen. New quality-50 runs and strict 1024-pixel detector crops are queued with
fixed settings. No adaptive resize or silent retry is used. Crop verification
replays all detector proposals and each raw response before exact Markdown checks.

Fixed-edge CPU OCR tests on identical images embedded at physical scales 0.5/1/2
produce identical pixels, text and normalized boxes at 2048 pixels. Fixed 150 DPI
changes whitespace and geometry. These legible authored controls show encoding
invariance, not an accuracy win: their text is recoverable in both arms. Detailed
wall/CPU/RSS measurements and the row-major versus cell-center scoring distinction
are retained in `bench/results/pipeline-ocr-scale-audit.md`.

Frozen format-repair counterfactuals are rejected as a default. Authoritative
Sonnet anchors improve 299 → 317 after clipping one out-of-range normalized bbox,
without another complete table. Haiku stays at 245 anchors while padding a ragged
row admits a false table on a negative page. The earlier auxiliary slot score is
explicitly separate from the 2333-anchor primary protocol. Strict parsers remain
unchanged. Detector containment fusion, row-wrap/column-track prompt variants,
and shorter ordinal response indexes are new opt-in hypotheses with explicit
source ownership and no reference-derived routing.

The complete 276-page model-assisted Haiku expansion is running, with its choice
fixed before those additional outcomes. CPU-only checks passed: 528 earlier
pipeline/generalization tests, then 89 focused integration checks. The full suite
had 3174 passes, 14 skips, two expected failures and twelve setup errors from an
unconfigured mise rustc shim. Selecting the already installed rustc explicitly
made all thirteen color-region tests pass; no system configuration was changed.
Concurrent local test/audit workloads are part of this research environment and
limit isolated latency comparisons.

P002 has 529 reserved/returned attempts at this checkpoint, USD 4.97082344 in
positive provider-reported charges, the preserved USD 0.30 interrupted reservation
and USD 0.30 active reservation. Conservative P002 accounting is USD 5.57082344;
reservations are not charges. No local GPU, remote GPU or rented host was used.

### P002 checkpoint: 2026-10-10 05:04 UTC

The fixed full276 Haiku expansion now has 270 verified complete source-owned
outputs, 166/249 complete tables, 6,329 exact text anchors and 136/172 exact
positive pages. Reported API charges are USD 0.1275912 for 119 calls; throughput
is 12.64 output pages/min and 2,116.13 output pages/API USD. The native regional
baseline has 120 complete tables, 4,258 exact anchors and 96 exact positive
pages, with 272 outputs and no API calls. Four unsupported diagnostics persist;
two model responses end at their output limit and fail atomically.

The cohort distinction matters: Haiku recovers 155/156 authored tables but only
11/93 natural tables. It also invents tables on eight authored negative pages
(six prose, two decorative) and one natural negative. The additional 48 natural
DEV pages contribute 9/40 complete tables and 1,041/1,514 exact text anchors,
without operational errors or extra tables. These pages extend the fixed screen;
they are not protected confirmation data. The complete negative audit retains
all 48 negative pages, including correct negatives, and all positive-family
aggregates. Simple line density, token length and punctuation observations
overlap positives and negatives; no threshold was fitted to this audit.

Matched natural16 YOLO + Haiku at 1024 pixels does not improve the 512-pixel arm:
outputs fall from 15 to 14, exact anchors from 258 to 247, and complete tables
remain 2/53. Both new failures are local frozen request admission, including
one dense newspaper. This is a coverage result, not proof that higher-resolution
pixels are unhelpful when admitted. Higher-DPI OCR plus compact evidence, fixed
JPEG50 whole-page controls, detector crops, static row-wrap/column-track prompts,
ordinal source indexes, PPLX admission gates and native/image hybrid runs remain
separately identified comparisons in the serial queue.

The retained full276 profile attributes 62.83% of summed page wall time to API
calls, 29.07% to source extraction including OCR, 6.37% to layout detection and
1.73% to other work. Parent totals are 1,281.413 s wall, 1,288.233 s CPU and
758.383 MiB sampled peak RSS. Detector worker CPU is separately 256.538 s and
peak RSS 1,187.758 MiB; these asynchronous peaks are not added. A verified
native-only detector shortcut has zero eligible pages, so it is not integrated.
An isolated, mocked concurrency prototype is being evaluated without changing
the paid queue. Compact row-continuation evidence is another source-only
experiment, with its generic specification frozen before outcome stratification.

Hybrid output verification now independently replays native quarantine, physical
grid bounds, detector exclusions, both child outputs, raw model responses,
source accounting and exact composed Markdown. Model-transcribed values remain
explicitly distinct from source-owned text. The latest 82 focused tests pass;
full mypy passes on 218 source files. At this checkpoint P002 has 632 attempts,
USD 5.09574214 positive provider-reported charges and the preserved USD 0.30
interruption reservation. Active reservations are transient and reported by the
live ledger. Local work remains CPU-only; no host is rented.

### P002 checkpoint: 2026-10-10 05:36 UTC

The strongest natural16 exact-cell result is now Sonnet with fixed 1024-pixel
YOLO crops: 982/2,333 exact anchors, 5/53 complete tables, all sixteen outputs,
no extra tables, 6.88 output pages/min and 69.41 pages/API USD. Haiku crops recover
687 anchors and four complete tables, with fourteen admitted pages, 8.57 pages/min
and 1,538.73 pages/API USD. Two malformed Haiku pages fail atomically. Whole-page
2048-pixel JPEG50 Opus returns 300 anchors and three complete tables at 6.84
pages/min and 34.59 pages/API USD. Sonnet crops beat that Opus configuration on
both micro exact-cell count and positive-page macro recall; Haiku crops beat its
micro count but lose on page-weighted recall (52.90% versus 62.01%). These are
single DEV runs, not a general model ranking.

Matched source-owned Haiku prompt controls expose a density tradeoff. Repeated
column-track instructions increase exact anchors from 258 to 332, remove the
negative false table and admit all sixteen pages, but lose 27 anchors on the
remaining fourteen pages while gaining 101 on the dense pair. Row-wrap wording
falls to 231 anchors. Short ordinal identifiers admit all sixteen and recover
311 anchors, retaining one negative false table. Complete-table recovery stays
at two for each control. No reference-derived per-page selector is introduced.

A frozen placement-free complete-string diagnostic consumes duplicate strings
once and keeps every failure in the denominator. Sonnet crop inventory rises
from 982 exact-position anchors to an optimistic 1,146 when placement is ignored;
Opus whole-page rises from 300 to 599. Every gain is on the two dense pages.
Even this optimistic inventory misses more than half of all reference anchors,
so placement repair alone cannot solve the coverage/transcription deficit.
See `bench/results/p002-cell-inventory.md`; this diagnostic supplies no inference
context or fitted repair rule.

Multiscale detector crops, larger JPEG50 crops, the matched 768/512/400-pixel
crop sweep, generation/gate row-context arms, semantic negative filtering and
native/image hybrids remain explicit independent runs in the bounded serial
queue. Four-worker whole-page Haiku is a final separate throughput control;
mocked thread/process races have proved atomic cumulative and wave admission,
unique reservations and preservation of failed settlements. It must run after
legacy serial requests, and overlapping per-call CPU time must not be summed.

The complete CPU-only suite now passes: 3,430 passed, 14 skipped and two expected
failures. Mypy passes on 226 source files. The rustc shim setup issue is resolved
for these tests by selecting the installed compiler per command. No local GPU
or rented host is used. At 05:36 UTC, P002 has 828 attempts and USD 6.1845728 in
positive reported charges, plus the preserved USD 0.30 interrupted reservation
and USD 0.30 active reservation: USD 6.7845728 conservative accounting. Raw
artifacts remain local; only code, protocols and aggregate reports are pushed.

### P002 checkpoint: 2026-10-10 06:00 UTC

Matched Haiku crop edges 400/512/768/1024 recover 225/290/403/687 exact anchors
and 3/2/3/4 complete tables on the same sixteen pages. Smaller edges admit all
sixteen outputs; 1024 admits fourteen. Dense-page exact counts are 0/2/110/416;
remaining-page counts are 225/288/293/271. Rates are 8.49/9.80/9.87/8.57 pages/min
and 1,779.68/1,979.73/1,849.20/1,538.73 pages/API USD. No per-page image-size
selector is fitted. Single fresh replicates do not isolate stochastic latency
or response-shape variation from image effects.

The complete native/image hybrid pilots expose that variability directly.
Sonnet's standalone crop run and hybrid pilot have identical proposals on all
sixteen pages, identical complete crop descriptors and all nineteen byte-identical
request bodies, with no native exclusions. Eight response contents match; provider
raw records also contain differing metadata. One fresh dense-page response fails
strict overlap validation, dropping its prior 692 exact cells. Hybrid primary
recovery is 289 instead of 982. Haiku also has all nineteen identical input bodies
and drops from 687 to 289 after a fresh dense-page format failure. These differences
must not be attributed to hybrid composition changing model accuracy. The full276
hybrid runs provide broader coverage and another fresh response set.

A concrete hybrid Markdown bug is fixed: tables without contained source words
could tie a footer's source anchor, then sort after the footer and alphabetically
by table contents. Renderer v2 uses source anchors, display geometry and stable
insertion order. Exact frozen v1 hashes still select the original historical
renderer in verification. Thirty-seven coordinate/ownership/failure tests pass,
including real CropBox, right-angle rotations and later-page extraction. Native-only
v1 and v2 output remains identical on all 272 available sources. A separate scorer
validation fix rejects string matrix rows and non-list span containers under the
existing canonical schema; matching rules stay frozen.

Four-worker whole-page Haiku at 2048/JPEG50 produces 13/16 strict outputs, 216 exact
cells and four complete tables in 25.217 seconds of page-processing wall time:
30.93 pages/min, 1,181.46 pages/API USD and USD 0.0110033 for all sixteen fresh calls.
The serial arm has 14 outputs, 208 cells, two complete tables and 12.43 pages/min.
All input requests match semantically, but fresh responses differ. Independent
review reconciles all UUIDs, charges, response hashes, output ordering and RSS
samples. Process CPU is 17.939 seconds; overlapping per-page CPU intervals sum to
67.538 and are explicitly nonadditive. Timing excludes artifact freezing/client
setup in both arms; it is not complete command-startup time.

The frozen partial-table salvage experiment retains only independently valid,
isolated tables from normally completed responses. It quarantines every member
of an overlap component across all crops, without repairing values, shapes or
boxes. On the failed Sonnet hybrid page this recovers 629 exact cells and adds one
extra table; original complete-page errors and primary scores remain unchanged.
Haiku controls gain 10–47 cells, with two extra tables in the four-worker control.
All eighty intended page/control observations, costs and failures remain retained.
These are explicitly partial review artifacts, not successful complete pages or
new paid runs. See `bench/results/p002-partial-salvage.md`.

The full276 hybrid Haiku run is active. At the latest accounting check P002 has
993 attempts, USD 6.47681702 positive reported charges and the preserved USD 0.30
interruption reservation (active reservations vary). The current code passes
tracked Ruff and full mypy on 229 source files; the earlier full-suite result
remains 3,430 passed/14 skipped/two expected failures, with new focused tests
passing separately. No local GPU or rental is used. T3 preview tabs open, but
snapshot/navigation automation fails on the client; gallery HTML is generated
and tested, with no claim of successful browser visual inspection.

### P002 checkpoint, 2026-10-10 06:34 UTC

Both full276 image/native hybrids completed. Haiku produces 268 operational
pages, 157/249 complete tables and 6,604/8,897 exact cells, with one negative
false-positive page; Sonnet produces 271 pages, 157 complete tables and 6,119
exact cells, with sixteen negative false-positive pages. All sixteen Sonnet
false positives are authored negatives; its natural negatives remain clean.
Reported API charges are USD 0.0397398 and USD 0.838664 respectively. Original
page-processing rates are 18.33 and 16.73 pages/min, and 6,743.87 and 323.13
pages/API USD. All original failures and costs remain in the report.

Six matched-input controls expose response variance. For each model, all nineteen
natural16 crop request hashes match across standalone crops, pilot hybrid and
full276 hybrid. Haiku exact cells vary 687/289/732; Sonnet varies 982/289/287.
Native exclusions and crop descriptors are identical on that screen. Dense-page
normal-stop geometry failures account for much of the variation. These are fresh
requests, not local response replay or evidence of a hybrid architecture penalty.

A generated asymmetric table reproduces physical native matrix order at right-angle
rotations. The committed logical projection uses actual character-weighted baseline
direction, including merged/multiline grids, CropBox offsets and counterrotated
content. Frozen offline replay changes exactly twelve rotated pages in each full
control, restoring 259 cells and twelve complete tables: Haiku reaches 6,863 cells
and 169 complete tables; Sonnet reaches 6,378 and 169. Every model table, physical
box, source ledger, original failure and extra table remains unchanged. These are
secondary corrected-quality observations, with separate local replay resources and
no new throughput/provider-cache claim. See `bench/results/p002-native-orientation.md`.

Independent arbitrary-document testing finds that regional proposal order can
scramble prose despite preserving every word. An explicit original-source-order
renderer restores original word and line metadata without changing model evidence,
canonical states or geometry. The new single-document CLI selects it, keeps original
child artifacts, and writes logically oriented native sidecars with frozen helper
and runtime provenance. Hybrid document modes also select logical native orientation.
Correction failures remain failed pages. Rich native styling remains a separate
public-library path; the experimental assembler emits literal prose and table HTML.

Multiscale Sonnet gains ten actual Table proposals on the dense page previously
missed entirely, but two invalid-geometry responses still reject their whole pages.
Its strict run has fourteen outputs and 293 exact cells. The unchanged partial
salvage specification is now predeclared for all sixteen pages of both multiscale
controls, retaining unsent proposals and partial replies without changing primary
success. Larger crops and row-context/combined-source comparisons remain queued.

Latest P002 accounting: 1,261 attempts, USD 7.82883072 positive reported charges,
and the preserved USD 0.30 unresolved reservation; live reservations can vary.
The newest orientation/source-order/wrapper focused checks pass, including 47
tests in the latest root run. Guarded private-main pushes continue; raw artifacts
remain local. No local GPU or remote rental is used in this wave.

### P002 validation and final control, 2026-10-10 06:55 UTC

The planned serial comparison queue completed. Direct matrix generation with
row context loses 33 exact cells (258 → 225) and one exact topology, keeps the
same fifteen successful pages and two complete tables, and costs about 53% more.
Gate-only row context behaves differently: PPLX gating plus Haiku ordinal assembly
improves from 232 to 336 cells, fifteen to sixteen successful pages, and seven to
zero extra tables, with about 3% higher API cost. Complete tables remain two.
The OCR300/compact-array/ordinal/column-prompt combination reaches 395 cells and
three complete tables, with sixteen outputs and no extra tables. It changes
multiple factors together; the next recorded hypothesis adds gate-only row
context to this combination, but that combination has not been run.

The all-page multiscale partial audit recovers 320 additional exact cells from
Sonnet's failed pages while admitting three extra tables; Haiku is unchanged.
Original page failures, all charges and unsent crop proposals remain retained.
The matched 300-DPI alternate-renderer OCR follow-up examines all four unsupported
diagnostics with three renderers. It consumes more CPU/RAM but does not establish
reliable Unicode recovery; no automatic renderer or OCR substitution is enabled.
See `bench/results/p002-multiscale-partial.md` and `p002-renderer-ocr-300.md`.

The actual arbitrary-document CLI smoke completes four pages and preserves all
145 source words exactly once, fixes rotated native indexing and multicolumn
prose ordering, and correctly marks a two-page subset partial. Frozen helper and
runtime hashes verify. The complete CPU suite passes 3,549 tests, with fourteen
skips and two expected failures in 145.22 seconds. Tracked Ruff and mypy over
235 source files pass. The last portion of the combined OCR control overlapped
CPU tests; its elapsed time has an explicit contention caveat. No heavy CPU
validation continues into the final fresh benchmark.

At 06:52:22 UTC root starts the separately frozen
`full276-hybrid-haiku-1024-logical` after both tests and the serial paid queue
drain. An 18-minute interrupt bound, followed by a 30-second kill grace, preserves
the five-hour reporting deadline. It changes the explicit logical-native flag,
not model pixels/prompts/exclusions. All new response variability and failures
will remain in its own primary scores and measured rates. The old full276 gated
expansion was never started and is explicitly deferred. No other paid arm is
authorized by this final-window plan.

Before that last run, P002 has 1,351 attempts and USD 7.92619116 positive reported
charges, plus the unchanged USD 0.30 interrupted-call reservation. Private-main
pushes include the implementation, tests, plans and aggregate reports; raw
artifacts remain ignored locally. An independent claims audit confirms the
README rates, denominators and corrected-versus-physical distinction, and fixes
one diagram wording error: native proposal exclusion uses overlap, not containment.

### P002 completed campaign, 2026-10-10 07:15 UTC

The final fresh logical-native Haiku hybrid completed normally before the
five-hour deadline. Across all 276 DEV pages it produces 269 operational outputs,
170/249 complete tables, 6,615/8,897 exact text cells, 195 exact topologies and
141/172 exact positive pages. There are three extra tables, including false
positives on two of the 48 negative pages. All 156 authored tables and all 5,050
authored cells are exact. The 64 natural pages remain a substantial limitation:
14/93 complete tables, 1,565/3,847 exact cells and three atomic failures. Four
unsupported native diagnostics also remain failures. Operational success is not
the same as a fully correct page.

The fresh run measures 18.20 operational pages/minute and 6,977.17 operational
pages/API USD, with USD 0.0385543 in 118 positive provider-reported charges.
Page-processing wall time is 886.820288 seconds, parent CPU 1,286.129753 seconds
and sampled parent peak RSS 873,086,976 bytes. RSS is sampled every 100 ms.
The separate detector worker uses 5.25327 startup CPU seconds and 240.982 request
CPU seconds, with a maximum sampled request RSS of 1,252,999,168 bytes. Parent
wall includes detector work; CPU and RSS scopes remain separate and peaks are
not summed. Local GPU and remote inference hardware utilization are unmeasured;
no local GPU or remote rental was used in this wave.

The source-only identity audit confirms identical native boxes, detector
proposals, exclusions and crop descriptors across all 276 pages, plus identical
hashes for all 118 retained requests, versus the physical-order Haiku control.
The natural16 subset likewise has 19 identical requests. Its changing scores
reflect fresh response variability. The deterministic paired offline correction
remains separate: it recovers 259 authored cells without changing any model
response. Fresh natural results must not be credited to that correction.

Final P002 accounting retains 1,469 attempts, 1,468 positive provider-reported
charges totaling USD 7.96474546, and one unresolved interrupted-call reservation
of USD 0.30. Cumulative conservative accounting is USD 44.9319455668, including
prior charges, reservations and historical rental, against the USD 150 cap.
All paid work has stopped. These amounts distinguish charges from reservations;
API throughput excludes local compute cost.

The final implementation passed 3,549 tests, with fourteen skips and two expected
failures; tracked Ruff and mypy over 235 source files passed. Only documentation
changed afterward. The arbitrary-document CLI, four-page actual smoke output,
source-order and native-orientation fixes, strict failure reporting and optional
partial-review artifacts are documented in the usage guide and final report.
The full276 gated expansion and combined OCR300/ordinal/column-prompt plus
gate-row-context hypothesis remain explicitly unrun. This completes the bounded
research campaign, not a claim of reliable extraction for every PDF family.

### P003 authorization and first layer, 2026-10-10 18:50 UTC

The user authorized an additional USD 50 and eight hours for decision-model
research. P003 starts at 18:27 UTC, stops new paid admissions at 02:12 UTC and
finishes reporting by 02:27 UTC on October 11. The cumulative cap is USD 200;
the independent P003 cap is USD 50. Shared ledger admission checks enforce its
deadline and include unresolved reservations across OpenRouter and Gateway.
An arm stops paid admission after its first transport failure. Existing history
and the USD 44.9319455668 conservative starting balance remain unchanged.

The predeclared contract is `bench/DECISION_RESEARCH_P003.md`. Three disjoint
CPU-only agents implement bounded local row decisions, generic OCR/raster region
proposals, and independent scoring. Public catalogs were refreshed and exact
model IDs, modality, provider-route and price evidence retained. New candidates
include Clef Omni, Microsoft Decision-1, Drex and seven economical multimodal
chat models. No GPU rental or local GPU is used. All source tuning remains DEV.

The first fresh OCR300/compact-array/ordinal/column-prompt control produces all
sixteen operational pages, 3/53 complete tables, 397/2333 exact text anchors and
384 span-aware exact anchors. It has no negative-page false positives and one
extra table. Parent elapsed time is 390.9945 seconds, CPU 777.3788 seconds and
100-ms sampled peak RSS 748,339,200 bytes; detector subprocess measurements remain
separate. All eighteen calls report positive charges totaling USD 0.0203311:
2.4553 operational pages/minute and 786.97 pages/API USD. This is a single DEV
screen, not evidence of an improvement over the preceding similar control.

The fixed source-template compatibility probe succeeds on thirteen of fourteen
text decision routes. Span again returns HTTP 404, preserving a USD 0.30
reservation; no automatic retry is made. All five advertised OpenRouter image
decision routes pass the same typed-answer parser. These probes do not measure
extraction quality or page throughput. Full-corpus gate comparisons follow.

Langfuse prices are refreshed for every admitted exact model ID. The deployment
rejects duplicate names with new start dates, so Clef Flash's changed price uses
the telemetry-only alias `cloudflare/clef-flash@2026-10-10`, with the original
requested ID retained as metadata. Its historical definition stays unchanged.
Reported positive charges still take precedence; zero/missing charges use
labeled catalog estimates with original reported values preserved.

The next layers compare the deferred OCR300 bundle plus gate-only row context,
multiple typed decision routes, native split/join/unresolved boundary decisions,
additional source-only region proposals, and fixed-provider crop transcription.
Candidate reranking against identical pixels is a separate hypothesis targeting
the large response variability observed in P002. Generated candidate costs and
incremental selector costs must remain separate from end-to-end performance.

### P003 first comparisons and evidence treatments, 2026-10-10 19:04 UTC

The matched PPLX gate plus rolling-context bundle ties the OCR300 source-ID
control at 3/53 complete tables and 384/2333 strict cell anchors, with 19.06%
more API cost. The first pinned Haiku crop run yields 393 strict anchors,
3 complete tables, one atomic output failure and one negative-page false
positive. Luna yields 784 strict anchors and 3 complete tables with all sixteen
pages operational and no negative-page false positives. These single runs do
not overcome the response variation observed previously; repeats remain required.
See `bench/results/decision-p003.md` for quality and resource tables.

The optimistic source-inventory audit permits at most 1880/2333 exact whole-token
anchor strings and 9/53 complete tables. This is a necessary bound with arbitrary
order and unlimited token reuse, not an achievable extraction score. It measured
0.391 seconds wall, 0.390 CPU seconds and 92,827,648 bytes sampled RSS. An initial
attempt using unavailable `/usr/bin/time` failed before execution and its error
log is retained; the completed run uses the existing 100-ms process sampler.

New isolated treatments provide source-only OCR/raster region proposals,
strict whole-crop candidate ranking, bounded row-boundary edits, and independent
gate image resolution. Gate packet treatments retain exact words, quarter-point
compact arrays, uniformly sampled 64-word evidence, image-only evidence, or
mechanical reading flow. Specialized admission instructions can be varied
independently from the packet. Existing full-source admission remains enforced.
All proposed source regions require semantic admission before transcription;
proposal counts are not extraction quality. No model sees reference labels.

Luna's zero OpenRouter charge exposed a BYOK accounting omission: positive
upstream charges are nested in `usage.cost_details.upstream_inference_cost`.
The client now records that amount separately and adds it to a known gateway
fee without overwriting the original reported zero. Shared-provider requests
never add upstream costs again. Missing fee data stays incomplete. All nineteen
Luna responses provide both amounts; their combined API-reported cost is
USD 0.012964825, pending independent overlay verification of the original frozen
report. Pricing and telemetry regression checks pass within 200 targeted tests.

### P003 eight-model screen and candidate ceilings, 2026-10-10 19:35 UTC

All eight pinned crop-transcription routes are scored with intended-page and
reference-table denominators intact. Six produce usable model outputs; Qwen
HTTP 429 and Gemini HTTP 400 stop their circuits after one attempted request each.
Luna reaches 784 strict anchors, Gemma 26B: 201, Gemma 31B: 264, Ministral 14B: 263,
Ministral 8B: 252, and Haiku: 393. Complete-table counts remain two or three; the
prior matched Sonnet run retains five. Full quality/cost/resource comparisons
are in README and `bench/results/decision-p003.md`.

Independent Luna cost reconciliation verifies all nineteen retained responses
and resolves its effective API charge to USD 0.012964825 while retaining original
zeros, old reservations and accounting revision history. No old Langfuse
observation was re-exported; new BYOK requests use corrected accounting.

A posthoc whole-crop oracle gives Luna/Sonnet 1,088 strict anchors and five complete
tables; adding Haiku gives 1,097 strict anchors and the same five tables. This
motivates blinded candidate ranking while preserving acquisition improvements.
No gold/quality/model identity is placed in selector prompts. Thirteen new gate
arms run at bounded transport concurrency 3. An initial unsupported CLI argument
failed all arms before inference; logs remain retained and the corrected launcher
now passes a real parser integration test.

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

## P003 broader corpus and spatial mechanisms, 2026-10-10 20:59 UTC

Fresh natural64 baselines retain 64 intended pages, 93 tables and 3,847 cell anchors. Luna returns 63 usable pages, 1,348 strict anchors, 1,358 text anchors, 1,731 structure anchors and 12 complete tables, with zero extra tables and zero negative-page false positives. Ordinal OCR300 returns 62 usable pages, 1,309 strict anchors, 1,329 text anchors, 1,806 structure anchors and 11 complete tables, with 11 extra tables but zero negative-page false positives. Full-generation rates are 5.54 pages/min and 1,985.15 pages/API USD for Luna; 2.69 and 1,013.32 for ordinal, under concurrent load. This broader DEV set includes the original 16 pages and is not held out.

Two ordinal errors are the existing 64-million-pixel raster admission at fixed DPI. The next queue explicitly tests the existing fixed-edge OCR acquisition at 2,048 and 3,072 px. No admission limit is relaxed; old failures remain recorded. A separate offline partial-table audit on natural64 Luna raises strict fragments from 1,348 to 1,828 but adds four extra tables and leaves complete-table count at twelve. Its original failed page remains an operational failure. It has no fresh API rate or cost claim.

The source-only pair-relation prototype conserves word IDs and rejects conflicting or missing pair evidence during complete-link partitioning. Atomic coverage needs 7,508 question batches, making segment compression and uncertainty subgraphs more practical next steps than immediate paid exhaustive inference. A separate CPU Table Transformer experiment now explores explicit row/column geometry conditional on existing detector crops.

The source-frozen valid-region candidate adapter excludes malformed whole crops while admitting valid crops from otherwise failed pages. Independent DEV oracles find no gain from adding fresh Sonnet to the original Luna/Sonnet pool: both remain 1,088 strict anchors and five complete tables. This preserves a useful general admission mechanism without claiming a quality improvement. Investigate compatible row combinations and geometry rather than repurchasing equivalent crop decisions.

Render reuse preserves all 266 crop/image comparisons exactly and reduces local rendering CPU by 6.09–6.18 times in two contended paired passes. It is a separate prototype, not an implicit change to active image experiments. Provider cache usage reporting now separates original retained transcript counters from zero new replay calls and correctly reads nested result usage.

The next predeclared queue contains 62 arms: two complete 276-page baselines; three stronger-model natural64 baselines; fixed-edge OCR; direct-cell versus row-then-anchor decisions; compact, neighbor and band evidence; ambiguity-only placement; small-image repeats, blank/blur controls, opaque candidate order/alias seeds, 500 px controls; and matrix/atomic transcription formats. Plan SHA256 cb78a6179c038254fdaa82dd3ffbbaf3e3503dd6d3c1ab5059498f5f40b1a8a7, seed 194. Six active arms may overlap, with at most three pipeline/candidate workers and three paid transports. Real process and shared-ledger tests pass; waiting reserves no money. All rates must state this contention policy. The USD 50 wave cap and 02:12 UTC paid cutoff remain unchanged.

## P003 independent decisions and fresh confirmation, 2026-10-10 21:24 UTC

The user clarified that each model must be its own experiment, without automatic model substitution or redundant retries. New comparisons preserve model/provider identity, retain failed attempts and abstentions, and schedule any investigated transient retry separately. Original retained candidate outputs must not receive decision-model success credit.

An independent audit now credits only complete crop states actually selected by the model. PPLX at 128 px RGB, fresh repeat, supports 984 strict cells and five complete tables; a matched blank-image control supports 11 cells and no complete tables. Both use all 16 pages, 53 tables and 2,333 reference anchors. Source-image calls select 15 crops and abstain once; blank-image calls select two and abstain fourteen times. Historical retained pipeline scores of 1,087 and 784 remain separate. Incremental processing rates are 4.83 and 3.94 pages/minute, and both cost USD 0.00059822 in reported selector charges (26,746 retained pages/API USD). Rates include no-question/abstained pages and exclude both candidate generations. Six host jobs contend for three paid transports; this does not measure serial or complete-pipeline performance.

The fresh confirmation source freeze contains 32 natural OmniDocBench pages (12 multiple-table, 12 single-table, eight negative), each with a distinct known parent, and 16 new synthetic layouts. Selection excludes 96 known source IDs and 50 known parents; 870 records with unknown parents were ineligible. Selection SHA256 7c28b5e13de6a0012444e40fb5921caec78f3dc67d5819cbcfc33737e214c0a2 preceded acquisition and scoring. The immutable source-only manifest SHA256 is 2548256a5289d64e1a0a5d0de1683c6e068fa8db295fce64814f3bb134664b99. Independent target attachment covers 66 tables, without changing the model evidence or source manifest. Protected silver references remain unused.

Short Gateway protocol controls were run serially after the preceding queue drained. Laya returned a valid left/right answer from a 299-byte request in 1.92 seconds; its reported zero is preserved, with a zero estimate from the frozen Gateway catalog's zero rates. Native d1 text returned the correct relation from a 346-byte request in 1.10 seconds, reported USD 0.00000272. The same d1 control with a retained 512 px image failed HTTP 400 in 1.08 seconds, with USD 0.30 still reserved and cost unknown. No retries or PDF-quality claim. Bounded micro relation packets now retain complete literal words and geometry in 470–730 UTF-8 bytes of state, versus 1,862–2,115 bytes for verbose controls. Independently run per-model probes are next.

CPU Table Transformer inference produced frozen row/column geometry for all 20 detector crops on the original 16 pages. Nine source-only placement treatments completed in 3.59 seconds wall / 3.47 CPU seconds with sampled peak RSS 99,856,384 bytes; this excludes original OCR/detection and structure inference. An initial placement attempt used the smaller model-prompt validator and stopped on dense source data. Its partial artifacts remain; the new attempt uses the existing complete-source validator with a two-MiB boundary, preserving word/slot limits. All 144 outputs were frozen before scoring. Separate adaptive-boundary and physical-line consensus hypotheses contribute 96 additional source-frozen outputs, with literal ambiguity packets and no generated replacement text. Independent quality assessment is pending.

Capacity is measured through CPU counters, sampled RSS and request/admission timing. The existing 40-minute per-arm limit is too short for some complete 276-page runs under shared transport. An authenticated continuation helper admits only untouched missing pages; completed errors and interrupted attempts remain excluded, so completion does not silently repurchase old work. Future queue plans can explicitly declare bounded longer durations, still subordinate to the unchanged 02:12 UTC paid cutoff, and checkpoint resource counters every five seconds. The currently running supervisor retains its original limits. At 21:18 UTC, P003 accounted USD 6.68356 including unresolved reservations, within its USD 50 ceiling; this is not all reported spend.

## P003 geometry losses and completion scheduling, 2026-10-10 21:42 UTC

Independent source/pixel/projection replay preceded reference scoring for all geometry treatments. Original detector crops reach at most 204 strict anchors and three complete tables, with false tables on three of four negative pages. Height-adaptive assignment ties the original maximum-overlap control; physical-line consensus loses two strict anchors at every threshold. Broader acquisition does not rescue this method: whole-page treatments score 7–10 strict anchors and zero complete tables, residual crops score two anchors and zero tables, and residual line/gap proposals score zero strict anchors and zero complete tables. Every treatment keeps the complete 16-page, 53-table, 2,333-anchor denominator. All 432 broader-acquisition outputs remain recorded, including negative-page false positives. See `bench/results/p003-structure-acquisition.md` and `bench/results/p003-structure-placement.md` for all scores and resource scopes.

The structure checkpoint assigns raw table-class probabilities above 0.98 to every original detector crop, including the prose failures. These probabilities do not establish semantic table presence. Next, independently frozen admission probes will compare PPLX, Luna Decisions and Clef on actual retained structure/source/pixel evidence; rejection, abstention or failure yields no predicted table. Admission can remove false positives but cannot repair a wrong cell matrix. Existing thresholds remain separate treatments rather than choosing one from these scores. The council-of-dans review uses three distinct lenses—Architect, Genius Inventor and Performance Wizard—to propose the next layer while retaining losing and moderately promising hypotheses.

The running supervisor's 40-minute limit interrupted ordinal after 195 completed page-result artifacts and Luna after 131, out of 276 intended pages each. An attempted administrative duration update through CPython's own debugger was denied by the OS; no limit, host protection, model or request was changed. The original attempt and refusal receipt remain private. Completed results will be authenticated and reused; serialized errors and partial requests remain excluded from automatic continuation. A root-only postmortem helper releases a concurrency slot only for a proved-dead process group and a request started within that recorded arm interval, preserving every financial field. Retained raw responses continue to block admission pending settlement. A review found those latter two safeguards missing before any real interruption was processed; four synthetic checks now cover the corrected behavior. No financial reservation is released by this helper.

The next batch is staged behind complete paid-queue drain: strict source/code/model-equivalent continuations for untouched pages, alongside all 48 fresh confirmation pages for Luna, Sonnet, Haiku matrix, and ordinal OCR300. Launcher SHA256 8b999916bfd280f113eba1ecb4f17c23bc1d7c9d7ba62e1d058b538a5956fca2; explicit per-arm durations remain subordinate to the original 02:12 UTC paid cutoff. Its dynamic remaining-page manifests are created only from authenticated missing source IDs, without reading references. Six-transport/eight-host-arm capacity support is tested in an isolated commit but remains inactive until strict three-transport continuations finish and root reconciles the ledger policy after full drain.

## P003 continuation admission and broader baseline, 2026-10-10 21:53 UTC

The continuation audit now distinguishes a prepared request file from an admitted request. Root verified that each stopped 276-page process group was absent, captured the shared ledger under its lock, and authenticated the exact original code, source records, artifact inventories and run/page request prefixes. Two pages had exactly one prepared request file and zero ledger entries of any kind. Those two pages may continue without repurchasing an attempted request. Completed failures remain excluded. Ordinal has 81 eligible remaining pages after 191 successes and four completed errors; Luna has 145 remaining after 130 successes and one completed error. The unsupported-no-text outcome is an immutable completed error, not a retry candidate. All 24 focused continuation, interruption and structure-admission tests pass.

The first audit script stopped after ordinal because its Luna arm name omitted `crops`; its artifacts remain. The corrected immutable v2 audit authenticates both arms. Launcher v1 was stopped while still waiting, and v2 is waiting for complete current-queue drain. Both original pipeline code maps still exactly match main. New precomputed continuation manifests and copied root proof/ledger snapshots preserve the zero-admission evidence; no model fallback or inline retry is added.

Independent natural64 Sonnet 5.5 scoring returns 64 usable pages, 1,839 strict cells, 1,851 exact-text cells, 2,505 structure cells and 14 of 93 complete tables. It misses 34 tables, adds four, and produces a false table on one of 24 negative pages. Its 56 requests cost USD 0.455752, all provider-reported; contended generation rates are 3.20 usable pages/minute and 140.43 pages/API USD. Parent CPU is 101.40 seconds, wall time 1,201.29 seconds, sampled parent RSS 618.16 MiB; separate layout-worker resources are not summed into parent RSS. This is the broader DEV corpus, not fresh confirmation. Sonnet improves quality over Luna and ordinal here, at a higher cost per page.

The ledger snapshot for this update has 4,333 admitted P003 attempts and USD 10.74456 accounted, including 15 unresolved reservations; this is not a claim that the entire amount was charged. Three transports remain active. No local GPU or paid GPU host is used in this wave.

## P003 council decisions and structural failure analysis, 2026-10-10 22:02 UTC

All three council outputs were presented separately: Architect, Genius Inventor and Performance Wizard. Their proposals, rationale, subsequent decisions and local serialization measurements are summarized in `bench/results/p003-council-next-layer.md`. Next CPU work changes the topology proposal language rather than only ranking words within a fixed wrong grid. Source-segment alternatives are frozen before independent reference scoring; fresh48 remains untouched for tuning.

Independent compatible-band scoring finds no strict-cell or complete-table improvement in the frozen 214 approximate page compositions. That pool remains at 1,088 strict cells and five complete tables. Its losing result is retained, and no paid selector is added to a pool with no measured opportunity. The current decision tables now also include 400 px, 500 px and 1,024 px selected-only outcomes, ownership failures, matrix/atomic representation tests, full provider-cost bases and CPU/RSS scopes. See `bench/results/p003-current-queue-progress.md`.

A repeat diagnosis locates 494 of Luna's 506 lost strict cells on one dense page rejected for nonrectangular matrices. Four returned tables have a short first row above a rectangular body; all cells are strings and the provider supplies no spans. Separate source-frozen hypotheses will compare header spans with left/right blank padding while preserving returned strings and bounds. The strict original failure is not repaired or rescored in place. No reference-dependent rule or another model is substituted into the original run.

The new explicit-corpus candidate selector is prepared in an isolated worktree, with 23 tests passing. It keeps 16 as the historical default and requires an explicit bounded expected-page count for larger cohorts; 48-page confirmation cannot silently shrink to successful outputs. Its process, evidence, request and parsing functions are unchanged. Merge waits until the current candidate queue drains, with narrowly reviewed compatibility for historical evidence.

## P003 independent geometry and header opportunities, 2026-10-10 22:21 UTC

The independent source-segment oracle rebuilt all 1,190 legal crop states before scoring. Both its geometry control and best restricted choice reach 94 strict cells and one complete table, with three of four negative pages receiving false tables. This proves no improvement within this bounded proposal language, not a general ceiling for spatial reasoning. No paid selector is assigned to this pool. Full results are in `bench/results/p003-segment-topology-oracle.md`.

Header hypotheses are more promising but remain unselected. All 150 complete page states, including 135 alternatives on one failed dense page, were authenticated before DEV scoring. Gold-selected hypotheses increase strict cells from 278 to 713, with complete tables unchanged at three and six extra tables. They preserve model-generated literals, not source-word ownership; the original generation failure remains recorded. A future decision experiment must choose from evidence without using the oracle's choices. See `bench/results/p003-header-proposals-oracle.md`.

Natural64 now includes Haiku explicit-matrix generation: 58 usable outputs, 1,333 strict cells, 12 complete tables, no extra tables or negative-page false positives, USD 0.0260132 provider-reported, 3.65 usable pages/minute and 2,229.64 pages/API USD. Fixed-edge 2048-pixel ordinal acquisition produces 63 usable outputs, 1,125 strict cells, ten complete tables, eleven extras and one negative-page false positive, USD 0.0599038 reported, 2.35 pages/minute and 1,051.69 pages/API USD. Both retain 64 pages, 93 tables and 3,847 cells in quality denominators. These contended DEV runs do not establish a causal image-size advantage.

Prepared source-word diagrams explicitly contain neutral word rectangles, no glyphs or source pixels. Their instruction notice makes them a distinct evidence treatment, not a pure pixel ablation. Filled and outlined diagrams at 128, 400 and 512 pixels preserve the original selector alternatives and alias seed. Each model will run separately. CPU preparation and all raw evidence remain archived; no paid diagram or structure-admission call has occurred at this checkpoint.

Root independently authenticated the diagram and segment pool code maps against their Git commits. Thirty-four focused checks covering diagrams, header proposals, segment scoring and strict admission replay passed. New queue support is prepared separately for structure admission, geometry diagrams and partial relation probes; relation answers have question rates, never invented full-page rates. Gateway micro probes are staged serially after the current queue drains, followed by strict unchanged-code 276-page continuations and the predeclared fresh48 generation cohort.


## P003 acquisition coverage, complete DEV baselines and protocol diagnosis, 2026-10-10 22:55 UTC

All 60 completed arms in the 62-arm mechanism queue now have independently verified scores. Two stopped full276 arms retain their incomplete status. Strict continuations started at 22:44 UTC for 81 ordinal and 145 Luna pages, including only authenticated missing work and two request-only pages with zero ledger admissions. Completed failures are never repurchased. Fresh48 Haiku matrix generation runs alongside; fresh48 Luna, Sonnet and ordinal follow. Three PPLX confirmation selectors are frozen at text-only, 128 and 512 px, seed 20261010 and explicit 48-page admission; plan SHA256 35c5227fba1b905253e4481cbe2e5fd6e3f7af871b2126117101e4dacbbad639. Confirmation outcomes will not select new configurations.

Natural64 Opus returns 62 operational pages, 1,617 strict cells, 15 complete tables, 36 missing and three extra tables, no negative-page false positives and two errors. Reported API cost is USD 0.85678; contended rates are 6.40 usable pages/minute and 72.36 pages/API USD. Sonnet still recovers more strict cells (1,839), while Opus completes one additional table. Fixed-edge 3072 ordinal produces 1,204 strict cells, 12 complete tables, 46 missing, 15 extra, no negative-page false positives and two errors; USD 0.0614165 reported, 2.57 pages/minute, 1,009.50 pages/API USD. All retain 64 pages, 93 tables and 3,847 cells. Contention differs, so elapsed rates do not establish causal model speed.

Source availability explains a major acquisition loss. Full-page text makes 2,259 of 2,333 cells character-compatible; original detector-owned text makes 1,267 compatible; the conservative segment assignment makes 1,162 compatible. Of 992 cells losing necessary character support between full source and detector regions, 991 occur on two dense pages. Compatibility permits arbitrary character order and is not attainable extraction quality. Nine source-only whole-page gutter treatments fail to capitalize on the extra text: the best reaches only 14 strict cells and no complete tables, with false tables on all four negative pages. All 144 outputs and bounded refusals remain archived.

Matched CPU YOLO internal sizes 640/1024/1280 produce 19/24/37 table proposals. Independent source-image/projection replay preceded scoring: at IoU 0.5 these match 14/16/23 of 53 tables, with 5/8/14 extra proposals and negative-page false positives on 3/1/0 of four pages. Detector inference totals 5.716/13.727/21.284 seconds wall and 11.133/26.969/41.892 CPU seconds; peak worker RSS is 1.31/1.36/1.48 GiB. The 1280 input loses some proposals found at 640. Follow-on TATR CPU inference completed all 80 regions and froze 432 page outputs across 27 placement treatments. Model-generated structure is measured independently of literal source ownership; overlapping-proposal word ownership stays unresolved. No reference-derived region or threshold is chosen for execution.

Gateway relationship probes use twelve source-hash-selected word pairs, four each for cell, row and wrap relations, over nine pages. Compact Laya produces eleven nonabstaining valid answers and one abstention. Its verbose arm stops on the first HTTP 422; eleven questions remain unattempted and USD 0.30 reserved with charge unknown. Native d1 returns all twelve compact and twelve verbose answers, but the original strict parser rejects a redundant `name: "q0"` echo. Offline source/request/wire replay removes only that exact matching metadata key, preserving raw choice, probabilities and confidence; all 24 answers then validate. Original failure reports remain unchanged and there are no new API calls. This demonstrates protocol compatibility, not correctness. Compact and verbose d1 charges are USD 0.0001368 and USD 0.00029316, provider-reported. Laya's reported zero remains zero, with its separate estimate also zero under the frozen catalog's promotional rates. Relation questions are not pages: page throughput/cost rates remain unavailable.

Root prepared 28 separate OpenRouter compact/verbose probes across fourteen models. They use the same twelve pairs, one attempt per question, no fallback and no inline retry. An explicit coordinated-queue admission mode is being tested before launching them alongside CPU-heavy continuations under the same global three-transport policy. A short psutil process-tree sample found ordinal using 319% of one CPU core and 1,457 MiB summed RSS; Luna and Haiku used 13%/26% CPU and about 1,447/1,439 MiB during provider waits. This three-second snapshot is not a sustained utilization claim. No local GPU or rented host is used.


## P003 complete-corpus confirmation and capacity measurement, 2026-10-10 23:25 UTC

Both authenticated full276 continuations are complete. Luna yields 275 usable pages, 6,902 strict cells and 166 complete tables; ordinal yields 269 usable pages, 6,232 cells and 165 tables. Quality denominators are 220 scored pages, 249 tables and 8,897 cells, with 56 additional diagnostic pages retained. Whole-run API costs are USD 0.08655564 and 0.1205097; rates are 4.86 / 5.33 usable pages/minute and 3,177.15 / 2,232.19 pages/API USD. Luna's cost includes provider-reported BYOK upstream charges despite reported gateway zero. Original stopped-parent CPU/RSS is unavailable, so complete combined resources remain unmeasured. All errors and attempted costs remain included. See `bench/results/p003-complete276-analysis.md`.

The fresh48 frozen baselines recover 2,664 strict cells / 27 complete tables for Haiku matrix, 2,467 / 25 for Luna standard, 1,891 / 27 for Sonnet standard, and 2,080 / 23 for ordinal OCR300. All retain 48 pages, 66 tables and 4,203 cells. Rates and natural/authored strata are in README and `bench/results/p003-confirmation-analysis.md`. Haiku matrix outperforms this Sonnet configuration in strict cells and cost, but differing representations and single runs preclude a general model ranking. Exact repeated natural64 Luna inputs produced materially different outputs: all 56 paired request and image hashes match, while strict quality changes from 1,348 to 1,953 cells. This is repeated-run variation, not an improved configuration.

The predeclared fresh48 PPLX selectors at text-only / 128 / 512 px yield selected-only 1,515 / 1,605 / 1,793 strict cells and 23 / 16 / 25 complete tables. Natural-only strict scores are 1,222 / 1,481 / 1,480. Each makes 39 independent requests, costing USD 0.00098172 / 0.00107728 / 0.00111316; candidate generation is excluded. Selected/unresolved counts are 31/8, 30/9 and 39/0. Shared retained or skipped-baseline pages receive no primary quality credit. An evaluator admission bug demanded nonexistent request files for explicitly never-requested tails after failed crop calls; the narrow fix exempts only tails with no request or call receipt, preserving every attempted request requirement. No frozen source, output or treatment changed.

The CPU YOLO/TATR follow-on improves strict cells from 204 at internal 640 px to 438 at 1280 px at matched 0.5 threshold and maximum-overlap placement, with three complete tables in both. The 1280/0.7 treatment reaches 451, mostly on two dense pages, while some smaller-size proposals are lost. All 27 treatments remain in `bench/results/p003-yolo-structure-analysis.md`. Regional gutter and physical-row derivatives fail to improve this: all 576 states independently replay, with best regional gutters 59 strict cells / one complete table, and physical-row/TATR-column hybrids 201 / two. See `bench/results/p003-regional-tracks-analysis.md`.

Actual capacity tests find the shared JSON accounting path dominates short calls. At 23,000 synthetic historical entries and 30 matched attempts, unchanged stdlib accounting takes 32.64 seconds with three workers and 33.36 with six. A SQLite/WAL prototype takes 0.542 / 0.322 seconds but omits production migration, cumulative-budget and crash guarantees; it is not deployed. A pinned guarded orjson adapter preserves financial types and request bytes but is slower: 37.80 / 42.87 seconds, including safety checks. Its negative result remains published. Six occupied workers alone do not establish useful capacity. Three paid transports remain in force; CPU preprocessing and independent scoring overlap inference. No local GPU or rentals are used.

The next source-only relation corpus contains twelve exact counterfactual twins: each pair has byte-identical literal text, IDs, boxes and text-only requests. Nine pairs differ only through observed rules/images; three pairs remain identical even in pixels. A new immutable v2 also corrects native OpenRouter image state to a plain string followed by an image part. V1 remains archived and never hosted. Root independently pins source code and frozen inventory before preparation. All 24 pages, including the six genuinely ambiguous cases, remain in the operational denominator; reference labels never enter model requests.


## P003 independent assembly derivatives, 2026-10-10 23:28 UTC

The 51-arm confirmation/header/micro queue completed without substituting models. Independent header replay accepts all 80 native receipts across 20 treatments, but selected-only quality reaches at most 180 strict cells and zero complete tables. PPLX local-header image treatments and several Luna/Clef image treatments reach that partial maximum; Jev full text does too, while Jev local text does not. Original historical table quality remains excluded. All abstentions, missing/extra tables, incremental costs, question rates and CPU/RAM are in `bench/results/p003-header-decision-analysis.md`.

After complete queue drain and zero active paid reservations, root launched 32 independent acquisition/admission/diagram treatments. Plan SHA256 14927772c15135fae838a5c07676367df91e3a4dee5f25f5574d50c56b177156, order seed 61011. Thirteen complete-pipeline arms cross internal YOLO 640/1024/1280 with Luna standard, Haiku matrix and Sonnet standard; Gemma31 and Ministral14 revisit 640/1280. All use fixed 1536 px detector rasters, 1024 px generation crops, OCR150 and four detector CPU threads. Nineteen previously prepared table-admission and geometry-diagram treatments remain separate. No fresh48 result selected these configurations. The bounded detector-size option changes only opt-in benchmark behavior, retains default 640 and requires worker acknowledgment; targeted tests and actual CPU worker smoke checks pass.

The next frozen successor contains 48 independent synthetic relation treatments: fourteen models with plain text geometry versus explicit observed rows/rules, plus five image-capable models with full-page/cropped images at 128/512 px. It retains all 24 cases in every arm, including the six evidence-indeterminate cases. Plan SHA256 79d165e01c20459fdc597ef62d5728f2cfa1ff5b9ed1089ebb812041e6d9549c, order seed 20261011. Its wrapper waits for complete preceding-queue drain without reserving money. Each arm makes at most 24 fresh distinct-case calls, stops on its first transport error and never switches models; malformed answers remain measured failures. These are local relationship questions, not full extracted pages. A separate CPU-only vector/raster spatial baseline is being frozen without reading gold.

A three-second snapshot of the active acquisition queue measured 159.3% of one CPU core, 1,688.8 MiB summed live RSS and five processes on an eight-logical-CPU machine. This is not a sustained utilization claim and excludes agent workloads. Shared JSON accounting still limits short-request throughput; increasing occupied workers alone did not improve the matched capacity test. Root is keeping preprocessing, protocol validation and independent scoring active rather than adding automatic retries.

## P003 official postprocessing and visible failure inspection, 2026-10-10 23:59 UTC

Independent replay of all 144 official Table Transformer postprocessing states completes before DEV scoring. These states reuse the same 80 retained model forwards and source-owned words across nine fixed acquisition-size/threshold treatments. At threshold 0.5, official postprocessing recovers 263 / 382 / 569 strict cells at detector inputs 640 / 1024 / 1280, versus 204 / 193 / 438 for the prior maximum-overlap decoder. Each completes three of 53 tables. The 1280 treatment also produces ten extra tables on positive pages, with no negative-page false positives. Two 640 treatments reproduce an upstream ValueError on one dense page; the complete failed page receives no partial credit. All outcomes and matched deltas are in `bench/results/p003-official-tatr-analysis.md`. The full postprocessing pass takes 217.616 seconds wall, 216.582 CPU seconds and 384.684 MiB sampled peak RSS, excluding source verification and earlier inference.

The user requested recurring visual review and visible inputs. A dedicated GPT-6.1-Sol medium agent now creates deterministic images from actual PDFs, outputs and independently verified scores. Source overlays mark whole reference tables; output overlays mark schematic cells because generative responses do not provide real cell boxes. Original unmarked images, full cell grids, mismatch JSON and readable regional comparisons remain local. The first five examples include a clean 81-cell table, a four-cell table, an academic partial result, a dense newspaper failure and a correctly empty negative page. No generative image model fabricates evidence. The reusable workflow and three tests are in `bench/P003_VISUAL_REVIEW.md` and `bench/p003_visual_review.py`.

Visual inspection identifies eight strict representation mismatches on the academic page: seven percent-spacing differences and one Unicode-subscript versus reference-LaTeX difference. The model preserved O₂; an initial diagnostic font failed to display the subscript. The renderer font was corrected and the user-facing interpretation corrected. Original strict scores remain unchanged at 58 of 66 cells, with no complete table. On the same dense newspaper page, Sonnet detector640 recovers zero of 1,036 strict cells; detector1024 recovers 71, still with no complete table. Actual source and extraction images were shown inline, including the failures.

The new 32-arm acquisition/admission/diagram queue has 24 completed arms and three running at this checkpoint. The separate synthetic48 successor remains scheduled after its complete drain. A source-only shared-context derivative is prepared for fourteen decision models, group sizes four/eight, and text geometry versus observed rows/rules. This is explicitly cross-page shared context, not isolated provider batching. All 24 cases remain in every arm, atomic malformed groups receive no salvaged answers, charges are counted once per request, and source-ID matched comparisons will expose interference. The new runner/evaluator and existing visual/official checks pass 19 targeted tests on main. No hosted shared-context request has occurred yet.

The latest accounting snapshot has 7,405 P003 attempts and USD 19.6322036915 accounted, including 17 reserved entries; this is not the amount proven charged. The shared transport limit remains three, the wave ceiling USD 50 and cumulative authorization USD 200. No local GPU or rental is active in this wave. Raw PDFs, source images, response bodies and accounting artifacts stay ignored; only reviewed code and compact Markdown reports are pushed privately.
