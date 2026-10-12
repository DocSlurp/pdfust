# Experiment handoff: pdfust research summary for DocSlurp

Prepared 2026-10-12 from the committed reports under `bench/` and
`bench/results/`. Every number below is copied from the report named next to
it; open that report before quoting a figure. Paths are relative to the
repository root.

## Read this first

- **Everything is DEV data.** The quality corpora are mostly authored or
  synthetic, with correlated sibling pages. Several were also used to tune the
  library, so gains on them are in-sample (`bench/DATASET_REALISM_REVIEW.md`).
  None of these results is DocSlurp accuracy. Build a DocSlurp eval from your own
  real inputs before claiming accuracy.
- **Single runs, one machine.** Timings and costs are single serial runs and are
  not replicated. Latency and cost figures are API HTTP time and charges, not
  end-to-end document time. Hosted model output varies run to run: identical
  Haiku requests on natural pages gave 687, 289 and 732 cells.
- **Held-out data was never used.** `bench/heldout-silver/` and the Langfuse
  `HELD-OUT-NOT-FOR-TRAINING/` datasets are out of scope for tuning; do not read
  or score them.
- **No model is wired into the library.** The public pdfust API calls no hosted
  model. Decision models, hosted transcription and OCR comparisons live only in
  `bench/`.

## Where the results are

| What | Where |
|---|---|
| This summary | `bench/EXPERIMENTS_HANDOFF.md` |
| Page-transcription model comparison (hosted, open GPU, native) | `bench/results/wild-v1-models.md` (regenerate with `python -m bench.wild_models_report`) |
| Native extraction and OCR audit on wild-v1 | `bench/results/wild-v1-latest.md`, `bench/WILD_CORPUS.md` |
| Dataset realism review | `bench/DATASET_REALISM_REVIEW.md`, `bench/REAL_WORLD_V2.md` |
| Library speed, layout, OCR, Markdown scores | `bench/results/latest.md`, `layout-latest.md`, `ocr-latest.md`, `markdown-scores.md`, `features-latest.md` |
| Decision-model studies | `bench/results/decision-findings.md`, `decision-alternatives.md`, `decision-p003.md`, `bench/P003_RESEARCH_EXTENSION.md` |
| Pipeline experiments | `bench/results/pipeline-conclusions.md`, `bench/PIPELINE_EXPERIMENTS.md`, `bench/GENERALIZATION_FINDINGS.md` |
| Scoring audits | `bench/SCORING_HANDOFF.md` |
| Everything else (all committed reports) | `bench/results/*.md` (about 320 files) |
| Raw per-page records, outputs, requests, ledger | `bench/results/pdf-master-artifacts/` (ignored by Git, local only) |
| Flat analysis export: CSVs, raw records, manifests, costs, test results | `bench/results/pdf-master-artifacts/results-export-20261012/` (README inside; regenerate with `python -m bench.export_results`) |
| Decision-model charts | `bench/results/pdf-master-artifacts/decision-visuals-20261012/` (`make_figures.py` regenerates them) |
| Langfuse (local) | experiments and datasets as `dev/...` datasets and scored runs; see `bench/LANGFUSE.md`. `dev/wild-v1` holds 111 runs |
| Paid-call ledger | `bench/results/pdf-master-artifacts/decisions/ledger.json` |

## 1. Library benchmarks

Detail and environments: `bench/results/latest.md` (Windows, Python 3.14.6),
`layout-latest.md` (Linux, 8 logical CPUs). Do not compare absolute
milliseconds across reports.

- **Speed vs other libraries** (`latest.md`, 14 real PDFs, median of 7).
  Text extraction: pdfust was faster than pymupdf on 9 of 14 files and slower
  on 4 (patent 26.6 vs 5.5 ms, usrguide 58.4 vs 49.3 ms). First-page render at
  2x was faster than pymupdf on all 14 (usrguide 29.2 vs 55.9 ms). Merge x14:
  44.0 ms vs 129.3 ms (pymupdf) vs 346.8 ms (pypdf). `render_pages()` on 12
  pages: 2.89x with 4 workers, 3.72x with 8.
