# P001 complete-page pipeline comparison

Offline private scoring after complete pipeline runs. Chronological completed-report order; each row retains its run name. DEV authored silver supports table/non-table structure only. Operational output means retained Markdown and complete source-owned state; it does not imply semantic correctness.

Dataset SHA-256: `3a1268f1d731a7c60a3fa91f1e90e887c3f41a84aec05beed81b797253afa9b2`. Manifest bytes SHA-256: `7570272d524d68ff3aad59ac1b5ea080e48b77acf605ba8bb30bef27205b94c8`. The fixed pilot is selected by frozen manifest membership; absent results remain failures. Full and pilot cohorts have distinct denominators.

| Run | Cohort | Policy | Model | Image edge | Context rows | Legend | Normalize rotation | Gate premise | Output / pages | Exact positive pages | Negative FP pages | All / scored errors |
|---|---|---|---|---:|---:|---|---|---|---:|---:|---:|---:|
| native-r1 | full | native | CPU only | — | — | — | False | False | 177/181 | 16/35 | 0/133 | 4/1 |
| pilot-pplx-512 | pilot | assembly | perplexity/pplx-decider-v1.1-27b | 512 | 1 | True | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| native-r2 | full | native | CPU only | — | — | — | False | False | 177/181 | 16/35 | 0/133 | 4/1 |
| native-text-r1 | full | native_text | CPU only | — | — | — | False | False | 178/181 | 3/35 | 26/133 | 3/1 |
| native-r3 | full | native | CPU only | — | — | — | False | False | 177/181 | 16/35 | 0/133 | 4/1 |
| pilot-flash-512 | pilot | assembly | cloudflare/clef-flash | 512 | 1 | True | False | False | 32/32 | 5/16 | 0/16 | 0/0 |
| pilot-luna-512 | pilot | assembly | openai/gpt-6-luna-decisions | 512 | 1 | True | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| pilot-flash-256 | pilot | assembly | cloudflare/clef-flash | 256 | 1 | True | False | False | 32/32 | 3/16 | 0/16 | 0/0 |
| pilot-luna-256 | pilot | assembly | openai/gpt-6-luna-decisions | 256 | 1 | True | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| pilot-pplx-256 | pilot | assembly | perplexity/pplx-decider-v1.1-27b | 256 | 1 | True | False | False | 32/32 | 15/16 | 4/16 | 0/0 |

| Run | Exact scored pages | Complete tables / charged tables | Exact cells / expected tables | Exact spans / expected tables | Correct slots / expected / charged slots | Missing / extra tables | Conserved / checked output pages | Oracle exact positive pages |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| native-r1 | 149/168 | 16/35 | 16/35 | 16/35 | 228/437/437 | 19/0 | 177/177 | 16/35 |
| pilot-pplx-512 | 27/32 | 15/20 | 15/16 | 15/16 | 198/207/280 | 1/4 | 32/32 | 15/16 |
| native-r2 | 149/168 | 16/35 | 16/35 | 16/35 | 228/437/437 | 19/0 | 177/177 | 16/35 |
| native-text-r1 | 110/168 | 3/75 | 3/35 | 3/35 | 32/437/1149 | 32/40 | 178/178 | 3/35 |
| native-r3 | 149/168 | 16/35 | 16/35 | 16/35 | 228/437/437 | 19/0 | 177/177 | 16/35 |
| pilot-flash-512 | 21/32 | 5/16 | 5/16 | 5/16 | 63/207/207 | 11/0 | 32/32 | 15/16 |
| pilot-luna-512 | 27/32 | 15/21 | 15/16 | 15/16 | 198/207/300 | 1/5 | 32/32 | 15/16 |
| pilot-flash-256 | 19/32 | 3/16 | 3/16 | 3/16 | 36/207/207 | 13/0 | 32/32 | 15/16 |
| pilot-luna-256 | 27/32 | 15/20 | 15/16 | 15/16 | 198/207/294 | 1/4 | 32/32 | 15/16 |
| pilot-pplx-256 | 27/32 | 15/21 | 15/16 | 15/16 | 198/207/288 | 1/5 | 32/32 | 15/16 |

