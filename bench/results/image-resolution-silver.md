# DEV image resolution matrix

125 physical DEV silver pages; authored gate labels; 10 positives and 115 negatives. These results do not establish real-world quality or generalization.

**Image conditions:** RGB8, grayscale8 and indexed color4, each at 128, 512 and 1200 px. Every image has a matched blank. Batch sizes depend on provider limits and request size; cross-observation influence remains possible.

Full-source exact recovery is scored through complete record materialization. Transformed-image evidence exactness is not validated. Optional monochrome conversion can erase pale fills; it is excluded from this matrix. Region crops exclude convention notes, while full-page images include them.

Unique completed/charged requests: 1500; effective USD: 0.45376812. Positive provider-reported costs win; other effective costs use retained catalog token rates when available. Reservations remain admission accounting, and missing prices/usage remain unknown.


## `openai/gpt-6-luna-decisions`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | rgb8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-1200 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | rgb8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-128 | 125 | 0 | 0 | 123 | — | 125 / +8 |
| page | gray8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | gray8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-1200 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | gray8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-128 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-1200 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | pal4-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 32826 / 0 | 624947 | 7143 | ~0.003283 |
| page | rgb8-128-blank | 6034 / 0 | 28124 | 1468 | ~0.000603 |
| page | rgb8-512 | 56834 / 0 | 5199663 | 7874 | ~0.005683 |
| page | rgb8-512-blank | 10458 / 0 | 60580 | 1586 | ~0.001046 |
| page | rgb8-1200 | 168644 / 0 | 17086996 | 17522 | ~0.016864 |
| page | rgb8-1200-blank | 31020 / 0 | 171268 | 1609 | ~0.003102 |
| page | gray8-128 | 32826 / 0 | 355175 | 6706 | ~0.003283 |
| page | gray8-128-blank | 6034 / 0 | 25032 | 2036 | ~0.000603 |
| page | gray8-512 | 56834 / 0 | 2351303 | 10375 | ~0.005683 |
| page | gray8-512-blank | 10458 / 0 | 44352 | 1357 | ~0.001046 |
| page | gray8-1200 | 168584 / 0 | 7739031 | 12614 | ~0.016858 |
| page | gray8-1200-blank | 31020 / 0 | 97224 | 1861 | ~0.003102 |
| page | pal4-128 | 32826 / 0 | 278099 | 6492 | ~0.003283 |
| page | pal4-128-blank | 6034 / 0 | 25552 | 1195 | ~0.000603 |
| page | pal4-512 | 56834 / 0 | 1312895 | 7179 | ~0.005683 |
| page | pal4-512-blank | 10458 / 0 | 28384 | 1553 | ~0.001046 |
| page | pal4-1200 | 168584 / 0 | 4286207 | 10375 | ~0.016858 |
| page | pal4-1200-blank | 31020 / 0 | 41844 | 1696 | ~0.003102 |

## `perplexity/pplx-decider-v1.1-27b`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-1200 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-128 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | gray8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | gray8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-1200 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | gray8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-128 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-1200 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 104790 / 125 | 625052 | 8127 | 0.002096 |
| page | rgb8-128-blank | 18600 / 23 | 28144 | 1273 | 0.000372 |
| page | rgb8-512 | 188530 / 125 | 5199768 | 18968 | 0.003771 |
| page | rgb8-512-blank | 33796 / 23 | 60600 | 1495 | 0.000676 |
| page | rgb8-1200 | 608612 / 125 | 17087176 | 29068 | 0.012172 |
| page | rgb8-1200-blank | 153914 / 23 | 171288 | 3298 | 0.003078 |
| page | gray8-128 | 104790 / 125 | 355280 | 13757 | 0.002096 |
| page | gray8-128-blank | 18600 / 23 | 25052 | 1383 | 0.000372 |
| page | gray8-512 | 188530 / 125 | 2351408 | 10484 | 0.003771 |
| page | gray8-512-blank | 33796 / 23 | 44372 | 1602 | 0.000676 |
| page | gray8-1200 | 865568 / 125 | 7739136 | 21829 | 0.017311 |
| page | gray8-1200-blank | 153914 / 23 | 97244 | 3333 | 0.003078 |
| page | pal4-128 | 104790 / 125 | 278204 | 9190 | 0.002096 |
| page | pal4-128-blank | 18600 / 23 | 25572 | 1466 | 0.000372 |
| page | pal4-512 | 188530 / 125 | 1313000 | 16761 | 0.003771 |
| page | pal4-512-blank | 33796 / 23 | 28404 | 2188 | 0.000676 |
| page | pal4-1200 | 865568 / 125 | 4286312 | 35068 | 0.017311 |
| page | pal4-1200-blank | 153914 / 23 | 41864 | 3219 | 0.003078 |

