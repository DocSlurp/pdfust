# Structured PDF recovery study

This optional study tests table and record relationships, rather than treating
the presence of Markdown table syntax as success. It is separate from the
lightweight timings and CPU model study. It does not change pdfust's public API
or install models into the library's regular environment.

The preserved inputs include all rich-feature cases plus independent derivatives:
the ragged borderless table at 90/180/270 degrees, a raster-only copy, and wrapped
records. Nine synthetic pages have explicit logical cell grids; six prose/math
pages are negative table controls. Other pages remain unscored for complete grid
accuracy. The Senate and NICS pages have independently visually checked record
cells in `structure_cases.py`: these are spot checks, not complete corpus gold.
Sources and redistribution terms remain in the existing corpus README.

Every adapter receives the same original bytes. Only page 0 is evaluated.
Preparation retains a white-background PNG with longest side 1,288 pixels,
positioned word IDs, source text, page rotation, and dominant display baseline
orientation. Page rotation alone is insufficient for orientation normalization:
the Senate's content is already upright after rendering. Extraction is an input
to the experiment and may itself miss Unicode or accessible text.

## Reproduction

The measured GPU environment uses Python 3.12, PyTorch CUDA 12.8, and a local
RTX 3090 with 24 GiB VRAM. Keep it isolated from the CPU Docling/Marker environment.
Choose a disk-backed path with room for model weights; `/tmp` may be a RAM disk.
These commands describe the historical baseline. The user subsequently required
all remaining GPU work to run remotely. The local coordinator was stopped and
disabled; do not execute inference or training commands on the local GPU.

```bash
uv venv --python 3.12 ~/.cache/pylopdf-structure-bench
uv pip install --python ~/.cache/pylopdf-structure-bench/bin/python \
  torch==2.11.0 torchvision==0.26.0 \
  --index-url https://download.pytorch.org/whl/cu128
uv pip install --python ~/.cache/pylopdf-structure-bench/bin/python \
  -r bench/structure-requirements.txt
uv pip install --python ~/.cache/pylopdf-structure-bench/bin/python \
  olmocr==0.4.27 --no-deps
uv run python -m bench.structure --prepare \
  --adapter pdfust --adapter pdfust-text \
  --adapter geometry --adapter geometry-wrapped \
  --adapter geometry-bullets --adapter geometry-wrapped-bullets \
  --adapter native-bullets --adapter native-header-bullets --repetitions 3
PYTHONPATH=src:. ~/.cache/pylopdf-structure-bench/bin/python -m bench.structure \
  --adapter yolo-geometry --adapter yolo-geometry-wrapped \
  --adapter yolo-normalized-geometry-wrapped
PYTHONPATH=src:. ~/.cache/pylopdf-structure-bench/bin/python -m bench.structure \
  --adapter olmocr-image --adapter olmocr-text --adapter olmocr-patch
PYTHONPATH=src:. ~/.cache/pylopdf-structure-bench/bin/python -m bench.structure \
  --adapter qwen-image --adapter qwen-text --adapter qwen-patch
```

Additional switches expose compact coordinate dumps, NF4 loading, normalized
orientation, and YOLO/geometry crops. Use `--help` for the complete adapter list.
Crop adapters reuse saved YOLO predictions or geometry and report that separately
from inference cost. They preserve extracted text outside the replaced regions;
this is an experimental block replacement, not a complete reading-order policy.
`--case` selects a subset, `--repetitions` repeats complete adapter calls, and
`--force` reruns a result. Completed rows are otherwise resumed by input hash.
Run one writer at a time. `--rescore` checks input/output hashes and updates
observations without regenerating or retiming outputs.

After normalized YOLO predictions exist, test the combined source-preserving path:

```bash
uv run python -m bench.structure --adapter hybrid-html --adapter hybrid-bullets \
  --repetitions 3
```

It prefers native vector cells and spans, uses the experimental header-guided
record fallback, gates remaining geometry candidates with normalized YOLO regions,
and performs native OCR only when the page has no extracted words. Detector cost
is reused and excluded from these adapter timings. Inferred headers remain
unverified, and partial/mixed text layers do not trigger automatic OCR repair.

The retained Docling/Marker adapters verify input and output hashes from the
earlier CPU study, require single-page inputs, and carry original timing and
provenance. Replaying their artifacts is not a new performance measurement.
Generate those artifacts using `MODEL_BENCHMARKS.md` before selecting the retained
adapters. They do not support the new derivatives without a new CPU conversion.

## Interventions and evaluation limits

- Geometry regroups physical rows before column assignment and permits trailing
  empty cells. The wrapped variant attaches short continuation lines to a prior
  record. This can incorrectly classify multicolumn prose as a table.
- YOLO26m-DocLayNet gates candidate regions; it does not predict cell structure.
  Detection uses image size 1,024 and confidence cutoff 0.2. Normalization follows
  dominant display text, and candidate coordinates are mapped back to source words.
