# P002 frozen row evidence audit

The generic source-only feature contract was frozen in commit `e2c6e0c` before this audit. `bench.pipeline_row_evidence.build(source)` retains complete original source order, IDs, literal text and display boxes, adds row observations, and makes no table or continuation decision. `encode(packet)` produces compact JSON with a 16 MiB UTF-8 boundary; refused packets are never truncated. Source admission retains the complete-page 65,536-word and 4 MiB character bounds. No runner or default parser changed.

The feature unit is median positive word-box height, explicitly an em proxy rather than measured font em. Geometric rows use nearest half-unit vertical-center bins; start and end alignment tracks use nearest half-unit horizontal bins. Original source boxes stay exact. Each row carries signed normalized intra-row gaps, minimum/median/maximum token lengths, Unicode lexical/numeric/mixed/other role counts, terminal punctuation and lowercase-start observations. Previous and following rows supply center spacing, indentation and right-edge shifts, normalized role L1 distance, shared start/end track counts, and neighboring punctuation/case observations. Complete words stay in source order; row membership is sorted by horizontal geometry with source-order ties. These are evidence fields, not calibrated confidence, a sentence parser, or a rule that merges wrapped rows.

The explicit frozen full276 run supplied 272 complete source packets, with four missing sources retained as missing. All available pages produced admitted evidence, with no feature errors. The packets cover 6,827 geometric rows: 6,012 have intra-row gaps and 6,824 have an adjacent row. Every available source has an em proxy. Outcome strata were joined only after all packets were built: all 48 negative pages, 172 positive pages, and 56 unscored native diagnostics stay in the audit.

Compact original word-array packets have a 5,700-byte page median; complete row evidence has a 20,100-byte median. Median per-page expansion is 3.34×. The maximum evidence packet is 380,057 bytes and all packets total 11,280,210 bytes. These are UTF-8 byte counts, not tokenizer measurements, provider charges or model quality. The largest page exceeds common existing 128,000-character prompt packet admission, so any future consuming runner must retain its own transport limits and complete regional-source policy. This experiment supplies evidence rather than bypassing those limits.

| Reporting stratum/family | Pages | Packets | Median words | Median rows | Median tracks | Source bytes | Evidence bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| negative/authored/decorative | 12 | 12 | 169.5 | 15.0 | 55.5 | 10989.0 | 26169.0 |
| negative/authored/prose | 12 | 12 | 169.5 | 15.0 | 55.5 | 10989.0 | 26169.0 |
| negative/omni/no-table | 24 | 24 | 226.0 | 31.5 | 96.5 | 20381.0 | 56819.0 |
| positive/authored/blank | 12 | 12 | 30.5 | 7.5 | 32.0 | 1872.5 | 7962.5 |
| positive/authored/borderless | 12 | 12 | 36.0 | 7.5 | 32.0 | 2185.0 | 8301.0 |
| positive/authored/cropped | 12 | 12 | 36.0 | 7.5 | 32.0 | 2229.0 | 8336.5 |
| positive/authored/dense | 12 | 12 | 191.5 | 21.5 | 58.0 | 11942.0 | 32432.5 |
| positive/authored/merged | 12 | 12 | 34.0 | 7.5 | 28.0 | 2076.0 | 8122.0 |
| positive/authored/mixed | 12 | 12 | 65.0 | 13.0 | 32.0 | 3822.0 | 14428.0 |
| positive/authored/multiple | 12 | 12 | 65.0 | 13.0 | 32.0 | 3822.0 | 14428.0 |
| positive/authored/ocr-carrier | 12 | 12 | 36.0 | 7.5 | 29.5 | 3147.5 | 10035.0 |
| positive/authored/rotated | 12 | 12 | 36.0 | 7.5 | 32.0 | 2185.0 | 8301.0 |
| positive/authored/ruled | 12 | 12 | 36.0 | 7.5 | 32.0 | 2185.0 | 8301.0 |
| positive/authored/wrapped | 12 | 12 | 46.0 | 12.0 | 34.0 | 2820.0 | 12237.0 |
| positive/omni/multiple-table | 16 | 16 | 188.5 | 54.5 | 82.0 | 17037.0 | 63963.5 |
| positive/omni/single-table | 24 | 24 | 100.0 | 34.0 | 68.5 | 9675.0 | 40093.0 |
| unscored/native/bill-hr815.pdf | 19 | 19 | 400 | 49 | 122 | 34197 | 83668 |
| unscored/native/bunka-kokugo-series-019-p4.pdf | 1 | 1 | 27 | 19 | 23 | 3435 | 18442 |
| unscored/native/f1040.pdf | 2 | 2 | 1115.0 | 90.5 | 257.0 | 78066.0 | 181841.0 |
| unscored/native/mhlw-doc.pdf | 2 | 2 | 38.5 | 23.5 | 41.5 | 4807.5 | 23477.5 |
| unscored/native/nics-background-checks-2015-11.pdf | 1 | 1 | 1504 | 67 | 375 | 102013 | 200760 |
| unscored/native/patent-us223898.pdf | 4 | 4 | 568.0 | 56.0 | 107.5 | 52496.0 | 114510.5 |
| unscored/native/pdf20-simple.pdf | 1 | 1 | 2 | 1 | 4 | 233 | 838 |
| unscored/native/pdfium-jpx-lzw.pdf | 1 | 0 | — | — | — | — | — |
| unscored/native/pdfium-links-highlights-annots.pdf | 1 | 1 | 12 | 3 | 22 | 886 | 3239 |
| unscored/native/pdfium-smask-blend.pdf | 1 | 0 | — | — | — | — | — |
| unscored/native/pdfium-type3.pdf | 1 | 0 | — | — | — | — | — |
| unscored/native/senate-expenditures.pdf | 1 | 1 | 637 | 50 | 94 | 58023 | 116794 |
| unscored/native/usrguide.pdf | 19 | 19 | 317 | 39 | 134 | 29317 | 69746 |
| unscored/native/wdl6812-manuscript.pdf | 2 | 1 | 1 | 1 | 2 | 192 | 800 |

