# Structured recovery comparison

These are exploratory results on the preserved study inputs, not held-out production accuracy.
Each adapter's denominators describe its attempted cohort. Failed calls remain in the denominators.
Unsupported retained Docling/Marker replays are listed separately and excluded from quality totals.
Positive grids, negative controls, and visual corpus spot checks are separate measurements.
Cell and relationship totals count the reference grid; spot checks do not cover a complete corpus page.
See STRUCTURE_BENCHMARKS.md for timing, source-agreement, training, and provenance limitations.
Truncated counts are lower bounds: older failed calls can lack generation metadata in the report.

## structure-latest

Source report run: 2026-10-08T03:18:26.318705+00:00
Snapshot SHA-256: `e443782cffb2123b2f542d3e99150d7b3286c35a515d353883efd6eb972b760c`.

| Adapter | Calls | Unsupported | Positive exact | Negative exact | Cells | Relation recall | Precision | Corpus cells | Errors | Truncated |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| pdfust | 28 | 0 | 2/9 | 6/6 | 18/83 | 24/111 | 24/24 | 12/35 | 0 | 0 |
| pdfust-text | 28 | 0 | 3/9 | 5/6 | 26/83 | 34/111 | 34/56 | 12/35 | 0 | 0 |
| yolo-geometry | 28 | 0 | 3/9 | 6/6 | 34/83 | 43/111 | 43/46 | 6/35 | 0 | 0 |
| yolo-geometry-wrapped | 28 | 0 | 4/9 | 6/6 | 46/83 | 60/111 | 60/63 | 6/35 | 0 | 0 |
| olmocr-image | 28 | 0 | 4/9 | 6/6 | 65/83 | 90/111 | 90/121 | 0/35 | 0 | 1 |
| olmocr-text | 28 | 0 | 3/9 | 6/6 | 61/83 | 93/111 | 93/121 | 0/35 | 3 | 0 |
| olmocr-patch | 28 | 0 | 0/9 | 0/6 | 0/83 | 0/111 | — | 0/35 | 28 | 0 |
| geometry | 28 | 0 | 6/9 | 4/6 | 61/83 | 79/111 | 79/126 | 12/35 | 0 | 0 |
| geometry-bullets | 28 | 0 | 6/9 | 4/6 | 61/83 | 79/111 | 79/126 | 12/35 | 0 | 0 |
| geometry-wrapped | 28 | 0 | 7/9 | 4/6 | 73/83 | 96/111 | 96/143 | 29/35 | 0 | 0 |
| geometry-wrapped-bullets | 28 | 0 | 7/9 | 4/6 | 73/83 | 96/111 | 96/143 | 29/35 | 0 | 0 |
| yolo-normalized-geometry-wrapped | 28 | 0 | 7/9 | 6/6 | 73/83 | 96/111 | 96/99 | 29/35 | 0 | 0 |
| qwen-image | 28 | 0 | 0/9 | 6/6 | 0/83 | 0/111 | — | 0/35 | 0 | 1 |
| qwen-text | 28 | 0 | 0/9 | 6/6 | 0/83 | 0/111 | — | 0/35 | 1 | 3 |
| qwen-patch | 28 | 0 | 0/9 | 0/6 | 0/83 | 0/111 | 0/32 | 0/35 | 25 | 0 |
| repair-qwen-image | 28 | 0 | 0/9 | 1/6 | 21/83 | 49/111 | 49/200 | 0/35 | 0 | 0 |
| repair-qwen-text | 28 | 0 | 2/9 | 3/6 | 49/83 | 54/111 | 54/140 | 0/35 | 1 | 0 |
| retained-docling | 28 | 6 | 1/4 | 5/6 | 10/35 | 15/46 | 15/25 | 23/35 | 0 | 0 |
| retained-docling-formulas | 28 | 6 | 1/4 | 5/6 | 10/35 | 15/46 | 15/25 | 23/35 | 0 | 0 |
| retained-marker-fast | 28 | 6 | 1/4 | 6/6 | 29/35 | 28/46 | 28/46 | 12/35 | 0 | 0 |
| ocr-geometry-wrapped | 28 | 0 | 8/9 | 5/6 | 82/83 | 108/111 | 108/133 | 29/35 | 0 | 0 |
| olmocr-normalized | 3 | 0 | 3/3 | — | 27/27 | 36/36 | 36/36 | — | 0 | 0 |
| olmocr-compact-text | 7 | 0 | 1/4 | 1/1 | 36/39 | 44/53 | 44/53 | 0/35 | 1 | 0 |
| olmocr-4bit-text | 2 | 0 | — | — | — | — | — | 0/35 | 1 | 0 |
| olmocr-yolo-crop | 7 | 0 | 4/4 | 1/1 | 39/39 | 53/53 | 53/53 | 11/35 | 0 | 1 |
| olmocr-geometry-crop | 5 | 0 | 3/4 | 1/1 | 38/39 | 50/53 | 50/53 | — | 0 | 0 |
| olmocr-row-crop | 2 | 0 | — | — | — | — | — | 7/35 | 0 | 1 |
| qwen-compact-text | 7 | 0 | 0/4 | 1/1 | 0/39 | 0/53 | — | 0/35 | 0 | 0 |
| qwen-compact-patch | 5 | 0 | 0/3 | 0/1 | 0/27 | 0/36 | — | 0/23 | 5 | 0 |
| native-bullets | 28 | 0 | 1/9 | 6/6 | 17/83 | 21/111 | 21/24 | 12/35 | 0 | 0 |
| native-header-bullets | 28 | 0 | 1/9 | 6/6 | 17/83 | 21/111 | 21/24 | 35/35 | 0 | 0 |
| hybrid-html | 28 | 0 | 9/9 | 6/6 | 83/83 | 111/111 | 111/111 | 35/35 | 0 | 0 |
| hybrid-bullets | 28 | 0 | 9/9 | 6/6 | 83/83 | 111/111 | 111/111 | 35/35 | 0 | 0 |

