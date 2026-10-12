# Structured PDF recovery experiments

Run: 2026-10-08T05:26:02.201730+00:00

Page 0 of each preserved input is evaluated. Full inputs, screenshots, positioned words, prompts,
raw responses, validated patches, and errors are retained locally in `structure-artifacts/`.
Reference cells are independent fixture definitions; corpus cells without a reference remain unscored.
Source agreement is not ground truth, especially for missing Unicode, scans, or OCR corrections.
Geometry bullet results score their underlying recovered cells, not reparsed bullet labels.
Timing covers the adapter after preparation, excluding fixture extraction/rendering; prepared baselines
are replayed, so their timing is not a conversion measurement. Process RSS is cumulative high-water RSS.
Model repetitions include the first inference; initialization is reported separately. No throughput claims.
CUDA figures are observed peak allocated bytes for retained generation calls, not reserved VRAM.
The provenance device is the requested backend; native geometry/OCR and replay/repair adapters use CPU.

| Case | Adapter | Exact grid | Cells | Relations recalled | Record cells | Seconds | CUDA GiB | Result |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| two-column-order | qwen-compact-patch | unscored | — | — | — | 6.395 | 7.66 | TypeError: each cell must contain a list of source word IDs |
| table-bordered | qwen-compact-patch | unscored | — | — | — | 4.037 | 7.33 | TypeError: patch root must be a JSON object with a tables list |
| table-borderless | qwen-compact-patch | unscored | — | — | — | 6.413 | 7.33 | TypeError: patch root must be a JSON object with a tables list |
| table-merged | qwen-compact-patch | unscored | — | — | — | 4.185 | 7.33 | TypeError: patch root must be a JSON object with a tables list |
| corpus-senate-expenditures | qwen-compact-patch | unscored | — | — | — | 173.432 | 9.77 | JSONDecodeError: Expecting property name enclosed in double quotes: line 165 column 17 (char 4684) |
| corpus-nics-background-checks-2015-11 | qwen-compact-patch | unscored | — | — | — | 222.146 | 12.96 | ValueError: patch exhausted its output token boundary |
| table-wrapped-records | qwen-compact-patch | unscored | — | — | — | 6.248 | 7.33 | TypeError: patch root must be a JSON object with a tables list |
| text-structure-and-literals | qwen-4bit-compact-patch | unscored | — | — | — | 30.547 | 2.65 | TypeError: each cell must contain a list of source word IDs |
| positioned-math | qwen-4bit-compact-patch | unscored | — | — | — | 10.867 | 2.59 | JSONDecodeError: Expecting ',' delimiter: line 2 column 188 (char 189) |
| math-actualtext | qwen-4bit-compact-patch | unscored | — | — | — | 3.330 | 2.58 | JSONDecodeError: Expecting ',' delimiter: line 3 column 2 (char 53) |
| two-column-order | qwen-4bit-compact-patch | unscored | — | — | — | 9.710 | 2.92 | TypeError: each cell must contain a list of source word IDs |
| table-bordered | qwen-4bit-compact-patch | unscored | — | — | — | 3.987 | 2.59 | JSONDecodeError: Expecting ',' delimiter: line 2 column 89 (char 90) |
| table-borderless | qwen-4bit-compact-patch | unscored | — | — | — | 3.905 | 2.59 | JSONDecodeError: Expecting ',' delimiter: line 2 column 86 (char 87) |
| table-merged | qwen-4bit-compact-patch | unscored | — | — | — | 3.488 | 2.59 | JSONDecodeError: Expecting ',' delimiter: line 2 column 86 (char 87) |
| table-borderless-aligned | qwen-4bit-compact-patch | unscored | — | — | — | 3.605 | 2.59 | JSONDecodeError: Expecting ',' delimiter: line 2 column 84 (char 85) |
| rotated-columns | qwen-4bit-compact-patch | unscored | — | — | — | 15.879 | 2.92 | TypeError: each cell must contain a list of source word IDs |
| footnotes-and-page-furniture | qwen-4bit-compact-patch | unscored | — | — | — | 9.921 | 2.59 | TypeError: patch root must be a JSON object with a tables list |
| corpus-senate-expenditures | qwen-4bit-compact-patch | unscored | — | — | — | 314.947 | 5.03 | ValueError: patch exhausted its output token boundary |
| corpus-nics-background-checks-2015-11 | qwen-4bit-compact-patch | unscored | — | — | — | 333.249 | 8.22 | ValueError: patch exhausted its output token boundary |
| table-borderless-rotate-90 | qwen-4bit-compact-patch | unscored | — | — | — | 3.750 | 2.59 | TypeError: patch root must be a JSON object with a tables list |
| table-borderless-rotate-180 | qwen-4bit-compact-patch | unscored | — | — | — | 6.633 | 2.59 | TypeError: patch root must be a JSON object with a tables list |
| table-borderless-rotate-270 | qwen-4bit-compact-patch | unscored | — | — | — | 4.201 | 2.59 | TypeError: patch root must be a JSON object with a tables list |
| table-borderless-scanned | qwen-4bit-compact-patch | unscored | — | — | — | 4.401 | 2.58 | TypeError: patch root must be a JSON object with a tables list |
| table-wrapped-records | qwen-4bit-compact-patch | unscored | — | — | — | 6.686 | 2.59 | TypeError: patch root must be a JSON object with a tables list |
| text-structure-and-literals | qwen-lora-4bit-compact-patch | unscored | — | — | — | 35.997 | 2.66 | JSONDecodeError: Expecting ',' delimiter: line 1 column 400 (char 399) |
| positioned-math | qwen-lora-4bit-compact-patch | False | — | — | — | 10.542 | 2.60 | ok |
| math-actualtext | qwen-lora-4bit-compact-patch | unscored | — | — | — | 6.008 | 2.60 | ValueError: unknown or duplicated source ID: p0w1 |
| two-column-order | qwen-lora-4bit-compact-patch | True | — | — | — | 1.597 | 2.93 | ok |
| table-bordered | qwen-lora-4bit-compact-patch | unscored | — | — | — | 10.632 | 2.60 | JSONDecodeError: Expecting ',' delimiter: line 1 column 120 (char 119) |
| table-borderless | qwen-lora-4bit-compact-patch | False | 0/9 | 0/12 | — | 10.716 | 2.60 | ok |
| table-merged | qwen-lora-4bit-compact-patch | unscored | — | — | — | 10.570 | 2.60 | JSONDecodeError: Expecting ',' delimiter: line 1 column 120 (char 119) |
| table-borderless-aligned | qwen-lora-4bit-compact-patch | False | 0/8 | 10/10 | — | 11.865 | 2.60 | ok |
| rotated-columns | qwen-lora-4bit-compact-patch | True | — | — | — | 1.626 | 2.94 | ok |
| footnotes-and-page-furniture | qwen-lora-4bit-compact-patch | unscored | — | — | — | 16.413 | 2.60 | ValueError: unknown or duplicated source ID: p0w12 |
| corpus-senate-expenditures | qwen-lora-4bit-compact-patch | unscored | — | — | — | 540.260 | 5.04 | ValueError: patch exhausted its output token boundary |
| corpus-nics-background-checks-2015-11 | qwen-lora-4bit-compact-patch | unscored | — | — | 0/12 | 9.129 | 8.23 | ok |
| table-borderless-rotate-90 | qwen-lora-4bit-compact-patch | False | 1/9 | 0/12 | — | 9.200 | 2.60 | ok |
| table-borderless-rotate-180 | qwen-lora-4bit-compact-patch | False | 0/9 | 0/12 | — | 8.339 | 2.60 | ok |
| table-borderless-rotate-270 | qwen-lora-4bit-compact-patch | False | 0/9 | 0/12 | — | 8.402 | 2.60 | ok |
| table-borderless-scanned | qwen-lora-4bit-compact-patch | unscored | — | — | — | 5.199 | 2.60 | ValueError: unknown or duplicated source ID: Left |
| table-wrapped-records | qwen-lora-4bit-compact-patch | False | 0/12 | 4/17 | — | 15.059 | 2.60 | ok |
| corpus-senate-expenditures | qwen-4bit-compact-row-patch | unscored | — | — | — | 51.846 | 2.62 | TypeError: each cell must contain a list of source word IDs |
| corpus-nics-background-checks-2015-11 | qwen-4bit-compact-row-patch | unscored | — | — | — | 14.286 | 2.78 | TypeError: each cell must contain a list of source word IDs |
| corpus-senate-expenditures | qwen-lora-4bit-compact-row-patch | unscored | — | — | — | 68.420 | 2.64 | JSONDecodeError: Expecting ',' delimiter: line 1 column 840 (char 839) |
| corpus-nics-background-checks-2015-11 | qwen-lora-4bit-compact-row-patch | unscored | — | — | — | 4.967 | 2.79 | ValueError: unknown or duplicated source ID: p0w1 |

