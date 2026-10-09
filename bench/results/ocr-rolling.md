# Raster OCR to rolling assembly DEV test

Fixed corpus: 28 pages (12 borderless, 12 aligned prose negatives, four merged vector controls), `66c3cde77b110038`. The pure OCR arms use frozen rendered pixels and exact OCR region strings/IDs/bboxes. There is no native extracted text or gold-guided splitting in their inputs. Physical and rolling rules are unchanged. Native vector override is an explicitly separate hybrid arm.

| Edge | Assembly | Path | Borderless exact /12 | Prose false positives /12 | Merged exact /4 | Complete exact /28 | Refused/missing /28 | OCR ID conservation /28 |
|---|---|---|---|---|---|---|---|---|
| 640 | physical | pure | 4/12 | 12/12 | 0/4 | 4/28 | 0/28 | 28/28 |
| 640 | physical | hybrid | 4/12 | 12/12 | 4/4 | 8/28 | 0/28 | 28/28 |
| 640 | rolling | pure | 4/12 | 12/12 | 0/4 | 4/28 | 0/28 | 28/28 |
| 640 | rolling | hybrid | 4/12 | 12/12 | 4/4 | 8/28 | 0/28 | 28/28 |
| 1200 | physical | pure | 6/12 | 12/12 | 0/4 | 6/28 | 0/28 | 28/28 |
| 1200 | physical | hybrid | 6/12 | 12/12 | 4/4 | 10/28 | 0/28 | 28/28 |
| 1200 | rolling | pure | 6/12 | 12/12 | 0/4 | 6/28 | 0/28 | 28/28 |
| 1200 | rolling | hybrid | 6/12 | 12/12 | 4/4 | 10/28 | 0/28 | 28/28 |

| Edge | Kind | OCR target-token recall | Correct pure physical / rolling cell-owned tokens | Multi-token OCR regions |
|---|---|---|---|---|
| 640 | borderless | 170/180 | 74 / 74 | 42/182 |
| 640 | prose | 356/432 | 0 / 0 | 134/256 |
| 640 | ruled-control | 124/132 | 124 / 124 | 46/64 |
| 1200 | borderless | 180/180 | 90 / 90 | 42/186 |
| 1200 | prose | 432/432 | 0 / 0 | 138/294 |
| 1200 | ruled-control | 132/132 | 132 / 132 | 48/64 |

640-pixel OCR completed 28/28: 14.512s summed OCR wall, 26.572s summed worker CPU, 19.972s complete worker wall. Separate engine initialization totals: 0.332s wall / 0.342s CPU. 177.0 MiB largest worker lifetime RSS.

1200-pixel OCR completed 28/28: 37.191s summed OCR wall, 68.429s summed worker CPU, 42.899s complete worker wall. Separate engine initialization totals: 0.329s wall / 0.339s CPU. 299.9 MiB largest worker lifetime RSS.

OCR-ID conservation counts each observed region once across candidates and unresolved items; it does not measure original PDF-word recall. Target-token recall is a post-output, case-sensitive whitespace-token bag metric over expected cell text (or authored prose on negatives); it ignores order and is not CER or spatial ownership. Cell-owned tokens use the unchanged authored matrix scorer and only receive credit in correctly dimensioned candidate slots. Native hybrid tables use original PDF vectors/text; OCR IDs remain a separately checked pure-path inventory, not hybrid cell attribution.

All 28 denominators remain explicit at both scales. Missing/refused pages score as unavailable, not as successful abstentions. Engine initialization precedes each OCR timer and remains separately retained; rendering/raster preparation and native-vector preparation are separately recorded. OCR includes raster-carrier render plus recognition. CPU2 threads, max_concurrent1, tile1408, overlap192, confidence0.5; watchdog30s per OCR call,1GiB observed RSS,10min cohort. Parent samples /proc worker PID at0.05s target interval plus overhead; killing can overshoot one polling interval. SELF getrusage records worker CPU and lifetime peak RSS, including native threads; there are no worker children.

Reproduce `.venv/bin/python -m bench.ocr_rolling --prepare --run --score`. Frozen rasters, exact OCR items, candidate matrices/IDs, source/model/assembler hashes, telemetry, native-vector branch, and private scores remain ignored under `ocr-rolling-v1/66c3cde77b110038/`. No hosted spending, GPU work, training, heldout access, or production API changes occurred. This is correlated authored DEV evidence, not independent-producer validation.


Source-only geometry diagnostic at edge 640: 18/22 sparse nonnumeric physical rows have negative bbox gaps to the preceding row. The unchanged rolling rule requires a nonnegative gap before joining. OCR region padding/overlap therefore blocks these continuation candidates even when their literal text is retained. This diagnoses the current geometry interface; no bbox shrinking, OCR-string splitting, or gold-directed correction was applied.

Source-only geometry diagnostic at edge 1200: 18/18 sparse nonnumeric physical rows have negative bbox gaps to the preceding row. The unchanged rolling rule requires a nonnegative gap before joining. OCR region padding/overlap therefore blocks these continuation candidates even when their literal text is retained. This diagnoses the current geometry interface; no bbox shrinking, OCR-string splitting, or gold-directed correction was applied.

Higher resolution improves recognition and six no-wrap borderless matrices, but does not repair wrapped row joining, merged spans, or prose/table semantic admission. Pure merged cells can retain all target words while unit-span proposals fail complete merged structure. Native vector override restores four merged controls only in the separately labeled hybrid. OCR source-ID conservation is necessary but insufficient for original-word and cell ownership.


Raster and separate native-vector preparation: 0.610s wall / 0.620s CPU; 864.2 MiB process-lifetime getrusage peak RSS. This parent-process lifetime peak is distinct from per-call OCR worker memory and includes the complete 56-raster preparation pass. No preparation-memory bound is inferred from the smaller OCR worker peaks.
