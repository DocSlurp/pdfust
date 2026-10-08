# PDF decision probability pilot

- Small existing-PDF table/prose region study; no full-matrix or production-quality claim.
- Raw native, heuristic, or self-reported scores are not calibrated probabilities.
- Threshold selection uses calibration cases only and does not calibrate probabilities.
- Probability metrics exclude failed predictions and publish sample counts; operational metrics retain failures.
- Gold None denotes insufficient evidence; accepting either answer is counted as unsafe.
- Wilson intervals are descriptive and do not correct for grid selection or correlated synthetic variants.
- No per-case latency or cost aggregation: batches require unique request accounting in the inference runner.

Cases: calibration 0; test 8.

| Model / policy | Test N | Labeled N | Failures | Forced accuracy | Probability N | Brier | Log loss | ECE | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic/claude-opus-4.6@rich-b1 / fixed | 8 | 8 | 0 | 0.875 | 8 | 0.044 | 0.156 | 0.121 | 6 | 0 | 0 | 0.390 |
| anthropic/claude-opus-4.6@rich-b1 / selected | 8 | 8 | 0 | 0.875 | 8 | 0.044 | 0.156 | 0.121 | 0 | 0 | 0 | n/a |
| baseline / fixed | 8 | 8 | 0 | 0.750 | 8 | 0.190 | 0.570 | 0.035 | 0 | 0 | 0 | n/a |
| baseline / selected | 8 | 8 | 0 | 0.750 | 8 | 0.190 | 0.570 | 0.035 | 0 | 0 | 0 | n/a |
| google/gemini-2.5-flash-lite@rich-b1 / fixed | 8 | 8 | 0 | 0.875 | 8 | 0.125 | 4.317 | 0.125 | 8 | 1 | 0 | 0.471 |
| google/gemini-2.5-flash-lite@rich-b1 / selected | 8 | 8 | 0 | 0.875 | 8 | 0.125 | 4.317 | 0.125 | 0 | 0 | 0 | n/a |
| qwen/qwen3.5-9b@rich-b1 / fixed | 8 | 8 | 0 | 1.000 | 8 | 0.000 | 0.010 | 0.010 | 8 | 0 | 0 | 0.324 |
| qwen/qwen3.5-9b@rich-b1 / selected | 8 | 8 | 0 | 1.000 | 8 | 0.000 | 0.010 | 0.010 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@choice-b1 / fixed | 8 | 8 | 0 | 0.875 | 8 | 0.068 | 0.196 | 0.141 | 6 | 0 | 0 | 0.390 |
| typesafe/jev-1.13@choice-b1 / selected | 8 | 8 | 0 | 0.875 | 8 | 0.068 | 0.196 | 0.141 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@rich-b1 / fixed | 8 | 8 | 0 | 0.875 | 8 | 0.106 | 0.336 | 0.224 | 3 | 0 | 0 | 0.561 |
| typesafe/jev-1.13@rich-b1 / selected | 8 | 8 | 0 | 0.875 | 8 | 0.106 | 0.336 | 0.224 | 0 | 0 | 0 | n/a |

**anthropic/claude-opus-4.6@rich-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:table / fixed | 8 | 8 | 0 | 0.875 | 6 | 0 | 0 | 0.390 |
| task:table / selected | 8 | 8 | 0 | 0.875 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / fixed | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / selected | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:public-report / fixed | 6 | 6 | 0 | 1.000 | 6 | 0 | 0 | 0.390 |
| family:public-report / selected | 6 | 6 | 0 | 1.000 | 0 | 0 | 0 | n/a |


**baseline selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: heuristic_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:table / fixed | 8 | 8 | 0 | 0.750 | 0 | 0 | 0 | n/a |
| task:table / selected | 8 | 8 | 0 | 0.750 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / fixed | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / selected | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:public-report / fixed | 6 | 6 | 0 | 0.833 | 0 | 0 | 0 | n/a |
| family:public-report / selected | 6 | 6 | 0 | 0.833 | 0 | 0 | 0 | n/a |


**google/gemini-2.5-flash-lite@rich-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:table / fixed | 8 | 8 | 0 | 0.875 | 8 | 1 | 0 | 0.471 |
| task:table / selected | 8 | 8 | 0 | 0.875 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / fixed | 2 | 2 | 0 | 0.500 | 2 | 1 | 0 | 0.905 |
| family:existing-synthetic / selected | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:public-report / fixed | 6 | 6 | 0 | 1.000 | 6 | 0 | 0 | 0.390 |
| family:public-report / selected | 6 | 6 | 0 | 1.000 | 0 | 0 | 0 | n/a |


