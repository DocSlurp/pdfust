# CPU SLANet-plus resolution and source-crop sweep

All 28 reviewed DEV pages stay in each configuration denominator. Ambiguous cases are unscored. Source-only native geometry selected crops before any reference read. Source crop,+4pt,+12pt are explicitly frozen alternatives; no gold crop or OCR input is supplied.

| DPI/route | Borderless exact | Prose false table | Native controls exact | Ambiguous unscored | Errors/refusals |
|---|---:|---:|---:|---:|---:|
| 72/page | 0/16 | 8/8 | 0/0 | 4 | 0 |
| 72/crop | 0/16 | 8/8 | 0/0 | 4 | 0 |
| 72/crop-pad4 | 3/16 | 8/8 | 0/0 | 4 | 0 |
| 72/crop-pad12 | 7/16 | 8/8 | 0/0 | 4 | 0 |
| 120/page | 0/16 | 8/8 | 0/0 | 4 | 0 |
| 120/crop | 0/16 | 8/8 | 0/0 | 4 | 0 |
| 120/crop-pad4 | 1/16 | 8/8 | 0/0 | 4 | 0 |
| 120/crop-pad12 | 5/16 | 8/8 | 0/0 | 4 | 0 |
| 180/page | 0/16 | 8/8 | 0/0 | 4 | 0 |
| 180/crop | 1/16 | 8/8 | 0/0 | 4 | 0 |
| 180/crop-pad4 | 1/16 | 8/8 | 0/0 | 4 | 0 |
| 180/crop-pad12 | 5/16 | 8/8 | 0/0 | 4 | 0 |

| DPI/route | Exact cell matrices | Exact spans | Intended values owned | Intended words owned | Source IDs conserved |
|---|---:|---:|---:|---:|---:|
| 72/page | 0/16 | 0/16 | 0/245 | 0/294 | 28/28 |
| 72/crop | 0/16 | 1/16 | 5/245 | 11/294 | 28/28 |
| 72/crop-pad4 | 3/16 | 5/16 | 76/245 | 94/294 | 28/28 |
| 72/crop-pad12 | 7/16 | 9/16 | 149/245 | 185/294 | 28/28 |
| 120/page | 0/16 | 0/16 | 0/245 | 0/294 | 28/28 |
| 120/crop | 0/16 | 0/16 | 0/245 | 0/294 | 28/28 |
| 120/crop-pad4 | 1/16 | 1/16 | 16/245 | 16/294 | 28/28 |
| 120/crop-pad12 | 5/16 | 8/16 | 126/245 | 154/294 | 28/28 |
| 180/page | 0/16 | 0/16 | 0/245 | 0/294 | 28/28 |
| 180/crop | 1/16 | 1/16 | 16/245 | 16/294 | 28/28 |
| 180/crop-pad4 | 1/16 | 1/16 | 16/245 | 16/294 | 28/28 |
| 180/crop-pad12 | 5/16 | 7/16 | 118/245 | 144/294 | 28/28 |

| DPI/route | Model wall/CPU s | Matching wall/CPU s | Route wall/CPU s |
|---|---:|---:|---:|
| 72/page | 2.381/4.580 | 3.633/4.619 | 6.347/9.617 |
| 72/crop | 1.459/2.829 | 2.367/2.763 | 3.977/5.798 |
| 72/crop-pad4 | 1.125/2.168 | 0.272/0.540 | 1.502/2.869 |
| 72/crop-pad12 | 1.093/2.116 | 0.281/0.557 | 1.483/2.846 |
| 120/page | 2.389/4.596 | 3.398/4.339 | 6.299/9.518 |
| 120/crop | 1.165/2.246 | 0.502/0.844 | 1.845/3.323 |
| 120/crop-pad4 | 1.262/2.446 | 0.500/0.899 | 1.947/3.605 |
| 120/crop-pad12 | 1.135/2.168 | 0.286/0.561 | 1.607/2.982 |
| 180/page | 2.267/4.416 | 1.564/2.461 | 4.689/7.810 |
| 180/crop | 1.097/2.116 | 0.297/0.567 | 1.664/3.011 |
| 180/crop-pad4 | 1.210/2.340 | 0.445/0.818 | 1.964/3.556 |
| 180/crop-pad12 | 1.075/2.078 | 0.650/0.974 | 2.021/3.425 |

Native load/text preparation: 0.795s wall/0.802s CPU. Rendering (84 distinct page/DPI rasters, each shared by four routes): 3.918s wall/4.195s CPU. Source proposal and preparation resources remain in source-frozen.json. Stage-summed CPU is measured process CPU, not a complete worker total; imports and global output serialization excluded. Worker RSS is sampled separately from the preparation parent.

Background: the root image sweep was network-bound and another agent could render 16 training derivatives concurrently. Timings describe this run, not a throughput ceiling. No repeats were run.

Model initialization/provenance: `{"model_sha256": "d57a942af6a2f57d6a4a0372573c696a2379bf5857c45e2ac69993f3b334514b", "providers": ["CPUExecutionProvider"], "initialization_cpu_seconds": 0.26045148299999993, "initialization_wall_seconds": 0.20924890298920218, "actual_intra_threads": 2, "actual_inter_threads": 1, "versions": {"rapid-table": "3.0.2", "onnxruntime": "1.30.0", "numpy": "2.5.3", "opencv-python": "5.0.0.93"}, "fixed_preprocess_max_side": 488}`.

Worker resources: `{"returncode": 0, "error": null, "wall_seconds": 62.75613953600987, "sampled_worker_peak_rss_bytes": 300834816, "measurement": "parent /proc child VmRSS every0.1s; single worker; no GPU; hard ten-minute cap"}`.

Routes retain HTML structure, cell boxes, row-major matrices/spans, exact source text/IDs, model/matching CPU and wall timings, render/native timings and RSS. Exact cells/spans and intended-word slot ownership are postfreeze scores in private-scores.json; raw string retention is not quality. Cell center ownership conserves IDs with ambiguous hits unresolved. It is separate from matcher text alignment and independently annotated source-ID gold. Missing HTML spans are unscored, not inferred. Empty source proposals perform zero model calls and remain full-denominator outcomes.

SLANet-plus fixes the longest side at 488 before a 488×488 tensor. The DPI sweep tests raster sampling/crop context, not larger model tensors. No input-size override was attempted. CPU-only cached pinned weights, two intra-op and one inter-op threads, no network access. Provider cost $0.

Artifacts: `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/specialist-resolution-v1/124953db381d4aa6`. Source hash `40131429205d35247660af0199fabfd0681b958da184f5916dd18ab7ce25cca5`. Raw outputs stay ignored.
