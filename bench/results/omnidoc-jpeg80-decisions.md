# OmniDocBench DEV image-presence pilot

16 official research-only public page images; 64 logical requests across four decision models, arms ['jpeg80-rgb1200']. JPEG80 is explicitly lossy evidence with unchanged full-page dimensions. No annotation text or filenames in request bodies. This tests table/math/multicolumn presence, not extraction or full table reconstruction. Public benchmark contamination unknown.

| Model / arm | Completed / 16 | q0 TP/TN/FP/FN | q1 TP/TN/FP/FN | q2 TP/TN/FP/FN | q2 unknown | USD | Pages/$ | Pages/min |
|---|---:|---|---|---|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions/jpeg80-rgb1200 | 16/16 | 4/12/0/0 | 1/15/0/0 | 7/4/1/0 | 4 | 0.0025934 | 6169.507210611552 | 128.65916504115108 |
| perplexity/pplx-decider-v1.1-27b/jpeg80-rgb1200 | 16/16 | 4/11/1/0 | 1/15/0/0 | 5/4/1/2 | 4 | 0.00112672 | 14200.511218403864 | 113.81644522066567 |
| cloudflare/clef-flash/jpeg80-rgb1200 | 7/16 | 1/5/1/0 | 0/7/0/0 | 3/4/0/0 | 4 | 0.00084024 | 8330.95306103018 | 119.22799302243519 |
| cloudflare/clef/jpeg80-rgb1200 | 7/16 | 1/4/2/0 | 0/6/1/0 | 3/4/0/0 | 4 | 0.0022406400000000003 | 3124.107397886318 | 76.43005629198522 |

Unique metered requests: 46; effective total USD: 0.006801; known partial USD: 0.006801. Charges are deduplicated by shared-ledger request index across the entire pilot.

Every confusion cell, unscored count, refusal, failed response and unknown label is retained in evaluation.json. Missing requests remain in the 16-page denominator. Layout labels other than explicit single/multiple columns are unknown. Blank controls expect all three features absent. Threshold 0.5 is frozen and probability is not calibrated correctness. Pages/min counts serial transmitted page observations per total HTTP time; prep and replay are excluded. Pages/$ uses unique completed provider page requests per known effective cost; local replay adds no throughput. Incomplete charge estimates never become complete totals. Positive provider charges win; zero/missing uses frozen catalog rates with reported token counts when available. Reservations are separate admission accounting.

Preparation CPU/RAM: {'cpu_seconds': 4.096002231, 'logical_cpus': 8, 'peak_rss_bytes': 550522880, 'platform': 'Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44', 'sampling': 'OS cumulative counters/high water, no periodic sampling', 'scope': 'current-exec CPU RGB resize/encode, lossless transport, body admission/artifact preparation', 'tool': 'perf_counter/process_time; /proc/self/status VmHWM (current executable)', 'wall_seconds': 4.112955546996091, 'workers': 1}. Shared ledger and run.lock; incremental cap $0.50, $0.30 reservation means no new request after $0.20 of accounted charges. Oversized payloads are honestly refused; lossless WebP may preserve Clef transport pixels, with no implicit crop/resize fallback. No automatic retries.
