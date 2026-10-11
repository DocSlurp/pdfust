# Mixed-evidence candidate source preparation

All 35 declared retained selectors passed source/output admission on the original natural16 DEV cohort: 16 intended pages per arm, 560 correlated page-run observations. This report records preparation only. Reference files remain unopened, historical strict witnesses have not yet been rerun, and no secondary scoring has occurred. No inference, retries, credential access, rentals or GPU work occurred.

The inventory is exactly the 28 PPLX image treatments (seven edges × four encodings) and seven difference-evidence treatments from [the tracked mixed comparison](p003-mixed-evidence.md). The exact completed queue is `pipeline-p003/parallel-mixed-evidence-v1/`. Status SHA256 is `616a333631c6e690d28fd3192e748c605c1e4f2be263cd89c79bee538b4e4293`; the independently verified inventory component is `9cca3621f32d377a52b49f6dd88a43f466af6a9cda7fe00dec17baa33c984567`.

Preparation uses the immutable `p003_additional_incremental_audit.admit` and `primary` helpers because these artifacts use the same `p003_candidate_choice` contract. Admission pins prior independent source/wire/output receipts, report/evaluation/frozen/manifest bytes, all actual page-result files and retained source/table hashes, and all 16 intended pages. The primary view uses only committed complete model-selected crops. Atomic operational failures, abstention, duplicate/no-question states and retained baseline outputs receive zero tables. Complete historical retained-composition strict totals and page witnesses remain a separate future replay; they must reproduce before selected-only schema/content metrics are reported. Archived Python is never executed.

The plan copies already approved corpus and target identities from `plans/additional-incremental-rescore48-v1.json`, SHA256 `0c12d3d66af28b3f1710a35c1e17a734b4a8385b85219b21b95cb62ae725f1b0`, without opening targets. Every report, evaluation, frozen execution inventory, run manifest and selected-prediction hash appears in the explicit 35-entry plan. Every prepared page list and prior artifact receipt hash is retained separately.

Authoritative preparation is `pipeline-p003/continuation-mixed35-prepared-v2/`; v1 is an unchanged initial source-preparation snapshot made before formatting and constant cleanup. Both have identical prediction/plan identities. Plan SHA256: `3635430df042f56a48bedcbdbc343267f32db2770a6fbeffe9cdc50ba60e987e`. Final preparation freeze SHA256: `a8ff6af35beb57c3ff08c9b8dbbf45aab4d363896d3a4031af9891142549bd39`.

Preparation measured 3.415296 seconds wall and 3.402548 CPU seconds with 78,397,440 bytes peak sampled process RSS. Measurement uses `process_time`, `perf_counter` and psutil sampling every 100 ms in one CPU-only process, with OMP/OpenBLAS/MKL thread counts one. No subprocess usage is implied. These measurements cover source preparation and artifact writes; they are not hosted inference rates or a claim about original compute cost.

Root must approve the explicit plan and independently pin the final current code map before scoring. The wrapper checks its own code and the unchanged helper closure, including the corpus loader, before plan admission. Root can run `python -m bench.p003_mixed_candidate_audit score --plan <prepared plan> --plan-sha256 <approved SHA> --trusted-code <external current helper map> --output <fresh directory>`. The unchanged historical witness gate and dual scorer run only in this separately authorized step. Historical generation costs remain separate from incremental selection costs; missing cost bases remain unknown. Existing candidate attempted-page zero counters retain their historical limitation and must not be promoted to measured zero performance.

