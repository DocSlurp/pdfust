# P003 DEV acquisition and transcription attribution

The matched natural16 crop runs lose most strict anchors on the two dense pages before transcription has a sufficiently covering crop. YOLO and the source-only fixed-grid proposals expose complementary opportunities; their raw union warrants acquisition experiments with explicit overlap and admission controls. These observations do not establish an achievable fusion score.

## Scope and method

All 16 intended DEV pages remain in the denominator: 53 tables and 2,333 anchor cells. The two predeclared dense pages contain 39 tables and 1,972 anchors; the other 14 contain 14 tables and 361 anchors, including four negative pages. Luna, Haiku, and the historical P002 Sonnet1024 runs have identical source records and retained YOLO crop inventory. Source archives and output replay were independently authenticated using root-supplied trusted digest maps. Historical Sonnet parser compatibility is separately reviewed; archived code is never executed.

The source-only proposal pass uses the authenticated ordinal baseline native words/page geometry, a 1536-edge PDF raster, and candidate cap **32**. It freezes tracks_whole and tracks_fixed2 proposals and the retained YOLO inventory before this analysis loads DEV references. No reference text or geometry enters proposal construction. Thresholds are declared as IoU 0.25/0.50/0.75 and target-area inclusion 0.90/0.95/1.00; no best threshold is selected. Inclusion is the fraction of a gold table visible in one crop. IoU also penalizes excess crop area.

Strict missed anchors are assigned by priority: whole-page rollback; no proposal reaching 95% target inclusion; no requested proposal reaching that inclusion; otherwise crop transcription/structure failure. Exact recovered anchors are excluded before attribution. This is a geometric diagnostic: partial crops can recover anchors, and a covering crop can still omit tables. It cannot prove a counterfactual strict-cell ceiling.

## Matched retained quality and miss partition

| Model | Group | Strict / expected | Complete / tables | Proposal miss | Admission miss | Crop transcription/structure miss | Rollback miss |
|---|---|---:|---:|---:|---:|---:|---:|
| Luna | all16 | 784/2333 | 3/53 | 1043 | 0 | 506 | 0 |
| Luna | dense2 | 494/1972 | 0/39 | 1036 | 0 | 442 | 0 |
| Luna | other14 | 290/361 | 3/14 | 7 | 0 | 64 | 0 |
| Haiku | all16 | 393/2333 | 3/53 | 1043 | 0 | 875 | 22 |
| Haiku | dense2 | 117/1972 | 0/39 | 1036 | 0 | 819 | 0 |
| Haiku | other14 | 276/361 | 3/14 | 7 | 0 | 56 | 22 |
| Sonnet1024 | all16 | 982/2333 | 5/53 | 1043 | 0 | 308 | 0 |
| Sonnet1024 | dense2 | 692/1972 | 1/39 | 1036 | 0 | 244 | 0 |
| Sonnet1024 | other14 | 290/361 | 4/14 | 7 | 0 | 64 | 0 |

For Luna, 1,043 of 1,549 missed anchors fall in the proposal category (67.3%); 1,036 are on the dense pages. Sonnet reduces crop transcription/structure misses from 506 to 308 with the same proposal inventory, while 1,043 proposal misses persist. Haiku has one malformed-page rollback costing 22 anchors on the other14 group; its retained error is “Table bounds are outside normalized image coordinates.” All other pages complete operationally.

| Model | Text anchors | Structure anchors | Missing tables | Extra tables | Negative FP pages / 4 | Errors / 16 | Exact positive pages | Pages/min | Pages/API USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Luna | 795 | 1045 | 30 | 5 | 0/4 | 0/16 | 2 | 4.188 | 1234.108 |
| Haiku | 406 | 491 | 37 | 1 | 1/4 | 1/16 | 2 | 8.491 | 1822.069 |
| Sonnet1024 | 982 | 1287 | 26 | 0 | 0/4 | 0/16 | 3 | 6.878 | 69.412 |

