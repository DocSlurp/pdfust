# Prompt tuning progress

Generic instruction-only ablations; fixed source words, images and candidate menus. All rows are DEV; heldout remains sealed. Prompts cannot recover missing candidates.

**Quarantine:** `fresh` rows contain class-specific explanatory sentences in the source PDFs. Their admission scores are excluded from primary model conclusions. Retained for audit only. `neutral` removes those cues, but some authored prose labels become ambiguous; its binary scores are also diagnostic only. `realistic` uses the separately reviewed v2 cohort.

| Cohort / prompt | Model | Completed / planned calls | Tables exact | Prose FP | Prose unresolved | Values owned | USD | Pages/$ | API pages/min |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fresh / P001-semantic-record-schema | perplexity/pplx-decider-v1.1-27b | 24/24 | 4/16 | 0/8 | 0/8 | 131/245 | 0.001906 | 12,594 | 129.1 |
| fresh / P001-semantic-record-schema | openai/gpt-6-luna-decisions | 24/24 | 3/16 | 0/8 | 0/8 | 38/245 | 0.007161 | 3,352 | 172.0 |
| fresh / P002-wrap-boundaries | perplexity/pplx-decider-v1.1-27b | 24/24 | 4/16 | 7/8 | 0/8 | 131/245 | 0.001910 | 12,568 | 126.8 |
| fresh / P002-wrap-boundaries | openai/gpt-6-luna-decisions | 24/24 | 3/16 | 4/8 | 0/8 | 61/245 | 0.007182 | 3,342 | 105.7 |
| fresh / P003-header-data-corridors | perplexity/pplx-decider-v1.1-27b | 24/24 | 4/16 | 7/8 | 0/8 | 47/245 | 0.001917 | 12,518 | 130.7 |
| fresh / P003-header-data-corridors | openai/gpt-6-luna-decisions | 24/24 | 3/16 | 5/8 | 0/8 | 38/245 | 0.007218 | 3,325 | 123.2 |
| fresh / P004-conflicting-evidence | perplexity/pplx-decider-v1.1-27b | 24/24 | 4/16 | 7/8 | 0/8 | 107/245 | 0.001910 | 12,565 | 129.4 |
| fresh / P004-conflicting-evidence | openai/gpt-6-luna-decisions | 24/24 | 3/16 | 3/8 | 0/8 | 38/245 | 0.007182 | 3,342 | 111.4 |
| fresh / P005-lean-complete-candidate | perplexity/pplx-decider-v1.1-27b | 24/24 | 4/16 | 7/8 | 0/8 | 107/245 | 0.001863 | 12,883 | 129.0 |
| fresh / P005-lean-complete-candidate | openai/gpt-6-luna-decisions | 24/24 | 3/16 | 6/8 | 0/8 | 61/245 | 0.006947 | 3,455 | 130.7 |
| neutral / P001-semantic-record-schema | perplexity/pplx-decider-v1.1-27b | 24/24 | 4/16 | 3/8 | 1/8 | 131/245 | 0.001561 | 15,376 | 144.6 |
| neutral / P001-semantic-record-schema | openai/gpt-6-luna-decisions | 24/24 | 4/16 | 0/8 | 0/8 | 70/245 | 0.006113 | 3,926 | 145.5 |
| original / E001_balanced_evidence | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 8/12 | 0/12 | 144/144 | 0.001521 | 15,783 | 142.0 |
| original / E001_balanced_evidence | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 9/12 | 0/12 | 144/144 | 0.005871 | 4,088 | 83.4 |
| original / E002_cross_cell_relations | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 0/12 | 0/12 | 144/144 | 0.001520 | 15,793 | 145.7 |
| original / E002_cross_cell_relations | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 2/12 | 0/12 | 144/144 | 0.005869 | 4,090 | 198.3 |
| original / E003_reading_order | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 3/12 | 0/12 | 144/144 | 0.001524 | 15,748 | 144.8 |
| original / E003_reading_order | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 1/12 | 0/12 | 144/144 | 0.005888 | 4,076 | 185.1 |
| original / E004_counterevidence | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 10/12 | 0/12 | 144/144 | 0.001527 | 15,714 | 146.3 |
| original / E004_counterevidence | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 11/12 | 0/12 | 144/144 | 0.005907 | 4,063 | 190.9 |
| original / E005_image_geometry_consistency | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.001533 | 15,659 | 145.3 |
| original / E005_image_geometry_consistency | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.005931 | 4,047 | 186.9 |
| original / minimal-compare | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.001470 | 16,329 | 147.4 |
| original / minimal-compare | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 11/12 | 0/12 | 144/144 | 0.005617 | 4,273 | 130.7 |
| original / minimal-false-positive-cost | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 10/12 | 0/12 | 144/144 | 0.001472 | 16,303 | 142.2 |
| original / minimal-false-positive-cost | openai/gpt-6-luna-decisions | 24/24 | 11/12 | 10/12 | 0/12 | 132/144 | 0.005626 | 4,266 | 110.7 |
| original / minimal-semantic-table | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 0/12 | 0/12 | 144/144 | 0.001473 | 16,292 | 148.4 |
| original / minimal-semantic-table | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 4/12 | 0/12 | 144/144 | 0.005631 | 4,262 | 69.2 |
| original / minimal-symmetric-errors | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.001468 | 16,345 | 150.0 |
| original / minimal-symmetric-errors | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 11/12 | 0/12 | 144/144 | 0.005609 | 4,279 | 93.3 |
| original / minimal-terse | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.001464 | 16,394 | 147.8 |
| original / minimal-terse | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 10/12 | 0/12 | 144/144 | 0.005588 | 4,295 | 150.2 |
| original / P001-semantic-record-schema | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 0/12 | 0/12 | 144/144 | 0.001515 | 15,843 | 139.8 |
| original / P001-semantic-record-schema | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 1/12 | 0/12 | 144/144 | 0.005840 | 4,110 | 69.8 |
| original / P002-wrap-boundaries | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 4/12 | 0/12 | 144/144 | 0.001519 | 15,803 | 146.5 |
| original / P002-wrap-boundaries | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.005861 | 4,095 | 149.0 |
| original / P003-header-data-corridors | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.001526 | 15,723 | 139.0 |
| original / P003-header-data-corridors | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 12/12 | 0/12 | 144/144 | 0.005897 | 4,070 | 112.7 |
| original / P004-conflicting-evidence | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 6/12 | 0/12 | 144/144 | 0.001519 | 15,798 | 146.8 |
| original / P004-conflicting-evidence | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 10/12 | 0/12 | 144/144 | 0.005861 | 4,095 | 113.0 |
| original / P005-lean-complete-candidate | perplexity/pplx-decider-v1.1-27b | 24/24 | 12/12 | 9/12 | 0/12 | 144/144 | 0.001472 | 16,303 | 146.4 |
| original / P005-lean-complete-candidate | openai/gpt-6-luna-decisions | 24/24 | 12/12 | 10/12 | 0/12 | 144/144 | 0.005626 | 4,266 | 133.3 |
| realistic / E001_balanced_evidence | perplexity/pplx-decider-v1.1-27b | 0/28 | 0/16 | 0/8 | 8/8 | 0/245 | unknown | unknown | unmeasured |
| realistic / E001_balanced_evidence | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.019971 | 1,402 | 171.8 |
| realistic / E002_cross_cell_relations | perplexity/pplx-decider-v1.1-27b | 0/28 | 0/16 | 0/8 | 8/8 | 0/245 | unknown | unknown | unmeasured |
| realistic / E002_cross_cell_relations | openai/gpt-6-luna-decisions | 28/28 | 3/16 | 0/8 | 0/8 | 43/245 | 0.019968 | 1,402 | 189.9 |
| realistic / E003_reading_order | perplexity/pplx-decider-v1.1-27b | 0/28 | 0/16 | 0/8 | 8/8 | 0/245 | unknown | unknown | unmeasured |
| realistic / E003_reading_order | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 102/245 | 0.019990 | 1,401 | 183.6 |
| realistic / E004_counterevidence | perplexity/pplx-decider-v1.1-27b | 0/28 | 0/16 | 0/8 | 8/8 | 0/245 | unknown | unknown | unmeasured |
| realistic / E004_counterevidence | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.020013 | 1,399 | 189.2 |
| realistic / E005_image_geometry_consistency | perplexity/pplx-decider-v1.1-27b | 0/28 | 0/16 | 0/8 | 8/8 | 0/245 | unknown | unknown | unmeasured |
| realistic / E005_image_geometry_consistency | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 68/245 | 0.020041 | 1,397 | 180.6 |
| realistic / minimal-compare | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.006133 | 4,566 | 58.7 |
| realistic / minimal-compare | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.019674 | 1,423 | 191.4 |
| realistic / minimal-false-positive-cost | perplexity/pplx-decider-v1.1-27b | 0/28 | 0/16 | 0/8 | 8/8 | 0/245 | unknown | unknown | unmeasured |
| realistic / minimal-false-positive-cost | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 68/245 | 0.019685 | 1,422 | 184.0 |
| realistic / minimal-semantic-table | perplexity/pplx-decider-v1.1-27b | 27/28 | 4/16 | 0/8 | 1/8 | 128/245 | unknown | unknown | 68.6 |
| realistic / minimal-semantic-table | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 102/245 | 0.019691 | 1,422 | 188.9 |
| realistic / minimal-symmetric-errors | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.006131 | 4,567 | 57.6 |
| realistic / minimal-symmetric-errors | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 94/245 | 0.019666 | 1,424 | 184.8 |
| realistic / minimal-terse | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.006126 | 4,571 | 58.0 |
| realistic / minimal-terse | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.019640 | 1,426 | 180.9 |
| realistic / P001-semantic-record-schema | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.006185 | 4,527 | 58.9 |
| realistic / P001-semantic-record-schema | openai/gpt-6-luna-decisions | 28/28 | 3/16 | 0/8 | 0/8 | 93/245 | 0.019935 | 1,405 | 165.1 |
| realistic / P002-wrap-boundaries | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.006190 | 4,524 | 59.6 |
| realistic / P002-wrap-boundaries | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.019960 | 1,403 | 180.3 |
| realistic / P003-header-data-corridors | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 68/245 | 0.006199 | 4,517 | 58.4 |
| realistic / P003-header-data-corridors | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 68/245 | 0.020002 | 1,400 | 130.1 |
| realistic / P004-conflicting-evidence | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.006190 | 4,523 | 57.9 |
| realistic / P004-conflicting-evidence | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 102/245 | 0.019960 | 1,403 | 163.4 |
| realistic / P005-lean-complete-candidate | perplexity/pplx-decider-v1.1-27b | 28/28 | 4/16 | 0/8 | 0/8 | 128/245 | 0.006136 | 4,564 | 59.7 |
| realistic / P005-lean-complete-candidate | openai/gpt-6-luna-decisions | 28/28 | 4/16 | 0/8 | 0/8 | 68/245 | 0.019685 | 1,422 | 184.7 |

Rates use unique provider requests; local replay adds no provider throughput. Positive reported charges win; reported zero falls back to catalog pricing with observed tokens. API time excludes local preparation. Unresolved prose is not a correct rejection. All selections conserve source IDs, which is not a correctness score. Incomplete rows retain fixed quality denominators; unmeasured cases are not observed model errors. Missing response charges remain unknown.
