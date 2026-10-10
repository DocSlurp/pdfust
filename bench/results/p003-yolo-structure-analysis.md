# P003 matched YOLO acquisition and CPU structure placements

Larger YOLO acquisition crops recover additional source-owned cells after CPU Table Transformer geometry. The 1,280 arm obtains 317–451 strict cells with maximum-overlap placement across the three frozen structure thresholds, compared with 191–204 at size 640. Every one of these arms recovers three complete tables. This is an observed DEV treatment family, without choosing a threshold or page-specific winner for execution or fresh confirmation.

All 27 treatments preserve the full 16 pages, 53 reference tables and 2,333 cells, including four negatives. Every one of the 80 CPU crop forwards completed; no generated cell strings, historical pipeline fallback or paid calls enter these predictions.

| YOLO size | Structure threshold | Source placement | Strict | Text | Structure | Complete | Missing | Extra | Negative FP /4 |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 640 | 0.3 | overlap_margin | 176 | 178 | 331 | 1 | 40 | 3 | 3 |
| 640 | 0.3 | max_overlap | 191 | 193 | 331 | 3 | 40 | 3 | 3 |
| 640 | 0.3 | center | 191 | 193 | 331 | 3 | 40 | 3 | 3 |
| 640 | 0.5 | overlap_margin | 189 | 191 | 596 | 1 | 38 | 3 | 3 |
| 640 | 0.5 | max_overlap | 204 | 206 | 596 | 3 | 38 | 3 | 3 |
| 640 | 0.5 | center | 204 | 206 | 596 | 3 | 38 | 3 | 3 |
| 640 | 0.7 | overlap_margin | 191 | 193 | 593 | 1 | 38 | 3 | 3 |
| 640 | 0.7 | max_overlap | 202 | 204 | 593 | 3 | 38 | 3 | 3 |
| 640 | 0.7 | center | 202 | 204 | 593 | 3 | 38 | 3 | 3 |
| 1024 | 0.3 | overlap_margin | 178 | 180 | 434 | 1 | 39 | 6 | 1 |
| 1024 | 0.3 | max_overlap | 193 | 195 | 434 | 3 | 39 | 6 | 1 |
| 1024 | 0.3 | center | 193 | 195 | 434 | 3 | 39 | 6 | 1 |
| 1024 | 0.5 | overlap_margin | 178 | 180 | 678 | 1 | 38 | 6 | 1 |
| 1024 | 0.5 | max_overlap | 193 | 195 | 678 | 3 | 38 | 6 | 1 |
| 1024 | 0.5 | center | 193 | 195 | 678 | 3 | 38 | 6 | 1 |
| 1024 | 0.7 | overlap_margin | 290 | 300 | 808 | 1 | 36 | 6 | 1 |
| 1024 | 0.7 | max_overlap | 306 | 316 | 808 | 3 | 36 | 6 | 1 |
| 1024 | 0.7 | center | 306 | 316 | 808 | 3 | 36 | 6 | 1 |
| 1280 | 0.3 | overlap_margin | 226 | 229 | 1088 | 1 | 30 | 7 | 0 |
| 1280 | 0.3 | max_overlap | 317 | 319 | 1088 | 3 | 30 | 7 | 0 |
| 1280 | 0.3 | center | 317 | 319 | 1088 | 3 | 30 | 7 | 0 |
| 1280 | 0.5 | overlap_margin | 344 | 355 | 1197 | 1 | 28 | 8 | 0 |
| 1280 | 0.5 | max_overlap | 438 | 448 | 1197 | 3 | 28 | 8 | 0 |
| 1280 | 0.5 | center | 438 | 449 | 1197 | 3 | 28 | 8 | 0 |
| 1280 | 0.7 | overlap_margin | 356 | 365 | 1175 | 1 | 30 | 8 | 0 |
| 1280 | 0.7 | max_overlap | 451 | 459 | 1175 | 3 | 30 | 8 | 0 |
| 1280 | 0.7 | center | 451 | 460 | 1175 | 3 | 30 | 8 | 0 |

