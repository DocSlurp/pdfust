# Reproducing the P002 PDF pipeline experiments

These `bench` modules are opt-in research runners, not a public production API.
They retain complete page outputs, failures, requests, responses, code hashes and
resource measurements. Start with the fixed 16-page DEV screen; the full DEV
manifest contains 276 pages. Neither command selects only successful pages.

## Environment and retained inputs

Run from the repository root with its built extension and benchmark dependencies:

```sh
uv sync --extra ocr --group bench --group bench-vision
p002="$PWD/bench/results/pdf-master-artifacts/pipeline-p002"
repro_id=$(date -u +%Y%m%dT%H%M%SZ)
```

Existing inputs are `$p002/corpus-r2/manifest.json` and
`$p002/screens/natural16/manifest.json`. They contain absolute source PDF paths,
page numbers and hashes. Moving the checkout does not relocate those PDFs.
Inference explicitly projects records to `id`, `pdf_path`, `pdf_sha256` and
`page_number`; references and family/quality metadata do not enter requests.
Each page verifies its PDF hash. Keep the original manifests and PDFs unchanged;
a relocated dataset needs a separately reviewed manifest and identity.

The native-only command needs no provider. Hosted routes currently read
`OPENROUTER_API_KEY` from repository `.env` or `.env.remote-hosts` through
DecisionClient; merely exporting a shell variable is not its implemented setup.
Optional Langfuse and the retained nonsecret pricing catalog have their own setup
in [DECISION_MODELS.md](DECISION_MODELS.md). The existing shared ledger and prior
cost history must be available: deleting them is not a fresh-run procedure.

YOLO routes additionally require the local assets pinned in
[pipeline_layout_detector.py](pipeline_layout_detector.py): Python at
`/home/dan/.cache/pylopdf-structure-bench/bin/python` and YOLO26m DocLayNet weights
under `/home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/`.
The runner does not download missing assets. Installing the repository extras does
not recreate that isolated model environment. Native OCR requires the `ocr` extra
and its independently distributed model files. This setup is CPU-only; YOLO forces
CPU and hides CUDA, and these commands use no local GPU.

## Complete source-owned output

Native grids and source-ID generation retain native/OCR strings and assign each
retained word once to table cells or remaining prose. Source conservation describes
this inventory, not whether OCR was correct or a detected region really was a table.
Detector boxes are proposals; native grids get priority and residual text remains
explicit. Run directories must be new: the runner refuses an existing directory.

The native full baseline uses the settings of `native-regional-full-r2`:

```sh
.venv/bin/python -m bench.generalization_run \
  --manifest "$p002/corpus-r2/manifest.json" --output "$p002/repro-$repro_id-native-full" \
  --policy native --rotation-mode always --ocr-dpi 150 --ocr-source legacy
```

A fresh natural16 Sonnet source-ID generation run uses the historical screen arm's
256-word regions and rotation behavior:

```sh
.venv/bin/python -m bench.generalization_run \
  --manifest "$p002/screens/natural16/manifest.json" \
  --output "$p002/repro-$repro_id-natural16-sonnet" --policy gated \
  --assembly-method generate --generation-model anthropic/claude-sonnet-5.5 \
  --generation-format anchors --generation-tokens 8192 --image-edge 512 \
  --region-words 256 --region-characters 8000 --packet-characters 25000 \
  --rotation-mode always --ocr-dpi 150 --ocr-source legacy
```

The full276 YOLO/Haiku matrix arm uses these settings:

```sh
.venv/bin/python -m bench.generalization_run \
  --manifest "$p002/corpus-r2/manifest.json" --output "$p002/repro-$repro_id-full276-haiku" \
  --policy gated --assembly-method generate --generation-model anthropic/claude-haiku-5.5 \
  --generation-format matrix --generation-evidence objects --generation-tokens 8192 \
  --image-edge 512 --region-words 1024 --region-characters 16000 \
  --packet-characters 25000 --layout-detector yolo --detector-edge 1536 \
  --detector-tiles none --detector-residual retain --detector-boundary retain \
  --rotation-mode native --ocr-dpi 150 --ocr-source legacy
```

