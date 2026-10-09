# Image decision model survey

Research date: **2026-10-08**. Public catalog and documentation reads only; no
credentials, inference requests, or paid probes were used for this survey.
Recommendations below are hypotheses to test on DEV evidence, not quality
rankings. The current plan tests RGB8, grayscale8, and a 16-color palette PNG
with 4-bit indices independently at 128/512/1200 px long edge: nine real arms
and nine matched blanks. Preserve aspect ratio. Palette4 is a color intervention;
there is no combined grayscale-plus-palette arm.

## Native image decision endpoints

Filtering the current OpenRouter catalog for output modality `decisions` and
input modality `image` yields exactly these four IDs. Their completion price is
zero; input prices below are USD per million tokens, converted from the catalog's
USD-per-token values. Other decision models currently advertise text input only.
[Official filtered catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions).

| Exact model ID | Catalog input USD/M | Catalog context | Candidate role |
| --- | ---: | ---: | --- |
| `perplexity/pplx-decider-v1.1-27b` | 0.020 | 262,144 | Cheapest catalog native image decision baseline |
| `cloudflare/clef-flash` | 0.021 | 65,536 | Low-price flash challenger |
| `openai/gpt-6-luna-decisions` | 0.100 | 1,050,000 | Native multimodal decision comparison |
| `cloudflare/clef` | 0.240 | 65,536 | Full Clef comparison |