- **Markdown/layout cost** (`layout-latest.md`). Tables cost time: bill-hr815
  (110 pages) markdown 668 ms with tables vs 399 ms without. The page caches
  hold 8 pages, so reuse of one Document helps small documents (f1040: 31.5 ms
  fresh vs 5.7 ms reused) and not past 8 pages.
- **Markdown element scores** (`markdown-scores.md`, 27 synthetic PDFs with exact
  truth, 0-100). pdfust is strongest on text (99), headings (100) and lists (93);
  tables score 50 with the default strategy and 83 with `table_strategy="text"`.
  It scores 0 on links and images and code, 12 on math and 29 on emphasis, so
  overall is 45 vs 71 for the best pymupdf4llm variants. It is cheap: 283 ms and
  92 MiB RSS for the whole suite, vs docling 25,690 ms and 1,426 MiB.
- **Native OCR** (`ocr-latest.md`, PP-OCRv6 small, 2 Japanese fixtures). Strict CER
  1.3-3.8%; 150 dpi took 1.98-4.70 s per case and 300 dpi 4.69-10.75 s. A second
  concurrent call saved little time (6.19 s to 5.70 s) while raising memory.
- **Free-threaded Python** (`free-threaded-latest.md`). 1.70x on two
  independent documents, a single data point.
- **Layout detector** (`gpu-comparison.md`). A GPU makes YOLO26m 9.95x faster
  (40.1 s to 4.0 s for 141 images). It missed all 10 ruled-table positives on silver,
  so keep native vector grids for born-digital tables. The model card is AGPL-3.0.

## 2. Datasets and native extraction quality

- **Silver DEV challenge** (`results/silver-challenge.md`): 104 authored PDFs,
  125 pages. 1,576/1,576 authored literal anchors found, 104/104 completed,
  median 16.4 ms per fresh document. Anchors are not a structure or math score.
- **wild-v1** (`results/wild-v1-latest.md`; 24 documents, at most 2 pages each,
  synthetic but realistic). Native text F1:

  | Level | Text F1 | Tables exact / total |
  |---|---:|---:|
  | L0 born-digital | 0.964 | 21/27 |
  | L1 untagged | 0.893 | 13/27 |
  | L4 raster, L6 phone scan, L7 photocopy | 0.000 | 0/27 |
  | L8 mixed | 0.705 | 8/27 |
  | L9 broken ToUnicode | 0.003 | 0/27 |

  With native OCR: L4 0.763, L6 0.517, L7 0.671 (table cell recall 0.27-0.58).
  `apply_ocr` skips pages that have extractable text, so a garbage text layer (L9)
  reaches only 0.529 with plain OCR; the `ocr-adaptive` and `ocr-fill` policies
  reach 0.751 and 0.745. On L8, fill reaches 0.835 vs 0.705 native.
- **wild-v1 additions** this round: 132 encoding/producer quirk cases
  (`bench/wild_quirks.py`), 21 raster variants x 24 documents (`bench/wild_raster.py`),
  64-document multi-page wild-v2 (`bench/wild_v2.py`), and 40 licensed real-world
  PDFs with 11 verified truths (`bench/REAL_WORLD_V2.md`). Quirk families scored
  producer 0.620 text F1 (8 cases with zero text) and font_encoding 0.755
  (`results/wild-v1-latest.md`).
- **Known extraction defects** (`bench/REAL_WORLD_V2.md`): `to_markdown` merges
  columns line by line on sidebar/two-column pages; it found none of the three
  W-4 wage tables; mixed RTL lines stay in visual order; fake-bold CJK is
  duplicated. These are real; plan for them.
- **Corpus gaps** (`DATASET_REALISM_REVIEW.md`): no benchmark corpus has documents
  over 2 pages with truth, multi-page continued tables, vertical CJK Identity-V,
  slides, bank statements or receipts.

## 3. Page transcription models (wild-v1, hosted vs open vs native)

Full tables, level breakdowns and caveats: `bench/results/wild-v1-models.md`.
Ten matched scan levels, 320 pages (text F1 / exact tables of 270 / cost per page):