These commands create new runs with current code. Exact historical replay also
requires the archived `code/`, `frozen.json` and recorded runtime/model environment;
a matching CLI does not promise identical hosted responses. Existing artifacts
`natural16-generate-sonnet` and `full276-yolo-matrix-haiku-512` can be inspected and
scored offline without paying for another run.

## Vision and hybrid provenance

Whole-page vision is an image-only **table-only** comparator. It preserves original
page rotation, sends explicit RGB JPEGs, and strictly parses model-transcribed cell
strings and global display boxes. It promises neither full prose nor source-ID
identity. A fresh natural16 run is:

```sh
.venv/bin/python -m bench.generalization_vision_run \
  --manifest "$p002/screens/natural16/manifest.json" \
  --output "$p002/repro-$repro_id-vision-haiku" \
  --generation-model anthropic/claude-haiku-5.5 --generation-tokens 16384 \
  --image-edge 1200 --jpeg-quality 90 --workers 1
```

The separate `--workers 4` experiment is allowed only for fresh P002 whole-page
Haiku vision with at most 16,384 output tokens, no OCR/detector and no retry/replay.
It uses atomic shared reservations and retains deterministic frozen page order.
It cannot be applied to detector crops or source/OCR/hybrid runners. Do not mix
legacy non-atomic wave admission with this concurrent experiment; keep historical
prior-cost ledgers immutable. A reservation must cover the model's possible charge.

The detector-crop comparison uses all fixed CPU YOLO proposals, with no score-based
page selection. Its 1024-pixel Sonnet control is reproduced with:

```sh
.venv/bin/python -m bench.generalization_vision_run \
  --manifest "$p002/screens/natural16/manifest.json" \
  --output "$p002/repro-$repro_id-crops-sonnet" --detector-crops \
  --generation-model anthropic/claude-sonnet-5.5 --generation-tokens 16384 \
  --image-edge 1024 --jpeg-quality 90 --workers 1
```

The Haiku comparison changes only `--generation-model` to
`anthropic/claude-haiku-5.5` and uses a different new output directory. Explicit
400/512/768-pixel JPEG90 controls change `--image-edge`; the 2048-pixel JPEG50
control changes both edge and quality. Every crop must validate before a page
is admitted. Failed crops remain charged, and no successful prefix becomes a
successful page. Fresh responses may differ even for identical request bytes.

Hybrid keeps validated native tables, obtains detector-crop transcriptions for
non-native proposals, and combines them with all remaining native/OCR words:

```sh
.venv/bin/python -m bench.generalization_hybrid_run \
  --manifest "$p002/screens/natural16/manifest.json" \
  --output "$p002/repro-$repro_id-hybrid-haiku" \
  --generation-model anthropic/claude-haiku-5.5 --generation-tokens 16384 \
  --ocr-source whitespace --ocr-dpi 150
```

Hybrid tracks every original word once as native, prose or superseded by a fully
containing transcribed table. Crossing/outside words stay literal. This accounting
is distinct from literal output conservation: model table text has transcription
provenance. Conflicting table geometry refuses the whole page; a retained native
baseline is diagnostic, not a successful hybrid output. With no transcription, a
validated native baseline remains source-conserved.

## Offline scoring and complete-output inspection

Scoring is a separate command that verifies archived code, replays retained output
and reads DEV reference files. It makes no inference calls. Keep its new output stem
separate from the immutable run directory:

