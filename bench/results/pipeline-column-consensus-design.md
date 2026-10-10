# Optional P001 column consensus proposer

The hypothesis was committed in `pipeline-gap-analysis.md` before implementation:
source seed columns should survive sparse rows, and column placement should use
consensus geometry rather than strict floor lookup of seed left edges. This module
adds alternatives without changing the existing assembly proposer or default
pipeline behavior. Root controls subsequent matched experimental arms.

`bench.pipeline_column_consensus.propose(page, existing)` returns complete combined
alternatives. Existing consecutive `cN` entries remain an unchanged prefix. New
entries append stable IDs and mechanisms `column_consensus_physical` or
`column_consensus_rolling`. Complete ownership, literal source-derived values and
span tiling are checked by the existing assembly validator. Duplicate alternatives
are omitted; calling the function again on its combined output is idempotent.

The input is the same source snapshot as the existing proposer. Only literal words,
page dimensions and native vector topology are used. Native-owned cells are
preserved; the remaining words are partitioned by the already declared vertical
region policy. Each region considers at most three seed bands with two through
eight separated fragments. A proposal requires at least three physical rows and
at least two rows with two occupied columns. Seed columns persist even when their
data cells are empty.

Initial separators bisect the whitespace between seed fragments. Source fragments
vote for their corresponding columns; median left and right edges yield new
whitespace separators, and median centers provide a second placement alternative.
A separator must remain strictly between the corresponding seed centers. Source
word centers determine cell ownership. Outer bounds extend by at least one median
word height or half the adjacent seed-center spacing. This tolerates modest scan
or OCR drift without reading target boxes or adding content.

Physical rows and conservative rolling rows are separate alternatives. Rolling
joins only nearby sparse bands lacking first-column content and content in observed
numeric columns. First-column content stays a separate record hypothesis even if
its numeric cells are blank. Left-column wrapped labels therefore remain physical
in this experiment; general mixed wrapping requires more alternatives. Height and
gap policies reuse the existing 1.8-height wrap, three-height extent and 2.5-times
typical-gap conventions. No reference-derived constants, strings, IDs or families
are used. At most four new complete alternatives can be added; the existing
24-alternative admission remains enforced without truncation.

Ten constructed tests cover left-edge drift, sparse final columns, missing middle
cells, right-aligned numeric values, physical and rolling continuation alternatives,
independent first-column records with blank numeric cells, aligned prose ambiguity,
multiple regions, native-grid preservation, outside captions, empty inputs,
annotation mutation, duplicate ownership refusal and prefix preservation.
Aligned prose can still produce a geometry candidate; the preserved no-table
alternative and separate admission decision remain necessary. Forty-seven tests
pass across the new module, assembly, rolling rows and topology; Ruff passes.

After implementation, complete augmented source/candidate bytes were frozen before
the new offline DEV scoring pass. Freeze SHA-256 is
`d8970ecb24cf9c182939d76fe2be2758da66e1ad429c4027110ddd3b547213f4`.
It appends alternatives on ten of 181 pages and raises normalized-plus-retained-OCR
positive exact candidate availability from 34/35 to 35/35. Negative pages with any
nonempty candidate remain 38/133. These are candidate-oracle observations, not
selected-model quality or independent validation. The malformed native diagnostic
grid remains refused; this proposer does not repair native spans.

The augmentation and offline score pass measured 0.69 seconds wall and 0.69 seconds
process CPU with `perf_counter` and `process_time`, sequentially on CPU with no
workers. Source extraction and loading of the retained source freeze precede this
timing; no OCR or hosted inference is included. Memory was not sampled; the
retained `getrusage` high-water is process-lifetime and may include inherited Linux
high-water, so it is not used as a module-specific memory comparison. Raw candidate
and summary artifacts remain ignored under `pipeline-p001-gap-audit`.