| Run | Output p/min | Output p/USD | Exact positive p/min | Exact positive p/USD | Wall s | CPU s | Peak sampled RSS bytes | Provider USD | Missing provider charges | Effective USD | Accounted USD | Cost bases |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| native-r1 | 3690.3 | unknown | 333.586 | unknown | 2.87782 | 2.97454 | 125878272 | 0 | 0 | 0 | 0 | {} |
| pilot-pplx-512 | 54.5532 | 10205.9 | 25.5718 | 4784.02 | 35.195 | 14.9024 | 201883648 | 0.00313544 | 0 | 0.00313544 | 0.00313544 | {"provider-reported USD": 32} |
| native-r2 | 4291.37 | unknown | 387.92 | unknown | 2.47474 | 2.56821 | 130228224 | 0 | 0 | 0 | 0 | {} |
| native-text-r1 | 4023.99 | unknown | 67.8201 | unknown | 2.65408 | 2.72698 | 132030464 | 0 | 0 | 0 | 0 | {} |
| native-r3 | 4259.93 | unknown | 385.078 | unknown | 2.493 | 2.58923 | 125640704 | 0 | 0 | 0 | 0 | {} |
| pilot-flash-512 | 31.7319 | 5318.91 | 4.9581 | 831.079 | 60.507 | 15.8482 | 192167936 | 0.00601627 | 0 | 0.00601627 | 0.00601627 | {"provider-reported USD": 32} |
| pilot-luna-512 | 67.6551 | 3136.06 | 31.7133 | 1470.03 | 28.3792 | 16.2325 | 191758336 | 0 | 0 | 0.0102039 | 0.0102039 | {"catalog estimate": 32} |
| pilot-flash-256 | 31.8398 | 5442.45 | 2.98498 | 510.23 | 60.3019 | 15.4808 | 204025856 | 0.0058797 | 0 | 0.0058797 | 0.0058797 | {"provider-reported USD": 32} |
| pilot-luna-256 | 58.3245 | 3293.03 | 27.3396 | 1543.61 | 32.9193 | 20.4373 | 192884736 | 0 | 0 | 0.0097175 | 0.0097175 | {"catalog estimate": 32} |
| pilot-pplx-256 | 46.5715 | 10445.4 | 21.8304 | 4896.26 | 41.2269 | 20.2362 | 204152832 | 0.00306356 | 0 | 0.00306356 | 0.00306356 | {"provider-reported USD": 32} |

Candidate oracle coverage uses private references to choose an already-retained complete candidate. It is reference-informed and unrunnable as an extraction policy; it does not synthesize missing candidates. Coverage is policy-specific: it scores only alternatives retained by that run. No output or model was supplied references during inference. Exactness compares complete matrices and spans after whitespace normalization; extra tables charge both table and cell denominators. Errors on negative pages remain failures, not correct zero-table pages.

Source conservation covers extracted snapshot word IDs, not all painted PDF content, Unicode mapping, visibility, OCR or semantic relations. Natural documents with incomplete references are diagnostic-only. Headings, lists, forms, equations, images and general document quality are not gold-scored. See [corpus contract](pipeline-corpus-design.md).

API cost excludes local electricity and amortization. Positive provider charges and catalog estimates retain distinct bases; missing provider counts remain visible. Accounted USD can contain reservations, which are separate from effective charges. Unknown effective totals yield unknown p/USD. Zero-cost native throughput has no finite p/USD.

<details>
<summary>Complete per-family structure scores</summary>

