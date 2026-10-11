# Supplemental random office values DEV corpus

All 40 newly authored pages are frozen in `pipeline-p003/random-office-values40-v1`. They contain 32 table pages and eight negative pages, with 36 tables total. Four pages contain two independent column tables. These sources are separate from natural documents, the earlier synthetic relationship set, fresh confirmation pages, and protected corpora. No existing corpus or model outcome was read during generation.

The seed is `p003-random-office-values-20261011-v1`. Independent deterministic streams choose layout, values, and opaque source filenames. Values are not derived from row numbers, filenames, or labels. Eight families each contribute four table pages: ruled, borderless, wrapped, merged headers, dense, column pairs, mixed types, and continuations. Tables have 8–24 rows and 3–6 columns. Negative pages contain prose, irregular forms, decorative rules, or prose columns.

The table body contains 943 one- or two-word English values, 644 USD values including 98 parenthesized negatives and 39 zero amounts, and 665 dates split across ISO, US numeric, and English month formats. It also contains 48 blanks, 44 `N/A`, 40 `NULL`, 42 em dashes, and 282 other zero/status noise values. Values repeat deliberately between surviving cells; duplicate literal excess across each page is 325, including incidental random repeats. Extraction retains every physical source word with a unique local ID rather than deduplicating text.

Textboxes use the library's actual width-dependent wrapping. Currency body values align right. Merged headers and two-row continuation cells retain rectangular spans and remove their corresponding internal rules. Generation refuses overflowing text instead of truncating or shrinking it. PDF metadata contains no case identity, hidden label, or layout family. All 40 sources extract successfully, retaining 4,829 words. No model confidence is supplied; its source receipt explicitly records `None`.

The standard schema 1 manifest is compatible with `generalization_report.load_corpus`. Only `id`, `pdf_path`, `pdf_sha256`, and `page_number` are model fields. Author-owned tables and literal construction receipts reside in separate `private-targets.json` and `private-construction.json`. Schema 1 dataset identity includes the separate target hash basis; the manifest contains no target literal. `source-inventory.json` hashes 120 PDFs, extracted source snapshots, and actual rendered images, excluding private files. `gallery.html` shows source pixels without reference overlays. Synthetic results must remain separate from natural document scores.

Frozen receipts:

- Dataset: `c8b22181196ce2e70e661a516ace7a2816afb47b09306a4f2bbf907f2f24a92d`.
- Manifest: `3aea2b9f92a69960bef158bedd03ab10d639be12a64ad2ccc3b568c9bcac23f9`.
- Source inventory: `8ef609e4722ca310cfcd15ce219648f5b789fdd4d9554931122a1c040ad63675`.
- Targets: `129d07decd9b289d35a4e691782e7f204d8fb5b133c01ba46372710acb7f0cce`.
- Frozen receipt: `ccee8bd3f7310d61e4adb84f70f29e28e6de82f2832e80f350567d894ce9a493`.

Generation, extraction, and rendering took 1.52 seconds wall and 1.51 seconds process CPU. Unsampled parent lifetime peak RSS was 606,832 KiB, including imports and render buffers. CPU settings were two Rayon threads and one OpenMP/BLAS/MKL thread; no GPU, hosted calls, or downloads were used. Four tests cover deterministic independent identities, actual wrapping and extraction, rectangular merged coverage, and complete loader/inventory/gallery compatibility. Ruff and targeted mypy pass.

Reproduction requires a new directory; existing artifacts are never overwritten:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=2 \
  .venv/bin/python -m bench.p003_random_values_corpus --output NEW_DIRECTORY
```
