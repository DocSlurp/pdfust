# Preliminary schema-limited pilot — superseded

Stopped after discovering the text state used an undocumented object form. Images and questions had documented fields and HTTP responses succeeded, but interpretation of the text context is unverified. These are retained exploratory results, not the primary comparison. Corrected plain-string requests are frozen separately in v4.

# OmniDocBench DEV image-presence pilot

16 official research-only public page images; 256 logical requests across four decision models, arms ['rgb128', 'rgb512', 'rgb1200', 'blank512']. JPEG80 is explicitly lossy evidence with unchanged full-page dimensions. No annotation text or filenames in request bodies. This tests table/math/multicolumn presence, not extraction or full table reconstruction. Public benchmark contamination unknown.

| Model / arm | Completed / 16 | q0 TP/TN/FP/FN | q1 TP/TN/FP/FN | q2 TP/TN/FP/FN | q2 unknown | USD | Pages/$ | Pages/min |
|---|---:|---|---|---|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions/rgb128 | 6/16 | 2/3/1/0 | 0/4/1/1 | 2/1/0/1 | 4 | 0.00035079999999999996 | 17103.762827822124 | 140.7545051969585 |
| openai/gpt-6-luna-decisions/rgb512 | 6/16 | 2/3/1/0 | 1/5/0/0 | 2/1/0/1 | 4 | 0.0004584 | 13089.005235602095 | 153.48139723901448 |
| openai/gpt-6-luna-decisions/rgb1200 | 4/16 | 1/3/0/0 | 1/3/0/0 | 1/1/0/0 | 4 | 0.0006353999999999999 | 6295.247088448222 | 134.6155150020024 |
| openai/gpt-6-luna-decisions/blank512 | 6/16 | 0/6/0/0 | 0/6/0/0 | 0/6/0/0 | 0 | 0.0003056 | 19633.50785340314 | 168.26484397514378 |
| perplexity/pplx-decider-v1.1-27b/rgb128 | 6/16 | 2/3/1/0 | 0/5/0/1 | 2/1/0/1 | 4 | 7.608e-05 | 78864.35331230283 | 179.94630006442128 |
| perplexity/pplx-decider-v1.1-27b/rgb512 | 6/16 | 2/4/0/0 | 1/5/0/0 | 2/1/0/1 | 4 | 0.00011460000000000001 | 52356.02094240837 | 115.66767825339811 |
| perplexity/pplx-decider-v1.1-27b/rgb1200 | 4/16 | 1/3/0/0 | 1/3/0/0 | 1/1/0/0 | 4 | 0.00027748 | 14415.453366008362 | 13.577213237888285 |
| perplexity/pplx-decider-v1.1-27b/blank512 | 6/16 | 0/6/0/0 | 0/6/0/0 | 0/6/0/0 | 0 | 7.672000000000001e-05 | 78206.46506777893 | 197.4888385736026 |
| cloudflare/clef-flash/rgb128 | 6/16 | 2/3/1/0 | 0/5/0/1 | 2/1/0/1 | 4 | 0.00023094 | 25980.774227071965 | 131.18863303963533 |
| cloudflare/clef-flash/rgb512 | 6/16 | 2/4/0/0 | 1/5/0/0 | 1/1/0/2 | 4 | 0.00028872 | 20781.37988362427 | 105.28754362897179 |
| cloudflare/clef-flash/rgb1200 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef-flash/blank512 | 6/16 | 0/6/0/0 | 0/6/0/0 | 0/6/0/0 | 0 | 0.00019296 | 31094.52736318408 | 133.08338125257362 |
| cloudflare/clef/rgb128 | 6/16 | 2/2/2/0 | 0/5/0/1 | 2/1/0/1 | 4 | 0.00061584 | 9742.790335151987 | 111.59221023774577 |
| cloudflare/clef/rgb512 | 6/16 | 2/3/1/0 | 1/5/0/0 | 2/1/0/1 | 4 | 0.00076992 | 7793.017456359103 | 83.65089089736398 |
| cloudflare/clef/rgb1200 | 0/16 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 4 | 0 | None | None |
| cloudflare/clef/blank512 | 6/16 | 0/6/0/0 | 0/6/0/0 | 0/6/0/0 | 0 | 0.00051456 | 11660.447761194031 | 131.781093688775 |

Unique metered requests: 72; effective total USD: 0.00490802; known partial USD: 0.00490802. Charges are deduplicated by shared-ledger request index across the entire pilot.

Every confusion cell, unscored count, refusal, failed response and unknown label is retained in evaluation.json. Missing requests remain in the 16-page denominator. Layout labels other than explicit single/multiple columns are unknown. Blank controls expect all three features absent. Threshold 0.5 is frozen and probability is not calibrated correctness. Pages/min counts serial transmitted page observations per total HTTP time; prep and replay are excluded. Pages/$ uses logical completed observations per known effective cost; replay can improve it and remains labeled. Incomplete charge estimates never become complete totals. Positive provider charges win; zero/missing uses frozen catalog rates with reported token counts when available. Reservations are separate admission accounting.

Preparation CPU/RAM: {'cpu_seconds': 24.023952668, 'logical_cpus': 8, 'peak_rss_bytes': 556531712, 'platform': 'Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44', 'sampling': 'OS cumulative counters/high water, no periodic sampling', 'scope': 'current-exec CPU RGB resize/encode, lossless transport, body admission/artifact preparation', 'tool': 'perf_counter/process_time; /proc/self/status VmHWM (current executable)', 'wall_seconds': 24.11456219200045, 'workers': 1}. Shared ledger and run.lock; incremental cap $0.50, $0.30 reservation means no new request after $0.20 of accounted charges. Oversized payloads are honestly refused; lossless WebP may preserve Clef transport pixels, with no implicit crop/resize fallback. No automatic retries.
