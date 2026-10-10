# P001 completed pilot findings and paired-input audit

Completed-pilot snapshot: 2026-10-10T00:22:25+00:00; 31 completed pilot reports. The full-cohort wave and any unfinished jobs are excluded. This is an offline aggregate: no requests, credentials, ledger reads or source extraction were performed.

Sonnet and Opus each recover all 32 scored pilot pages: all 16 complete table matrices and span topologies, all 207 intended slots, and zero tables on all 16 negative pages. No completed control exceeds that measured quality. The DEV-selected PPLX gate with one conditional Sonnet review ties it, at lower observed request charges and elapsed time. This policy uses 256px images and different routing; it is not an equal-input comparison of PPLX against frontier models.

The compact comparison below can be copied into a README with its qualification paragraphs. Rates count exact scored pages, including correct negative pages, rather than merely emitted files. Every listed pilot emitted all 32 operational outputs; table positives and negative false positives remain visible so abstention on every page cannot masquerade as table recovery.

| Completed pilot policy | Exact table pages / 16 | Non-table FP / 16 | Exact pages / 32 | Calls | API USD | Wall s | Exact pages/min | Exact pages/USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sonnet assembly, 512px | 16/16 | 0/16 | 32/32 | 32 | 0.29151800 | 105.333 | 18.23 | 109.77 |
| Opus assembly, 512px | 16/16 | 0/16 | 32/32 | 32 | 0.56969600 | 147.610 | 13.01 | 56.17 |
| Haiku assembly, 512px | 16/16 | 3/16 | 29/32 | 32 | 0.01608840 | 119.940 | 14.51 | 1802.54 |
| PPLX gate + conditional Sonnet review, 256px | 16/16 | 0/16 | 32/32 | 27 | 0.01022948 | 31.330 | 61.28 | 3128.21 |
| PPLX relational gate, 256px | 16/16 | 1/16 | 31/32 | 27 | 0.00158094 | 35.200 | 52.84 | 19608.59 |
| Luna relational gate, 1024px | 16/16 | 1/16 | 31/32 | 27 | 0.00737830 (estimate) | 34.946 | 53.22 | 4201.51 |
| PPLX geometry text only | 16/16 | 4/16 | 28/32 | 32 | 0.00274844 | 39.257 | 42.80 | 10187.60 |
| Luna geometry text only | 15/16 | 3/16 | 28/32 | 32 | 0.00912300 (estimate) | 30.044 | 55.92 | 3069.17 |
| Flash geometry text only | 0/16 | 0/16 | 16/32 | 32 | 0.00528116 | 54.017 | 17.77 | 3029.64 |
| PPLX original assembly, 512px | 15/16 | 4/16 | 27/32 | 32 | 0.00313544 | 35.195 | 46.03 | 8611.23 |
| Luna original assembly, 512px | 15/16 | 4/16 | 27/32 | 32 | 0.01020390 (estimate) | 28.379 | 57.08 | 2646.05 |
| Flash original assembly, 512px | 5/16 | 0/16 | 21/32 | 32 | 0.00601627 | 60.507 | 20.82 | 3490.53 |

USD values use complete-run effective charges, including all attempted requests and reviews. Positive provider-reported charges are retained for PPLX, Flash and frontier models. Luna entries preserve provider-reported zero and use separately labeled catalog estimates. Local electricity, amortization and storage are unpriced. A rate is unknown when effective charges are unknown; no reservations are treated as actual charges. There are no missing results, malformed outputs or scoring errors in these completed pilots.

The review policy uses 26 PPLX calls (USD 0.00151548) plus one Sonnet call (USD 0.008714), totaling USD 0.01022948. The single review is 85.19% of its measured API charge. Both charges are counted. Its exact output rate is 61.2827 pages/min and 3128.2138 pages/USD; exact positive table-page rates are 30.6414/min and 1564.1069/USD. These are pilot observations from one serial run, not estimates of production throughput or unseen quality.

Paired-input audit:

| Pair | Same opaque page IDs | Identical literal source snapshots | Identical complete candidate collections | Identical rendered image hashes | Decoded questions, criteria and source state |
|---|---:|---:|---:|---:|---|
| Haiku / Sonnet | 32/32 | 32/32 | 32/32 | 32/32 | Identical 32/32 |
| Sonnet / Opus | 32/32 | 32/32 | 32/32 | 32/32 | Identical 32/32 |
| PPLX text / Luna text | 32/32 | 32/32 | 32/32 | No images | Identical 32/32 |
| Luna text / Flash text | 32/32 | 32/32 | 32/32 | No images | Identical 32/32 |
| PPLX oriented 256px / PPLX text | 32/32 | 32/32 | 32/32 | Different image availability | Image presence differs |
| Original PPLX 512px / Sonnet | 32/32 | 30/32 | 30/32 | 30/32 | Rotation/source preprocessing differs |
| Original Flash 512px / Sonnet | 32/32 | 30/32 | 30/32 | 30/32 | Rotation/source preprocessing differs |
| PPLX minimal gate / relational gate | 32/32 | 32/32 | 32/32 | 32/32 | Gate premise intentionally differs |

The three frontier arms have byte-equivalent decoded instructions, criteria, text/image state and request settings apart from the requested model ID. Each selects from the same source-derived complete alternatives using a strict choice-only JSON schema, a 1024-token output boundary and no assumed optional temperature or reasoning settings. They are matched candidate-selection controls, not unrestricted PDF extraction. All native decision-model text-only arms likewise have identical decoded questions, criteria and complete source state. Native decision and frontier chat transports differ; the chat wrapper preserves native instructions and criteria while adding strict JSON formatting instructions.

The frontier serving routes also differ: all Haiku and Sonnet calls report Azure; all Opus calls report Claude Platform on AWS. Served model IDs match their requested model IDs in those entries. Therefore wall and price comparisons describe the observed model/provider routes, not model compute in isolation. Requests were sequential, not interleaved repeated trials. Native decision adapters report different token conventions and probabilities, whereas frontier answers contain choices only; no artificial probabilities are created for the chat controls.

Rotation normalization changes two page snapshots/candidate sets relative to the original image pilots. The original cohort has one positive without an exact complete candidate; normalized arms make all 16 exact positive candidates available. Comparing their score improvement to an original unnormalized model arm confounds proposal geometry with model choice. Gate, repair, adaptive, reading-premise and conditional-review arms deliberately change policy or evidence, and are labeled pipeline comparisons.

For PPLX, the text-only normalized arm and the oriented 256px arm have identical snapshots and alternatives. Both obtain 16/16 exact positives and 4/16 false-positive negatives. Removing images lowers reported input tokens from 148,164 to 137,422 and charges from USD 0.00296328 to 0.00274844 (7.25% each), with wall 39.257s versus 40.689s. The matched text-only cross-model comparison shows that equal source/candidate data does not ensure equal model behavior: Flash emits no tables and misses all 16 positives; Luna misses one positive and admits three false-positive negatives; PPLX recovers all positives but admits four false positives. This pilot does not establish that images are generally unnecessary.

The original image scale sweep also has losses: PPLX remains 15/16 positives plus 4/16 false positives at 256/512/1024px; Luna rises from 15/16 plus 4/16 false positives at 256/512px to 15/16 plus 2/16 at 1024px; Flash changes from 3/16, 5/16, 6/16 positives at 256/512/1024px, with 0/16, 0/16, 1/16 false positives. Larger image preparation and token costs are measured in [the phase analysis](pipeline-perf-analysis.md).

All three completed frontier models recover the 16 complete positives; Haiku loses three negative pages to false-positive table admission. PPLX and Luna gate variants recover all positives but retain one false-positive negative. Reading-premise variants retain the same 31/32 exact-page result. The conditionally reviewed gate resolves that remaining pilot error with one independent Sonnet gate review. Its trigger (uncalibrated maximum decision score below 0.8 or score margin below 0.25) was selected during DEV exploration. These scores are not calibrated correctness probabilities; the trigger is not an independently validated production policy.

