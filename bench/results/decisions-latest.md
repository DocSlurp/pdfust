# PDF decision probability pilot

- Small synthetic PDF decision study; these results do not establish production safety.
- Raw native, heuristic, or self-reported scores are not calibrated probabilities.
- Threshold selection uses calibration cases only and does not calibrate probabilities.
- Probability metrics exclude failed predictions and publish sample counts; operational metrics retain failures.
- Gold None denotes insufficient evidence; accepting either answer is counted as unsafe.
- Wilson intervals are descriptive and do not correct for grid selection or correlated synthetic variants.
- No per-case latency or cost aggregation: batches require unique request accounting in the inference runner.

Cases: calibration 48; test 48.

| Model / policy | Test N | Labeled N | Failures | Forced accuracy | Probability N | Brier | Log loss | ECE | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic/claude-opus-4.6@resolved / fixed | 48 | 36 | 0 | 0.806 | 36 | 0.139 | 0.431 | 0.170 | 6 | 0 | 2 | 0.700 |
| anthropic/claude-opus-4.6@resolved / selected | 48 | 36 | 0 | 0.806 | 36 | 0.139 | 0.431 | 0.170 | 0 | 0 | 0 | n/a |
| anthropic/claude-opus-4.6@rich / fixed | 48 | 36 | 0 | 0.750 | 36 | 0.182 | 0.539 | 0.258 | 3 | 0 | 1 | 0.792 |
| anthropic/claude-opus-4.6@rich / selected | 48 | 36 | 0 | 0.750 | 36 | 0.182 | 0.539 | 0.258 | 0 | 0 | 0 | n/a |
| baseline / fixed | 48 | 36 | 0 | 0.417 | 36 | 0.369 | 0.972 | 0.361 | 0 | 0 | 0 | n/a |
| baseline / selected | 48 | 36 | 0 | 0.417 | 36 | 0.369 | 0.972 | 0.361 | 0 | 0 | 0 | n/a |
| google/gemini-2.5-flash-lite@resolved / fixed | 48 | 36 | 0 | 0.611 | 36 | 0.378 | 11.641 | 0.383 | 48 | 14 | 12 | 0.674 |
| google/gemini-2.5-flash-lite@resolved / selected | 48 | 36 | 0 | 0.611 | 36 | 0.378 | 11.641 | 0.383 | 0 | 0 | 0 | n/a |
| google/gemini-2.5-flash-lite@rich / fixed | 48 | 36 | 0 | 0.694 | 36 | 0.301 | 9.661 | 0.300 | 48 | 11 | 12 | 0.617 |
| google/gemini-2.5-flash-lite@rich / selected | 48 | 36 | 0 | 0.694 | 36 | 0.301 | 9.661 | 0.300 | 0 | 0 | 0 | n/a |
| qwen/qwen3.5-9b@resolved-b1 / fixed | 48 | 36 | 0 | 0.472 | 36 | 0.480 | 2.472 | 0.489 | 48 | 19 | 12 | 0.766 |
| qwen/qwen3.5-9b@resolved-b1 / selected | 48 | 36 | 0 | 0.472 | 36 | 0.480 | 2.472 | 0.489 | 0 | 0 | 0 | n/a |
| qwen/qwen3.5-9b@rich / fixed | 48 | 36 | 0 | 0.417 | 36 | 0.526 | 4.317 | 0.538 | 48 | 21 | 12 | 0.801 |
| qwen/qwen3.5-9b@rich / selected | 48 | 36 | 0 | 0.417 | 36 | 0.526 | 4.317 | 0.538 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@choice-b1 / fixed | 48 | 36 | 0 | 0.556 | 36 | 0.269 | 0.722 | 0.356 | 18 | 0 | 6 | 0.563 |
| typesafe/jev-1.13@choice-b1 / selected | 48 | 36 | 0 | 0.556 | 36 | 0.269 | 0.722 | 0.356 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@resolved / fixed | 48 | 36 | 0 | 0.694 | 36 | 0.169 | 0.508 | 0.278 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@resolved / selected | 48 | 36 | 0 | 0.694 | 36 | 0.169 | 0.508 | 0.278 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@resolved-b1 / fixed | 48 | 36 | 0 | 0.667 | 36 | 0.243 | 0.678 | 0.335 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@resolved-b1 / selected | 48 | 36 | 0 | 0.667 | 36 | 0.243 | 0.678 | 0.335 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@resolved-text-b1 / fixed | 48 | 36 | 0 | 0.667 | 36 | 0.209 | 0.594 | 0.280 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@resolved-text-b1 / selected | 48 | 36 | 0 | 0.667 | 36 | 0.209 | 0.594 | 0.280 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@rich / fixed | 48 | 36 | 0 | 0.472 | 36 | 0.268 | 0.733 | 0.289 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@rich / selected | 48 | 36 | 0 | 0.472 | 36 | 0.268 | 0.733 | 0.289 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@rich-b1 / fixed | 48 | 36 | 0 | 0.389 | 36 | 0.306 | 0.812 | 0.313 | 0 | 0 | 0 | n/a |
| typesafe/jev-1.13@rich-b1 / selected | 48 | 36 | 0 | 0.389 | 36 | 0.306 | 0.812 | 0.313 | 0 | 0 | 0 | n/a |

