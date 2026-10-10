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

The frozen PPLX selector controls are text-only, 128 RGB and 512 RGB, using the same full48 Luna/Sonnet candidate inputs. They are pending independent verification. Selector costs will be incremental and separate from generation; selected-only quality will give no baseline credit to abstained, failed or duplicate/no-question crops. Their frozen settings remain unchanged.

Independent verification authenticated external code maps and source/PDF hashes, reconstructed retained actual requests and strict parse/whole-page composition/Markdown, and checked complete source inventory. Scorer-only cohort metrics use the frozen confirmation references; generated states/prompts were not changed. All48 primary counts and ignored evaluation records include operational errors. No new inference was performed by this evaluator.