| Model | Text F1 | Exact tables | $/page |
|---|---:|---:|---:|
| Claude Sonnet 5.5 | 0.937 | 159 | 0.0155 |
| GPT-6 Luna | 0.930 | 122 | 0.0010 |
| Claude Haiku 5.5 | 0.927 | 139 | 0.0008 |
| Gemini 3.5 Flash Lite | 0.919 | 92 | 0.0023 |
| dots.ocr (GPU) | 0.912 | 79 | rental |
| DeepSeek V4.1 Flash, effort none | 0.906 | 125 | 0.0012 |
| olmOCR-2 (GPU) | 0.886 | 94 | rental |
| GLM-5.3 Flash, effort minimal | 0.863 | 98 | 0.0007 |
| Nanonets-OCR2 3B (GPU) | 0.862 | 85 | rental |
| DeepSeek-OCR-2 (GPU) | 0.811 | 25 | rental |
| Native pdfust + OCR (CPU) | 0.604 | 12 | none |

- On the 672-page hard-raster set, Sonnet scored 0.932 F1 and 324/567 exact
  tables; DeepSeek V4.1 Flash 0.911 and 273/567 for $0.77; GLM-5.3 Flash 0.870 and
  200/567 for $0.48.
- **Reasoning effort matters.** DeepSeek V4.1 Flash at default reasoning finished
  74/96 pages (F1 0.688, $0.0064/page); at effort `none` 94/96 (F1 0.901,
  $0.0011/page). GLM-5.3 Flash rejects `none`, so it ran at `minimal`.
- **Serving errors, not model faults:** DeepSeek-OCR-2 needed a 6,144-token
  completion cap (8,192 context) and `skip_special_tokens: false`, because its
  `<tr>`/`<td>` tags are special tokens. Both failed runs are kept and labeled.
- **Rotated scans:** most models drop on the 90-degree-rotated level; DeepSeek-OCR-2
  scores 0.251 there. Check rotation handling before a model goes into a pipeline.
- GPU rental for the open models was about $0.8 in total (estimated from rate and wall time), with every instance
  destroyed and a systemd watchdog (`bench/vast_watchdog.py`) as backstop.

## 4. Decision models (small models that judge table/prose, wrap, header, cell ownership)

"Jev" is `typesafe/jev-1.13`; "PPLX" is `perplexity/pplx-decider-v1.1-27b`. A
"GEV" model appears only in a self-hosting shortlist (`bench/HF_DECISION_MODELS.md`);
it was never run.

- **Initial pilot** (`results/decision-findings.md`; 36 known test answers, always-"no"
  scores 24/36). Jev with raw IDs scored 14-17/36; with source text spelled out
  24-25/36. Opus 4.6 scored 27-29/36. Jev was 12x faster (276 ms vs 3,308 ms median)
  and 76x cheaper ($0.0057 vs $0.43 for 96 observations).
- **Eight more models, same set** (`results/decision-alternatives.md`, singleton
  resolved text): Luna-decisions 31/36, PPLX 30/36, Solar Flash 25, Clef Flash 24,
  Mercury 21, d1 20, Tev 17; span-01 returned HTTP 404. A confidence-free per-task
  router scored 36/36 on calibration but 29/36 on test, below Luna alone. No model
  was well calibrated, so do not rely on confidence scores.
- **Admission of source-candidate tables** (28 pages, `results/rolling-extent-admission.md`):
  PPLX, Haiku 5.5 and Sonnet 5.5 each got 16/16 tables with 0 wrong; Opus 5.5 15/16;
  Luna 9/16 with 4 wrong. Cost: PPLX $0.0101, Haiku $0.0535, Sonnet $0.99.
- **Repair of injected damage** (`bench/P003_RESEARCH_EXTENSION.md`, 64 pages x 4
  scenarios): PPLX fixed 31 pages and broke 2 (net +29, $0.0089 total). Mercury net
  +2, Clef -13, Tev -46, Kev timed out. On 37 wild-v1 table pages PPLX improved
  content on 14 of 31 swapped pages with no strict regressions, but native extraction
  was exact on only 13 of 37 pages before damage, so table detection and structure
  are the bottleneck, not the decision step.
