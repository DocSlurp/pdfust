# Image-only wrapped-expression retrieval

2026-10-08. Frozen DEV comparison:24 authored PDF pages, six matched queries with two positives each, and two no-match controls. All three image conditions and both models were fixed before scored image requests. No response-dependent tuning occurred. This is not an independent held-out test.

Image embeddings receive pixels only. Native extracted text is used only by the separate literal baseline. Query expressions include wrapped/hyphenated payment terms, currencies, financial measures, wavelength units and dosage. Near-number/unit/reordering distractors and the same words in separate ruled cells test more than topic retrieval.

The declared relevance policy requires the expression within one logical/cell-local record. Cross-cell and reordered-text negatives are stricter than general semantic similarity and are not human-adjudicated business gold. Do not claim semantic comprehension or exact-string proof from this small synthetic retrieval score.

| Model | Image | Correct first hit /6 | Correct in top3 /6 | MRR | Positive-vs-hard-negative wins /24 | Median HTTP ms/page | Median input tokens/page | Image indexing reported USD |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| google | page128 | 5 | 6 | 0.917 | 20 | 898.3 | 258 | 0.00306504 |
| google | page512 | 5 | 6 | 0.917 | 22 | 872.9 | 258 | 0.00306504 |
| google | oracle-roi512 | 5 | 6 | 0.889 | 19 | 858.6 | 258 | 0.00306504 |
| voyageai | page128 | 3 | 6 | 0.694 | 17 | 353.8 | 89 | 0.00072000 |
| voyageai | page512 | 6 | 6 | 1.000 | 22 | 363.3 | 362 | 0.00291963 |
| voyageai | oracle-roi512 | 6 | 6 | 1.000 | 23 | 352.5 | 123 | 0.00099533 |

Voyage512px whole pages recovered a correct first hit for all six queries; 128px fell to3/6. Gemini reached5/6 at both sizes. The known ROI improved Voyage pair discrimination but hurt Gemini versus its whole page. Oracle ROI locations come from fixture construction; crop discovery is not demonstrated.

All arms return a neighbor for both absent expressions when forced to rank. No similarity/abstention threshold is calibrated. Image retrieval is a candidate-finding path, not exact expression verification, text recovery, or table extraction.

The native normalized-literal baseline returns three matches per query: both positives plus the same-word cross-cell distractor. Its displayed hit@1/MRR happen to be perfect under document-ID tie order; that is not evidence of better discrimination. The meaningful observation is2/3literal-match precision under the declared policy,12hard-negative pair ties, and zero literal matches for the two absent queries.

Both models share one vector per image and separately embedded queries. Gemini queries use the provider-documented `task: search result | query:` prefix; Voyage uses raw query text, without unverified gateway task parameters. This is a documented configuration comparison, not identical prompting. Vectors must be finite, complete, correctly indexed and equal-dimensional; local cosine scoring rejects malformed results. No OCR/native text enters document embedding inputs.

Provider-reported usage and charge are authoritative, including zero; never replace them with catalog estimates. Image-indexing costs above exclude one shared8-query request per model and two initial one-query smoke probes. Reported HTTP time excludes CPU render/crop/cache construction and telemetry export; subsequent queries can reuse indexed vectors but still require query embedding.

Frozen manifest: `341245b59b28ede468d372876303096645bacf8d2ffde2f9354d24faa7525060`. Ignored evidence lives in `bench/results/pdf-master-artifacts/decisions/retrieval/` with manifest, scores, complete rankings, image hashes and ledger references. Exact hosted bodies/outputs stay in the common ledger artifact directory. The runner source was later formatted/type-annotated; exact request hashes remain authoritative for sent inputs.

Reproduce: `python -m bench.decision_retrieval_run --run-hosted`. [Design and scorer](embedding-design.md), [contamination audit](evidence-contamination-audit.md), [experiment log](../../EXPERIMENTS_LOG.md).

Decision: carry forward512px whole-page image indexing as a retrieval candidate; validate on genuinely unseen independently curated documents before claiming business accuracy. Do not replace exact structure recovery or absence checks with nearest-neighbor similarity.
