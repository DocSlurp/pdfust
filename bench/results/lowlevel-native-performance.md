# Private glyph snapshot: allocation, conservation and CPU audit

The opt-in snapshot preserves the admitted interpreted-glyph evidence on these DEV inputs and adds measurable extraction cost. Keep it experimental. No new normal-path work was introduced in the source diff; the measured revision comparison supports no material slowdown on these small authored workloads, but does not prove zero overhead or an extraction speedup.

## Fixed comparison and results

Five balanced, interleaved independent-process blocks compared pre-hook `2f563f3` normal extraction, hook `d41311a` normal extraction and **the same hook build** snapshot plus normal extraction. The integrated `0dcfab2` hook has an identical diff for the four owned files. Each block used fresh Documents, repeating original104 ten times and cohort72 thirty times. Per-corpus values below normalize each block's totals by its repeat count; ranges retain all five valid blocks.

| Workload / arm | Median wall seconds per corpus (range) | Median process CPU seconds per corpus |
| --- | --- | --- |
| original104, old text | 0.16850 (0.16445–0.17167) | 0.16770 |
| original104, new text | 0.16261 (0.16053–0.16971) | 0.16217 |
| original104, new snapshot + text | 0.33810 (0.33583–0.34814) | 0.33659 |
| cohort72, old text | 0.01566 (0.01504–0.01695) | 0.01655 |
| cohort72, new text | 0.01589 (0.01446–0.01632) | 0.01680 |
| cohort72, new snapshot + text | 0.02675 (0.02444–0.02749) | 0.02743 |

The median paired snapshot-plus-text/new-text wall ratios were **2.09×** (1.99–2.14×) on original104 and **1.68×** (1.50–1.87×) on cohort72. These measure additional interpretation and Python/Rust evidence materialization. Snapshot-only cost was not separately measured. Normal extraction already batches pages through one interpreter cache; the snapshot is intentionally a fresh one-page interpretation and does not fill that text cache.

Median paired new/old normal-text wall ratios were 0.976 (0.947–0.993) and 0.961 (0.945–1.042). Small differences, five process blocks and shared-host scheduling do not support claiming a performance improvement. The median-of-arm and median-of-paired-ratio summaries differ because their operations differ; raw paired observations are retained.

Process-wide peak RSS across both workloads was **33.75 MiB** old text (33.68–33.96), **33.76 MiB** new text (33.60–33.79), and **34.60 MiB** snapshot plus text (34.50–34.73). This is about 0.84 MiB additional median peak in this serial small-document exercise; it is not a 65,536-glyph or concurrent-memory bound. CPU/wall ratios were about 100% on original104 and 102–106% on cohort72. Every worker ended with two OS threads, consistent with the main thread plus the requested single Rayon worker; CPU accounting covers all threads in that process.

## Inputs, oracle and provenance

Original104 was read exclusively through its explicit **DEV** manifest:
`bench/results/pdf-master-artifacts/silver-v1/2e3b8c00f83375cc/manifest.json`.
All 104 PDF hashes were verified; it comprises 125 pages and yielded **56,084 admitted mapped glyphs** per traversal. No protected held-out locations were read, enumerated or searched. The authored `bench.lowlevel_cases.cases()` cohort contains 24 logical cases crossed with three encodings, totaling 72 PDFs/pages and **1,935 admitted mapped glyphs**.

All default text hashes matched exactly between old text, new text and snapshot-plus-text for every repeated document. On every snapshot document, the multiset of mapped non-whitespace Unicode characters equaled the non-whitespace characters of default extraction: no admitted mapped character was added or lost. This oracle preserves multiplicity, including overprints and multi-character mappings; it does not establish reading order, semantics, whitespace reconstruction or coverage of unmapped glyphs. Original104 emitted its existing skipped-no-Unicode warning; the gap remains.

Across all 24 logical controls, sorted glyph records matched across runs, TJ arrays and reverse-positioned painting at absolute numeric tolerance **1e-4**. Compared fields were mapping, origin, size, advance, direction, font key/name/flags and draw mode; source-order ordinals were intentionally excluded. This verifies retained glyph evidence under these authored encoding transformations, not original operator identity. The source mapping is snapshot-local: reversing callback order changes ordinals and glyph-to-ordinal association. The hook conserves accepted callback records, not every PDF glyph/operator or visible pixel.

