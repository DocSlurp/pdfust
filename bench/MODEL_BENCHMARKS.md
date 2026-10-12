# Docling and Marker feature measurements

The optional model study uses the same 23 PDF bytes as the lightweight study.
[Its report](results/features-models.md) includes the earlier measurements with
their original provenance, plus Docling, Docling with formula enrichment, and
Marker's CPU fast mode. It does not rerun or relabel the earlier timings.

These dependencies are deliberately isolated from the library and its regular
development environment. The published model run uses Python 3.12, CPU-only
PyTorch, and four inference threads. Reproduce on Linux with:

```bash
uv sync --group bench-rich
uv run python -m bench.features
uv venv --python 3.12 /tmp/pdfust-model-bench
uv pip install --python /tmp/pdfust-model-bench/bin/python \
  --index-strategy unsafe-best-match \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  -r bench/models-requirements.txt
PYTHONPATH=src:. /tmp/pdfust-model-bench/bin/python -m bench.model_features \
  > bench/results/features-models.log 2>&1
```

The pinned requirements capture the measured environment rather than declaring
cross-platform support. Initial execution downloads model weights. Weights are
cached outside the repository; the report records their repository, revision,
file sizes, and SHA-256 digests. No hosted LLM API is used.

The adapters use public entry points:

- Docling `DocumentConverter` with `PdfPipelineOptions(do_ocr=False)`, CPU
  acceleration, picture generation, and embedded-image Markdown export.
- A separate Docling mode enables `do_formula_enrichment=True`. This is
  model-based formula recognition even though page OCR is disabled. Recognition
  depends on the preceding layout stage finding a formula region. See
  [Docling's enrichment documentation](https://docling-project.github.io/docling/usage/enrichments/).
- Marker `PdfConverter` with `mode='fast'`, `disable_ocr=True`, `use_llm=False`,
  and one PDF text worker. This version's OCR-off setting also disables equation
  recognition. Images are saved alongside the unmodified Markdown so relative
  references resolve. See [Marker's public API](https://github.com/datalab-to/marker).

Pipeline construction is recorded separately. Each input receives an unmeasured
warmup, followed by three complete conversions with a fresh PDF input. Lazy
model startup is included in warmup; median conversion timings include inference
and Markdown export. Structured JSON and external image serialization, syntax
probes, and hashing occur outside that timer. Structured artifacts retain the
first warmup result and are not separately timed extraction benchmarks.
Marker's sidecar serializes the Markdown renderer's output and metadata, with
PIL image objects saved as separate files; it is not the separate JSON renderer's
block-tree output. Docling's sidecar is its native document tree.

Git stores the Markdown summaries, pinned environment, and compact timing/hash
baseline. Full feature JSON, copied source PDFs, raw outputs, structured sidecars,
images, and logs are generated locally and ignored. The summaries retain model
versions, initialization timings, and cached weight revisions/hashes; use the
local details to inspect content. From a clean checkout, generate the lightweight
base study first, as shown above.

The local JSON retains original run metadata plus `additional_runs`; each model result
has a `run_index`. Original input hashes must match before adding measurements.
Failures remain visible. Output repeatability refers to exact Markdown bytes,
not deterministic structured metadata or image encoding. Syntax and literal
probes are observations, not an overall quality score or an equivalent-work
speedup claim. Inspect the source PDF, full Markdown, structured output, and
image files together.
Retain the console log too: pipeline logging warnings, such as discarded table
cells, can indicate content loss even when conversion returns successfully.

Use repeated `--adapter` and `--case` arguments for a subset. `--base` accepts a
previous combined report, allowing another adapter run to replace its own rows
while retaining all other results and provenance. Use `--threads` and
`--repetitions` to control the recorded execution settings.
After an interruption, pass the partial report as `--base` and use `--resume`
to preserve successful rows with their original run metadata and continue the
remaining cases. Input hashes are checked before any model pipeline starts.
