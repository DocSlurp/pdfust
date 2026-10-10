# P003 fresh confirmation source freeze

Date: 2026-10-10 UTC. This corpus was prepared after the original DEV16
exploratory comparisons. It provides fresh confirmation inputs, not a
protected heldout result. No protected directory was enumerated, read or
searched; there were no credentials, GPU or hosted inference calls.

The frozen pool has **48 pages**: 12 multiple-table, 12 single-table and eight
negative public OmniDocBench pages, plus 16 newly authored synthetic pages.
Natural table counts are classification metadata, totaling 50 table blocks.
No natural recognition text, HTML, reference polygons or scorer results were
used for selection or rendering. Natural targets are attached separately by
the independent scorer after this source freeze.

## Selection and separation

The exact seed is `jev-pdf-p003-fresh-confirmation-20261010-v1`. The eligible
metadata source is the retained public `pipeline-p002/OmniDocBench.json`, at
existing pinned dataset revision `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec`.
Only page identifier, source width/height, page classification attributes and
layout category counts are projected into selection metadata.
[Public dataset](https://huggingface.co/datasets/opendatalab/OmniDocBench/tree/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec).

Authorized unprotected exclusion files are exactly:

- `bench/omnidoc-dev/registry.json` and `bench/omnidoc-training/registry.json`;
- P002 `selection-frozen.json`, `corpus-r2/manifest.json` and
  `ocr-evidence/selection-frozen.json`;
- P002 `private-provenance.json` and `corpus-r2/private-provenance.json`,
  accessed only for IDs, source case and document-parent mapping.

The frozen exclusion receipt records hashes for all seven files, 96 source
IDs, 50 parent groups, known opaque page IDs and known input PDF hashes.
Every OCR-evidence opaque ID is proved a subset of the authorized corpus-r2
manifest. Document parents are inferred only from explicit `_page_N.ext` or
`.pdf_N.ext` filename suffixes; 870 unknown-parent rows are rejected. Known
eligible pools contain 51 multiple-table, 158 single-table and 464 negative
pages before within-selection parent deduplication.

Within each fixed density quota, selection greedily covers source/language/
layout/category/math-density metadata; seeded SHA-256 ordering breaks ties.
Selected parents are immediately excluded from subsequent choices. All 32
selected natural pages have distinct known parents, and neither source IDs
nor parents overlap known exclusions. The code refuses insufficient quotas
rather than relaxing separation. This establishes separation from the named
known exploratory/training sources; it makes no claim about the public
model's original training exposure or protected custodial inputs.

`selection-frozen.json` was written before any image acquisition or PDF
rendering, SHA-256
`7c28b5e13de6a0012444e40fb5921caec78f3dc67d5819cbcfc33737e214c0a2`.
It includes the 32 selected metadata records and all 16 authored construction
plans, with individual seed hashes and hypotheses.

## New authored designs

Two novel numeric/text seeds are rendered for each of eight fixed designs:
wrapped cells, merged anchors, a table beside prose columns, aligned prose
negatives, a math inset beside a table, separate multiple tables, blank cells,
and borderless tables. The new seed produces distinctive labels and numbers;
existing synthetic pages or construction targets are not regenerated.

Each PDF uses new explicit operators with separate construction matrices.
Merged-slot omissions in vector dividers follow the declared spans. Wrapped
continuations remain literal text fragments in one construction cell.
Prose-negative pages contain aligned text and decorative rules with zero
construction tables. Math insets contain a displayed polynomial and prose,
with no inset table. Construction targets are retained separately from the
runtime manifest and are labeled repository-authored references, not
independently adjudicated natural gold.

The hypotheses were fixed before rendering: preserve logical wrapped cells,
merged occupancy, independent table boundaries and blank positions, and avoid
absorbing neighboring prose or formula insets. No source design was changed
in response to model output or score.

## Source contract and scoring handoff

Ignored artifacts are under
`pipeline-p003/confirmation48-v1/`. Public images are wrapped losslessly in
new PDF carriers at source scale 0.36 points per pixel, with zero offsets and
rotation. Actual decoded image dimensions must match public metadata. Every
page retains its PDF hash, explicit display viewport and preview hash; source
provenance retains image hash, public annotation path/hash and exact
annotation-to-display transform. Natural PDFs are image carriers, not
original native PDFs. The dataset's research-only/noncommercial restriction
is recorded in provenance and its pinned dataset card is retained locally.

The immutable runtime manifest uses schema 2 and identity basis
`source-only-confirmation-v1`. Its dataset identity is SHA-256 of canonical
JSON containing **exactly** `schema: 2`, that identity basis, selection hash,
and all complete page records with only `pdf_path` omitted. Targets are not
part of this source identity. The independent scorer must validate source
bytes, selected IDs/table counts/transforms, then attach its own targets with
this dataset identity and separate target-file provenance. It must not
rewrite the runtime manifest.

Source dataset SHA-256:
`6a95069917f121c0ab591467606b017f9d1a94077d445ef58fa6ca70440fe3e1`.
Manifest SHA-256:
`2548256a5289d64e1a0a5d0de1683c6e068fa8db295fce64814f3bb134664b99`.
`source-freeze.json` records manifest, selection, source provenance,
construction-target and helper hashes. Only input IDs/PDF paths/hashes/page
numbers are allowed into model evidence; family, source metadata, hypotheses
and construction targets remain experiment/scorer metadata.

## Confirmation treatment and CPU checks

Root's predeclared primary comparison is PPLX selector images at 128 RGB
versus 512 RGB and text-only controls. Baseline generations are separately
identified for Luna and Sonnet. Their generation/provider identities must
remain explicit, with no automatic fallback. This preparation makes no
request and selects no winner; comparisons and derivative arms belong to
root's separately frozen paid plans.

Source acquisition/build took 16.761 seconds wall and 11.849 seconds self CPU;
Linux lifetime self peak RSS was 661,740 KiB. At most four public downloads
were concurrent, while rendering used one CPU process. Root workers were
active, so wall time is contended. Downloads totaled 30,406,985 image bytes;
48 PDF carriers/native constructions total 45,181,990 bytes. CPU/RSS use
`process_time`/`getrusage`, with no sampling or child-process measurements.
The separate metadata freeze and interpreter imports are outside this build
receipt. This is not a hosted latency, OCR throughput or complete setup claim.

Five CPU tests check exact quotas/determinism, parent exclusions and unknown
parent rejection, refusal on insufficient separation, invariance to natural
answer changes, required OCR subset proof, and all 16 deterministic new PDFs
with complete nonoverlapping construction slot tilings. All source PDF hashes
were rechecked after the complete build. Ruff and strict module mypy pass.

```sh
python -m bench.p003_confirmation_corpus --output <fresh-directory> --freeze
python -m bench.p003_confirmation_corpus --output <fresh-directory> --build
```

Both phases refuse an existing frozen output of the same phase. Raw source
images, PDFs, previews, construction targets, manifests and resource receipts
remain ignored local artifacts; only helper/tests/this report are committed.
