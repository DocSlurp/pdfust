# DEV image resolution matrix

30 DEV cases; ten correlated templates across three vocabularies. These results do not establish real-world quality or generalization.

**Image conditions:** RGB8, grayscale8 and indexed color4, each at 128, 512 and 1200 px. Every image has a matched blank. Batch sizes depend on provider limits and request size; cross-observation influence remains possible.

Full-source exact recovery is scored through complete record materialization. Transformed-image evidence exactness is not validated. Optional monochrome conversion can erase pale fills; it is excluded from this matrix. Region crops exclude convention notes, while full-page images include them.

Unique completed/charged requests: 402; effective USD: None. Positive provider-reported costs win; other effective costs use retained catalog token rates when available. Reservations remain admission accounting, and missing prices/usage remain unknown.


## `openai/gpt-6-luna-decisions`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| region | current | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | native | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| region | rgb8-128 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| region | rgb8-128-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | rgb8-512 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| region | rgb8-512-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | rgb8-1200 | 30 | 0 | 0 | 6 | 0.200 | 30 / +3 |
| region | rgb8-1200-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | gray8-128 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| region | gray8-128-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | gray8-512 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| region | gray8-512-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | gray8-1200 | 30 | 0 | 0 | 6 | 0.200 | 30 / +3 |
| region | gray8-1200-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | pal4-128 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| region | pal4-128-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | pal4-512 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| region | pal4-512-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| region | pal4-1200 | 30 | 0 | 0 | 5 | 0.167 | 30 / +2 |
| region | pal4-1200-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | current | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | native | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | rgb8-128 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| page | rgb8-128-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | rgb8-512 | 30 | 0 | 0 | 5 | 0.167 | 30 / +2 |
| page | rgb8-512-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | rgb8-1200 | 30 | 0 | 0 | 9 | 0.300 | 30 / +6 |
| page | rgb8-1200-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | gray8-128 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| page | gray8-128-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | gray8-512 | 30 | 0 | 0 | 5 | 0.167 | 30 / +2 |
| page | gray8-512-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | gray8-1200 | 30 | 0 | 0 | 9 | 0.300 | 30 / +6 |
| page | gray8-1200-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | pal4-128 | 30 | 0 | 0 | 3 | 0.100 | 30 / +0 |
| page | pal4-128-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | pal4-512 | 30 | 0 | 0 | 5 | 0.167 | 30 / +2 |
| page | pal4-512-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |
| page | pal4-1200 | 30 | 0 | 0 | 7 | 0.233 | 30 / +4 |
| page | pal4-1200-blank | 30 | 0 | 0 | 3 | 0.100 | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| region | current | 16862 / 0 | 66021 | 2040 | ~0.001686 |
| region | native | 23024 / 0 | 81573 | 1421 | ~0.002302 |
| region | rgb8-128 | 18092 / 0 | 122819 | 1547 | ~0.001809 |
| region | rgb8-128-blank | 18092 / 0 | 77331 | 1546 | ~0.001809 |
| region | rgb8-512 | 19412 / 0 | 454239 | 1743 | ~0.001941 |
| region | rgb8-512-blank | 19412 / 0 | 84171 | 1602 | ~0.001941 |
| region | rgb8-1200 | 24842 / 0 | 1212083 | 1897 | ~0.002484 |
| region | rgb8-1200-blank | 24842 / 0 | 109071 | 1696 | ~0.002484 |
| region | gray8-128 | 18092 / 0 | 97363 | 1470 | ~0.001809 |
| region | gray8-128-blank | 18092 / 0 | 76611 | 1580 | ~0.001809 |
| region | gray8-512 | 19412 / 0 | 236971 | 1537 | ~0.001941 |
| region | gray8-512-blank | 19412 / 0 | 80931 | 1539 | ~0.001941 |
| region | gray8-1200 | 24842 / 0 | 592335 | 1816 | ~0.002484 |
| region | gray8-1200-blank | 24842 / 0 | 92631 | 1628 | ~0.002484 |
| region | pal4-128 | 18092 / 0 | 91099 | 1847 | ~0.001809 |
| region | pal4-128-blank | 18092 / 0 | 78291 | 2235 | ~0.001809 |
| region | pal4-512 | 19412 / 0 | 170587 | 1745 | ~0.001941 |
| region | pal4-512-blank | 19412 / 0 | 79251 | 1620 | ~0.001941 |
| region | pal4-1200 | 24842 / 0 | 379595 | 1697 | ~0.002484 |
| region | pal4-1200-blank | 24842 / 0 | 82551 | 1732 | ~0.002484 |
| page | current | 16862 / 0 | 66021 | 2040 | ~0.001686 |
| page | native | 23024 / 0 | 81573 | 1421 | ~0.002302 |
| page | rgb8-128 | 18572 / 0 | 125037 | 1471 | ~0.001857 |
| page | rgb8-128-blank | 18572 / 0 | 82281 | 1793 | ~0.001857 |
| page | rgb8-512 | 24332 / 0 | 486283 | 1722 | ~0.002433 |
| page | rgb8-512-blank | 24332 / 0 | 125631 | 1577 | ~0.002433 |
| page | rgb8-1200 | 51182 / 0 | 1398181 | 2476 | ~0.005118 |
| page | rgb8-1200-blank | 51182 / 0 | 272181 | 2375 | ~0.005118 |
| page | gray8-128 | 18572 / 0 | 98553 | 1479 | ~0.001857 |
| page | gray8-128-blank | 18572 / 0 | 78081 | 1585 | ~0.001857 |
| page | gray8-512 | 24332 / 0 | 256651 | 2066 | ~0.002433 |
| page | gray8-512-blank | 24332 / 0 | 103671 | 2044 | ~0.002433 |
| page | gray8-1200 | 51182 / 0 | 658045 | 2384 | ~0.005118 |
| page | gray8-1200-blank | 51182 / 0 | 173901 | 2668 | ~0.005118 |
| page | pal4-128 | 18572 / 0 | 92961 | 1527 | ~0.001857 |
| page | pal4-128-blank | 18572 / 0 | 78801 | 1541 | ~0.001857 |
| page | pal4-512 | 24332 / 0 | 167275 | 1731 | ~0.002433 |
| page | pal4-512-blank | 24332 / 0 | 82551 | 1662 | ~0.002433 |
| page | pal4-1200 | 51182 / 0 | 366953 | 2274 | ~0.005118 |
| page | pal4-1200-blank | 51182 / 0 | 100221 | 2171 | ~0.005118 |

