# L001 progress

Updated 2026-10-09T16:55:15.985681+00:00. Hosted execution is in progress; these are completion/accounting observations, not a matched quality ranking.

| Model | Completed / planned requests | Failures | Known effective USD |
| --- | ---: | ---: | ---: |
| liquid/d1 | 100 / 168 | 0 | 0.06759336 |
| typesafe/jev-1.13 | 114 / 168 | 0 | 0.02910470 |
| perplexity/pplx-decider-v1.1-27b | 154 / 216 | 0 | 0.05751744 |
| openai/gpt-6-luna-decisions | 147 / 216 | 0 | 0.08432690 |

Full initial matrix: 24 logical cases, 72 encoded pages, 768 requests, 2,304 conditional grouping decisions. Separate history freeze: 12 logical cases, 36 encoded pages, 392 requests, 1,152 decisions. No protected heldout access. Current CPU validation: 2,104 tests passed, 14 skipped, two expected failures.

[Plan, hypotheses and preflight verdicts](../LOWLEVEL_DECISIONS.md). [CPU/RAM comparison](lowlevel-native-performance.md). [Evidence audit](lowlevel-evidence-audit.md).
