# P003 decision-model research: progress

Updated 2026-10-10 19:04 UTC. Running; these are first DEV screens, not selected production settings. All rows use the same sixteen natural pages: twelve positive, four negative, 53 tables and 2,333 reference cell anchors. No protected silver data was read.

## Quality and operational coverage

| Model / treatment | Operational pages | Complete tables | Strict span + text anchors | Exact text anchors | Exact positive pages | Negative pages with false positives | Extra / missing tables |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Haiku source IDs, OCR300 | 16/16 | 3/53 | 384/2,333 | 397/2,333 | 2/12 | 0/4 | 1 / 38 |
| Haiku 5.5 crop transcription, 1024 JPEG90 | 15/16 | 3/53 | 393/2,333 | 406/2,333 | 2/12 | 1/4 | 1 / 37 |
| Luna crop transcription, 1024 JPEG90 | 16/16 | 3/53 | 784/2,333 | 795/2,333 | 2/12 | 0/4 | 5 / 30 |

## Throughput and measured resources

Rates count operational pages, including complete empty outputs on negatives. API prices include failed attempts; local CPU electricity and amortization are unpriced. Parent CPU/RSS exclude the separately measured detector subprocess. RSS is sampled every 100 ms. No local GPU was used; hosted GPU utilization is unmeasured.

| Treatment | Pages/minute | Pages/API USD | API USD | Parent wall seconds | Parent CPU seconds | Parent peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Haiku source IDs, OCR300 | 2.455 | 786.97 | 0.02033110 | 390.994 | 777.379 | 713.67 |
| Haiku 5.5 crop transcription, 1024 JPEG90 | 8.491 | 1,822.07 | 0.00823240 | 105.997 | 17.379 | 328.80 |
| Luna crop transcription, 1024 JPEG90 | 4.188 | Pending reconciliation | Pending reconciliation | 229.232 | 17.587 | 335.23 |

The original Luna report has five unresolved reservations because cache-write prices were unavailable. All nineteen raw responses contain a positive BYOK upstream cost alongside OpenRouter's reported zero. An offline read of these fields totals USD 0.012964825; independent cost reconciliation is in progress. Original reports and reported zeros remain unchanged. The accounting client now retains upstream and gateway amounts separately for new requests. See [OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting).

## Interpretation and next experiments

- The additional PPLX gate plus rolling context ties the source-ID control on aggregate quality while costing 19.06% more. Individual page differences and generation noise remain; this is not an isolated context ablation.
- Luna has more correct cell anchors in its first crop run, but no more complete tables. Haiku has one atomic output error and one negative-page false positive. Repeat before drawing a model ranking.
- An optimistic source-token inventory audit finds only 1,880/2,333 anchors and 9/53 complete tables representable by exact whole-token joins. Arbitrary order and unlimited reuse make this an upper bound, not achievable quality. Whitespace-relaxed matching raises the necessary bound to 2,110 anchors and 23 tables.
- Eight pinned crop transcription routes are running. Prepared next: broad typed-model gate comparisons, source-derived OCR/raster proposals, row-boundary repair, whole-crop candidate selection, and independent prompt/evidence/image-size treatments.

## Reproduction and retained evidence

The [research contract](../DECISION_RESEARCH_P003.md) defines the USD 50 wave ceiling and the eight-hour deadline. Each run retains frozen source/code/runtime/configuration, actual requests, responses, per-page outputs, resources and independently verified evaluation JSON under ignored `pipeline-p003/<run>/`. Root-controlled code digest maps are separate from run self-attestations. Raw development artifacts are not published.
