# P002 single-document native smoke

The final experimental CLI extracted all four generated pages successfully, with zero hosted calls, zero ledger attempts and USD 0 cost. Retained outputs are under `bench/results/pdf-master-artifacts/pipeline-p002/document-smoke-final/`; the complete document is `native-all/document.md`, with page artifacts and provenance linked from `native-all/document.json`. This is a generated-source smoke test, not corpus quality scoring.

The source contains an upright 2×2 grid, two-column prose, bold/list/link examples, and the same grid with page rotation 90°. PDF SHA-256: `1e38989d5cf559f2bc8637bc8e667dea41dee9f799e459a8866646936f70a0af`. Runtime: Python 3.14.7, pdfust 0.13.0, Linux x86_64, eight logical CPUs, one native runner worker. No OCR, detector, network inference or local GPU was needed for these text-bearing pages.

Commands ran from `/home/dan/code/oss/jev-pdf-p002-evaluation` at revision `764ca965e40c0722ef19bc767b966f92ce81b0b3`:

```sh
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.extract_document /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002/document-smoke-final/constructed.pdf --output /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002/document-smoke-final/native-all --mode native
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.extract_document /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002/document-smoke-final/constructed.pdf --output /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002/document-smoke-final/native-subset --mode native --page 3 --page 1
```

The first command exited 0 with `complete=true`, 4/4 requested pages successful. The subset exited 2 with `complete=false`, `status=partial`, and `requested_pages_complete=true`: pages 2 and 4 were retained in physical page order, and omitted pages were never counted as complete. Reproduction needs a new output directory; existing artifacts are refused.

| Physical page | Source words | Retained physical table matrix | Corrected logical matrix |
| --- | ---: | --- | --- |
| 1 | 4 | `[[Name, Value], [Alpha, 42]]` | Same |
| 2 | 115 | No native table | No native table |
| 3 | 22 | No native table | No native table |
| 4 | 4 | `[[Alpha, Name], [42, Value]]` | `[[Name, Value], [Alpha, 42]]` |

All 145 source words have exactly one table/prose owner and one ledger entry. Each corrected page and document page summary reports `source_conserved=true`; structures additionally report `accounting_complete=true` and `source_inventory_complete=true`. Corrected source word dictionaries equal the original child dictionaries, including display boxes and line metadata. Table provenance is `native-source`. Page 4 retains original/effective rotation 90° and original physical child artifacts; only separate logical sidecars change table indexing. The 16 prose lines appear once each, left column lines 1–8 followed by right column lines 1–8. The subset preserves all 119 selected words with the same checks. Compact verification observations are retained in `verification.json`.

Native child configuration is frozen with `rotation_mode=preserve`, `source_order=original`. Every retained correction helper copy was checked against its recorded SHA-256. Relevant identities:

| Artifact | SHA-256 |
| --- | --- |
| Frozen wrapper | `3660601411b0cff229be39d90e8d61029b40cd6edc68858bff5071321e5bbae1` |
| Native orientation helper | `c75766aaf3e2407fe9f720dbedb9fd31199bccd0128e93a3d73b4c96c8bbba26` |
| Source order helper | `938a5a1f25837b636957266e08e347c0d775329db11af6f9ee7a55503d31b68d` |
| Installed native extension | `c33611249b961c358c952de48de3a3b7011b92fda7bc1c51a2db36e91d2a9a59` |
| Complete document Markdown | `892930685800de9a3fa98e4bf3dc7d0e49564eef5cbde1e1aa33232524bd36c2` |
| Complete document JSON | `cb260085a94e5023f0d374d24256a6b0fb165c00ae84ed918cb44610e3dec945` |

| Measurement | All four pages | Two-page subset |
| --- | ---: | ---: |
| Runner child processing wall | 0.068603 s | 0.048297 s |
| Runner child process CPU | 0.072043 s | 0.050240 s |
| Runner child sampled peak RSS | 39,993,344 bytes | 39,874,560 bytes |
| Parent correction/aggregation wall | 0.098481 s | 0.071398 s |
| Parent correction/aggregation CPU | 0.100975 s | 0.072444 s |
| Wrapper dispatch wall | 0.377896 s | 0.364879 s |

The child measures RSS with psutil every 100 ms and CPU with `process_time`; these short runs do not establish a true allocation peak. Parent correction RSS and full wrapper CPU/RSS are unmeasured. Dispatch includes child startup and correction/aggregation before final combined-file writing; it overlaps the other wall intervals and must not be added to them. Each run has zero calls, zero ledger attempts and zero reported/accounted/effective cost.

Rich presentation remains limited: bold and link labels survive as plain paragraph text, bullet/number strings survive literally, but this experimental wrapper emits no bold markup, list structure, heading hierarchy or hyperlink target. Source-owned words/geometry and logical native tables are verified here; full rich-format fidelity is not claimed. Input admission remains 64 MiB and default 128 pages (explicit maximum 4096); combined Markdown has a separate 64 MiB cap. OCR assets are needed for image-only input, which this smoke does not exercise.
