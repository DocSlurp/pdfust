# Source-only synthetic relationship geometry controls

Four fixed treatments were frozen for all 24 independently authenticated synthetic-v2 cases before external scoring: bbox physical-row proxy, direct-vector rules, crop raster128, and crop raster512. No generator module, authored configuration, labels, counterfactual grouping, or reference outputs participate in the classifier. Archived generator bytes are hashed for authority and never imported or decoded as code. Only each selected source record's extracted word boxes, requested relationship kind, source pair IDs, drawings, and authenticated crop pixels are used. Literal strings and case IDs do not affect choices.

The native output contract is `same`, `separate`, or `unresolved`. Complete minimal rule enclosures establish shared cell membership or distinct cell membership. Shared top/bottom boundaries establish a row band; disjoint bands or a horizontal separator establish separation. A complete axis separator spanning both word boxes can establish separate cells or prevent a same-cell wrap continuation. Shared enclosure does not establish logical continuation, so positive wrap decisions abstain. The separate bbox treatment uses physical vertical overlap as a row proxy and explicitly risks treating wrapped logical rows as different rows. It provides no cell or wrap prediction.

Raster treatments independently extract dark long thin runs, using threshold96, minimum12px and10% of the relevant image dimension, aspect>=12. No vector rules are injected into their evidence. All thresholds, search caps, and treatments are fixed globally. Each receipt retains every admitted segment, source pair boxes, enclosure candidates, separator booleans, choice reason, and proxy declaration. Complete evidence exceeding256segments or4096 rectangle candidates refuses; no partial search result is accepted. Nonfinite/inverted boxes and missing source evidence remain explicit refusals. No probability or calibration claim is made.

| Treatment | Classified | Abstained | Same | Separate |
|---|---:|---:|---:|---:|
| Bbox physical-row proxy | 8 | 16 | 4 | 4 |
| Direct vector | 15 | 9 | 7 | 8 |
| Crop raster128 | 7 | 17 | 0 | 7 |
| Crop raster512 | 8 | 16 | 0 | 8 |

These are protocol coverage counts, not accuracy. No source assignments or table outputs are applied. Raster positives are absent under this conservative complete-enclosure rule; anti-aliasing and short or fragmented dividers can remove necessary enclosure evidence. Axis rules can also be decoration, so these qualifiers are hypotheses for independent scoring rather than a general PDF truth oracle. Wrap semantics can remain underdetermined even with complete source geometry.

The final ignored artifact is `bench/results/pdf-master-artifacts/p003-synthetic-geometry-v2` in the isolated synthetic-geometry worktree. It contains frozen code, copied label-free source projections,96 receipts, a result digest, external trust/source identities, and a report. Input source pool and external map are the root's explicit `pipeline-p003/synthetic-micro-relations-v2` and `trusted-code/synthetic-micro-relations-v2.json`; the authenticated source frozen SHA is `fe51369b77b2f6d45c80713c9ebc8cb71b79659b37db6ae5e94c2e5418cba84e`.

Resource measurement: one CPU process, no provider calls, no GPU, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=2`, machine8logical CPUs. Authentication, extraction of pixel runs, classification, and artifact freezing took0.771s wall and0.756s CPU. psutil sampled process RSS at100ms, peak44.1MB. Reported resource lifetime high-water RSS539156KiB is retained separately and does not agree with sampled interval RSS; it must not be treated as an incremental peak. Imports precede the measured interval. No full-pipeline throughput or page-quality rate is claimed.

Six local tests cover closed and missing enclosures, separating rules, logical/physical row differences, absent wrap proof, identity/text invariance and source immutability, raster rectangle/blob discrimination, geometry/cap refusals, external digest failures, complete24-case freezing, and a deliberately non-executable archived generator fixture. Ruff passes.
