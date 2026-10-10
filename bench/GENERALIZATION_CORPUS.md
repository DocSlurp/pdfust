# P002 generalization DEV corpus

P002 adds 276 pages selected and constructed before pipeline extraction: 156
new authored one-page layouts, 64 fresh OmniDocBench page images, and 56 pages
from the existing licensed real-world diagnostic assets. This remains DEV
research. Authored references are construction silver, public benchmark
contamination is unknown, and native diagnostics have incomplete structural
references. No cohort establishes heldout generalization.

Run from the repository root:

```sh
uv run python -m bench.generalization_corpus \
  --directory /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002
```

Use `--annotation-path <pinned-OmniDocBench.json>` to reuse a retained snapshot;
its SHA256 is recorded. `--acquire-only` freezes selection and downloads public
images before the full build. Existing frozen selections must agree exactly;
an existing manifest refuses rebuilding. All inputs, source annotations,
private targets, and provenance remain in the ignored artifact directory.

## Cohorts and references

| Cohort | Pages | Selection and coverage | Reference status |
|---|---:|---|---|
| Authored | 156 | 12 variants each of ruled, borderless, mixed, multiple, dense, wrapped, blank, merged, rotated, cropped, decorative, prose, and OCR carrier designs | Cell matrices and spans declared alongside construction operators |
| OmniDocBench | 64 | 16 multiple-table, 24 single-table, 24 zero-table pages; greedy source/language/layout/category-density coverage with frozen hash tie order | Official HTML tables parsed conservatively; unsupported/malformed/ignored table annotations make the entire page structurally unscored |
| Native diagnostics | 56 | Round-robin pages across the explicitly attributed real-world assets | Incomplete references; never count empty targets as true negatives |

Authored geometry varies font sizes, row/column counts, numeric data, blank
anchors, wrapped records, merged headers, rotations, and crop offsets. Dense
variants have 18–22 rows and 7–9 columns. Mixed pages contain both ruled and
borderless tables; multiple pages contain two ruled tables. Negative prose
and decorative-rule pages preserve aligned columns and numeric language.
OCR carrier variants rasterize authored native sources at 120 dpi, then wrap
the resulting RGB pixels without adding hidden scoring text.

OmniDocBench is pinned to revision
`aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec` of
[opendatalab/OmniDocBench](https://huggingface.co/datasets/opendatalab/OmniDocBench).
Its dataset card permits research purposes only, not commercial use. These
inputs are lossless PDF carriers of official page images. Original native
PDFs are unavailable in this snapshot. Raster pages must be reported separately
from original native documents, and native extraction alone is not an OCR
quality measurement.

Only `bench/omnidoc-dev/registry.json` and
`bench/omnidoc-training/registry.json` supply exclusions. Selection excludes
their exact source IDs and known numbered filename parents, including
`*.pdf_<page>.jpg` and `*_page_<page>.*` forms. Known parents are distinct
within P002 too. UUID-style filenames have unknown document parents;
document-level separation cannot be guaranteed. Selection uses category
presence/counts and public classification metadata, never HTML/text answers or
pipeline results. No heldout registry or artifact is accessed.

Native inputs are copied byte-for-byte from `tests/assets/real_world/`.
[The asset attribution](../tests/assets/real_world/README.md) supplies the
original sources, licenses, and producer limitations. Private provenance
retains each source URL, license, and coverage description; source PDFs retain
their original page numbers. The cohort includes real public-domain US
forms/reports/legislation, LPPL LaTeX documentation, licensed Japanese material,
scans, and redistributable interoperability fixtures. Diagnostics are reused
assets with newly selected page records, not newly acquired documents.

## Frozen contracts and leakage boundaries

`manifest.json` and `private-targets.json` follow P001 schema 1. Each manifest
page has an opaque ID, absolute source PDF path, PDF hash, and zero-based page
number. Cohort, family, diversity, label status, and pilot membership are
scoring/analysis metadata. Model evidence admits only the four `model_fields`:
`id`, `pdf_path`, `pdf_sha256`, and `page_number`. Neither source answer HTML,
private tables, provenance, nor selection labels may enter extraction evidence.

Private targets contain rectangular values, `None` covered span slots,
explicit anchor spans, and `structural_scored`. Geometric bboxes are retained
when directly known; rotated/cropped authored targets omit bboxes rather than
claim incorrect display geometry. Original Omni annotation rows and parsing
errors are retained even when scoring abstains. A page with a broken table
annotation remains diagnostic rather than becoming a fabricated negative.

Selection freezes before acquisition; targets/provenance freeze before
extraction; the manifest is written last. Dataset identity includes source
PDF hashes, page identities/metadata, and private references with absolute
artifact paths removed. The predefined 32-page pilot comprises the first two
construction variants of each authored family and the first two metadata
selections of each Omni table-density cohort. Pilot membership is independent
of output quality and excluded from model evidence.

Build measurements use Linux `getrusage(RUSAGE_SELF)` lifetime peak RSS and
`process_time` CPU time, with wall time. Acquisition uses four public-download
threads; construction is one CPU process, including bounded 120-dpi authored
rasterization. No GPU, hosted inference, credential access, or child workers
are involved. Utilization sampling is unmeasured. The full pipeline measures
preprocessing and inference separately.

The initial frozen build contains all 276 pages and 220 structurally scored
pages; the 56 native diagnostics remain unscored. Omni selection covers 10
source genres, five layout classes, and four language labels (35 English,
24 simplified Chinese, three mixed English/Chinese, two traditional Chinese).
All 64 official page annotations parsed without an annotation refusal.
The frozen dataset SHA256 is
`68dda47aa6b0e3fd61cb751d53c7d8ae11546dea4e97ab74e6f9cac6d528332b`.
Initial public acquisition took 13.51 seconds wall and 1.57 seconds process
CPU, with 427,412 KiB process lifetime peak RSS. The separate full construction
process took 17.04 seconds wall and 17.02 seconds CPU, with 767,528 KiB peak
RSS. These are build measurements, not extraction or throughput claims.