**qwen/qwen3.5-9b@rich-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:table / fixed | 8 | 8 | 0 | 1.000 | 8 | 0 | 0 | 0.324 |
| task:table / selected | 8 | 8 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / fixed | 2 | 2 | 0 | 1.000 | 2 | 0 | 0 | 0.658 |
| family:existing-synthetic / selected | 2 | 2 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| family:public-report / fixed | 6 | 6 | 0 | 1.000 | 6 | 0 | 0 | 0.390 |
| family:public-report / selected | 6 | 6 | 0 | 1.000 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@choice-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: conditional_choice_mass.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:table / fixed | 8 | 8 | 0 | 0.875 | 6 | 0 | 0 | 0.390 |
| task:table / selected | 8 | 8 | 0 | 0.875 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / fixed | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / selected | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:public-report / fixed | 6 | 6 | 0 | 1.000 | 6 | 0 | 0 | 0.390 |
| family:public-report / selected | 6 | 6 | 0 | 1.000 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@rich-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: native_decision_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:table / fixed | 8 | 8 | 0 | 0.875 | 3 | 0 | 0 | 0.561 |
| task:table / selected | 8 | 8 | 0 | 0.875 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / fixed | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:existing-synthetic / selected | 2 | 2 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:public-report / fixed | 6 | 6 | 0 | 1.000 | 3 | 0 | 0 | 0.561 |
| family:public-report / selected | 6 | 6 | 0 | 1.000 | 0 | 0 | 0 | n/a |

Fixed policy: confidence ≥ 0.9 and answerability ≥ 0.9. A probability of exactly 0.5 predicts yes.

Selection requires ≥ 8 accepted calibration cases and unsafe-rate Wilson upper ≤ 0.1.

Zero observed wrong decisions does not imply zero risk. Full threshold curves and reliability bins are retained in JSON.
## Frozen cohort and assembly analysis

- The baseline is an illustrative geometry/type heuristic, not native extractor quality.
- These 8 grounded regional table gates contain 4 positive and 4 negative labels.
- The regions come from 6 original sources; NICS and Senate each contribute two clips. Eight regions are not eight independent documents.
- Sources mix original public PDFs and existing repository synthetic controls used in earlier studies.
- These controls are test-only, with no calibration cases. The selected abstain-all policy is unsupported by calibration, not learned from the controls.
- Labels identify record tables versus prose in retained regions. They do not provide header, value-assignment, individual-cell, wrap, or complete-grid gold.
- Source-word conservation protects retained data; it does not establish correct logical relationships.
- Isolation comparisons describe batch sensitivity and do not identify its causal mechanism.

| Cohort / split | Status | Successful / total | Known correct / N | Known accuracy |
|---|---|---:|---:|---:|
| anthropic/claude-opus-4.6@rich-b1 / calibration | complete | 0/0 | 0/0 | n/a |
| anthropic/claude-opus-4.6@rich-b1 / test | complete | 8/8 | 7/8 | 0.875 |
| baseline / calibration | complete | 0/0 | 0/0 | n/a |
| baseline / test | complete | 8/8 | 6/8 | 0.750 |
| google/gemini-2.5-flash-lite@rich-b1 / calibration | complete | 0/0 | 0/0 | n/a |
| google/gemini-2.5-flash-lite@rich-b1 / test | complete | 8/8 | 7/8 | 0.875 |
| qwen/qwen3.5-9b@rich-b1 / calibration | complete | 0/0 | 0/0 | n/a |
| qwen/qwen3.5-9b@rich-b1 / test | complete | 8/8 | 8/8 | 1.000 |
| typesafe/jev-1.13@choice-b1 / calibration | complete | 0/0 | 0/0 | n/a |
| typesafe/jev-1.13@choice-b1 / test | complete | 8/8 | 7/8 | 0.875 |
| typesafe/jev-1.13@rich-b1 / calibration | complete | 0/0 | 0/0 | n/a |
| typesafe/jev-1.13@rich-b1 / test | complete | 8/8 | 7/8 | 0.875 |

### Retained-source application

| Cohort / split / policy | Affirmative requested | Applied | Correct | Wrong | Unknown | Constraint refusals | Source words before / after | Preserved cases / total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic/claude-opus-4.6@rich-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| anthropic/claude-opus-4.6@rich-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| anthropic/claude-opus-4.6@rich-b1 / test / fixed | 4 | 4 | 4 | 0 | 0 | 0 | 356/356 | 8/8 |
| anthropic/claude-opus-4.6@rich-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 356/356 | 8/8 |
| baseline / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| baseline / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| baseline / test / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 356/356 | 8/8 |
| baseline / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 356/356 | 8/8 |
| google/gemini-2.5-flash-lite@rich-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| google/gemini-2.5-flash-lite@rich-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| google/gemini-2.5-flash-lite@rich-b1 / test / fixed | 5 | 5 | 4 | 1 | 0 | 0 | 356/356 | 8/8 |
| google/gemini-2.5-flash-lite@rich-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 356/356 | 8/8 |
| qwen/qwen3.5-9b@rich-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| qwen/qwen3.5-9b@rich-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| qwen/qwen3.5-9b@rich-b1 / test / fixed | 4 | 4 | 4 | 0 | 0 | 0 | 356/356 | 8/8 |
| qwen/qwen3.5-9b@rich-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 356/356 | 8/8 |
| typesafe/jev-1.13@choice-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| typesafe/jev-1.13@choice-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| typesafe/jev-1.13@choice-b1 / test / fixed | 4 | 4 | 4 | 0 | 0 | 0 | 356/356 | 8/8 |
| typesafe/jev-1.13@choice-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 356/356 | 8/8 |
| typesafe/jev-1.13@rich-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| typesafe/jev-1.13@rich-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| typesafe/jev-1.13@rich-b1 / test / fixed | 3 | 3 | 3 | 0 | 0 | 0 | 356/356 | 8/8 |
| typesafe/jev-1.13@rich-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 356/356 | 8/8 |

