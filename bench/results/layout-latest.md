# Markdown and structured-output benchmark

- Run at: 2026-10-08 00:30 UTC
- Environment: Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44 / Python 3.14.7 / x86_64
- Machine: x86_64 / 8 logical CPUs
- pdfust: 0.13.0
- Font extras: none
- Source commit: 7213dec77a5504fc4cbb5de149c34c77252e27f6
- Repetitions: 5
- Selection: corpus and synthetic

One warmup plus median timings. Fresh includes opening, all-page extraction, and closing.
Reused repeats the task on one Document after warmup; it does not promise every page is cached.
Each task owns an independent Document. Synthetic generation, JSON serialization, hashing,
and output validation are outside the timer. Structured results retain all requested pages.
Output bytes are UTF-8 Markdown or compact, sorted-key UTF-8 JSON for structured results.
Reproduce: uv sync && uv run python bench/layout.py (default: five repetitions).
Save a baseline with --output /tmp/layout-baseline.json; compare with
--baseline /tmp/layout-baseline.json. Use --synthetic-only to omit corpus files.

Corpus: bill-hr815, f1040, patent-us223898, and usrguide from tests/assets/real_world.
Sources and licenses are documented in that directory's README. Synthetic cases contain
20 prose lines and one 4x3 bordered table per page, at 1, 8, and 16 pages.
Unicode cases use invisible Japanese OCR text without model inference or font extras.
The page counts exercise workloads below, at, and above the current eight-page caches.

Speedup = baseline median / candidate median; below 1.00x is a regression.
A ratio requires matching PDF and full-output SHA-256 hashes. Changed outputs need review
before claiming a speedup. Matching hashes establish repeatability, not extraction quality.

