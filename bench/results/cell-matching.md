# Saved-prediction CPU cell matching

Run `PYTHONPATH=src:. /home/dan/.cache/pdf-master-cpu/bin/python -m bench.cell_matching --repeats 3`.

Python 3.14.7; NumPy 2.5.3; rapid-table 3.0.2; 3 repeats; word chunks 64.

The installed TableMatch and utils source are loaded through an isolated package namespace; rapid_table's package root, model and inference runtime are not imported. No PDF opening, rendering, inference, GPU access, network, training or dependency installation occurs. Saved source coordinates, structures and cell predictions are reused unchanged.

This original matcher precomputes polygon axis boxes once, computes IoU and the upstream corner-weighted L1 distance in bounded NumPy chunks, and chooses maximum IoU, then minimum distance, then earliest cell index. Scalar arithmetic order, floating dtype and tiny-IoU threshold are preserved. Upstream HTML rendering is reused unchanged. This does not improve structure quality, missing model cells, false tables, or source order.

Limits: 4,096 words, 4,096 cells, 262,144 word-cell pairs per scratch chunk, and finite coordinates within ±10 million. Matching float32/float64 input dtypes are required. Empty-cell input is explicitly defined as all sources unassigned; upstream process_one raises on that input, so that extension is not an equivalence claim.

Timing covers filtering, matching and identical HTML assembly on prepared saved arrays. Saved file reads, coordinate reconstruction, hashing and validation comparisons are excluded. Optimized input admission and AABB precomputation are included. Traced allocation peak is measured in a separate untimed replay; it is not process RSS.

| Input | Route | Words / cells | Upstream ms | Optimized ms | Speedup | Choices / HTML / saved / complete equal | Peak traced KiB | Unassigned IDs |
|---|---|---:|---:|---:|---:|---|---:|---:|
| corpus-nics-background-checks-2015-11 | full | 1504 / 244 | 4069.043 | 15.693 | 259.3× | True/True/True/True | 1770.7 | 90 |
| corpus-nics-background-checks-2015-11 | cropped | 1500 / 283 | 4825.841 | 17.724 | 272.3× | True/True/True/True | 1992.6 | 24 |
| corpus-senate-expenditures | full | 637 / 290 | 2048.917 | 8.388 | 244.3× | True/True/True/True | 1738.1 | 3 |
| corpus-senate-expenditures | cropped | 637 / 201 | 1414.890 | 5.901 | 239.8× | True/True/True/True | 1239.4 | 52 |
| table-bordered | full | 10 / 13 | 1.460 | 0.191 | 7.6× | True/True/True/True | 12.4 | 0 |
| table-bordered | cropped | 8 / 9 | 1.955 | 0.184 | 10.6× | True/True/True/True | 8.9 | 0 |
| table-borderless | full | 10 / 68 | 7.142 | 0.235 | 30.3× | True/True/True/True | 44.6 | 0 |
| table-borderless | cropped | 8 / 9 | 0.799 | 0.135 | 5.9× | True/True/True/True | 8.9 | 0 |
| table-borderless-aligned | full | 10 / 76 | 8.262 | 0.300 | 27.5× | True/True/True/True | 49.3 | 0 |
| table-borderless-aligned | cropped | 8 / 8 | 0.729 | 0.146 | 5.0× | True/True/True/True | 8.5 | 0 |
| table-merged | full | 10 / 11 | 1.223 | 0.207 | 5.9× | True/True/True/True | 11.2 | 0 |
| table-merged | cropped | 8 / 8 | 0.733 | 0.152 | 4.8× | True/True/True/True | 8.5 | 0 |
| text-structure-and-literals | full | 38 / 23 | 9.080 | 0.234 | 38.8× | True/True/True/True | 58.5 | 0 |
| text-structure-and-literals | cropped | 0 / 0 | n/a | n/a | n/a | True/True/True/True | 0.0 | 0 |
| two-column-order | full | 115 / 80 | 101.355 | 0.756 | 134.0× | True/True/True/True | 432.3 | 0 |
| two-column-order | cropped | 112 / 16 | 19.096 | 0.409 | 46.6× | True/True/True/True | 112.6 | 0 |

Exact association and region/complete HTML equivalence: 16/16 saved routes.
Nonempty matching routes: 15; empty cropped routes: 1.

Unassigned source IDs include words filtered above the smallest cell y coordinate and words failing the original IoU threshold. They are retained separately in local JSON. The equivalence output deliberately preserves the specialist's original complete-HTML assembly policy; those IDs are not silently reinserted into a new table or counted as recovered cells. Empty cropped routes have zero regions and vacuous matching equality.

## Provenance and next tests

Validation: 19 targeted tests pass in the isolated CPU dependency environment. Ruff and targeted mypy pass. The regular development environment skips these optional tests when rapid-table is absent; no production dependencies are added.

Measured source SHA-256: `977b6f920eea93c82daa9684ab5503ae9c21d4ae8cea76710141ea4ad8d6464b` (retained as `measured-code.py`).

Report generator SHA-256: `dcbc4ac91dcd9e98994367dbe69f02e6c7c3ea2693c79ab521a28a9d0237bc9f` (retained as `report-generator-code.py`). Reporting and provenance-copy changes after timing do not alter the matcher or recorded samples.

Upstream source SHA-256: `{'main.py': '7c9bb46cbabaa5cb03c6fe54720484756436a0598ad827a56b796c7ab89d6396', 'utils.py': '93e08c37035883ec16bacc1e4baa9fc7bf958ecfa806d788375585367d55f703'}`.

Full associations, unmatched IDs, saved-input hashes, all timings, original matched HTML, and the executed source snapshot remain local in `bench/results/pdf-master-artifacts/matching/`. Inputs come from the eight-case specialist pilot; upstream/saved parity checks expose coordinate reconstruction or tie differences instead of concealing them.

Next tests: independent structure predictors and documents; nearly equal float32 IoUs; real overlapping/degenerate cells; adversarial larger tables at admission boundaries; HTML with predicted cells missing corresponding closing tags. A conservative overlap or containment policy would change associations and needs separate quality labels. These saved predictions do not establish semantic table accuracy.