The conditional policy ties Sonnet/Opus quality on the pilot while costing about 28.5 times less than Sonnet and 55.7 times less than Opus. It has no quality improvement beyond their 32/32 result. The smaller pilot, post-observation policy selection, different image edge and fewer conditional requests prevent a general model superiority claim. The broader frozen full-cohort run is needed to examine failures beyond these selected pilot families; even that cohort is DEV and includes diagnostic-only natural documents.

Limits and verification: the pilot is 32 predefined repository-authored synthetic DEV pages (16 positives, 16 negatives), not a random natural-document sample or protected holdout. Matrix/spans references come from construction before extraction, but they are not independently adjudicated gold. Every frozen PDF hash, manifest-byte hash, complete source-record projection, target-ID inventory and successful retained Markdown/structure state passed the offline contract checks. Every retained result used opaque page IDs. Gold matrices, family metadata and pilot membership are scorer-only; inference requests contained source evidence and hypotheses. Source-ID conservation covers extracted words, not OCR completeness, missing Unicode mappings, visibility, correct reading order, prose/form/math semantics, images or document correctness.

Wall uses perf_counter and current-process CPU uses process_time. One runner process, concurrency 1, eight logical CPUs, Python 3.14.7 on Linux 7.2.5 Omarchy x86_64/glibc 2.44; current-process RSS is sampled every 100ms. Pipeline wall includes provider waiting, ledger/telemetry and output persistence. Remote resource use and separate provider compute are unmeasured. Resource overhead and changing client history affect these one-run rates.

<details>
<summary>All completed pilot controls, including wins and losses</summary>

