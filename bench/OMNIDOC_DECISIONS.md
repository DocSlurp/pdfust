# OmniDocBench DEV image-presence decisions

This is an opt-in research pilot on the fixed 16-image DEV sample in `omnidoc-dev/registry.json`. The upstream dataset is restricted to research purposes and excludes commercial use. Public benchmark contamination is unknown. Keep official images, annotations, request bodies and responses in ignored local artifacts; commit only code, registry provenance and Markdown summaries. The pilot measures table, isolated-math and multicolumn presence. It does not reconstruct tables, measure OCR accuracy or change extraction defaults.

Four allowlisted native decision models receive one whole-page image per request: Luna Decisions, PPLX Decider, Clef Flash and Clef. Conditions are RGB with maximum edge 128, 512 or 1200 pixels, plus a matched all-white 512-pixel canvas. Aspect ratio is retained. There are 256 logical requests, each with fixed `q0`, `q1`, `q2`; all conditions keep the same 16-page denominator.

The request builder accepts image bytes and a model only. Official pixels are resized explicitly for the selected arm; annotation text, filenames, category counts, layout labels and source URLs never enter request bodies. Private scoring labels derive from registry category presence and layout, separately frozen in `private-labels.json`. `other_layout` is unknown for multicolumn scoring; `1andmore_column` counts as including multiple columns. Blank controls expect all features absent. A frozen 0.5 threshold produces complete TP/TN/FP/FN matrices; returned probability is not calibrated correctness.

Prepare locally without constructing a credential-bearing client:

```bash
PYTHONPATH=. /home/dan/code/oss/pylopdf/.venv/bin/python -m bench.omnidoc_decisions \
  --prepare \
  --directory /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/decisions/omnidoc-dev-presence-v4 \
  --registry /home/dan/code/oss/pylopdf/bench/omnidoc-dev/registry.json \
  --image-root /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/omnidoc-dev/images \
  --prices /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/decisions/langfuse/catalog-prices.json
```

A prepared directory is immutable; rerun without `--prepare` to refresh local reports. After reviewing frozen request hashes, admit hosted execution explicitly by adding `--run-hosted --client-root /home/dan/code/oss/pylopdf`, using the same paths and omitting `--prepare`. The CLI holds the shared `decisions/run.lock`; the existing `DecisionClient` applies its shared ledger and cumulative $15 cap. This pilot additionally enforces a persistent $0.50 incremental cap across all `omnidoc-dev/` ledger tags, including failed and unsettled calls. With a $0.30 next-request reservation, paid calls stop when accounted charges exceed $0.20. A retained reservation can stop the pilot earlier. The persistent marker is `omnidoc-dev-wave.json`; changing output directories does not reset tagged spending.

Bodies and private labels are hashed, prices and their provenance are snapshotted, and all hashes are verified before client construction. Clef transport may use lossless WebP with decoded-pixel equality verified. Requests still exceeding body, text or base64 boundaries are honestly refused, without implicit cropping, further resolution reduction or automatic retries. Cached successful bodies may replay; failed identical requests require investigation and remain failed.

Reports retain every logical observation, including refused, unattempted, failed and malformed responses. Confusion counts distinguish unknown references from unscored requests. Provider charges are deduplicated by shared-ledger index. Positive reported charges take precedence; zero or missing reported charges can use frozen catalog rates and reported token counts as labeled estimates. Missing usage/rates remain unknown, and partial estimates do not become complete totals. Ledger reservations remain separate from effective charges.

Pages/min uses transmitted page observations divided by total serial HTTP time; preparation and replay are excluded. Pages/$ uses completed logical observations and known effective charges, with replay retained explicitly. Resource measurements cover CPU image preparation, encoding, lossless transport and artifact writes, with current-executable high-water RSS. They are separate from hosted HTTP timing. No local GPU is used.

## Corrected baseline and JPEG transport intervention

The original v3 run used an undocumented text-object item in `state`; its image and question fields were documented, but text handling remains unverified. Preserve its artifacts as diagnostic evidence. The corrected v4 baseline uses plain-string text state and is the primary comparison. It has the same 256 logical conditions and provider admission bounds.

`--prepare --jpeg80-only` prepares the separately named `jpeg80-rgb1200` arm in `omnidoc-dev-presence-v5-jpeg80`: 64 logical requests on the same 16 pages and four models. It keeps the exact RGB1200 dimensions, encodes actual 8-bit RGB JPEG at quality 80 with 4:2:0 sampling, and records original resized PNG bytes/hash, JPEG bytes/hash and actual decoded-pixel-change status. This is lossy evidence, distinct from PNG/WebP pixels. It does not adapt quality, crop or silently resize. All directories share the same tagged $0.50 cap.

To halt gracefully after the current in-flight request, create `STOP` in the pilot directory or `omnidoc-dev.STOP` next to the shared ledger. Remaining logical requests stay unattempted. Remove the marker to resume. A model also stops after its first provider failure or malformed response; its remaining requests stay unattempted, including on resume. Other models continue within the shared cap. Failed identical requests are not retried.

The [official OpenRouter guide](https://openrouter.ai/docs/guides/community/multimodal-decisions), checked 2026-10-08, requires top-level image parts and plain-string text items, accepts PNG/JPEG/WebP data URLs, and limits Clef to four images. It describes admission from base64 length at approximately four characters per token against a 65,536-token window, with images below roughly 300 KB advised. Our 200,000-character base64 cap and 4,000-byte text cap are local conservative bounds, rather than documented exact provider maxima. They remain unchanged in this intervention.
