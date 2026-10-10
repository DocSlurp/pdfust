# Standalone partial-table salvage on natural16

The helper specification and twelve synthetic tests were frozen at `20b87cc` before reading DEV references. This is an offline secondary artifact experiment. It leaves strict complete-page extraction, all original errors, provider responses, costs and primary scores unchanged. No inference, retry, clipping, padding, text rewrite or confidence selection was performed.

Only complete valid outer JSON from one normally completed `stop`/`end_turn` response without refusal is eligible. Each original table is parsed independently through the unchanged strict vision adapter and original crop viewport, mapping to page display coordinates. Invalid tables are quarantined whole. A page-global positive-area overlap graph includes all valid tables across all crops; every member of each conflicting component is quarantined. Only isolated valid tables remain, in original response/table order. Aggregate admission refuses the entire isolated set, never a convenient subset. Missing or abnormal replies contribute no tables; unrelated complete crop replies may remain explicitly partial evidence. Every helper output is `status=partial`, `complete_page=false`, `source_conserved=false` and `coverage=partial_unverified`, even if no quarantine occurred.

All sixteen intended pages remain in each secondary fixed-reference denominator: 53 tables and 2,333 anchor cells. The unchanged scorer receives an evaluation-only projection of validated partial inventories; its table metrics do not relabel partial processor outputs as complete-page success. There are no new successful page counts, pages/minute or pages/USD productivity claims.

| Control | Original errors / 16 | Partial pages containing tables / 16 | Primary → secondary exact cells | Primary → secondary reference-exact tables | Primary → secondary extras | Original reported API USD |
|---|---:|---:|---:|---:|---:|---:|
| Sonnet crops1024 | 0 | 11 | 982 → 982 | 5 → 5 | 0 → 0 | 0.230508 |
| Hybrid Sonnet1024 vision | 1 | 11 | 289 → 918 | 4 → 5 | 0 → 1 | 0.222808 |
| Haiku crops1024 | 2 | 10 | 687 → 697 | 4 → 5 | 3 → 3 | 0.0090984 |
| Haiku whole2048q50 serial | 2 | 12 | 208 → 255 | 2 → 2 | 4 → 4 | 0.0117628 |
| Haiku whole2048q50 workers4 | 3 | 12 | 216 → 263 | 4 → 4 | 3 → 5 | 0.0110033 |

The hybrid control recovers 629 exact cells on its originally failed dense page, after quarantining both overlapping tables, but admits one extra table. Its original error remains an error. Standalone Sonnet crops gain nothing because its retained tables already passed atomic admission. Haiku crops gain ten cells and one reference-exact table from complete unaffected replies; serial whole-page Haiku gains 47 cells without another exact table. Workers4 whole-page Haiku also gains 47 cells, but admits two extra tables. Its extra-table total rises from three to five. This is evidence for retaining reviewable partial artifacts, not for weakening complete-page validation or automatic adoption.

All four negative pages remain in the analysis. Negative false-positive pages stay unchanged: zero for both Sonnet controls and Haiku crops, one for each whole-page Haiku control. New extras occur on positive pages. Partial evidence can therefore still contain incorrect tables even when every retained matrix passes strict syntax and geometry validation.

| Control | Stratum | Exact cells: primary → secondary | Reference-exact tables: primary → secondary | Secondary missing tables | Secondary extras |
|---|---|---:|---:|---:|---:|
| Sonnet crops1024 | dense2 | 692 → 692 | 1 → 1 | 26 | 0 |
| Sonnet crops1024 | remaining14 | 290 → 290 | 4 → 4 | 0 | 0 |
| Hybrid Sonnet1024 vision | dense2 | 0 → 629 | 0 → 1 | 29 | 1 |
| Hybrid Sonnet1024 vision | remaining14 | 289 → 289 | 4 → 4 | 0 | 0 |
| Haiku crops1024 | dense2 | 416 → 416 | 0 → 0 | 30 | 3 |
| Haiku crops1024 | remaining14 | 271 → 281 | 4 → 5 | 2 | 0 |
| Haiku whole2048q50 serial | dense2 | 0 → 0 | 0 → 0 | 39 | 2 |
| Haiku whole2048q50 serial | remaining14 | 208 → 255 | 2 → 2 | 3 | 2 |
| Haiku whole2048q50 workers4 | dense2 | 0 → 0 | 0 → 0 | 38 | 3 |
| Haiku whole2048q50 workers4 | remaining14 | 216 → 263 | 4 → 4 | 3 | 2 |

The hybrid natural screen contains zero retained native tables, so its secondary numbers above refer only to the image-transcribed vision child. They are not mixed-provenance source-conserved outputs. The two dense pages have 39 reference tables and 1,972 cells; the remaining fourteen include four negatives, 14 reference tables and 361 cells.

