# Larger-corpus tuning wave

Started **2026-10-09 04:27 UTC**; stop new experiments by **06:27 UTC**.
The user authorized a private push and up to two hours of iterative experiments.
Available capacity is three parallel agents plus the coordinator, despite the
requested upper bound of eight agents. Each builder uses a separate worktree.

## Contract

- **Quality first:** preserve exact source ownership and cell/header relationships;
  report table-presence classification separately from full reconstruction.
- **Workloads:** the frozen 104-file / 125-page silver DEV corpus, a reproducible
  16-row public OmniDocBench DEV sample, and separately versioned DEV extensions
  when existing positive coverage cannot test a hypothesis.
- **Protected data:** the separate 20-file holdout stays unopened and untuned.
  Public benchmark familiarity/pretraining contamination is unknown.
- **Budget:** cumulative USD 15 authorization remains. All hosted calls use the
  shared reservation ledger. Positive reported charges take precedence; missing
  or zero charges use published prices and reported tokens, marked estimates.
- **Resources:** CPU by default; the user subsequently authorized bounded local
  GPU comparison points. Health check passed on RTX 3090. Record CPU time, wall
  time, current-exec RSS, GPU allocated/reserved VRAM and sampled utilization.
  API timing excludes local work unless explicitly measured end to end.
- **Cache:** test actual provider retransmissions and returned cache counters.
  Local replay and faster repeats are not evidence of provider cache hits.
- **Acceptance:** do not change production defaults in this screening wave.
  A candidate must retain source conservation and report every attempted input,
  error and false positive. Prefer the simpler baseline when quality ties.
  A DEV win needs fresh, preplanned confirmation before a generalization claim.
- **Artifacts:** raw images, annotations, requests, responses and traces remain
  ignored. Commit compact reports, reproducible code and source/license manifests.

## First-round priorities

| Track | Hypothesis | Evidence needed | Rejection condition |
| --- | --- | --- | --- |
| OmniDocBench sample | Real page images expose missing layout diversity | 16 metadata-stratified rows with pinned provenance and coverage | Missing license/provenance, or treating image-wrapped pages as native PDFs |
| CPU routes | Native geometry can reject prose without a model call | Exact table ownership/spans and false positives over all 125 pages | Any lost baseline grid or unsupported borderless recall claim |
| Evidence designs | Compact source geometry, neighbors or a schematic can improve decisions cheaply | Paired model results with fixed labels and body hashes | Gold-derived inputs, lost source IDs or lower quality at higher cost |
| Image matrix | Larger images recover information missing at 128 px | All sizes/color arms plus matched blanks on the same pages | Gains explained by text/batching changes or incomplete denominators |
| Row/oplog pilots | Smaller assembly decisions beat single whole-region choices | Exact records, candidate ceilings, steps, costs and failures | Source conservation confused with semantic accuracy |

The Council of Dans runs three distinct proposals: **Architect**, **Ruthless
Minimalist** and **Genius Inventor**. Preserve all three artifacts and their
rationales; the coordinator then selects the next experiments using measured
results, as the user requested.

## Progress

- Initial code and reports are local at `eeb23e5`; private push pending the sample.
- The prior full-test errors came from the unset `rustc` mise shim. Selecting the
  installed Rust 1.99 toolchain explicitly passes all 13 color-region tests;
  this is an environment repair, not an extraction change.
- Provider retransmission probe completed 18 calls. None returned cache-read or
  cache-write counters, so **no provider-cache saving is established**.
- Existing vector-grid baseline is already 10/10 exact on the silver positives.
  This corpus has no authored positive borderless targets; add a separately
  labeled DEV extension before claiming borderless recall improvement.

## Council disposition and round two

- [Architect](council-wave/architect.md): candidate recall/source conservation
  before model selection, then a bounded external OCR admission test. Rejects
  annotation text as a substitute for actual OCR. Conditional stop below 95%
  candidate recall; current companion set is far below that threshold.
- [Ruthless Minimalist](council-wave/minimalist.md): paired borderless/prose DEV
  examples and an external native-evidence audit. Its proposed companion set
  ran first and exposed a 2/12 complete candidate ceiling.
- [Genius Inventor](council-wave/inventor.md): a small paired evidence screen,
  then bounded wrap/header operations. Rejects broad easy-gate sweeps as a
  substitute for structural accuracy.

All three proposals are retained separately. The selected next experiments are
source-only rolling-row assembly on the new 28-page companion, a bounded paired
geometry/blob/neighbor screen, and external image-only decisions without
annotation text. Matching original OmniDocBench PDFs are unavailable in this
release, so native-evidence audits cannot manufacture an OCR layer from labels.
GPU comparison is a later explicit user exception to the proposals' initial
CPU-only brief. No local training is authorized.