## `perplexity/pplx-decider-v1.1-27b`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| region | current | 30 | 0 | 0 | 6 | 0.200 | 0 / +0 |
| region | native | 30 | 0 | 0 | 30 | 1.000 | 0 / +0 |
| region | rgb8-128 | 30 | 0 | 0 | 14 | 0.467 | 30 / +5 |
| region | rgb8-128-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| region | rgb8-512 | 30 | 0 | 0 | 17 | 0.567 | 30 / +9 |
| region | rgb8-512-blank | 30 | 0 | 0 | 8 | 0.267 | 0 / +0 |
| region | rgb8-1200 | 30 | 0 | 0 | 22 | 0.733 | 30 / +14 |
| region | rgb8-1200-blank | 30 | 0 | 0 | 8 | 0.267 | 0 / +0 |
| region | gray8-128 | 30 | 0 | 0 | 14 | 0.467 | 30 / +5 |
| region | gray8-128-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| region | gray8-512 | 30 | 0 | 0 | 17 | 0.567 | 30 / +9 |
| region | gray8-512-blank | 30 | 0 | 0 | 8 | 0.267 | 0 / +0 |
| region | gray8-1200 | 30 | 0 | 0 | 22 | 0.733 | 30 / +14 |
| region | gray8-1200-blank | 30 | 0 | 0 | 8 | 0.267 | 0 / +0 |
| region | pal4-128 | 30 | 0 | 0 | 16 | 0.533 | 30 / +7 |
| region | pal4-128-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| region | pal4-512 | 30 | 0 | 0 | 16 | 0.533 | 30 / +8 |
| region | pal4-512-blank | 30 | 0 | 0 | 8 | 0.267 | 0 / +0 |
| region | pal4-1200 | 30 | 0 | 0 | 22 | 0.733 | 30 / +14 |
| region | pal4-1200-blank | 30 | 0 | 0 | 8 | 0.267 | 0 / +0 |
| page | current | 30 | 0 | 0 | 6 | 0.200 | 0 / +0 |
| page | native | 30 | 0 | 0 | 30 | 1.000 | 0 / +0 |
| page | rgb8-128 | 30 | 0 | 0 | 17 | 0.567 | 30 / +8 |
| page | rgb8-128-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| page | rgb8-512 | 30 | 0 | 0 | 22 | 0.733 | 30 / +13 |
| page | rgb8-512-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| page | rgb8-1200 | 30 | 0 | 0 | 27 | 0.900 | 30 / +17 |
| page | rgb8-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | gray8-128 | 30 | 0 | 0 | 17 | 0.567 | 30 / +8 |
| page | gray8-128-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| page | gray8-512 | 30 | 0 | 0 | 22 | 0.733 | 30 / +13 |
| page | gray8-512-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| page | gray8-1200 | 30 | 0 | 0 | 27 | 0.900 | 30 / +17 |
| page | gray8-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | pal4-128 | 30 | 0 | 0 | 17 | 0.567 | 30 / +8 |
| page | pal4-128-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| page | pal4-512 | 30 | 0 | 0 | 22 | 0.733 | 30 / +13 |
| page | pal4-512-blank | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| page | pal4-1200 | 30 | 0 | 0 | 28 | 0.933 | 30 / +18 |
| page | pal4-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| region | current | 73424 / 30 | 66046 | 1864 | 0.001468 |
| region | native | 130934 / 30 | 81598 | 2299 | 0.002619 |
| region | rgb8-128 | 94664 / 30 | 122844 | 2159 | 0.001893 |
| region | rgb8-128-blank | 94664 / 30 | 77356 | 2013 | 0.001893 |
| region | rgb8-512 | 94664 / 30 | 454264 | 2553 | 0.001893 |
| region | rgb8-512-blank | 94664 / 30 | 84196 | 2068 | 0.001893 |
| region | rgb8-1200 | 117344 / 30 | 1212108 | 22120 | 0.002347 |
| region | rgb8-1200-blank | 117344 / 30 | 109096 | 2396 | 0.002347 |
| region | gray8-128 | 94664 / 30 | 97388 | 2397 | 0.001893 |
| region | gray8-128-blank | 94664 / 30 | 76636 | 2116 | 0.001893 |
| region | gray8-512 | 94664 / 30 | 236996 | 2141 | 0.001893 |
| region | gray8-512-blank | 94664 / 30 | 80956 | 2072 | 0.001893 |
| region | gray8-1200 | 117344 / 30 | 592360 | 2667 | 0.002347 |
| region | gray8-1200-blank | 117344 / 30 | 92656 | 2398 | 0.002347 |
| region | pal4-128 | 94664 / 30 | 91124 | 2140 | 0.001893 |
| region | pal4-128-blank | 94664 / 30 | 78316 | 2108 | 0.001893 |
| region | pal4-512 | 94664 / 30 | 170612 | 2201 | 0.001893 |
| region | pal4-512-blank | 94664 / 30 | 79276 | 2349 | 0.001893 |
| region | pal4-1200 | 117344 / 30 | 379620 | 2811 | 0.002347 |
| region | pal4-1200-blank | 117344 / 30 | 82576 | 2384 | 0.002347 |
| page | current | 73424 / 30 | 66046 | 1864 | 0.001468 |
| page | native | 130934 / 30 | 81598 | 2299 | 0.002619 |
| page | rgb8-128 | 97364 / 30 | 125062 | 2219 | 0.001947 |
| page | rgb8-128-blank | 97364 / 30 | 82306 | 2166 | 0.001947 |
| page | rgb8-512 | 117704 / 30 | 486308 | 2719 | 0.002354 |
| page | rgb8-512-blank | 117704 / 30 | 125656 | 2412 | 0.002354 |
| page | rgb8-1200 | 281684 / 30 | 1398206 | 5847 | 0.005634 |
| page | rgb8-1200-blank | 281684 / 30 | 272206 | 5156 | 0.005634 |
| page | gray8-128 | 97364 / 30 | 98578 | 2312 | 0.001947 |
| page | gray8-128-blank | 97364 / 30 | 78106 | 2087 | 0.001947 |
| page | gray8-512 | 117704 / 30 | 256676 | 2593 | 0.002354 |
| page | gray8-512-blank | 117704 / 30 | 103696 | 2399 | 0.002354 |
| page | gray8-1200 | 281684 / 30 | 658070 | 5216 | 0.005634 |
| page | gray8-1200-blank | 281684 / 30 | 173926 | 4904 | 0.005634 |
| page | pal4-128 | 97364 / 30 | 92986 | 2118 | 0.001947 |
| page | pal4-128-blank | 97364 / 30 | 78826 | 2241 | 0.001947 |
| page | pal4-512 | 117704 / 30 | 167300 | 2529 | 0.002354 |
| page | pal4-512-blank | 117704 / 30 | 82576 | 2443 | 0.002354 |
| page | pal4-1200 | 281684 / 30 | 366978 | 5175 | 0.005634 |
| page | pal4-1200-blank | 281684 / 30 | 100246 | 24338 | 0.005634 |

