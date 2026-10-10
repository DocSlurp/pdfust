# P003 frozen fresh48 confirmation

All four independently verified generation treatments attempted the same predeclared 48 new pages: 32 natural pages (50 tables, 3,866 cells, eight negatives) and 16 authored designs (16 tables, 337 cells, two negatives). Source selection excluded known DEV/training source IDs and parent groups before reference attachment and inference. No protected heldout sources were accessed. The source-only manifest and separate scorer references remain immutable.

These are single observations of separately declared models and representations. Haiku uses matrix strict while Luna and Sonnet use legacy transcription, so their difference does not isolate a model effect. All failures remain in the complete denominators; no retry, other-model fallback or fresh-result tuning receives credit.

| Cohort | Treatment | Strict / expected cells | Text | Structure | Complete / expected tables | Missing / extra | Negative FP | Errors / pages |
| --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| omnidoc | Luna / legacy | 2130 / 3866 | 2143 | 2876 | 9 / 50 | 9 / 0 | 0 / 8 | 1 / 32 |
| authored | Luna / legacy | 337 / 337 | 337 | 337 | 16 / 16 | 0 / 0 | 0 / 2 | 0 / 16 |
| omnidoc | Sonnet / legacy | 1554 / 3866 | 1558 | 2119 | 11 / 50 | 19 / 0 | 0 / 8 | 3 / 32 |
| authored | Sonnet / legacy | 337 / 337 | 337 | 337 | 16 / 16 | 0 / 0 | 0 / 2 | 0 / 16 |
| omnidoc | Haiku / matrix strict | 2327 / 3866 | 2337 | 3537 | 11 / 50 | 8 / 1 | 0 / 8 | 1 / 32 |
| authored | Haiku / matrix strict | 337 / 337 | 337 | 337 | 16 / 16 | 0 / 0 | 0 / 2 | 0 / 16 |
| omnidoc | Ordinal OCR / Haiku | 1743 / 3866 | 1749 | 1992 | 7 / 50 | 19 / 2 | 0 / 8 | 4 / 32 |
| authored | Ordinal OCR / Haiku | 337 / 337 | 337 | 337 | 16 / 16 | 0 / 1 | 1 / 2 | 0 / 16 |

| Full48 treatment | Strict /4203 | Complete /66 | Usable /48 | Effective API USD | Attempts | Contended wall s | Usable pages/min | Usable pages/APIUSD |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Luna / legacy | 2467 | 25 / 66 | 47 / 48 | 0.029278725 | 52 | 562.380 | 5.01440 | 1605.26 |
| Sonnet / legacy | 1891 | 27 / 66 | 45 / 48 | 0.500746 | 55 | 424.260 | 6.36403 | 89.87 |
| Haiku / matrix strict | 2664 | 27 / 66 | 47 / 48 | 0.0351338 | 53 | 438.047 | 6.43767 | 1337.74 |
| Ordinal OCR / Haiku | 2080 | 23 / 66 | 44 / 48 | 0.0643005 | 39 | 976.764 | 2.70280 | 684.29 |

Rates count operational complete-pipeline outputs, not exact pages or complete tables. Costs include every attributed attempt and failure. Luna preserves reported gateway zero and uses provider-reported upstream plus gateway USD; the other three use provider-reported USD. No cost/time allocation to natural or authored subsets is inferred. Runs used contended transport concurrency three; these are not serial throughput measurements. Parent CPU/RSS, separate detector worker usage, cache-counter coverage and compact authenticated provenance are retained in [the progress report](p003-confirmation-progress.md).

The predeclared text-only, 128 RGB and 512 RGB selector controls are now independently verified below; no settings changed.

Independent verification authenticated external code maps and source/PDF hashes, reconstructed retained actual requests and strict parse/whole-page composition/Markdown, and checked complete source inventory. Scorer-only cohort metrics use the frozen confirmation references; generated states/prompts were not changed. All48 primary counts and ignored evaluation records include operational errors. No new inference was performed by this evaluator.