Round two: [borderless companion results](results/borderless-challenge.md)
retain 12 positives, 12 prose negatives and four merged-grid controls. Native
text candidates fully recover only two 13-point no-wrap tables; all six wrapped
cases fail. The numeric/prose veto keeps zero negative false positives but does
not improve this 2/12 ceiling. Candidate assembly, not ranking, is the priority.

Initial private push completed at `6bf56ca`. Full CPU suite passed 1,844 tests,
with 16 skips and two expected failures; the new sample/routing checks also pass.

## GPU comparison and next external-evidence test

The bounded [YOLO CPU/GPU comparison](results/gpu-comparison.md) completed all
141 source images. Enforced four-thread CPU FP32 median was 40.105 s; RTX 3090
FP32 was 4.030 s (**9.95× faster**) with matching detection topology and boxes
within the predeclared tolerances. FP16 was slower at 4.193 s and changed two
pages' detections; reject it for this configuration. VRAM, GPU utilization,
power, CPU time and RSS are recorded. No GPU errors or training occurred.

Detection quality is separate: YOLO missed all ten synthetic ruled-table
positives; on OmniDocBench it detected four table-bearing pages but produced
three false-positive pages. Keep native vectors for born-digital grids; use
learned layout proposals only as an experimental raster path.

Next external-evidence probe: sample rows 1, 2, 5 and 9, chosen from existing
source/language metadata, at 640 and 1200 pixels. Run actual CPU OCR with native
PP-OCRv6, then assess evidence against retained annotations. Never provide
annotation text as OCR input or call image carriers original PDFs. Per-page
limits: 30 seconds and 1 GiB RSS; two CPU threads, no GPU or provider spend.

## Evidence-to-experiment planning rule

At every reprioritization, match each observed failure to an already measured
technique before proposing a new isolated method. Record **failure → mechanism
→ compatible technique → combined arm → removal ablation → acceptance gate**.
A filter can reduce false positives; it cannot recover cells absent from every
candidate. Keep those failure classes separate. Source-observable routing may
use text, geometry and image properties; it may not use case IDs, gold labels,
document-family labels or known answers.

| Observed failure | Technique with relevant evidence | Next combined experiment | Required ablation and failure check |
| --- | --- | --- | --- |
| Rolling candidates accept all 12 numeric-prose pages | Luna plus a 512 px page image rejected all 12 while retaining 12 borderless positives | Native vector route, then rolling candidate assembly, then source-image admission | Compare text-only admission on identical candidates; count unresolved negatives separately from true rejections |
| Rolling candidates lose spans on all four merged controls | Native vectors preserve all four controls | Retain complete native grids before offering uncovered regions to the row assembler | Remove the vector route; report exact spans and source ownership, not just retained strings |
| OCR padded boxes block every eligible wrapped continuation at 1200 px | Native-word rolling assembly recovers wraps; observed OCR boxes have negative vertical gaps | Allow bounded overlap only for otherwise eligible sparse, nonnumeric continuation bands | Freeze tolerances 0, 0.25 and 0.5 word heights; retain numeric rows and all prose negatives |
| Fresh layouts reduce rolling candidate coverage to 4/16 positives | Existing native and rolling hypotheses are incomplete on small/irregular grids | Audit missing-column, small-row and continuation topology before adding candidates | Run the frozen selector unchanged first; never claim filtering repairs missing candidates |
| Large external page images exceed request bounds | Named JPEG80 preserves dimensions and admits 46/64 versus 26/64 PNG1200 requests | Fixed-resolution compressed image plus the same decision questions | Compare only matched admitted inputs for quality, and separately report all-input coverage; retain lossy pixel changes and refusals |
| Raster pages have no native source text | Actual CPU OCR at 1200 px retains much more printed content than 640 px | OCR source inventory, then overlap-aware assembly, then image admission | Compare against OCR-only and native-word ceilings; source-ID conservation is not original-text recall |
| Layout inference is slow on CPU | YOLO FP32 is 9.95× faster on this GPU with matched outputs | Optional GPU proposals for raster pages, followed by source-backed extraction | Keep native-grid and end-to-end quality baselines; YOLO misses all ten silver grids and does not extract cell values |

Choose the next two or three combinations by how many measured failures they
can address, candidate coverage, implementation cost and expected provider
spend. Reuse retained responses only for offline scoring, not as evidence of
provider caching or fresh throughput. A positive combined result earns a
frozen-config robustness check, not an automatic production default.

## Package identity