The following examples use the first available multi-row source page in manifest order per cohort. Selection does not depend on correctness, table labels, or failure status. Display excerpts are short for readability; retained packets contain every literal word and ID.

- Authored source: the title row `Operations report 101` has gaps approximately 0.591 and 0.591 units and roles [2 lexical, 1 numeric]. The next row `Column 1 Column 2 Column 3` has within-label gaps 0.278 and column separations 16.971 units. Its following row shares four start tracks; the preceding title row shares none. This exposes track and spacing differences without declaring either row to be a table.
- Native diagnostic source: `Department of the Treasury—Internal Revenue Service` has five gaps approximately 0.208 units. The next row `Form 1040 2025` has gaps 0.025 and 25.895 units, roles [1 lexical, 2 numeric], and a left-edge shift −7.700 units from its predecessor. These fields expose a heading/form transition; they do not validate record structure.
- Natural source: the first row `THE C7` has a 34.612-unit gap and lexical/mixed roles. The next row begins `WEDNESDAY, JANUARY 8, 2025 BOSTON` and has a 0.110-unit center separation from its predecessor, a 22.721-unit indentation shift, and no shared start tracks. This small center separation illustrates how mixed heading font sizes and spatial groups can occupy distinct bins without representing separate physical record baselines.

Potential next experiments can present these fields unchanged to a matched model control and test whether sentence continuity, independent role resets, wrap indentation, or alignment across neighboring rows improves precision while preserving dense, wrapped, merged and borderless positives. No threshold, prompt, case-specific routing, hard rejection, or claim of improvement was selected here. Every role observation is derived from literal source characters; OCR errors and multi-column ambiguity remain. Quantized geometry is auxiliary evidence only, never replacement source geometry.

The single-process CPU audit used 1.513 s wall time, 1.505 s process CPU time, and 405,080 KiB Linux `getrusage(RUSAGE_SELF)` high-water RSS. The scope includes dependency imports, all 276 source reads, evidence generation and retained packet writes; no subprocesses, utilization sampling, network, credentials, GPU, or provider requests were used. All 276 input result hashes remained unchanged. Eight generic tests cover source identity and Unicode, metadata independence, finite geometry, empty/degenerate evidence, duplicate admission, no truncation, and uniform-scale invariance. Ruff and focused mypy checks passed.

Complete packets and audit metadata are retained under ignored `pipeline-p002/row-evidence-audit/`; the full specification remains in `pipeline_row_evidence.SPEC`.
