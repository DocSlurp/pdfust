# P003 public model catalog and transport research

Research date: **2026-10-10 UTC**, repository baseline `24cf9fd`. These are
unauthenticated public GET observations. No credentials, inference, rentals,
GPU work, source references, or protected heldout inputs were accessed. Catalog
availability establishes an advertised route, not account availability, measured
PDF quality, calibrated probabilities, or a successful request.

The useful division is **decision gates select retained alternatives; multimodal
chat transcribes missing text and topology**. P002's dense natural-page misses,
detector omissions, strict geometry/merge failures, and incomplete OCR inventory
cannot all be repaired by selecting among the same incomplete alternatives.
Use separate matched gate and transcription screens rather than treating every
model carrying an evaluation label as a substitute for table reconstruction.

## Requested decision and evaluation models

The [OpenRouter filtered decisions catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions)
contains 19 entries, up from 16 in the October 8 research. The ordinary chat
catalog omits these entries. All exact requested IDs below remain advertised.
Prices are USD per million input tokens; their advertised output price is zero.

| Exact OpenRouter ID | Input USD/M | Context | Input |
|---|---:|---:|---|
| `typesafe/jev-1.13` | 0.042 | 64,000 | text |
| `perplexity/pplx-decider-v1.1-27b` | 0.020 | 262,144 | text, image |
| `liquid/d1` | 0.040 | 65,536 | text |
| `upstage/solar-decide-flash` | 0.050 | 524,288 | text |
| `upstage/solar-decide` | 0.050 | 524,288 | text |
| `openai/gpt-6-luna-decisions` | 0.100 | 1,050,000 | text, image |
| `cloudflare/clef-flash` | 0.038 | 65,536; provider 16,384 | text, image |
| `cloudflare/clef` | 0.240 | 65,536 | text, image |
| `togethercomputer/tev1-4b-experimental` | 0.042 | 32,768 | text |
| `inception/mercury-decide` | 0.020 | 65,536 | text |
| `respan/span-01` | 0.020 | unknown: catalog zero | text |

Clef Flash's input price increased from 0.021 to 0.038 USD/M in the previous
snapshot. New entries are `cloudflare/clef-omni` (image/text, 65,536 context,
0.150 USD/M), `microsoft/microsoft-decision-1` (text, 32,768, 0.042 USD/M), and
`nace-ai/drex-v1.5` (text, 131,072, 0.040 USD/M). New catalog entries are
compatibility-probe candidates, not measured upgrades. The `~typesafe/jev-latest`
entry is an alias; retain the pinned Jev checkpoint for repeatability.