**anthropic/claude-opus-4.6@resolved selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.778 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 0.778 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.556 | 3 | 0 | 2 | 0.939 |
| task:header / selected | 12 | 9 | 0 | 0.556 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 1.000 | 1 | 0 | 0 | 0.793 |
| task:table / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.889 | 2 | 0 | 0 | 0.658 |
| task:wrap / selected | 12 | 9 | 0 | 0.889 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.750 | 4 | 0 | 1 | 0.699 |
| family:financial / selected | 16 | 12 | 0 | 0.750 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.833 | 1 | 0 | 1 | 1.000 |
| family:invoice / selected | 16 | 12 | 0 | 0.833 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.833 | 1 | 0 | 0 | 0.793 |
| family:scientific / selected | 16 | 12 | 0 | 0.833 | 0 | 0 | 0 | n/a |


**anthropic/claude-opus-4.6@rich selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.889 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 0.889 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.444 | 1 | 0 | 1 | 1.000 |
| task:header / selected | 12 | 9 | 0 | 0.444 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.889 | 2 | 0 | 0 | 0.658 |
| task:table / selected | 12 | 9 | 0 | 0.889 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.778 | 0 | 0 | 0 | n/a |
| task:wrap / selected | 12 | 9 | 0 | 0.778 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.833 | 1 | 0 | 0 | 0.793 |
| family:financial / selected | 16 | 12 | 0 | 0.833 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.667 | 2 | 0 | 1 | 0.905 |
| family:invoice / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.750 | 0 | 0 | 0 | n/a |
| family:scientific / selected | 16 | 12 | 0 | 0.750 | 0 | 0 | 0 | n/a |


**baseline selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: heuristic_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.000 | 0 | 0 | 0 | n/a |
| task:header / selected | 12 | 9 | 0 | 0.000 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:table / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.000 | 0 | 0 | 0 | n/a |
| task:wrap / selected | 12 | 9 | 0 | 0.000 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:financial / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:invoice / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:scientific / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |


**google/gemini-2.5-flash-lite@resolved selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.778 | 12 | 2 | 3 | 0.680 |
| task:assignment / selected | 12 | 9 | 0 | 0.778 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.667 | 12 | 3 | 3 | 0.746 |
| task:header / selected | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.667 | 12 | 3 | 3 | 0.746 |
| task:table / selected | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.333 | 12 | 6 | 3 | 0.911 |
| task:wrap / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.417 | 16 | 7 | 4 | 0.858 |
| family:financial / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.750 | 16 | 3 | 4 | 0.668 |
| family:invoice / selected | 16 | 12 | 0 | 0.750 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.667 | 16 | 4 | 4 | 0.720 |
| family:scientific / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |


**google/gemini-2.5-flash-lite@rich selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.667 | 12 | 3 | 3 | 0.746 |
| task:assignment / selected | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.667 | 12 | 3 | 3 | 0.746 |
| task:header / selected | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.889 | 12 | 1 | 3 | 0.609 |
| task:table / selected | 12 | 9 | 0 | 0.889 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.556 | 12 | 4 | 3 | 0.807 |
| task:wrap / selected | 12 | 9 | 0 | 0.556 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.750 | 16 | 3 | 4 | 0.668 |
| family:financial / selected | 16 | 12 | 0 | 0.750 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.750 | 16 | 3 | 4 | 0.668 |
| family:invoice / selected | 16 | 12 | 0 | 0.750 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.583 | 16 | 5 | 4 | 0.769 |
| family:scientific / selected | 16 | 12 | 0 | 0.583 | 0 | 0 | 0 | n/a |


