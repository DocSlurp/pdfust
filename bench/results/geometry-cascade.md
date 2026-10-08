# CPU geometry cascade study

Run `.venv/bin/python -m bench.geometry_cascade --repeats 3`.

Python 3.14.7; pylopdf 0.13.0; 3 fresh-document repeats.

Native extension SHA-256: `dbc4c1c26cea0f34b00881c51942056259e383cddf46865fe9eaaf9d1293bfa6`. Repository base revision: `7008b627bb01fcec4c12f80308967b511e4e2422`; the extension hash identifies the actual loaded build, including local rebuilds.

CPU only. No model calls, OCR, cached detector boxes, network inference, or training. Timings include PDF opening and complete extraction/Markdown assembly, exclude fixture construction, label scoring and artifact writes. Source comparison runs outside timing. Per-page geometry admission: 8,192 source words, 32 tables, 4,096 cells; native API limits also apply.

Round one froze a numeric evidence gate before benchmarking. Round two corrects full-grid native scoring through Page.to_markdown's existing logical rotation normalization and proposes a stricter vector-header handoff using Senate and two new development controls. Geometry's numerical gate is unchanged. No reference cells, fixture names or content-operator order shortcuts enter extraction. Existing inputs are observations; solid/borderless/partial/prose forward inputs are development; encoding changes, reverse content operators, missing cells, numeric prose and rotations are heldout transformations. Templates are related across splits: this does not demonstrate independent-document generalization.

The heldout transformation outcomes were inspected after round one. Subsequent scores on them are regression observations, not a fresh untouched test. The original report and complete results are preserved locally as round1-before-normalization.{md,json}. Header control inputs are explicitly development-round2; no threshold was tuned against the heldout transformations. Round-two pre-normalization results are preserved as round2-before-logical-header.{md,json}. The final run uses the locally rebuilt native collinear-rule connectivity fix. Prior round artifacts predate that rebuild and lack an extension hash; they cannot isolate its timing effect.

The header baseline reuses header_guided_records without an evidence gate. It extends to page end and expands merged header labels. The revised handoff admits at least two numeric-last-column records, permits anonymous salary records, stops at unsupported prose/gaps, preserves source IDs once, and keeps description continuation out of scalar amount cells. Round three transforms word and vector boxes through the same interpreted baseline direction, handling rotated headers. A merged parent label remains at its anchor once; that is not complete header semantics.

| Split | Method | Exact labeled pages | Correct cells | Relationship recall | False table pages / negatives; excess tables | Median ms | Missing / extra source tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| existing | native | 8/15 | 18/83 | 24/111 | 0/6; 0 | 15.822 | 119/3250 |
| existing | text | 8/15 | 26/83 | 34/111 | 1/6; 1 | 16.015 | 111/3246 |
| existing | geometry | 11/15 | 73/83 | 96/111 | 2/6; 2 | 15.337 | 0/0 |
| existing | header | 6/15 | 0/83 | 0/111 | 0/6; 0 | 15.472 | 0/4 |
| existing | cascade | 10/15 | 38/83 | 51/111 | 0/6; 0 | 15.753 | 0/3187 |
| development | native | 2/4 | 15/36 | 19/51 | 0/1; 0 | 10.128 | 0/0 |
| development | text | 2/4 | 15/36 | 19/51 | 0/1; 0 | 9.741 | 0/0 |
| development | geometry | 3/4 | 36/36 | 51/51 | 1/1; 1 | 8.842 | 0/0 |
| development | header | 2/4 | 12/36 | 17/51 | 0/1; 0 | 9.187 | 0/0 |
| development | cascade | 4/4 | 36/36 | 51/51 | 0/1; 0 | 9.778 | 0/0 |
| heldout | native | 7/16 | 72/168 | 93/238 | 0/2; 0 | 9.714 | 0/0 |
| heldout | text | 7/16 | 72/168 | 93/238 | 0/2; 0 | 9.628 | 0/0 |
| heldout | geometry | 14/16 | 168/168 | 238/238 | 2/2; 2 | 8.803 | 0/0 |
| heldout | header | 3/16 | 12/168 | 17/238 | 0/2; 0 | 9.149 | 0/0 |
| heldout | cascade | 16/16 | 168/168 | 238/238 | 0/2; 0 | 9.349 | 0/0 |
| development-round2 | native | 1/2 | 9/18 | 9/24 | 0/0; 0 | 9.896 | 0/0 |
| development-round2 | text | 0/2 | 9/18 | 9/24 | 0/0; 1 | 10.084 | 0/0 |
| development-round2 | geometry | 0/2 | 15/18 | 19/24 | 0/0; 0 | 9.147 | 0/0 |
| development-round2 | header | 0/2 | 15/18 | 19/24 | 0/0; 0 | 10.059 | 0/0 |
| development-round2 | cascade | 2/2 | 18/18 | 24/24 | 0/0; 0 | 10.304 | 0/0 |

## Complete derivative results

