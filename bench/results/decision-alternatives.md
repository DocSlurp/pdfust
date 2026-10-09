# Eight additional decision models — 2026-10-08

**Quality is the primary comparison.** Confidence can help routing but is not a
qualification gate. These measurements extend the initial pilot with the eight
exact IDs requested by the user, without changing source cases, prompts or labels.

All eight appear in the [filtered OpenRouter decisions catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions).
The default catalog omits decision models. Seven returned native probability
responses and completed 96 singleton observations; `respan/span-01` returned HTTP
404 on its compatibility probe despite being advertised as active. No unlisted
alias or chat model was substituted. [Catalog and official sources](../DECISION_CATALOG.md).

## Primary results

The 36 known test labels below are part of the existing, repeatedly inspected
synthetic development corpus. Twelve indeterminate cases are separate and are
not counted as correct or incorrect. These scores are exploratory development
evidence, not clean held-out confirmation or business-document extraction
accuracy. Always-no scores 24/36 because of the class imbalance.

| Model | Known answers correct /36 | Separate region gates /8 | Median HTTP ms | Reported USD for 96 observations |
|---|---:|---:|---:|---:|
| `openai/gpt-6-luna-decisions` | **31** | **8** | 285 | 0 reported |
| `perplexity/pplx-decider-v1.1-27b` | 30 | 6 | 294 | 0.004325 |
| `upstage/solar-decide-flash` | 25 | 5 | 928 | 0.012004 |
| `cloudflare/clef-flash` | 24 | Not measured | 371 | 0.010497 |
| `inception/mercury-decide` | 21 | 7 | 468 | 0.002075 |
| `liquid/d1` | 20 | 6 | 341 | 0.009505 |
| `togethercomputer/tev1-4b-experimental` | 17 | 7 | 283 | 0.007608 |
| `respan/span-01` | Not measured: HTTP 404 | Not measured | — | Unknown; 0.30 reserved |
| Earlier Jev, same singleton/resolved format | 24 | Different prior format | 247 | 0.006550 |

Each observation requests two native Nouls: relationship truth and whether the
evidence suffices to decide either way. The table reports full HTTP latency,
not end-to-end document time. Costs include the initial smoke request reused by
the scored cohort; replay adds no new charge. Luna's responses report cost zero,
while the catalog advertises $0.10/M input tokens. Zero is an observed billing
field, not a promise of free future use. Its 114,522 reported input tokens would
correspond to about $0.01145 at that advertised price, before cache adjustments.

Clef's authored runs all used Cloudflare. That provider documents a roughly
2K-token text-state truncation limit; authored states were kept to at most 2,090
UTF-8 bytes. The larger region controls can exceed the safe compact range. An
explicit PrimeIntellect route was attempted for them, but returned HTTP 404 on
the first request. That cohort has one failure and seven unattempted cases, not
zero correct out of eight. Span and PrimeIntellect were not retried silently.

The separate region controls cover four table and four prose regions from six
existing sources, including dense NICS and Senate tables. **They test region type**,
not complete matrices, header ownership or dense-report reconstruction. Sources
and exact clips are in the retained controls manifest.

## Ability differs by task

| Model | Assignment /9 | Header /9 | Table /9 | Wrap /9 |
|---|---:|---:|---:|---:|
| Luna | 6 | 8 | 8 | 9 |
| Perplexity | 9 | 3 | 9 | 9 |
| Solar Flash | 5 | 5 | 8 | 7 |
| Clef Flash | 8 | 4 | 9 | 3 |
| Mercury | 7 | 2 | 9 | 3 |
| d1 | 9 | 5 | 3 | 3 |
| Tev | 8 | 3 | 3 | 3 |
| Jev reference | 9 | 9 | 3 | 3 |

Luna is the best observed general candidate in this small set. Perplexity is
strong outside headers. Several header labels encode debatable author intent;
these scores must not be treated as independent human-adjudicated semantics.
Inspecting those limitations is more useful than demanding calibrated model
confidence before proceeding with further quality tests.

## A confidence-free router did not improve quality

An offline task router selected models using only known calibration accuracy,
then lower median calibration HTTP latency, then lexical model ID. Indeterminate
calibration examples contributed latency only. Missing or failed calibration
predictions could not win. No test labels or predictions selected the routes.

| Task | Selected model | Calibration correct /9 | Test correct /9 |
|---|---|---:|---:|
| Assignment | Jev | 9 | 9 |
| Header | Tev | 9 | 3 |
| Table | Luna | 9 | 8 |
| Wrap | Luna | 9 | 9 |
| Combined | | 36/36 | **29/36** |

**Negative result:** the router loses to using Luna alone (31/36). Tev's header selection fails to generalize.
This is an exploratory reuse of an already exposed development corpus; it does
not establish a valid new holdout result. The router code and scorer regressions
make the negative result reproducible without extra model calls. Do not repair
the router by selecting winners from these test labels.

Confidence remains a secondary diagnostic. At the earlier fixed .9/.9 thresholds,
Luna accepts one wrong known answer and four indeterminate cases; Perplexity
accepts two wrong known answers and four indeterminate cases. Indeterminate
acceptances are not proven semantic errors. The old calibration-selected
all-abstain policy does not disqualify these models from useful deployment
experiments. Region controls have no calibration split at all.

## Reproduction, limits and accounting

See [DECISION_CATALOG.md](../DECISION_CATALOG.md) for exact commands. The runner
now routes all admitted decision IDs to `/api/alpha/decisions`, retains original
chat defaults, accepts optional provider pins without losing chat price caps,
and limits native requests to 16 questions and 32,000 bytes. This bounds repeated
state billing as well as payload size. Credentials and bulk outputs stay ignored.

- **Requests:** the phase starts at ledger index 628 and ends at 1349: **722 new requests**, including 720 successful scored observations and two failed availability probes.
- **Additional cost:** provider-reported cost is **$0.053802074**; two unknown charges retain **$0.60** of reservations.
- **Cumulative spend:** reported spend is **$2.046954530**; conservative accounting including those reservations is **$2.646954530** against the $15 cap.

No local GPU or new GPU host was used. No GitHub publication occurred.

The full CPU suite passed 1,458 tests, with 16 skips and two expected failures;
Ruff and source/test/benchmark type checks passed. The later offline router has
its own eight passing tests. All rows, including failures and negative findings,
are tracked through [EXPERIMENTS_LOG.md](../../EXPERIMENTS_LOG.md).
