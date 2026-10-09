# DEV image resolution matrix

30 DEV cases; ten correlated templates across three vocabularies. These results do not establish real-world quality or generalization.

**Image conditions:** RGB8, grayscale8 and indexed color4, each at 128, 512 and 1200 px. Every image has a matched blank. Batch sizes depend on provider limits and request size; cross-observation influence remains possible.

Full-source exact recovery is scored through complete record materialization. Transformed-image evidence exactness is not validated. Optional monochrome conversion can erase pale fills; it is excluded from this matrix. Region crops exclude convention notes, while full-page images include them.

Unique completed/charged requests: 770; effective USD: 0.36641055. Positive provider-reported costs win; other effective costs use retained catalog token rates when available. Reservations remain admission accounting, and missing prices/usage remain unknown.


## `cloudflare/clef-flash`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| region | current | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| region | native | 30 | 0 | 0 | 17 | 0.567 | 0 / +0 |
| region | rgb8-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +0 |
| region | rgb8-128-blank | 30 | 0 | 0 | 12 | 0.400 | 0 / +0 |
| region | rgb8-512 | 30 | 0 | 0 | 15 | 0.500 | 30 / +3 |
| region | rgb8-512-blank | 30 | 0 | 0 | 12 | 0.400 | 0 / +0 |
| region | rgb8-1200 | 30 | 0 | 0 | 16 | 0.533 | 30 / +3 |
| region | rgb8-1200-blank | 30 | 0 | 0 | 13 | 0.433 | 0 / +0 |
| region | gray8-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +0 |
| region | gray8-128-blank | 30 | 0 | 0 | 12 | 0.400 | 0 / +0 |
| region | gray8-512 | 30 | 0 | 0 | 15 | 0.500 | 30 / +3 |
| region | gray8-512-blank | 30 | 0 | 0 | 12 | 0.400 | 0 / +0 |
| region | gray8-1200 | 30 | 0 | 0 | 16 | 0.533 | 30 / +3 |
| region | gray8-1200-blank | 30 | 0 | 0 | 13 | 0.433 | 0 / +0 |
| region | pal4-128 | 30 | 0 | 0 | 11 | 0.367 | 30 / -1 |
| region | pal4-128-blank | 30 | 0 | 0 | 12 | 0.400 | 0 / +0 |
| region | pal4-512 | 30 | 0 | 0 | 15 | 0.500 | 30 / +5 |
| region | pal4-512-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| region | pal4-1200 | 30 | 0 | 0 | 16 | 0.533 | 30 / +3 |
| region | pal4-1200-blank | 30 | 0 | 0 | 13 | 0.433 | 0 / +0 |
| page | current | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | native | 30 | 0 | 0 | 17 | 0.567 | 0 / +0 |
| page | rgb8-128 | 30 | 0 | 0 | 11 | 0.367 | 30 / +1 |
| page | rgb8-128-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | rgb8-512 | 30 | 0 | 0 | 14 | 0.467 | 30 / +2 |
| page | rgb8-512-blank | 30 | 0 | 0 | 12 | 0.400 | 0 / +0 |
| page | rgb8-1200 | 30 | 0 | 0 | 19 | 0.633 | 30 / +9 |
| page | rgb8-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | gray8-128 | 30 | 0 | 0 | 11 | 0.367 | 30 / +1 |
| page | gray8-128-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | gray8-512 | 30 | 0 | 0 | 14 | 0.467 | 30 / +1 |
| page | gray8-512-blank | 30 | 0 | 0 | 13 | 0.433 | 0 / +0 |
| page | gray8-1200 | 30 | 0 | 0 | 19 | 0.633 | 30 / +9 |
| page | gray8-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | pal4-128 | 30 | 0 | 0 | 11 | 0.367 | 30 / +1 |
| page | pal4-128-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | pal4-512 | 30 | 0 | 0 | 15 | 0.500 | 30 / +2 |
| page | pal4-512-blank | 30 | 0 | 0 | 13 | 0.433 | 0 / +0 |
| page | pal4-1200 | 30 | 0 | 0 | 19 | 0.633 | 30 / +9 |
| page | pal4-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| region | current | 19940 / 0 | 66276 | 4164 | 0.001795 |
| region | native | 29835 / 0 | 82113 | 5614 | 0.002685 |
| region | rgb8-128 | 23390 / 0 | 123074 | 4226 | 0.002105 |
| region | rgb8-128-blank | 23390 / 0 | 77586 | 4990 | 0.002105 |
| region | rgb8-512 | 23390 / 0 | 454494 | 5236 | 0.002105 |
| region | rgb8-512-blank | 23390 / 0 | 84426 | 4344 | 0.002105 |
| region | rgb8-1200 | 27170 / 0 | 1212338 | 5493 | 0.002445 |
| region | rgb8-1200-blank | 27170 / 0 | 109326 | 5417 | 0.002445 |
| region | gray8-128 | 23390 / 0 | 97618 | 4566 | 0.002105 |
| region | gray8-128-blank | 23390 / 0 | 76866 | 4453 | 0.002105 |
| region | gray8-512 | 23390 / 0 | 237226 | 4712 | 0.002105 |
| region | gray8-512-blank | 23390 / 0 | 81186 | 4543 | 0.002105 |
| region | gray8-1200 | 27170 / 0 | 592590 | 5303 | 0.002445 |
| region | gray8-1200-blank | 27170 / 0 | 92886 | 4902 | 0.002445 |
| region | pal4-128 | 23390 / 0 | 91354 | 4383 | 0.002105 |
| region | pal4-128-blank | 23390 / 0 | 78546 | 4629 | 0.002105 |
| region | pal4-512 | 23390 / 0 | 170842 | 4337 | 0.002105 |
| region | pal4-512-blank | 23390 / 0 | 79506 | 5201 | 0.002105 |
| region | pal4-1200 | 27170 / 0 | 379850 | 5304 | 0.002445 |
| region | pal4-1200-blank | 27170 / 0 | 82806 | 5098 | 0.002445 |
| page | current | 19940 / 0 | 66276 | 4164 | 0.001795 |
| page | native | 29835 / 0 | 82113 | 5614 | 0.002685 |
| page | rgb8-128 | 23840 / 0 | 125292 | 4467 | 0.002146 |
| page | rgb8-128-blank | 23840 / 0 | 82536 | 4883 | 0.002146 |
| page | rgb8-512 | 27230 / 0 | 486538 | 4839 | 0.002451 |
| page | rgb8-512-blank | 27230 / 0 | 125886 | 5768 | 0.002451 |
| page | rgb8-1200 | 51740 / 0 | 1398436 | 8102 | 0.004657 |
| page | rgb8-1200-blank | 51740 / 0 | 272436 | 7448 | 0.004657 |
| page | gray8-128 | 23840 / 0 | 98808 | 4538 | 0.002146 |
| page | gray8-128-blank | 23840 / 0 | 78336 | 4413 | 0.002146 |
| page | gray8-512 | 27230 / 0 | 256906 | 5000 | 0.002451 |
| page | gray8-512-blank | 27230 / 0 | 103926 | 4711 | 0.002451 |
| page | gray8-1200 | 51740 / 0 | 658300 | 7648 | 0.004657 |
| page | gray8-1200-blank | 51740 / 0 | 174156 | 6968 | 0.004657 |
| page | pal4-128 | 23840 / 0 | 93216 | 4538 | 0.002146 |
| page | pal4-128-blank | 23840 / 0 | 79056 | 4545 | 0.002146 |
| page | pal4-512 | 27230 / 0 | 167530 | 4794 | 0.002451 |
| page | pal4-512-blank | 27230 / 0 | 82806 | 4832 | 0.002451 |
| page | pal4-1200 | 51740 / 0 | 367208 | 7235 | 0.004657 |
| page | pal4-1200-blank | 51740 / 0 | 100476 | 6980 | 0.004657 |