Machine: Intel i7-7700K, eight logical CPUs, Linux 7.2.5, about 62.7 GiB RAM; matching CPython 3.12.15 interpreters; optimized release extension builds with Rust 1.99.0. Documents were processed sequentially with one Python worker and `RAYON_NUM_THREADS=1`. Inputs were loaded before workload timing; file/OS caches were not dropped. Import/input setup are included only in process-total fields, not workload times. Extension hashes and exact commands are in `performance.json`.

`/usr/bin/time` is absent on this host. Measurements use `time.perf_counter`, `time.process_time` and Linux `resource.getrusage`: process CPU includes user/system and all process threads, and RSS is the kernel process high-water mark, with no sampling interval. Driver process-total CPU uses child accounting. No GPU, network inference or hosted request was involved.

An initial pilot retained all worker JSON in the launcher and contaminated later child peak RSS through inherited launch high-water memory. Its observations are retained separately in `performance-invalid-rss-pilot.json` and excluded from the results above. The fixed launcher retains only file paths while measuring and aggregates after all children exit. The complete five-block schedule was rerun for all arms; no timing outlier was removed from the valid run.

## Allocation and admission review

The wrapper adds no collector fields, branch or collection to ordinary extraction. Snapshot glyph/text/mode/row vectors and owned text/font copies grow fallibly. Accepted glyphs are capped at 65,536, Unicode payload at 1 MiB, repeated copied font-name payload at 1 MiB, and font-key output at 32 bytes per admitted row. Modes are recorded only after a glyph was retained; failure prevents returning any zipped partial rows. Output is owned and remains immutable after document edits/close. No text/table cache is installed by this hook.

Collection, row allocation and metadata refusal precede document admission. The detached hayro snapshot is restored on success and mapped error; the interpreter cache remains call-local. Document cumulative text/glyph usage is shared by page and is not charged again by later normal/table interpretations. Existing admission's internal maps and hayro/font Unicode allocation are inherited implementation behavior, so this private API is not a claim of universally fallible parsing. Python object conversion happens after native admission: Python allocation failure may leave a successfully interpreted page admitted, just as other structured-output paths do.

Finite snapshot output budgets do **not** cap total upstream interpreter CPU, decoded PDF input, skipped/unmapped/empty/nonfinite glyph callbacks, or all upstream allocations. Those require DocumentLimits and potentially a later callback budget. The fixed font-name ceiling refuses complete output with PdfError rather than a dedicated metadata LimitError code. Font keys are interpretation cache identities, not stable PDF object IDs; Type3 has the existing zero/unknown key and approximate metrics.

A direct private `_Document` call bypasses Python locale-provider initialization and warning delivery. Bench callers must run `doc._ensure_fallback_fonts()` before snapshotting and `doc._emit_warnings()` afterward to match public extraction settings. This is a caller integration requirement, not a Rust default-behavior change; the measured Standard14 controls have no locale providers and showed identical normal output. Marked-content tags/inline MCIDs are available in hayro but were intentionally omitted from the minimal hook. Original stream IDs, text-show operation boundaries, mapping fallback provenance and clip-resolved visibility remain unavailable.

No additional tracked-file fix was justified by this audit. The next useful implementation improvement, if experiments justify it, is an explicitly owned replay path that derives candidate partitions from one admitted glyph snapshot and avoids a second hayro interpretation. Its correctness and output-resource gates should be measured before integrating any model choice.

## Reproduction

Run the fixed launcher with the existing matching worktree environments, then aggregate:

```sh
/home/dan/code/oss/jev-pdf-lowlevel-native/.venv/bin/python .scratch/council/lowlevel-architect/run_blocks.py
/home/dan/code/oss/jev-pdf-lowlevel-native/.venv/bin/python .scratch/council/lowlevel-architect/summarize.py
```

Raw observations, valid per-process output hashes/CPU/RSS, canonical comparison and summaries are retained in `performance.json`, individual `block-*.json` files and `canonical.json`. The runners and their hashes are preserved beside this report. These are DEV screening measurements, with no independent producer or maximum-capacity validation.
