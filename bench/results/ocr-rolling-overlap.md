# A004 OCR overlap ablation

Three allowances (0.0, 0.25, 0.5 median OCR item heights) were frozen before this paired scorer ran. All use the same 56 immutable OCR observations; no new OCR, inference, geometry shrinking, string splitting, or case-specific rule changes occur. Original A003/default behavior remains unchanged; the optional keyword defaults to zero and validates finite values in [0, 0.5].

| Edge | Allowance | Borderless exact /12 | Wrapped exact /6 | Prose FP /12 | Pure merged exact /4 | Pure complete /28 | Hybrid complete /28 | OCR IDs conserved /28 |
|---|---|---|---|---|---|---|---|---|
| 640 | 0.0 | 4/12 | 0/6 | 12/12 | 0/4 | 4/28 | 8/28 | 28/28 |
| 640 | 0.25 | 4/12 | 0/6 | 12/12 | 0/4 | 4/28 | 8/28 | 28/28 |
| 640 | 0.5 | 6/12 | 2/6 | 12/12 | 0/4 | 6/28 | 10/28 | 28/28 |
| 1200 | 0.0 | 6/12 | 0/6 | 12/12 | 0/4 | 6/28 | 10/28 | 28/28 |
| 1200 | 0.25 | 10/12 | 4/6 | 12/12 | 0/4 | 10/28 | 14/28 | 28/28 |
| 1200 | 0.5 | 12/12 | 6/6 | 12/12 | 0/4 | 12/28 | 16/28 | 28/28 |

All 56 zero-allowance outputs exactly match the original frozen candidates. Missing/refused counts are 0/28 per scale; all denominators include 12 borderless, 12 prose, and 4 merged pages. The lower gap boundary alone becomes -height×allowance; numeric-bearing and complete bands still cannot join, and the existing upper-gap, anchor-support, column and source-conservation conditions remain active. Native vectors/text are used solely for the separately labeled hybrid.

CPU assembly-only pass: 0.085s wall / 0.085s CPU; 28.9 MiB process-lifetime getrusage SELF RSS, single sequential process, no sampling/children/GPU. No provider spending or additional OCR resource usage. These are authored correlated DEV results, not independent confirmation or production acceptance.

Reproduce `.venv/bin/python -m bench.ocr_rolling --overlap` after the frozen baseline exists. Config, source hashes, candidate matrices/IDs, full scores and resources remain ignored in `ocr-rolling-v1/66c3cde77b110038/overlap-a004-v1/`. The default candidate artifact is preserved.

At 1200 pixels, the 0.5-height allowance recovers all six wrapped tables and reaches 12/12 borderless matrices. It remains an opt-in DEV hypothesis: all twelve prose negatives still receive false table proposals, and pure OCR has no merged-span inference. The separately labeled native hybrid restores merged controls but does not resolve prose admission.
