# OmniDoc DEV JPEG80 transport preparation

The separately frozen `jpeg80-rgb1200` arm uses the same 16 official research-only DEV images and the exact RGB1200 full-page dimensions. It encodes actual 8-bit RGB JPEG at quality 80 with 4:2:0 sampling. It is lossy evidence: decoded pixels changed on all 16 pages. This preparation measures admission and bytes, not decision quality. No hosted calls were made by the preparing agent.

| Model | RGB1200 PNG/lossless transport admitted / 16 | JPEG80 admitted / 16 | JPEG80 refused / 16 |
|---|---:|---:|---:|
| Luna Decisions | 10 | 16 | 0 |
| PPLX Decider | 10 | 16 | 0 |
| Clef Flash | 3 | 7 | 9 |
| Clef | 3 | 7 | 9 |

The corrected v4 baseline admits 26/64 RGB1200 requests. The v5 JPEG80 intervention admits 46/64, leaving 18 honest refusals under the unchanged conservative bounds. Across 16 resized pages, original RGB PNG payloads total 9,214,450 bytes and JPEG80 totals 2,877,036 bytes, a 68.8% reduction. MIME, quality, dimensions, original resized PNG hashes/bytes, JPEG hashes/bytes and actual decoded-pixel-change flags are retained per request. No cropping, adaptive quality or silent further resolution reduction occurred; SSIM was not measured.

The primary baseline is the corrected plain-string-state v4. The earlier v3 text-object state is undocumented and its text handling remains unverified; retain it as diagnostic evidence. Both corrected v4 and JPEG80 v5 use the same documented question and text-state schema. Existing v3 artifacts were not changed.

Preparation took 4.113 seconds wall and 4.096 seconds CPU, with 550,522,880 bytes current-executable peak RSS. Measurement: `perf_counter/process_time` and `/proc/self/status VmHWM`, cumulative counters/high-water mark without periodic sampling, one CPU worker on Linux 7.2.5 / eight logical CPUs. Scope includes official image read, RGB resize, PNG/JPEG encoding, decoded-pixel comparison, body admission and artifact writes. No GPU or remote inference was used. Peak RSS covers the whole runner, including imports.

The [official OpenRouter multimodal Decisions guide](https://openrouter.ai/docs/guides/community/multimodal-decisions), checked 2026-10-08, documents plain-string text items, PNG/JPEG/WebP image data URLs, and at most four Clef images. Its approximate admission description uses base64 length at four characters per token against 65,536 tokens. The existing 200,000-character base64 and 4,000-byte text bounds are stricter local safeguards, not claimed exact provider maxima; this intervention preserves them.

All 64 logical requests, including refusals, are frozen under ignored `bench/results/pdf-master-artifacts/decisions/omnidoc-dev-presence-v5-jpeg80/`. Scoring labels remain private and outside model bodies. The v4 baseline remains separately frozen under `omnidoc-dev-presence-v4/`. All directories share the persistent `omnidoc-dev/` $0.50 cap; moving to JPEG does not reset spending. A later root-run decision comparison must retain all 16-page denominators and distinguish admission gains from accuracy gains on lossy input.