## Frozen PPLX selector confirmation

All three predeclared controls passed independent replay on the full48 Luna/Sonnet candidate pool. Primary quality counts only actually selected complete crops: abstention, failure, duplicate/no-question and historical baseline retention contribute zero tables. The controls made 39 requests each to the same declared PPLX model with no transport errors, observed other-model substitution or retry. Existing generation costs remain separate.

| Control / cohort | Strict / expected cells | Text | Structure | Complete / expected tables | Missing / extra | Negative FP | Primary page errors / pages |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| 0 / all48 | 1515 / 4203 | 1520 | 1542 | 23 / 66 | 29 / 0 | 0 / 10 | 4 / 48 |
| 0 / omnidoc | 1222 / 3866 | 1227 | 1249 | 9 / 50 | 27 / 0 | 0 / 8 | 3 / 32 |
| 0 / authored | 293 / 337 | 293 | 293 | 14 / 16 | 2 / 0 | 0 / 2 | 1 / 16 |
| 128 / all48 | 1605 / 4203 | 1610 | 2246 | 16 / 66 | 26 / 0 | 0 / 10 | 4 / 48 |
| 128 / omnidoc | 1481 / 3866 | 1486 | 2122 | 10 / 50 | 16 / 0 | 0 / 8 | 3 / 32 |
| 128 / authored | 124 / 337 | 124 | 124 | 6 / 16 | 10 / 0 | 0 / 2 | 1 / 16 |
| 512 / all48 | 1793 / 4203 | 1798 | 2435 | 25 / 66 | 17 / 0 | 0 / 10 | 4 / 48 |
| 512 / omnidoc | 1480 / 3866 | 1485 | 2122 | 10 / 50 | 16 / 0 | 0 / 8 | 3 / 32 |
| 512 / authored | 313 / 337 | 313 | 313 | 15 / 16 | 1 / 0 | 0 / 2 | 1 / 16 |

| Control | Selected / unresolved choices | Fully chosen pages /48 | Incremental API USD | All questions | Question attempts/min | Questions/APIUSD | Legacy retained strict / complete |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 0 | 31 / 8 | 24 / 48 | 0.00098172 | 39 | 5.77470 | 39726.19 | 2545 / 26 |
| 128 | 30 / 9 | 23 / 48 | 0.00107728 | 39 | 5.00563 | 36202.29 | 2546 / 26 |
| 512 | 39 / 0 | 31 / 48 | 0.00111316 | 39 | 4.90621 | 35035.39 | 2545 / 26 |

The 128 and 512 controls recover nearly equal natural strict cells (1,481 versus 1,480), while text recovers 1,222. Their full48 difference is concentrated in authored outcomes: 128 retains nine abstentions and recovers 124/337 authored cells, versus 512 with no abstentions and 313/337 cells. The text control recovers 293 authored cells. These single-run confidence/abstention differences do not establish a stable image-size optimum; no fresh-result selection or revised prompt/threshold follows.

All controls retain the same status inventory: 31 completed incremental pages, 13 no-question pages, two pages blocked by another generation baseline failure, one first-baseline failure and one failed incremental page. Primary errors count the three generation-blocked pages plus the incremental failure across all48; abstained choices contribute no tables. The legacy retained pipeline happens to report 47 operational outputs and about 2,545 strict cells, which includes unchanged history and is not decision success. The primary table does not award that credit.

Question rates use every fresh attempt and the contended incremental parent wall interval. Full-pipeline rates for selectors remain undefined. Generation includes complete model-specific runs and all their costs; it is not silently allocated to selected crops. Parent CPU/RSS and provenance/cache coverage appear in the progress report. Independent replay also preserves failed generation tails: crops explicitly never requested after an earlier failure do not invent absent request bodies; any actual request/call evidence remains mandatory.