## structure-hosted

Source report run: 2026-10-08T04:42:19.263122+00:00
Snapshot SHA-256: `f8876273d14fc47236593bedd3197fff303505f8e97522d7659ab649d68e8429`.

| Adapter | Calls | Unsupported | Positive exact | Negative exact | Cells | Relation recall | Precision | Corpus cells | Errors | Truncated |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| qwen-hosted-compact-text | 28 | 0 | 0/9 | 6/6 | 0/83 | 0/111 | — | 0/35 | 0 | 0 |
| qwen-jev-hosted-compact-text | 17 | 0 | 8/9 | 4/6 | 74/83 | 99/111 | 99/124 | 0/35 | 2 | 2 |
| qwen-hosted-image | 28 | 0 | 0/9 | 6/6 | 0/83 | 0/111 | — | 0/35 | 0 | 1 |
| qwen-hosted-compact-patch | 28 | 0 | 7/9 | 5/6 | 68/83 | 87/111 | 87/121 | 0/35 | 2 | 0 |
| jev-text-gated-geometry-wrapped | 15 | 0 | 7/9 | 6/6 | 73/83 | 96/111 | 96/99 | — | 0 | 0 |
| qwen-jev-hosted-compact-patch | 17 | 0 | 5/9 | 5/6 | 47/83 | 63/111 | 63/63 | 0/35 | 7 | 0 |
| repair-qwen-hosted-image | 28 | 0 | 6/9 | 6/6 | 63/83 | 105/111 | 105/121 | 23/35 | 0 | 0 |
| repair-qwen-hosted-compact-text | 28 | 0 | 7/9 | 6/6 | 73/83 | 96/111 | 96/116 | 23/35 | 0 | 0 |
| qwen-hosted-compact-row-patch | 2 | 0 | — | — | — | — | — | 0/35 | 2 | 0 |
| qwen-jev-hosted-compact-row-patch | 2 | 0 | — | — | — | — | — | 0/35 | 2 | 0 |

## structure-remote48

Source report run: 2026-10-08T04:57:08.275703+00:00
Snapshot SHA-256: `ad80f854a201f3fa686654ffd82b3c02aa0ad30055707473bc732d08a1e44108`.

| Adapter | Calls | Unsupported | Positive exact | Negative exact | Cells | Relation recall | Precision | Corpus cells | Errors | Truncated |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| olmocr-text | 3 | 0 | — | — | — | — | — | 0/35 | 0 | 1 |
| olmocr-compact-text | 3 | 0 | — | — | — | — | — | 0/35 | 0 | 0 |
| qwen-text | 3 | 0 | — | — | — | — | — | 0/35 | 0 | 1 |
| repair-qwen-text | 3 | 0 | — | — | — | — | — | 0/35 | 0 | 0 |

## structure-remote48-long

Source report run: 2026-10-08T05:10:56.667603+00:00
Snapshot SHA-256: `2401ae80f2031180015166ece1a20e08c8c393e3a4e4eacc23163d53ba5d48d5`.

| Adapter | Calls | Unsupported | Positive exact | Negative exact | Cells | Relation recall | Precision | Corpus cells | Errors | Truncated |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| olmocr-image | 2 | 0 | — | — | — | — | — | 0/35 | 0 | 1 |

## structure-remote-patches

Source report run: 2026-10-08T05:26:02.201730+00:00
Snapshot SHA-256: `2fa88c9fef1889db957f0f9201fdac740193813d31313049f6a47120638a0cf2`.

| Adapter | Calls | Unsupported | Positive exact | Negative exact | Cells | Relation recall | Precision | Corpus cells | Errors | Truncated |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| qwen-compact-patch | 7 | 0 | 0/4 | 0/1 | 0/39 | 0/53 | — | 0/35 | 7 | 1 |
| qwen-4bit-compact-patch | 17 | 0 | 0/9 | 0/6 | 0/83 | 0/111 | — | 0/35 | 17 | 2 |
| qwen-lora-4bit-compact-patch | 17 | 0 | 0/9 | 2/6 | 1/83 | 14/111 | 14/75 | 0/35 | 7 | 1 |
| qwen-4bit-compact-row-patch | 2 | 0 | — | — | — | — | — | 0/35 | 2 | 0 |
| qwen-lora-4bit-compact-row-patch | 2 | 0 | — | — | — | — | — | 0/35 | 2 | 0 |

## structure-remote-highres

Source report run: 2026-10-08T06:01:45.480431+00:00
Snapshot SHA-256: `32b69df4ba2ece4ebb2fce2682e5e9d89e79369455ea7e59ef4195c670014c7b`.

| Adapter | Calls | Unsupported | Positive exact | Negative exact | Cells | Relation recall | Precision | Corpus cells | Errors | Truncated |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| olmocr-highres-image | 1 | 0 | — | — | — | — | — | 0/12 | 0 | 1 |

