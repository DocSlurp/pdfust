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
- **Budget:** cumulative $15 authorization remains. All hosted calls use the
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

The user renamed the project to **jev-pdf**. GitHub is now private
`justsml/jev-pdf`; both remotes and the private-main pre-push guard target that
name. GitHub Actions remain disabled. Distribution `jev-pdf` adds the public
`jev_pdf` import while keeping `pylopdf` as the compatible implementation/API.
Original license notices and data-package names are retained. Existing artifact
paths remain unchanged to preserve frozen experiment provenance. No package
release or index publication is authorized by this rename.

## 05:16 UTC checkpoint and prompt round

The explicit prompt-tuning window is 05:05–06:05 UTC, within the overall
04:27–06:27 UTC wave. Fifteen generic instruction-only variants from three
independent agent tracks are frozen across both DEV cohorts and two models
(Luna and PPLX): 1,440 logical page requests. Each request preserves its
source words, 512 px image and complete candidate menu. The sweep has a
persistent $1 incremental admission cap under the cumulative $15 limit;
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

Local editable migration to `jev-pdf` succeeded. Full Python suite: 1,919 passed,
16 skipped, two expected failures. Benchmark typing fixes are being integrated
before the next private push. Raw artifacts and credentials remain ignored.