## `cloudflare/clef-flash`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-512 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | rgb8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-1200 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-128 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | gray8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-512 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | gray8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-1200 | 125 | 0 | 0 | 123 | — | 125 / +8 |
| page | gray8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-128 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-512 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | pal4-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-1200 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | pal4-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 39679 / 0 | 626018 | 19321 | 0.003571 |
| page | rgb8-128-blank | 6027 / 0 | 23407 | 3040 | 0.000542 |
| page | rgb8-512 | 54163 / 0 | 5201133 | 27947 | 0.004875 |
| page | rgb8-512-blank | 8205 / 0 | 50087 | 3420 | 0.000738 |
| page | rgb8-1200 | 158153 / 0 | 12268278 | 46219 | 0.014234 |
| page | rgb8-1200-blank | 23529 / 0 | 141239 | 9015 | 0.002118 |
| page | gray8-128 | 39679 / 0 | 356246 | 17564 | 0.003571 |
| page | gray8-128-blank | 6027 / 0 | 20875 | 3243 | 0.000542 |
| page | gray8-512 | 53729 / 0 | 2352374 | 19405 | 0.004836 |
| page | gray8-512-blank | 8205 / 0 | 36787 | 2810 | 0.000738 |
| page | gray8-1200 | 156665 / 0 | 7741128 | 38113 | 0.014100 |
| page | gray8-1200-blank | 23529 / 0 | 80299 | 4428 | 0.002118 |
| page | pal4-128 | 39679 / 0 | 279170 | 17616 | 0.003571 |
| page | pal4-128-blank | 6027 / 0 | 21299 | 3041 | 0.000542 |
| page | pal4-512 | 53729 / 0 | 1313966 | 19081 | 0.004836 |
| page | pal4-512-blank | 8205 / 0 | 23635 | 2826 | 0.000738 |
| page | pal4-1200 | 155673 / 0 | 4287392 | 31991 | 0.014011 |
| page | pal4-1200-blank | 23529 / 0 | 34743 | 5190 | 0.002118 |

## `cloudflare/clef`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 125 | 0 | 0 | 123 | — | 125 / +8 |
| page | rgb8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | rgb8-1200 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | rgb8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-128 | 125 | 0 | 0 | 123 | — | 125 / +8 |
| page | gray8-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | gray8-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | gray8-1200 | 125 | 0 | 0 | 124 | — | 125 / +9 |
| page | gray8-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-128 | 125 | 0 | 0 | 123 | — | 125 / +8 |
| page | pal4-128-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-512 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-512-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |
| page | pal4-1200 | 125 | 0 | 0 | 125 | — | 125 / +10 |
| page | pal4-1200-blank | 125 | 0 | 0 | 115 | — | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| page | rgb8-128 | 39679 / 0 | 625766 | 24513 | 0.009523 |
| page | rgb8-128-blank | 6027 / 0 | 23365 | 3767 | 0.001446 |
| page | rgb8-512 | 54163 / 0 | 5200839 | 36812 | 0.012999 |
| page | rgb8-512-blank | 8205 / 0 | 50045 | 5216 | 0.001969 |
| page | rgb8-1200 | 158153 / 0 | 12267774 | 82449 | 0.037957 |
| page | rgb8-1200-blank | 23529 / 0 | 141197 | 7591 | 0.005647 |
| page | gray8-128 | 39679 / 0 | 355994 | 24850 | 0.009523 |
| page | gray8-128-blank | 6027 / 0 | 20833 | 3431 | 0.001446 |
| page | gray8-512 | 53729 / 0 | 2352122 | 26817 | 0.012895 |
| page | gray8-512-blank | 8205 / 0 | 36745 | 4099 | 0.001969 |
| page | gray8-1200 | 156665 / 0 | 7740768 | 58328 | 0.037600 |
| page | gray8-1200-blank | 23529 / 0 | 80257 | 7173 | 0.005647 |
| page | pal4-128 | 39679 / 0 | 278918 | 23648 | 0.009523 |
| page | pal4-128-blank | 6027 / 0 | 21257 | 3696 | 0.001446 |
| page | pal4-512 | 53729 / 0 | 1313714 | 25734 | 0.012895 |
| page | pal4-512-blank | 8205 / 0 | 23593 | 3823 | 0.001969 |
| page | pal4-1200 | 155673 / 0 | 4287128 | 50270 | 0.037362 |
| page | pal4-1200-blank | 23529 / 0 | 34701 | 6704 | 0.005647 |