The user renamed the project to **pdfust**. GitHub is now private
`justsml/jev-pdf`; both remotes and the private-main pre-push guard target that
name. GitHub Actions remain disabled. Distribution `pdfust` adds the public
`pdfust` import while keeping `pdfust` as the compatible implementation/API.
Original license notices and data-package names are retained. Existing artifact
paths remain unchanged to preserve frozen experiment provenance. No package
release or index publication is authorized by this rename.

## 05:16 UTC checkpoint and prompt round

The explicit prompt-tuning window is 05:05–06:05 UTC, within the overall
04:27–06:27 UTC wave. Fifteen generic instruction-only variants from three
independent agent tracks are frozen across both DEV cohorts and two models
(Luna and PPLX): 1,440 logical page requests. Each request preserves its
source words, 512 px image and complete candidate menu. The sweep has a
persistent USD 1 incremental admission cap under the cumulative USD 15 limit;
provider reservations and actual/effective charges remain separate.

| Test | Exact positive tables | Prose false tables | Interpretation |
| --- | ---: | ---: | --- |
| Original native-word rolling + Luna 512 | 12/12 | 0/12 | Promising in the original DEV family |
| Fresh unchanged rolling + Luna 512 | 3/16 | 2/8 | Candidate ceiling is 4/16; filtering cannot fix missing topology |
| OCR 1200 rolling, no overlap allowance | 6/12 | 12/12 | Padded OCR boxes block continuation joins |
| OCR 1200 rolling, 0.5-height allowance | 12/12 | 12/12 | Candidate recovery improves; admission remains necessary |

All original four merged-grid controls stay on the native vector path. The
fresh cohort has no such controls. Both are DEV, not heldout confirmation.
The next topology experiment targets small tables, header/data edge mismatches,
and blank columns while prompt changes test admission on unchanged candidates.

Local editable migration to `pdfust` succeeded. Full Python suite: 1,919 passed,
16 skipped, two expected failures. Benchmark typing fixes are being integrated
before the next private push. Raw artifacts and credentials remain ignored.

## 05:22 UTC — source-cue quarantine

The source-only audit found that fresh24 includes class-specific explanatory
sentences directing the reader to treat rows as records or columns as independent
narrative. These visibly disclose the table/prose decision. **All fresh24 model
admission results above are quarantined and excluded from primary conclusions.**
Retain requests, responses, costs and reports as an audit trail. Geometric candidate
coverage remains a diagnostic observation; it does not validate model admission.

Stop additional cued requests after the in-flight bounded batch. A separate
source-only ablation deletes the common explanatory band while preserving body
operators/coordinates. Freeze its new sources, candidates and requests before
reading references or scoring. Keep original28 prompt testing independent;
the audit found no class-specific title/footer there, though its narrow synthetic
content limits generalization. Do not access the protected heldout set.

## 05:30 UTC — Astra realism review and decomposition priorities

At the user's request, an Astra subagent is reviewing silver realism and applying
fixes in a separate worktree. Original104 remains immutable and is classified as
implementation probes, not natural-document generalization evidence. The new
reviewed cohort will contain 16 meaningful tables, eight coherent prose pages,
and four explicitly ambiguous pages. Ambiguous references receive no binary or
exactness scores; decisions, source conservation and costs remain observable.
The neutral deletion arm also has ambiguous authored negatives and is diagnostic
only. Further fresh/neutral prompt requests are stopped persistently.

| Combined mechanism | Latest result | Next action |
| --- | --- | --- |
| OCR 1200 + 0.5-height overlap + Luna image512 admission | 12/12 exact tables, 0/12 prose false tables, 4/4 native controls | Test the aggregate-selected semantic prompt, then transfer unchanged to reviewed DEV |
| Same OCR route + PPLX baseline admission | 12/12 exact tables, 6/12 prose false tables | Semantic prompt and source-only first gate target admission errors |
| Source seed corridors + continuation candidates | 16/16 neutral positive candidates exact, versus old 4/16 ceiling | Freeze generic candidate menus; rerun unchanged on realism-reviewed source |
| Candidate-free table gate before matrix selection | Preparing | Test whether removing candidate matrices avoids table-acceptance bias; charge actual gate requests separately |

The 48-call OCR admission comparison cost USD 0.00808632 effective, with 22.08
summed HTTP seconds. Those are model-stage measurements; OCR preprocessing and
native routing are reported separately, not hidden in an end-to-end speed claim.

## 05:40 UTC — broaden exploration at the user's direction