| Arm | Committed model crops | Selected complete tables | Primary failed pages / 16 | Prior independent evaluation SHA256 |
|---|---:|---:|---:|---|
| choice-pplx-128-rgb_palette16-r1-c3 | 14 | 25 | 0 | `e426003d53bf0bfebc267588af91efa8cb176c37c753fa6933d439c61eba44af` |
| choice-pplx-400-rgb_palette16-r1-c3 | 15 | 26 | 0 | `9e20bc4a40db90ea47ae9a5b1609d3d81a4ac83c005678c9a2e2a9fa93f18bc0` |
| choice-diff-d1-0-r0-c3 | 7 | 7 | 1 | `290a4713c24c439681700e6db45c72bcec9f82939338a7b0d798b7f46ba46398` |
| choice-diff-tev-0-r0-c3 | 5 | 5 | 1 | `0ae0cde9f4de64cf252efa5fcdacc63dfccfc460bf975e98a1e3c26868544ad8` |
| choice-pplx-400-rgb-r1-c3 | 15 | 26 | 0 | `7499f01a9479c24e0ca8b1a6d2c0d47d8458f8da910bfb59ab1cb5b118abd1fb` |
| choice-pplx-1200-rgb_palette16-r1-c3 | 15 | 15 | 0 | `ef2cd3a007c6fbd8f49ac391d184a5ba41e9dd3b72c8509ea2881cfa0cc73d20` |
| choice-pplx-512-rgb_png-r1-c3 | 16 | 27 | 0 | `c5f6e987dfc268934231a2c7de4512bcabca21b162b454abb376cc3801b65d8f` |
| choice-diff-luna-0-r0-c3 | 0 | 0 | 1 | `bb960adbab198db9dcf678d35bce1262194beba669e30bf670e2cbd1962a57ca` |
| choice-pplx-400-rgb_png-r1-c3 | 15 | 26 | 0 | `9907f2c40f6a27b5cc51912a9a19d229d23318b9c5f78ac8006ca62de4dffbc6` |
| choice-pplx-1024-grayscale8-r1-c3 | 15 | 15 | 0 | `b68cc88d3fd62a09642bc7a71d084add4a92306098ff075bf049c7d7f0c75d8e` |
| choice-pplx-512-grayscale8-r1-c3 | 16 | 27 | 0 | `9acc9d07a38767058363756bfa38d9f890a907240f95ae624ba4a6ce4fd785fe` |
| choice-pplx-1024-rgb-r1-c3 | 15 | 15 | 0 | `058542cb04a5af0ba47ecb00cb3c8fdc123ba023e226efa9f58543fd9f3b944b` |
| choice-pplx-400-grayscale8-r1-c3 | 15 | 26 | 0 | `8cc68f9e06c1604ce331caf00d7fb65b435420ea5148b35f7686f9f49286ed97` |
| choice-diff-pplx-0-r0-c3 | 2 | 2 | 1 | `82f5fe4d37cdb79244fd92d43fee9073285a194d9d29c64b32a694270bd3464a` |
| choice-pplx-1200-rgb-r1-c3 | 15 | 15 | 0 | `697944c054b47adcac821dc0ff6fd4c13c2172c6f08c195b34abb8a966433855` |
| choice-pplx-1024-rgb_palette16-r1-c3 | 15 | 15 | 0 | `86bc33f1b0aad203a943abc2d3f7cfaf3f514b40e404e40f1a5a7eee8722615a` |
| choice-pplx-256-rgb_palette16-r1-c3 | 15 | 26 | 0 | `3837432099b37d89f3fc07ac8c50d0879f24ff646bb5f78a4d909d482d199588` |
| choice-diff-pplx-512-r0-c3 | 14 | 14 | 1 | `13a7e9596306d581f1f5eac2015faad54cf766d247fee64e2dfcd9e561ad45bc` |
| choice-pplx-768-rgb_palette16-r1-c3 | 16 | 27 | 0 | `f1ac695ebec6bc2c9b4c6166143a059bec079eac72a3c78d2870ac7a60f0110d` |
| choice-pplx-768-rgb_png-r1-c3 | 16 | 27 | 0 | `49449e9c3d1a040a614ec56724e28a97d26a78136034c9e665f0674f978d3b93` |
| choice-pplx-1024-rgb_png-r1-c3 | 8 | 8 | 5 | `b7bf79523686c05cd7e81d289c0b58661ca2acde1d32910ef78e70ef16094dde` |
| choice-pplx-768-grayscale8-r1-c3 | 16 | 27 | 0 | `3762ac3e4b0091ec03c85750c242e13b65d0eed1db1c4557a6e8a17b0874defd` |
| choice-diff-luna-512-r0-c3 | 7 | 7 | 1 | `d99fccd488d4c9038775dd61330d56a1f0de47a817e51b13d8bc50f7ace1a346` |
| choice-pplx-128-rgb_png-r1-c3 | 15 | 26 | 0 | `2a56944cf28ecaab2397f2b4061102feb5bdb4275f3ec53dbf6e06c71b0edda3` |
| choice-pplx-256-rgb-r1-c3 | 15 | 26 | 0 | `0632104d060c69944a060af69405a2c42ed057d90b644faf48249c315b35ea75` |
| choice-pplx-1200-grayscale8-r1-c3 | 15 | 15 | 0 | `7398dfb205944069966417856822ee18c9ff28c92aa99b50804c19d980357644` |
| choice-pplx-512-rgb-r1-c3 | 16 | 27 | 0 | `a581ece42e89d7f80e693f684392ecab7d9a35c701fa536e7647241898a51026` |
| choice-pplx-256-grayscale8-r1-c3 | 15 | 26 | 0 | `8129b93bb198242c1a21c8793f66d1634dae594cbbcbb9d2528c2d339439b58c` |
| choice-pplx-256-rgb_png-r1-c3 | 15 | 26 | 0 | `9ab08496fb3953c52e82c56ccff6606db8b3539b4533260dba1811d174e1e771` |
| choice-pplx-1200-rgb_png-r1-c3 | 8 | 8 | 5 | `5c66351220cfdb8bc239bae7abc98d0e3a336cd271b3b0693eb58a67b139a86b` |
| choice-pplx-128-grayscale8-r1-c3 | 15 | 26 | 0 | `7e7ccaf89b84abe526d831cd11866c956ba2a0e2db60216a37db1d5eb9a7bdc5` |
| choice-pplx-128-rgb-r1-c3 | 15 | 26 | 0 | `9ce67660715f6dbd9de24eb3b7d872c107e08a4e6abd80b7f802bcfeb035ce32` |
| choice-pplx-512-rgb_palette16-r1-c3 | 16 | 27 | 0 | `3406d57e8e7e9e6a5c32a4266abd47bed3652948a670f237a9b766189d7b3f26` |
| choice-pplx-768-rgb-r1-c3 | 16 | 27 | 0 | `30c5c58ed2e3be7c122dd9c97b2e2056fdd8d03afb0dbd42fffda31e6fc890b3` |
| choice-diff-jev-0-r0-c3 | 0 | 0 | 1 | `6cc92c0aa613f3b50c9252353eb69e50ad4c5df842c57441a9fdea16c9061b42` |

Validation: seven new scope and authorization-gate tests pass. Scoped Ruff and mypy (`--follow-imports=silent`) pass; unrestricted mypy also exposes existing errors in imported historical benchmark modules. None of those immutable historical helpers was changed.
