# P002 multiscale partial salvage

This secondary offline diagnostic applies the existing frozen partial-salvage helper unchanged to all 16 intended pages of each completed multiscale control. Historical atomic failures, provider charges, missing requests, and primary scores remain unchanged. Every diagnostic output remains `partial`, never a complete-page success or source-conserved extraction. There are no fresh inference, throughput, pages-per-dollar, or provider-cache claims.

The unchanged helper was frozen in `20b87cc`. Explicit named-control support and retention tests were committed in `13d2675` before this derivative scoring. Only complete outer JSON from normal-stop responses is eligible. Each table passes the unchanged strict adapter independently; invalid tables are quarantined whole. A positive-area overlap graph across all tables and crops removes every member of each conflicting component. Isolated strict-valid tables remain. No clipping, padding, text rewriting, retry, or reference-selected rules are applied. Crop-local normalized coordinates are mapped through each retained global viewport before cross-crop overlap checks.

Both runs use the same fixed natural16 references and all 2333 reference anchor cells across 53 tables. Failed prefixes are shown only as explicit partial evidence; their original complete-page status is retained. Source-only proposal coverage remains unverified, including proposals never submitted after a preceding error. References are used only by the secondary scorer.

| Retained control | Exact cells: primary → partial | Structure cells: primary → partial | Complete tables: unchanged | Extra tables: primary → partial | Original errors: unchanged |
| --- | ---: | ---: | ---: | ---: | ---: |
| Multiscale Sonnet crops 1024 | 293 → 613 / 2333 | 361 → 991 / 2333 | 4 / 53 | 0 → 3 | 2 |
| Multiscale Haiku crops 1024 | 581 → 581 / 2333 | 829 → 829 / 2333 | 2 / 53 | 2 → 2 | 1 |

Sonnet's entire gain is in dense2: exact cells 0 → 320 / 1972, structure 0 → 630, missing tables 39 → 27, and extra tables 0 → 3. No dense table becomes complete. The other 14 pages remain 293/361 exact cells, 4 complete tables, and zero extra tables. The partial gain is useful evidence, but the three added unmatched tables show that recovery is not a precision-preserving replacement for atomic admission.

Haiku dense2 remains 299/1972 exact cells and two extra tables. Its remaining14 remains 282/361 exact cells, two complete tables, and no extras. Its failed response contains no isolated valid table to recover.

Sonnet quarantines three invalid tables, six members of overlap components, and five ineligible missing responses. Its first dense page retains nine isolated tables from five submitted calls; five further detector proposals remain `not_requested`. Its second dense page retains six isolated tables from two submitted calls. Haiku quarantines one invalid table and one ineligible missing response; one proposal remains `not_requested` on the failed page. None of these missing requests is invented or counted as inferred output.

All intended pages follow, including negative controls and successful pages. `E` means original atomic error; `O` means original atomic success. The cell columns are secondary partial exact anchor matches, not a changed primary score. Full per-page canonical partial outputs, original calls, proposal counts, every region's index/status/viewport/detector box/request and response presence, and quarantine reasons are retained in `multiscale-partial-review/audit.json`.

