# SLANet-plus CPU specialist pilot

Private local research; optional isolated environment only.

Run: `CUDA_VISIBLE_DEVICES='' PYTHONPATH=src:. /home/dan/.cache/pdf-master-cpu/bin/python -m bench.specialist_cpu --dpi 120`.

Versions: {'rapid-table': '3.0.2', 'onnxruntime': '1.30.0', 'numpy': '2.5.3', 'opencv-python': '5.0.0.93'}; Python 3.14.7. Actual providers: ['CPUExecutionProvider']; actual intra/inter threads: 2/1. Warm-cache initialization: 136.3 ms; complete pilot wall time: 16.6 s.

Eight first-page inputs: four independently declared table matrices, two no-table prose controls, and two prepared Senate/NICS corpus pages with partial record checks. One model call per admitted region; no repetitions or tuning. Failures remain in denominators. Full-page and cropped routes use identical native words and share page preparation. No OCR model is loaded. Geometry proposals contain no reference-answer boxes.

An initial harness run discarded transparent alpha, producing entirely black inputs. That run is archived as invalid under `specialist-invalid-alpha-v1/` and contributes no model quality evidence. This run renders explicitly on white and refuses nonopaque/blank rasters; representative saved table and prose images were visually inspected.

| Input | Route | Regions | Cells correct/expected | Exact | Record checks | Source matched/expected | Render ms | Native ms | Infer ms | Match ms | Total ms | Error |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| text-structure-and-literals | full | 1 | 0/0 | False | 0/0 | 47/47 | 30.5 | 1.1 | 62.1 | 15.0 | 142.2 | - |
| text-structure-and-literals | cropped | 0 | 0/0 | True | 0/0 | 47/47 | 30.5 | 1.1 | 0.0 | 0.0 | 32.7 | - |
| two-column-order | full | 1 | 0/0 | False | 0/0 | 115/115 | 44.3 | 2.9 | 74.8 | 119.5 | 259.4 | - |
| two-column-order | cropped | 1 | 0/0 | False | 0/0 | 115/115 | 44.3 | 2.9 | 41.5 | 21.2 | 117.9 | - |
| table-bordered | full | 1 | 0/9 | False | 0/0 | 14/14 | 32.3 | 0.3 | 47.3 | 1.7 | 93.3 | - |
| table-bordered | cropped | 1 | 9/9 | True | 0/0 | 14/14 | 32.3 | 0.3 | 46.2 | 0.9 | 83.5 | - |
| table-borderless | full | 1 | 0/9 | False | 0/0 | 14/14 | 44.0 | 0.4 | 109.5 | 11.2 | 181.5 | - |
| table-borderless | cropped | 1 | 9/9 | True | 0/0 | 14/14 | 44.0 | 0.4 | 52.3 | 1.3 | 102.3 | - |
| table-merged | full | 1 | 0/9 | False | 0/0 | 14/14 | 39.0 | 0.3 | 59.5 | 1.3 | 111.9 | - |
| table-merged | cropped | 1 | 9/9 | True | 0/0 | 14/14 | 39.0 | 0.3 | 36.8 | 0.8 | 80.5 | - |
| table-borderless-aligned | full | 1 | 0/8 | False | 0/0 | 10/10 | 29.4 | 0.2 | 78.3 | 10.3 | 130.5 | - |
| table-borderless-aligned | cropped | 1 | 8/8 | True | 0/0 | 10/10 | 29.4 | 0.2 | 37.6 | 0.8 | 70.3 | - |
| corpus-senate-expenditures | full | 1 | 0/0 | - | 7/23 | 962/966 | 85.3 | 7.9 | 118.2 | 2328.3 | 2563.1 | - |
| corpus-senate-expenditures | cropped | 1 | 0/0 | - | 17/23 | 894/966 | 85.3 | 7.9 | 110.1 | 1573.2 | 1799.1 | - |
| corpus-nics-background-checks-2015-11 | full | 1 | 0/0 | - | 0/12 | 1437/1533 | 88.8 | 9.3 | 120.3 | 4412.9 | 4666.3 | - |
| corpus-nics-background-checks-2015-11 | cropped | 1 | 0/0 | - | 0/12 | 1504/1533 | 88.8 | 9.3 | 111.5 | 5682.6 | 5947.0 | - |

Observed quality: full: cells 0/35; exact matrices 0/4; prose false positives 2/2; corpus partial records 7/35. cropped: cells 35/35; exact matrices 4/4; prose false positives 1/2; corpus partial records 17/35.


Cell scores require the declared row/column position, including merged-slot expansion. Corpus checks are partial spot checks, not full table accuracy. Source agreement counts exact tokens, not placement correctness. Complete source prose outside cropped regions is retained; unmatched words inside model regions may disappear and are scored as losses.

SLANet is a table structure recognizer, not a page-level table detector. Full-page prose false positives are therefore an intentional control. Cropped proposals merge intersecting native-grid/geometry boxes with 12-point margins; no proposal means no model call. A model failure returns no tables and retains source prose, with the failure reported.

Stage definitions: native includes word extraction; render includes full-page raster and BGR conversion; infer includes SLANet preprocess/ONNX/postprocess; matching joins native text to predicted cells. Total charges load/native/render to each route, plus crop proposals for cropped routes and route elapsed time (including artifact writes). Shared preparation is performed once. Initialization and model download are separate. This pilot does not establish speed superiority over geometry: raster/model costs and output scope differ.

Native extension SHA256: `82be43976ae5c0930c699288c6fbcc5594ee616997475e76c63029f1fbf37226`. Native/source/script hashes are retained in the ignored manifest; all cases used one rebuilt extension. The first separate download plus session initialization took 2.77 s; the reported pilot initialization reused the verified model cache and excludes optional-runtime imports.

Model: https://www.modelscope.cn/models/RapidAI/RapidTable/resolve/v2.0.0/slanet-plus.onnx; SHA256 `d57a942af6a2f57d6a4a0372573c696a2379bf5857c45e2ac69993f3b334514b`; 7,758,305 bytes. RapidTable package code declares Apache-2.0; [the upstream PaddlePaddle SLANet-plus card](https://huggingface.co/PaddlePaddle/SLANet_plus/raw/main/README.md) declares Apache-2.0. The RapidAI conversion's package manifest pins this ONNX checksum; the ModelScope page did not expose a separately readable converted-weight license through the research browser. Record this provenance limitation before redistribution. Weights stay only in the isolated environment and are not copied into repository artifacts.

[RapidTable source](https://github.com/RapidAI/RapidTable) and [upstream table module](https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/module_usage/table_structure_recognition.html) describe the specialist pipeline. Full PDF inputs, raster crops, predictions, HTML, source IDs, hashes, versions, and errors remain ignored under `bench/results/pdf-master-artifacts/specialist/`.

Matching dominates the large corpus pages in this pilot: the upstream matcher loops over every source box and every predicted cell. Measure a bounded spatial/indexed association route before spending effort accelerating the ONNX model.

Next: broader independent table ground truth, bounded cell-box/source-ID admission, unmatched-word retention, proposal confidence and prose rejection, then repeated timing against equivalent outputs. A positive-only mean would conceal the prose and corpus failures.
