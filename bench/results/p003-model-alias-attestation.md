# Exact native returned-model identifier attestation

All 14 requested decision model IDs have an explicit `canonical_slug` in the retained primary [OpenRouter decisions catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions), fetched 2026-10-10 at 18:28:05.795199 UTC. The raw catalog SHA256 is `b07bd50be8933b083a6f2c9da1bf59624c6c59f4134dc0b595b51a278a82dca5`. No prefix, wildcard, arbitrary date suffix or observed-answer inference is needed.

| Requested ID | Exact attested canonical returned ID |
|---|---|
| typesafe/jev-1.13 | typesafe/jev-1.13-20260917 |
| perplexity/pplx-decider-v1.1-27b | perplexity/pplx-decider-v1.1-27b-20261006 |
| upstage/solar-decide-flash | upstage/solar-decide-flash-20261008 |
| openai/gpt-6-luna-decisions | openai/gpt-6-luna-decisions-20261006 |
| liquid/d1 | liquid/d1-20260930 |
| cloudflare/clef-flash | cloudflare/clef-flash |
| cloudflare/clef | cloudflare/clef |
| togethercomputer/tev1-4b-experimental | togethercomputer/tev1-4b-experimental-20260923 |
| inception/mercury-decide | inception/mercury-decide-20260930 |
| respan/span-01 | respan/span-01-20260925 |
| cloudflare/clef-omni | cloudflare/clef-omni-20261009 |
| microsoft/microsoft-decision-1 | microsoft/microsoft-decision-1-20261009 |
| nace-ai/drex-v1.5 | nace-ai/drex-v1.5-20261009 |
| upstage/solar-decide | upstage/solar-decide-20260928 |

The ignored main artifact `pipeline-p003/catalog-alias-attestation-v1/aliases.json` freezes schema 1, the 14 explicit alias lists, source URL/time, raw catalog and catalog-manifest paths/hashes, and extraction scope. Its SHA256 is `2611b9db728544889bbcce3779d74452c0fe6e46f1a5c66aa3b3487ed827e068`. The same directory contains exact raw catalog and manifest copies; original retained catalog paths remain unchanged.

This evidence supports separately labeled offline normalization of only a raw response's attested `model` identifier to its exact requested ID, after wire, requested-model ledger/tag and source authentication. It does not authorize changing choices, probabilities, rankings, original results, request identities or charges. Unlisted identifiers remain invalid. The original strict failures are retained; no hosted retry or active helper modification was performed for this research.
