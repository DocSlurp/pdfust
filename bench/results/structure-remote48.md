# Structured PDF recovery experiments

Run: 2026-10-08T04:57:08.275703+00:00

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
| corpus-senate-expenditures | olmocr-text | unscored | — | — | 0/23 | 83.105 | 27.49 | ok |
| corpus-nics-background-checks-2015-11 | olmocr-text | unscored | — | — | 0/12 | 264.915 | 37.19 | truncated |
| corpus-f1040 | olmocr-text | unscored | — | — | — | 32.111 | 31.65 | ok |
| corpus-senate-expenditures | olmocr-compact-text | unscored | — | — | 0/23 | 32.784 | 20.05 | ok |
| corpus-nics-background-checks-2015-11 | olmocr-compact-text | unscored | — | — | 0/12 | 17.271 | 25.36 | ok |
| corpus-f1040 | olmocr-compact-text | unscored | — | — | — | 15.851 | 22.72 | ok |
| corpus-senate-expenditures | qwen-text | unscored | — | — | 0/23 | 244.615 | 14.24 | truncated |
| corpus-nics-background-checks-2015-11 | qwen-text | unscored | — | — | 0/12 | 29.381 | 20.06 | ok |
| corpus-f1040 | qwen-text | unscored | — | — | — | 19.673 | 16.73 | ok |
| corpus-senate-expenditures | repair-qwen-text | unscored | — | — | 0/23 | 0.033 | — | ok |
| corpus-nics-background-checks-2015-11 | repair-qwen-text | unscored | — | — | 0/12 | 0.001 | — | ok |
| corpus-f1040 | repair-qwen-text | unscored | — | — | — | 0.001 | — | ok |

## Run provenance

```json
{
  "started_at": "2026-10-08T04:57:08.275703+00:00",
  "environment": "Linux-5.15.0-141-generic-x86_64-with-glibc2.39",
  "python": "3.12.3",
  "source_commit": "75ea032",
  "remote_spend_authorized_usd": 15,
  "remote_spend_usd": 1.024262108,
  "remote_instance_id": 54777034,
  "remote_hourly_usd": 0.4333333333333333,
  "native_runtime": "published pdfust 0.13.0 wheel used only to import runner; all model inputs frozen locally",
  "host_scope": "48 GiB A6000 memory/output-budget controls; separate from 24 GiB baseline",
  "seed_metadata_started_at": "2026-10-08T04:51:00.292628+00:00",
  "original_archive_report_sha256": "c2f6bd6c224df7c8e08d323457bf71dfd37224fb195cff17ec2b2dcc94615408",
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
| 0 | olmocr-text | 366.254 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 1 | olmocr-compact-text | 9.448 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 2 | qwen-text | 64.163 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 3 | repair-qwen-text | 0.000 | 1 | cpu | none |

Full dependency versions, per-result run indexes, code hashes, and retained-run provenance are in JSON.