**qwen/qwen3.5-9b@resolved-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 1.000 | 12 | 0 | 3 | 0.532 |
| task:assignment / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.333 | 12 | 6 | 3 | 0.911 |
| task:header / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.333 | 12 | 6 | 3 | 0.911 |
| task:table / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.222 | 12 | 7 | 3 | 0.953 |
| task:wrap / selected | 12 | 9 | 0 | 0.222 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.500 | 16 | 6 | 4 | 0.815 |
| family:financial / selected | 16 | 12 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.500 | 16 | 6 | 4 | 0.815 |
| family:invoice / selected | 16 | 12 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.417 | 16 | 7 | 4 | 0.858 |
| family:scientific / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |


**qwen/qwen3.5-9b@rich selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: self_reported.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.333 | 12 | 6 | 3 | 0.911 |
| task:assignment / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.333 | 12 | 6 | 3 | 0.911 |
| task:header / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.556 | 12 | 4 | 3 | 0.807 |
| task:table / selected | 12 | 9 | 0 | 0.556 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.444 | 12 | 5 | 3 | 0.862 |
| task:wrap / selected | 12 | 9 | 0 | 0.444 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.417 | 16 | 7 | 4 | 0.858 |
| family:financial / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.500 | 16 | 6 | 4 | 0.815 |
| family:invoice / selected | 16 | 12 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.333 | 16 | 8 | 4 | 0.898 |
| family:scientific / selected | 16 | 12 | 0 | 0.333 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@choice-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: conditional_choice_mass.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 1.000 | 7 | 0 | 0 | 0.354 |
| task:assignment / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.333 | 6 | 0 | 3 | 0.812 |
| task:header / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.556 | 0 | 0 | 0 | n/a |
| task:table / selected | 12 | 9 | 0 | 0.556 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.333 | 5 | 0 | 3 | 0.882 |
| task:wrap / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.583 | 6 | 0 | 2 | 0.700 |
| family:financial / selected | 16 | 12 | 0 | 0.583 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.500 | 6 | 0 | 2 | 0.700 |
| family:invoice / selected | 16 | 12 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.583 | 6 | 0 | 2 | 0.700 |
| family:scientific / selected | 16 | 12 | 0 | 0.583 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@resolved selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: native_decision_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:header / selected | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:table / selected | 12 | 9 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.444 | 0 | 0 | 0 | n/a |
| task:wrap / selected | 12 | 9 | 0 | 0.444 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.583 | 0 | 0 | 0 | n/a |
| family:financial / selected | 16 | 12 | 0 | 0.583 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:invoice / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.833 | 0 | 0 | 0 | n/a |
| family:scientific / selected | 16 | 12 | 0 | 0.833 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@resolved-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: native_decision_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:header / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:table / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:wrap / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:financial / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:invoice / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:scientific / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@resolved-text-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: native_decision_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:header / selected | 12 | 9 | 0 | 1.000 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:table / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:wrap / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:financial / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:invoice / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |
| family:scientific / selected | 16 | 12 | 0 | 0.667 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@rich selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: native_decision_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.444 | 0 | 0 | 0 | n/a |
| task:header / selected | 12 | 9 | 0 | 0.444 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.778 | 0 | 0 | 0 | n/a |
| task:table / selected | 12 | 9 | 0 | 0.778 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:wrap / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.583 | 0 | 0 | 0 | n/a |
| family:financial / selected | 16 | 12 | 0 | 0.583 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:invoice / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:scientific / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |


**typesafe/jev-1.13@rich-b1 selected policy:** abstain all. No calibration threshold meets minimum support and the Wilson unsafe-rate bound.

Raw score provenance: native_decision_score.

| Slice / policy | Test N | Labeled N | Failures | Forced accuracy | Accepted | Wrong | Unknown accepted | Unsafe Wilson upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task:assignment / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:assignment / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:header / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:header / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:table / fixed | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:table / selected | 12 | 9 | 0 | 0.333 | 0 | 0 | 0 | n/a |
| task:wrap / fixed | 12 | 9 | 0 | 0.556 | 0 | 0 | 0 | n/a |
| task:wrap / selected | 12 | 9 | 0 | 0.556 | 0 | 0 | 0 | n/a |
| family:financial / fixed | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:financial / selected | 16 | 12 | 0 | 0.417 | 0 | 0 | 0 | n/a |
| family:invoice / fixed | 16 | 12 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:invoice / selected | 16 | 12 | 0 | 0.500 | 0 | 0 | 0 | n/a |
| family:scientific / fixed | 16 | 12 | 0 | 0.250 | 0 | 0 | 0 | n/a |
| family:scientific / selected | 16 | 12 | 0 | 0.250 | 0 | 0 | 0 | n/a |

