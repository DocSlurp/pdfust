# P003 explicit table geometry with CPU Table Transformer

Date: 2026-10-10 UTC. All source crops and model geometry were frozen before
reference access. This experiment used no credentials, GPU, hosted inference,
or protected inputs. No DEV reference was read or score computed by this
agent. Independent geometry evaluation is a separate treatment.

## Model and isolated environment

The public checkpoint is
`microsoft/table-transformer-structure-recognition-v1.1-all`, revision
`7587a7ef111d9dcbf8ac695f1376ab7014340a0c`. The repository advertises MIT
licensing and training on PubTables-1M plus FinTabNet.c. The downloaded
safetensors file is 115,437,156 bytes, SHA-256
`9df416575a3a36ebd0129342d4f597f14d6e5170268f3d52d28584ab4466a501`.
The config declares 125 queries, six foreground classes, an internal ResNet
backbone, and no timm backbone. No additional model weights were needed.
[Model card](https://huggingface.co/microsoft/table-transformer-structure-recognition-v1.1-all),
[pinned configuration](https://huggingface.co/microsoft/table-transformer-structure-recognition-v1.1-all/blob/7587a7ef111d9dcbf8ac695f1376ab7014340a0c/config.json).

The main development environment lacked model dependencies. An ignored,
isolated Python 3.12.15 environment was created using public prebuilt wheels:
PyTorch 2.9.1+cpu, torchvision 0.24.1+cpu, Transformers 4.57.6, Pillow 12.3.0,
and psutil 7.2.2. The complete dependency lock and public download provenance
are retained locally. There were no source builds or main-environment edits.
Model downloads total 115,515,347 bytes including the README/config files,
below the authorized 1 GB weight cap. Public downloads used unauthenticated
URLs; inference uses local files with implicit tokens and network access
disabled at the Hugging Face client level.

The checkpoint processor config contains only `longest_edge: 800`.
Transformers 4.57 rejected this before the first model forward, because its
DETR resize path requires both edge keys. The failed attempt is preserved as
`attempts/processor-contract-failure.json`, with zero completed crop
inferences and unmeasured resources. The successful pass explicitly sets
`shortest_edge: 800` and `longest_edge: 800`; this retains the longest-edge
budget. Both checkpoint and effective settings are archived. There was no
reference-based preprocessing selection. [Pinned processor config](https://huggingface.co/microsoft/table-transformer-structure-recognition-v1.1-all/blob/7587a7ef111d9dcbf8ac695f1376ab7014340a0c/preprocessor_config.json),
[DETR processor implementation](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/models/detr/image_processing_detr.py).

## Source-only crop freeze and inference

`p003_structure_geometry_prepare` authenticates the retained ordinal
`screen-ordinal-ocr300-512-r0` baseline using independently supplied
`trusted-code/b773d57.json`, including source PDF hashes and complete source
ownership replay. It selects **every** region whose source-plan kind is
`detector_proposal`, irrespective of original admission route or generated
output. Complete original source word IDs, literal strings, crop viewports,
source hashes, original/effective rotations, and baseline artifact hashes
remain local. Generated cell strings are not used for selection, geometry,
or image construction.

All 16 pages remain in the denominator: 14 have 20 detector proposals in
total, and two have none. Pages without crops are explicitly
`no_detector_proposal`, rather than failures or fabricated empty successes.
The page is rendered at the existing 4,096-edge cap in its authenticated
effective rotation. The existing continuous EXTENT crop primitive produces
RGB JPEG at edge 1,024 and quality 90. Crop bytes and source snapshots are
hashed before inference. This is conditional on the ordinal detector pool;
missed tables cannot be recovered by this experiment. The ordinal pool has
20 crops and differs from the earlier 19-crop vision control on one page,
so their aggregate scores would not form a matched model comparison.

`p003_structure_geometry.infer` loads only pinned local safetensors, forces
CPU, uses two intra-op threads and one inter-op thread, enables deterministic
algorithms, and performs one model forward per crop. The model input contains
pixels only. Original source strings and IDs are retained for later assembly,
but are never fed to this geometry model. All 125 raw logits, normalized
center/width/height boxes, complete seven-class softmax distributions,
processed input dimensions, and per-crop timing are archived.

Thresholds **0.3, 0.5, 0.7** were declared before inference. All three views
come from the same logits, without repeated model calls or reference-based
choice. Foreground scores are detector scores, not calibrated structure
correctness. Each normalized box maps through the exact continuous crop
viewport into global source coordinates. Out-of-viewport portions are
explicitly clipped and flagged; original projected boxes and raw queries
remain retained. Empty/outside objects are excluded with receipts.

## Bounded topology candidates

The pure helper also supplies a conservative experimental topology view.
It selects the highest-scoring table object, suppresses row/column duplicates
at axis-overlap/minimum-band-width 0.8, sorts band centers, and puts separators
at adjacent-center midpoints within the table bounds. This is our fixed
prototype policy, not the complete official Table Transformer postprocessor.
Raw row/column objects remain available for a later alternative boundary fit.

Spanning objects cover grid slots when intersection/cell-area is at least
0.5. Nonrectangular coverage or conflicting spans refuses the entire topology
candidate, retaining the conflict receipt. Uncovered slots receive atomic
anchors, including empty cells. Positive row/column counts and at most 4,096
slots are required; one-row/one-column shapes are permitted. Accepted anchor
boxes form a nonoverlapping rectangular tiling with valid global bounds.
Header objects are retained in raw detections but do not author semantic cell
roles. No source text assignment, table admission gate, or public extraction
behavior is changed.

| Threshold | Row objects | Column objects | Span objects | Valid geometry candidates | Span-conflict refusals | Retained merged anchors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.3 | 250 | 132 | 75 | 17/20 | 3 | 12 |
| 0.5 | 231 | 125 | 48 | 19/20 | 1 | 10 |
| 0.7 | 208 | 113 | 37 | 19/20 | 1 | 6 |

All thresholds retain 20 table objects. Accepted row counts range up to 62;
these are predictions, not measured correctness. Clipping affects 9, 8, and
5 retained objects respectively. Every saved threshold view and topology was
reconstructed exactly from its frozen raw queries. Neither a higher valid
candidate count nor fewer span conflicts establishes higher extraction
quality; unresolved/conflicting cases must remain in later evaluation.

## CPU resources and validation

Source authentication, rendering and crop preparation took 6.494 seconds
wall and 6.449 seconds self CPU, with Linux lifetime peak RSS 539,156 KiB.
The successful inference pass, measured after Python/model-library imports,
took 9.036 seconds wall and 15.960 seconds self CPU, averaging about 177% of
one CPU. Model loading took 0.211 seconds. Crop processing totals were 8.363
seconds wall and 15.108 seconds CPU. These measurements exclude downloads,
dependency installation, Python import time, and the initial incompatible
processor attempt; they are not complete setup-cost estimates.

Inference RSS was sampled every 100 ms for the one process: peak 710,438,912
bytes (about 678 MiB); `getrusage` lifetime peak was 723,168 KiB. Complete RSS,
CPU-time and native-thread samples are retained. Other root workers were
active, so wall times are contended and are not a serial throughput claim.
Local preprocessing and model inference are separate processes and resource
receipts; there were no remote inference costs.

Five synthetic CPU tests cover coordinate projection, clipping/query
identity, threshold views, complete anchor tiling, merged spans, overlap
refusal, duplicate suppression, missing structure, and invalid finite model
contracts. Ruff and strict mypy pass for both new modules. The retained crop
pass validates actual offline model loading and processing. Independent
scoring must authenticate the source baseline and helper separately, replay
raw-query projection/topology, preserve all 16 pages and refused candidates,
and distinguish geometry coverage from source-owned extraction quality.

Reproduction uses the isolated CPU interpreter for inference:

```sh
python -m bench.p003_structure_geometry_prepare \
  --baseline /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/screen-ordinal-ocr300-512-r0 \
  --trusted-code /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/b773d57.json \
  --output <artifact>/source
<cpu-env>/bin/python -m bench.p003_structure_geometry \
  --manifest <artifact>/source/manifest.json \
  --model-directory <artifact>/model --output <artifact>/geometry --threads 2
```

Ignored artifacts are under `pipeline-p003/structure-geometry-v1/`. Exact
source/geometry manifests, helper code, public model provenance, JPEG crops,
complete raw outputs, locks, resource samples and failed-attempt receipt are
retained. The isolated environment itself is only in the experiment
worktree. No model or raw development artifact is committed or uploaded.
