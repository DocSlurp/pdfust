# Remote GPU prompt × resolution screen

All four native models returned 480/480 valid answers. Across the 20 fixed treatments, known exactness ranged 6–12/16 for Flash, 6–13/16 for Clef, 8–13/16 for PPLX and 7–12/16 for Intern. Ambiguous abstention ranged 0–2/8, 0–2/8, 0–4/8 and 0/8 respectively. PPLX RGB 640/identity reached 12/16 known and 4/8 ambiguous, compared with 10/16 and 0/8 in its matched fresh-original image baseline (four known gains/two losses; four abstention gains/no losses). No treatment resolves all eight ambiguous cases; these are DEV observations, not a selected production policy.

The four native runs used two independent model processes per GPU: Flash+Clef with OMP_NUM_THREADS=6 each and PPLX+Intern with OMP_NUM_THREADS=8 each. Per-model inference wall time includes contention. Fresh-original baselines used a different execution context; their quality comparisons remain matched, while latency differences do not isolate a prompt or resolution effect. CPU/RSS scope is each model process; GPU allocator peaks cover that process, and device-wide utilization is separate. No invoice or rental-cost inference is made from the table.

24 authored DEV regions, repeated across five sizes and four fixed prompts; not independent pages

All 504 fresh source packets and exact prompt transformations were verified before local DEV scoring. The four prompts, five RGB sizes and four native models were predeclared. No case-specific prompts were used.