The predeclared dense-two versus other-fourteen sensitivity explains the source of the gain; it does not replace the complete cohort above. Those same two dense pages contain 1,972 reference cells. At threshold 0.7/max-overlap, size 1280 adds 247 correct dense-page cells while the other 14 remain at 204. Size640 has zero correct cells on the dense pages. Complete-table recovery remains concentrated outside the dense pair.

| YOLO size | Structure threshold | Dense2 strict /1,972 | Other14 strict /361 |
| ---: | ---: | ---: | ---: |
| 640 | 0.3 | 0 | 191 |
| 640 | 0.5 | 0 | 204 |
| 640 | 0.7 | 0 | 202 |
| 1024 | 0.3 | 2 | 191 |
| 1024 | 0.5 | 2 | 191 |
| 1024 | 0.7 | 106 | 200 |
| 1280 | 0.3 | 126 | 191 |
| 1280 | 0.5 | 235 | 203 |
| 1280 | 0.7 | 247 | 204 |

At size 1280, no negative page receives a table, but the 0.5/0.7 placements still produce eight extra tables on positive pages and miss 28/30 reference tables. This does not establish semantic admission correctness. All overlapping geometry participants are refused; no arbitrary positive winner is retained. Each complete source ID is placed once or remains explicitly unresolved. Unique word-center ownership is frozen separately for each acquisition size; multiple-center hits remain unresolved, crossing whole-word boxes are disclosed, and incidental pixel context never gains ownership.

| Acquisition size | Fresh structure forwards | Structure inference wall s | Structure inference CPU s | Max sampled worker RSS MiB |
| ---: | ---: | ---: | ---: | ---: |
| 640 | 19 | 6.094 | 11.762 | 774.1 |
| 1024 | 24 | 7.729 | 14.933 | 774.1 |
| 1280 | 37 | 11.991 | 22.898 | 774.0 |

The same pinned structure checkpoint and processor 800, two CPU intra-op threads and one inter-op thread are used for all 80 fresh forwards. Raw logits and normalized geometry are frozen once per crop; all three thresholds reuse that forward. Structure initialization is separately 3.086 s wall / 3.181 s CPU. Source/raster/crop preparation is 11.453 s wall / 11.352 s parent CPU; all 432 offline placements are 29.562 s wall / 29.329 s parent CPU. Preparation/placement lifetime parent RSS is 526.52 MiB, measured with `getrusage` and not an isolated sampled working-set peak. Worker RSS uses 100 ms `/proc/self/statm` samples plus endpoints and excludes the parent; maxima must not be summed. Original OCR/source extraction, YOLO inference, initialization, and historical generation costs remain separate. No full-pipeline throughput or APIUSD rate is claimed.

Before loading references, the independent analyzer authenticated the external 10-file Git authority, original b773 source authority and 05f YOLO authority; regenerated all 16 original source rasters and all 80 continuous JPEG crop bytes; rebuilt complete per-size source/context/crossing/overlap inventories; checked pinned model/config bytes; reprojected all 240 threshold views; and rebuilt all 432 whole-page source-owned states. It also checked each of 125 raw queries per crop, raw-logit softmax probabilities, pinned class labels, output hashes and reported counts. Recorded raw outputs are replayed, not new model inference. The one reviewed historical vision helper exception excludes only unused transcription-request/process branches; all called functions/constants retain exact AST. Archived code is never executed.

Source manifest SHA-256 `78f29990652232e7288ce3f895afbe5ef279385d5fdc7ee0b95feb76c255dd6a`; geometry report `9c6419b7549cbd133aae03ef536be8a80f41414cb310b705a157827140c032ec`; placement report `6011fb0ca7540e66f82f7030c8540661b5e3ce67d692543ae86c2623c017f71a`. Complete per-page scores/provenance stay in ignored `structure-yolo-resolutions-v1/independent-evaluation.json`. No fresh confirmation or protected heldout access occurred.