Silver scores measure authored ruled-table presence only, not transcription or structure. Unresolved positives count as false negatives; unresolved negatives reduce specificity.

| Model | Arm | TP | FP | FN | TN | Precision | Recall | Specificity | Unresolved |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions | rgb8-128 | 10 | 1 | 0 | 114 | 0.909 | 1.000 | 0.991 | 0 |
| perplexity/pplx-decider-v1.1-27b | rgb8-128 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | rgb8-128 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef | rgb8-128 | 10 | 2 | 0 | 113 | 0.833 | 1.000 | 0.983 | 0 |
| openai/gpt-6-luna-decisions | rgb8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | rgb8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | rgb8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | rgb8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | rgb8-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | rgb8-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | rgb8-512 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| cloudflare/clef | rgb8-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | rgb8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | rgb8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | rgb8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | rgb8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | rgb8-1200 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | rgb8-1200 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef | rgb8-1200 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | rgb8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | rgb8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | rgb8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | gray8-128 | 10 | 2 | 0 | 113 | 0.833 | 1.000 | 0.983 | 0 |
| perplexity/pplx-decider-v1.1-27b | gray8-128 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | gray8-128 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef | gray8-128 | 10 | 2 | 0 | 113 | 0.833 | 1.000 | 0.983 | 0 |
| openai/gpt-6-luna-decisions | gray8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | gray8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | gray8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | gray8-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | gray8-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | gray8-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | gray8-512 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| cloudflare/clef | gray8-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | gray8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | gray8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | gray8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | gray8-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | gray8-1200 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | gray8-1200 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | gray8-1200 | 8 | 0 | 2 | 115 | 1.000 | 0.800 | 1.000 | 0 |
| cloudflare/clef | gray8-1200 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | gray8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | gray8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | gray8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | gray8-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | pal4-128 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | pal4-128 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | pal4-128 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef | pal4-128 | 10 | 2 | 0 | 113 | 0.833 | 1.000 | 0.983 | 0 |
| openai/gpt-6-luna-decisions | pal4-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | pal4-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | pal4-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | pal4-128-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | pal4-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | pal4-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | pal4-512 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| cloudflare/clef | pal4-512 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | pal4-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | pal4-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | pal4-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | pal4-512-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | pal4-1200 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | pal4-1200 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| cloudflare/clef-flash | pal4-1200 | 9 | 0 | 1 | 115 | 1.000 | 0.900 | 1.000 | 0 |
| cloudflare/clef | pal4-1200 | 10 | 0 | 0 | 115 | 1.000 | 1.000 | 1.000 | 0 |
| openai/gpt-6-luna-decisions | pal4-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| perplexity/pplx-decider-v1.1-27b | pal4-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef-flash | pal4-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |
| cloudflare/clef | pal4-1200-blank | 0 | 0 | 10 | 115 | unknown | 0.000 | 1.000 | 0 |

## Local preparation resources

```json
{
  "cpu_seconds": 41.99457467,
  "measurement": "current process, serial CPU; perf_counter/process_time; VmHWM lifetime RSS bytes; no sampling",
  "peak_rss_bytes": 110047232,
  "wall_seconds": 41.401576274001854
}
```
