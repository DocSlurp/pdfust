# P001 offline pipeline performance analysis

Completed-report snapshot: 2026-10-10T00:08:33+00:00; 27 completed runs. Incomplete or still-running jobs are excluded from these measurements. No requests, ledger reads, credentials, network, GPU work or extraction reruns were used. The analysis reads retained sanitized call entries and private DEV construction references only after completed reports exist.

Dataset `3a1268f1d731a7c60a3fa91f1e90e887c3f41a84aec05beed81b797253afa9b2`; physical full cohort 181 pages, scored subset 168; predefined pilot 32 pages, 16 table positives and 16 negatives. All source bytes, frozen cohort projections and retained successful output files passed the offline report contract checks.

The main latency burden in the instrumented pilot runs is the hosted client path. Native extraction, candidate assembly and small page-image preparation together take roughly 0.8–2.5 seconds per 32-page assembly pilot. HTTP intervals dominate Flash elapsed time; client work outside those intervals is comparable to or greater than the HTTP intervals for several PPLX and Luna runs. This overhead has substantial measured process CPU, so provider response time alone does not explain complete-pipeline throughput.

| Completed run | Pages / calls | Wall s | CPU s | Extraction s | Proposal s | Render s | HTTP interval s | Client non-HTTP s | Client CPU s | Remaining wall s | Peak sampled RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| native-r1 | 181/0 | 2.878 | 2.975 | 2.398 | 0.078 | not used | not used | not used | not used | 0.402 | 120.0 |
| native-r2 | 181/0 | 2.475 | 2.568 | 2.057 | 0.093 | not used | not used | not used | not used | 0.325 | 124.2 |
| native-r3 | 181/0 | 2.493 | 2.589 | 2.099 | 0.082 | not used | not used | not used | not used | 0.313 | 119.8 |
| native-text-r1 | 181/0 | 2.654 | 2.727 | 2.187 | 0.207 | not used | not used | not used | not used | 0.260 | 125.9 |
| pilot-adaptive-luna | 32/18 | 19.195 | 10.376 | 0.382 | 0.144 | 0.122 | 7.573 | 8.659 | 7.424 | 2.317 | 183.6 |
| pilot-adaptive-pplx | 32/21 | 23.383 | 11.720 | 0.401 | 0.140 | 0.125 | 10.536 | 9.605 | 8.483 | 2.575 | 183.7 |
| pilot-flash-1024 | 32/32 | 76.801 | 19.835 | 0.472 | 0.169 | 1.386 | 54.047 | 16.315 | 13.767 | 4.411 | 188.6 |
| pilot-flash-256 | 32/32 | 60.302 | 15.481 | 0.671 | 0.126 | 0.141 | 43.480 | 12.434 | 11.094 | 3.450 | 194.6 |
| pilot-flash-512 | 32/32 | 60.507 | 15.848 | 0.588 | 0.145 | 0.353 | 43.337 | 12.679 | 11.362 | 3.406 | 183.3 |
| pilot-gated-flash-512 | 32/30 | 56.202 | 21.658 | 0.525 | 0.194 | 0.213 | 32.469 | 18.088 | 16.161 | 4.712 | 191.2 |
| pilot-gated-luna-1024 | 32/27 | 34.946 | 22.674 | 0.659 | 0.195 | 0.754 | 10.113 | 18.516 | 16.534 | 4.710 | 195.4 |
| pilot-gated-pplx-minimal | 32/28 | 31.848 | 16.867 | 0.423 | 0.139 | 0.080 | 13.730 | 13.736 | 12.503 | 3.740 | 183.8 |
| pilot-gated-pplx-relational | 32/27 | 35.200 | 20.544 | 0.519 | 0.214 | 0.099 | 12.806 | 17.270 | 15.520 | 4.292 | 195.9 |
| pilot-luna-1024 | 32/32 | 31.430 | 16.855 | 0.394 | 0.150 | 1.235 | 13.357 | 12.720 | 11.526 | 3.573 | 188.0 |
| pilot-luna-256 | 32/32 | 32.919 | 20.437 | 0.820 | 0.156 | 0.165 | 10.907 | 16.253 | 14.736 | 4.618 | 183.9 |
| pilot-luna-512 | 32/32 | 28.379 | 16.233 | 0.620 | 0.126 | 0.359 | 11.040 | 12.763 | 11.661 | 3.471 | 182.9 |
| pilot-oriented-pplx-256 | 32/32 | 40.689 | 19.444 | 0.438 | 0.173 | 0.176 | 19.892 | 15.702 | 14.363 | 4.308 | 184.8 |
| pilot-pplx-1024 | 32/32 | 49.481 | 19.657 | 0.658 | 0.224 | 1.602 | 22.701 | 19.473 | 13.766 | 4.823 | 190.8 |
| pilot-pplx-256 | 32/32 | 41.227 | 20.236 | 0.553 | 0.197 | 0.195 | 18.569 | 16.938 | 14.733 | 4.775 | 194.7 |
| pilot-pplx-512 | 32/32 | 35.195 | 14.902 | 0.367 | 0.131 | 0.351 | 18.937 | unmeasured | unmeasured | unmeasured | 192.5 |
| pilot-repair-flash-c1 | 32/17 | 26.471 | 10.335 | 0.519 | 0.162 | 0.410 | 14.628 | 8.412 | 7.083 | 2.340 | 185.1 |
| pilot-repair-flash-c3 | 32/18 | 38.940 | 13.876 | 0.518 | 0.237 | 0.466 | 23.304 | 11.327 | 9.746 | 3.088 | 184.4 |
| pilot-repair-luna-c1 | 32/21 | 17.674 | 10.421 | 0.370 | 0.133 | 0.345 | 6.479 | 8.078 | 7.303 | 2.269 | 196.0 |
| pilot-repair-luna-c3 | 32/19 | 27.507 | 17.302 | 0.552 | 0.296 | 0.495 | 8.650 | 13.547 | 12.056 | 3.968 | 186.4 |
| pilot-repair-pplx-c1 | 32/23 | 22.794 | 11.965 | 0.407 | 0.140 | 0.360 | 10.014 | 9.153 | 8.339 | 2.720 | 184.1 |
| pilot-repair-pplx-c3 | 32/22 | 40.513 | 18.863 | 0.781 | 0.337 | 0.686 | 13.494 | 19.633 | 13.335 | 5.583 | 183.0 |
| pilot-text-pplx | 32/32 | 39.257 | 17.111 | 0.395 | 0.161 | not used | 19.505 | 15.304 | 12.693 | 3.891 | 184.7 |