```sh
.venv/bin/python -m bench.generalization_report \
  --corpus "$p002/screens/natural16" --run "$p002/natural16-generate-sonnet" \
  --output "$p002/repro-$repro_id-natural16-evaluation"
.venv/bin/python -m bench.generalization_report \
  --corpus "$p002/corpus-r2" --run "$p002/full276-yolo-matrix-haiku-512" \
  --output "$p002/repro-$repro_id-full276-evaluation"
.venv/bin/python -m bench.generalization_demo \
  --manifest "$p002/screens/natural16/manifest.json" \
  --run "$p002/natural16-generate-sonnet" --output "$p002/repro-$repro_id-gallery"
```

Open the gallery's local `index.html`. It includes all 16 intended pages, errors and
missing outputs, source images, provenance, safely rendered structured tables and
links to complete retained Markdown/JSON. Raw Markdown is displayed as escaped
text; model HTML is not injected. Galleries accept an explicit screen of at most
20 pages, so the same natural16 screen can inspect a full276 run. No upload or
JavaScript dependency is involved. Optional `--evaluation` expects one verified run
object from the scorer JSON's `runs` list, not the enclosing multi-run document.

For every run, inspect `report.json`, `frozen.json`, page `*-result.json`,
`*-structure.json`, `*.md` and retained requests/responses together. Parent resources
use process CPU time and RSS sampled every 100 ms; detector-worker CPU/RSS and cold
initialization have separate scope. OCR initialization is charged at first use.
The serial default is one page at a time; OCR and YOLO each use four CPU threads.
Four-worker vision reports whole-run parent CPU/RSS/wall as primary measurements;
overlapping per-page/call process CPU intervals are nonadditive. Remote GPU and
server utilization remain unmeasured.

Paid requests share `bench/results/pdf-master-artifacts/decisions/ledger.json`, a
USD 150 cumulative ceiling and a separate USD 50 P002 ceiling. Fresh output paths do
not reset spend. Keep positive provider charges, reported zero, labeled catalog
estimates and unresolved reserves distinct; unknowns do not become zero costs.
Preserve failed-call reservations and raw receipts, and investigate them before any
explicit retry. These experiments remain DEV-only; protected heldout data is outside
this reproduction workflow.

## Extracting your own PDF

The experimental single-document wrapper creates a source-only manifest for an
arbitrary local PDF; it creates no annotations or scoring corpus. Native CPU
extraction is the default:

```sh
.venv/bin/python -m bench.extract_document /absolute/path/document.pdf \
  --output "$PWD/bench/results/pdf-master-artifacts/my-document-$repro_id"
```

Use `--page 0 --page 2` for an explicit zero-based subset. The default admits up to
128 requested pages; `--max-pages` can explicitly increase that bound through
4,096. Larger whole documents require an explicit subset or raised admission.
Inputs are bounded to 64 MiB, and an existing output directory is refused.
Combined Markdown has a separate 64 MiB UTF-8 cap, checked before reading/concatenating
page Markdown. Refusal marks the document partial with an explicit combined-output
error; individual complete page artifacts remain intact.

`document.md` combines requested pages in physical page order with visible failure
placeholders. `document.json` distinguishes complete document output from partial
output and separately records whether every requested page succeeded. A successful
subset remains a partial document. The CLI exits 2 for partial output. The unique
child directory retains the original runner's frozen manifest/config/code, complete
page Markdown/structures/results, requests/responses, costs and resource report;
`pipeline.log` retains startup or dispatch failures. Wrapper dispatch wall includes
child startup and aggregation; pipeline CPU/RSS measures the runner child, and detector worker
measurements remain separate. Wrapper CPU/RSS is unmeasured.

The explicit paid modes `--mode hybrid-haiku` and `--mode hybrid-sonnet` delegate to
the existing coordinated hybrid runner with preserved page rotation, whitespace
OCR at 150 DPI and 16,384 output tokens. They use the project provider configuration
and shared ledger; they require the same local OCR/YOLO assets described above.
Native mode also uses OCR on pages lacking extractable text, so those pages need
the OCR extra. Failed pages remain partial rather than becoming successful empty
outputs. This wrapper does not make the research pipeline a portable public
production API or alter the frozen experiment settings.
