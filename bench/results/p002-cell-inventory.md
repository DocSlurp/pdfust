# Optimistic complete-cell string inventory on natural16

The metric and five synthetic tests were frozen in `90a7704` before corpus references were opened. This offline diagnostic consumes each normalized complete anchor-cell string once in a page-wide multiset intersection. It uses authoritative NFC and Unicode-whitespace normalization, preserving case, punctuation and complete strings. It ignores table, row, column, spans and geometry. Covered merged slots are excluded. Empty anchors are reported separately. Failed pages contribute zero, including successful prefixes. Primary exact-coordinate scores remain unchanged.

All sixteen intended DEV pages are retained for each of four fixed completed controls. The dense pair has 1,972 anchors (1,947 nonempty); the remaining fourteen have 361 (345 nonempty), including four negatives. Total reference anchors are 2,333, including 41 empty anchors.

| Control | Stratum | Admitted / intended | Primary exact anchors | Nonempty bag matches | Empty bag matches | Optimistic total | Gap over primary |
|---|---|---:|---:|---:|---:|---:|---:|
| crops-sonnet-1024 | all16 | 16/16 | 982 | 1112 | 34 | 1146 | 164 |
| crops-sonnet-1024 | dense2 | 2/2 | 692 | 838 | 18 | 856 | 164 |
| crops-sonnet-1024 | remaining14 | 14/14 | 290 | 274 | 16 | 290 | 0 |
| crops-haiku-1024 | all16 | 14/16 | 687 | 788 | 25 | 813 | 126 |
| crops-haiku-1024 | dense2 | 2/2 | 416 | 524 | 18 | 542 | 126 |
| crops-haiku-1024 | remaining14 | 12/14 | 271 | 264 | 7 | 271 | 0 |
| sonnet-2048-q50 | all16 | 16/16 | 540 | 507 | 41 | 548 | 8 |
| sonnet-2048-q50 | dense2 | 2/2 | 247 | 230 | 25 | 255 | 8 |
| sonnet-2048-q50 | remaining14 | 14/14 | 293 | 277 | 16 | 293 | 0 |
| opus-2048-q50 | all16 | 16/16 | 300 | 559 | 40 | 599 | 299 |
| opus-2048-q50 | dense2 | 2/2 | 7 | 282 | 24 | 306 | 299 |
| opus-2048-q50 | remaining14 | 14/14 | 293 | 277 | 16 | 293 | 0 |

Every placement-free gain occurs on the dense pair. Sonnet crops gain at most 164 anchors (16.7% over 982 primary exact anchors), Haiku crops 126 (18.3% over 687), Sonnet whole-page 8 (1.5% over 540), and Opus whole-page 299 (99.7% over 300). Remaining-fourteen inventory totals equal primary exact counts in every control. Opus therefore has the strongest placement-loss signal; crop outputs also retain some complete correct strings that current placement does not credit.

This is an optimistic bound on rearranging already emitted complete strings, not a feasible repair result or proof of transcription correctness. Repeated labels, extra tables, wrong spans, cross-table string coincidence and absent geometry can inflate this inventory. It neither splits nor joins cells, recovers absent tables, repairs failed outputs, nor measures all character-level transcription. Even the best inventory reaches only 1,146/2,333 anchors: dense detection, coverage and transcription remain substantial bottlenecks. A next experiment could freeze a generic source-image placement repair before evaluating it; this diagnostic must never supply inference evidence, select a prompt, or tune a case-specific rule.

| Control | Predicted nonempty anchors | Predicted empty anchors | Matched empties / 41 |
|---|---:|---:|---:|
| crops-sonnet-1024 | 1261 | 35 | 34 |
| crops-haiku-1024 | 894 | 79 | 25 |
| sonnet-2048-q50 | 621 | 53 | 41 |
| opus-2048-q50 | 694 | 52 | 40 |

Measured on Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44, Python 3.14.7, one CPU process and no network/model calls: audit wall 0.035042 s, process CPU 0.034897 s, lifetime maximum RSS 440,488 KiB. CPU/wall cover the audit after imports; RSS includes imported benchmark dependencies. `time.perf_counter`, `time.process_time` and kernel `resource.getrusage` were used without sampling or subprocesses. This measures offline bookkeeping, not inference performance.

Retained artifact: `bench/results/pdf-master-artifacts/pipeline-p002/cell-inventory-audit.json` (ignored), including all 64 per-page observations, grouping totals, metric specification and every input hash. Each verified evaluation attests its exact report hash; independently verified error pages suppress prefixes. All inputs were rehashed after the audit and remained unchanged.

Dataset SHA-256: `68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.
Audit artifact SHA-256: `dea6dbe8797ef432a58c642e04c2a77edc83b253ce625acf3865c48fe0a7ddb6`.

| Frozen input | SHA-256 |
|---|---|
| `screens/natural16/manifest.json` | `be1cc3788068e7354586863270627ce20d19926a7ee42c1c7903ca4c87b7d6b3` |
| `screens/natural16/private-targets.json` | `3dd46b62b4726f482f8ad5b9bf4c34e45f15efe5ad3d02ab7378fb9ec05de5b0` |
| `natural16-vision-crops-sonnet-1024/report.json` | `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57` |
| `natural16-vision-crops-sonnet-1024/verified-evaluation.json` | `3284aecced1ac8d6b128b3da08472d4e804eee9838aa213483c8e7d5801e6d65` |
| `natural16-vision-crops-haiku-1024/report.json` | `41cb5ce1525c7b6230a6adbfc69c2aea2b1c27ad172f11a51364dbea75bf85b3` |
| `natural16-vision-crops-haiku-1024/verified-evaluation.json` | `7c4a0f31467bf9ba27a1d24da73cf072c846dea498991a7843b43dfea70261f8` |
| `natural16-vision-sonnet-2048-q50/report.json` | `b37575ca7d8a850e73b6cb397f288a4d43244888f151cad8d096f71ace44ac0b` |
| `natural16-vision-sonnet-2048-q50/verified-evaluation.json` | `6a95fa75d8e64d0ce323488519a1c58fa47ee576124a188031b34f89029504a5` |
| `natural16-vision-opus-2048-q50/report.json` | `840cd66c3e428376b0b0ffbb0f47337be3146c38e48379f4007432b3ed81179b` |
| `natural16-vision-opus-2048-q50/verified-evaluation.json` | `4d5ed827a057cdb251caadaa21a128aad009077932e9d7783b874faa6ffcaa80` |

Reproduce with the root virtualenv from the repository:

```sh
python -m bench.generalization_cell_inventory --artifact-root bench/results/pdf-master-artifacts/pipeline-p002 --output bench/results/pdf-master-artifacts/pipeline-p002/cell-inventory-audit.json
```
