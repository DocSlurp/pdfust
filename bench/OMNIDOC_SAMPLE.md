# OmniDocBench DEV sample protocol

The registry in [omnidoc-dev/registry.json](omnidoc-dev/registry.json) freezes 16
metadata-selected external DEV page images. The official
[dataset](https://huggingface.co/datasets/opendatalab/OmniDocBench) revision is
`aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` (1,651 annotated pages, including the
April 2026 hard subsets). The official
[project](https://github.com/opendatalab/OmniDocBench) supplies annotation schema
and evaluation tools. This is a public benchmark; model pretraining exposure is
unknown, and tuning on these rows makes them DEV rather than heldout evidence.

The pinned dataset card says the dataset is **for research purposes only and not
for commercial use**. This dataset restriction is separate from the benchmark
code's license. Raw images, annotation answers, and complete output artifacts
stay in the ignored local directory
`bench/results/pdf-master-artifacts/omnidoc-dev`; only identifiers, classification
metadata, source URLs, hashes, and summary observations are committed. These
files do not grant a license to underlying document content.

Selection uses metadata only: greedily maximize newly covered `data_source`,
`language`, `layout`, and Boolean presence of isolated equations and tables.
Candidates are ordered by SHA256 of the frozen seed plus image identifier to
break ties, then the same order fills remaining slots. No recognition text,
LaTeX answer, model confidence, extraction output, or benchmark score enters
selection. The policy is intentionally a diversity sample, not a population
estimate, and includes rare language/document strata.

Reproduce from the repository root with its built CPU extension:

```sh
.venv/bin/python -m bench.omnidoc_sample --fetch --baseline
```

`--fetch` downloads the pinned card, annotations, and only the 16 selected images,
retains canonical selected annotation rows, and regenerates the compact registry.
Downloads use public HTTPS without credentials. SHA256 hashes identify original
annotation/card bytes, each image, and each canonical selected annotation row.
`--baseline` verifies image hashes and generates the retained full baseline JSON
and the readable [16-row report](results/omnidoc-sample.md). Supply `--artifacts`
to move the ignored raw artifact directory; take care not to commit its contents.

At this revision the dataset file listing has images and annotations but **no
original PDFs**. Earlier dataset history and the card mention original slices;
this protocol does not assume those historical files match this release. CPU
baseline PDFs are explicitly synthetic image carriers: 200-DPI source pixels
map to points at 0.36 points/pixel, then render at 72 DPI. Image insertion,
`get_text`, `find_tables`, `get_images`, Markdown conversion, and PNG rendering
run sequentially with one document at a time. Their empty native text/vector
results are expected and do not measure OCR or native-PDF extraction quality.

Resource measurements use Linux `resource.getrusage(RUSAGE_SELF)` CPU deltas and
process-lifetime peak RSS, with elapsed wall time from `perf_counter`. No polling
interval applies, there are no worker children, and complete baseline provenance
records platform, logical CPU count, version, and concurrency. Download time is
outside this baseline. No local GPU, training, hosted inference, or provider
spending occurs.