## `cloudflare/clef`

**Quality and completion**

| Scope | Arm | Scored | Errors | Unattempted | Exact | Record F1 | Paired blank n / delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| region | current | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| region | native | 30 | 0 | 0 | 25 | 0.833 | 0 / +0 |
| region | rgb8-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +1 |
| region | rgb8-128-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | rgb8-512 | 30 | 0 | 0 | 12 | 0.400 | 30 / +1 |
| region | rgb8-512-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | rgb8-1200 | 30 | 0 | 0 | 14 | 0.467 | 30 / +3 |
| region | rgb8-1200-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | gray8-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +1 |
| region | gray8-128-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | gray8-512 | 30 | 0 | 0 | 12 | 0.400 | 30 / +1 |
| region | gray8-512-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | gray8-1200 | 30 | 0 | 0 | 14 | 0.467 | 30 / +3 |
| region | gray8-1200-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | pal4-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +1 |
| region | pal4-128-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | pal4-512 | 30 | 0 | 0 | 12 | 0.400 | 30 / +1 |
| region | pal4-512-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| region | pal4-1200 | 30 | 0 | 0 | 14 | 0.467 | 30 / +3 |
| region | pal4-1200-blank | 30 | 0 | 0 | 11 | 0.367 | 0 / +0 |
| page | current | 30 | 0 | 0 | 9 | 0.300 | 0 / +0 |
| page | native | 30 | 0 | 0 | 25 | 0.833 | 0 / +0 |
| page | rgb8-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +2 |
| page | rgb8-128-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | rgb8-512 | 30 | 0 | 0 | 19 | 0.633 | 30 / +9 |
| page | rgb8-512-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | rgb8-1200 | 30 | 0 | 0 | 18 | 0.600 | 30 / +8 |
| page | rgb8-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | gray8-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +2 |
| page | gray8-128-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | gray8-512 | 30 | 0 | 0 | 19 | 0.633 | 30 / +9 |
| page | gray8-512-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | gray8-1200 | 30 | 0 | 0 | 18 | 0.600 | 30 / +8 |
| page | gray8-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | pal4-128 | 30 | 0 | 0 | 12 | 0.400 | 30 / +2 |
| page | pal4-128-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | pal4-512 | 30 | 0 | 0 | 19 | 0.633 | 30 / +9 |
| page | pal4-512-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |
| page | pal4-1200 | 30 | 0 | 0 | 18 | 0.600 | 30 / +8 |
| page | pal4-1200-blank | 30 | 0 | 0 | 10 | 0.333 | 0 / +0 |

