# Library OCR-fill validation (wild-v1 DEV)

Generated 2026-10-12 21:15 UTC; `Page.ocr_fill`, dpi 200, 2 OCR threads, PP-OCR via pdfust-ocr-models. Synthetic DEV documents; not a real-world claim.
Text F1 is character-bigram multiset overlap against truth (`bench/wild_corpus.audit_pdf`). `Recorded` is the bench-only policy in `bench/results/wild-v1-latest.md`.

| Arm | Docs | Text F1 | Recorded | Markdown F1 | Table cell recall | Pages | Filled words | s/page | cpu s/page |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| L8_mixed+adaptive | 24 | 0.795 | 0.795 | 0.756 | 0.367 | 32 | 1128 | 15.02 | 12.75 |
| L8_mixed+fill | 24 | 0.835 | 0.835 | 0.799 | 0.500 | 32 | 851 | 31.01 | 23.22 |
| L8_mixed+native | 24 | 0.705 | 0.705 | 0.690 | 0.414 | — | 0 | nan | nan |
| L9_broken_tounicode+adaptive | 24 | 0.751 | 0.751 | 0.713 | 0.462 | 32 | 1745 | 26.52 | 23.21 |
| L9_broken_tounicode+fill | 24 | 0.745 | 0.745 | 0.708 | 0.463 | 32 | 1648 | 25.97 | 22.95 |
| L9_broken_tounicode+native | 24 | 0.003 | 0.003 | 0.003 | 0.000 | — | 0 | nan | nan |

`s/page` is wall time of `ocr_fill` plus the in-memory text/Markdown rebuild, measured on a host shared with other jobs (load average noted in the commit message), so treat it as an upper bound; `cpu s/page` is process CPU time (`getrusage`, whole process including OCR threads).