Rates describe the original complete pipelines, not this offline analysis. Luna uses the verified BYOK reconciliation, USD 0.012964825; the original report accounted USD 1.5105027 including unresolved reservations. Haiku costs USD 0.0082324 and Sonnet USD 0.230508. Different provider/model runs are not matched timing repeats. See [evaluation contract](p003-eval-design.md) for repeat and uncertainty requirements.

## Geometric sensitivity

Each entry is **covered tables / anchors belonging to those tables**. These anchor counts describe inventory opportunities, not attainable strict scores. YOLO+fixed2 is a raw candidate union: overlapping crops remain, partial crops are not joined, candidate admission is not simulated, and no nonoverlap composition constraint is applied.

| Group | Inventory | IoU ≥.25 | IoU ≥.50 | IoU ≥.75 | Inclusion ≥.90 | Inclusion ≥.95 | Inclusion 1.00 |
|---|---|---:|---:|---:|---:|---:|---:|
| all16 | yolo | 16/741 | 14/361 | 14/361 | 27/1297 | 26/1279 | 14/944 |
| all16 | tracks_whole | 12/427 | 10/273 | 10/273 | 30/1051 | 28/1024 | 20/831 |
| all16 | tracks_fixed2 | 21/945 | 16/548 | 13/420 | 32/1174 | 30/1147 | 21/891 |
| all16 | yolo_union_fixed2 | 25/1259 | 20/636 | 17/508 | 41/1833 | 39/1806 | 27/1480 |
| dense2 | yolo | 2/380 | 0/0 | 0/0 | 13/936 | 13/936 | 13/936 |
| dense2 | tracks_whole | 1/136 | 0/0 | 0/0 | 20/778 | 18/751 | 18/751 |
| dense2 | tracks_fixed2 | 10/654 | 6/275 | 3/147 | 22/901 | 20/874 | 19/811 |
| dense2 | yolo_union_fixed2 | 11/898 | 6/275 | 3/147 | 27/1472 | 26/1463 | 25/1400 |
| other14 | yolo | 14/361 | 14/361 | 14/361 | 14/361 | 13/343 | 1/8 |
| other14 | tracks_whole | 11/291 | 10/273 | 10/273 | 10/273 | 10/273 | 2/80 |
| other14 | tracks_fixed2 | 11/291 | 10/273 | 10/273 | 10/273 | 10/273 | 2/80 |
| other14 | yolo_union_fixed2 | 14/361 | 14/361 | 14/361 | 14/361 | 13/343 | 2/80 |

At 95% inclusion, the union adds 13 tables and 527 associated anchors over YOLO, including 13 dense-page tables and 527 dense anchors. It covers 39/53 tables and 1,806 associated anchors in total. At IoU 0.50 it exposes 20 tables and 636 anchors; the dense contribution is only six tables and 275 anchors. The gap between inclusion and IoU warns that broad crops supply pixels without reliably localizing individual tables. The other14 union matches YOLO at every threshold.

## Reproducibility and resources

Two independent source-only construction passes produced byte-equivalent page plans. The measured pass took 8.234 seconds wall and 8.498 seconds process CPU, with 311,100 KiB lifetime process peak RSS from getrusage. Scope includes source authentication, retained-output replay, PDF rendering, and proposal generation; one CPU process, no OCR, network inference, or GPU. This is an offline analysis cost, not pipeline throughput. No retained worker PID is used to signal or manage processes.

The CLI is `python -m bench.p003_failure_analysis --source <ordinal-run> --baseline <Luna> --baseline <Haiku> --baseline <Sonnet> --trusted-code <source-map> --trusted-code <Luna-map> --trusted-code <Haiku-map> --trusted-code <Sonnet-map> --corpus <natural16> --freeze <new-file> --output <new-file>`. Existing freezes are never overwritten. The pure `analyze(frozen_path, corpus)` seam scores an existing immutable freeze. Six focused tests cover geometry, raw union semantics, and miss accounting.

Detailed evidence remains ignored under `pipeline-p003/coverage-analysis/`. Frozen measured proposal SHA256: `1f93d37b2cc4b44510b3ad651397bb1d877931f51c32722a97f4cf7d0e48347e`. Source proposal helper SHA256: `450ecb92f5fd3d9a68e571159037f2f0df574770695d4595988ff74448b94d44`.