- Native records preserve vector-grid data and use neutral column labels when
  a very large merged header is unresolved. Header-guided records extend a short
  vector header into the page body and attach description continuations. These
  are experimental heuristics; unrelated prose below a header can be absorbed.
  Neutral labels retain the displaced source header words once outside the grid,
  without text-based deduplication of repeated labels. The earlier lossy prototype
  is archived in `structure-artifacts/history/before-header-retention.tar.gz`;
  its cell scores alone did not reveal 65 missing NICS source tokens.
- olmOCR uses its public no-anchoring v4 YAML prompt, BF16, SDPA, greedy decoding,
  and a default 4,096-token output boundary. The text and patch variants are
  experimental prompts, not the recommended upstream conversion pipeline.
  Automatic retries and orientation correction from the upstream toolkit are
  not claimed. NF4 variants are explicitly separate from BF16 results.
- General Qwen2.5-VL-3B variants test image/text and source-ID patch responses.
  Patches reject invented or duplicated IDs, ragged matrices, and invalid spans.
  Source ID validity cannot prove correct semantic cell/header relationships.
- Row crops split dense regions between physical rows at 12 rows or 160 words,
  whichever comes first, with at most 16 crops. A single oversized row cannot be
  split by this policy. Row patch variants validate all source IDs and reject
  truncation before appending same-width grids. They do not infer spans across
  regions or join header semantics. Crop responses and failed patches are retained.
- Fence repair removes only one whole-response HTML/Markdown fence. It reuses
  inference and cannot repair incorrect cells or a title treated as a table row.
- Native OCR runs on white at 150 dpi, uses four threads, and skips existing text.
  Its geometry fallback retains recognition errors rather than silently replacing
  them with the synthetic reference.

Exact grid checks include table count, cell position, punctuation, and empty cells.
Relationship checks compare horizontal/vertical neighbors, with both reference
and observed totals retained. Merged slots expand from explicit spans for cell
checks; HTML span metadata is observed separately. HTML inside a Markdown code
fence is code, not a rendered table. Bullet variants are scored on their recovered
cell matrices; the experiment does not claim that repeated labels are a semantically
verified header hierarchy. Source token agreement is not OCR ground truth.

Preparation/render/extraction costs are outside adapter timings. Prepared pdfust
baselines are replays and do not provide new conversion timings. GPU initialization
is separate; first inference is included in measured repetitions. Process RSS is
a cumulative high-water value, not a per-case peak. Generation truncation and
allocation failures remain visible. No cross-tool throughput ranking is implied.

## Training pilot

```bash
PYTHONPATH=src:. ~/.cache/pylopdf-structure-bench/bin/python \
  -m bench.structure_train --steps 64
PYTHONPATH=src:. ~/.cache/pylopdf-structure-bench/bin/python -m bench.structure \
  --adapter qwen-4bit-compact-patch --adapter qwen-lora-4bit-compact-patch
```

The fixed pilot uses 36 generated training pages and 12 generated validation
pages, seed 7,100, LoRA rank 8, learning rate 0.0001, and NF4 base weights with BF16
compute. It trains only attention projections and masks image/user tokens from
the loss. The raster's longest side is 640 pixels for this pilot. Validation pages
have separate generated values and layouts, but share template families: this is
a feasibility check, not a template-family holdout or generalization claim.
The original 28 study inputs never enter training. Compare quantized base and
adapted models under the same prompt/quantization before attributing a gain to training.
An adapter checkpoint is saved every eight steps. The measured first attempt
stopped after nine completed steps with NVIDIA Xid 79/154; its losses, responses,
and kernel log are retained separately. After an external OS reboot, the fixed
64-step pilot restarted from the same seed and completed. This infrastructure
failure is not scored as model quality. The pilot does not establish GPU stability.

The tested checkpoints are pinned in the runner:

| Checkpoint | Revision |
| --- | --- |
| YOLO26m-DocLayNet | `49b97586dbd3bdae169e8f5e165710d0facf5f1e` |
| olmOCR-2-7B-1025 | `e52d6f090b7a9007afffbbd6ce510876222fea93` |
| Qwen2.5-VL-3B-Instruct | `66285546d2b821cf421d4f5eb2576359d3770cd3` |

The local `structure-artifacts/model-provenance.json` retains file sizes and SHA-256
hashes, including the loaded weight shards. Findings and cohort denominators are
reported separately from the complete per-case Markdown report.

