# P003 source-only TATR acquisition coverage alternatives

Date: 2026-10-10 UTC. These arms were selected and cropped using source
geometry only, before structure inference and before any reference or score
access. No protected input, credential, GPU, hosted API or new download was
used. The original 20 detector crops and nine placement arms are unchanged.

## Frozen acquisition arms

The source is the independently authenticated original ordinal DEV16
baseline. The original 20 detector crops own 2,205 of 10,778 retained source
words. Three alternatives were fixed to test acquisition coverage rather
than tune assignment against known reference boxes:

| Arm | Intended pages | Crops | Exact owned source words | Scope |
| --- | ---: | ---: | ---: | --- |
| Full page | 16 | 16 | 10,778 | One whole-page crop per page, including negatives |
| Residual | 16 | 32 | 8,573 | Every original source-owned residual region |
| Residual line/gap density | 16 | 17 | 2,948 | At most eight disjoint source-only proposals per page |

Ownership counts describe admitted source IDs, not words correctly placed
in tables. The full-page arm may shrink dense text below useful resolution.
The structure checkpoint is a table-crop model; a whole page can contain
multiple tables or prose that this acquisition does not separately localize.
Its geometry candidate view still selects one highest-scoring table object
per crop, and all raw detections remain available. A larger owned inventory
or more finite geometry candidates cannot establish extraction quality.

The residual arm takes each existing residual bbox and pads by
`min(12 points, 1.5 * median positive source-word-box height)`, clipping to
page bounds. It retains **only** that original region's literal source IDs.
The 1,050 additional word appearances in padded pixels are explicitly
context-only and do not receive ownership. Multiple crop pixels and predicted
table boxes may overlap; those overlaps are retained, not silently merged.
The downstream source-owned placer must refuse conflicting table boxes.

All source pages retain source snapshots, original/effective rotation,
source PDF and baseline-output hashes, exact crop viewport, JPEG bytes/hash,
and ownership/context receipts. Source rasterization uses the existing
4,096-edge display render and continuous EXTENT RGB JPEG crop at edge 1,024,
quality 90. A full-page crop contains all retained IDs even when none belong
to a table; no ground-truth routing is applied.

## Bounded residual line/gap proposal arm

The density arm reuses the existing source-only `_ocr_regions` mechanism on
**residual words only**. Physical bands need at least two separated word
segments and a consecutive track of at least three bands. Neighbors require
two monotonically matched segment edges within measured word-height scale,
consistent horizontal extent and bounded vertical separation. Complete tracks
and fixed 4/8/16/32-row windows supply raw alternatives.

All 101 raw proposals are retained. Fixed ordering uses source-only track
priority, physical-row count and owned-word count descending, followed by
geometry/proposal-ID ties. A word is eligible for a candidate only when its
center lies in that bbox and its ID is in the original residual inventory.
The first at most eight accepted candidates per page must have disjoint bboxes
and IDs. Seventy-five proposals are rejected with explicit overlap receipts;
nine more are rejected by the page cap. No proposals are merged or silently
lost. Negative/ambiguous aligned prose, lists or charts can pass this geometry
filter: it is a crop hypothesis, with no semantic table gate.

The accepted per-page crop counts are
`2,0,0,0,0,0,0,0,0,3,0,8,0,0,4,0`. Twelve intended pages have no density
proposal and remain explicitly `no_owned_crop`; they are not omitted from the
denominator or turned into invented empty successes. Uncovered residual IDs
remain archived. This policy deliberately misses single-segment and poorly
aligned regions; no threshold is relaxed to fill a desired page or coverage.

## Pinned CPU inference

All 65 crops completed one forward each using the previously retained
`microsoft/table-transformer-structure-recognition-v1.1-all` safetensors,
revision `7587a7ef111d9dcbf8ac695f1376ab7014340a0c`. Existing CPU environment,
model provenance, local safetensors and explicit processor compatibility
setting are reused; weights are neither downloaded nor duplicated. Two
intra-op threads, one inter-op thread, deterministic algorithms and the
CPU-only PyTorch build remain fixed. No source strings enter model inputs.

Thresholds 0.3/0.5/0.7 reuse the exact same 125 raw queries per crop. Every
crop's complete logits, seven-class probabilities and global geometry views
are retained. The original inference helper/report is preserved byte-for-byte;
new frozen wrappers add accurate acquisition scope, intended page/crop counts
and wrapper hash. The older helper's historical detector-only scope string
remains visible only in `inference-report-original.json`, whose SHA is recorded
by the corrected report. Projection/topology code and its hash are unchanged.