Fixed policy: confidence ≥ 0.9 and answerability ≥ 0.9. A probability of exactly 0.5 predicts yes.

Selection requires ≥ 8 accepted calibration cases and unsafe-rate Wilson upper ≤ 0.1.

Zero observed wrong decisions does not imply zero risk. Full threshold curves and reliability bins are retained in JSON.
## Frozen cohort and assembly analysis

- The baseline is an illustrative geometry/type heuristic, not native extractor quality.
- Frozen labels describe synthetic author intent; they are not independently annotated real-world PDF truth.
- Unknown wrap controls contain 'continued detail', which provides a plausible continuation cue.
- Unknown headers place 'Observed Value' above aligned values, a conventional header cue.
- Negative 'Provisional estimate only' controls can plausibly qualify a numeric column.
- Unit-mismatched assignment controls supply stronger observable evidence than hidden-intent controls.
- Related templates, vocabularies, and instruction variants do not constitute independent samples.
- Calibration/test label priors differ; threshold transfer includes class-prior shift.
- Source-word conservation protects retained data; it does not establish correct logical relationships.
- Isolation comparisons describe batch sensitivity and do not identify its causal mechanism.

| Cohort / split | Status | Successful / total | Known correct / N | Known accuracy |
|---|---|---:|---:|---:|
| anthropic/claude-opus-4.6@resolved / calibration | complete | 48/48 | 30/36 | 0.833 |
| anthropic/claude-opus-4.6@resolved / test | complete | 48/48 | 29/36 | 0.806 |
| anthropic/claude-opus-4.6@rich / calibration | complete | 48/48 | 24/36 | 0.667 |
| anthropic/claude-opus-4.6@rich / test | complete | 48/48 | 27/36 | 0.750 |
| baseline / calibration | complete | 48/48 | 21/36 | 0.583 |
| baseline / test | complete | 48/48 | 15/36 | 0.417 |
| google/gemini-2.5-flash-lite@resolved / calibration | complete | 48/48 | 20/36 | 0.556 |
| google/gemini-2.5-flash-lite@resolved / test | complete | 48/48 | 22/36 | 0.611 |
| google/gemini-2.5-flash-lite@rich / calibration | complete | 48/48 | 17/36 | 0.472 |
| google/gemini-2.5-flash-lite@rich / test | complete | 48/48 | 25/36 | 0.694 |
| qwen/qwen3.5-9b@resolved-b1 / calibration | complete | 48/48 | 20/36 | 0.556 |
| qwen/qwen3.5-9b@resolved-b1 / test | complete | 48/48 | 17/36 | 0.472 |
| qwen/qwen3.5-9b@rich / calibration | complete | 48/48 | 25/36 | 0.694 |
| qwen/qwen3.5-9b@rich / test | complete | 48/48 | 15/36 | 0.417 |
| typesafe/jev-1.13@choice-b1 / calibration | complete | 48/48 | 26/36 | 0.722 |
| typesafe/jev-1.13@choice-b1 / test | complete | 48/48 | 20/36 | 0.556 |
| typesafe/jev-1.13@resolved / calibration | complete | 48/48 | 28/36 | 0.778 |
| typesafe/jev-1.13@resolved / test | complete | 48/48 | 25/36 | 0.694 |
| typesafe/jev-1.13@resolved-b1 / calibration | complete | 48/48 | 29/36 | 0.806 |
| typesafe/jev-1.13@resolved-b1 / test | complete | 48/48 | 24/36 | 0.667 |
| typesafe/jev-1.13@resolved-text-b1 / calibration | complete | 48/48 | 30/36 | 0.833 |
| typesafe/jev-1.13@resolved-text-b1 / test | complete | 48/48 | 24/36 | 0.667 |
| typesafe/jev-1.13@rich / calibration | complete | 48/48 | 25/36 | 0.694 |
| typesafe/jev-1.13@rich / test | complete | 48/48 | 17/36 | 0.472 |
| typesafe/jev-1.13@rich-b1 / calibration | complete | 48/48 | 19/36 | 0.528 |
| typesafe/jev-1.13@rich-b1 / test | complete | 48/48 | 14/36 | 0.389 |