| Run | Family | Scored / diagnostic pages | Exact positive / positives | Negative FP / negatives | Exact scored pages | Errors |
|---|---|---:|---:|---:|---:|---:|
| native-r1 | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r1 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r1 | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| native-r1 | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| native-r1 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-r1 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-r1 | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r1 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r1 | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r1 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-r1 | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r1 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| pilot-pplx-512 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-512 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-512 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-pplx-512 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-512 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-pplx-512 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-512 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-512 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-512 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-512 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-512 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-pplx-512 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r2 | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r2 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r2 | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| native-r2 | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| native-r2 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-r2 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-r2 | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r2 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r2 | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r2 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-r2 | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r2 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | companion/borderless-plain | 6/0 | 2/6 | 0/0 | 2/6 | 0 |
| native-text-r1 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-text-r1 | companion/prose | 12/0 | 0/0 | 8/12 | 4/12 | 0 |
| native-text-r1 | companion/ruled-control | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| native-text-r1 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-text-r1 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-text-r1 | silver/merged-table | 5/0 | 0/5 | 0/0 | 0/5 | 0 |
| native-text-r1 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/multilevel-table | 5/0 | 0/5 | 0/0 | 0/5 | 0 |
| native-text-r1 | silver/reading-order | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| native-text-r1 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/sidebar | 5/0 | 0/0 | 2/5 | 3/5 | 0 |
| native-text-r1 | silver/three-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| native-text-r1 | silver/two-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| native-text-r1 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/table-bordered | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-text-r1 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-text-r1 | structure/table-merged | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/two-column-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| native-text-r1 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r3 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r3 | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| native-r3 | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| native-r3 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-r3 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-r3 | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r3 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r3 | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r3 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-r3 | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r3 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| pilot-flash-512 | companion/borderless-plain | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-flash-512 | companion/borderless-wrap | 4/0 | 3/4 | 0/0 | 3/4 | 0 |
| pilot-flash-512 | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-512 | companion/ruled-control | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-512 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-512 | silver/merged-table | 2/0 | 1/2 | 0/0 | 1/2 | 0 |
| pilot-flash-512 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/multilevel-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-512 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-flash-512 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-luna-512 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-512 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-512 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-luna-512 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-512 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-luna-512 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-512 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-512 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-512 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-512 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-luna-512 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-flash-256 | companion/borderless-plain | 4/0 | 1/4 | 0/0 | 1/4 | 0 |
| pilot-flash-256 | companion/borderless-wrap | 4/0 | 1/4 | 0/0 | 1/4 | 0 |
| pilot-flash-256 | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-256 | companion/ruled-control | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-256 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-256 | silver/merged-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-256 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/multilevel-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-256 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-flash-256 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-luna-256 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-256 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-256 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-luna-256 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-256 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-luna-256 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-256 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-256 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-256 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-256 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-luna-256 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-pplx-256 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-256 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-256 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-pplx-256 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-256 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-pplx-256 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-256 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-256 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-256 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-256 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-256 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-pplx-256 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |

</details>

Incomplete frozen runs (not scored):

No completed report exists for these frozen runs; they may be running or aborted. Result-file counts are progress evidence only. Accuracy, charges, wall/CPU and RSS remain unknown. Jobs not yet frozen by the runner are outside this observed inventory.

| Run | Policy | Model | Planned pages | Result files | Source contract matches |
|---|---|---|---:|---:|---|
| pilot-flash-1024 | assembly | cloudflare/clef-flash | 32 | 27 | True |

Measurement and frozen provenance:

- `native-r1`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "8f7920a0a1c27b64696238fbea55f3a45d7178b16087179b9d1b560ed0ca4da0", "pipeline_run.py": "08eabdb0717f044856b0e35456a7b04267378ff049f01e5b7a096a87965a889d"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-pplx-512`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "8f7920a0a1c27b64696238fbea55f3a45d7178b16087179b9d1b560ed0ca4da0", "pipeline_run.py": "3fcd576461a437ced1c8e6b65c915c52e8b5ca0ebbc0430c67424307d21fb562"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `native-r2`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `native-text-r1`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `native-r3`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-flash-512`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-luna-512`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-flash-256`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-luna-256`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-pplx-256`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
