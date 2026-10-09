# Generic identity wording on natural PDF DEV evidence

Flash catches more insufficient description-only evidence with the generic identity wording: ambiguous abstention rises from 5/44 to 19/44, while known-scope correct decisions fall from 35/52 to 32/52 and known abstentions rise from 4 to 12. Clef remains decisive on all 44 insufficient conditions and loses two known correct decisions. This wording is not a general ambiguity solution.

The fixed identity transform was authored before this transfer and applies uniformly to all 96 packets. Verification checks all original L011 source/stage requests and images, exact retained transform code hash, the source-to-opaque-ID mapping, projected body bytes/hashes and identical PNG bytes before local references. Only q0 instructions and criterion descriptions change; literal state, options, transport model and images remain exact. Both original and projected models completed 96/96 with no schema or worker errors.

| Model | Wording | Known-scope correct/52 | Wrong known | Known abstentions | Ambiguous abstentions/44 | Full-source matches/96 |
|---|---|---:|---:|---:|---:|---:|
| flash | original | 35 | 13 | 4 | 5 | 62 |
| clef | original | 44 | 8 | 0 | 0 | 76 |
| flash | identity | 32 | 8 | 12 | 19 | 52 |
| clef | identity | 42 | 10 | 0 | 0 | 76 |

| Model | Wording | Arm | Scope matches/24 | Ambiguous abstentions | Total abstentions | Inference s | CPU s | RSS MiB |
|---|---|---|---:|---:|---:|---:|---:|---:|
| flash | original | record-512 | 14 | 0 | 3 | 2.063 | 3.321 | 18796.2 |
| flash | original | record-1200 | 17 | 0 | 1 | 1.580 | 2.936 | 18796.2 |
| flash | original | description-512 | 5 | 3 | 3 | 1.465 | 2.685 | 18796.2 |
| flash | original | description-1200 | 4 | 2 | 2 | 2.087 | 4.018 | 18796.2 |
| clef | original | record-512 | 20 | 0 | 0 | 5.016 | 6.360 | 53031.6 |
| clef | original | record-1200 | 20 | 0 | 0 | 4.652 | 6.079 | 53031.6 |
| clef | original | description-512 | 2 | 0 | 0 | 4.399 | 5.697 | 53031.6 |
| clef | original | description-1200 | 2 | 0 | 0 | 6.042 | 8.019 | 53031.6 |
| flash | identity | record-512 | 13 | 0 | 6 | 3.691 | 4.700 | 18794.2 |
| flash | identity | record-1200 | 16 | 0 | 5 | 3.031 | 4.108 | 18794.2 |
| flash | identity | description-512 | 13 | 12 | 13 | 3.242 | 4.231 | 18794.2 |
| flash | identity | description-1200 | 9 | 7 | 7 | 4.142 | 5.699 | 18794.2 |
| clef | identity | record-512 | 18 | 0 | 0 | 5.960 | 6.913 | 53028.6 |
| clef | identity | record-1200 | 20 | 0 | 0 | 5.268 | 6.303 | 53028.6 |
| clef | identity | description-512 | 2 | 0 | 0 | 5.077 | 6.024 | 53028.6 |
| clef | identity | description-1200 | 2 | 0 | 0 | 6.393 | 7.801 | 53028.6 |

The larger description crop does not uniformly improve abstention: Flash identity catches 12/22 at 512 and 7/22 at 1200. Its full-record agreement falls by one per resolution (14→13 and 17→16), with known-record abstentions rising from 4/48 to 11/48. Clef full-record agreement changes from 20/24 at both sizes to 18/24 and 20/24, with no abstentions. These are matched fixed cohorts; no case-level selector or prompt adjustment was fit to the answers.

Reference agreement remains provisional: 24 overlapping regions from one Senate page; 48 full-record conditions and 4 answerable description conditions, plus 44 insufficient description conditions. Full-source matches on limited description evidence are reported separately and do not establish sufficient information.

Serial adapter inference includes preprocessing and native prediction. Process/thread CPU and lifetime Linux ru_maxrss include the worker loading scope; repeated per-arm RSS high-water values do not sum to concurrent RAM. Detailed CUDA allocator peaks remain in JSON. Root supplied Flash/Clef USD 1.275/hour: warm serial estimates multiply measured inference seconds by this quote and exclude downloads, initialization, idle and cleanup; they are not billed totals.

| Model | Wording | Summed inference s | Warm estimate USD | Inputs/min | Inputs/estimated USD |
|---|---|---:|---:|---:|---:|
| flash | original | 7.195 | 0.002548 | 800.5 | 37672 |
| clef | original | 20.109 | 0.007122 | 286.4 | 13480 |
| flash | identity | 14.106 | 0.004996 | 408.3 | 19216 |
| clef | identity | 22.700 | 0.008039 | 253.7 | 11941 |

CPU-only verify/score: wall 0.579 s, CPU 0.575 s, peak RSS 114.5 MiB. Retained evaluation: `.scratch/council/lowlevel-eval/natural-identity-evaluation.json`; source-only projection provenance: `.scratch/remote-gpu-20261009/r001/natural-identity-provenance.json`. No inference was run during analysis.