## `cloudflare/clef-flash`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| region | current | 30 | 0 | 0 | 13 | 0.433 | 0 / +0 |
| region | native | 30 | 0 | 0 | 13 | 0.433 | 0 / +0 |
| region | rgb8-128 | 0 | 1 | 24 | 0 | — | 0 / +0 |
| region | rgb8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | current | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | native | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| region | current | 19630 / 0 | 65991 | 2683 | 0.001767 |
| region | native | 29215 / 0 | 81543 | 2694 | 0.002629 |
| region | rgb8-128 | 0 / 0 | 24222 | 148 | unknown |
| region | rgb8-128-blank | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-512 | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-512-blank | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-1200 | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| region | gray8-128 | 0 / 0 | 0 | 0 | unknown |
| region | gray8-128-blank | 0 / 0 | 0 | 0 | unknown |
| region | gray8-512 | 0 / 0 | 0 | 0 | unknown |
| region | gray8-512-blank | 0 / 0 | 0 | 0 | unknown |
| region | gray8-1200 | 0 / 0 | 0 | 0 | unknown |
| region | gray8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| region | pal4-128 | 0 / 0 | 0 | 0 | unknown |
| region | pal4-128-blank | 0 / 0 | 0 | 0 | unknown |
| region | pal4-512 | 0 / 0 | 0 | 0 | unknown |
| region | pal4-512-blank | 0 / 0 | 0 | 0 | unknown |
| region | pal4-1200 | 0 / 0 | 0 | 0 | unknown |
| region | pal4-1200-blank | 0 / 0 | 0 | 0 | unknown |
| page | current | 0 / 0 | 0 | 0 | unknown |
| page | native | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-128 | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-128-blank | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-512 | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-512-blank | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-1200 | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| page | gray8-128 | 0 / 0 | 0 | 0 | unknown |
| page | gray8-128-blank | 0 / 0 | 0 | 0 | unknown |
| page | gray8-512 | 0 / 0 | 0 | 0 | unknown |
| page | gray8-512-blank | 0 / 0 | 0 | 0 | unknown |
| page | gray8-1200 | 0 / 0 | 0 | 0 | unknown |
| page | gray8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| page | pal4-128 | 0 / 0 | 0 | 0 | unknown |
| page | pal4-128-blank | 0 / 0 | 0 | 0 | unknown |
| page | pal4-512 | 0 / 0 | 0 | 0 | unknown |
| page | pal4-512-blank | 0 / 0 | 0 | 0 | unknown |
| page | pal4-1200 | 0 / 0 | 0 | 0 | unknown |
| page | pal4-1200-blank | 0 / 0 | 0 | 0 | unknown |

