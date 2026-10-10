# P002 logical native table orientation

This is an offline correction diagnostic, using retained full-corpus model responses. It does not change historical primary scores, charges, failures, or throughput, and makes no fresh inference or provider-cache claim.

The preserved-rotation hybrid path retained native cells in physical display row-major order. Core `Document.to_markdown()` instead projects native tables into the dominant actual text-baseline direction. The opt-in `native_table_orientation=logical` adapter now uses that same core baseline rule, with a character-weighted table-local vote and the existing core page fallback when no native lines lie inside the table. Page `/Rotate` alone does not select direction: counterrotated content can have upright baselines. Missing native baseline evidence retains the core rightward fallback; this does not establish logical orientation of image-only text.

The source-only specification and generated tests were committed in `14dbc99` before reference scoring. Generated asymmetric grids cover all four right-angle rotations, CropBox offsets, merged headers, multiline cells, counterrotated content, and an outside heading with a different direction. Projection reindexes rectangular native spans and source IDs into logical inline/block axes, preserving every source literal and ownership partition. Physical native child structures, original PDF rotation, full native boxes, native exclusions, detector pixels, crop requests, model responses, and model tables stay unchanged. The flag defaults to physical for historical reproducibility; logical runs require the new frozen dependency and replayed original-PDF baseline evidence.

Both completed controls were replayed on all 276 intended pages, including 220 structurally scored pages and 56 diagnostic pages. Failed pages retain zero admitted tables. Exactly the 12 authored rotated pages changed in each control; all other predicted tables remained identical. Original model tables, source ledgers, and native physical boxes were checked for equality on every successful page.

| Fixed retained control | Exact anchor cells: physical → logical | Complete tables: physical → logical | Original all-page errors | Extra tables: unchanged |
| --- | ---: | ---: | ---: | ---: |
| Full Haiku hybrid crops 1024 | 6604 → 6863 / 8897 | 157 → 169 / 249 | 8 | 2 |
| Full Sonnet hybrid crops 1024 | 6119 → 6378 / 8897 | 157 → 169 / 249 | 5 | 16 |

For each control, authored rotated12 improves from 5/264 to 264/264 exact cells and from 0/12 to 12/12 complete tables. This correction addresses native indexing; it provides no evidence that detector coverage or model transcription improved.

The tracked reproduction requires existing verified report/manifest identities and complete unique 276-page coverage. It explicitly opens only the named control, corpus manifest/targets, listed original PDFs, and successful vision child structures. References are read only after source-only recomposition, never to choose orientation. All input and dependency SHA-256 hashes and all per-page corrected predictions are retained in the output JSON.

```sh
python -m bench.generalization_native_orientation_audit \
  --artifact-root bench/results/pdf-master-artifacts/pipeline-p002 \
  --run full276-hybrid-haiku-1024 \
  --output bench/results/pdf-master-artifacts/pipeline-p002/native-orientation-haiku-replay.json
# Repeat with --run full276-hybrid-sonnet-1024 and a separate output.
```

Linux CPU measurements use `perf_counter`, `process_time`, and `getrusage(RUSAGE_SELF)`. Replay wall/CPU exclude imports; peak RSS includes imports and is the process lifetime high-water mark. One process and no GPU, network, credentials, or fresh provider calls were used. Haiku replay took 6.765 s wall / 7.011 s CPU; Sonnet took 7.520 s wall / 7.745 s CPU. Both measured 440488 KiB peak RSS. These are offline local correction costs, not pipeline productivity measurements.

The focused suite passed 29 tests; Ruff and scoped mypy passed. The pre-existing orchestration stub now patches both the module registry and package attribute so test collection order cannot silently replace its mock with the real helper.

Frozen helper SHA-256: `c75766aaf3e2407fe9f720dbedb9fd31199bccd0128e93a3d73b4c96c8bbba26`.

| Input | SHA-256 |
| --- | --- |
| Haiku retained report | `60b8c88b7207aa390aa8f9c1d294bf870ac5e33810da5ec355906c34bee9ac35` |
| Haiku verified evaluation | `66007d54d95b00ff4aef503bc003ef2865fce6cf816681241ff7b327744a6166` |
| Sonnet retained report | `544d4d72b4c27f60b2b46c668704d53a690cbf546bff47b7ce7e5f23839f16cf` |
| Sonnet verified evaluation | `c75d68168928aa5451efe5ab3e0bbb91b562e8640e9e873b50a6618de8218881` |
| Corpus manifest | `4d97bdc63a399cc3df99302e84ec9c8e97c8cd9efcda6a9fcd7426fa9a94548b` |
| Private DEV targets | `7010168fc0f36263ca247a7b9378572b44df9e9e120f2c74ca3f29ec8edfcdef` |
