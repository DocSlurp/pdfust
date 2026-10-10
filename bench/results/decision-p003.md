# P003 decision-model research: progress

Updated 2026-10-10 19:55 UTC. These are first DEV screens, not production settings. All rows use the same sixteen natural pages: twelve positive, four negative, 53 tables and 2,333 reference cell anchors. Protected silver remains untouched.

## Quality and operational coverage

Crop transcription uses identical YOLO proposals and 1024 px JPEG90 crops, with each serving provider pinned. Source-ID treatments use OCR300 and 512 px evidence. Failed pages remain in every quality denominator.

| Model / treatment | Outputs / 16 | Complete / 53 | Strict cells / 2,333 | Text cells / 2,333 | Structure cells / 2,333 | Exact positives / 12 | Negative FP / 4 | Extra / missing tables |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Haiku source IDs, OCR300 | 16 | 3 | 384 | 397 | 465 | 2 | 0 | 1 / 38 |
| PPLX gate + Haiku source IDs | 16 | 3 | 384 | 397 | 465 | 2 | 0 | 1 / 38 |
| Haiku 5.5 | 15 | 3 | 393 | 406 | 491 | 2 | 1 | 1 / 37 |
| GPT-6 Luna | 16 | 3 | 784 | 795 | 1045 | 2 | 0 | 5 / 30 |
| Gemma 4 26B A4B | 12 | 3 | 201 | 201 | 267 | 2 | 0 | 0 / 43 |
| Qwen 3.5 9B (HTTP 429) | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 53 |
| Ministral 14B | 13 | 2 | 263 | 263 | 331 | 2 | 0 | 1 / 41 |
| Gemma 4 31B | 14 | 3 | 264 | 268 | 319 | 2 | 1 | 2 / 41 |
| Ministral 8B | 12 | 2 | 252 | 252 | 303 | 2 | 0 | 2 / 43 |
| Gemini 3.5 Flash Lite (HTTP 400) | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 53 |

## Throughput and costs

Rates count operational pages, including empty outputs on negatives. The two provider-failure rows completed only two no-crop pages, so their rates do not describe model inference throughput. Costs include failed attempts; local compute is unpriced. All runs below are serial.

| Model / treatment | Pages/minute | Pages/API USD | Effective API USD |
| --- | ---: | ---: | ---: |
| Haiku source IDs, OCR300 | 2.455 | 786.97 | 0.02033110 |
| PPLX gate + Haiku source IDs | 2.292 | 660.97 | 0.02420686 |
| Haiku 5.5 | 8.491 | 1,822.07 | 0.00823240 |
| GPT-6 Luna | 4.188 | 1,234.11 | 0.01296482 |
| Gemma 4 26B A4B | 1.083 | 4,945.25 | 0.00242657 |
| Qwen 3.5 9B (HTTP 429) | 6.856 | Unknown | Unknown; USD 0.30 reserved |
| Ministral 14B | 4.955 | 3,130.72 | 0.00415240 |
| Gemma 4 31B | 2.597 | 5,755.63 | 0.00243240 |
| Ministral 8B | 6.836 | 3,860.07 | 0.00310875 |
| Gemini 3.5 Flash Lite (HTTP 400) | 6.689 | Unknown | Unknown; USD 0.30 reserved |

Luna accounting is independently reconciled from all nineteen raw responses: positive BYOK upstream charges plus a known zero gateway charge total USD 0.012964825. The original reported zeros, historical report and five former reservations remain preserved in the audit history. Zero charges elsewhere fall back to published serving rates when reported token counters are sufficient.

## Findings and next experiments

- The PPLX gate plus rolling-context bundle ties the source-ID control, with 19.06% more API cost in this pair. This does not isolate the context effect.
- Luna recovers substantially more cell anchors than the new Haiku run, but both complete only three tables. Smaller transcription models often fail strict rectangular/merged-cell validation. No malformed outputs are silently repaired.
- Qwen returned HTTP 429; Gemini returned HTTP 400. Their circuits stopped after the first failed request. These are route failures, not evidence of poor extraction ability. Alternate routes and request compatibility need separate tests.
- The earlier authenticated Sonnet run on identical crop pixels recovered 982 strict anchors and five complete tables. Its same-request repeats recovered only 289 and 287 strict anchors: dense-page atomic failures make the single best run unstable. A posthoc oracle choosing entire Luna/Sonnet crop answers reaches 1,088 strict anchors but still only five complete tables; adding Haiku reaches 1,097. These optimistic ceilings use DEV references only in offline evaluation and are not model-selected results.
- Exact whole-token source inventory can represent at most 1,880/2,333 anchors and 9/53 complete tables, even allowing arbitrary order and unlimited reuse. Better decisions cannot recover text absent from their evidence.
- Five additional gate screens completed. A new 29-arm batch tests blinded whole-crop selection and bounded row-boundary edits against frozen baselines. Source proposals and independent image/prompt treatments follow.

## Resources and reproducibility

