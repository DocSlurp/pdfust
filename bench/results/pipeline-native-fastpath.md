# Native-owned detector shortcut and full276 stage profile

The proposed shortcut is structurally sound but has **zero eligible pages** in both
retained 276-page runs. Leave the production runner unchanged. API calls dominate
wall time; skipping the detector under this guard cannot improve this corpus.

The source-only plan was frozen before the census in
`performance/native-detector-fastpath/plan.md`. The helper
`native_fastpath(source, source_id_only=True, max_words=..., max_characters=...)`
returns a detector-free native plan only for nonempty source inventories whose
validated native grids own every word. Default scope refuses the shortcut;
image-only transcription is excluded. Outside words, mixed native/borderless
sources, malformed grids and zero-word pages remain ineligible. Native ownership,
merged spans and literal values follow the existing native-first region splitter.
The returned plan is equivalent in topology and source ownership, while detector
proposal metadata naturally differs. No source/quality-driven exception was added.

The completed `full276-yolo-matrix-haiku-512` run contains 270 successful pages,
four `unsupported_no_text` pages and two errors, with 119 retained API calls.
All 272 source snapshots have residual words; 111 include native grids, and the
smallest residual on a page containing a native grid is seven words. The separate
`native-regional-full-r2` census also has 272 ineligible source snapshots and four
pages without retained source. Cached detector evidence on all 272 current-run
source pages was replayed: native regions remain identical and every source ID
appears exactly once. There is no real eligible page on which to demonstrate a
complete detector-free output comparison. Focused tests provide that proof for
complete native ownership, including merged cells and arbitrary detector proposals.

The eligible retained detector wall/CPU upper bound is zero because no page passes
the guard. The JSON summaries have count zero and null measurements for this empty
eligible subset, rather than fabricated measured zero samples. No fresh end-to-end
performance win, visual-table coverage claim or model-quality inference follows.

| Nonoverlapping page wall phase | Seconds | Share of summed page wall |
| --- | ---: | ---: |
| Source, including instrumented OCR | 371.442 | 29.07% |
| Detector parent stage, including raster/worker wait/partition | 81.366 | 6.37% |
| API client intervals | 802.950 | 62.83% |
| Other or uninstrumented parent work | 22.139 | 1.73% |
| Summed page wall | 1277.896 | 100% |

Source and detector stages are instrumented on 272 pages. API intervals include
119 calls and zero intervals on pages without calls. All failures remain in the
whole-page totals. Of 369.935 seconds reported for 82 OCR calls, 367.162 seconds
is nested in measured source stages; the remaining 2.774 seconds is on unsupported
pages without a completed source-stage measurement and belongs to uninstrumented
parent wall. OCR time must not be added to source time. Likewise, 71.839 seconds
of detector worker wall is nested inside its 81.366-second parent stage.

Total page parent CPU is 1287.726 seconds. Detector parent CPU is 9.503 seconds
and API client parent CPU is 48.847 seconds, both included in that total. Source/OCR
CPU has no separate retained stage measurement, so its CPU contribution is
unmeasured. Detector worker CPU is separately scoped at 256.538 seconds and is
excluded from parent CPU. The large remaining parent CPU supports investigating
source/OCR work but cannot attribute it precisely. The detector child runs four
Torch threads on CPU; native OCR also uses four threads with one admitted call.

The operational whole-run parent reports 1281.413 wall seconds, 1288.233 CPU seconds
and 758.383 MiB peak sampled RSS. Whole-run bookkeeping and detector initialization
are outside individual page wall totals. The detector's one-time child initialization
is retained separately: 2.911 wall / 6.578 CPU seconds. Its maximum sampled worker RSS
across inference calls is 1187.758 MiB. Parent RSS is sampled with psutil every 100 ms;
worker RSS uses `/proc/self/statm` every 100 ms plus endpoints and lifetime getrusage
peaks. Peak values are maxima, never sums; simultaneous combined peak memory is
unmeasured. Local preprocessing and remote waiting are separated; hosted GPU usage
is unmeasured. These are retained observations from one serial run, not independent
replications or a throughput confirmation experiment.

The CPU-only audit itself took 6.541 wall / 6.514 CPU seconds, with 51.840 MiB peak
sampled process RSS and 395.586 MiB process-lifetime peak RSS. Its scoped sampler
starts after imports, whereas lifetime peak includes them. It performed no OCR,
detector worker calls, PDF rendering, API calls or credential access. Relevant
assembly, region and detector module hashes exactly match the frozen run. Root's
ordinary native sanitizer was applied before the proof, retaining quarantine
warnings. All reads derive from the explicit frozen record IDs; no corpus discovery
or references are needed.

A useful next performance target is the API stage, preserving requested work and
quality; detector removal even without this restricted guard would have only a
6.37% ideal page-wall ceiling. This audit authorizes no broader skip, altered OCR
resolution, parallel paid requests, or inference-cache timing claim.

Eight focused tests pass, plus Ruff and explicit-file mypy. Tests cover ownership,
outside/mixed/invalid/merged/zero-word cases, scope refusal, completed-report gating,
cached equivalence and nonadditive nested timing/RSS accounting. Reproduce with:

```sh
python -m bench.pipeline_native_fastpath \
  --run bench/results/pdf-master-artifacts/pipeline-p002/full276-yolo-matrix-haiku-512 \
  --native-run bench/results/pdf-master-artifacts/pipeline-p002/native-regional-full-r2 \
  --output bench/results/pdf-master-artifacts/pipeline-p002/native-detector-fastpath
```

The full local JSON is ignored at `pipeline-p002/native-detector-fastpath/audit.json`,
including every intended page, eligibility reason, cached source/native preservation,
complete stage summaries, module/frozen/result hashes and separately scoped resources.
Final aggregation requires the completed report and every intended result; optional
partial audits remain explicitly incomplete.
