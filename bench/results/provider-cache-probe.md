# Actual resubmission cache probe

Identical actual provider requests; no automatic retries. Local retained-response replay is a separate zero-call mechanism and is not provider caching. First/repeat order does not establish cold/warm cache state. Only returned cache counters support a cache-use observation. Missing counters leave cache status unverified. Positive provider charges take precedence; token estimates use published component rates, with missing cache prices unknown.

| Model | Condition | Submission | Status | Provider | Read tokens | Write tokens | Reported USD | Effective USD | Token estimate USD | HTTP ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| openai/gpt-6-luna-decisions | rgb8-1200 | first | ok | OpenAI | unknown | unknown | 0 | 0.0004934 | 0.0004934 | 809.3177659902722 |
| openai/gpt-6-luna-decisions | rgb8-1200 | repeat-1 | ok | OpenAI | unknown | unknown | 0 | 0.0004934 | 0.0004934 | 343.1998829910299 |
| openai/gpt-6-luna-decisions | rgb8-1200 | repeat-2 | ok | OpenAI | unknown | unknown | 0 | 0.0004934 | 0.0004934 | 588.035710999975 |
| openai/gpt-6-luna-decisions | rgb8-1200 | first | ok | OpenAI | unknown | unknown | 0 | 0.0010202 | 0.0010202 | 473.59511301328894 |
| openai/gpt-6-luna-decisions | rgb8-1200 | repeat-1 | ok | OpenAI | unknown | unknown | 0 | 0.0010202 | 0.0010202 | 1560.1393660035683 |
| openai/gpt-6-luna-decisions | rgb8-1200 | repeat-2 | ok | OpenAI | unknown | unknown | 0 | 0.0010202 | 0.0010202 | 559.9263140029507 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200 | first | ok | Perplexity | unknown | unknown | 0.00046736 | 0.00046736 | 0.00046736 | 578.3328370016534 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200 | repeat-1 | ok | Perplexity | unknown | unknown | 0.00046736 | 0.00046736 | 0.00046736 | 819.1076579969376 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200 | repeat-2 | ok | Perplexity | unknown | unknown | 0.00046736 | 0.00046736 | 0.00046736 | 601.8545069964603 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200 | first | ok | Perplexity | unknown | unknown | 0.00112472 | 0.00112472 | 0.00112472 | 1141.9868680095533 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200 | repeat-1 | ok | Perplexity | unknown | unknown | 0.00112472 | 0.00112472 | 0.00112472 | 1307.0229290024145 |
| perplexity/pplx-decider-v1.1-27b | rgb8-1200 | repeat-2 | ok | Perplexity | unknown | unknown | 0.00112472 | 0.00112472 | 0.00112472 | 1036.5094649896491 |
| cloudflare/clef-flash | current | first | ok | Cloudflare | unknown | unknown | 0.00035019 | 0.00035019 | 0.00035019 | 492.1997559868032 |
| cloudflare/clef-flash | current | repeat-1 | ok | Cloudflare | unknown | unknown | 0.00035019 | 0.00035019 | 0.00035019 | 504.8981639993144 |
| cloudflare/clef-flash | current | repeat-2 | ok | Cloudflare | unknown | unknown | 0.00035019 | 0.00035019 | 0.00035019 | 512.4640779977199 |
| cloudflare/clef | current | first | ok | Cloudflare | unknown | unknown | 0.00093384 | 0.00093384 | 0.00093384 | 879.2380469967611 |
| cloudflare/clef | current | repeat-1 | ok | Cloudflare | unknown | unknown | 0.00093384 | 0.00093384 | 0.00093384 | 944.9676380027086 |
| cloudflare/clef | current | repeat-2 | ok | Cloudflare | unknown | unknown | 0.00093384 | 0.00093384 | 0.00093384 | 1108.1727359996876 |

Catalog token estimates are comparisons, not newly observed charges. Missing cache counters assume zero for absent components with an explicitly unverified uncached assumption; observed cache counters without matching published cache prices produce an unknown total. Raw usage, ledger entries, fallback assumptions and component prices remain in the adjacent results JSON.

Extra-wave ceiling: $0.50; at most 24 actual calls, 4 models, 2 conditions/model, three submissions/condition. The shared client's cumulative $15 ceiling and reservation ledger also apply.
