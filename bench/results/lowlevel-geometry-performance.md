# Conditional public drawing gate cost

On the exact root `lowlevel-v1/basic-final` 72 authored PDFs, all 72 fresh public `get_drawings()` + existing `grouping()` decisions matched the frozen source-only `hybrid-basic/routing-before-scoring.json` before timing. All 720 timed gate/snapshot decisions also matched. No targets, gold labels or model outcomes were read.

Five serial repetitions per method used fresh Documents, preloaded PDF bytes and retained selectors, alternating method order. Medians for all 72 pages:

| Phase | Wall ms | Process CPU ms |
|---|---:|---:|
| Document open | 5.930 | 21.783 |
| Public get_drawings interpretation/materialization | 13.051 | 25.342 |
| Public-key projection + existing grouping | 2.198 | 2.258 |
| Document close | 0.449 | 0.471 |
| Complete drawing gate pass, including measurement/record overhead | **22.937** | **52.942** |
| Complete existing glyph/word/drawing/operator/render/crop snapshot pass | **4,613.789** | **4,624.683** |

The gate's complete wall time is 201× lower on these inputs, about 0.319ms/page versus 64.080ms/page for full snapshot preparation. Interpretation plus grouping alone totals approximately 15.25ms per 72 pages (sum of phase medians). Complete gate wall range was 22.287–24.169ms; full snapshot range was 4.495–4.879s. Phase medians do not exactly sum to the complete-pass median.

This prices a gate **given the retained two target boxes and task selector**. It does not price target discovery, full text extraction, production layout preparation, end-to-end conversion or a hosted cascade. The snapshot comparator includes unused glyphs, words, operators, full-page rasterization and two PNG crops; paying for those is unnecessary for this particular drawing gate. The result does not establish semantic correctness or corpus-wide speedup.

Measurement: `perf_counter`, `process_time`, Linux process VmHWM, no sampling. One serial benchmark caller; library native concurrency remains at defaults. A separate minimal same-extension/source probe observed 1 thread before Document open and 9 afterward (8 native workers), explaining why process CPU exceeds gate wall; original benchmark thread counts were not sampled. Python 3.14.7, Linux x86_64, 8 available CPUs/affinity CPUs. The machine was shared with root's inference activity; this is not an isolated-host result. No agent network/GPU/credential use.

Mixed-process peak VmHWM was 154,013,696 bytes (146.9MiB). The first gate pass, before any full snapshot, reached 57,466,880 bytes (54.8MiB). Later gate VmHWM includes earlier snapshot peaks, so these are process observations rather than independently isolated memory comparisons. PDF file reads, source hash/selector verification and initial routing checks were outside timed passes. Docs were reopened for every page and pass; retained document caches were not reused.

Reproduction: root `.venv/bin/python .scratch/council/lowlevel-architect/geometry-perf/run.py`. Full per-page/per-pass timing, source/routing hashes, routing assertions and context are in `geometry-perf/raw.json`; stdout is `geometry-perf/stdout.jsonl`. No tracked files or native code changed.
