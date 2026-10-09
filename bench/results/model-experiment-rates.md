# Model-grouped experiment rates and scores

Computed from retained provider responses and request ledger; no new inference. All quality results are DEV, not clean held-out validation.

**Units:** pages/$ = admitted page inputs / provider-reported USD; pages/min =60,000×admitted page inputs / sum of original HTTP milliseconds. Deduplicate request indexes, exclude replay time/charges, count each six-observation batch as six inputs. Decision/assembly/gate inputs are partial-page observations, not full-page extraction. Embedding whole-page rows are actual page images; oracle-ROI rows are one authored crop per page. These are sequential API-only rates, excluding CPU render/extraction, telemetry, scheduling and concurrency.

`$0 reported` means the provider returned zero and division is undefined; it is not a claim of free future inference. Unknown-charge reservations are not spend. Embedding indexing rates exclude shared query embedding: the8-query batch is charged once per model and reused for its three image conditions. No full-pipeline pages/min or hardware-adjusted CPU pages/$ was measured.

**Scores:** relationship quality uses36known observations from historical test partition; operational rates cover the full96-observation cohort. Gates use8regions. Assembly exactness uses30or9regions; “evidence” is correctness given admitted information, and P/R/F1 are mean record precision/recall/F1. All assemblies conserve100%of admitted source IDs. Retrieval uses6matched and2absent queries over24pages. Absent-query false hits assume forced nearest-neighbor ranking; no rejection threshold is calibrated.

## All model experiments