| Completed pilot policy | Exact table pages / 16 | Non-table FP / 16 | Exact pages / 32 | Calls | API USD | Wall s | Exact pages/min | Exact pages/USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot-adaptive-luna | 10/16 | 4/16 | 22/32 | 18 | 0.00254760 (estimate) | 19.195 | 68.77 | 8635.58 |
| pilot-adaptive-pplx | 12/16 | 6/16 | 22/32 | 21 | 0.00079134 | 23.383 | 56.45 | 27800.95 |
| pilot-flash-1024 | 6/16 | 1/16 | 21/32 | 32 | 0.00675439 | 76.801 | 16.41 | 3109.09 |
| pilot-flash-256 | 3/16 | 0/16 | 19/32 | 32 | 0.00587970 | 60.302 | 18.90 | 3231.46 |
| Flash original assembly, 512px | 5/16 | 0/16 | 21/32 | 32 | 0.00601627 | 60.507 | 20.82 | 3490.53 |
| Haiku assembly, 512px | 16/16 | 3/16 | 29/32 | 32 | 0.01608840 | 119.940 | 14.51 | 1802.54 |
| Opus assembly, 512px | 16/16 | 0/16 | 32/32 | 32 | 0.56969600 | 147.610 | 13.01 | 56.17 |
| Sonnet assembly, 512px | 16/16 | 0/16 | 32/32 | 32 | 0.29151800 | 105.333 | 18.23 | 109.77 |
| pilot-gated-flash-512 | 10/16 | 0/16 | 26/32 | 30 | 0.00397845 | 56.202 | 27.76 | 6535.21 |
| Luna relational gate, 1024px | 16/16 | 1/16 | 31/32 | 27 | 0.00737830 (estimate) | 34.946 | 53.22 | 4201.51 |
| pilot-gated-pplx-minimal | 16/16 | 1/16 | 31/32 | 28 | 0.00162914 | 31.848 | 58.40 | 19028.44 |
| PPLX relational gate, 256px | 16/16 | 1/16 | 31/32 | 27 | 0.00158094 | 35.200 | 52.84 | 19608.59 |
| pilot-gated-reading-luna | 16/16 | 1/16 | 31/32 | 28 | 0.00969300 (estimate) | 27.640 | 67.29 | 3198.18 |
| pilot-gated-reading-pplx | 16/16 | 1/16 | 31/32 | 27 | 0.00212190 | 28.197 | 65.97 | 14609.55 |
| PPLX gate + conditional Sonnet review, 256px | 16/16 | 0/16 | 32/32 | 27 | 0.01022948 | 31.330 | 61.28 | 3128.21 |
| pilot-luna-1024 | 15/16 | 2/16 | 29/32 | 32 | 0.01209830 (estimate) | 31.430 | 55.36 | 2397.03 |
| pilot-luna-256 | 15/16 | 4/16 | 27/32 | 32 | 0.00971750 (estimate) | 32.919 | 49.21 | 2778.49 |
| Luna original assembly, 512px | 15/16 | 4/16 | 27/32 | 32 | 0.01020390 (estimate) | 28.379 | 57.08 | 2646.05 |
| pilot-oriented-pplx-256 | 16/16 | 4/16 | 28/32 | 32 | 0.00296328 | 40.689 | 41.29 | 9448.99 |
| pilot-pplx-1024 | 15/16 | 4/16 | 27/32 | 32 | 0.00352392 | 49.481 | 32.74 | 7661.92 |
| pilot-pplx-256 | 15/16 | 4/16 | 27/32 | 32 | 0.00306356 | 41.227 | 39.29 | 8813.28 |
| PPLX original assembly, 512px | 15/16 | 4/16 | 27/32 | 32 | 0.00313544 | 35.195 | 46.03 | 8611.23 |
| pilot-repair-flash-c1 | 10/16 | 5/16 | 21/32 | 17 | 0.00132099 | 26.471 | 47.60 | 15897.12 |
| pilot-repair-flash-c3 | 10/16 | 6/16 | 20/32 | 18 | 0.00189563 | 38.940 | 30.82 | 10550.58 |
| pilot-repair-luna-c1 | 10/16 | 5/16 | 21/32 | 21 | 0.00320450 (estimate) | 17.674 | 71.29 | 6553.28 |
| pilot-repair-luna-c3 | 10/16 | 6/16 | 20/32 | 19 | 0.00373390 (estimate) | 27.507 | 43.63 | 5356.33 |
| pilot-repair-pplx-c1 | 11/16 | 6/16 | 21/32 | 23 | 0.00101070 | 22.794 | 55.28 | 20777.68 |
| pilot-repair-pplx-c3 | 11/16 | 5/16 | 22/32 | 22 | 0.00114738 | 40.513 | 32.58 | 19174.12 |
| Flash geometry text only | 0/16 | 0/16 | 16/32 | 32 | 0.00528116 | 54.017 | 17.77 | 3029.64 |
| Luna geometry text only | 15/16 | 3/16 | 28/32 | 32 | 0.00912300 (estimate) | 30.044 | 55.92 | 3069.17 |
| PPLX geometry text only | 16/16 | 4/16 | 28/32 | 32 | 0.00274844 | 39.257 | 42.80 | 10187.60 |

</details>

<details>
<summary>Frozen completed-report provenance</summary>

Dataset SHA-256 `3a1268f1d731a7c60a3fa91f1e90e887c3f41a84aec05beed81b797253afa9b2`; manifest bytes `7570272d524d68ff3aad59ac1b5ea080e48b77acf605ba8bb30bef27205b94c8`.

