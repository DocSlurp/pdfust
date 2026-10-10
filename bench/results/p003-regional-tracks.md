# P003 regional source tracks

The new regional controls apply physical-row assembly and source-gap column
tracks inside every independently frozen YOLO table proposal. They address the
global-gutter control's dependence on unrelated page prose without changing
source strings, detector boxes or ownership rules. They do not infer wraps,
semantic headers or merged cells.

Each of the three YOLO acquisition sizes (640, 1024, 1280) receives the same
nine predeclared profiles: minimum horizontal gap 0.5/1.0/1.5 word heights and
support fraction 0.1/0.25/0.5, with at least two supporting physical lines.
Three separate hybrid controls use frozen TATR column edges at thresholds
0.3/0.5/0.7 together with source physical rows. Hybrid outer table bounds are
the original YOLO region; only the frozen interior column boundaries are used.
No threshold or profile is selected by quality feedback. All 16 pages receive
all 36 treatments, including empty proposals and refusals: 576 outputs.

Words belong only to their original uniquely owned region. Literal strings and
IDs remain whole. A word crossing the region box or a proposed column boundary
remains unresolved. Contested and unowned source IDs remain globally unresolved.
All overlapping region participants are refused, even if some individual words
had unique center ownership. A combined page exceeding the existing 4096-slot
admission refuses all proposed tables atomically; local candidate grids remain
archived with `effective_page_accepted: false` and receive no output credit.
The complete final state always assigns each source ID once to a cell or the
unresolved inventory. Overlap/support measurements are geometry, not calibrated
probabilities or evidence that a proposed grid is a real table.

`regional.compose(source, regions, gap, support, topologies=None)` returns the
global `state`, per-region frozen plans and local states, conflict IDs, an
explicit page refusal, and assigned/unresolved/source counts. Each region
contains an `ambiguity_inventory` with complete unresolved word literals,
global boxes and refusal reasons. These are source-only evidence inventories
for a future bounded decision protocol, not model answers or truncated prompts.

`p003_regional_tracks_prepare.authenticate` requires independent structure,
detector and source code authorities. It authenticates all input archive bytes
and matching current helpers, replays original source preparation, original PDF
rasters/crop images and unique region ownership, and regenerates every TATR
projection from retained raw queries. It neither executes archived code nor
loads a model for inference. The pinned checkpoint bytes are authenticated as
historical provenance by the original preparation helper.

```sh
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
python -m bench.p003_regional_tracks_prepare \
  --geometry /absolute/path/structure-yolo-resolutions-v1 \
  --structure-trusted-code /absolute/path/yolo-structure-v1.json \
  --detector-trusted-code /absolute/path/yolo-resolution-v1.json \
  --source-trusted-code /absolute/path/b773d57.json \
  --output /absolute/path/fresh-regional-controls
```

The original geometry authority pins `generalization_vision_regions.py` to
SHA-256 `20ea20232c0fc3076293ed3c74a2018dcf7f02bada86da81c36c3ed238345230`.
Current root changed that module later. The default authentication correctly
refuses this difference. The CPU preparation used an isolated checkout of the
independently authenticated Git `10b3436` version of that helper; no compatibility
exception was added and no main-worktree helper was changed. Reproduction must
use the same reviewed Git helper in an isolated checkout rather than execute
artifact archives or relax input authorities.

`frozen.json` retains original records, input manifest/geometry hashes, all
independent authority paths/hashes, current code inventory, profiles, sizes,
hybrid thresholds and every complete output hash. `report.json` records every
page treatment and its source-only counts, explicit refusals, code freeze hash,
thread environment and CPU/RSS/wall resources. Complete original source/crop
artifacts are copied privately under `source/`. Quality references and fresh
confirmation pages are never read during preparation.

Nine focused CPU tests pass, including complete duplicate literals, crossing
word conservation, all-participant conflict refusal, hybrid separation, unknown
ownership rejection and atomic slot admission. The first full frozen run took
42.7 seconds wall / 42.4 seconds process CPU and sampled peak RSS 438 MB.
Resources include independent authentication, raster/crop replay and all
derivations, measured for one process with RSS sampled every 100 ms. They exclude
original OCR, YOLO and TATR inference. No API calls, credentials, GPU work or
quality-reference reads were used. These counts and costs do not establish
table quality or complete-pipeline speed.