Extraction is the retained cumulative `extraction_seconds`: PDF hash read, open and word/native-table interpretation up to the snapshot. Proposal is `proposal_complete_seconds - extraction_seconds`. Render is the separately measured wall interval, including render, image conversion and encoding. These are serial wall-stage sums; extraction and proposal do not have separately recorded process CPU. For unsupported no-text pages, extraction can be measured while proposal/render are not entered. Native render/client intervals are marked not used rather than presented as measured zero work. The hosted text-only arm does not render an image; its image helper records a 0.000186s wall / 0.000136s CPU dispatch interval across 32 calls, which is not raster preparation and is labeled not used in the table.

Each sanitized entry `elapsed_ms` begins just before HTTP transmission and ends after receiving, writing and accounting the response. It includes network transit, provider queue/inference and some local response work; it is not provider compute time or a pure RTT measurement. `client_wall_seconds` encloses `DecisionClient.request` plus strict answer parsing. Its difference from the HTTP interval includes ledger loading/admission, locks, pre-request reservations and writes, telemetry export and final persistence. The root wave-cap ledger read happens before the client timer, so it is included in the remaining-wall residual along with request construction/writes, state validation, output persistence and sampling/progress overhead. No one of these components is separately timed.

For example, `pilot-pplx-256` spends 35.507s inside the client: 18.569s in the enclosing HTTP interval and 16.938s outside it. Its client CPU is 14.733s, 72.8% of total process CPU. `pilot-luna-512` spends 23.803s in the client, split into 11.040s HTTP and 12.763s non-HTTP; client CPU is 11.661s, 71.8% of total CPU. `pilot-flash-512` spends 43.337s in HTTP, 71.6% of complete wall, plus 12.679s client non-HTTP overhead; client CPU is 11.362s, 71.7% of total CPU.

