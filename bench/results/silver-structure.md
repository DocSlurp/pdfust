# Authored silver table structure baseline

104 DEV documents, 125 physical pages. References are transcribed from authored generator geometry and labels, not extraction output. They are not independently reviewed gold. Only bordered tables and non-table false positives are scored; math, form semantics, prose order and full layout quality are outside this score.

| Strategy | Exact table cells | Exact merged spans | Owned values | Non-table FP pages | Unmatched tables | Errors |
|---|---:|---:|---:|---:|---:|---:|
| lines | 10/10 | 10/10 | 140/140 | 0/115 | 0 | 0 |
| text | 0/10 | 0/10 | 0/140 | 17/115 | 27 | 0 |

Exact cells include every row-major slot and the covered `None` slot. Span topology is measured separately. Ownership requires the complete authored cell value in its intended slot and exactly one occurrence across detected cells. Decorative rectangles, checkbox fields, prose panels and all math pages target zero tables. Text-strategy false positives remain counted. Unmatched candidates include partial grids on authored table pages; they are not exact complete-table recoveries.

Sequential CPU run: 1.722s wall, 1.758s CPU (102.1% of one core); peak RSS 93396992 bytes. wall/CPU: checksum reads, document load, both sequential strategies, scoring; excludes imports/target preparation/artifact writes. Peak RSS: full runner lifetime. Tool: perf_counter/process_time/os.times; /proc/self/status VmHWM (current executable). Sampling: OS cumulative counters and high-water RSS; no periodic sampling. Machine: Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44; Python 3.14.7; 8 logical CPUs; one worker. Strategy timings share a document and may reuse interpretation caches; these are not cold independent performance comparisons.

Dataset SHA-256: `2e3b8c00f83375cc5d5e804ebe473f9ea0926f0ac2e1153996058381fdf02d21`. Complete private targets, every detected table and per-page scores/resources are retained in the ignored `bench/results/pdf-master-artifacts/silver-v1/2e3b8c00f83375cc/structure-runs/20261009T035020-zc_0qv32` directory. No hosted models or model calls were used.