| Page ID | Sonnet original | Sonnet partial tables / exact cells / extras | Sonnet unsubmitted | Haiku original | Haiku partial tables / exact cells / extras | Haiku unsubmitted |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `p1bfa52a41a5e15015698` | E | 9 / 58 / 2 | 5 | O | 6 / 161 / 1 | 0 |
| `p6ef5d3c5c2edb1c109c4` | O | 2 / 58 / 0 | 0 | O | 2 / 58 / 0 | 0 |
| `p391ea102f48e27fcdd65` | O | 2 / 9 / 0 | 0 | O | 2 / 11 / 0 | 0 |
| `p9f92a30432da612d1bcc` | O | 2 / 22 / 0 | 0 | O | 2 / 19 / 0 | 0 |
| `p656361df32bd7d69a39e` | O | 2 / 11 / 0 | 0 | E | 0 / 0 / 0 | 1 |
| `p98d10ef50dee4b24506a` | E | 6 / 262 / 1 | 0 | O | 5 / 138 / 1 | 0 |
| `pc848c2a56527f81021a7` | O | 1 / 22 / 0 | 0 | O | 1 / 22 / 0 | 0 |
| `pc9c4bcc7f4f2a5dc3bab` | O | 1 / 68 / 0 | 0 | O | 1 / 68 / 0 | 0 |
| `p1e230b0fd05df7dd5e23` | O | 1 / 4 / 0 | 0 | O | 1 / 4 / 0 | 0 |
| `pda95432063a8a20bbe01` | O | 1 / 0 / 0 | 0 | O | 1 / 0 / 0 | 0 |
| `pe87ca2d41151f28dc44c` | O | 1 / 81 / 0 | 0 | O | 1 / 81 / 0 | 0 |
| `pf012d6adb9592dab9a13` | O | 1 / 18 / 0 | 0 | O | 1 / 19 / 0 | 0 |
| `p27ec5aaca0dd08c90360` | O | 0 / 0 / 0 | 0 | O | 0 / 0 / 0 | 0 |
| `p9cc5ebfad2ee46a13b5e` | O | 0 / 0 / 0 | 0 | O | 0 / 0 / 0 | 0 |
| `pdb4e1fa3babeca265abb` | O | 0 / 0 / 0 | 0 | O | 0 / 0 / 0 | 0 |
| `p42049db34e230ce77d75` | O | 0 / 0 / 0 | 0 | O | 0 / 0 / 0 | 0 |

Original API charges remain USD 0.288916 for Sonnet's 25 calls and USD 0.0132065 for Haiku's 29 calls, including calls whose output failed strict admission. The original run wall/resource records are retained unchanged; no productivity measure is recomputed from partial tables.

The combined offline audit took 0.326 s wall and 0.325 s CPU, excluding imports. Linux `getrusage(RUSAGE_SELF)` lifetime peak RSS was 440488 KiB, including imports. This was one CPU process on Linux 7.2.5 with Python 3.14.7, no GPU, provider client, credentials, or network calls. Kernel RSS is a lifetime high-water mark without sampling. The audit helper's focused suite passed 23 tests, including preserved pending proposals and failed-page status; Ruff and scoped mypy passed.

```sh
python -m bench.generalization_partial_audit \
  --artifact-root bench/results/pdf-master-artifacts/pipeline-p002 \
  --control natural16-vision-multiscale-sonnet-1024 \
  --control natural16-vision-multiscale-haiku-1024 \
  --output bench/results/pdf-master-artifacts/pipeline-p002/multiscale-partial-review
```

The helper SHA-256 is `0fd61025a8b52aee1e120e76cab208877fa8bb3a99ae407fe02cbb693e675314`. All input identities are checked before scoring and rehashed at the end; original raw artifacts are preserved.

| Explicit input | SHA-256 |
| --- | --- |
| `natural16-vision-multiscale-haiku-1024/report.json` | `462848cd4730c2440de66b775f5778237eda109de64127dcb334ee0ff8f458cf` |
| `natural16-vision-multiscale-haiku-1024/verified-evaluation.json` | `891624f94c9f74256ae73d7971fa15cf273dea98e84950dc35f1743d5ac55c93` |
| `natural16-vision-multiscale-sonnet-1024/report.json` | `b031c36b7b6b852daebdddd0ea7d3e20a1a5a7590c3d96ea8200533197ed9985` |
| `natural16-vision-multiscale-sonnet-1024/verified-evaluation.json` | `809b66a757b82a661f83c006976d103c781a12894e06f099f18bd1ee07a54d11` |
| `screens/natural16/manifest.json` | `be1cc3788068e7354586863270627ce20d19926a7ee42c1c7903ca4c87b7d6b3` |
| `screens/natural16/private-targets.json` | `3dd46b62b4726f482f8ad5b9bf4c34e45f15efe5ad3d02ab7378fb9ec05de5b0` |