The source implementation repeatedly parses and checkpoints the persistent JSON ledger and performs synchronous telemetry export; sanitized completed entries report telemetry exported. These mechanisms are plausible contributors to the measured non-HTTP interval. The reported approximately 14 MiB ledger size was supplied by the root investigator and was not measured or opened for this analysis. Existing intervals cannot isolate ledger JSON parsing, filesystem writes, lock contention or telemetry network waiting. A component profile would be required to attribute their shares. This report proposes no change to reservations, locking, cost accounting or spending semantics.

Completed pilot quality and inference charges (all completed policies):

| Run | Policy / image edge | Input tokens | API effective USD | Cost basis | Exact positive pages | Negative FP pages | Candidate missing positives | Available-but-unrecovered positives |
|---|---|---:|---:|---|---:|---:|---:|---:|
| pilot-adaptive-luna | adaptive/256 | 25476 | 0.00254760 | catalog estimate | 10/16 | 4/16 | 0 | 6 |
| pilot-adaptive-pplx | adaptive/256 | 39567 | 0.00079134 | provider-reported USD | 12/16 | 6/16 | 0 | 4 |
| pilot-flash-1024 | assembly/1024 | 177747 | 0.00675439 | provider-reported USD | 6/16 | 1/16 | 1 | 9 |
| pilot-flash-256 | assembly/256 | 154729 | 0.00587970 | provider-reported USD | 3/16 | 0/16 | 1 | 12 |
| pilot-flash-512 | assembly/512 | 158323 | 0.00601627 | provider-reported USD | 5/16 | 0/16 | 1 | 10 |
| pilot-gated-flash-512 | gated/512 | 104696 | 0.00397845 | provider-reported USD | 10/16 | 0/16 | 0 | 6 |
| pilot-gated-luna-1024 | gated/1024 | 73783 | 0.00737830 | catalog estimate | 16/16 | 1/16 | 0 | 0 |
| pilot-gated-pplx-minimal | gated/256 | 81457 | 0.00162914 | provider-reported USD | 16/16 | 1/16 | 0 | 0 |
| pilot-gated-pplx-relational | gated/256 | 79047 | 0.00158094 | provider-reported USD | 16/16 | 1/16 | 0 | 0 |
| pilot-luna-1024 | assembly/1024 | 120983 | 0.01209830 | catalog estimate | 15/16 | 2/16 | 1 | 0 |
| pilot-luna-256 | assembly/256 | 97175 | 0.00971750 | catalog estimate | 15/16 | 4/16 | 1 | 0 |
| pilot-luna-512 | assembly/512 | 102039 | 0.01020390 | catalog estimate | 15/16 | 4/16 | 1 | 0 |
| pilot-oriented-pplx-256 | assembly/256 | 148164 | 0.00296328 | provider-reported USD | 16/16 | 4/16 | 0 | 0 |
| pilot-pplx-1024 | assembly/1024 | 176196 | 0.00352392 | provider-reported USD | 15/16 | 4/16 | 1 | 0 |
| pilot-pplx-256 | assembly/256 | 153178 | 0.00306356 | provider-reported USD | 15/16 | 4/16 | 1 | 0 |
| pilot-pplx-512 | assembly/512 | 156772 | 0.00313544 | provider-reported USD | 15/16 | 4/16 | 1 | 0 |
| pilot-repair-flash-c1 | repair/512 | 34763 | 0.00132099 | provider-reported USD | 10/16 | 5/16 | not a ceiling | not attributed |
| pilot-repair-flash-c3 | repair/512 | 49885 | 0.00189563 | provider-reported USD | 10/16 | 6/16 | not a ceiling | not attributed |
| pilot-repair-luna-c1 | repair/512 | 32045 | 0.00320450 | catalog estimate | 10/16 | 5/16 | not a ceiling | not attributed |
| pilot-repair-luna-c3 | repair/512 | 37339 | 0.00373390 | catalog estimate | 10/16 | 6/16 | not a ceiling | not attributed |
| pilot-repair-pplx-c1 | repair/512 | 50535 | 0.00101070 | provider-reported USD | 11/16 | 6/16 | not a ceiling | not attributed |
| pilot-repair-pplx-c3 | repair/512 | 57369 | 0.00114738 | provider-reported USD | 11/16 | 5/16 | not a ceiling | not attributed |
| pilot-text-pplx | assembly/0 | 137422 | 0.00274844 | provider-reported USD | 16/16 | 4/16 | 0 | 0 |

