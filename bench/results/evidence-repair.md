# Evidence repair and tiny screenshot experiments

2026-10-08. All results are DEV. Ten authored, correlated row-wrap templates use three domain vocabularies (30 PDFs), not 30 independent producers. Gold and candidate generation are authored controls; this does not measure production candidate recall or dense-table recovery. No local GPU was used.

## Complete source-linked records

Primary outcome is exact region assembly, including source-ID cell ownership and complete records. All admitted words remain owned once or unresolved; every returned assembly passed conservation. No confidence threshold is used. The experiment-specific native boundary/explicit-legend baseline and constructed candidate oracle both reach 30/30. These are not claims about the default public table extractor.

| Model | Evidence / representation | Exact regions /30 | Mean record F1 | Median HTTP ms | Median input tokens | Reported USD |
|---|---|---:|---:|---:|---:|---:|
| openai | current | 12 | 0.400 | 273.4 | 1082 | 0.00000000 |
| openai | native | 12 | 0.400 | 286.9 | 1409 | 0.00000000 |
| openai | image128 | 12 | 0.400 | 285.3 | 1167 | 0.00000000 |
| perplexity | current | 13 | 0.433 | 321.2 | 1598 | 0.00093602 |
| perplexity | native | 20 | 0.667 | 339.0 | 2217 | 0.00133550 |
| perplexity | image128 | 15 | 0.500 | 326.0 | 1691 | 0.00099468 |
| openai | compact-current | 3 | 0.100 | 268.6 | 526 | 0.00000000 |
| openai | compact-native | 10 | 0.333 | 274.4 | 696 | 0.00000000 |
| openai | derived-native | 7 | 0.233 | 276.5 | 758 | 0.00000000 |
| openai | compact-image128 | 3 | 0.100 | 278.8 | 593 | 0.00000000 |
| openai | compact-image512 | 3 | 0.100 | 290.2 | 637 | 0.00000000 |
| perplexity | compact-current | 3 | 0.100 | 293.7 | 650 | 0.00038998 |
| perplexity | compact-native | 23 | 0.767 | 352.1 | 968 | 0.00057832 |
| perplexity | derived-native | 26 | 0.867 | 299.4 | 1052 | 0.00062044 |
| perplexity | compact-image128 | 16 | 0.533 | 316.2 | 776 | 0.00046592 |
| perplexity | compact-image512 | 15 | 0.500 | 314.0 | 776 | 0.00046592 |
| openai | fact-native | 14 | 0.467 | 281.6 | 295 | 0.00000000 |
| perplexity | fact-native | 20 | 0.667 | 291.7 | 284 | 0.00017068 |

Complete literal candidate descriptions improved Perplexity from20/30 to23/30; explicit geometry facts reached26/30. Luna regressed with the compact format (12→10, derived7), and verbalized facts reached14/30. Verbalizing facts reduced Perplexity to20/30 while lowering median input tokens to284. Preserve these losses; no model beat the native control.

With only target words/geometry, the opposing visible-layout pairs are deliberately indistinguishable. Initial forced-looking choices accidentally matched12/30 Luna and13/30 Perplexity full-document labels, but neither correctly abstained on any of the30 insufficient observations. Compact questions instead abstained on all30. Report document recovery and evidence-appropriate abstention separately: abstention is not recovered structure.

## Rolling context, morphology and placebo controls

The prespecified diagnostic subset is indices0,1,8,12,13,18,24,25,29 (nine exposed DEV cases). History comes only from preceding physical source rows; geometry counts are explicitly proxies, never known wrap events or model outcomes. Page notes can provide missing scope; historical patterns may change. No historical labels or expected choices are sent.

| Arm | Luna exact /9 | Perplexity exact /9 |
|---|---:|---:|
| prior | 4 | 6 |
| context | 4 | 6 |
| prior-summary | 4 | 6 |
| prior-both | 4 | 6 |
| native-reverse | 4 | 7 |
| image64 | 4 | 6 |
| image256 | 4 | 4 |
| image512 | 4 | 4 |
| blur128 | 3 | 6 |
| blank128 | 5 | 6 |

Raw preceding rows, proxy summaries and both together did not yield a consistent gain. Blank128 performed as well as or better than actual thumbnails on this subset; tiny-image gains are therefore not established by this representation. Larger crops and blur were not reliable improvements. Compact image arms improved Perplexity over its deliberately insufficient compact text state but lack a matched compact blank-image arm; do not attribute that difference entirely to pixels.

Correct full-resolution labels do not establish that a cue survived downsampling. “Evidence exact” against the intended image cue is only a diagnostic; no independent human visibility audit was performed for tiny images. These tests cannot qualify an automatic screenshot route.

## Caching and reproducibility

CPU pages render opaque white once at1024px longest edge, with four decoded rasters retained. Crops use64/128/256/512px longest edge; blur is Gaussian1.2px after resizing. The crop is target geometry `[40,155,540,225]`, so128px crops are only18px tall. Cache identities include PDF bytes, page, renderer binary/Python/Pillow hashes or versions, crop transform, kernel, blur, codec and blank condition. Full-page render cost remains even for a crop.

Images are bounded to20KB and requests to32KB. Exact successful hosted requests replay without extra inference. Reported latency above is original HTTP latency; replay is not a fresh service timing. Image timing excludes cache-constructor binary hashing and is not an end-to-end production claim.

Artifacts: ignored `bench/results/pdf-master-artifacts/decisions/context-run-{initial,ablations,compact,facts}.json`, per-case records, exact request/response bodies, raster caches and shared ledger. Request SHA-256 binds the exact prompt and image sent. Early context code hashes were collected late and omitted the compact module; this provenance defect is recorded by the audit and fixed for future runs. Do not call those hashes a complete pre-run code freeze.

Reproduce with `python -m bench.decision_context_run --run-hosted --arms ...`; hosted execution uses the shared reservation ledger and $15 cumulative cap. See [the central log](../../EXPERIMENTS_LOG.md), [contamination audit](evidence-contamination-audit.md), and the three [council proposals](../council/2026-10-08/inventor.md).

Decision: retain cheap native evidence and the Perplexity compact/derived DEV candidate for further independent evaluation. Do not enable a hosted default, promote the weak rolling prior, or qualify image routing from these controls.