### Retained-source application

| Cohort / split / policy | Affirmative requested | Applied | Correct | Wrong | Unknown | Constraint refusals | Source words before / after | Preserved cases / total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic/claude-opus-4.6@resolved / calibration / fixed | 7 | 7 | 5 | 0 | 2 | 0 | 540/540 | 48/48 |
| anthropic/claude-opus-4.6@resolved / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| anthropic/claude-opus-4.6@resolved / test / fixed | 4 | 4 | 2 | 0 | 2 | 0 | 675/675 | 48/48 |
| anthropic/claude-opus-4.6@resolved / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| anthropic/claude-opus-4.6@rich / calibration / fixed | 11 | 11 | 8 | 0 | 3 | 0 | 540/540 | 48/48 |
| anthropic/claude-opus-4.6@rich / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| anthropic/claude-opus-4.6@rich / test / fixed | 3 | 3 | 2 | 0 | 1 | 0 | 675/675 | 48/48 |
| anthropic/claude-opus-4.6@rich / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| baseline / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| baseline / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| baseline / test / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| baseline / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| google/gemini-2.5-flash-lite@resolved / calibration / fixed | 25 | 25 | 13 | 5 | 7 | 0 | 540/540 | 48/48 |
| google/gemini-2.5-flash-lite@resolved / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| google/gemini-2.5-flash-lite@resolved / test / fixed | 20 | 20 | 5 | 7 | 8 | 0 | 675/675 | 48/48 |
| google/gemini-2.5-flash-lite@resolved / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| google/gemini-2.5-flash-lite@rich / calibration / fixed | 8 | 8 | 5 | 0 | 3 | 0 | 540/540 | 48/48 |
| google/gemini-2.5-flash-lite@rich / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| google/gemini-2.5-flash-lite@rich / test / fixed | 6 | 6 | 3 | 2 | 1 | 0 | 675/675 | 48/48 |
| google/gemini-2.5-flash-lite@rich / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| qwen/qwen3.5-9b@resolved-b1 / calibration / fixed | 33 | 33 | 16 | 8 | 9 | 0 | 540/540 | 48/48 |
| qwen/qwen3.5-9b@resolved-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| qwen/qwen3.5-9b@resolved-b1 / test / fixed | 39 | 39 | 11 | 18 | 10 | 0 | 675/675 | 48/48 |
| qwen/qwen3.5-9b@resolved-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| qwen/qwen3.5-9b@rich / calibration / fixed | 42 | 42 | 21 | 9 | 12 | 0 | 540/540 | 48/48 |
| qwen/qwen3.5-9b@rich / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| qwen/qwen3.5-9b@rich / test / fixed | 42 | 42 | 12 | 21 | 9 | 0 | 675/675 | 48/48 |
| qwen/qwen3.5-9b@rich / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@choice-b1 / calibration / fixed | 18 | 18 | 12 | 0 | 6 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@choice-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@choice-b1 / test / fixed | 12 | 12 | 6 | 0 | 6 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@choice-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@resolved / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@resolved / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@resolved / test / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@resolved / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@resolved-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@resolved-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@resolved-b1 / test / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@resolved-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@resolved-text-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@resolved-text-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@resolved-text-b1 / test / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@resolved-text-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@rich / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@rich / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@rich / test / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@rich / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@rich-b1 / calibration / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@rich-b1 / calibration / selected | 0 | 0 | 0 | 0 | 0 | 0 | 540/540 | 48/48 |
| typesafe/jev-1.13@rich-b1 / test / fixed | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |
| typesafe/jev-1.13@rich-b1 / test / selected | 0 | 0 | 0 | 0 | 0 | 0 | 675/675 | 48/48 |

### Known-label task slices

