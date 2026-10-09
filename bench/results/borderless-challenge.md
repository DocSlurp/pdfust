# Borderless companion DEV challenge

Separate 28-page authored DEV corpus: 12 borderless positives, 12 numeric multicolumn-prose negatives, four ruled merged-header controls. Original 125-page cohort remains immutable. Authored references are frozen independently of extraction; not independently adjudicated gold.

| Route | Borderless exact cells / 12 | Borderless exact spans / 12 | Prose FP / 12 | Controls exact / 4 | Errors / 28 |
|---|---:|---:|---:|---:|---:|
| none | 0/12 | 0/12 | 0/12 | 0/4 | 0/28 |
| vector | 0/12 | 0/12 | 0/12 | 4/4 | 0/28 |
| raw-text | 2/12 | 2/12 | 8/12 | 0/4 | 0/28 |
| vector-veto | 2/12 | 2/12 | 0/12 | 4/4 | 0/28 |
| vector-paint | 0/12 | 0/12 | 0/12 | 4/4 | 0/28 |
| candidate-ceiling | 2/12 | 2/12 | 8/12 | 4/4 | 0/28 |

Paired borderless exact-cell outcomes (no-wrap / wrap), same authored values:

| Font | Numeric alignment | Native candidate ceiling | Veto route |
|---|---|---|---|
| 9 | left | 0 / 0 | 0 / 0 |
| 11 | left | 0 / 0 | 0 / 0 |
| 13 | left | 1 / 0 | 1 / 0 |
| 9 | right | 0 / 0 | 0 / 0 |
| 11 | right | 0 / 0 | 0 / 0 |
| 13 | right | 1 / 0 | 1 / 0 |

Ownership totals (complete unique cell values / intended-slot word multiplicity):

- `none`: borderless 0/144 values, 0/180 words; controls 0/56 values, 0/132 words.
- `vector`: borderless 0/144 values, 0/180 words; controls 56/56 values, 132/132 words.
- `raw-text`: borderless 24/144 values, 30/180 words; controls 0/56 values, 0/132 words.
- `vector-veto`: borderless 24/144 values, 30/180 words; controls 56/56 values, 132/132 words.
- `vector-paint`: borderless 0/144 values, 0/180 words; controls 56/56 values, 132/132 words.
- `candidate-ceiling`: borderless 24/144 values, 30/180 words; controls 56/56 values, 132/132 words.

The same veto preserves the two complete borderless candidates while removing eight prose false positives, but ten positive matrices remain missing from the native candidate set. All six wrapped labels fail, including paired pages whose unwrapped 13-point versions succeed. Paint gating loses both successes. The next hypothesis is source-ID-conserving row assembly with continuation-line joins before any model ranking; candidate selection alone cannot exceed the measured two-table ceiling. Visual inspection of a wrapped positive, a prose negative and a merged-grid control confirmed the authored construction. No extraction default changed.

Candidate ceiling asks whether any individual native vector/text candidate has the complete authored matrix; it supplies no gold to routing and does not assemble new candidates. Cell exactness compares all row-major slots after whitespace normalization, while topology compares spans. Borderless edges have no author-drawn boundary, so invented cell rectangles are not scored as exact geometry. Unique complete-cell ownership and word multiplicity remain in per-page private scores. Wrap and no-wrap members share values, font size and numeric alignment; only the first-column label breaks across lines. Six settings use 9/11/13 point type and left/right numeric alignment. Negatives retain independent prose columns and similar terms and numeric density, but are not pixel-identical lexical controls.

Frozen routing rules are unchanged from round 1; no thresholds were adapted after companion scores. Model-facing evidence contains words, geometry, native candidates and rendered images without table/prose labels, intended cells, pairing settings or gold relationships. Case IDs are opaque and must never be routing features. Private references and scores remain separate files.

Resources: {'wall_seconds': 0.8267929420107976, 'cpu_seconds': 0.7260488679999999, 'peak_rss_bytes': 105586688, 'tool': 'perf_counter/process_time; /proc/self/status VmHWM (current executable)', 'workers': 1, 'scope': 'current-exec native extraction, render, routing/scoring; RSS whole runner', 'sampling': 'OS cumulative counters/high water; no periodic sampling', 'logical_cpus': 8, 'platform': 'Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44'}. No hosted requests or GPU inference. Dataset `66c3cde77b11003827f594dbd5827a1a0e531e61195a9aced0efb7d334a49290`, runner `febf6d4f95491e191db5572c245433060dc7b90105ff69198012c1dd2e50f3fe`, rules `cacb457eeca5d6605e5470b7013fcfd849af1133eccba222877422e4a6bb8df3`. Complete private artifacts: `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/borderless-dev-v1/66c3cde77b110038/run-or_2i6th`.
