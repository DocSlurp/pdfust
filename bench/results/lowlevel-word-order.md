# Deterministic word-order repair after the lower-level DEV experiment

The source-history control exposed an extraction bug that can be repaired without a decision model. Keep all frozen hosted observations on their original pre-fix evidence. Candidate commits are `da75b2b` followed by `4987427` on `experiment/lowlevel-native`; the private glyph snapshot hook is unchanged, and the root extension was never rebuilt by this agent.

## Failure, shrink and cause

Of the 12 logical history controls crossed with three content encodings, the three `new_identifier` reverse-positioned cases corrupted the final description word. For example, ordinary/TJ-array extraction retained `105` and `pressure-rated fittings`, whereas reverse painting produced identifier fragments `1` / `05` and tail words `s` / `pressure-rated` / `fitting`. The pixels and canonical mapped glyph geometry were unchanged.

A four-glyph, one-baseline PDF is sufficient. The display glyphs are `1@40`, `2@46`, `A@100`, `B@106`, each with advance 6. Callback order `2@46, 1@40, B@106, A@100` gave:

```text
1 B
2
A
```

instead of `12 AB`. The old paint-run detector split backward resets but retained forward jumps. It therefore joined `1@40` and `B@106` into one run, then treated the run's entire bounding interval as painted. That broad interval falsely overlapped intervening `2` and `A`, producing extra logical layers and changing word membership. This is a native clustering error; semantic row ownership and history interpretation are separate questions.

## Repair and bounded work

The first repair adds a run boundary at a forward gap exceeding the existing `WORD_GAP` threshold. It retains source-order layers for genuine overprints. Each layer caches its interval envelope, so a new interval outside the envelope skips the previous linear scan; monotone sparse runs do not turn quadratic as their count grows.

A subsequent allocation diagnostic motivated the second commit. Before source-run detection, a no-allocation preflight checks adjacent glyph advances in the existing geometry sequence. If all glyphs have exactly the same direction and their inline intervals are monotonically disjoint, geometry directly establishes their order. The function returns one geometry-sorted line without allocating run/layer vectors. Equal origins and any interval overlap take the original overlap path; unusually narrow repeated glyphs are not admitted by this fast path. Both ascending and descending geometry sequences are supported, including right-angle rotations. Mixed direction, overlapping glyphs and nonmonotone geometry retain layer analysis.

The preflight is linear, uses borrowed arena records and allocates only the existing fallible result vector on acceptance. It does not clone glyphs/text, alter glyph admission, change cached bidi properties, deduplicate overprints, reinterpret original operators or infer row ownership. Source-order IDs remain snapshot-local accepted callback ordinals. The fixes preserve every mapped glyph while changing the erroneous partition/order.

## Verification

Before the repair, all 16 original rotation/phrase regressions failed against the frozen extension. After `da75b2b`, the complete suite passed **2082 tests**, with **22 optional skips** and **2 known expected failures**, in 69.98 seconds. This included Arabic/Hebrew/CJK/Thai locale fonts and existing bidi/RTL, overprint, layout, table, Markdown, limit and real-world coverage. Locale provider packages, NumPy and the explicit Rust compiler were needed to resolve initial environment-only test failures; those failed attempts were not presented as product regressions.

After `4987427`, the relevant extraction/layout/table/spatial/Markdown/limit/real-world suites passed **440 tests**, with **8 optional skips** and the same **2 expected failures**. New coverage includes all **24 permutations** of the four-glyph minimal case, four page rotations, all three affected phrases, overprint multiplicity and 256 sparse fields in both directions. Clippy, formatting, Ruff and targeted mypy passed. Per the bounded follow-up scope, the entire 2082-test suite was not repeated after the equivalent disjoint preflight; final targeted coverage includes the changed seam and existing overprint/RTL/CJK extraction behavior.

Final replay of all **12 logical history cases × three encodings** now has identical complete plain text, word text/geometry/membership and canonical glyph records, excluding intentional callback-ordinal differences. Every default text hash on the explicit original104 DEV manifest (104 PDFs/125 pages) and the original cohort72 also matches the pre-fix baseline. Original104 hashes were verified through the DEV manifest; no protected held-out paths were read, enumerated or searched.

## CPU and memory diagnostics

The first candidate's five balanced process blocks used matching CPython 3.12.15 release builds, fresh Documents, `RAYON_NUM_THREADS=1`, one Python worker, and the previous explicit original104/cohort72 harness. Each process traversed original104 ten times and cohort72 thirty times. Baseline `2f563f3` has the same normal extraction implementation as the pre-fix snapshot build; the appended private hook does not enter this normal path. The median paired candidate/baseline wall ratios were **0.970** on original104 (0.911–1.124) and **1.003** on cohort72 (0.974–1.110). Median process peak RSS was **33.80 MiB** candidate versus **33.79 MiB** baseline. These small, noisy measurements support no performance gain claim. Full per-document hashes, process CPU time, wall time, peak RSS and environment are in `word-order/performance.json`.

An initial sparse diagnostic found avoidable allocations in `da75b2b`: at 4096 widely spaced, individually painted glyphs, its median was 8.84 ms versus an earlier baseline's 5.77 ms. `4987427` removes those run allocations by construction. A fresh, alternating **five-process-pair** comparison measured final medians of 9.27 ms versus matched baseline 9.49 ms at 4096 glyphs; ranges were broad (final 6.73–11.94 ms, baseline 6.42–10.94 ms) on the shared host. Thus no residual slowdown is established, and these measurements do not prove a speedup. The 512/1024/2048/4096 series retained all glyphs and words and supports linear workload growth, rather than the quadratic interval scan that was explicitly avoided.

Measurements use `perf_counter`, `process_time` and Linux `getrusage` for whole-process/thread CPU and high-water RSS; `/usr/bin/time` is unavailable. Kernel high-water RSS has no polling interval. Workload timings exclude input generation/import setup; process peaks include both. No GPU, training, hosted inference or credential access was involved. The final preflight received a corpus hash replay and matched sparse diagnostic; the macro CPU/RSS figures above belong to the first candidate, not an unmeasured final macro timing claim. An accidentally concurrent test/benchmark pilot was stopped, retained as `performance-concurrent-tests-pilot.json`, and excluded; the complete five-block macro schedule was rerun after tests ended.

## Recommendation

Integrate both commits after frozen inference waves finish, then retain the old paid evidence and run a separately identified post-fix control. The changed word IDs/partitions must not silently replace pre-fix decision contexts. This deterministic repair removes the specific need to ask a model to reconstruct glyphs lost from a word through clustering. It does not establish whether a continuation belongs to the previous row, whether a header governs a value, or whether history provides enough semantic evidence to resolve an intentionally ambiguous case.

The report and raw diagnostics are under `.scratch/council/lowlevel-architect/word-order*`. Source/test commits are ready for review; root extension and paid artifacts remain unchanged.