| Model | Experiment | Pages/$ | Pages/min | Scores |
|---|---|---:|---:|---|
| anthropic/claude-opus-4.6 | Region gate rich-b1 | 90 | 35.6 | 7/8 (87.5%) |
| anthropic/claude-opus-4.6 | Relationships resolved | 222 | 107.6 | 29/36 (80.6%) |
| anthropic/claude-opus-4.6 | Relationships rich | 258 | 109.1 | 27/36 (75.0%) |
| cloudflare/clef-flash | Region gate resolved-via-primeintellect-b1 | — | — | HTTP 404: 1 failed, 7 unattempted; no quality score |
| cloudflare/clef-flash | Relationships resolved-b1 | 9,146 | 152.6 | 24/36 (66.7%) |
| google/gemini-2.5-flash-lite | Region gate rich-b1 | 4,049 | 64.9 | 7/8 (87.5%) |
| google/gemini-2.5-flash-lite | Relationships resolved | 11,221 | 246.7 | 22/36 (61.1%) |
| google/gemini-2.5-flash-lite | Relationships rich | 13,022 | 255.6 | 25/36 (69.4%) |
| google/gemini-3.1-flash-lite | Smoke only | $0 reported | — | No completed scored cohort |
| google/gemini-embedding-2 | Image embedding oracle-roi512 | 7,830 | 65.6 | Hit@1 0.833; Hit@3 1.000; Recall@1 0.417; Recall@3 0.917; MRR 0.889; pairs 19/24; ties 0; absent false hits 2/2 |
| google/gemini-embedding-2 | Image embedding page128 | 7,830 | 64.0 | Hit@1 0.833; Hit@3 1.000; Recall@1 0.417; Recall@3 1.000; MRR 0.917; pairs 20/24; ties 0; absent false hits 2/2 |
| google/gemini-embedding-2 | Image embedding page512 | 7,830 | 64.3 | Hit@1 0.833; Hit@3 1.000; Recall@1 0.417; Recall@3 1.000; MRR 0.917; pairs 22/24; ties 0; absent false hits 2/2 |
| inception/mercury-decide | Region gate resolved-b1 | 16,110 | 94.3 | 7/8 (87.5%) |
| inception/mercury-decide | Relationships resolved-b1 | 46,274 | 119.2 | 21/36 (58.3%) |
| liquid/d1 | Region gate resolved-b1 | 3,777 | 138.4 | 6/8 (75.0%) |
| liquid/d1 | Relationships resolved-b1 | 10,100 | 161.3 | 20/36 (55.6%) |
| openai/gpt-6-luna-decisions | Assembly blank128 [9-case subset] | $0 reported | 166.7 | Exact 5/9; evidence 2/9; P/R/F1 0.556/0.556/0.556 |
| openai/gpt-6-luna-decisions | Assembly blur128 [9-case subset] | $0 reported | 153.7 | Exact 3/9; evidence 3/9; P/R/F1 0.333/0.333/0.333 |
| openai/gpt-6-luna-decisions | Assembly compact-current | $0 reported | 215.0 | Exact 3/30; evidence 30/30; P/R/F1 0.100/0.100/0.100 |
| openai/gpt-6-luna-decisions | Assembly compact-image128 | $0 reported | 213.9 | Exact 3/30; evidence 9/30; P/R/F1 0.100/0.100/0.100 |
| openai/gpt-6-luna-decisions | Assembly compact-image512 | $0 reported | 200.7 | Exact 3/30; evidence 9/30; P/R/F1 0.100/0.100/0.100 |
| openai/gpt-6-luna-decisions | Assembly compact-native | $0 reported | 189.9 | Exact 10/30; evidence 10/30; P/R/F1 0.333/0.333/0.333 |
| openai/gpt-6-luna-decisions | Assembly context [9-case subset] | $0 reported | 214.8 | Exact 4/9; evidence 2/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Assembly current | $0 reported | 188.5 | Exact 12/30; evidence 0/30; P/R/F1 0.400/0.400/0.400 |
| openai/gpt-6-luna-decisions | Assembly derived-native | $0 reported | 213.6 | Exact 7/30; evidence 7/30; P/R/F1 0.233/0.233/0.233 |
| openai/gpt-6-luna-decisions | Assembly fact-native | $0 reported | 196.7 | Exact 14/30; evidence 14/30; P/R/F1 0.467/0.467/0.467 |
| openai/gpt-6-luna-decisions | Assembly image128 | $0 reported | 199.8 | Exact 12/30; evidence 9/30; P/R/F1 0.400/0.400/0.400 |
| openai/gpt-6-luna-decisions | Assembly image256 [9-case subset] | $0 reported | 200.8 | Exact 4/9; evidence 2/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Assembly image512 [9-case subset] | $0 reported | 169.5 | Exact 4/9; evidence 2/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Assembly image64 [9-case subset] | $0 reported | 217.3 | Exact 4/9; evidence 2/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Assembly native | $0 reported | 204.7 | Exact 12/30; evidence 12/30; P/R/F1 0.400/0.400/0.400 |
| openai/gpt-6-luna-decisions | Assembly native-reverse [9-case subset] | $0 reported | 214.5 | Exact 4/9; evidence 4/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Assembly prior [9-case subset] | $0 reported | 214.8 | Exact 4/9; evidence 2/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Assembly prior-both [9-case subset] | $0 reported | 221.6 | Exact 4/9; evidence 2/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Assembly prior-summary [9-case subset] | $0 reported | 161.1 | Exact 4/9; evidence 2/9; P/R/F1 0.444/0.444/0.444 |
| openai/gpt-6-luna-decisions | Region gate resolved-b1 | $0 reported | 159.1 | 8/8 (100.0%) |
| openai/gpt-6-luna-decisions | Relationships resolved-b1 | $0 reported | 200.2 | 31/36 (86.1%) |
| perplexity/pplx-decider-v1.1-27b | Assembly blank128 [9-case subset] | 29,917 | 184.6 | Exact 6/9; evidence 0/9; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly blur128 [9-case subset] | 29,990 | 181.3 | Exact 6/9; evidence 3/9; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly compact-current | 76,908 | 180.8 | Exact 3/30; evidence 30/30; P/R/F1 0.100/0.100/0.100 |
| perplexity/pplx-decider-v1.1-27b | Assembly compact-image128 | 64,389 | 148.6 | Exact 16/30; evidence 19/30; P/R/F1 0.533/0.533/0.533 |
| perplexity/pplx-decider-v1.1-27b | Assembly compact-image512 | 64,389 | 163.6 | Exact 15/30; evidence 18/30; P/R/F1 0.500/0.500/0.500 |
| perplexity/pplx-decider-v1.1-27b | Assembly compact-native | 51,874 | 138.6 | Exact 23/30; evidence 23/30; P/R/F1 0.767/0.767/0.767 |
| perplexity/pplx-decider-v1.1-27b | Assembly context [9-case subset] | 25,922 | 177.5 | Exact 6/9; evidence 3/9; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly current | 32,108 | 187.4 | Exact 13/30; evidence 0/30; P/R/F1 0.433/0.433/0.433 |
| perplexity/pplx-decider-v1.1-27b | Assembly derived-native | 48,353 | 198.4 | Exact 26/30; evidence 26/30; P/R/F1 0.867/0.867/0.867 |
| perplexity/pplx-decider-v1.1-27b | Assembly fact-native | 175,768 | 202.5 | Exact 20/30; evidence 20/30; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly image128 | 30,183 | 183.9 | Exact 15/30; evidence 12/30; P/R/F1 0.500/0.500/0.500 |
| perplexity/pplx-decider-v1.1-27b | Assembly image256 [9-case subset] | 29,990 | 183.5 | Exact 4/9; evidence 3/9; P/R/F1 0.444/0.444/0.444 |
| perplexity/pplx-decider-v1.1-27b | Assembly image512 [9-case subset] | 29,990 | 181.3 | Exact 4/9; evidence 3/9; P/R/F1 0.444/0.444/0.444 |
| perplexity/pplx-decider-v1.1-27b | Assembly image64 [9-case subset] | 30,026 | 174.8 | Exact 6/9; evidence 3/9; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly native | 22,463 | 170.2 | Exact 20/30; evidence 20/30; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly native-reverse [9-case subset] | 22,602 | 183.7 | Exact 7/9; evidence 7/9; P/R/F1 0.778/0.778/0.778 |
| perplexity/pplx-decider-v1.1-27b | Assembly prior [9-case subset] | 27,149 | 179.2 | Exact 6/9; evidence 2/9; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly prior-both [9-case subset] | 25,991 | 134.7 | Exact 6/9; evidence 2/9; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Assembly prior-summary [9-case subset] | 27,197 | 192.0 | Exact 6/9; evidence 2/9; P/R/F1 0.667/0.667/0.667 |
| perplexity/pplx-decider-v1.1-27b | Region gate resolved-b1 | 7,798 | 139.8 | 6/8 (75.0%) |
| perplexity/pplx-decider-v1.1-27b | Relationships resolved-b1 | 22,198 | 187.0 | 30/36 (83.3%) |
| qwen/qwen3.5-9b | Region gate rich-b1 | 4,203 | 54.5 | 8/8 (100.0%) |
| qwen/qwen3.5-9b | Relationships resolved-b1 | 10,785 | 59.0 | 17/36 (47.2%) |
| qwen/qwen3.5-9b | Relationships rich | 15,471 | 134.3 | 15/36 (41.7%) |
| respan/span-01 | Compatibility probe | — | — | HTTP404; no quality score; $0.30 reserved |
| togethercomputer/tev1-4b-experimental | Region gate resolved-b1 | 4,519 | 159.3 | 7/8 (87.5%) |
| togethercomputer/tev1-4b-experimental | Relationships resolved-b1 | 12,619 | 203.0 | 17/36 (47.2%) |
| typesafe/jev-1.13 | Region gate choice-b1 | 6,741 | 224.4 | 7/8 (87.5%) |
| typesafe/jev-1.13 | Region gate rich-b1 | 6,868 | 221.9 | 7/8 (87.5%) |
| typesafe/jev-1.13 | Relationships choice-b1 | 17,338 | 240.9 | 20/36 (55.6%) |
| typesafe/jev-1.13 | Relationships resolved | 16,973 | 1,258.3 | 25/36 (69.4%) |
| typesafe/jev-1.13 | Relationships resolved-b1 | 14,657 | 238.8 | 24/36 (66.7%) |
| typesafe/jev-1.13 | Relationships resolved-text-b1 | 22,597 | 237.7 | 24/36 (66.7%) |
| typesafe/jev-1.13 | Relationships rich | 19,472 | 1,231.1 | 17/36 (47.2%) |
| typesafe/jev-1.13 | Relationships rich-b1 | 16,512 | 235.3 | 14/36 (38.9%) |
| upstage/solar-decide-flash | Region gate resolved-b1 | 3,363 | 60.7 | 5/8 (62.5%) |
| upstage/solar-decide-flash | Relationships resolved-b1 | 7,998 | 57.2 | 25/36 (69.4%) |
| voyageai/voyage-multimodal-3.5 | Image embedding oracle-roi512 | 24,113 | 167.8 | Hit@1 1.000; Hit@3 1.000; Recall@1 0.500; Recall@3 1.000; MRR 1.000; pairs 23/24; ties 0; absent false hits 2/2 |
| voyageai/voyage-multimodal-3.5 | Image embedding page128 | 33,333 | 153.8 | Hit@1 0.500; Hit@3 1.000; Recall@1 0.250; Recall@3 0.833; MRR 0.694; pairs 17/24; ties 0; absent false hits 2/2 |
| voyageai/voyage-multimodal-3.5 | Image embedding page512 | 8,220 | 164.8 | Hit@1 1.000; Hit@3 1.000; Recall@1 0.500; Recall@3 1.000; MRR 1.000; pairs 22/24; ties 0; absent false hits 2/2 |

