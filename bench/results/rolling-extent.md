# T005 local-gap extent ablation

T001–T003 remain frozen. Three separately declared extent rules trim trailing
logical rows from unchanged T003 source-owned candidates: minimum positive
logical-row top gap, nearest-rank lower quartile gap, and median of first two
gaps capped at six median word heights. Region stops use the existing three
height / 2.5 gap multipliers. Each rule preserves native vector candidates,
unknown header roles, and all removed source IDs as unresolved. These are
complementary unaccepted candidates, not automatic table admission.

The generator and all three configs were committed before source preparation
and scoring (`971f8f9`). Original28 plus reviewed V2 28 candidate freeze SHA256:
`4e8d29729df0c69ae74d0fc54b719d625e6e37b90f033654c5dcfdad29722b37`.
No policy changed after this freeze.

| Frozen rule | Original borderless exact | Native control exact | Reviewed V2 tables exact | Original / V2 prose proposals | Ambiguous proposals (unscored) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Minimum local gap | 12/12 | 4/4 | 16/16 | 12/12 + 8/8 | 4/4 |
| Lower quartile gap | 12/12 | 4/4 | 16/16 | 12/12 + 8/8 | 4/4 |
| First two, capped | 12/12 | 4/4 | 16/16 | 12/12 + 8/8 | 4/4 |

Each rule recovers all four two-row footer-extent failures of the original
T003 V2 freeze, preserving all earlier exact positive matrices and native spans.
No positive candidate failures or observed regressions remain on these fixed
DEV cases. Prose proposals persist on every negative, so candidate recall does
not establish safe admission. Four ambiguous V2 pages are explicitly unscored.
Original positives retain 144/144 unique owned values and 180/180 slot words;
controls retain 56/56 values and 132/132 words. V2 exact matrices retain 294/294
slot words; lexical uniqueness ownership is 235 values because repeated values
are penalized by that scorer even when the complete matrices are exact.

Preparation: 0.4713 seconds wall / 0.4628 process CPU, lifetime peak RSS
33,325,056 bytes via `/proc/self/status` VmHWM, sequential process, no sampling.
Remote inference was not performed. Full candidates, scores and failure lists
remain ignored artifacts. This is a post-failure DEV hypothesis test, not an
independent generalization or production/default-admission claim. Dense irregular
row leading, distant true rows and detached subtotal rows still need validation.
