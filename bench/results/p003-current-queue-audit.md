# P003 current queue: decision-confirmed evidence

This final drained-queue checkpoint covers all 60 independently verified completed arms from the explicit `parallel-mechanisms-generalization-v3/status.json` inventory. Detailed quality, exact-page counts, resources, cost bases, provider cache coverage and hashes are in [the progress tables](p003-current-queue-progress.md). Infrastructure-stopped full276 arms remain incomplete; they are not model-quality failures.

Primary candidate quality credits only committed model-selected complete crop states. Abstained, failed and deterministic duplicate-only crops predict no tables. All 16 pages, 53 tables and 2,333 anchor cells remain in the denominator. Legacy retained pipeline outputs remain separate provenance.

| Candidate treatment | Selected-only strict / complete | Missing / extra | Negative FP /4 | Legacy strict / complete |
| --- | ---: | --- | ---: | ---: |
| `choice-pplx-128-rgb-r2-c6` | 984 / 5 | 27 / 0 | 0 | 1087 / 5 |
| `choice-pplx-128-rgb-blank-r0-c6` | 11 / 0 | 51 / 0 | 0 | 784 / 3 |
| `choice-pplx-512-rgb_palette16-blank-r0-c6` | 2 / 0 | 52 / 0 | 0 | 784 / 3 |
| `choice-pplx-512-rgb_palette16-r2-c6` | 981 / 5 | 26 / 0 | 0 | 981 / 5 |
| `choice-pplx-128-rgb_palette16-seed7-r0-c6` | 979 / 3 | 28 / 0 | 0 | 1086 / 4 |
| `choice-pplx-1024-rgb-r2-c6` | 294 / 4 | 38 / 0 | 0 | 685 / 4 |
| `choice-pplx-400-rgb-seed19-r0-c6` | 1081 / 5 | 26 / 3 | 0 | 1081 / 5 |
| `choice-pplx-1024-rgb_palette16-r2-c6` | 294 / 4 | 38 / 0 | 0 | 685 / 4 |

The 128 RGB repeat scores 984 strict cells and five complete tables, versus 11 cells and zero tables with blank pixels. The 400 RGB/seed19 arm scores 1,081/five but introduces three extra tables. Both edge and permutation seed differ, so this is an observed result, not a causal resize comparison. Confirmation configurations remain frozen; these DEV results do not retune fresh48. Larger 1024 arms score 294/four on selected-only quality; abstention retention does not receive primary credit.

These incremental selectors reuse frozen Luna/P002 Sonnet generation candidates. Historical generation cost is separate from fresh selector cost. Retained-page processing rates include no-question and abstained pages; they are not decision-complete-page or fresh full-pipeline rates. Requested decision models remain separate; consistent request inventories do not contain an explicit alternative-model fallback or inline retry.

The following ownership metric credits only completed incremental whole-page composition. Failed, skipped and no-question baseline pages predict no tables, retaining the full 16/53/2,333 denominator. It includes deterministic geometry and protected source portions; it is not model-only cell attribution.

| Ownership treatment | Successful composition strict / complete | Missing / extra | Failed pages | Legacy strict / complete |
| --- | ---: | --- | ---: | ---: |
| `ownership-hybrid-pplx-neighbors-r0-c6` | 268 / 3 | 39 / 1 | 1 | 370 / 3 |
| `ownership-allwords-pplx-compact-r0-c6` | 200 / 1 | 39 / 0 | 1 | 302 / 1 |
| `ownership-allwords-jev-neighbors-r0-c6` | 49 / 1 | 33 / 5 | 2 | 126 / 1 |
| `ownership-direct-jev-neighbors-r0-c6` | 245 / 3 | 41 / 1 | 2 | 358 / 3 |
| `ownership-allwords-pplx-neighbors-r0-c6` | 208 / 2 | 39 / 0 | 1 | 310 / 2 |
| `ownership-allwords-jev-compact-r0-c6` | 38 / 1 | 43 / 1 | 4 | 242 / 2 |
| `ownership-direct-tev-neighbors-r0-c6` | 249 / 3 | 39 / 1 | 1 | 351 / 3 |
| `ownership-direct-pplx-neighbors-r0-c6` | 252 / 3 | 39 / 1 | 1 | 354 / 3 |
| `ownership-direct-d1-bands-r0-c6` | 249 / 3 | 39 / 1 | 1 | 351 / 3 |
| `ownership-direct-jev-bands-r0-c6` | 250 / 3 | 39 / 1 | 1 | 352 / 3 |