## Probability and selective-policy diagnostics

Confidence is secondary to measured ability. These retain the original fixed0.9/0.9 policy diagnostics, without using that policy to select the quality winners. All calibration-selected policies in these cohorts abstained; this is not calibrated correctness. Historical “unknown accepted” is an unsupported assertion count, not a proven semantic error.

| Model | Experiment | Truth Brier | Truth log loss | Truth ECE | Answerability Brier | Answerability log loss | Answerability ECE | Fixed-policy details |
|---|---|---:|---:|---:|---:|---:|---:|---|
| anthropic/claude-opus-4.6 | Region gate rich-b1 | 0.0439 | 0.1558 | 0.1212 | 0.0102 | 0.0808 | 0.0750 | {'total': 8, 'accepted': 6, 'accepted_labeled': 6, 'accepted_correct': 6, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 2, 'coverage': 0.75, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.39033428790216534, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.39033428790216534} |
| anthropic/claude-opus-4.6 | Relationships resolved | 0.1393 | 0.4306 | 0.1700 | 0.1841 | 0.5700 | 0.0871 | {'total': 48, 'accepted': 6, 'accepted_labeled': 4, 'accepted_correct': 4, 'accepted_wrong': 0, 'unknown_accepted': 2, 'unsafe_accepted': 2, 'abstained': 42, 'coverage': 0.125, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.4898908364545973, 'unsafe_rate': 0.3333333333333333, 'unsafe_rate_wilson95_upper': 0.7000066848616079} |
| anthropic/claude-opus-4.6 | Relationships rich | 0.1819 | 0.5392 | 0.2581 | 0.2053 | 0.6135 | 0.1040 | {'total': 48, 'accepted': 3, 'accepted_labeled': 2, 'accepted_correct': 2, 'accepted_wrong': 0, 'unknown_accepted': 1, 'unsafe_accepted': 1, 'abstained': 45, 'coverage': 0.0625, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.6576197724933469, 'unsafe_rate': 0.3333333333333333, 'unsafe_rate_wilson95_upper': 0.7923403991979523} |
| cloudflare/clef-flash | Region gate resolved-via-primeintellect-b1 | — | — | — | — | — | — | {'total': 8, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 8, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| cloudflare/clef-flash | Relationships resolved-b1 | 0.2376 | 0.6850 | 0.2804 | 0.2230 | 0.6523 | 0.1376 | {'total': 48, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 48, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| google/gemini-2.5-flash-lite | Region gate rich-b1 | 0.1250 | 4.3173 | 0.1250 | 0.0000 | 0.0000 | 0.0000 | {'total': 8, 'accepted': 8, 'accepted_labeled': 8, 'accepted_correct': 7, 'accepted_wrong': 1, 'unknown_accepted': 0, 'unsafe_accepted': 1, 'abstained': 0, 'coverage': 1.0, 'wrong_rate_labeled': 0.125, 'wrong_rate_labeled_wilson95_upper': 0.47088818221285345, 'unsafe_rate': 0.125, 'unsafe_rate_wilson95_upper': 0.47088818221285345} |
| google/gemini-2.5-flash-lite | Relationships resolved | 0.3783 | 11.6408 | 0.3833 | 0.2500 | 8.6347 | 0.2500 | {'total': 48, 'accepted': 48, 'accepted_labeled': 36, 'accepted_correct': 22, 'accepted_wrong': 14, 'unknown_accepted': 12, 'unsafe_accepted': 26, 'abstained': 0, 'coverage': 1.0, 'wrong_rate_labeled': 0.3888888888888889, 'wrong_rate_labeled_wilson95_upper': 0.5513554090339485, 'unsafe_rate': 0.5416666666666666, 'unsafe_rate_wilson95_upper': 0.6742475770713254} |
| google/gemini-2.5-flash-lite | Relationships rich | 0.3006 | 9.6610 | 0.3000 | 0.2500 | 8.6347 | 0.2500 | {'total': 48, 'accepted': 48, 'accepted_labeled': 36, 'accepted_correct': 25, 'accepted_wrong': 11, 'unknown_accepted': 12, 'unsafe_accepted': 23, 'abstained': 0, 'coverage': 1.0, 'wrong_rate_labeled': 0.3055555555555556, 'wrong_rate_labeled_wilson95_upper': 0.4685627285051034, 'unsafe_rate': 0.4791666666666667, 'unsafe_rate_wilson95_upper': 0.616707676966572} |
| inception/mercury-decide | Region gate resolved-b1 | 0.1170 | 0.4242 | 0.1228 | 0.3469 | 1.4794 | 0.3840 | {'total': 8, 'accepted': 5, 'accepted_labeled': 5, 'accepted_correct': 4, 'accepted_wrong': 1, 'unknown_accepted': 0, 'unsafe_accepted': 1, 'abstained': 3, 'coverage': 0.625, 'wrong_rate_labeled': 0.2, 'wrong_rate_labeled_wilson95_upper': 0.6244653702374747, 'unsafe_rate': 0.2, 'unsafe_rate_wilson95_upper': 0.6244653702374747} |
| inception/mercury-decide | Relationships resolved-b1 | 0.3438 | 1.1345 | 0.3526 | 0.4645 | 1.5705 | 0.4711 | {'total': 48, 'accepted': 13, 'accepted_labeled': 10, 'accepted_correct': 4, 'accepted_wrong': 6, 'unknown_accepted': 3, 'unsafe_accepted': 9, 'abstained': 35, 'coverage': 0.2708333333333333, 'wrong_rate_labeled': 0.6, 'wrong_rate_labeled_wilson95_upper': 0.8318196702937638, 'unsafe_rate': 0.6923076923076923, 'unsafe_rate_wilson95_upper': 0.8731929634428949} |
| liquid/d1 | Region gate resolved-b1 | 0.1049 | 0.2877 | 0.1389 | 0.1762 | 0.5664 | 0.2806 | {'total': 8, 'accepted': 3, 'accepted_labeled': 3, 'accepted_correct': 3, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 5, 'coverage': 0.375, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.5614970317550455, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.5614970317550455} |
| liquid/d1 | Relationships resolved-b1 | 0.3336 | 1.0182 | 0.3919 | 0.2424 | 1.0345 | 0.2424 | {'total': 48, 'accepted': 26, 'accepted_labeled': 18, 'accepted_correct': 12, 'accepted_wrong': 6, 'unknown_accepted': 8, 'unsafe_accepted': 14, 'abstained': 22, 'coverage': 0.5416666666666666, 'wrong_rate_labeled': 0.3333333333333333, 'wrong_rate_labeled_wilson95_upper': 0.5625053270405489, 'unsafe_rate': 0.5384615384615384, 'unsafe_rate_wilson95_upper': 0.7124414646960877} |
| openai/gpt-6-luna-decisions | Region gate resolved-b1 | 0.0004 | 0.0115 | 0.0113 | 0.0007 | 0.0179 | 0.0175 | {'total': 8, 'accepted': 8, 'accepted_labeled': 8, 'accepted_correct': 8, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 0, 'coverage': 1.0, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.32440756488388023, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.32440756488388023} |
| openai/gpt-6-luna-decisions | Relationships resolved-b1 | 0.1396 | 0.4387 | 0.1942 | 0.1697 | 0.5452 | 0.1210 | {'total': 48, 'accepted': 14, 'accepted_labeled': 10, 'accepted_correct': 9, 'accepted_wrong': 1, 'unknown_accepted': 4, 'unsafe_accepted': 5, 'abstained': 34, 'coverage': 0.2916666666666667, 'wrong_rate_labeled': 0.1, 'wrong_rate_labeled_wilson95_upper': 0.4041500267952385, 'unsafe_rate': 0.35714285714285715, 'unsafe_rate_wilson95_upper': 0.612355768960926} |
| perplexity/pplx-decider-v1.1-27b | Region gate resolved-b1 | 0.1800 | 0.5045 | 0.2060 | 0.0492 | 0.1581 | 0.1165 | {'total': 8, 'accepted': 6, 'accepted_labeled': 6, 'accepted_correct': 5, 'accepted_wrong': 1, 'unknown_accepted': 0, 'unsafe_accepted': 1, 'abstained': 2, 'coverage': 0.75, 'wrong_rate_labeled': 0.16666666666666666, 'wrong_rate_labeled_wilson95_upper': 0.5635028221864702, 'unsafe_rate': 0.16666666666666666, 'unsafe_rate_wilson95_upper': 0.5635028221864702} |
| perplexity/pplx-decider-v1.1-27b | Relationships resolved-b1 | 0.1458 | 0.4727 | 0.1928 | 0.2088 | 0.7076 | 0.2894 | {'total': 48, 'accepted': 17, 'accepted_labeled': 13, 'accepted_correct': 11, 'accepted_wrong': 2, 'unknown_accepted': 4, 'unsafe_accepted': 6, 'abstained': 31, 'coverage': 0.3541666666666667, 'wrong_rate_labeled': 0.15384615384615385, 'wrong_rate_labeled_wilson95_upper': 0.4223463101948253, 'unsafe_rate': 0.35294117647058826, 'unsafe_rate_wilson95_upper': 0.5869963651478131} |
| qwen/qwen3.5-9b | Region gate rich-b1 | 0.0002 | 0.0101 | 0.0100 | 0.0003 | 0.0077 | 0.0075 | {'total': 8, 'accepted': 8, 'accepted_labeled': 8, 'accepted_correct': 8, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 0, 'coverage': 1.0, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.32440756488388023, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.32440756488388023} |
| qwen/qwen3.5-9b | Relationships resolved-b1 | 0.4797 | 2.4715 | 0.4889 | 0.2480 | 7.9780 | 0.2485 | {'total': 48, 'accepted': 48, 'accepted_labeled': 36, 'accepted_correct': 17, 'accepted_wrong': 19, 'unknown_accepted': 12, 'unsafe_accepted': 31, 'abstained': 0, 'coverage': 1.0, 'wrong_rate_labeled': 0.5277777777777778, 'wrong_rate_labeled_wilson95_upper': 0.6801395848482095, 'unsafe_rate': 0.6458333333333334, 'unsafe_rate_wilson95_upper': 0.7656635587439514} |
| qwen/qwen3.5-9b | Relationships rich | 0.5258 | 4.3171 | 0.5378 | 0.2465 | 7.3301 | 0.2385 | {'total': 48, 'accepted': 48, 'accepted_labeled': 36, 'accepted_correct': 15, 'accepted_wrong': 21, 'unknown_accepted': 12, 'unsafe_accepted': 33, 'abstained': 0, 'coverage': 1.0, 'wrong_rate_labeled': 0.5833333333333334, 'wrong_rate_labeled_wilson95_upper': 0.7285943794855395, 'unsafe_rate': 0.6875, 'unsafe_rate_wilson95_upper': 0.8005431655341219} |
| togethercomputer/tev1-4b-experimental | Region gate resolved-b1 | 0.1132 | 0.3403 | 0.2301 | 0.2309 | 0.6982 | 0.3578 | {'total': 8, 'accepted': 3, 'accepted_labeled': 3, 'accepted_correct': 3, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 5, 'coverage': 0.375, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.5614970317550455, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.5614970317550455} |
| togethercomputer/tev1-4b-experimental | Relationships resolved-b1 | 0.2406 | 0.6507 | 0.2331 | 0.3220 | 0.9710 | 0.3207 | {'total': 48, 'accepted': 1, 'accepted_labeled': 1, 'accepted_correct': 1, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 47, 'coverage': 0.020833333333333332, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.7934506856227626, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.7934506856227626} |
| typesafe/jev-1.13 | Region gate choice-b1 | 0.0685 | 0.1958 | 0.1414 | 0.0001 | 0.0063 | 0.0062 | {'total': 8, 'accepted': 6, 'accepted_labeled': 6, 'accepted_correct': 6, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 2, 'coverage': 0.75, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.39033428790216534, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.39033428790216534} |
| typesafe/jev-1.13 | Region gate rich-b1 | 0.1063 | 0.3356 | 0.2238 | 0.0167 | 0.1270 | 0.1175 | {'total': 8, 'accepted': 3, 'accepted_labeled': 3, 'accepted_correct': 3, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 5, 'coverage': 0.375, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.5614970317550455, 'unsafe_rate': 0.0, 'unsafe_rate_wilson95_upper': 0.5614970317550455} |
| typesafe/jev-1.13 | Relationships choice-b1 | 0.2691 | 0.7217 | 0.3556 | 0.2249 | 0.7897 | 0.1831 | {'total': 48, 'accepted': 18, 'accepted_labeled': 12, 'accepted_correct': 12, 'accepted_wrong': 0, 'unknown_accepted': 6, 'unsafe_accepted': 6, 'abstained': 30, 'coverage': 0.375, 'wrong_rate_labeled': 0.0, 'wrong_rate_labeled_wilson95_upper': 0.24249400665524087, 'unsafe_rate': 0.3333333333333333, 'unsafe_rate_wilson95_upper': 0.5625053270405489} |
| typesafe/jev-1.13 | Relationships resolved | 0.1695 | 0.5079 | 0.2781 | 0.1799 | 0.5506 | 0.1237 | {'total': 48, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 48, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| typesafe/jev-1.13 | Relationships resolved-b1 | 0.2430 | 0.6782 | 0.3353 | 0.1946 | 0.5830 | 0.0573 | {'total': 48, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 48, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| typesafe/jev-1.13 | Relationships resolved-text-b1 | 0.2091 | 0.5938 | 0.2800 | 0.1970 | 0.5864 | 0.1413 | {'total': 48, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 48, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| typesafe/jev-1.13 | Relationships rich | 0.2683 | 0.7329 | 0.2889 | 0.1908 | 0.5683 | 0.0558 | {'total': 48, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 48, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| typesafe/jev-1.13 | Relationships rich-b1 | 0.3062 | 0.8116 | 0.3125 | 0.2103 | 0.6167 | 0.1921 | {'total': 48, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 48, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| upstage/solar-decide-flash | Region gate resolved-b1 | 0.2092 | 0.5885 | 0.3920 | 0.0535 | 0.2508 | 0.2175 | {'total': 8, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 8, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |
| upstage/solar-decide-flash | Relationships resolved-b1 | 0.2076 | 0.6056 | 0.2247 | 0.2208 | 0.6328 | 0.1723 | {'total': 48, 'accepted': 0, 'accepted_labeled': 0, 'accepted_correct': 0, 'accepted_wrong': 0, 'unknown_accepted': 0, 'unsafe_accepted': 0, 'abstained': 48, 'coverage': 0.0, 'wrong_rate_labeled': None, 'wrong_rate_labeled_wilson95_upper': None, 'unsafe_rate': None, 'unsafe_rate_wilson95_upper': None} |

## Source reports and exclusions

- [Relationships and task slices](decision-alternatives.md); [complete legacy scores](decisions-latest.md); [gate scores](decisions-controls-latest.md). These also retain task/family breakdowns and selected-policy diagnostics.
- [Assembly and visual ablations](evidence-repair.md); [image retrieval](image-embedding-retrieval.md); [contamination audit](evidence-contamination-audit.md).
- Native rule control and constructed candidate oracle both score30/30; CPU/API financial comparability is not available. [Rust color experiment](color-regions.md): native10/10boundary controls, rasterpale8/8atthreshold8and0/8at18/36; outlines2/2with4extras. These are geometry-component results, not hosted model extraction.
- [Earlier SLANet specialist](specialist-cpu.md): cropped4/4smalltables,35/35smallcells; dense17/35spotcells; prose1/2falsepositives. No defensible per-page rental allocation or comparable timed cohort is available here, so no invented pages/$ rate.
- Offline model router:29/36versusLuna31/36; it reused existing predictions and incurred no new inference. Nemotron embeddings were catalogued/registered but not benchmarked.
- Gemini3.1FlashLite smoke had no complete scored cohort; Span and the Clef PrimeIntellect route had availability failures. Failed rows have no accuracy/throughput estimate.

Generated from `bench/results/pdf-master-artifacts/decisions/{ledger,evaluation,evaluation-controls,context-run-*,retrieval/results}.json`. Values may overlap requests across experiment arms; do not sum per-arm costs to estimate actual campaign spend.
