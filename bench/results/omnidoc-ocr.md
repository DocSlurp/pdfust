# External DEV native OCR admission probe

Four frozen OmniDocBench images (#1 English exam, #2 Chinese academic paper, #5 Chinese report, #9 English notes), metadata-selected before OCR. CPU only, existing PP-OCRv6 small RTen weights, two threads and one admitted call. These are image-carrier PDFs, not original native PDFs. No GPU, hosted API, training, or provider spending occurred.

| Sample | Max edge | Status | OCR wall / CPU | Lifetime RSS | OCR words / chars | Text block coverage | Scored plain blocks/chars | Strict bag recall | NFKC bag recall / precision |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 640 | complete | 1.189s / 2.154s | 177.6 MiB | 38 / 756 | 20/20 | 20/714 | 0.947 | 0.951 / 0.983 |
| 1 | 1200 | complete | 2.128s / 3.860s | 281.7 MiB | 38 / 774 | 20/20 | 20/714 | 0.972 | 0.978 / 0.991 |
| 2 | 640 | complete | 1.331s / 2.405s | 178.2 MiB | 32 / 568 | 3/4 | 2/430 | 0.949 | 0.988 / 0.988 |
| 2 | 1200 | complete | 6.806s / 12.446s | 282.4 MiB | 377 / 3653 | 4/4 | 2/430 | 0.965 | 1.000 / 1.000 |
| 5 | 640 | complete | 1.439s / 2.635s | 169.9 MiB | 91 / 543 | 0/2 | 2/391 | 0.000 | 0.000 / n/a |
| 5 | 1200 | complete | 3.944s / 7.042s | 288.3 MiB | 151 / 1274 | 2/2 | 2/391 | 0.997 | 1.000 / 0.997 |
| 9 | 640 | complete | 0.339s / 0.596s | 169.3 MiB | 0 / 0 | 0/0 | 0/0 | n/a | n/a / n/a |
| 9 | 1200 | complete | 1.081s / 1.973s | 287.8 MiB | 2 / 7 | 0/0 | 0/0 | n/a | n/a / n/a |

Scoring uses nonignored text_block annotations only. Each OCR word center is assigned to one containing annotation bbox (smallest-area tie choice). Formula and table blocks are separate excluded categories; text blocks containing LaTeX markers are also excluded from character-bag metrics. Coverage counts a block with at least one OCR observation and is not recognition accuracy. Character bags count matching nonwhitespace characters per block with strict or NFKC forms. They ignore order and are not CER, word accuracy, mathematical fidelity, or complete reconstruction.

Each observed word retains a unique run-local source ID and source-image/display bbox. These records permit spatial candidate experiments but do not establish row membership or header ownership. OCR items can contain full lines, so their boxes are not guaranteed word/cell geometry. No reference answer enters OCR or image cropping; full pages and fixed scales are used. Annotations are loaded only by the scorer after observed outputs are persisted.

Timing uses perf_counter and resource.getrusage SELF user/system CPU; RSS is process-lifetime ru_maxrss. The parent samples one worker PID at a 0.05s target interval plus query overhead, kills on observed RSS above 1 GiB or OCR wall above 30s, and aborts remaining calls after a refusal. There are no worker children; threads are included. Engine initialization is separated per call in retained artifacts, and image insertion precedes the OCR timer. Rendering and recognition are both included in OCR time. Gate detection can overshoot by one sampling interval; this is a watchdog, not an OS memory reservation. Initialization and pre-OCR preparation also have a 30s watchdog.

Reproduce with `.venv/bin/python -m bench.omnidoc_ocr --run --report` in the worktree. Complete words, bboxes, initialization timings, model/image hashes, CPU measurements, and telemetry remain in ignored `omnidoc-dev/ocr-admission/`. Public benchmark pretraining contamination is unknown; these are DEV observations. OmniDocBench retains its noncommercial research restriction.


The 1200-pixel arm supplies usable positioned printed-text evidence on the three populated pages within 6.81s and 289 MiB each, but 640 pixels misses both Chinese-report prose blocks. The smaller scale is therefore not admitted as an interchangeable input for row assembly. At 1200 pixels, normalized character-bag recall reaches 0.978/1.000/1.000 for the scored English-exam/Chinese-academic/Chinese-report blocks. These are limited content-retention observations, not structural correctness or calibrated model confidence. The metadata-selected note page is essentially blank ruled paper with a small header; it has no text_block annotation and provides no handwriting or unsupported-language accuracy estimate. English and simplified-Chinese printed text both yield observations here; no other script capability is inferred.

Sample 1 edge 640 engine initialization: 0.011s wall / 0.012s CPU; 61.7 MiB lifetime RSS.

Sample 1 edge 1200 engine initialization: 0.012s wall / 0.012s CPU; 61.7 MiB lifetime RSS.

Sample 2 edge 640 engine initialization: 0.011s wall / 0.012s CPU; 61.7 MiB lifetime RSS.

Sample 2 edge 1200 engine initialization: 0.012s wall / 0.012s CPU; 61.7 MiB lifetime RSS.

Sample 5 edge 640 engine initialization: 0.020s wall / 0.020s CPU; 61.7 MiB lifetime RSS.

Sample 5 edge 1200 engine initialization: 0.011s wall / 0.012s CPU; 61.8 MiB lifetime RSS.

Sample 9 edge 640 engine initialization: 0.015s wall / 0.015s CPU; 61.8 MiB lifetime RSS.

Sample 9 edge 1200 engine initialization: 0.011s wall / 0.012s CPU; 61.7 MiB lifetime RSS.