| Model / treatment | Valid/planned | Known correct | Ambiguous abstention | Known abstentions | Exact partition | Conserved | Wall s | CPU s | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flash / rgb-128/sufficiency | 24/24 | 8/16 | 1/8 | 0 | 9/24 | 24/24 | 4.353 | 5.314 | 18793.5 |
| flash / rgb-128/alternatives | 24/24 | 7/16 | 1/8 | 0 | 8/24 | 24/24 | 4.406 | 5.366 | 18793.5 |
| flash / rgb-128/identity | 24/24 | 12/16 | 0/8 | 1 | 12/24 | 24/24 | 3.133 | 4.079 | 18793.5 |
| flash / rgb-128/neutral | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 | 4.567 | 5.546 | 18793.5 |
| flash / rgb-256/sufficiency | 24/24 | 7/16 | 0/8 | 0 | 7/24 | 24/24 | 3.261 | 4.229 | 18793.5 |
| flash / rgb-256/alternatives | 24/24 | 7/16 | 0/8 | 0 | 7/24 | 24/24 | 4.330 | 5.327 | 18793.5 |
| flash / rgb-256/identity | 24/24 | 9/16 | 2/8 | 0 | 11/24 | 24/24 | 3.394 | 4.350 | 18793.5 |
| flash / rgb-256/neutral | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 4.226 | 5.250 | 18793.5 |
| flash / rgb-400/sufficiency | 24/24 | 7/16 | 0/8 | 0 | 7/24 | 24/24 | 4.018 | 4.989 | 18793.5 |
| flash / rgb-400/alternatives | 24/24 | 10/16 | 0/8 | 0 | 10/24 | 24/24 | 3.568 | 4.590 | 18793.5 |
| flash / rgb-400/identity | 24/24 | 9/16 | 2/8 | 2 | 11/24 | 24/24 | 4.514 | 5.554 | 18793.5 |
| flash / rgb-400/neutral | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 3.304 | 4.287 | 18793.5 |
| flash / rgb-500/sufficiency | 24/24 | 6/16 | 0/8 | 0 | 6/24 | 24/24 | 4.272 | 5.340 | 18793.5 |
| flash / rgb-500/alternatives | 24/24 | 7/16 | 0/8 | 0 | 7/24 | 24/24 | 4.337 | 5.405 | 18793.5 |
| flash / rgb-500/identity | 24/24 | 7/16 | 1/8 | 2 | 8/24 | 24/24 | 3.601 | 4.641 | 18793.5 |
| flash / rgb-500/neutral | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 4.582 | 5.690 | 18793.5 |
| flash / rgb-640/sufficiency | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 4.267 | 5.374 | 18793.5 |
| flash / rgb-640/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 3.922 | 5.117 | 18793.5 |
| flash / rgb-640/identity | 24/24 | 7/16 | 1/8 | 2 | 8/24 | 24/24 | 5.002 | 6.146 | 18793.5 |
| flash / rgb-640/neutral | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 | 3.777 | 4.950 | 18793.5 |
| clef / rgb-128/sufficiency | 24/24 | 6/16 | 1/8 | 4 | 7/24 | 24/24 | 6.357 | 7.258 | 53029.6 |
| clef / rgb-128/alternatives | 24/24 | 8/16 | 2/8 | 1 | 10/24 | 24/24 | 5.793 | 6.728 | 53029.6 |
| clef / rgb-128/identity | 24/24 | 7/16 | 1/8 | 5 | 8/24 | 24/24 | 5.873 | 6.780 | 53029.6 |
| clef / rgb-128/neutral | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 | 5.639 | 6.548 | 53029.6 |
| clef / rgb-256/sufficiency | 24/24 | 9/16 | 1/8 | 4 | 10/24 | 24/24 | 5.957 | 6.867 | 53029.6 |
| clef / rgb-256/alternatives | 24/24 | 7/16 | 0/8 | 4 | 7/24 | 24/24 | 5.786 | 6.715 | 53029.6 |
| clef / rgb-256/identity | 24/24 | 9/16 | 2/8 | 6 | 11/24 | 24/24 | 5.895 | 6.849 | 53029.6 |
| clef / rgb-256/neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 5.691 | 6.602 | 53029.6 |
| clef / rgb-400/sufficiency | 24/24 | 11/16 | 1/8 | 4 | 12/24 | 24/24 | 5.793 | 6.743 | 53029.6 |
| clef / rgb-400/alternatives | 24/24 | 10/16 | 0/8 | 3 | 10/24 | 24/24 | 5.886 | 6.839 | 53029.6 |
| clef / rgb-400/identity | 24/24 | 8/16 | 2/8 | 8 | 10/24 | 24/24 | 5.913 | 6.879 | 53029.6 |
| clef / rgb-400/neutral | 24/24 | 13/16 | 0/8 | 0 | 13/24 | 24/24 | 5.637 | 6.622 | 53029.6 |
| clef / rgb-500/sufficiency | 24/24 | 10/16 | 1/8 | 4 | 11/24 | 24/24 | 6.065 | 7.099 | 53029.6 |
| clef / rgb-500/alternatives | 24/24 | 9/16 | 1/8 | 2 | 10/24 | 24/24 | 6.212 | 7.250 | 53029.6 |
| clef / rgb-500/identity | 24/24 | 8/16 | 1/8 | 7 | 9/24 | 24/24 | 5.937 | 6.942 | 53029.6 |
| clef / rgb-500/neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 5.747 | 6.745 | 53029.6 |
| clef / rgb-640/sufficiency | 24/24 | 11/16 | 1/8 | 3 | 12/24 | 24/24 | 6.189 | 7.266 | 53029.6 |
| clef / rgb-640/alternatives | 24/24 | 11/16 | 0/8 | 1 | 11/24 | 24/24 | 6.353 | 7.469 | 53029.6 |
| clef / rgb-640/identity | 24/24 | 8/16 | 1/8 | 6 | 9/24 | 24/24 | 6.327 | 7.432 | 53029.6 |
| clef / rgb-640/neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 6.235 | 7.335 | 53029.6 |
| pplx / rgb-128/sufficiency | 24/24 | 10/16 | 1/8 | 0 | 11/24 | 24/24 | 6.440 | 8.728 | 6075.7 |
| pplx / rgb-128/alternatives | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 | 4.955 | 7.264 | 6075.7 |
| pplx / rgb-128/identity | 24/24 | 8/16 | 2/8 | 5 | 10/24 | 24/24 | 5.115 | 7.435 | 6075.7 |
| pplx / rgb-128/neutral | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 | 4.915 | 7.235 | 6075.7 |
| pplx / rgb-256/sufficiency | 24/24 | 11/16 | 0/8 | 1 | 11/24 | 24/24 | 4.901 | 7.241 | 6075.7 |
| pplx / rgb-256/alternatives | 24/24 | 11/16 | 0/8 | 1 | 11/24 | 24/24 | 4.875 | 7.169 | 6075.7 |
| pplx / rgb-256/identity | 24/24 | 10/16 | 2/8 | 5 | 12/24 | 24/24 | 4.991 | 7.302 | 6075.7 |
| pplx / rgb-256/neutral | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 | 4.817 | 7.149 | 6075.7 |
| pplx / rgb-400/sufficiency | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 4.915 | 7.240 | 6075.7 |
| pplx / rgb-400/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 4.861 | 7.168 | 6075.7 |
| pplx / rgb-400/identity | 24/24 | 11/16 | 3/8 | 5 | 14/24 | 24/24 | 5.059 | 7.370 | 6075.7 |
| pplx / rgb-400/neutral | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 | 4.849 | 7.198 | 6075.7 |
| pplx / rgb-500/sufficiency | 24/24 | 13/16 | 0/8 | 0 | 13/24 | 24/24 | 5.077 | 7.411 | 6075.7 |
| pplx / rgb-500/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 5.043 | 7.379 | 6075.7 |
| pplx / rgb-500/identity | 24/24 | 12/16 | 2/8 | 3 | 14/24 | 24/24 | 5.208 | 7.544 | 6075.7 |
| pplx / rgb-500/neutral | 24/24 | 10/16 | 0/8 | 1 | 10/24 | 24/24 | 4.948 | 7.308 | 6075.7 |
| pplx / rgb-640/sufficiency | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 5.525 | 7.912 | 6075.7 |
| pplx / rgb-640/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 5.479 | 7.815 | 6075.7 |
| pplx / rgb-640/identity | 24/24 | 12/16 | 4/8 | 4 | 16/24 | 24/24 | 5.455 | 7.802 | 6075.7 |
| pplx / rgb-640/neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 5.385 | 7.737 | 6075.7 |
| intern / rgb-128/sufficiency | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 4.860 | 7.150 | 9084.4 |
| intern / rgb-128/alternatives | 24/24 | 7/16 | 0/8 | 0 | 7/24 | 24/24 | 3.430 | 5.734 | 9084.4 |
| intern / rgb-128/identity | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.560 | 5.860 | 9084.4 |
| intern / rgb-128/neutral | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 3.317 | 5.637 | 9084.4 |
| intern / rgb-256/sufficiency | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.544 | 5.887 | 9084.4 |
| intern / rgb-256/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 3.657 | 5.994 | 9084.4 |
| intern / rgb-256/identity | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 | 3.507 | 5.826 | 9084.4 |
| intern / rgb-256/neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.318 | 5.606 | 9084.4 |
| intern / rgb-400/sufficiency | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.475 | 5.810 | 9084.4 |
| intern / rgb-400/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 3.729 | 6.050 | 9084.4 |
| intern / rgb-400/identity | 24/24 | 10/16 | 0/8 | 2 | 10/24 | 24/24 | 3.448 | 5.769 | 9084.4 |
| intern / rgb-400/neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.506 | 5.822 | 9084.4 |
| intern / rgb-500/sufficiency | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.622 | 5.933 | 9084.4 |
| intern / rgb-500/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 3.345 | 5.661 | 9084.4 |
| intern / rgb-500/identity | 24/24 | 9/16 | 0/8 | 2 | 9/24 | 24/24 | 3.690 | 6.005 | 9084.4 |
| intern / rgb-500/neutral | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.446 | 5.739 | 9084.4 |
| intern / rgb-640/sufficiency | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 | 3.435 | 5.781 | 9084.4 |
| intern / rgb-640/alternatives | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 | 3.931 | 6.267 | 9084.4 |
| intern / rgb-640/identity | 24/24 | 10/16 | 0/8 | 1 | 10/24 | 24/24 | 3.507 | 5.848 | 9084.4 |
| intern / rgb-640/neutral | 24/24 | 11/16 | 0/8 | 1 | 11/24 | 24/24 | 3.777 | 6.112 | 9084.4 |

