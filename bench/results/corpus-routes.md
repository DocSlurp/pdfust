# DEV corpus source-only routing screen

104 documents / 125 physical pages; fixed all-page denominator. Authored silver references are not independently reviewed gold. Scoring covers exact table cells, merged topology, unique intended-cell ownership and non-table false positives; no anchor metric.

| Route | Exact pages / 125 | Exact cells / 10 | Exact spans / 10 | Owned / 140 | Non-table FP / 115 | Unmatched tables | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| none | 115/125 | 0/10 | 0/10 | 0/140 | 0/115 | 0 | 0 |
| vector | 125/125 | 10/10 | 10/10 | 140/140 | 0/115 | 0 | 0 |
| raw-text | 98/125 | 0/10 | 0/10 | 0/140 | 17/115 | 27 | 0 |
| vector-veto | 108/125 | 10/10 | 10/10 | 140/140 | 17/115 | 17 | 0 |
| vector-paint | 125/125 | 10/10 | 10/10 | 140/140 | 0/115 | 0 | 0 |

Rules were written to a hashed freeze artifact before preparing scorer targets. The router accepts only native vector/text table observations and native drawings, never IDs, families, producer groups or references. `none` is the minimal baseline; `vector` preserves the extraction default; `raw-text` exposes ambiguity. The two conditional routes preserve vectors, reject overlapping candidates, veto cells over 8 tokens/72 characters and sentence endings, and require two rows with digits in at least two cells. `vector-paint` additionally requires two distinct horizontal stroke positions spanning at least 70% of candidate width within a 2-point tolerance.

False-positive pages by family (diagnostic grouping only; never routing inputs):
- `none`: {}
- `vector`: {}
- `raw-text`: {"reading-order": 5, "sidebar": 2, "three-column": 5, "two-column": 5}
- `vector-veto`: {"reading-order": 5, "sidebar": 2, "three-column": 5, "two-column": 5}
- `vector-paint`: {}

The vector baseline already reaches the authored table ceiling. Conditional routes cannot establish borderless recall on this cohort: there are no positive authored borderless references. Gains over raw text are rejection gains; preserving 10 vector grids is not evidence of general layout improvement. Numeric content and compact cells can still appear in prose, forms or mathematical matrices. Next hypothesis: add independently reviewed borderless tables and aligned numeric-prose negatives to DEV, then test row/column ownership and prose reading order before expanding admission. No core default was changed.

One sequential CPU run: 2.022s wall, 2.054s CPU, 101.6% of one core, peak current-exec RSS 98938880 bytes. Measurement: {'wall_seconds': 2.022389955993276, 'cpu_seconds': 2.054180851, 'cpu_utilization_pct': 101.57194684004995, 'peak_rss_bytes': 98938880, 'tool': 'perf_counter/process_time; /proc/self/status VmHWM (current executable)', 'sampling': 'cumulative counters and OS high-water mark, no periodic sampling', 'scope': 'single current executable; sequential source verification, load, both detections, paint, routing, scoring; RSS includes target preparation/imports', 'workers': 1, 'logical_cpus': 8, 'platform': 'Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44', 'python': '3.14.7', 'gpu': 'unused', 'remote_inference': 'none'}. Evidence is shared across routes, so these are quality screens, not independent route performance comparisons. No provider charges.

Dataset SHA-256 `2e3b8c00f83375cc5d5e804ebe473f9ea0926f0ac2e1153996058381fdf02d21`; rules SHA-256 `cacb457eeca5d6605e5470b7013fcfd849af1133eccba222877422e4a6bb8df3`; runner SHA-256 `ad1791875e3594f5a9b28decfea8fe15535182696b458adcbafa878000891197`. Complete observations, per-page errors and scores, frozen rules and authored targets remain in ignored `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/silver-v1/2e3b8c00f83375cc/corpus-route-runs/20261009T043100-nf5o971m`.
