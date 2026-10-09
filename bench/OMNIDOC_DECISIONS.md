# OmniDocBench DEV image-presence decisions

This is an opt-in research pilot on the fixed 16-image DEV sample in `omnidoc-dev/registry.json`. The upstream dataset is restricted to research purposes and excludes commercial use. Public benchmark contamination is unknown. Keep official images, annotations, request bodies and responses in ignored local artifacts; commit only code, registry provenance and Markdown summaries. The pilot measures table, isolated-math and multicolumn presence. It does not reconstruct tables, measure OCR accuracy or change extraction defaults.

Four allowlisted native decision models receive one whole-page image per request: Luna Decisions, PPLX Decider, Clef Flash and Clef. Conditions are RGB with maximum edge 128, 512 or 1200 pixels, plus a matched all-white 512-pixel canvas. Aspect ratio is retained. There are 256 logical requests, each with fixed `q0`, `q1`, `q2`; all conditions keep the same 16-page denominator.

The request builder accepts image bytes and a model only. Official pixels are resized explicitly for the selected arm; annotation text, filenames, category counts, layout labels and source URLs never enter request bodies. Private scoring labels derive from registry category presence and layout, separately frozen in `private-labels.json`. `other_layout` is unknown for multicolumn scoring; `1andmore_column` counts as including multiple columns. Blank controls expect all features absent. A frozen 0.5 threshold produces complete TP/TN/FP/FN matrices; returned probability is not calibrated correctness.

Prepare locally without constructing a credential-bearing client:

```bash
PYTHONPATH=. /home/dan/code/oss/pylopdf/.venv/bin/python -m bench.omnidoc_decisions \
  --prepare \
  --directory /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/decisions/omnidoc-dev-presence-v3 \
  --registry /home/dan/code/oss/pylopdf/bench/omnidoc-dev/registry.json \
  --image-root /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/omnidoc-dev/images \
  --prices /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/decisions/langfuse/catalog-prices.json
```

A prepared directory is immutable; rerun without `--prepare` to refresh local reports. After reviewing frozen request hashes, admit hosted execution explicitly by adding `--run-hosted --client-root /home/dan/code/oss/pylopdf`, using the same paths and omitting `--prepare`. The CLI holds the shared `decisions/run.lock`; the existing `DecisionClient` applies its shared ledger and cumulative $15 cap. This pilot additionally enforces a persistent $0.50 incremental cap across all `omnidoc-dev/` ledger tags, including failed and unsettled calls. With a $0.30 next-request reservation, paid calls stop when accounted charges exceed $0.20. A retained reservation can stop the pilot earlier. The persistent marker is `omnidoc-dev-wave.json`; changing output directories does not reset tagged spending.

Bodies and private labels are hashed, prices and their provenance are snapshotted, and all hashes are verified before client construction. Clef transport may use lossless WebP with decoded-pixel equality verified. Requests still exceeding body, text or base64 boundaries are honestly refused, without implicit cropping, further resolution reduction or automatic retries. Cached successful bodies may replay; failed identical requests require investigation and remain failed.

Reports retain every logical observation, including refused, unattempted, failed and malformed responses. Confusion counts distinguish unknown references from unscored requests. Provider charges are deduplicated by shared-ledger index. Positive reported charges take precedence; zero or missing reported charges can use frozen catalog rates and reported token counts as labeled estimates. Missing usage/rates remain unknown, and partial estimates do not become complete totals. Ledger reservations remain separate from effective charges.

Pages/min uses transmitted page observations divided by total serial HTTP time; preparation and replay are excluded. Pages/$ uses completed logical observations and known effective charges, with replay retained explicitly. Resource measurements cover CPU image preparation, encoding, lossless transport and artifact writes, with current-executable high-water RSS. They are separate from hosted HTTP timing. No local GPU is used.