| Input | Split | Native exact | Text exact | Geometry exact | Header exact | Cascade exact / route |
|---|---|---|---|---|---|---|
| cascade-solid-r0-forward | development | True | True | True | False | True / native-grid |
| cascade-borderless-r0-forward | development | False | False | True | False | True / numeric-geometry |
| cascade-partial-r0-forward | development | False | False | True | True | True / strict-vector-header |
| cascade-prose-r0-forward | development | True | True | False | True | True / abstain |
| cascade-broken-r0-reverse | heldout | False | False | True | False | True / numeric-geometry |
| cascade-dashed-r0-reverse | heldout | True | True | True | False | True / native-grid |
| cascade-filled-r0-reverse | heldout | True | True | True | False | True / native-grid |
| cascade-partial-r0-reverse | heldout | False | False | True | True | True / strict-vector-header |
| cascade-missing-r0-reverse | heldout | False | False | True | False | True / numeric-geometry |
| cascade-prose-r0-reverse | heldout | True | True | False | True | True / abstain |
| cascade-numeric-prose-r0-reverse | heldout | True | True | False | True | True / abstain |
| cascade-solid-r90-reverse | heldout | True | True | True | False | True / native-grid |
| cascade-partial-r90-reverse | heldout | False | False | True | False | True / strict-vector-header |
| cascade-missing-r90-reverse | heldout | False | False | True | False | True / numeric-geometry |
| cascade-solid-r180-reverse | heldout | True | True | True | False | True / native-grid |
| cascade-partial-r180-reverse | heldout | False | False | True | False | True / strict-vector-header |
| cascade-missing-r180-reverse | heldout | False | False | True | False | True / numeric-geometry |
| cascade-solid-r270-reverse | heldout | True | True | True | False | True / native-grid |
| cascade-partial-r270-reverse | heldout | False | False | True | False | True / strict-vector-header |
| cascade-missing-r270-reverse | heldout | False | False | True | False | True / numeric-geometry |
| cascade-header-prose | development-round2 | True | False | False | False | True / native-grid |
| cascade-header-footnote | development-round2 | False | False | False | False | True / strict-vector-header |

## Corpus spot checks

Senate and NICS use existing visual record annotations only; full matrices have no gold. The fractions below are annotated cells, not document accuracy.

| Input | Method | Spot-check cells | Open + extract ms | Missing / extra source tokens |
|---|---|---:|---:|---:|
| corpus-senate-expenditures | native | 0/23 | 20.427 | 0/16 |
| corpus-senate-expenditures | text | 0/23 | 20.605 | 0/16 |
| corpus-senate-expenditures | geometry | 23/23 | 19.627 | 0/0 |
| corpus-senate-expenditures | header | 23/23 | 23.709 | 0/4 |
| corpus-senate-expenditures | cascade | 23/23 | 26.690 | 0/0 |
| corpus-nics-background-checks-2015-11 | native | 12/12 | 69.069 | 0/3185 |
| corpus-nics-background-checks-2015-11 | text | 12/12 | 70.131 | 0/3185 |
| corpus-nics-background-checks-2015-11 | geometry | 6/12 | 36.908 | 0/0 |
| corpus-nics-background-checks-2015-11 | header | 0/12 | 55.126 | 0/0 |
| corpus-nics-background-checks-2015-11 | cascade | 12/12 | 97.279 | 0/3185 |

## Header stop and retention evidence

| Input | Method | Admission | Stop | Header IDs retained once |
|---|---|---|---|---:|
| corpus-senate-expenditures | header | ungated | end-of-page-without-record-evidence-gate | n/a |
| corpus-senate-expenditures | cascade | accepted | end-of-source | True |
| cascade-header-prose | header | ungated | end-of-page-without-record-evidence-gate | n/a |
| cascade-header-prose | cascade | insufficient-numeric-records | unsupported-record-or-prose | n/a |
| cascade-header-footnote | header | ungated | end-of-page-without-record-evidence-gate | n/a |
| cascade-header-footnote | cascade | accepted | unsupported-record-or-prose | True |

Errors: 0.

Exact cells preserve empty slots; relationship recall counts horizontal/vertical neighboring cell values, including empties. Missing/extra tokens compare output with the extracted text layer, not OCR gold. Geometry preserves unassigned words outside tables; source agreement does not establish correct ordering. Scanned inputs remain unavailable to geometry.

Extra tokens on native merged tables can reflect intentional merged-cell expansion, not new source facts. The stricter header path retains labels once instead. Timing differences include different output work; these are complete-path measurements rather than interpreter-only costs.

False-positive page counts use gold no-table controls. Excess table counts additionally include extra candidates on labeled pages with a real table, such as prose below a vector header. Unassigned source is HTML-escaped to preserve literal angle brackets and Markdown punctuation.

Next tests: independently labeled partial-rule reports; numerical multicolumn prose with short keys; multiple tables beside prose; wrapped descriptions with blank record keys; merged headers under right-angle rotations; dashed/broken rules with irregular joins; duplicate and overlapping source words. The stricter handoff assumes one dominant right-angle baseline; mixed directions, vertical writing and unrelated document families need separate abstention and correctness evaluation before promoting this cascade.

Complete inputs, per-method output, hashes, timings and errors are local under `bench/results/pdf-master-artifacts/geometry/`. No general fastest-method claim follows from this small synthetic study.