| Run | Report SHA-256 | Runner SHA-256 |
|---|---|---|
| pilot-adaptive-luna | `7096290e3069713e032a318b062669c6de872dcb6da8c529bc3bb840280b11be` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-adaptive-pplx | `b45db3b4841da7390a067bf3aa3d6116a6b3c187f0ff282dd88a4da13dc560e0` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-flash-1024 | `ae00d5262137a056c83d9a02ebfdfd95b8b0d5661b11c1702530414b0b0f4431` | `1e45acff39062373e618ac3dfef4d6fedb978800198c67a9b675a0d76daac5f5` |
| pilot-flash-256 | `cc993eef7328fad6d15daba5c935acbdd96e55bec295bc4b831c0ca7fc343a04` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-flash-512 | `7573eb775fc6face7d56903d2d1db1b842b2a5b777435e1b32588b0c89e25ece` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-frontier-haiku | `08d3efbf5f36686dac2d82dbdb233c9aa170b7f09a9d8995ad48b5f49f60e78e` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-frontier-opus | `3701a28593bc7e010686de871d4e27b3f0dda519e031503bbb9ca664bcc93f22` | `5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7` |
| pilot-frontier-sonnet | `be8299cafd543220eef31b43351b26d7dbaafa55b55afce69124985691ae008d` | `1f9bbaee008f3063a4c8bd927b36a094336f637c06aeec32a0b7425cfe1964f5` |
| pilot-gated-flash-512 | `98b99c43d107a93ac78005ddd6b2f9811d4678b4d6fc34597d205cb6d4a4a697` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-gated-luna-1024 | `c8fc08d2ef73ff8a722ea815dad25f284ff0b39d621c731dd9603325af1b6ca9` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-gated-pplx-minimal | `a8adb873498a4128a210e8a7fb4e9e52200fa6d8d759c5d6012c6a5c035839bb` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-gated-pplx-relational | `c807f7e9f8988f7ac4ef8675a2cb3e62c84be9b30b576acb7c8ff899dd2e844c` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-gated-reading-luna | `9cd38fa2a5319c69503d49582e53b550920ae16aac7b75208e539dee07bbc04a` | `5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7` |
| pilot-gated-reading-pplx | `4515919a30c08c9a8bebd76fb5716fc4570d5e8dd28af846a284f6ebc842426e` | `5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7` |
| pilot-gated-reviewed-pplx | `378010fae17bc4ba01e0649c030fde9fe7db2de046004d734e5dce05bab4199e` | `5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7` |
| pilot-luna-1024 | `8ed90820ef9d7cbd7a6a01362010dc3687cfa84aee73557d26cb3e4cef37081d` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-luna-256 | `9b8817f2c1fa85b3916e782de61c3a4f1f4c204567cfc8cd42110725a7e83cdb` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-luna-512 | `737c3efe49add96737557105aa0a272b6678b052c40b40fcf8399b8574182b47` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-oriented-pplx-256 | `0463675dc11fb7b47391966c9e853f9ad5de6933ca96b86081d65a7c0532a6e4` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-pplx-1024 | `9971ea9afe03c9f275dc6ee122d868e15da561c5fe365b3ba1c16e3ff62df241` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-pplx-256 | `c6cc7030f7f5ce592738198cac68c402ba80c0536d21e92728699b7fdd40b47e` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-pplx-512 | `c6037212ee3d32977afc8625564b4e9e0be29f0c5a02fb216c8a29818ec0d3ae` | `3fcd576461a437ced1c8e6b65c915c52e8b5ca0ebbc0430c67424307d21fb562` |
| pilot-repair-flash-c1 | `0a98efe64a2531439dd3b130e753e408bbebb401ef0c4ea2f9d845918cc29068` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-repair-flash-c3 | `0c39d5290b71073eaea31a3c098ea7d3ad9e74e546f4767cf4d920f1365a4e93` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-repair-luna-c1 | `e00c28a834f19830dc9d6f1a4fff7a55e9470fc92fc46f32dc0bc56cb4dfb238` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-repair-luna-c3 | `0efb9d32502cc15d349da56b3bf59d8feb824974cdb90f076dbc056c2fce3518` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-repair-pplx-c1 | `68b11ae3cd810bb3264ed2593e81819802b876e2db73c6d9c80e05bbeb89536d` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-repair-pplx-c3 | `c91d36c727053f2df317a941d392e3327f1d78bf4c9369cd19f5e1ff2a36d5b1` | `02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37` |
| pilot-text-flash | `fc636a4e197f632d1620e2489549f4be175cc36eaa22836a0d92e0990b5fa976` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-text-luna | `de6fd59d5ea477c306ce3c35b62d33786276aa2044c15e6c9f7459eb5822e15c` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-text-pplx | `3ab24eacaf07f0ea9170547e465b9ebd283963b5e794de6a77ee1be7a1bf158f` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |

</details>