- **Image evidence** (`results/image-axis-interpretation.md`,
  `image-resolution-matrix.md`): PPLX exact cases rose with image size (17/30 at
  128 px, 22 at 512, 27 at 1200). Always run a blank-image control: where it
  matches the real image, the pixels were not used.
- **What not to do** (same reports): do not ask a small model to decode raw
  source-ID/coordinate arrays (resolving to text lifted Jev from 14/36 to 24/36);
  do not batch unrelated observations (33 of 96 hard answers changed between
  formats); do not count oracle unions (30/30) as an achievable ensemble.

## 5. Pipelines

Detail: `results/pipeline-conclusions.md`, `PIPELINE_EXPERIMENTS.md`,
`GENERALIZATION_FINDINGS.md`.

- **P001, authored pages** (181 pages: 35 table pages, 133 prose pages scored).
  Best configuration: native/OCR source + column consensus + PPLX gate + selective
  Sonnet review reached 168/168 exact scored pages, 72.36 pages/min and
  1,725.88 pages per API dollar ($0.103 total). Direct Opus got 167/168 at 13.02
  pages/min and 56 pages per dollar; direct Haiku got 149/168. This is a selected
  configuration on authored data, not evidence for all documents.
- **P002/P003, natural pages.** Hybrid (native grids kept, CPU YOLO crops sent to
  Haiku as strict JSON) reached 170/249 complete tables at 18.2 pages/min and about
  $0.039 for 276 pages, but natural pages stay weak: natural64 14/93 complete
  tables. Detector coverage, then source-text availability, then placement, are
  the limits (`GENERALIZATION_FINDINGS.md`).
- **Scoring audits** (`SCORING_HANDOFF.md`): strict reference scoring penalized
  acceptable alternatives (3 vs 4 columns, wrapped rows). A tolerant score now sits
  beside the strict one. Content recovery can coexist with a wrong merge, so it does
  not replace the strict score.

## 6. Integration implications (each supported above)

1. **Detect text-less and garbage pages first** and route them to OCR; native
   extraction returns silent empty output on raster and broken-ToUnicode pages.
2. **Use the OCR-fill policy for mixed or broken text layers**, not plain OCR.
   Bound OCR concurrency, since it saves little time and costs memory.
3. **Open each Document once** and loop over pages; make table detection a
   per-page switch; keep `table_strategy="text"` opt-in.
4. **Do not rely on pdfust Markdown for links, images, code or math**; take them
   from structured APIs or another path. Validate reading order on multi-column pages.
5. **For scans, a hosted page-transcription model beats native OCR by a wide
   margin** (F1 0.86-0.94 vs 0.60 here). Haiku and Luna are about 0.001 $/page,
   Sonnet about 0.016. Run any new model at its lowest reasoning effort first.
6. **A decision model is worth adding only as a bounded chooser over
   code-generated candidates**, with validators and conservation checks.
   PPLX is the best-measured cheap option; the others broke as many pages as they fixed.
7. **Table detection and structure, not decisions, limit natural pages.** Invest
   there first.

## 7. Cost and compute notes

- **Ledger:** `P003/extension-v1-*` charges total $47.18 conservative (including
  $12.90 held as unresolved reservations); authorized caps are $280 (P003) and
  $430 (cumulative). Reported charges are preferred; zero charges use catalog
  rates, labeled as estimates (`AGENTS.md`).
- **GPU:** all rentals are Vast.ai, one GPU, explicitly destroyed; the last
  verified state was zero live instances.
- **Local CPU/RSS:** reports state the sampling scope; parent RSS ran 326-832 MiB
  and a YOLO detector worker about 1.1-1.2 GB (not summed).

## 8. Open problems

- Dense natural pages; admission of prose vs tables; atomic page failures from
  strict validation; run-to-run variance of hosted models; OCR accuracy on natural
  PDFs; headings, lists, math, forms, links, reading order and multi-page
  continuation are unmeasured at scale.
- Many reports were written before the later wild-v1/v2 and model comparisons, and
  have not been cross-reviewed against them.
