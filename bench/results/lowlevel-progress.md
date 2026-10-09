# Lower-level decision research progress

Updated 2026-10-09T17:56:50.589914+00:00. Runs remain in progress. Counts are distinct frozen request bodies, not independent documents.

| Experiment | Successful bodies | Failed bodies | Planned bodies | Manifest records |
| --- | ---: | ---: | ---: | ---: |
| basic-final | 768 | 0 | 768 | 768 |
| history-v2 | 309 | 1 | 392 | 392 |
| prompt-factors | 400 | 0 | 512 | 544 |
| frontier-basic | 69 | 0 | 648 | 648 |
| compact-basic | 71 | 1 | 384 | 384 |
| compact-history | 72 | 0 | 240 | 240 |
| matched-history | 95 | 1 | 96 | 288 |
| images-focus | 277 | 1 | 1728 | 1728 |
| images-rich | 0 | 0 | 864 | 864 |
| gateway-text | 10 | 2 | 144 | 216 |
| gateway-vision | 52 | 0 | 432 | 432 |
| gateway-serialized | 10 | 2 | 144 | 216 |
| provider-cache | 0 | 0 | 24 | 24 |

Cumulative shared-ledger accounting (all research, including earlier waves):

| Component | USD |
| --- | ---: |
| Prior separately accounted API/rental | 1.02426211 |
| catalog estimate | 1.46203490 |
| provider-reported USD | 8.07888894 |
| reserved | 4.20000000 |
| Conservative accounted total | 14.76518595 |
| Authorized cumulative cap | 100.00 |

Unresolved reservations are held spending capacity, not observed charges. Published-rate estimates retain original reported zeros. Partial scores and incomplete model arms do not establish a ranking.

L005 matched raw/compact history preserved aggregate known and ambiguous scores for Jev, d1 and Luna while reducing estimated charges by 68.5%, 66.1% and 69.1%, respectively. Their ambiguity handling remains poor. PPLX has one failed raw request and cannot support the same complete cost comparison.

Gateway d1 accepts text and images. Both Laya aliases failed compact-canonical payloads with HTTP 422; serializing the same state in L010 did not resolve this. These are compatibility failures, not wrong classifications. PPLX stopped after HTTP 429 in the larger L006 sweep despite ten-second spacing. Other models continue.

All preprocessing is CPU-only. CPU time and process peak RSS are retained separately for each preparation/execution; hosted CPU/GPU usage is unmeasured. No protected heldout access. Latest full validation: 2,190 passed, 14 skipped, two expected failures; newer modules have focused checks pending the final integrated suite.

[Plan and hypotheses](../LOWLEVEL_DECISIONS.md), [matched packet scores and rates](lowlevel-matched-history.md), [Gateway details](../VERCEL_DECISIONS.md), [native CPU/RAM](lowlevel-native-performance.md).
