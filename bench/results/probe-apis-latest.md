# Per-page inspection API timings

Generated 2026-10-12 21:22 UTC. 110 documents (licensed real-world fixtures plus wild-v1 DEV variants when present), at most 20 pages each, median of 5 passes after a warmup, single thread, reused `Document`. Milliseconds per page; the p50/p90/max columns are over documents, not pages.

| Call | Median ms/page | p90 ms/page | Max ms/page |
|---|---:|---:|---:|
| `get_text` | 0.02 | 0.06 | 6.89 |
| `scan` | 2.46 | 12.64 | 41.29 |
| `get_text_spans` | 2.11 | 12.41 | 20.67 |
| `get_image_info` | 1.58 | 10.09 | 27.61 |
| `get_images (decodes)` | 8.61 | 38.97 | 107.58 |
| `get_fonts` | 0.01 | 0.03 | 0.39 |
| `widgets` | 0.00 | 0.00 | 0.53 |
| `annots` | 0.00 | 0.00 | 0.19 |
| `get_links` | 0.00 | 0.00 | 0.02 |

`get_text` hits the cached interpretation after warmup, so it is not a cold comparison; `scan()` always interprets afresh. Process peak RSS 154 MiB (getrusage, lifetime). `scan()` is one interpretation pass; `get_text_spans()` and `get_image_info()` are `scan()` with one product disabled.
