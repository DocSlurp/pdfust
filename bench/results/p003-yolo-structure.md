# P003 structure geometry from all matched YOLO resolutions

On 2026-10-10, all 80 table proposals from the independently frozen YOLO 640/1024/1280 arms were passed through the retained CPU Table Transformer checkpoint. No reference, oracle selection, fresh confirmation data, credential, GPU, hosted inference, download, or model fallback was accessed. All 16 pages remain present separately in each acquisition arm. The experiment freezes 27 treatments: three acquisition sizes × three structure thresholds × three literal source placement policies, yielding 432 complete page records.

The root-approved `yolo-resolution-v1.json` code map authenticates the exact Git `05f7a6a` detector experiment. The separate `b773d57.json` map authenticates the complete original ordinal source baseline. Source PDFs, retained source snapshots, display viewports, rotations, cached detector pixels, every raw YOLO output and projection, and the full 16-page inventory were revalidated before crop preparation. Both authorities are required; copied maps are receipts, not independent approvals. No higher-resolution arm was selected from reference quality.

All 19/24/37 returned YOLO Table proposals are retained, including empty, overlapping, or potentially false proposals. They receive distinct crop IDs; there is no additional NMS, capacity split, confidence-ranked acquisition winner, or silent crop merge. Word ownership is fixed before structure inference: a bbox center inside exactly one inclusive proposal owns that whole literal source ID; a center in multiple proposals stays unresolved. Non-owned words with positive bbox intersection are explicit pixel-context-only IDs. Owned word bboxes crossing the crop are flagged, rather than claiming full pixel visibility. This differs from the historical confidence-ranked/capacity-split ordinal crop inventory.

| YOLO size | Crops | Uniquely owned words | Contested center IDs | Owned words crossing crop bbox | Raw proposal overlap pairs |
|---|---:|---:|---:|---:|---:|
| 640 | 19 | 2,205 | 0 | 49 | 0 |
| 1024 | 24 | 3,218 | 0 | 159 | 0 |
| 1280 | 37 | 3,125 | 143 | 257 | 3 |

The complete 10,778-word source remains present on every page. The 1280 table-box union covered 3,268 word centers in the detector diagnostic; unique ownership here deliberately excludes the 143 contested IDs. Ownership and counts describe source acquisition, not whether words are reference table text or whether a proposal is correct.

All 80 crop images were frozen before the first structure forward. Pixel preparation matches the original structure experiment: render the unchanged source PDF at scale `4095/max(display width,height)`, then use the existing continuous EXTENT crop primitive with edge 1024, JPEG quality 90, and exact YOLO global bbox. Rendered pixels use white background and RGB. Original/effective rotations were zero and had to agree with the actual PDF; no rotation normalization was performed. The old 640 TATR outputs were not reused because exact old crop geometry, source ownership and image/input byte identity was not proven. This is a new conditional acquisition treatment, not a matched reuse of the historical 20-crop ordinal pool.

The retained `microsoft/table-transformer-structure-recognition-v1.1-all` checkpoint is unchanged at revision `7587a7ef111d9dcbf8ac695f1376ab7014340a0c`; the safetensors SHA-256 is `9df416575a3a36ebd0129342d4f597f14d6e5170268f3d52d28584ab4466a501`. Every retained model/config file was hash checked. The existing isolated environment reported Torch 2.9.1+cpu, torchvision 0.24.1+cpu, Transformers 4.57.6, and Pillow 12.3.0. CPU-only build and parameter devices were required; CUDA visibility, implicit token lookup, and Hugging Face network access were disabled. No weights or packages were downloaded.

Model preprocessing and forward settings match the original helper: `use_fast=False`, pinned checkpoint processor `longest_edge=800`, explicit compatibility keys `shortest_edge=800,longest_edge=800`, deterministic algorithms, two intra-op threads, one inter-op thread, CPU eval and `torch.inference_mode`. The model sees pixels only. Each crop produces one forward; thresholds 0.3/0.5/0.7 reuse its complete 125 raw logits, normalized boxes and seven-class distributions. Every threshold view and conservative topology is rebuilt with the unchanged `p003_structure_geometry.project/topology` helpers. These are experimental row/column/span policies, not the complete official TATR postprocessor or calibrated correctness probabilities.

All 80 forwards completed successfully. All 240 threshold views reconstructed exactly. Geometry initialization is separately measured, including imports/model load, and took 3.086 wall s / 3.181 CPU s with sampled peak RSS 383,279,104 bytes. There is no separate warmup forward. Thus the first crop includes any cold inference setup.

| Acquisition size | CPU forwards | Forward scopes wall s | Forward scopes CPU s | Maximum sampled worker RSS bytes |
|---|---:|---:|---:|---:|
| 640 | 19 | 6.094 | 11.762 | 811,671,552 |
| 1024 | 24 | 7.729 | 14.933 | 811,679,744 |
| 1280 | 37 | 11.991 | 22.898 | 811,556,864 |