API effective charges cover inference requests only. PPLX and Flash rows retain positive provider-reported USD; Luna rows retain original provider-reported zero and use separately labeled catalog estimates. The API decision adapters report output-token counts of zero for Flash/Luna; those observations are retained, not interpreted as absent decision computation. Tokens are provider-reported and are not a common tokenizer or image-token unit across models. Reservations and local CPU electricity/amortization are not inference charges.

In the matched original assembly arm, increasing image edge from 256 to 1024 raises input tokens from 153,178 to 176,196 for PPLX (+15.0%), 154,729 to 177,747 for Flash (+14.9%), and 97,175 to 120,983 for Luna (+24.5%). Render preparation rises from roughly 0.14–0.19s to 1.23–1.60s across the complete 32-page pilot. Render CPU is separately retained in per-page stages, but extraction/proposal CPU is unavailable. Larger images therefore have measured preparation and token costs; these runs do not establish a general quality benefit or a controlled provider-latency effect. They are sequential observations with varying code hashes, persistent-client history and provider load, not randomized repeated performance trials.

Candidate and selection misses are distinct. The original image assembly pilot has one positive with no exact complete candidate; remaining positive errors where an exact candidate was retained are selection failures. The orientation-normalized arm changes the source/proposal geometry and its available-candidate coverage, so it cannot be treated as an image-only model comparison. Negative false positives are table/prose admission errors despite conservation and a zero-table alternative. This identifies a relationship/admission problem without using intended cell values or fixture identities as prompt hints.

The candidate comparison above is reference-informed and unrunnable: it checks whether an already-retained complete state matches the private reference. It neither supplies gold to inference nor constructs missing candidates. Repair arms can create later states, so their initial proposal coverage is not a hard ceiling and candidate-miss attribution is omitted for them. For gated/adaptive policies, an available-but-unrecovered positive can result from routing or admission as well as final candidate selection. The completed gated PPLX and Luna variants recover 16/16 positive pages with one negative false positive; their remaining error is admission/selection rather than absent candidate structure. Adaptive PPLX uses fewer calls but recovers 12/16 positives with 6/16 negative false positives, and adaptive Luna recovers 10/16 with 4/16 false positives. Call savings therefore have to be assessed against final structure. Fewer repair calls reduce request count, but sparse call count alone is not a complete-pipeline quality or performance win; final matrices, spans, false positives and total wall/CPU remain part of the comparison.

The completed PPLX geometry-text-only arm has exactly the same 32 literal source snapshots and candidate collections as `pilot-oriented-pplx-256`. Both recover 16/16 positives with 4/16 negative false positives. Removing images reduces input tokens from 148,164 to 137,422 (7.25%) and provider-reported charges from USD 0.00296328 to 0.00274844 (7.25%); complete wall is 39.257s versus 40.689s, and CPU 17.111s versus 19.444s. This one sequential paired observation shows no quality change on this pilot and does not establish that images are generally unnecessary. Other geometry-text-only models and frontier controls still incomplete at this snapshot have no claimed measurements here. CPU `native_text` is a native text-table strategy, not this hosted geometry-text-only arm. No GPU measurements or remote CPU/RAM utilization are available.