| Sample | Pages | Task | Mode | Output bytes | Median ms | Speedup |
|---|---:|---|---|---:|---:|---:|
| bill-hr815.pdf | 110 | markdown | fresh | 305995 | 668.246 | n/a |
| bill-hr815.pdf | 110 | markdown | reused | 305995 | 665.828 | n/a |
| bill-hr815.pdf | 110 | markdown-no-tables | fresh | 305995 | 399.184 | n/a |
| bill-hr815.pdf | 110 | markdown-no-tables | reused | 305995 | 401.743 | n/a |
| bill-hr815.pdf | 110 | words | fresh | 3682406 | 165.347 | n/a |
| bill-hr815.pdf | 110 | words | reused | 3682406 | 161.697 | n/a |
| bill-hr815.pdf | 110 | blocks | fresh | 346750 | 162.345 | n/a |
| bill-hr815.pdf | 110 | blocks | reused | 346750 | 152.439 | n/a |
| bill-hr815.pdf | 110 | dict | fresh | 2135821 | 147.866 | n/a |
| bill-hr815.pdf | 110 | dict | reused | 2135821 | 140.580 | n/a |
| f1040.pdf | 2 | markdown | fresh | 10358 | 31.473 | n/a |
| f1040.pdf | 2 | markdown | reused | 10358 | 5.749 | n/a |
| f1040.pdf | 2 | markdown-no-tables | fresh | 10220 | 18.613 | n/a |
| f1040.pdf | 2 | markdown-no-tables | reused | 10220 | 4.632 | n/a |
| f1040.pdf | 2 | words | fresh | 151318 | 15.511 | n/a |
| f1040.pdf | 2 | words | reused | 151318 | 1.972 | n/a |
| f1040.pdf | 2 | blocks | fresh | 11821 | 15.164 | n/a |
| f1040.pdf | 2 | blocks | reused | 11821 | 1.139 | n/a |
| f1040.pdf | 2 | dict | fresh | 84865 | 14.460 | n/a |
| f1040.pdf | 2 | dict | reused | 84865 | 0.563 | n/a |
| patent-us223898.pdf | 4 | markdown | fresh | 11475 | 73.466 | n/a |
| patent-us223898.pdf | 4 | markdown | reused | 11475 | 5.322 | n/a |
| patent-us223898.pdf | 4 | markdown-no-tables | fresh | 11475 | 38.659 | n/a |
| patent-us223898.pdf | 4 | markdown-no-tables | reused | 11475 | 5.464 | n/a |
| patent-us223898.pdf | 4 | words | fresh | 177284 | 33.363 | n/a |
| patent-us223898.pdf | 4 | words | reused | 177284 | 1.176 | n/a |
| patent-us223898.pdf | 4 | blocks | fresh | 12953 | 34.482 | n/a |
| patent-us223898.pdf | 4 | blocks | reused | 12953 | 1.113 | n/a |
| patent-us223898.pdf | 4 | dict | fresh | 99000 | 31.094 | n/a |
| patent-us223898.pdf | 4 | dict | reused | 99000 | 0.753 | n/a |
| usrguide.pdf | 27 | markdown | fresh | 56478 | 473.345 | n/a |
| usrguide.pdf | 27 | markdown | reused | 56478 | 472.460 | n/a |
| usrguide.pdf | 27 | markdown-no-tables | fresh | 56478 | 247.526 | n/a |
| usrguide.pdf | 27 | markdown-no-tables | reused | 56478 | 259.203 | n/a |
| usrguide.pdf | 27 | words | fresh | 798183 | 113.761 | n/a |
| usrguide.pdf | 27 | words | reused | 798183 | 119.666 | n/a |
| usrguide.pdf | 27 | blocks | fresh | 87501 | 124.298 | n/a |
| usrguide.pdf | 27 | blocks | reused | 87501 | 118.935 | n/a |
| usrguide.pdf | 27 | dict | fresh | 790274 | 118.392 | n/a |
| usrguide.pdf | 27 | dict | reused | 790274 | 115.200 | n/a |
| synthetic-ascii-1p | 1 | markdown | fresh | 2623 | 14.620 | n/a |
| synthetic-ascii-1p | 1 | markdown | reused | 2623 | 1.239 | n/a |
| synthetic-ascii-1p | 1 | markdown-no-tables | fresh | 2618 | 11.782 | n/a |
| synthetic-ascii-1p | 1 | markdown-no-tables | reused | 2618 | 1.036 | n/a |
| synthetic-ascii-1p | 1 | words | fresh | 27023 | 7.025 | n/a |
| synthetic-ascii-1p | 1 | words | reused | 27023 | 0.184 | n/a |
| synthetic-ascii-1p | 1 | blocks | fresh | 2881 | 7.013 | n/a |
| synthetic-ascii-1p | 1 | blocks | reused | 2881 | 0.208 | n/a |
| synthetic-ascii-1p | 1 | dict | fresh | 10692 | 7.283 | n/a |
| synthetic-ascii-1p | 1 | dict | reused | 10692 | 0.100 | n/a |
| synthetic-unicode-ocr-1p | 1 | markdown | fresh | 4504 | 24.044 | n/a |
| synthetic-unicode-ocr-1p | 1 | markdown | reused | 4504 | 1.138 | n/a |
| synthetic-unicode-ocr-1p | 1 | markdown-no-tables | fresh | 4455 | 13.706 | n/a |
| synthetic-unicode-ocr-1p | 1 | markdown-no-tables | reused | 4455 | 0.928 | n/a |
| synthetic-unicode-ocr-1p | 1 | words | fresh | 7107 | 11.605 | n/a |
| synthetic-unicode-ocr-1p | 1 | words | reused | 7107 | 0.108 | n/a |
| synthetic-unicode-ocr-1p | 1 | blocks | fresh | 4781 | 11.646 | n/a |
| synthetic-unicode-ocr-1p | 1 | blocks | reused | 4781 | 0.104 | n/a |
| synthetic-unicode-ocr-1p | 1 | dict | fresh | 12314 | 11.643 | n/a |
| synthetic-unicode-ocr-1p | 1 | dict | reused | 12314 | 0.269 | n/a |
| synthetic-ascii-8p | 8 | markdown | fresh | 20998 | 118.253 | n/a |
| synthetic-ascii-8p | 8 | markdown | reused | 20998 | 11.844 | n/a |
| synthetic-ascii-8p | 8 | markdown-no-tables | fresh | 20958 | 56.569 | n/a |
| synthetic-ascii-8p | 8 | markdown-no-tables | reused | 20958 | 7.138 | n/a |
| synthetic-ascii-8p | 8 | words | fresh | 216177 | 52.241 | n/a |
| synthetic-ascii-8p | 8 | words | reused | 216177 | 1.604 | n/a |
| synthetic-ascii-8p | 8 | blocks | fresh | 23041 | 52.105 | n/a |
| synthetic-ascii-8p | 8 | blocks | reused | 23041 | 1.466 | n/a |
| synthetic-ascii-8p | 8 | dict | fresh | 85529 | 58.304 | n/a |
| synthetic-ascii-8p | 8 | dict | reused | 85529 | 0.802 | n/a |
| synthetic-unicode-ocr-8p | 8 | markdown | fresh | 36046 | 191.623 | n/a |
| synthetic-unicode-ocr-8p | 8 | markdown | reused | 36046 | 9.403 | n/a |
| synthetic-unicode-ocr-8p | 8 | markdown-no-tables | fresh | 35654 | 104.973 | n/a |
| synthetic-unicode-ocr-8p | 8 | markdown-no-tables | reused | 35654 | 7.840 | n/a |
| synthetic-unicode-ocr-8p | 8 | words | fresh | 56849 | 92.948 | n/a |
| synthetic-unicode-ocr-8p | 8 | words | reused | 56849 | 0.863 | n/a |
| synthetic-unicode-ocr-8p | 8 | blocks | fresh | 38241 | 93.820 | n/a |
| synthetic-unicode-ocr-8p | 8 | blocks | reused | 38241 | 0.837 | n/a |
| synthetic-unicode-ocr-8p | 8 | dict | fresh | 98505 | 99.512 | n/a |
| synthetic-unicode-ocr-8p | 8 | dict | reused | 98505 | 0.729 | n/a |
| synthetic-ascii-16p | 16 | markdown | fresh | 42005 | 468.598 | n/a |
| synthetic-ascii-16p | 16 | markdown | reused | 42005 | 451.482 | n/a |
| synthetic-ascii-16p | 16 | markdown-no-tables | fresh | 41925 | 227.002 | n/a |
| synthetic-ascii-16p | 16 | markdown-no-tables | reused | 41925 | 253.304 | n/a |
| synthetic-ascii-16p | 16 | words | fresh | 432353 | 116.560 | n/a |
| synthetic-ascii-16p | 16 | words | reused | 432353 | 101.723 | n/a |
| synthetic-ascii-16p | 16 | blocks | fresh | 46081 | 110.466 | n/a |
| synthetic-ascii-16p | 16 | blocks | reused | 46081 | 103.896 | n/a |
| synthetic-ascii-16p | 16 | dict | fresh | 171043 | 103.626 | n/a |
| synthetic-ascii-16p | 16 | dict | reused | 171043 | 100.556 | n/a |
| synthetic-unicode-ocr-16p | 16 | markdown | fresh | 72101 | 760.904 | n/a |
| synthetic-unicode-ocr-16p | 16 | markdown | reused | 72101 | 774.735 | n/a |
| synthetic-unicode-ocr-16p | 16 | markdown-no-tables | fresh | 71317 | 384.656 | n/a |
| synthetic-unicode-ocr-16p | 16 | markdown-no-tables | reused | 71317 | 383.760 | n/a |
| synthetic-unicode-ocr-16p | 16 | words | fresh | 113697 | 185.276 | n/a |
| synthetic-unicode-ocr-16p | 16 | words | reused | 113697 | 188.682 | n/a |
| synthetic-unicode-ocr-16p | 16 | blocks | fresh | 76481 | 192.444 | n/a |
| synthetic-unicode-ocr-16p | 16 | blocks | reused | 76481 | 186.810 | n/a |
| synthetic-unicode-ocr-16p | 16 | dict | fresh | 196995 | 187.444 | n/a |
| synthetic-unicode-ocr-16p | 16 | dict | reused | 196995 | 184.922 | n/a |