Do not retire moderately plausible approaches based on one narrow screen.
Keep prior results and vary mechanisms, source conditions, and combinations.
The next resolution matrix uses 200/300/400/500/600/800 px with separate width,
height and longest-edge limits, RGB8, gray8 and palette4, all four image-capable
native decision models, and actual dimensions/bytes. Equivalent pixel evidence
is identified as such, never called a provider-cache hit. Optional anisotropic
squeezes are a separate experiment, not an implicit image transformation.

An additional 16 OmniDocBench references are being acquired specifically for
TRAINING-oriented synthetic layout derivatives with newly authored content.
Parent/descendant groups and research-only provenance remain explicit; they must
not later count as independent evaluation examples. Original DEV16 stays separate.

The internal shared-ledger ceiling increases from USD 5 to USD 8 to allow these
bounded experiments; the user's cumulative USD 15 cap is unchanged and includes
prior usage. At 05:34 UTC, conservative accounted usage including prior charges
and USD 1.20 unresolved reservations was USD 4.5718355968. New image-axis calls
have a separately named persistent USD 2 wave budget, without resetting old wave
accounting. Per-run prompt, gate and union caps remain in force.

## 05:56 UTC — broad sweeps and renewed specialist evidence

The user's wider exploration request extends the prompt window within their
30–90 minute allowance, up to 06:26 UTC; overall wave deadline remains 06:27 UTC.
All 15 original prompt variants completed. The reviewed v2 prompt sweep remains
active around the serialized provider image runs; retained completed bodies are
not charged again or called provider-cache hits. All missing arms stay explicit.

| SLANet-plus DPI | Full page exact | Tight source crop exact | +4 pt exact | +12 pt exact |
| --- | ---: | ---: | ---: | ---: |
| 72 | 0/16 | 0/16 | 3/16 | 7/16 |
| 120 | 0/16 | 0/16 | 1/16 | 5/16 |
| 180 | 0/16 | 1/16 | 1/16 | 5/16 |

All configurations falsely propose tables on 8/8 prose pages; four ambiguous
pages remain unscored. All 336 outputs completed without model errors. The model's
fixed 488-pixel tensor helps explain why increasing render DPI alone does not
improve this sample; padding remains a useful independent variable. These are
CPU observations with background-work caveats, not hardware ceiling claims.

The first generic union reaches PPLX 12/16 exact reviewed tables (two accepted
wrong, two unresolved), versus 4/16 with the older candidates; Luna reaches 8/16.
A separately frozen local-gap extent ablation restores 16/16 candidate coverage
without regressing original positive cases; model selection on that expanded
menu is queued. Candidate coverage still does not establish automatic accuracy.

## 06:05 UTC — preserve broad options, combine complementary errors

| Observation | Combination to retain | Interpretation |
| --- | --- | --- |
| SLANet 72 DPI / +12 pt wins over larger renders on this reviewed sample | Low-resolution specialist plus source-ID agreement with T005 | Seven correct accepted tables, no scored wrong accepts, nine deferred positives; selective route, not full extraction |
| PPLX source-only gate detects all 16 reviewed tables without prose false positives | Presence gate followed by expanded extent candidate selection | Actual selector experiment queued; retained gate conjunction is only an offline simulation |
| Width400 and height400 produce different actual pixel counts and quality | Explicit axis budget plus grayscale/palette arms | Compare actual W×H, bytes, quality and provider charges, not nominal size alone |
| Initial Omni TRAINING scaffolds misrepresent typography, masks and density | Pixel-derived line density, category-specific fonts and suppression of redactions | Astra reviewing every pair; photographs and handwriting remain approximations |

All prior moderately plausible arms remain recorded. The next planning pass should
use per-case failure overlap to propose combinations and removal ablations rather
than discarding a method solely on its aggregate score. No tuning uses heldout data.

## 06:26 UTC — close the authorized two-hour wave

Regular and anisotropic matrices completed all 1,560 unique requests. Expanded-menu
prompt transfer completed 112 calls, preserving PPLX 16/16 exactness under both
prompts; Luna improves to 10/16 with cross-cell instructions and regresses to 8/16
with reading order. Keep both outcomes. Reviewed-set prompt tuning is complete
for Luna; PPLX remains partial after one interrupted request, with missing work
explicit and its reservation retained. Internal prompt cap is now USD 1.40;
cumulative user cap remains USD 15. Conservative accounted total is USD 6.3056201568,
including USD 1.50 unresolved reservations. No further paid work is queued.

Next planning starts from the [closing report](results/tuning-wave-2026-10-09.md):
transfer size tests to natural/reviewed sources, measure real routing cascades,
inspect selective-route deferrals, and freeze arbitration before scoring. The
additional 16 reference-derived pages remain TRAINING and research-only.