[Vercel's public models catalog](https://ai-gateway.vercel.sh/v1/models) and
[TypeSafe-specific listing](https://ai-gateway.vercel.sh/typesafe/v1/models)
confirm Laya, d1, Jev, Microsoft Decision-1, and Luna Decisions. Their identity
and modality contracts must be frozen independently from OpenRouter.

| Vercel ID | Input USD/M | Context | Catalog input | Notes |
|---|---:|---:|---|---|
| `convaiinnovations/laya` | 0 | 8,192 | text | evaluation; max_tokens 0 |
| `convaiinnovations/laya-free` | 0 | 8,192 | text | evaluation; max_tokens 0 |
| `liquid/d1` | 0.040 | 65,536 | text, image | evaluation; max_tokens 0 |
| `typesafe-ai/jev` | 0.042 | 32,000 | text | evaluation; distinct gateway ID |

The TypeSafe listing labels Jev `jev` and describes 64,000 total request tokens
and 32,000 for state plus the longest question. Preserve that distinction from
the main catalog's 32,000 context rather than choosing an optimistic interpretation.
Vercel's evaluation output modality says text even though these entries generate
bounded answers and set max_tokens to zero; this is not evidence for transcription.
The [Laya launch announcement](https://vercel.com/changelog/laya-decision-model-now-available-on-ai-gateway-free-through-october-31)
limits the free Boundless promotion to October 31, 2026. The standard ID begins
billing afterward; the `-free` ID stops serving. Retain Boundless-only routing.
The [d1 launch announcement](https://vercel.com/changelog/liquid-ai-d1-is-available-on-ai-gateway)
explicitly demonstrates image decisions, confirming a real provider difference
from the text-only OpenRouter d1 catalog entry.

## Exact endpoint and adapter compatibility

[OpenRouter Decisions](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
uses `POST /api/alpha/decisions`, shared `state`, a named `questions` mapping, and
`noul`, `choice`, or `score` questions. The repository's `decision_hosted.py`
already supports the requested pinned decision IDs. Decisions return typed
answers; they cannot generate arbitrary cell strings or invent source IDs.

The [OpenRouter multimodal contract](https://openrouter.ai/docs/guides/community/multimodal-decisions)
places image_url data-URL parts directly in the top-level state array with plain
string text items. PNG/JPEG/WebP are supported; remote URLs are not fetched.
Clef variants allow four images; Luna allows 128. Clef Flash and Clef Workers AI
silently discard text-state tokens after roughly 2,000, and estimate admission
from base64 length, so catalog context alone is unsafe for long evidence. The
new Omni entry is documented as image-capable, but the guide does not explicitly
extend those Flash text/base64 limits to Omni: test it rather than assuming.

[Vercel TypeSafe](https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe)
uses `POST https://ai-gateway.vercel.sh/typesafe/v1/systemone` with the same
state/named-question primitives. The existing `decision_gateway.py` allowlist
is Laya/Laya-free/d1 only; Jev, Microsoft, and Luna require a reviewed adapter
extension before experiments. The main
[Vercel decision API](https://vercel.com/docs/ai-gateway/modalities/decision)
uses `/v1/evaluate`; it is a separate transport from the TypeSafe compatibility
route. Vercel's SDK d1 example places image parts in state, while the repository's
previous successfully measured TypeSafe d1 vision adapter sends top-level
`images`. Do not copy a different API's image schema over the working adapter
without an explicit matched compatibility probe.

Vercel decision fallbacks can charge multiple stages and change the served
model. Keep them disabled in model comparisons. The official TypeSafe contract
states that chat fallback choice/score `confidence: 0` and empty probabilities
mean unavailable measurements, not measured zero confidence. Native probabilities
and absent measurements must remain distinguishable.

Tev's [Together-authored model card](https://huggingface.co/togethercomputer/Tev1-4B-experimental)
uses a next-token letter classifier over 2–24 options; gateway probability
normalization is a distinct wrapper. [Span's author documentation](https://www.respan.ai/docs/documentation/span-01/concept)
concerns behavior detection over conversation spans with an unknown/not-observable
state, not generic PDF transcription. [Laya's author repository](https://github.com/NandhaKishorM/laya)
describes a non-autoregressive text decision engine. None of these descriptions
establishes generic document reconstruction quality.

Existing measured evidence remains [decision-alternatives.md](decision-alternatives.md):
Span returned 404 despite listing; an explicit Clef Flash PrimeIntellect route
also returned 404. That provider is still listed today, which does not resolve
the failure. Luna's prior reported-zero charges retain labeled estimates.
[Gateway supported results](lowlevel-gateway-supported.md) establish Laya's
successful minimal/word requests and poor relationship quality;
[Laya diagnostics](lowlevel-laya-diagnostics.md) retain 422 failures on compact
requests. [Gateway vision results](lowlevel-gateway-vision.md) already retain d1
image experiments. Preserve those observations instead of restarting discovery
as though the models were untested.

## Eight standard multimodal transcription candidates

All eight exact OpenRouter IDs below currently advertise image input, text
output, `response_format`, and `structured_outputs`. Prices are ordinary base
catalog input/output USD per million tokens, excluding cache discounts, long
context tiers, tools, service tiers, and image-token accounting. These are
shortlist hypotheses; only Haiku is an existing P002 transcription baseline.

| OpenRouter ID | Input / output USD/M | Context | Vercel ID and base price |
|---|---:|---:|---|
| `anthropic/claude-haiku-5.5` | 0.100 / 0.500 | 1,000,000 | same, same |
| `openai/gpt-6-luna` | 0.100 / 0.500 | 1,050,000 | same, same |
| `qwen/qwen3.5-9b` | 0.100 / 0.150 | 262,144 | exact ID absent in frozen catalog |
| `google/gemma-4-26b-a4b-it` | 0.0675 / 0.225 | 262,144 | same, 0.150 / 0.600 |
| `google/gemma-4-31b-it` | 0.090 / 0.340 | 262,144 | same, 0.140 / 0.400 |
| `mistralai/ministral-8b-2512` | 0.150 / 0.150 | 262,144 | `mistral/ministral-8b`, same price |
| `mistralai/ministral-14b-2512` | 0.200 / 0.200 | 262,144 | `mistral/ministral-14b`, same price |
| `google/gemini-3.5-flash-lite` | 0.300 / 2.500 | 1,048,576 | same; context 1,000,000, same price |

Qwen is already on the shared hosted allowlist, but the pipeline's chat model
menu is the three Anthropic baselines. Luna/Gemma/Ministral/new Gemini require
reviewed allowlist and frozen-rate additions; this research edits neither client.
Avoid routers, latest aliases, free variants, image-generation models, or treating
Vercel's differently named Ministral routes as proven checkpoint identity.

[Provider-specific endpoint listings](https://openrouter.ai/api/v1/models/google/gemma-4-26b-a4b-it/endpoints)
show that capability and price depend on route. A stable matched screen can pin
schema-advertising providers with `only`, `allow_fallbacks: false`, and
`require_parameters: true`, retain served provider/model, and keep strict local
semantic validation. Candidate routes verified in the saved endpoint responses:

| Model | Example exact provider tag | Input / output USD/M |
|---|---|---:|
| Gemma 26B A4B | `nextbit/bf16` | 0.0675 / 0.225 |
| Gemma 26B A4B | `deepinfra/fp8` | 0.070 / 0.340 |
| Gemma 31B | `deepinfra/turbo` | 0.090 / 0.340 |
| Qwen 9B | `deepinfra/bf16` | 0.100 / 0.150 |
| Ministral 8B / 14B | `mistral` | 0.150 / 0.150; 0.200 / 0.200 |
| Luna chat | `openai` | 0.100 / 0.500 |
| Haiku | `anthropic` | 0.100 / 0.500 |
| Gemini Lite | `google-ai-studio` | 0.300 / 2.500 |

Gemma26's cheapest endpoint is `darkbloom` at 0.042/0.220, with advertised schema
support, while several other Gemma endpoints omit it. Haiku AWS/Bedrock routes
omit `structured_outputs`; Anthropic/Google/Azure routes advertise it. The
[structured-output documentation](https://openrouter.ai/docs/guides/features/structured-outputs)
explicitly makes support endpoint-specific and warns that strict enforcement
varies by provider. Even a valid schema cannot ensure normalized bounds, covered
merge slots, literal text, or correct topology. Vercel Ministral8's catalog
maximum output is 4,000 versus the much larger OpenRouter provider maximum;
keep fixed bounded output settings and record truncations.

## P002-directed experimental sequence

1. **Strict crop transcription:** use the same frozen natural16 crops and exact
   image bytes across Haiku, Luna chat, Qwen9B, Gemma26, and Ministral14B first.
   Retain all attempts, normal-stop failures, source-negative cases, output
   tokens, full tables/cells/spans, wall/CPU/RSS, and route-specific cost. Primary
   quality remains complete page-atomic validation, with separate diagnostics
   for bbox range, rectangularity, covered slots and duplicate spans. This tests
   P002's repeated strict-output failures and stochastic dense response variation.
2. **Acquisition versus legibility:** freeze detector boxes before comparing
   transcription. Independently test whole-page/fixed-tile acquisition on dense
   pages, then transcribe the same acquired crops. P002's dense p1 often had no
   proposals; cheap decision gates cannot recover an unoffered region. Keep all
   sixteen primary pages, including negatives and atomic failures.
3. **Decision-only relational gates:** compare compact source-only PPLX/Luna
   Decisions/d1 image decisions against the identical finite alternatives, with
   explicit none/abstain. New Clef Omni is a bounded compatibility screen for
   late-state/image evidence, not a replacement for transcription. Jev/Laya/Solar/
   Mercury/Tev are text controls; Span needs its unresolved 404 investigated
   before any new quality run. No choice may fabricate missing OCR characters.
4. **Source inventory ceilings:** preserve the P002 distinction between missing
   text, unsupported source, and incorrect assignment. Evaluate standard image
   transcription where required source values are absent; gate-only improvements
   cannot exceed source-owned inventory ceilings. Keep native logical orientation
   fixed so known authored rotated improvements do not confound model comparison.

These are proposed root-coordinated paid experiments, not executed work. Begin
with small source-only compatibility cases and the existing tiny screen, then
expand only a frozen DEV-selected policy. Spending reservations and account keys
remain root-owned. Full276 is a later confirmation after screening, not a reason
to repeatedly tune on protected data.

## Retained public provenance

Raw catalogs, provider endpoint responses and official contract pages are retained
under ignored `bench/results/pdf-master-artifacts/pipeline-p003/catalog/`.
`manifest.json` records exact URL, fetch UTC, payload bytes and SHA-256 for every
successful public fetch. Raw payloads were preserved before parsing; derived
`.text` files are readable helpers, not substitutes for raw provenance. The
Vercel `/sdks-and-apis/openai` URL returned 404; the correct retrieved route is
`/sdks-and-apis/openai-compat`. No live POST was made. This documentation-only
change needs no behavior tests; provenance/hash and ignore checks were run.

| Payload | Fetched UTC | Bytes | SHA-256 |
|---|---|---:|---|
| [openrouter-decisions.json](https://openrouter.ai/api/v1/models?output_modalities=decisions) | 2026-10-10T18:28:05.795199+00:00 | 17533 | `b07bd50be8933b083a6f2c9da1bf59624c6c59f4134dc0b595b51a278a82dca5` |
| [openrouter-chat.json](https://openrouter.ai/api/v1/models) | 2026-10-10T18:28:05.852852+00:00 | 765928 | `a9f0778fc0060792c642d51eeafacc096b398c54e219f0457c38b1c0b40198dc` |
| [vercel-models.json](https://ai-gateway.vercel.sh/v1/models) | 2026-10-10T18:28:06.080298+00:00 | 469110 | `35fdf51d7f0dd6ece4e68e99797ae89090799d1c2ede8edb28c686044c004959` |
| [vercel-typesafe.html](https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe) | 2026-10-10T18:28:41.759220+00:00 | 12698 | `56c8dbd697344bfab750d70a7d98f12f6879a009cdb9abbdcff5de33c02f32a4` |
| [openrouter-multimodal-decisions.html](https://openrouter.ai/docs/guides/community/multimodal-decisions) | 2026-10-10T18:28:43.579237+00:00 | 568890 | `c8a72faf0a478176cd0187409c613e72c08267d2de5e0f2a6fe9a2ff2269374c` |
| [openrouter-decisions-contract.html](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) | 2026-10-10T18:28:43.864064+00:00 | 784774 | `e9d0c03ef016e12cf430d68b39b28e569a8de03301c1d08a5aea6a3b6b845a40` |
| [openrouter-structured-outputs.html](https://openrouter.ai/docs/guides/features/structured-outputs) | 2026-10-10T18:28:44.013715+00:00 | 696011 | `5f1974843a77eb977b6508e119474a672becff550eddcddb6d4e30360ac95916` |
| [laya-readme.md](https://raw.githubusercontent.com/NandhaKishorM/laya/main/README.md) | 2026-10-10T18:28:44.130292+00:00 | 110756 | `da723fff47b513146bac734de4c42312b6f1cbcf8d900ddf12cba55d57cd382f` |
| [tev-model-card.md](https://huggingface.co/togethercomputer/Tev1-4B-experimental/raw/main/README.md) | 2026-10-10T18:28:44.209548+00:00 | 3427 | `3984b6b90801471bdf1ad802852605c835720533d80fbb60c42cd5245527ee40` |
| [span-concept.html](https://www.respan.ai/docs/documentation/span-01/concept) | 2026-10-10T18:28:44.735223+00:00 | 166447 | `b2c1bf3f0831b5a94c36fea310c0be07b2e7e6f57c091079e881ddf0e7553dd2` |
| [vercel-typesafe-models.json](https://ai-gateway.vercel.sh/typesafe/v1/models) | 2026-10-10T18:28:58.277271+00:00 | 2387 | `37999dadcc4e582ed5ebf2644b00224b4a4773c64088e74e8c96e423eb2c522b` |
| [vercel-decision.md](https://vercel.com/docs/ai-gateway/modalities/decision) | 2026-10-10T18:28:58.853936+00:00 | 1160088 | `cde9c03924ebb92f69d33329468094ec428cae2f9aa659996cb931cdef64ec38` |
| [vercel-liquid.md](https://vercel.com/changelog/liquid-ai-d1-is-available-on-ai-gateway) | 2026-10-10T18:28:59.861747+00:00 | 541159 | `a871a2cb4032b1a05aa1bba968646dca18c0bc6df4d1e6d2d98b2ed33d8bc9dd` |
| [vercel-laya.md](https://vercel.com/changelog/laya-decision-model-now-available-on-ai-gateway-free-through-october-31) | 2026-10-10T18:29:00.257858+00:00 | 522372 | `1c4d025376cd30e1bbe3f1736488138eb8f509aa1577a540e80e28a1967890aa` |
| [vercel-openai-contract.md](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-compat) | 2026-10-10T18:29:00.806166+00:00 | 1138483 | `34e7787e67502c35e8d646182fd8c8091af811476578305796c8d56cbf75bb30` |
| [endpoints-anthropic--claude-haiku-5.5.json](https://openrouter.ai/api/v1/models/anthropic/claude-haiku-5.5/endpoints) | 2026-10-10T18:29:52.708860+00:00 | 13485 | `a8edd1647d5c1bf900ec536122fccd43e99d4383669b6fcb1d87d6f120c5d011` |
| [endpoints-openai--gpt-6-luna.json](https://openrouter.ai/api/v1/models/openai/gpt-6-luna/endpoints) | 2026-10-10T18:29:52.809706+00:00 | 8918 | `8d01937e058189dd8ce8dddf477a0fb56d8cf08c6a56f5d4141a1e21077bd027` |
| [endpoints-google--gemini-3.5-flash-lite.json](https://openrouter.ai/api/v1/models/google/gemini-3.5-flash-lite/endpoints) | 2026-10-10T18:29:52.858391+00:00 | 9910 | `a8b13b5eb7be103625c49730213ede4b884897308a7c67afc3bd53fba9a63c9e` |
| [endpoints-google--gemma-4-26b-a4b-it.json](https://openrouter.ai/api/v1/models/google/gemma-4-26b-a4b-it/endpoints) | 2026-10-10T18:29:52.905142+00:00 | 13396 | `3cdc1501cb026b1a0b95fc4d7d3287f620c18ea07065c3a805dc5bcd8e3d5d0b` |
| [endpoints-google--gemma-4-31b-it.json](https://openrouter.ai/api/v1/models/google/gemma-4-31b-it/endpoints) | 2026-10-10T18:29:52.955779+00:00 | 13143 | `5f615aae513eeb9413cba8f2697e4d4f01019d36591f6d21d9e386ea5c3f58fa` |
| [endpoints-qwen--qwen3.5-9b.json](https://openrouter.ai/api/v1/models/qwen/qwen3.5-9b/endpoints) | 2026-10-10T18:29:53.001761+00:00 | 6226 | `9a663fa644fd148279c82b91faf02f73d242f58154a94a27795f01dd513b4f25` |
| [endpoints-mistralai--ministral-14b-2512.json](https://openrouter.ai/api/v1/models/mistralai/ministral-14b-2512/endpoints) | 2026-10-10T18:29:53.050146+00:00 | 3315 | `ac76045fad6491c5c36f2134f7ab1f7e565a32459f75002194a7ceb5715e6985` |
| [endpoints-mistralai--ministral-8b-2512.json](https://openrouter.ai/api/v1/models/mistralai/ministral-8b-2512/endpoints) | 2026-10-10T18:29:53.104201+00:00 | 3240 | `796d3c8106671e3a622300d5aa69823693c48a12f125dcfa66c4cb2704cb19fe` |
| [endpoints-cloudflare--clef-flash.json](https://openrouter.ai/api/v1/models/cloudflare/clef-flash/endpoints) | 2026-10-10T18:29:53.149364+00:00 | 1938 | `0fef8fd43270420ca28945ce098f5fe3087dd57580ce82cc98aa69cb5023bdb5` |
| [endpoints-cloudflare--clef-omni.json](https://openrouter.ai/api/v1/models/cloudflare/clef-omni/endpoints) | 2026-10-10T18:29:53.222833+00:00 | 1223 | `3c5eaadd00bdf6fea4ce7eaf73d8f697ac1ee3d2138569ea9ab846585966d3f2` |
| [endpoints-perplexity--pplx-decider-v1.1-27b.json](https://openrouter.ai/api/v1/models/perplexity/pplx-decider-v1.1-27b/endpoints) | 2026-10-10T18:29:53.297634+00:00 | 1291 | `514320287e5e45d6845c89fa48cd5273a7c01e6f1bf7447584994350a55a9e0c` |
| [endpoints-typesafe--jev-1.13.json](https://openrouter.ai/api/v1/models/typesafe/jev-1.13/endpoints) | 2026-10-10T18:29:53.345564+00:00 | 1171 | `aebca84579552afcd462dd79489570f19fd9324a8657cad3d9d1a9a678b2a943` |
