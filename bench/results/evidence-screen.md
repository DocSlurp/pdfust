# D001 source-selected evidence screen

Model: `perplexity/pplx-decider-v1.1-27b`. Twelve DEV pages chosen only by source-grid presence and descending word count (six per stratum). Three arms, frozen before calls; no independent validation claim.

| Arm | Correct / total | TP | FP | FN | TN | Unresolved | Effective USD | API ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| geometry | 12 / 12 | 6 | 0 | 0 | 6 | 0 | 0.001536 | 6850 |
| neighbors | 12 / 12 | 6 | 0 | 0 | 6 | 0 | 0.001710 | 7323 |
| blob | 12 / 12 | 6 | 0 | 0 | 6 | 0 | 0.001461 | 7240 |

All-three answer agreement: **12/12**. This screen measures ruled-table presence, not cell recovery. Missing/failed inputs remain unresolved; unresolved negatives do not count as true negatives. Provider probabilities are not calibrated correctness.

No automatic all-corpus expansion. Stop at this screen and prioritize candidate assembly unless a concrete evidence-dependent error warrants a separately frozen follow-up.
