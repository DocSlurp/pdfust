# Lower-level decision research progress

Updated 2026-10-09T18:17:58.837592+00:00. Work remains in progress. Counts are distinct request bodies, not independent documents.

| Experiment | Successful bodies | Failed bodies | Planned bodies | Manifest records |
| --- | ---: | ---: | ---: | ---: |
| basic-final | 768 | 0 | 768 | 768 |
| history-v2 | 309 | 1 | 392 | 392 |
| prompt-factors | 400 | 0 | 512 | 544 |
| frontier-basic | 92 | 1 | 648 | 648 |
| compact-basic | 71 | 1 | 384 | 384 |
| compact-history | 72 | 0 | 240 | 240 |
| matched-history | 95 | 1 | 96 | 288 |
| images-focus | 1120 | 1 | 1728 | 1728 |
| images-rich | 144 | 0 | 864 | 864 |
| gateway-text | 52 | 2 | 144 | 216 |
| gateway-vision | 148 | 0 | 432 | 432 |
| gateway-serialized | 52 | 2 | 144 | 216 |
| gateway-supported | 0 | 0 | 64 | 96 |
| ocr-gate | 0 | 0 | 84 | 108 |
| natural-matrix | 0 | 0 | 480 | 480 |

L007 separately plans 24 distinct bodies transmitted three times each (72 provider requests), gated on successful originals. L008 has 108 labeled configurations / 84 distinct bodies; 512/native aliases share evidence.

| Cumulative ledger component | USD |
| --- | ---: |
| Prior separately accounted API/rental | 1.02426211 |
| catalog estimate | 1.48764890 |
| provider-reported USD | 8.77627441 |
| reserved | 5.45000000 |
| Conservative accounted total | 16.73818542 |
| Authorized cumulative cap | 100.00 |

Reservations include unresolved failures and any currently in-flight request; they are not observed charges. Positive reported charges win, otherwise published-rate estimates preserve the original reported zero.

## Results that support a follow-up

- Matched compact packets preserve aggregate known/ambiguous scores for Jev, d1 and Luna while reducing estimated charges by 68.5%, 66.1% and 69.1%. Ambiguity handling remains poor.
- Offline source-only geometry plus Jev words improves 28/48 to 40/48 authored known choices, with zero paired regressions and unchanged 0/24 ambiguous abstentions. Actual cascade cost/latency remains unmeasured.
- Geometry plus PPLX minimal typed/resolved input reaches 14/16 known and 4/8 ambiguous abstentions. Resolved crop512 reaches 15/16 and 1/8. These are 24 authored logical cases, not generalization evidence.
- Gateway d1 accepts images and completed all text controls. Laya compact packets still return HTTP 422 after string serialization; supported text representations and a separate compatibility diagnosis continue.
- PPLX L006 and Haiku L003 stopped on HTTP 429. Their incomplete arms cannot support complete model rankings.

All local processing is CPU-only. Preparation/execution retain process CPU and peak RSS separately; provider CPU/GPU is unmeasured. Integrated suite: 2,274 passed, 14 skipped, two expected failures; later modules have focused checks. No protected heldout access.

[Plan](../LOWLEVEL_DECISIONS.md), [matched costs and scores](lowlevel-matched-history.md), [all geometry/model combinations](lowlevel-hybrid-basic.md), [prompt combinations](lowlevel-hybrid-prompts.md), [Gateway](../VERCEL_DECISIONS.md), [CPU/RAM](lowlevel-native-performance.md).
