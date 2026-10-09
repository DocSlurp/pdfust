# OmniDocBench DEV image-presence pilot

Preparation only: 216 admitted requests, 40 payload refusals, zero hosted calls. The frozen manifest and request hashes remain in ignored `bench/results/pdf-master-artifacts/decisions/omnidoc-dev-presence-v3/`.

16 official research-only public page images; 256 logical requests across four decision models, RGB maximum edges 128/512/1200 and matched blank512. No annotation text or filenames in request bodies. This tests table/math/multicolumn presence, not extraction or full table reconstruction. Public benchmark contamination unknown.

| Model / arm | Completed / 16 | q0 TP/TN/FP/FN | q1 TP/TN/FP/FN | q2 TP/TN/FP/FN | q2 unknown | USD | Pages/$ | Pages/min |
|---|---:|---|---|---|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions/rgb128 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| openai/gpt-6-luna-decisions/rgb512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| openai/gpt-6-luna-decisions/rgb1200 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| openai/gpt-6-luna-decisions/blank512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 0 | 0 | None | None |
| perplexity/pplx-decider-v1.1-27b/rgb128 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| perplexity/pplx-decider-v1.1-27b/rgb512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| perplexity/pplx-decider-v1.1-27b/rgb1200 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| perplexity/pplx-decider-v1.1-27b/blank512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 0 | 0 | None | None |
| cloudflare/clef-flash/rgb128 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef-flash/rgb512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef-flash/rgb1200 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef-flash/blank512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 0 | 0 | None | None |
| cloudflare/clef/rgb128 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef/rgb512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef/rgb1200 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef/blank512 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 0 | 0 | None | None |

Unique metered requests: 0; effective total USD: 0; known partial USD: 0. Charges are deduplicated by shared-ledger request index across the entire pilot.

Every confusion cell, unscored count, refusal, failed response and unknown label is retained in evaluation.json. Missing requests remain in the 16-page denominator. Layout labels other than explicit single/multiple columns are unknown. Blank controls expect all three features absent. Threshold 0.5 is frozen and probability is not calibrated correctness. Pages/min counts serial transmitted page observations per total HTTP time; prep and replay are excluded. Pages/$ uses logical completed observations per known effective cost; replay can improve it and remains labeled. Incomplete charge estimates never become complete totals. Positive provider charges win; zero/missing uses frozen catalog rates with reported token counts when available. Reservations are separate admission accounting.

Preparation CPU/RAM: {'cpu_seconds': 24.023952668, 'logical_cpus': 8, 'peak_rss_bytes': 556531712, 'platform': 'Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44', 'sampling': 'OS cumulative counters/high water, no periodic sampling', 'scope': 'current-exec CPU RGB resize/encode, lossless transport, body admission/artifact preparation', 'tool': 'perf_counter/process_time; /proc/self/status VmHWM (current executable)', 'wall_seconds': 24.11456219200045, 'workers': 1}. Shared ledger and run.lock; incremental cap $0.50, $0.30 reservation means no new request after $0.20 of accounted charges. Oversized payloads are honestly refused; lossless WebP may preserve Clef transport pixels, with no implicit crop/resize fallback. No automatic retries.