## Run provenance

```json
{
  "started_at": "2026-10-08T05:26:02.201730+00:00",
  "environment": "Linux-5.15.0-141-generic-x86_64-with-glibc2.39",
  "python": "3.12.3",
  "source_commit": "75ea032",
  "remote_spend_authorized_usd": 15,
  "remote_spend_usd": 1.024262108,
  "remote_instance_id": 54777034,
  "remote_hourly_usd": 0.4333333333333333,
  "native_runtime": "published pdfust 0.13.0 wheel used only to import runner; all model inputs frozen locally",
  "host_scope": "Remote-only continuation and matched NF4 base/LoRA comparison; local queue disabled by user",
  "seed_metadata_started_at": "2026-10-08T04:51:00.292628+00:00",
  "original_archive_report_sha256": "233d61ed683e690f9b05d30143fb40c8f007f3ee1ce673d5cbef00dcb05cd545",
  "bootstrap_source_commit": "75ea032",
  "source_provenance_note": "source_commit identifies worker bootstrap; per-run source_files_sha256 describe later worker code changes",
  "observation_code_sha256": "5a1f588ac88fc76515aaa9253d93e1b6a249a4311eedfcd4ffc2979b30d665e3",
  "spend_scope": "Shared whole-study total, including API and rental; do not add totals across reports",
  "remote_cleanup_verified": true,
  "spend_breakdown": {
    "reported_at": "2026-10-08T06:16:29.886431+00:00",
    "rental_provider_reported_usd": 0.684,
    "rental_provider_query_at": 1791440003.470863,
    "api_provider_reported_usd": 0.340262108,
    "api_requests": 138,
    "unsettled_api_requests": 0,
    "combined_provider_reported_usd": 1.024262108,
    "authorized_cap_usd": 15,
    "billing_note": "Provider-reported snapshot after destruction; rental rows are rounded to three decimals",
    "instance_id": 54777034,
    "instance_removed": true,
    "archive_sha256": "31a21270168baa6d283aaea4c40ea2aa2b1ea227d798a9a0657a4f66c047c825"
  }
}
```

| Run | Adapter | Initialization seconds | Repetitions | Device | Model |
| --- | --- | ---: | ---: | --- | --- |
| 0 | qwen-compact-patch | 11.457 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 1 | qwen-4bit-compact-patch | 20.032 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 2 | qwen-lora-4bit-compact-patch | 18.681 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 3 | qwen-4bit-compact-row-patch | 19.697 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 4 | qwen-lora-4bit-compact-row-patch | 19.389 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |

Full dependency versions, per-result run indexes, code hashes, and retained-run provenance are in JSON.
