# Frozen CPU structure geometry and source placement

All 144 source-owned outputs (nine predeclared treatments × 16 DEV pages) passed independent replay before references were loaded. The scorer authenticates the ordinal source baseline with its external trust map, matches the announced source/geometry hashes, replays raw structure queries into crop geometry, and reconstructs every placement and source-derived string. No archived Python is executed. Empty and negative pages remain in every treatment.

The complete denominator is 16 pages, 53 tables, and 2,333 anchor cells. Geometry is conditional on the original 20 ordinal detector crops; tables absent from those crops remain misses. No generated table fallback is credited.

| Structure threshold | Placement | Strict cells | Text cells | Structure cells | Complete tables | Missing / extra tables | Negative FP pages | Errors |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| .3 | overlap margin | 176 | 178 | 347 | 1 | 39 / 3 | 3 | 0 |
| .3 | maximum overlap | 191 | 193 | 347 | 3 | 39 / 3 | 3 | 0 |
| .3 | unique center | 191 | 193 | 347 | 3 | 39 / 3 | 3 | 0 |
| .5 | overlap margin | 189 | 191 | 352 | 1 | 39 / 3 | 3 | 0 |
| .5 | maximum overlap | 204 | 206 | 352 | 3 | 39 / 3 | 3 | 0 |
| .5 | unique center | 204 | 206 | 352 | 3 | 39 / 3 | 3 | 0 |
| .7 | overlap margin | 191 | 193 | 349 | 1 | 39 / 3 | 3 | 0 |
| .7 | maximum overlap | 202 | 204 | 349 | 3 | 39 / 3 | 3 | 0 |
| .7 | unique center | 202 | 204 | 349 | 3 | 39 / 3 | 3 | 0 |

For context, the original composed ordinal output scored 384 strict cells and three complete tables with zero negative FP pages. The structure controls introduce false tables on three of four negatives. These fixed observations support further acquisition/structure work; selecting the best threshold from this table would be DEV tuning and would require a separately frozen confirmation.

The retained geometry inference measured 9.04 seconds wall, 15.96 seconds CPU, and 677.53 MiB sampled peak RSS in one contended CPU process, sampled every 100 ms. Source placement across all nine treatments measured 3.59 seconds wall, 3.47 seconds CPU, and 95.23 MiB sampled peak RSS. Original OCR/detection/generation resources and historical API costs remain separate. No new API calls were made. These are conditional geometry/placement timings, without a full-pipeline pages/minute or pages/API-dollar claim.

There is one frozen geometry inference per crop, shared across thresholds, and one placement pass per treatment. No repeat variability or confidence interval is established.

`bench.p003_structure_evaluation` verifies and scores explicitly named geometry, placement, corpus, and baseline trust paths. Detailed per-page scores and resource records remain in the ignored placement artifact's `evaluation.json`.

Six additional source-only qualifier treatments were frozen separately and all 96 outputs replayed before scoring. They reuse the same raw geometry and crop inventory; these are alternatives, not repeated independent inferences.

| Structure threshold | Qualifier placement | Strict cells | Text cells | Structure cells | Complete tables | Missing / extra tables | Negative FP pages | Errors |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| .3 | height-adaptive | 191 | 193 | 347 | 3 | 39 / 3 | 3 | 0 |
| .3 | physical row consensus | 189 | 191 | 347 | 3 | 39 / 3 | 3 | 0 |
| .5 | height-adaptive | 204 | 206 | 352 | 3 | 39 / 3 | 3 | 0 |
| .5 | physical row consensus | 202 | 204 | 352 | 3 | 39 / 3 | 3 | 0 |
| .7 | height-adaptive | 202 | 204 | 349 | 3 | 39 / 3 | 3 | 0 |
| .7 | physical row consensus | 200 | 202 | 349 | 3 | 39 / 3 | 3 | 0 |

Height-adaptive placement matches the original maximum-overlap/center scores; row consensus loses two strict cells at each threshold. Neither fixes the three negative-page false positives. The complete source and explicit unresolved IDs remain conserved. Qualifier runtime was 3.15 seconds wall and 3.13 seconds CPU for all six treatments. The reported 526.52 MiB process-lifetime peak RSS includes earlier authentication/imports, excludes a dedicated sampling window, and cannot establish isolated qualifier memory use. Historical OCR/generation and original structure-inference costs remain separate.
