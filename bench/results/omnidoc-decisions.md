# OmniDocBench DEV image-presence pilot

16 official research-only public page images; 256 logical requests across four decision models, arms ['rgb128', 'rgb512', 'rgb1200', 'blank512']. JPEG80 is explicitly lossy evidence with unchanged full-page dimensions. No annotation text or filenames in request bodies. This tests table/math/multicolumn presence, not extraction or full table reconstruction. Public benchmark contamination unknown.

| Model / arm | Completed / 16 | q0 TP/TN/FP/FN | q1 TP/TN/FP/FN | q2 TP/TN/FP/FN | q2 unknown | USD | Pages/$ | Pages/min |
|---|---:|---|---|---|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions/rgb128 | 16/16 | 4/11/1/0 | 0/14/1/1 | 6/4/1/1 | 4 | 0.0009232 | 17331.02253032929 | 201.50351981588884 |
| openai/gpt-6-luna-decisions/rgb512 | 16/16 | 4/10/2/0 | 1/14/1/0 | 5/4/1/2 | 4 | 0.0012143999999999998 | 13175.230566534916 | 170.74018086296226 |
| openai/gpt-6-luna-decisions/rgb1200 | 10/16 | 3/6/1/0 | 1/9/0/0 | 2/4/1/1 | 4 | 0.0015937999999999998 | 6274.312962730582 | 142.4461978545092 |
| openai/gpt-6-luna-decisions/blank512 | 16/16 | 0/16/0/0 | 0/16/0/0 | 0/16/0/0 | 0 | 0.0007608 | 13144.058885383807 | 197.64763148858862 |
| perplexity/pplx-decider-v1.1-27b/rgb128 | 16/16 | 4/10/2/0 | 0/14/1/1 | 6/4/1/1 | 4 | 0.00019203999999999998 | 83315.97583836701 | 183.10500460251873 |
| perplexity/pplx-decider-v1.1-27b/rgb512 | 16/16 | 4/11/1/0 | 1/14/1/0 | 7/4/1/0 | 4 | 0.0002992 | 53475.935828877 | 115.03193085820983 |
| perplexity/pplx-decider-v1.1-27b/rgb1200 | 10/16 | 3/6/1/0 | 1/9/0/0 | 2/4/1/1 | 4 | 0.00069052 | 14481.839772924752 | 98.3209140697923 |
| perplexity/pplx-decider-v1.1-27b/blank512 | 16/16 | 0/16/0/0 | 0/16/0/0 | 0/16/0/0 | 0 | 0.00018952 | 52764.8796960743 | 190.66043412925507 |
| cloudflare/clef-flash/rgb128 | 16/16 | 4/10/2/0 | 0/14/1/1 | 5/4/1/2 | 4 | 0.0006039 | 26494.45272396092 | 152.33036839885628 |
| cloudflare/clef-flash/rgb512 | 15/16 | 4/11/0/0 | 1/13/1/0 | 4/4/1/3 | 4 | 0.0007146 | 20990.764063811923 | 129.38258036707012 |
| cloudflare/clef-flash/rgb1200 | 3/16 | 0/2/1/0 | 0/3/0/0 | 0/3/0/0 | 4 | 0.00035928 | 8350.0334001336 | 127.88782684745576 |
| cloudflare/clef-flash/blank512 | 16/16 | 0/16/0/0 | 0/16/0/0 | 0/16/0/0 | 0 | 0.00048168 | 20760.67098488623 | 131.77446304611223 |
| cloudflare/clef/rgb128 | 16/16 | 4/7/5/0 | 0/14/1/1 | 6/4/1/1 | 4 | 0.0016104000000000001 | 9935.419771485345 | 115.80782478030389 |
| cloudflare/clef/rgb512 | 15/16 | 4/8/3/0 | 1/13/1/0 | 6/4/1/1 | 4 | 0.0019056 | 7871.5365239294715 | 85.31137916396779 |
| cloudflare/clef/rgb1200 | 3/16 | 0/2/1/0 | 0/2/1/0 | 0/3/0/0 | 4 | 0.00095808 | 3131.2625250501 | 58.39930328415154 |
| cloudflare/clef/blank512 | 16/16 | 0/16/0/0 | 0/16/0/0 | 0/16/0/0 | 0 | 0.00128448 | 7785.251619332337 | 118.8208058538788 |

Unique metered requests: 192; effective total USD: 0.0137815; known partial USD: 0.0137815. Charges are deduplicated by shared-ledger request index across the entire pilot.

Every confusion cell, unscored count, refusal, failed response and unknown label is retained in evaluation.json. Missing requests remain in the 16-page denominator. Layout labels other than explicit single/multiple columns are unknown. Blank controls expect all three features absent. Threshold 0.5 is frozen and probability is not calibrated correctness. Pages/min counts serial transmitted page observations per total HTTP time; prep and replay are excluded. Pages/$ uses unique completed provider page requests per known effective cost; local replay adds no throughput. Incomplete charge estimates never become complete totals. Positive provider charges win; zero/missing uses frozen catalog rates with reported token counts when available. Reservations are separate admission accounting.

Preparation CPU/RAM: {'cpu_seconds': 23.208450734000003, 'logical_cpus': 8, 'peak_rss_bytes': 556265472, 'platform': 'Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44', 'sampling': 'OS cumulative counters/high water, no periodic sampling', 'scope': 'current-exec CPU RGB resize/encode, lossless transport, body admission/artifact preparation', 'tool': 'perf_counter/process_time; /proc/self/status VmHWM (current executable)', 'wall_seconds': 23.282554795994656, 'workers': 1}. Shared ledger and run.lock; incremental cap $0.50, $0.30 reservation means no new request after $0.20 of accounted charges. Oversized payloads are honestly refused; lossless WebP may preserve Clef transport pixels, with no implicit crop/resize fallback. No automatic retries.