**Usage and cost**

| Scope | Arm | Input / output tokens | Request bytes | API ms | Effective USD |
| --- | --- | ---: | ---: | ---: | ---: |
| region | current | 19940 / 0 | 66216 | 6028 | 0.004786 |
| region | native | 29835 / 0 | 82023 | 9577 | 0.007160 |
| region | rgb8-128 | 23390 / 0 | 123014 | 7250 | 0.005614 |
| region | rgb8-128-blank | 23390 / 0 | 77526 | 7509 | 0.005614 |
| region | rgb8-512 | 23390 / 0 | 454434 | 7349 | 0.005614 |
| region | rgb8-512-blank | 23390 / 0 | 84366 | 7691 | 0.005614 |
| region | rgb8-1200 | 27170 / 0 | 1212278 | 9475 | 0.006521 |
| region | rgb8-1200-blank | 27170 / 0 | 109266 | 8402 | 0.006521 |
| region | gray8-128 | 23390 / 0 | 97558 | 7812 | 0.005614 |
| region | gray8-128-blank | 23390 / 0 | 76806 | 7446 | 0.005614 |
| region | gray8-512 | 23390 / 0 | 237166 | 7457 | 0.005614 |
| region | gray8-512-blank | 23390 / 0 | 81126 | 7872 | 0.005614 |
| region | gray8-1200 | 27170 / 0 | 592530 | 9027 | 0.006521 |
| region | gray8-1200-blank | 27170 / 0 | 92826 | 8640 | 0.006521 |
| region | pal4-128 | 23390 / 0 | 91294 | 7526 | 0.005614 |
| region | pal4-128-blank | 23390 / 0 | 78486 | 9544 | 0.005614 |
| region | pal4-512 | 23390 / 0 | 170782 | 7592 | 0.005614 |
| region | pal4-512-blank | 23390 / 0 | 79446 | 6781 | 0.005614 |
| region | pal4-1200 | 27170 / 0 | 379790 | 8234 | 0.006521 |
| region | pal4-1200-blank | 27170 / 0 | 82746 | 7894 | 0.006521 |
| page | current | 19940 / 0 | 66216 | 6028 | 0.004786 |
| page | native | 29835 / 0 | 82023 | 9577 | 0.007160 |
| page | rgb8-128 | 23840 / 0 | 125232 | 7829 | 0.005722 |
| page | rgb8-128-blank | 23840 / 0 | 82476 | 7928 | 0.005722 |
| page | rgb8-512 | 27230 / 0 | 486478 | 8503 | 0.006535 |
| page | rgb8-512-blank | 27230 / 0 | 125826 | 8876 | 0.006535 |
| page | rgb8-1200 | 51740 / 0 | 1398376 | 15848 | 0.012418 |
| page | rgb8-1200-blank | 51740 / 0 | 272376 | 13741 | 0.012418 |
| page | gray8-128 | 23840 / 0 | 98748 | 8584 | 0.005722 |
| page | gray8-128-blank | 23840 / 0 | 78276 | 7699 | 0.005722 |
| page | gray8-512 | 27230 / 0 | 256846 | 8016 | 0.006535 |
| page | gray8-512-blank | 27230 / 0 | 103866 | 9734 | 0.006535 |
| page | gray8-1200 | 51740 / 0 | 658240 | 14275 | 0.012418 |
| page | gray8-1200-blank | 51740 / 0 | 174096 | 13095 | 0.012418 |
| page | pal4-128 | 23840 / 0 | 93156 | 8013 | 0.005722 |
| page | pal4-128-blank | 23840 / 0 | 78996 | 8139 | 0.005722 |
| page | pal4-512 | 27230 / 0 | 167470 | 7709 | 0.006535 |
| page | pal4-512-blank | 27230 / 0 | 82746 | 8354 | 0.006535 |
| page | pal4-1200 | 51740 / 0 | 367148 | 13094 | 0.012418 |
| page | pal4-1200-blank | 51740 / 0 | 100416 | 12947 | 0.012418 |

## Local preparation resources

```json
{
  "cpu_seconds": 10.942484948999999,
  "measurement": "current process, serial CPU; perf_counter/process_time; VmHWM lifetime RSS bytes; no sampling",
  "peak_rss_bytes": 112418816,
  "wall_seconds": 10.484975365994615
}
```