The existing root-owned `p003_structure_place.place` implementation is reused exactly for `overlap_margin`, `max_overlap`, and `center`. Source ID ownership is disjoint within each acquisition arm, and cross-arm candidates are never combined. `overlap_margin` requires best word-area overlap≥0.8 and margin≥0.15; `max_overlap` requires positive overlap and margin>1e-9; `center` requires a unique half-open anchor hit. Spans and complete rectangular tiling are validated before assignment. All participants in overlapping predicted table geometry are refused, with their source IDs unresolved; no score-ranked winner survives. Missing/refused topology likewise leaves source unresolved. Word-height probabilities, generated cell strings, and gold routing are absent.

| Acquisition | Threshold | Retained tables | Assigned IDs, overlap_margin | Assigned IDs, max_overlap | Assigned IDs, center | Conflicting table indices per policy |
|---|---:|---:|---:|---:|---:|---:|
| 640 | 0.3 | 16 | 653 | 743 | 743 | 0 |
| 640 | 0.5 | 18 | 950 | 1,874 | 1,874 | 0 |
| 640 | 0.7 | 18 | 1,034 | 1,874 | 1,874 | 0 |
| 1024 | 0.3 | 20 | 861 | 1,005 | 1,005 | 0 |
| 1024 | 0.5 | 21 | 1,070 | 2,116 | 2,116 | 0 |
| 1024 | 0.7 | 23 | 1,343 | 2,329 | 2,329 | 0 |
| 1280 | 0.3 | 30 | 934 | 2,481 | 2,475 | 3 |
| 1280 | 0.5 | 33 | 1,173 | 2,847 | 2,841 | 3 |
| 1280 | 0.7 | 31 | 1,166 | 2,776 | 2,771 | 5 |

These are source-only prediction counts, not cell/table scores or a selected quality winner. Some pages have no proposals; their source is fully unresolved rather than an inference error. All 432 output states passed the existing strict validator and exact source-ID Counter conservation check. Every source ID appears once, assigned or unresolved, with physical duplicates retained. Source-conserving assembly preserves retained literal words, which can still be wrong or incomplete OCR/extraction. More assigned IDs do not establish more correct cells.

Parent source authentication/rendering/crop encoding took 11.453 wall s / 11.352 process CPU s with lifetime peak RSS 539,156 KiB. Offline placement/projection replay and writing 432 page records took 29.562 wall s / 29.329 CPU s, also with lifetime peak RSS 539,156 KiB. Parent peak measurements use `getrusage` with no sampling and include imports; preparation and placement timers exclude imports. Model worker CPU is `process_time`; own RSS uses `/proc/self/statm` every 100 ms plus endpoints and lifetime `getrusage`. Initialization and each crop are distinct worker scopes; PNG/JPEG preparation and output JSON writing are outside forward scopes. Parent/worker peaks must not be summed. Other campaign workers may contend; execution order is frozen page, acquisition 640/1024/1280, then original detector box order. This is not an uncontended throughput estimate.

The final ignored archive is `bench/results/pdf-master-artifacts/pipeline-p003/structure-yolo-resolutions-v1` in the main workspace: 625 files totaling 152,334,454 bytes. It contains complete sources, all ownership/context receipts and 80 JPEGs, 80 raw geometry files, and 432 placement outputs. Before scoring, root must independently approve the ten archived helper hashes, including the two new modules and existing exact geometry/placement/assembly/crop dependencies. Archived Python is never executed for authentication. Independent scoring should reauthenticate source and YOLO authorities, reconstruct inputs/ownership/raw-query views/placements, preserve all 27 treatments and 16 pages, and separate acquisition coverage from semantic table admission and correct cell extraction.

| Receipt | SHA-256 |
|---|---|
| `source/manifest.json` | `78f29990652232e7288ce3f895afbe5ef279385d5fdc7ee0b95feb76c255dd6a` |
| `geometry/report.json` | `9c6419b7549cbd133aae03ef536be8a80f41414cb310b705a157827140c032ec` |
| `placement/report.json` | `6011fb0ca7540e66f82f7030c8540661b5e3ce67d692543ae86c2623c017f71a` |
| Canonical sorted file inventory | `1af158f5780b9349ec4fc86de0595cd035ef852e6a2fc1d7eb77cb4ea65947dd` |

Four focused tests cover complete unique ownership, unresolved contested centers despite unequal confidence, physical duplicate strings, explicit crossing/context records, negative/no-proposal inventory, and exact-boundary ties. Ruff and new-module mypy passed. No shared runtime or existing source module was modified; the root-owned placement file was copied only as an unstaged dependency. Fresh confirmation remains untouched.