### Known-label task slices

| Cohort / split / task | Status | Known correct / N | Known accuracy |
|---|---|---:|---:|
| anthropic/claude-opus-4.6@rich-b1 / test / table | complete | 7/8 | 0.875 |
| baseline / test / table | complete | 6/8 | 0.750 |
| google/gemini-2.5-flash-lite@rich-b1 / test / table | complete | 7/8 | 0.875 |
| qwen/qwen3.5-9b@rich-b1 / test / table | complete | 8/8 | 1.000 |
| typesafe/jev-1.13@choice-b1 / test / table | complete | 7/8 | 0.875 |
| typesafe/jev-1.13@rich-b1 / test / table | complete | 7/8 | 0.875 |

### Identical-observation singleton versus batch

| Model / split | Paired successes / N | Forced flips | Fixed outcome flips | Mean decision delta | Max decision delta | Max answerability delta |
|---|---:|---:|---:|---:|---:|---:|

No matching singleton and batch cohorts are recorded.

## Request accounting

This table accounts for the entire campaign, including separately tagged controls and diagnostics.
Latency is complete HTTP wall time. Batch time divided by items is serial amortization, not decision latency.
Unknown charges retain a $0.30 reservation. No automatic retries. Cached replays add no requests.

| Cohort | Requests | Items | Median HTTP ms | Total HTTP s | Accounted USD | Unsettled |
|---|---:|---:|---:|---:|---:|---:|
| anthropic/claude-opus-4.6@resolved/batch | 16 | 96 | 3308.1 | 53.545 | 0.431755 | 0 |
| anthropic/claude-opus-4.6@rich/batch | 16 | 96 | 3240.1 | 52.785 | 0.371770 | 0 |
| anthropic/claude-opus-4.6@rich/smoke | 1 | 1 | 3039.1 | 3.039 | 0.006190 | 0 |
| controls/anthropic/claude-opus-4.6@rich-b1/batch | 8 | 8 | 1668.9 | 13.494 | 0.089315 | 0 |
| controls/google/gemini-2.5-flash-lite@rich-b1/batch | 8 | 8 | 896.7 | 7.390 | 0.001976 | 0 |
| controls/qwen/qwen3.5-9b@rich-b1/batch | 8 | 8 | 1128.7 | 8.813 | 0.001904 | 0 |
| controls/typesafe/jev-1.13@choice-b1/batch | 8 | 8 | 262.0 | 2.139 | 0.001187 | 0 |
| controls/typesafe/jev-1.13@rich-b1/batch | 8 | 8 | 255.5 | 2.163 | 0.001165 | 0 |
| google/gemini-2.5-flash-lite@resolved/batch | 16 | 96 | 1502.5 | 23.349 | 0.008555 | 0 |
| google/gemini-2.5-flash-lite@rich/batch | 16 | 96 | 1500.2 | 22.535 | 0.007372 | 0 |
| google/gemini-2.5-flash-lite@rich/smoke | 1 | 1 | 588.2 | 0.588 | 0.000107 | 0 |
| google/gemini-3.1-flash-lite@rich/smoke | 1 | 1 | 1107.6 | 1.108 | 0.000000 | 0 |
| qwen/qwen3.5-9b@resolved-b1/batch | 96 | 96 | 969.6 | 97.566 | 0.008902 | 0 |
| qwen/qwen3.5-9b@rich/batch | 16 | 96 | 2602.0 | 42.891 | 0.006205 | 0 |
| qwen/qwen3.5-9b@rich/smoke | 1 | 1 | 957.4 | 0.957 | 0.000097 | 0 |
| typesafe/jev-1.13@choice-b1/batch | 96 | 96 | 239.9 | 23.910 | 0.005537 | 0 |
| typesafe/jev-1.13@resolved-b1/batch | 96 | 96 | 247.1 | 24.125 | 0.006550 | 0 |
| typesafe/jev-1.13@resolved-text-b1/batch | 88 | 88 | 240.6 | 22.215 | 0.003894 | 0 |
| typesafe/jev-1.13@resolved/batch | 16 | 96 | 275.9 | 4.578 | 0.005656 | 0 |
| typesafe/jev-1.13@rich-b1/batch | 95 | 95 | 249.1 | 24.220 | 0.005753 | 0 |
| typesafe/jev-1.13@rich/batch | 16 | 96 | 280.4 | 4.679 | 0.004930 | 0 |
| typesafe/jev-1.13@rich/smoke | 1 | 1 | 242.2 | 0.242 | 0.000071 | 0 |