| Model / treatment | Fresh-original known correct | Known gains/losses | Ambiguity gains/losses | Unpaired |
|---|---:|---:|---:|---:|
| flash / rgb-128/sufficiency | 8/16 | 3/3 | 1/0 | 0 |
| flash / rgb-128/alternatives | 8/16 | 2/3 | 1/0 | 0 |
| flash / rgb-128/identity | 8/16 | 5/1 | 0/0 | 0 |
| flash / rgb-128/neutral | 8/16 | 4/3 | 0/0 | 0 |
| flash / rgb-256/sufficiency | 10/16 | 0/3 | 0/0 | 0 |
| flash / rgb-256/alternatives | 10/16 | 3/6 | 0/0 | 0 |
| flash / rgb-256/identity | 10/16 | 0/1 | 2/0 | 0 |
| flash / rgb-256/neutral | 10/16 | 4/6 | 0/0 | 0 |
| flash / rgb-400/sufficiency | 10/16 | 0/3 | 0/0 | 0 |
| flash / rgb-400/alternatives | 10/16 | 4/4 | 0/0 | 0 |
| flash / rgb-400/identity | 10/16 | 0/1 | 2/0 | 0 |
| flash / rgb-400/neutral | 10/16 | 4/6 | 0/0 | 0 |
| flash / rgb-500/sufficiency | 9/16 | 0/3 | 0/0 | 0 |
| flash / rgb-500/alternatives | 9/16 | 3/5 | 0/0 | 0 |
| flash / rgb-500/identity | 9/16 | 0/2 | 1/0 | 0 |
| flash / rgb-500/neutral | 9/16 | 4/5 | 0/0 | 0 |
| flash / rgb-640/sufficiency | 10/16 | 2/4 | 0/0 | 0 |
| flash / rgb-640/alternatives | 10/16 | 4/6 | 0/0 | 0 |
| flash / rgb-640/identity | 10/16 | 1/4 | 1/0 | 0 |
| flash / rgb-640/neutral | 10/16 | 4/5 | 0/0 | 0 |
| clef / rgb-128/sufficiency | 9/16 | 1/4 | 1/0 | 0 |
| clef / rgb-128/alternatives | 9/16 | 0/1 | 2/0 | 0 |
| clef / rgb-128/identity | 9/16 | 2/4 | 1/0 | 0 |
| clef / rgb-128/neutral | 9/16 | 2/2 | 0/0 | 0 |
| clef / rgb-256/sufficiency | 9/16 | 3/3 | 1/0 | 0 |
| clef / rgb-256/alternatives | 9/16 | 0/2 | 0/0 | 0 |
| clef / rgb-256/identity | 9/16 | 3/3 | 2/0 | 0 |
| clef / rgb-256/neutral | 9/16 | 5/2 | 0/0 | 0 |
| clef / rgb-400/sufficiency | 10/16 | 3/2 | 1/0 | 0 |
| clef / rgb-400/alternatives | 10/16 | 1/1 | 0/0 | 0 |
| clef / rgb-400/identity | 10/16 | 2/4 | 2/0 | 0 |
| clef / rgb-400/neutral | 10/16 | 4/1 | 0/0 | 0 |
| clef / rgb-500/sufficiency | 9/16 | 3/2 | 1/0 | 0 |
| clef / rgb-500/alternatives | 9/16 | 0/0 | 1/0 | 0 |
| clef / rgb-500/identity | 9/16 | 3/4 | 1/0 | 0 |
| clef / rgb-500/neutral | 9/16 | 5/2 | 0/0 | 0 |
| clef / rgb-640/sufficiency | 10/16 | 3/2 | 1/0 | 0 |
| clef / rgb-640/alternatives | 10/16 | 1/0 | 0/0 | 0 |
| clef / rgb-640/identity | 10/16 | 2/4 | 1/0 | 0 |
| clef / rgb-640/neutral | 10/16 | 4/2 | 0/0 | 0 |
| pplx / rgb-128/sufficiency | 10/16 | 1/1 | 1/0 | 0 |
| pplx / rgb-128/alternatives | 10/16 | 2/3 | 0/0 | 0 |
| pplx / rgb-128/identity | 10/16 | 2/4 | 2/0 | 0 |
| pplx / rgb-128/neutral | 10/16 | 2/3 | 0/0 | 0 |
| pplx / rgb-256/sufficiency | 12/16 | 1/2 | 0/0 | 0 |
| pplx / rgb-256/alternatives | 12/16 | 2/3 | 0/0 | 0 |
| pplx / rgb-256/identity | 12/16 | 2/4 | 2/0 | 0 |
| pplx / rgb-256/neutral | 12/16 | 2/3 | 0/0 | 0 |
| pplx / rgb-400/sufficiency | 10/16 | 3/1 | 0/0 | 0 |
| pplx / rgb-400/alternatives | 10/16 | 2/4 | 0/0 | 0 |
| pplx / rgb-400/identity | 10/16 | 4/3 | 3/0 | 0 |
| pplx / rgb-400/neutral | 10/16 | 3/2 | 0/0 | 0 |
| pplx / rgb-500/sufficiency | 10/16 | 4/1 | 0/0 | 0 |
| pplx / rgb-500/alternatives | 10/16 | 2/4 | 0/0 | 0 |
| pplx / rgb-500/identity | 10/16 | 4/2 | 2/0 | 0 |
| pplx / rgb-500/neutral | 10/16 | 3/3 | 0/0 | 0 |
| pplx / rgb-640/sufficiency | 10/16 | 4/2 | 0/0 | 0 |
| pplx / rgb-640/alternatives | 10/16 | 2/4 | 0/0 | 0 |
| pplx / rgb-640/identity | 10/16 | 4/2 | 4/0 | 0 |
| pplx / rgb-640/neutral | 10/16 | 4/2 | 0/0 | 0 |
| intern / rgb-128/sufficiency | 11/16 | 3/2 | 0/0 | 0 |
| intern / rgb-128/alternatives | 11/16 | 1/5 | 0/0 | 0 |
| intern / rgb-128/identity | 11/16 | 3/2 | 0/0 | 0 |
| intern / rgb-128/neutral | 11/16 | 2/5 | 0/0 | 0 |
| intern / rgb-256/sufficiency | 12/16 | 2/2 | 0/0 | 0 |
| intern / rgb-256/alternatives | 12/16 | 2/6 | 0/0 | 0 |
| intern / rgb-256/identity | 12/16 | 2/3 | 0/0 | 0 |
| intern / rgb-256/neutral | 12/16 | 2/2 | 0/0 | 0 |
| intern / rgb-400/sufficiency | 12/16 | 2/2 | 0/0 | 0 |
| intern / rgb-400/alternatives | 12/16 | 2/6 | 0/0 | 0 |
| intern / rgb-400/identity | 12/16 | 2/4 | 0/0 | 0 |
| intern / rgb-400/neutral | 12/16 | 2/2 | 0/0 | 0 |
| intern / rgb-500/sufficiency | 12/16 | 2/2 | 0/0 | 0 |
| intern / rgb-500/alternatives | 12/16 | 2/6 | 0/0 | 0 |
| intern / rgb-500/identity | 12/16 | 2/5 | 0/0 | 0 |
| intern / rgb-500/neutral | 12/16 | 2/2 | 0/0 | 0 |
| intern / rgb-640/sufficiency | 12/16 | 2/2 | 0/0 | 0 |
| intern / rgb-640/alternatives | 12/16 | 2/6 | 0/0 | 0 |
| intern / rgb-640/identity | 12/16 | 2/4 | 0/0 | 0 |
| intern / rgb-640/neutral | 12/16 | 2/3 | 0/0 | 0 |

Qwen9, when explicitly admitted, is an exploratory extension beyond the four predeclared native models. Stock labels have no native probabilities or tie calibration. HTTP latency overlaps at concurrency8. Its sum is not batch elapsed. Client CPU/RSS and CUDA metrics cannot price the separate model server.

Missing, failed and malformed responses retain planned denominators. Resource measurements cover the serial native inference process; GPU device-wide utilization is separate. Absent matched fresh-original runs provide no isolated prompt-effect estimate. Full grouping metrics, failures, candidate oracle, tie abstentions and CUDA allocator peaks remain in the JSON report.