## `cloudflare/clef`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| region | current | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| region | native | 30 | 0 | 0 | 24 | 0.800 | 0 / +0 |
| region | rgb8-128 | 0 | 1 | 24 | 0 | — | 0 / +0 |
| region | rgb8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | rgb8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | gray8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| region | pal4-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | current | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | native | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | rgb8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | gray8-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-128 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-128-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-512 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-512-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-1200 | 0 | 0 | 30 | 0 | — | 0 / +0 |
| page | pal4-1200-blank | 0 | 0 | 30 | 0 | — | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| region | current | 19630 / 0 | 65961 | 5538 | 0.004711 |
| region | native | 29215 / 0 | 81513 | 6084 | 0.007012 |
| region | rgb8-128 | 0 / 0 | 24216 | 149 | unknown |
| region | rgb8-128-blank | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-512 | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-512-blank | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-1200 | 0 / 0 | 0 | 0 | unknown |
| region | rgb8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| region | gray8-128 | 0 / 0 | 0 | 0 | unknown |
| region | gray8-128-blank | 0 / 0 | 0 | 0 | unknown |
| region | gray8-512 | 0 / 0 | 0 | 0 | unknown |
| region | gray8-512-blank | 0 / 0 | 0 | 0 | unknown |
| region | gray8-1200 | 0 / 0 | 0 | 0 | unknown |
| region | gray8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| region | pal4-128 | 0 / 0 | 0 | 0 | unknown |
| region | pal4-128-blank | 0 / 0 | 0 | 0 | unknown |
| region | pal4-512 | 0 / 0 | 0 | 0 | unknown |
| region | pal4-512-blank | 0 / 0 | 0 | 0 | unknown |
| region | pal4-1200 | 0 / 0 | 0 | 0 | unknown |
| region | pal4-1200-blank | 0 / 0 | 0 | 0 | unknown |
| page | current | 0 / 0 | 0 | 0 | unknown |
| page | native | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-128 | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-128-blank | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-512 | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-512-blank | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-1200 | 0 / 0 | 0 | 0 | unknown |
| page | rgb8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| page | gray8-128 | 0 / 0 | 0 | 0 | unknown |
| page | gray8-128-blank | 0 / 0 | 0 | 0 | unknown |
| page | gray8-512 | 0 / 0 | 0 | 0 | unknown |
| page | gray8-512-blank | 0 / 0 | 0 | 0 | unknown |
| page | gray8-1200 | 0 / 0 | 0 | 0 | unknown |
| page | gray8-1200-blank | 0 / 0 | 0 | 0 | unknown |
| page | pal4-128 | 0 / 0 | 0 | 0 | unknown |
| page | pal4-128-blank | 0 / 0 | 0 | 0 | unknown |
| page | pal4-512 | 0 / 0 | 0 | 0 | unknown |
| page | pal4-512-blank | 0 / 0 | 0 | 0 | unknown |
| page | pal4-1200 | 0 / 0 | 0 | 0 | unknown |
| page | pal4-1200-blank | 0 / 0 | 0 | 0 | unknown |

## Local preparation resources

```json
{
  "cpu_seconds": 38.876260664,
  "measurement": "current process, serial CPU; perf_counter/process_time; VmHWM lifetime RSS bytes; no sampling",
  "peak_rss_bytes": 133251072,
  "wall_seconds": 38.52655575699464
}
```
