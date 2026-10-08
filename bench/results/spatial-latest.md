# CPU spatial field assignment

Synthetic account fields; label, scale, and content-order shift held out. Not calibrated real-document accuracy.

Six-feature logistic ranker; 240 training PDFs, 80 separate policy-selection PDFs,
160 evaluation PDFs (128 values, 32 missing-value controls). All inference and training use CPU.
Model coefficients are opt-in and are not shipped as a general-purpose pretrained model.

| Method | Correct accepted | Wrong accepted | Abstained | Missing values rejected |
| --- | ---: | ---: | ---: | ---: |
| Unique candidate only | 0 | 0 | 160 | 32/32 |
| Distance/alignment rule | 128 | 0 | 32 | 32/32 |
| Tiny ranker | 104 | 0 | 56 | 32/32 |

Fitted state: 195 bytes of JSON; no tensor runtime or model download.
Policy selected on validation only: threshold 0.8, margin 0.3.
Geometric policy also selected on validation only: threshold 0.4, margin 0.2.

| Operation | Median |
| --- | ---: |
| candidate_score_us | 1.430 microseconds |
| field_query_with_model_us | 57.511 microseconds |
| field_query_without_model_us | 38.741 microseconds |
| rectangle_query_us | 3.259 microseconds |
| fit_seconds | 0.237 seconds |
| total_seconds | 7.696 seconds |

Timings are one local CPU run, with warmed query state; they exclude PDF opening and interpretation.

| First-call public API (opening excluded) | Input | Median milliseconds |
| --- | --- | ---: |
| separate_words_and_tables | senate-expenditures.pdf | 16.102 |
| spatial_snapshot | senate-expenditures.pdf | 12.665 |
| separate_words_and_tables | nics-background-checks-2015-11.pdf | 41.341 |
| spatial_snapshot | nics-background-checks-2015-11.pdf | 48.541 |

Seven repetitions per first-call API. Both include geometry extraction and Python materialization;
the spatial API also constructs the query index and source-word membership for every cell.
These measurements include the extra work; sharing interpretation does not promise a net speedup.
Geometry does not establish semantic truth. A closer, aligned wrong value can defeat this model;
use application validation, explicit regions, and independent document-family evaluation.
Full coefficients, fixture hashes, and decisions are in ignored spatial-artifacts/placement-model.json.
All generated input PDFs are retained alongside that report.
Reproduce with `CUDA_VISIBLE_DEVICES='' uv run python -m bench.spatial`.
