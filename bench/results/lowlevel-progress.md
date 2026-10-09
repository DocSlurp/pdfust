# Lower-level decision research progress

Updated 2026-10-09T18:57:39.966968+00:00. Completed checkpoint; unfinished matrix slices remain explicitly partial. Counts are request bodies, not independent documents.

| Experiment | Successful bodies | Failed bodies | Planned bodies | Manifest records |
|---|---:|---:|---:|---:|
| basic-final | 768 | 0 | 768 | 768 |
| history-v2 | 309 | 1 | 392 | 392 |
| prompt-factors | 400 | 0 | 512 | 544 |
| frontier-basic | 140 | 1 | 648 | 648 |
| compact-basic | 71 | 1 | 384 | 384 |
| compact-history | 72 | 0 | 240 | 240 |
| matched-history | 95 | 1 | 96 | 288 |
| images-focus | 1304 | 1 | 1728 | 1728 |
| images-rich | 144 | 0 | 864 | 864 |
| gateway-text | 52 | 2 | 144 | 216 |
| gateway-vision | 432 | 0 | 432 | 432 |
| gateway-serialized | 52 | 2 | 144 | 216 |
| gateway-supported | 64 | 0 | 64 | 96 |
| ocr-gate | 84 | 0 | 84 | 84 |
| natural-matrix | 40 | 0 | 480 | 480 |
| images-large | 864 | 0 | 864 | 864 |
| gateway-images-large | 0 | 0 | 216 | 216 |
| gateway-sanity | 4 | 1 | 8 | 8 |

L007 provider-cache repetition remains a separate partial experiment. L008 has 108 configurations mapped to 84 bodies. L016 has zero paid calls: native Gateway vision remains blocked pending a positive image-consumption check. L009 vision successes mean accepted requests, not verified image use.

| Cumulative ledger component | USD |
|---|---:|
| Prior separately accounted API/rental | 1.02426211 |
| catalog estimate | 1.50440000 |
| provider-reported USD | 10.23717952 |
| reserved | 6.05000000 |
| Conservative accounted total | 18.81584162 |
| Authorized cumulative cap | 100.00 |

Unresolved reservations are not observed charges. Positive reported charges take priority; zero/missing reported cost falls back to published rates times reported tokens, preserving the original zero. The L015 runner has completed; this checkpoint created no GPU rental.

## Findings and next experiments

- Fresh 512/768/1024 comparison completed all 864 calls. Luna RGB known scores rise 7/16 → 7/16 → 11/16; Flash 9/16 → 11/16 → 10/16. Format-specific paired gains, losses and rates are in the [full resolution report](lowlevel-images-large.md).
- Matched frontier crop512: Opus 46/48 known + 14/24 ambiguous abstentions; Sonnet 37/48 + 10/24; PPLX 38/48 + 0/24. PPLX exceeds Sonnet on known choices only. Haiku remains partial.
- Lossless compact state preserves aggregate Jev/d1/Luna history scores while cutting reported/estimated costs by 66–69%; equal aggregates do not guarantee identical decisions.
- Frozen geometry plus Jev words improves known choices from 28/48 to 40/48, without paired losses. It is an offline replay, not a measured cascade speedup.
- Gateway native d1 circle control fails HTTP 400. The old TypeSafe image controls all answer unresolved. Gateway image quality and resolution effects remain unverified; preserved costs still count.
- Original short-text Laya configurations complete; longer expanded and compact glyph packets still have retained compatibility failures.
- Next: pair Luna gray1024 and Flash768 with geometry gates and rolling row evidence, cross PPLX resolved criteria with fresh crops, and benchmark the [eight self-hosted candidates](../HF_DECISION_MODELS.md) using their actual decision runtimes.

Validation: full CPU-only suite 2,337 passed, 14 skipped, two expected failures; subsequent reporting/type fixes passed 43 focused tests. Whole-workspace Ruff and mypy over source/tests plus the new runners pass. No protected heldout data was accessed. Remote inference resource consumption remains unmeasured; local CPU/RSS are retained separately.

[README comparisons](../../README.md), [experiment log](../../EXPERIMENTS_LOG.md), [Gateway audit](lowlevel-gateway-native-audit.md), [geometry resources](lowlevel-geometry-performance.md).