Ownership failure reasons include rejected native probability/mass receipts and overlapping source-owned composed tables. They remain explicit failed compositions. Returned word-question counts can include the same word in both stages; recorded geometry locks are admission declarations, not model decisions or proof of committed model cell contribution.

The verified Clef gate composes 384/three versus ClefOmni 280/one. Both new PPLX gates (400 palette and 1024 grayscale) compose 384/three, equal to the frozen ordinal control. These gate experiments condition on frozen generation and have incremental costs only.

Luna legacy generation repeat scores 278/three with one failed page; matrix-strict scores 290/three with one failed page. The original Luna generation was 784/three. This material repeat variation prevents attributing an unmatched downstream change entirely to its decision treatment. Failures remain in the 16-page denominator.

Sonnet on the existing natural64 DEV cohort independently scores 1,839 strict, 1,851 text and 2,505 structure cells out of 3,847, with 14/93 complete tables, 34 missing and four extra tables, one negative false-positive page out of 24, and zero failures across all 64 pages. Cost is USD 0.455752 for 56 provider-reported attempts. Contended elapsed time is 1,201.285 seconds (3.197 operational pages/minute; 140.43 operational pages/APIUSD), parent CPU 101.401 seconds and sampled parent RSS 618.16 MiB. Worker measurements remain separate in the progress tables. This cohort is existing DEV, not fresh confirmation.

Single-run treatment results and unmatched repeat differences are not calibrated confidence intervals. All rates are labeled by processing scope; no fallback baseline is credited as a successful model decision.

The next independently verified checkpoint adds the following results; all retain the same full natural16 denominator:

| Treatment | Primary scope | Strict / complete | Missing / extra | Errors | Legacy strict / complete | Incremental API USD / basis |
| --- | --- | ---: | --- | ---: | ---: | --- |
| PPLX500 palette | Model-selected crops | 980 / 5 | 27 / 0 | 0 | 1083 / 5 | 0.00061344 / reported |
| Direct Luna bands | Successful composition, geometry included | 242 / 3 | 39 / 1 | 1 | 344 / 3 | 0.2293663 / catalog estimate; reported zero preserved |
| Direct d1 neighbors | Successful composition, geometry included | 249 / 3 | 39 / 1 | 1 | 351 / 3 | 0.7554552 / reported |
| Haiku atomic-cell transcription | Complete pipeline output | 358 / 2 | 40 / 0 | 2 | 358 / 2 | 0.0186637 / reported |

Neither the 500-pixel result nor differences among unmatched representations establish a causal optimum. Detailed statuses, evidence, resources and operational rates are retained in the updated progress tables.

The following checkpoint preserves the complete natural64 denominator (64 pages, 93 tables, 3,847 cells and 24 negatives):

| Generation arm | Strict | Complete | Missing / extra | Negative FP | Errors | API USD / basis |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| Ordinal OCR edge2048 | 1125 | 10 | 46 / 11 | 1 / 24 | 1 | 0.0599038 / reported |
| Haiku matrix-strict | 1333 | 12 | 50 / 0 | 0 / 24 | 6 | 0.0260132 / reported |
| Sonnet legacy, earlier checkpoint | 1839 | 14 | 34 / 4 | 1 / 24 | 0 | 0.455752 / reported |

These runs differ in generation/model/representation and share contended transport, so the table records observed complete-denominator results rather than a causal representation comparison. Successful-page-only scoring would hide Haiku's six failures.

