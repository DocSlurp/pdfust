# P002 source-only generation evidence serialization

The fixed natural16 retained-source diagnostic measured complete source packets at 256- and 1,024-word region budgets on 2026-10-09. Lossless arrays reduced UTF-8 packet bytes by 15–16%. Quarter-unit geometry reduced bytes by 57–58% and introduced at most 0.125 display-unit coordinate error. These are serialization measurements; no model calls or quality comparisons were performed.

## Transport contracts

`evidence_format="objects"` is the unchanged default. Tests pin byte-identical pre-change anchor and matrix requests, including their system instructions and response schemas. The alternative `arrays` encodes each complete source word as `[id,text,bbox]`, with an explicit field and display-coordinate legend. IDs, literal text, word order, boxes, page bounds and viewport remain lossless.

`quarter` uses those same arrays and rounds only word bbox coordinates to the nearest 0.25 display units, with ties to even. The packet declares the maximum error of 0.125. IDs and text remain byte-identical; page bounds and viewport remain unchanged. Rounding is monotonic and finite; extremely large representable coordinates already spaced at quarter units remain unchanged. Source coordinates retained outside the request are not replaced. Both response parsers continue validating against the original source inventory and geometry.

Source admission remains 4,096 words and 16,000 ID/text characters. Formatting happens before the existing 128,000-character packet admission; no format truncates evidence or bypasses source admission. A synthetic complete 1,200-word float-heavy packet refused in object form fits as arrays. Unknown formats fail explicitly. Non-source metadata is excluded from all formats.

## Fixed cached-source observations

The 16 known DEV pages have 7,351 cached extraction/OCR words. Source-only geometric splitting uses maximum ID/text characters 16,000 and word budgets 256 or 1,024. The respective partitions contain 47 and 28 regions. All rows retain original-source and encoded-packet hashes.

| Word budget | Format | Complete regions | Total UTF-8 bytes | Largest packet bytes | Bytes saved versus objects | Largest coordinate error | Packet refusals |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 256 | objects | 47 | 807,847 | 28,496 | 0% | 0 | 0 |
| 256 | arrays | 47 | 683,030 | 23,967 | 15.45% | 0 | 0 |
| 256 | quarter | 47 | 344,459 | 11,933 | 57.36% | 0.125 | 0 |
| 1,024 | objects | 28 | 805,196 | 111,295 | 0% | 0 | 0 |
| 1,024 | arrays | 28 | 674,375 | 92,459 | 16.25% | 0 | 0 |
| 1,024 | quarter | 28 | 335,044 | 45,610 | 58.39% | 0.125 | 0 |

All natural16 packets already fit in object form. The 1,024-word object maximum leaves relatively little room below the character admission compared with arrays. UTF-8 bytes and admission characters are recorded separately; the admission is unchanged and still measures characters. Token counts are unmeasured: no explicit local model tokenizer was supplied. No byte-derived token estimate is presented as measured or provider-reported usage. System instructions, response schemas, and image payloads are outside these packet-only byte totals.

The complete diagnostic took 0.721 wall seconds and 0.714 own-process CPU seconds. Linux getrusage reported 30,672 KiB process-lifetime peak RSS; RSS was not sampled. Scope covers reading cached sources, validation, splitting, serialization, hashing and comparison, excluding original extraction/OCR and any inference. This short local run is not a model latency or cost claim.

## Reproduction and validation

Run `python -m bench.pipeline_generation_evidence --manifest <natural16 manifest> --sources-directory <natural16-generate-sonnet directory> --output <new report.json>`. An optional `--tokenizer-json <explicit local tokenizer JSON>` measures tokens using that local tokenizer, labeled separately from provider-reported usage. The tokenizer loader does not fetch assets. Detailed rows remain in ignored `bench/results/pdf-master-artifacts/pipeline-p002/generation-evidence-natural16-v2.json`.

Eight new encoding tests plus 46 existing generation/matrix tests pass; Ruff lint and format checks pass. Tests cover exact legacy bytes, lossless arrays, immutable Unicode IDs/text, quarter-unit error and finite ordered geometry, metadata exclusion, encoding before packet admission, retained source limits, extreme finite coordinates and unknown-format rejection. No network, credentials, inference or scoring references were accessed.