| Cohort / split / task | Status | Known correct / N | Known accuracy |
|---|---|---:|---:|
| anthropic/claude-opus-4.6@resolved / calibration / assignment | complete | 7/9 | 0.778 |
| anthropic/claude-opus-4.6@resolved / calibration / header | complete | 5/9 | 0.556 |
| anthropic/claude-opus-4.6@resolved / calibration / table | complete | 9/9 | 1.000 |
| anthropic/claude-opus-4.6@resolved / calibration / wrap | complete | 9/9 | 1.000 |
| anthropic/claude-opus-4.6@resolved / test / assignment | complete | 7/9 | 0.778 |
| anthropic/claude-opus-4.6@resolved / test / header | complete | 5/9 | 0.556 |
| anthropic/claude-opus-4.6@resolved / test / table | complete | 9/9 | 1.000 |
| anthropic/claude-opus-4.6@resolved / test / wrap | complete | 8/9 | 0.889 |
| anthropic/claude-opus-4.6@rich / calibration / assignment | complete | 2/9 | 0.222 |
| anthropic/claude-opus-4.6@rich / calibration / header | complete | 6/9 | 0.667 |
| anthropic/claude-opus-4.6@rich / calibration / table | complete | 8/9 | 0.889 |
| anthropic/claude-opus-4.6@rich / calibration / wrap | complete | 8/9 | 0.889 |
| anthropic/claude-opus-4.6@rich / test / assignment | complete | 8/9 | 0.889 |
| anthropic/claude-opus-4.6@rich / test / header | complete | 4/9 | 0.444 |
| anthropic/claude-opus-4.6@rich / test / table | complete | 8/9 | 0.889 |
| anthropic/claude-opus-4.6@rich / test / wrap | complete | 7/9 | 0.778 |
| baseline / calibration / assignment | complete | 3/9 | 0.333 |
| baseline / calibration / header | complete | 3/9 | 0.333 |
| baseline / calibration / table | complete | 9/9 | 1.000 |
| baseline / calibration / wrap | complete | 6/9 | 0.667 |
| baseline / test / assignment | complete | 6/9 | 0.667 |
| baseline / test / header | complete | 0/9 | 0.000 |
| baseline / test / table | complete | 9/9 | 1.000 |
| baseline / test / wrap | complete | 0/9 | 0.000 |
| google/gemini-2.5-flash-lite@resolved / calibration / assignment | complete | 7/9 | 0.778 |
| google/gemini-2.5-flash-lite@resolved / calibration / header | complete | 3/9 | 0.333 |
| google/gemini-2.5-flash-lite@resolved / calibration / table | complete | 7/9 | 0.778 |
| google/gemini-2.5-flash-lite@resolved / calibration / wrap | complete | 3/9 | 0.333 |
| google/gemini-2.5-flash-lite@resolved / test / assignment | complete | 7/9 | 0.778 |
| google/gemini-2.5-flash-lite@resolved / test / header | complete | 6/9 | 0.667 |
| google/gemini-2.5-flash-lite@resolved / test / table | complete | 6/9 | 0.667 |
| google/gemini-2.5-flash-lite@resolved / test / wrap | complete | 3/9 | 0.333 |
| google/gemini-2.5-flash-lite@rich / calibration / assignment | complete | 3/9 | 0.333 |
| google/gemini-2.5-flash-lite@rich / calibration / header | complete | 3/9 | 0.333 |
| google/gemini-2.5-flash-lite@rich / calibration / table | complete | 8/9 | 0.889 |
| google/gemini-2.5-flash-lite@rich / calibration / wrap | complete | 3/9 | 0.333 |
| google/gemini-2.5-flash-lite@rich / test / assignment | complete | 6/9 | 0.667 |
| google/gemini-2.5-flash-lite@rich / test / header | complete | 6/9 | 0.667 |
| google/gemini-2.5-flash-lite@rich / test / table | complete | 8/9 | 0.889 |
| google/gemini-2.5-flash-lite@rich / test / wrap | complete | 5/9 | 0.556 |
| qwen/qwen3.5-9b@resolved-b1 / calibration / assignment | complete | 5/9 | 0.556 |
| qwen/qwen3.5-9b@resolved-b1 / calibration / header | complete | 6/9 | 0.667 |
| qwen/qwen3.5-9b@resolved-b1 / calibration / table | complete | 6/9 | 0.667 |
| qwen/qwen3.5-9b@resolved-b1 / calibration / wrap | complete | 3/9 | 0.333 |
| qwen/qwen3.5-9b@resolved-b1 / test / assignment | complete | 9/9 | 1.000 |
| qwen/qwen3.5-9b@resolved-b1 / test / header | complete | 3/9 | 0.333 |
| qwen/qwen3.5-9b@resolved-b1 / test / table | complete | 3/9 | 0.333 |
| qwen/qwen3.5-9b@resolved-b1 / test / wrap | complete | 2/9 | 0.222 |
| qwen/qwen3.5-9b@rich / calibration / assignment | complete | 6/9 | 0.667 |
| qwen/qwen3.5-9b@rich / calibration / header | complete | 6/9 | 0.667 |
| qwen/qwen3.5-9b@rich / calibration / table | complete | 8/9 | 0.889 |
| qwen/qwen3.5-9b@rich / calibration / wrap | complete | 5/9 | 0.556 |
| qwen/qwen3.5-9b@rich / test / assignment | complete | 3/9 | 0.333 |
| qwen/qwen3.5-9b@rich / test / header | complete | 3/9 | 0.333 |
| qwen/qwen3.5-9b@rich / test / table | complete | 5/9 | 0.556 |
| qwen/qwen3.5-9b@rich / test / wrap | complete | 4/9 | 0.444 |
| typesafe/jev-1.13@choice-b1 / calibration / assignment | complete | 8/9 | 0.889 |
| typesafe/jev-1.13@choice-b1 / calibration / header | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@choice-b1 / calibration / table | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@choice-b1 / calibration / wrap | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@choice-b1 / test / assignment | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@choice-b1 / test / header | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@choice-b1 / test / table | complete | 5/9 | 0.556 |
| typesafe/jev-1.13@choice-b1 / test / wrap | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@resolved / calibration / assignment | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved / calibration / header | complete | 5/9 | 0.556 |
| typesafe/jev-1.13@resolved / calibration / table | complete | 7/9 | 0.778 |
| typesafe/jev-1.13@resolved / calibration / wrap | complete | 7/9 | 0.778 |
| typesafe/jev-1.13@resolved / test / assignment | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved / test / header | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@resolved / test / table | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@resolved / test / wrap | complete | 4/9 | 0.444 |
| typesafe/jev-1.13@resolved-b1 / calibration / assignment | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved-b1 / calibration / header | complete | 8/9 | 0.889 |
| typesafe/jev-1.13@resolved-b1 / calibration / table | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@resolved-b1 / calibration / wrap | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@resolved-b1 / test / assignment | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved-b1 / test / header | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved-b1 / test / table | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@resolved-b1 / test / wrap | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@resolved-text-b1 / calibration / assignment | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved-text-b1 / calibration / header | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved-text-b1 / calibration / table | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@resolved-text-b1 / calibration / wrap | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@resolved-text-b1 / test / assignment | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved-text-b1 / test / header | complete | 9/9 | 1.000 |
| typesafe/jev-1.13@resolved-text-b1 / test / table | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@resolved-text-b1 / test / wrap | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@rich / calibration / assignment | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@rich / calibration / header | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@rich / calibration / table | complete | 7/9 | 0.778 |
| typesafe/jev-1.13@rich / calibration / wrap | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@rich / test / assignment | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@rich / test / header | complete | 4/9 | 0.444 |
| typesafe/jev-1.13@rich / test / table | complete | 7/9 | 0.778 |
| typesafe/jev-1.13@rich / test / wrap | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@rich-b1 / calibration / assignment | complete | 5/9 | 0.556 |
| typesafe/jev-1.13@rich-b1 / calibration / header | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@rich-b1 / calibration / table | complete | 6/9 | 0.667 |
| typesafe/jev-1.13@rich-b1 / calibration / wrap | complete | 2/9 | 0.222 |
| typesafe/jev-1.13@rich-b1 / test / assignment | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@rich-b1 / test / header | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@rich-b1 / test / table | complete | 3/9 | 0.333 |
| typesafe/jev-1.13@rich-b1 / test / wrap | complete | 5/9 | 0.556 |

### Identical-observation singleton versus batch

| Model / split | Paired successes / N | Forced flips | Fixed outcome flips | Mean decision delta | Max decision delta | Max answerability delta |
|---|---:|---:|---:|---:|---:|---:|
| typesafe/jev-1.13@resolved / calibration | 48/48 | 7 | 0 | 0.121 | 0.520 | 0.250 |
| typesafe/jev-1.13@resolved / test | 48/48 | 10 | 0 | 0.136 | 0.460 | 0.310 |
| typesafe/jev-1.13@rich / calibration | 48/48 | 14 | 0 | 0.103 | 0.370 | 0.310 |
| typesafe/jev-1.13@rich / test | 48/48 | 19 | 0 | 0.151 | 0.440 | 0.280 |

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