Additional natural16 candidate controls use primary selected-only quality:

| Candidate arm | Primary strict / complete | Missing / extra | Legacy strict / complete | API USD / reported |
| --- | ---: | --- | ---: | ---: |
| PPLX400 RGB seed7 | 980 / 5 | 27 / 0 | 1083 / 5 | 0.00060236 |
| PPLX128 palette seed19 | 1078 / 3 | 27 / 3 | 1082 / 4 | 0.00059822 |
| PPLX128 palette blank | 11 / 0 | 51 / 0 | 784 / 3 | 0.00059822 |
| PPLX128 palette blur | 98 / 0 | 46 / 0 | 784 / 3 | 0.00059822 |

At fixed 400 RGB, seed19 previously scored 1,081/five with three extras, whereas seed7 scores 980/five with none. At fixed 128 palette, seed7 previously scored 979/three with no extras versus seed19's 1,078/three with three extras. This permutation sensitivity does not identify an optimal seed or image size. No control is changed based on fresh-confirmation outcomes.

ClefOmni direct bands score 209/two after failure filtering (legacy311/two), with one failed composition. Luna gate composes372/two and PPLX128 palette gate384/three on frozen generation. Their costs and resource scopes are in the progress tables; baseline retention remains excluded from successful ownership quality.

The next checkpoint adds these independently verified selected-only controls,
again using all 16 pages, 53 tables and 2,333 reference cells:

| Candidate arm | Primary strict / complete | Missing / extra | Legacy strict / complete | Incremental API USD / reported |
| --- | ---: | --- | ---: | ---: |
| PPLX400 RGB seed43 | 1083 / 5 | 26 / 3 | 1083 / 5 | 0.00060236 |
| PPLX128 palette seed43 | 1078 / 3 | 27 / 3 | 1082 / 4 | 0.00059822 |
| PPLX512 palette blur | 44 / 0 | 48 / 0 | 784 / 3 | 0.00061408 |
| PPLX128 palette repeat2 | 979 / 3 | 28 / 0 | 1086 / 4 | 0.00059822 |
| PPLX128 RGB blur | 98 / 0 | 46 / 0 | 784 / 3 | 0.00059822 |
| PPLX512 RGB repeat2 | 981 / 5 | 26 / 0 | 981 / 5 | 0.00061408 |

The blur controls remain weak on confirmed selections despite their retained
legacy baseline scores. The higher 400 RGB and 128 palette seed43 cell counts
also retain three extra tables; the permutation tradeoff persists. None of
these observations selects a fresh-confirmation treatment.

| Ownership arm | Successful composition strict / complete, geometry included | Missing / extra | Failed pages | Legacy strict / complete | Incremental API USD |
| --- | ---: | --- | ---: | ---: | ---: |
| Hybrid Jev neighbors | 359 / 3 | 32 / 3 | 1 | 370 / 3 | 0.112295736 |
| Direct PPLX bands | 251 / 3 | 39 / 1 | 1 | 353 / 3 | 0.87598702 |
| Direct Luna neighbors | 245 / 3 | 39 / 1 | 1 | 347 / 3 | 0.1915652 |

These composition counts include deterministic geometry and protected source
portions. The failed pages contribute no predicted tables to primary quality;
the legacy columns preserve original fallback outputs separately. All costs
cover incremental attempts only. Luna's reported zero is preserved and its
effective cost uses labeled catalog estimates; the other two costs are reported.

The following completed controls are also independently verified with full
natural16 denominators. Candidate values remain selected-only; ownership values
are successful composition including geometry, with each failed page excluded
from table credit.