Provider-specific endpoints matter. Clef Flash currently lists PrimeIntellect at
$0.021/M with 16,384 context and Cloudflare at $0.090/M with 65,536 context.
Full Clef lists PrimeIntellect at $0.042/M with 16,384 context and Cloudflare at
$0.240/M with 65,536 context. Do not substitute the minimum endpoint rate for
the provider actually serving a request.
[Flash endpoints](https://openrouter.ai/api/v1/models/cloudflare/clef-flash/endpoints),
[Clef endpoints](https://openrouter.ai/api/v1/models/cloudflare/clef/endpoints).
The observed Luna and Perplexity endpoint rates agree with their catalog rates.
[Luna endpoints](https://openrouter.ai/api/v1/models/openai/gpt-6-luna-decisions/endpoints),
[Perplexity endpoints](https://openrouter.ai/api/v1/models/perplexity/pplx-decider-v1.1-27b/endpoints).

Image modality declarations are discovery evidence, not confirmation that every
provider accepts the benchmark's exact System One `state` envelope, image
encoding, question type, or batching. Probe compatibility before expanding the
matrix. Do not silently drop a model when it fails; retain the request shape,
sanitized error, provider, and failure category.

## Vercel can provide a native decision route

Vercel officially documents `POST https://ai-gateway.vercel.sh/v1/decisions`,
including `openai/gpt-6-luna-decisions` with images. Its envelope uses `input`
messages and a question array, rather than the existing System One `state` and
question mapping. Images are base64 data URLs in `input_image` parts, with
`detail` set to `low`, `high`, `auto`, or `original`; external URLs/file IDs are
unsupported. There is a 128-image request limit. Returned answers are ordered
and usage/routing/cost metadata is retained.
[Official Vercel Decisions API](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions).

There is a discovery discrepancy: public `/v1/models`, including requests with
`?type=decision` and `?output_modalities=decisions`, did not list Luna Decisions
or Clef on the research date. The returned Jev entry was text-only and typed
`evaluation`. Do not infer that documented decision endpoints are unavailable
from this catalog response alone; verify the desired slug through an authorized
compatibility request. No Vercel inference was performed here.
[Public Vercel model catalog](https://ai-gateway.vercel.sh/v1/models).

Vercel also documents decision fallbacks to vision language models using
structured output. Those are generative selectors, not native probabilistic
decision heads. Choice/Score confidence and distributions are unavailable on
language-model fallback; its TypeSafe-compatible surface uses `confidence: 0`
and `probabilities: {}` as unavailable sentinels, not measured zero confidence.
Record final model and every routing attempt, and charge fallback attempts
separately. Disable automatic fallback during an individual-model comparison.
[Official decision fallback semantics](https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks).

## Cheap generative challengers through Vercel

The following exact IDs currently advertise image input and structured output.
Prices are ordinary uncached USD/M input/output at the first pricing tier.
Refresh tiers and actual provider before paid requests.
[Official Vercel catalog](https://ai-gateway.vercel.sh/v1/models).

| Exact model ID | Input / output USD/M | Proposed comparison |
| --- | ---: | --- |
| `alibaba/qwen3.7-flash` | 0.030 / 0.130 | Lowest-price shortlisted vision selector; tier rises above 32k context |
| `anthropic/claude-haiku-5.5` | 0.100 / 0.500 | Cross-family comparison; first tier through 100k context |
| `google/gemini-2.5-flash-lite` | 0.100 / 0.400 | Low-cost Google vision baseline |
| `google/gemini-3.1-flash-lite` | 0.250 / 1.500 | Newer Google comparison at higher listed rates |
| `openai/gpt-6-luna` | 0.100 / 0.500 | Generative versus native Luna comparison |
| `mistral/ministral-14b` | 0.200 / 0.200 | Alternative family with inexpensive bounded output |

My recommended first additional probes are Qwen3.7 Flash, Haiku5.5, and
Gemini2.5 Flash Lite: low catalog rates and different provider families make
them useful challengers. This is a cost/diversity rationale, not evidence that
they outperform the native decision models. Keep choices to retained candidate
IDs plus explicit abstention, use a strict schema, and bound output/reasoning.
Embeddings return vectors and require a separate downstream ranking method;
embedding models must not be counted as decision-model trials.

## Image cost and fidelity

Reducing PNG bit depth or grayscale channels can reduce encoded bytes and
base64 transport size. It does not establish lower image-token cost: providers
decode images and apply model-specific resizing, patches, tiles, or resolution
budgets. As direct-provider examples, current Claude documentation describes
28×28 visual patches and tier-specific resizing; Google describes image tiling
and Gemini3 media-resolution token budgets. Retain actual width/height,
quantization levels, PNG mode/header bit depth, encoded bytes, decoded pixels,
and requested/provider-resolved detail settings.
[Claude image processing](https://platform.claude.com/docs/en/build-with-claude/vision),
[Gemini image processing](https://ai.google.dev/gemini-api/docs/image-understanding).

Compare RGB8 with gray8 and color-palette4 at each resolution. The palette
intervention is 16-color indexed PNG with 4-bit indices, not grayscale or a
4-bit-per-channel raster. Quantizing values while retaining an 8-bit container
must be labeled accurately. Reduced levels can destroy faint grid rules,
antialiasing, fine text, and color distinctions; those are experimental outcomes.
Do not predict tokens from base64 character count or multiply image size by a
universal token constant. Prefer positive provider charges; when charge is zero
or missing, estimate from published serving-provider rates and reported tokens,
label the basis, retain reported zero separately, and mark incomplete token/rate
coverage as partial. Reservations remain separate from effective estimates.

## Compatibility and experiment admission

Before running the full matrix for a model/provider:

1. Freeze the exact model ID, catalog access timestamp, serving provider,
   uncached rates, route, request schema, and image options.
2. Send one authorized small DEV image with a simple predicate and bounded
   choice over retained IDs. Validate typed answers, abstention, token usage,
   cost/routing fields, and whether confidence is native or unavailable.
3. Confirm accepted grayscale PNG modes and reduced-bit-depth containers with
   a bounded probe. A format rejection is a compatibility result.
4. Run RGB8/gray8/palette4 independently at 128/512/1200 px across **all four**
   discovered native image decision IDs, with a matched
   blank for every arm, retaining failures and complete outputs.
   Keep generative selector results in a separately labeled comparison.
5. Evaluate declared relationship labels and abstention separately from authored
   silver literal anchors. Report transport bytes, provider tokens, measured or
   estimated cost, latency, and CPU/RSS for local preprocessing independently.

Direct-provider documentation informs preprocessing and compatibility, but
direct-provider inference integrations are outside this comparison: the user
is willing to configure Vercel as the alternative gateway. Held-out evidence
must remain sealed; this survey and its proposed compatibility work use DEV only.