| Intended page ID | Sonnet crops: primary → partial exact cells | Hybrid vision | Haiku crops | Haiku whole serial | Haiku whole workers4 |
|---|---:|---:|---:|---:|---:|
| `p1bfa52a41a5e15015698` | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| `p6ef5d3c5c2edb1c109c4` | 58 → 58 | 58 → 58 | 58 → 58 | 0 → 47 | 0 → 47 |
| `p391ea102f48e27fcdd65` | 5 → 5 | 4 → 4 | 13 → 13 | 8 → 8 | 8 → 8 |
| `p9f92a30432da612d1bcc` | 22 → 22 | 22 → 22 | 0 → 10 | 8 → 8 | 8 → 8 |
| `p656361df32bd7d69a39e` | 11 → 11 | 11 → 11 | 25 → 25 | 17 → 17 | 25 → 25 |
| `p98d10ef50dee4b24506a` | 692 → 692 | 0 → 629 | 416 → 416 | 0 → 0 | 0 → 0 |
| `pc848c2a56527f81021a7` | 22 → 22 | 22 → 22 | 22 → 22 | 22 → 22 | 22 → 22 |
| `pc9c4bcc7f4f2a5dc3bab` | 68 → 68 | 68 → 68 | 68 → 68 | 68 → 68 | 68 → 68 |
| `p1e230b0fd05df7dd5e23` | 4 → 4 | 4 → 4 | 4 → 4 | 4 → 4 | 4 → 4 |
| `pda95432063a8a20bbe01` | 1 → 1 | 1 → 1 | 0 → 0 | 0 → 0 | 0 → 0 |
| `pe87ca2d41151f28dc44c` | 81 → 81 | 81 → 81 | 81 → 81 | 81 → 81 | 81 → 81 |
| `pf012d6adb9592dab9a13` | 18 → 18 | 18 → 18 | 0 → 0 | 0 → 0 | 0 → 0 |
| `p27ec5aaca0dd08c90360` | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| `p9cc5ebfad2ee46a13b5e` | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| `pdb4e1fa3babeca265abb` | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| `p42049db34e230ce77d75` | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |

All 80 per-page partial outputs, original parent/vision statuses, quarantines, conflict components, table origins and scorer details are retained in ignored `partial-salvage-audit.json`. Complete normal-stop successful prefixes on failed pages appear only in these explicitly secondary partial inventories. Neither baseline output files nor original charges/run resource records were overwritten. Every original request attempt remains represented by the retained baseline all-attempt ledger cost summary; this reuse is neither a provider cache hit nor a new paid run.

Offline audit wall 0.685743 s; process CPU 0.683309 s; lifetime kernel maximum RSS 440,488 KiB. Platform: Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44; Python 3.14.7. One CPU process, no subprocesses. `perf_counter`/`process_time` exclude imports; `resource.getrusage` peak RSS includes imports and was not sampled. No network, credentials, GPU or protected corpus access occurred.

Frozen helper SHA-256: `0fd61025a8b52aee1e120e76cab208877fa8bb3a99ae407fe02cbb693e675314`.
Dataset SHA-256: `68d1800d4c7f83dd0aeeadeab6362edc84aa7aaa56c1c1a740ee9fafb90b8c2d`.
Retained audit artifact SHA-256: `3d5d84496dbee60fbab675178b0726eee1ebb789643608de0e3274d8763ed3b3`.
Retained offline script SHA-256: `cc794c0ca1d91ea9efb65b8b457804c2baf31e34feae5e71cb7a4c83f86f8f39`.

| Input | SHA-256 |
|---|---|
| `screens/natural16/manifest.json` | `be1cc3788068e7354586863270627ce20d19926a7ee42c1c7903ca4c87b7d6b3` |
| `screens/natural16/private-targets.json` | `3dd46b62b4726f482f8ad5b9bf4c34e45f15efe5ad3d02ab7378fb9ec05de5b0` |
| `natural16-vision-crops-sonnet-1024/report.json` | `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57` |
| `natural16-vision-crops-sonnet-1024/verified-evaluation.json` | `3284aecced1ac8d6b128b3da08472d4e804eee9838aa213483c8e7d5801e6d65` |
| `natural16-hybrid-sonnet-1024/report.json` | `34e39985b127e3ecced418a6a18b7e4d791db527dd21075a83821b09afd77573` |
| `natural16-hybrid-sonnet-1024/verified-evaluation.json` | `bd5d96ea8e0ec6b7c1713665d1f4ca195f5fe67ae70866990c59f3ae686cdfc4` |
| `natural16-vision-crops-haiku-1024/report.json` | `41cb5ce1525c7b6230a6adbfc69c2aea2b1c27ad172f11a51364dbea75bf85b3` |
| `natural16-vision-crops-haiku-1024/verified-evaluation.json` | `7c4a0f31467bf9ba27a1d24da73cf072c846dea498991a7843b43dfea70261f8` |
| `natural16-vision-haiku-2048-q50/report.json` | `2e773a8e1d95d28fe59f9f533d30949269c17c9b517f92b1a1ebdc7e287d8121` |
| `natural16-vision-haiku-2048-q50/verified-evaluation.json` | `af4986271fc1b602d6409a4b4889ec2a32b4074f8ed3393a211acc06d64bfe01` |
| `natural16-vision-haiku-2048-q50-workers4/report.json` | `1db6aa25a8c65c26553220a98228df72fc11e57bff2922cf524b601492a7b864` |
| `natural16-vision-haiku-2048-q50-workers4/verified-evaluation.json` | `367866dbb0acc092c2b53c040ab78ec0e382cc37ae9eab89f5000ede586f1e60` |

Every input was rehashed at audit completion and remained unchanged. Each saved authoritative evaluation attests its exact retained report hash. The ignored script reproduces the audit after merging the helper:

```sh
PYTHONPATH=. python bench/results/pdf-master-artifacts/pipeline-p002/partial-salvage-audit.py
```