| Arm | Geometry candidates at 0.3 / 0.5 / 0.7 | Span refusals | Shape refusals |
| --- | ---: | ---: | ---: |
| Full page | 9 / 13 / 14 | 7 / 3 / 2 | 0 / 0 / 0 |
| Residual | 28 / 28 / 24 | 4 / 2 / 2 | 0 / 2 / 6 |
| Density | 15 / 16 / 14 | 2 / 0 / 0 | 0 / 1 / 3 |

These are syntax/geometry-admission observations, not table labels, recall or
quality scores. Candidate overlaps must still be checked during assembly.
No arm, threshold or page treatment was chosen using these counts.

## Artifacts and independent scoring seam

Ignored main-root directories are:

- `pipeline-p003/structure-acquisition-v1/fullpage/`;
- `pipeline-p003/structure-acquisition-v1/residual/`;
- `pipeline-p003/structure-density-v2/`.

Each has the existing `source/manifest.json` plus `geometry/report.json` and
complete raw output protocol. Root's unchanged `p003_structure_place.run`
can consume each arm directory directly; candidates own disjoint source IDs
within an arm, and predicted overlapping tables retain the existing refusal
behavior. Different acquisition arms remain separate treatments. Combining
original detector and residual candidates requires a separately declared
source partition/conflict policy, not an implicit merge.

Full-page source/geometry report SHA-256:
`5a522394e5fcdcf9ad32e8169f98db26d572e3d7b44cfc4a694b70e008aea221` /
`e14e449415797ae702436281dda68fde6e8a047b51df440c87b9576123c19cf4`.
Residual source/geometry SHA-256:
`e37d0438b9a53fd42bf786c85550ac890a762df657ce82724c80be2c00729483` /
`8ff0566a319fcf287bdfdd0b3b345f2b5ce97cd6e5c90b2560bf8f5536f6fe70`.
Density source/geometry SHA-256:
`4e10577137bfc152e711efa6c7239863b4e6455eac4eed7783314e9b6792f063` /
`607e5a33e5795959d92e6b2a04eb0bdce26e2a6fec061d0f06f5b8d74ed95bd8`.

Archive manifests record every file SHA/byte count. Acquisition archive SHA
is `d013c94e2b80017f14a556018207ab0a3e1987a7bde889d8d43c2b015e367d8c`;
density archive SHA is
`0ad7f30a88eec69c33c48d9cf415292af21ab9b7edb7f9d118528489fcdc9125`.
Density v1 contains only an earlier source preparation, without inference;
v2 adds a strict type annotation and verifies input PDF bytes immediately
before rendering. The same quality-blind proposal inventory was retained.
No scores or references were used between preparations.

Independent evaluation must authenticate the baseline through the supplied
external trust map, validate every original/source/crop hash, authenticate
both inference wrapper and unchanged geometry helper, replay projections from
raw queries, and preserve all intended pages/refusals/unresolved IDs. Coverage
and source-owned placement quality remain separate measurements; ground truth
is only available to the independent scorer after this freeze.

## CPU resources and checks

Source acquisition preparation took 8.938 seconds wall / 8.887 seconds self
CPU; density preparation took 2.214 / 2.201 seconds. Both report Linux lifetime
peak self RSS 539,156 KiB, including their imported baseline-authentication
machinery. Rendering uses one CPU process and no RSS sampling.

| CPU inference arm | Wall seconds | Self CPU seconds | Sampled peak RSS bytes |
| --- | ---: | ---: | ---: |
| Full page | 7.118 | 13.319 | 666,234,880 |
| Residual | 11.351 | 21.580 | 766,726,144 |
| Density | 1.939 | 3.511 | 558,505,984 |

Inference uses one process at a time, with psutil RSS samples every 100 ms.
Library imports, earlier acquisition and original OCR/detection are excluded
from inference times. Root workers were active; these are contended wall
measurements, not serial deployment throughput or a complete setup estimate.

Six synthetic CPU tests check bounded height padding/page clipping, complete
whole-page IDs, residual ownership versus pixel context, duplicate rejection,
empty-region receipts, literal IDs, no-proposal prose cases and explicit
rejection of overlapping capacity windows. Ruff and strict mypy pass for the
four new modules. All completed geometry payload hashes were independently
rechecked against their receipts; no new quality score is reported here.