Future hypothesis: a cheap decision model could request a matched frontier choice only when its available-alternative scores have insufficient margin or it abstains. The gated pilot still has a prose/table false positive despite complete positive recovery, so escalation must be evaluated for both recall and false positives, with the same source evidence and candidate menu. Raw decision scores are uncalibrated ranking signals, not correctness probabilities. No fixture-specific threshold or prompt hint is selected here. This is an untested hypothesis pending the matched frontier controls and a separately frozen routing rule; no additional request is authorized or made by this analysis.

Measurement scope and reproducibility: one serial runner process, concurrency 1, eight logical CPUs, Python 3.14.7, Linux 7.2.5 Omarchy x86_64/glibc 2.44. `perf_counter` measures wall, `process_time` counts current-process CPU across its threads, and psutil samples current-process RSS every 100ms. Peak sampled RSS can miss shorter peaks; it is not an OS high-water value and does not include remote resources. Overall runner metrics include provider waiting and local serialization; imports, corpus construction and root campaign orchestration outside the recorded context are excluded. Current-executable imports inside individual page processing are included when they occur. Native CPU slightly exceeds wall because process CPU includes native threads and the sampler; it is not a claim of independent-document parallel throughput.

This is complete operational output plus table/non-table authored-silver evaluation, not general document extraction accuracy. Snapshot word conservation cannot establish Unicode completeness, pixel visibility, headings/lists/math/forms/image semantics or correct reading order. The five natural PDF sources and other cases with incomplete references remain diagnostic-only. Source bytes and full outputs remain in ignored artifacts; summary numbers do not replace them.

<details>
<summary>Completed-report and code provenance</summary>

| Run | Completed report SHA-256 | Runner SHA-256 |
|---|---|---|
| native-r1 | `a814d6a2c07b5397de4f5556855427e48bc6a297d857e650876954ca67923a6b` | `08eabdb0717f044856b0e35456a7b04267378ff049f01e5b7a096a87965a889d` |
| native-r2 | `66825db3cb242cebc36bbc1902aa0999614f8c60184c865929e9f3b6bb9de70c` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| native-r3 | `264e340499ed3033abac237b433f9eb87bc537f06bbeed6c16900f0a97d681e4` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| native-text-r1 | `f0664409cfe287c8ee31d7542b7b826110a26b1b48864290f622c5644d6631a5` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-adaptive-luna | `7096290e3069713e032a318b062669c6de872dcb6da8c529bc3bb840280b11be` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-adaptive-pplx | `b45db3b4841da7390a067bf3aa3d6116a6b3c187f0ff282dd88a4da13dc560e0` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-flash-1024 | `ae00d5262137a056c83d9a02ebfdfd95b8b0d5661b11c1702530414b0b0f4431` | `1e45acff39062373e618ac3dfef4d6fedb978800198c67a9b675a0d76daac5f5` |
| pilot-flash-256 | `cc993eef7328fad6d15daba5c935acbdd96e55bec295bc4b831c0ca7fc343a04` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-flash-512 | `7573eb775fc6face7d56903d2d1db1b842b2a5b777435e1b32588b0c89e25ece` | `0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c` |
| pilot-gated-flash-512 | `98b99c43d107a93ac78005ddd6b2f9811d4678b4d6fc34597d205cb6d4a4a697` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-gated-luna-1024 | `c8fc08d2ef73ff8a722ea815dad25f284ff0b39d621c731dd9603325af1b6ca9` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-gated-pplx-minimal | `a8adb873498a4128a210e8a7fb4e9e52200fa6d8d759c5d6012c6a5c035839bb` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
| pilot-gated-pplx-relational | `c807f7e9f8988f7ac4ef8675a2cb3e62c84be9b30b576acb7c8ff899dd2e844c` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |
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
| pilot-text-pplx | `3ab24eacaf07f0ea9170547e465b9ebd283963b5e794de6a77ee1be7a1bf158f` | `ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2` |

</details>