All PDFs, PNGs, prompts, full responses, traces, model weights, and JSON details
stay outside Git. Commit the protocol, code, tests, and Markdown findings only.
Model licenses remain independent of pdfust: [YOLO checkpoint](https://huggingface.co/hantian/yolo-doclaynet),
[olmOCR checkpoint](https://huggingface.co/allenai/olmOCR-2-7B-1025), and
[Qwen checkpoint](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct).
The local study does not redistribute any model or trained adapter.
## Hosted and larger-memory controls

The hosted controls use local `.env.remote-hosts` credentials without retaining
credential values in artifacts. Run one hosted writer at a time: the cost ledger
is not a concurrent transaction store. These commands send the preserved study
page images and source word dumps to the configured inference provider.

```bash
uv run python -m bench.structure --device hosted-API \
  --report bench/results/structure-hosted.json \
  --adapter qwen-hosted-image --adapter qwen-hosted-compact-text \
  --adapter qwen-hosted-compact-patch
uv run python -m bench.structure --device hosted-API \
  --report bench/results/structure-hosted.json \
  --adapter jev-text-gated-geometry-wrapped \
  --adapter qwen-jev-hosted-compact-text --adapter qwen-jev-hosted-compact-patch
```

Direct vision controls request `qwen/qwen3-vl-235b-a22b-instruct`. Direct Jev
requests `typesafe/jev-1.13` through the typed decisions endpoint, using only
text/coordinates and a proposed geometry grid. It gates candidates at a fixed,
uncalibrated 0.5 threshold; it does not generate or repair missing cell content.
The separate `typesafe/jev-router` experiments send screenshot plus text and
request Qwen routing. The available router pool can ignore that preference;
the actual served model, provider, and router metadata must accompany results.
The adapter name describes the prompt family and does not prove Qwen served it.

Every request reserves $0.25 before transmission against a separate $1.50 API
study ceiling. Provider-reported usage replaces that reservation; absent usage
keeps it. There are no automatic network retries. Full responses, costs, and
generation IDs remain in the ignored hosted ledger and response directory.
API latency includes network/provider work and is not local GPU throughput.

The larger-memory control uses a rented Vast.ai RTX A6000 with 48 GiB VRAM,
PyTorch 2.11.0/CUDA 12.8, and the same pinned model revisions and prepared inputs.
It tests the Senate, NICS, and Form 1040 pages with full/compact text prompts,
plus a separate 16,384-token image-only output-budget control on Senate/NICS.
Reports are `structure-remote48{,-long}.{json,md}`. Input preparation stays local:
the worker's published pdfust 0.13.0 wheel provides scaffolding, since the local
extension requires a newer glibc than the rental host. Native extraction/rendering
timings from that worker are not claimed. Model inference and prepared inputs
remain matched. Preserve remote logs/results before destroying the instance.

On the prepared remote worker, reproduce the memory and output controls with:

```bash
PYTHONPATH=. /workspace/study-env/bin/python -m bench.structure \
  --adapter olmocr-text --adapter olmocr-compact-text --adapter qwen-text \
  --case corpus-senate-expenditures \
  --case corpus-nics-background-checks-2015-11 --case corpus-f1040 \
  --report bench/results/structure-remote48.json
PYTHONPATH=. /workspace/study-env/bin/python -m bench.structure \
  --adapter olmocr-image --max-tokens 16384 \
  --case corpus-senate-expenditures \
  --case corpus-nics-background-checks-2015-11 \
  --report bench/results/structure-remote48-long.json
```

The remaining compact patch, NF4 base/LoRA, and NF4 row-patch cohorts use
`structure-remote-patches.json` on the same worker. The matched base and adapter
cohort contains the nine positive fixtures, six negative controls, and Senate/NICS;
the row-patch cohort contains Senate/NICS. All use the original frozen screenshots
and compact source words, greedy decoding, and 4,096 output tokens. The interrupted
local compact-patch cohort is retained as partial history, not a matched training
comparison. Remote weight hashes are retained independently of local cache hashes.

The separate `olmocr-highres-image` NICS derivative keeps the original 4,096-token
output boundary and uses a fresh white-background CPU render of the original PDF
at a 2,048-pixel longest side. It reads `page-highres.png`, not an upsampled version
of the 1,288-pixel screenshot. The retained `page-highres.json` records PDF/PNG
hashes, dimensions, DPI, and renderer provenance. Prepare the image on CPU and
copy it with its sidecar to the worker before the remote inference command:

```bash
CUDA_VISIBLE_DEVICES='' uv run python -m bench.structure --prepare-highres \
  --case corpus-nics-background-checks-2015-11
PYTHONPATH=. /workspace/study-env/bin/python -m bench.structure \
  --adapter olmocr-highres-image --case corpus-nics-background-checks-2015-11 \
  --report bench/results/structure-remote-highres.json
```

This is a resolution control, not a replacement for the longer-output control.

The user authorized $15 total remote spend, including rental and API inference.
The rental initially had a two-hour destruction watchdog. Dense NF4 generation
required extending that guard to three hours (about $1.30 maximum rental at the
observed rate), within the authorized total cap. Destroy it after artifact
collection rather than waiting for the guard. Record provider charges or explicitly labeled estimates
in the final findings; do not infer actual billed dollars from elapsed time alone.

Generate the compact, failure-inclusive comparison after all writers finish:

```bash
uv run python -m bench.structure_summary \
  --report bench/results/structure-latest.json \
  --report bench/results/structure-hosted.json \
  --report bench/results/structure-remote48.json \
  --report bench/results/structure-remote48-long.json
```

The comparison embeds each input report's snapshot hash. Failed model calls stay
in the positive/negative and corpus-cell denominators; unsupported CPU artifact
replays are reported separately. Cohorts with different denominators must not be
compared as if every adapter ran the same cases.
