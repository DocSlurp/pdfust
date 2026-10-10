# P002 offline gallery design

`bench.generalization_demo` builds a local, static gallery from an explicit predefined DEV screen and a retained run. It shows every intended screen page, including missing predictions and failures. The screen may contain at most twenty pages; natural16 is the recommended complete sixteen-page screen. It does not rank pages or select successful examples.

The gallery verifies frozen code through the existing P002 verifier, matches each screen source record to the frozen run, requires absolute PDF paths and matching PDF hashes, and revalidates exact successful structure and Markdown through the trusted offline output verifier. A predefined screen may be a subset of a larger frozen run, provided every projected source record matches exactly. Both screen and full-run manifest hashes are recorded. A changed successful artifact is rejected.

Whole-page, regional source assembly and image-only table transcription share the viewer. Source-owned output is labeled with verified retained-source conservation; vision output is labeled model-transcribed without source ownership. Failed and missing pages show their source raster and visible status rather than disappearing from the denominator. Source images follow the retained effective page rotation where available; image-only transcription preserves the original display rotation.

Only table HTML generated locally from verified cell values and integer spans is rendered. All cell strings, errors, provenance, retained JSON and exact Markdown are HTML-escaped. Raw retained Markdown is shown as literal code, never interpreted as model-supplied HTML. Download links point only to exact copied local Markdown, structure and result files. The page has no JavaScript, external dependencies, inference calls, upload behavior or remote resource URLs. A restrictive content policy blocks executable content and network resources.

Optional evaluation input is the already-verified JSON returned by `generalization_report.score_run`. The viewer checks frozen configuration, manifest identity, verification metadata and completed-page count, then displays per-page scores as escaped offline data. An optional retained-report hash is checked when supplied. The gallery never opens scoring references or builds a model request. Evaluation remains a separate offline operation.

Run:

```sh
python -m bench.generalization_demo \
  --manifest <predefined natural16 manifest> \
  --run <verified retained run> \
  --output bench/results/pdf-master-artifacts/pipeline-p002/<new gallery> \
  --image-edge 1024
```

The root `index.html` can be opened locally. Images, exact output copies and `gallery.json` remain ignored artifacts. A source-owned natural16 gallery was built successfully from `natural16-generate-sonnet`: all sixteen outputs passed trusted byte/state verification. Its local location is `bench/results/pdf-master-artifacts/pipeline-p002/demo-natural16-source-owned/index.html`. This is a viewer smoke check, not a quality claim or a deployment.

Seven CPU tests pass, covering all three processors, missing/failed pages, exact copied outputs, escaped hostile cell/error strings, changed output/source rejection, optional evaluation identity, predefined-screen bounds, ignored output destinations and rejection of relative PDF paths. Ruff checks pass. The package extraction API remains unchanged and experimental features remain opt-in.