| Arm | Primary strict / complete | Missing / extra | Operational failures | Legacy strict / complete | Incremental API USD |
| --- | ---: | --- | ---: | ---: | ---: |
| Direct Tev bands | 249 / 3 | 39 / 1 | 1 | 351 / 3 | 1.809086664 |
| Direct PPLX neighbors text | 249 / 3 | 39 / 1 | 1 | 351 / 3 | 0.6206455 |
| Hybrid Luna neighbors | 198 / 2 | 39 / 1 | 1 | 300 / 2 | 0.230661 |
| PPLX400 palette repeat2 | 978 / 5 | 27 / 0 | 0 | 1081 / 5 | 0.00060236 |
| PPLX400 RGB repeat2 | 978 / 5 | 27 / 0 | 0 | 1081 / 5 | 0.00060236 |
| PPLX500 RGB | 1083 / 5 | 26 / 3 | 0 | 1083 / 5 | 0.00061344 |
| PPLX512 RGB blank | 2 / 0 | 52 / 0 | 0 | 784 / 3 | 0.00061408 |

Luna's cost is a catalog estimate over 155 attempts with reported zero preserved;
the other costs are provider reported. These are incremental decisions over
retained evidence. Matching observed scores across some arms do not establish
equivalent mechanisms, and the 500 RGB result retains three extra tables. The
blank 512 RGB control receives only two strict cells on actual selected crops,
despite its original baseline-retaining score of 784 cells.

Opus legacy transcription on the existing natural64 DEV cohort independently
scores 1,617 strict, 1,627 text and 2,215 structure cells, with 15 complete tables,
36 missing and three extra tables. All 64 pages, 93 tables and 3,847 cells remain
in the denominator, including two failed pages; none of the 24 negative pages
has a false-positive table. Provider-reported cost is USD 0.85678 over 55 attempts.
The observed operational rate is 6.404 pages/minute and 72.36 pages/APIUSD under
contended transport. Resource details remain in the progress tables.

Sonnet's earlier same-cohort observation was 1,839 strict cells, 14 complete
tables and zero failures. Opus's higher complete-table count therefore coexists
with fewer strict cells and two failures. These single observations do not
establish a causal model difference or a treatment choice for fresh confirmation.

Additional full-natural16 observations retain 16/53/2,333:

| Arm | Primary scope | Strict / complete | Missing / extra | Failures | Incremental API USD |
| --- | --- | ---: | --- | ---: | ---: |
| Luna legacy repeat2 | Complete pipeline | 291 / 4 | 39 / 0 | 1 | 0.010607825 |
| Luna atomic cells | Complete pipeline | 515 / 4 | 35 / 6 | 0 | 0.0188228 |
| Direct ClefOmni neighbors | Successful composition, geometry included | 201 / 2 | 39 / 1 | 1 | 0.4281609 |
| PPLX512 RGB blur | Model-selected crops | 51 / 0 | 47 / 0 | 0 | 0.00061408 |

The two Luna values cover generation API attempts rather than incremental
decisions. Their positive upstream-plus-gateway BYOK basis preserves the reported
gateway zero. ClefOmni and PPLX costs cover reported incremental decisions only.
Luna's atomic-cell arm produces six extra positive-page tables, and unmatched
repeat variation prevents treating its difference as isolated representation
causality. Blur's baseline-retaining legacy score remains 784/three; primary
model-selected quality gives it only 51 strict cells and no complete table.

The final ordinal OCR edge3,072 arm retains all 64 natural pages, 93 tables and
3,847 cells: 1,204 strict, 1,223 text and 1,484 structure cells, 12 complete
tables, 46 missing and 15 extra tables, zero false-positive negative pages out
of 24, and two failures. Reported API cost is USD 0.0614165 over 55 attempts.
Contended elapsed time is 1,447.868 seconds, parent CPU 2,201.746 seconds and
sampled parent RSS 728.648 MiB; observed operational throughput is 2.569
pages/minute and 1,009.5 pages/APIUSD. Worker resources remain separate.
The earlier edge2,048 observation was 1,125/ten with eleven extras and one
failure; these single observations do not establish an OCR resolution optimum.

All 62 declared arms are drained: 60 completed and independently verified, plus
two infrastructure-stopped full276 runs. Their partial outputs and wall-limit
failures remain separate; no missing pages are silently credited or retried in
this report. Any authenticated continuation will be reported separately with
its original segment provenance.
