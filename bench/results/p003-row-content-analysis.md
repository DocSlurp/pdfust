# Historical R001 conditional body content audit

All 80 retained parser-v2 outputs replayed successfully before historical targets were interpreted. Every original fragment assignment and record score reproduced exactly. This adds eight conditional row-assembly treatments to the 32 generation and 64 incremental audits; these are different scopes, not 104 complete extraction pipelines.

Each treatment contains ten correlated authored cases: nine with known body assembly and one author-unresolved case. Content precision/recall and completeness below use the nine known bodies; the unresolved case remains in coverage and abstention reporting. Predictions contain two source-owned fields (`row_key` and `value`), preserve literal source IDs exactly once, and exclude fixed headers. Schema acceptance and full-page extraction are unmeasured.

| Model | Evidence | Cases known / unresolved | Fragment accuracy | Original record F1 | Strict complete bodies / known | Content-recovered bodies / known | Content P / R (%) | Matched / missing / extra units | Unresolved abstentions / cases |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions | geometry | 9 / 1 | 0.733 | 0.400 | 4 / 9 | 4 / 9 | 77.31 / 77.31 | 276 / 81 / 81 | 0 / 1 |
| openai/gpt-6-luna-decisions | image1200 | 9 / 1 | 0.833 | 0.700 | 7 / 9 | 7 / 9 | 88.80 / 88.80 | 317 / 40 / 40 | 0 / 1 |
| openai/gpt-6-luna-decisions | image128 | 9 / 1 | 0.700 | 0.300 | 3 / 9 | 3 / 9 | 67.97 / 67.97 | 244 / 115 / 115 | 0 / 1 |
| openai/gpt-6-luna-decisions | image512 | 9 / 1 | 0.800 | 0.600 | 6 / 9 | 6 / 9 | 83.47 / 83.47 | 298 / 59 / 59 | 0 / 1 |
| perplexity/pplx-decider-v1.1-27b | geometry | 9 / 1 | 0.733 | 0.400 | 4 / 9 | 4 / 9 | 74.59 / 75.00 | 270 / 90 / 92 | 0 / 1 |
| perplexity/pplx-decider-v1.1-27b | image1200 | 9 / 1 | 0.800 | 0.600 | 6 / 9 | 6 / 9 | 84.36 / 84.36 | 302 / 56 / 56 | 0 / 1 |
| perplexity/pplx-decider-v1.1-27b | image128 | 9 / 1 | 0.733 | 0.400 | 4 / 9 | 4 / 9 | 73.61 / 73.82 | 265 / 94 / 95 | 0 / 1 |
| perplexity/pplx-decider-v1.1-27b | image512 | 9 / 1 | 0.700 | 0.300 | 3 / 9 | 3 / 9 | 68.33 / 68.52 | 246 / 113 / 114 | 0 / 1 |

Luna’s retained 1200-pixel treatment recovers seven of nine known bodies with 88.80% content precision and recall, versus four bodies and 77.31% for geometry. PPLX recovers six bodies at 1200 pixels versus four for geometry, while its 512-pixel treatment recovers three. This small correlated pilot does not establish monotonic resolution gains or a general model ranking. All eight treatments select a decisive assembly on the author-unresolved case, so improved known-case recovery does not resolve abstention behavior.

Tolerant content alignment awards partial credit for retained literal text, but adds no fully recovered body beyond strict body completeness in this corpus. A wrong join/split changes row organization even when all source fragments survive. Numeric boundaries remain intact; content counts can differ slightly between joined and split interpretations because declared joining separators are counted explicitly. Content recovery never certifies correct headers, columns, spans or complete page assembly.

A useful future test would pair identical visible fragments with independently varied observable continuation cues and an explicit insufficient-evidence subset, retain all cases, and compare both correct assembly and abstention. It should validate the native image contract first and use a new source-frozen corpus rather than tune on these ten historical templates.

## Authentication and limitations

- Completed source: `decisions/row-decisions-r001-parser-v2`; the initial `row-decisions-r001` directory stopped after two parser failures and is not the completed corpus.
- The historical six-file archive is independently Git-authenticated against `c83de37`. Current projection and evaluation helpers have separate root-approved six/seven-file authorities.
- Preparation reconstructs all 80 source packets, actual request bodies, PNG dimensions/bytes, exact encoded image payloads, raw response identities, finite catalog aliases, source assignments and body matrices. All retained input/output hashes are checked again before target interpretation.
- Some parser-v2 receipts reuse responses from the initial directory. The original two failures remain unchanged; local replay is not another provider call. Probabilities, rankings, raw responses and original charges remain immutable.
- Original generated PDFs were not retained in this corpus. Exact retained request/image evidence is authenticated, but PDF re-rendering and historical provider image consumption are not validated. The old page-scope image contract is not retroactively endorsed.
- Ten correlated templates do not establish natural-document quality. Fixed headers receive no new model credit. Author-unresolved cases are unscorable for body content rather than empty-table gold. There is no fresh inference throughput or savings claim.

## Frozen receipts

- Preparation SHA256: `beb2ac6553bf782e5b75da99fcdefcffc33b81fb33a824e07bace6f247907d52`.
- Source/output inventory SHA256: `cbd3495aab39ade0b395b604b8f09f737a0f9548e71118c2e13a6f9ba6882e31`.
- Historical authority SHA256: `99cf9cbe2a3b83435ccbedae841a985e14265622eeef8a723ba872300dbeb7e3`.
- Evaluator authority SHA256: `b5ec1327264301454844ba40707c365da0ceff2b2fa57de3471479e726097430`.
- Output: `pipeline-p003/r001-content-eval-v1/report.json`, SHA256 `8dcafd54b62213ae16959a7352a7bbf0fd9549e813b483097ee583b7335b5042`.
- Metric versions: `p003-r001-body-evaluation-v1`, projection `p003-r001-body-content-v1`, and `p003-content-alignment-v2`.

The source replay and scoring interval measured 0.4328 seconds wall, 0.4280 CPU seconds and 46,067,712 bytes peak sampled RSS. Measurement uses current-process `process_time` and psutil RSS sampled every 100 ms, one process and no subprocesses; OMP/OpenBLAS/MKL each use one thread. No GPU, hosted calls or credentials were used.