Each completed run retains parent CPU time and RSS sampled every 100 ms, plus separate detector-worker measurements. Parent RSS ranges from approximately 326 to 714 MiB in these screens; OCR source-ID assembly consumes substantially more CPU than direct image transcription. Worker peaks are not added to parent peaks. No local GPU was used; hosted GPU utilization is unmeasured. Detailed resource/cache tables can be regenerated with `python -m bench.p003_progress` from explicit verified run paths.


| Treatment | Parent wall s | Parent CPU s | Parent peak RSS MiB | Detector request CPU s | Detector peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Haiku source IDs, OCR300 | 390.99 | 777.38 | 713.67 | 15.31 | 1106.71 |
| PPLX gate + Haiku source IDs | 418.78 | 787.86 | 675.83 | 13.84 | 1093.33 |
| Haiku 5.5 | 106.00 | 17.38 | 328.80 | 14.98 | 1121.11 |
| GPT-6 Luna | 229.23 | 17.59 | 335.23 | 15.36 | 1109.99 |
| Gemma 4 26B A4B | 664.79 | 16.48 | 337.17 | 14.54 | 1119.00 |
| Qwen 3.5 9B (HTTP 429) | 17.50 | 10.35 | 326.49 | 14.82 | 1122.80 |
| Ministral 14B | 157.43 | 16.07 | 329.32 | 15.99 | 1125.75 |
| Gemma 4 31B | 323.50 | 16.51 | 330.92 | 15.86 | 1131.84 |
| Ministral 8B | 105.32 | 16.86 | 336.41 | 15.60 | 1136.98 |
| Gemini 3.5 Flash Lite (HTTP 400) | 17.94 | 10.36 | 326.82 | 14.18 | 1139.60 |

Detector CPU sums request intervals only; initialization is retained separately. Detector RSS is the maximum sampled request RSS, never added to the parent peak.

The [research contract](../DECISION_RESEARCH_P003.md) defines the USD 50 wave ceiling and eight-hour deadline. Root-owned independent code digest maps authenticate frozen source, exact requests/responses, outputs and evaluations. Raw artifacts remain ignored under `pipeline-p003/`. Provider cache tokens are recorded separately from local replay.

## Additional gate screens, 19:55 UTC

All use the same OCR300 source and 512 px generation evidence, with rolling-row context and Haiku generation. These arms ran concurrently; their rates are contended and should not be ranked against serial timings above.

| Gate | Outputs / 16 | Complete / 53 | Strict / 2,333 | Text / 2,333 | Negative FP / 4 | Extra / missing | Pages/minute | Pages/API USD | API USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Tev text | 16 | 0 | 181 | 194 | 0 | 0 / 49 | 2.118 | 856.14 | 0.01868844 |
| d1 text | 15 | 3 | 304 | 317 | 0 | 1 / 42 | 1.719 | 687.46 | 0.02181930 |
| Solar text | 7 | 0 | 124 | 124 | 0 | 0 / 50 | 0.552 | Unknown | Unknown |
| Solar Flash text | 16 | 0 | 0 | 0 | 0 | 0 / 53 | 2.205 | 1,338.00 | 0.01195815 |
| Clef image | 16 | 3 | 352 | 365 | 0 | 19 / 40 | 1.783 | 210.94 | 0.07584980 |

d1 lost one page to a duplicate source-word index in downstream generation. Solar timed out and retained USD 0.30 as an unresolved reservation; its seven outputs include empty pages. Solar Flash selected prose or unresolved on every gate. Clef admitted more regions but produced nineteen extra tables. None improves the 384 strict-anchor source-ID control in this screen.

The queue supervisor and one Clef Omni child were SIGKILLed for an unconfirmed reason. Five independently complete reports remain valid; partial Clef Omni output has no quality conclusion, and queue aggregate throughput is unavailable. A monitored transient user service now owns subsequent paid queues.

Parent CPU seconds / peak sampled RSS MiB: Tev 956.9 / 740.3; d1 986.2 / 723.2; Solar 967.9 / 736.2; Solar Flash 963.1 / 731.6; Clef 913.3 / 741.3. Scope and sampling match the resource section above.

Coverage analysis separates acquisition from transcription: 1,043 of Luna’s 1,549 missed strict anchors belong to insufficiently covered proposals. An unconstrained YOLO + fixed-grid union contains at least 95% of 39/53 reference table areas, versus 26/53 for YOLO. Actual bounded, deduplicated, semantically gated union extraction remains to be tested. See [coverage analysis](p003-coverage-analysis.md).

Rust color regions were measured on 96 page/size/threshold combinations. Broad background components can contain tables without locating them: at 512 px / threshold 36, area inclusion reaches 40 tables but IoU >= 0.5 reaches only six. This is not an extraction-quality gain.

On eighteen retained gate images, grayscale8 and 16-color palette PNGs use 42.7% and 24.7% of original RGB bytes. These are encoding measurements only; quality, token accounting and resolution effects require fresh decision calls.
