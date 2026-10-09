# Requested decision model catalog

Research snapshot: **2026-10-08**. All eight exact requested IDs appear in
OpenRouter's public catalog when filtered for `output_modalities=decisions`.
This establishes advertised availability, pricing, and modalities; it does not
establish successful inference for this account, PDF relationship quality, or
calibration. Retained request results and measured findings belong in
[decision-alternatives.md](results/decision-alternatives.md), separately from this catalog.
No requested ID is replaced with a chat model, earlier checkpoint, larger model,
or free variant.

## Discovery and advertised specifications

Fetch the [public decisions catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions)
with an unauthenticated GET. The retained response is
`bench/results/pdf-master-artifacts/decisions/discovery/decision-model-catalog.json`
(ignored local artifact). It contains 16 entries. An unfiltered
`GET /api/v1/models` excluded these decisions entries during discovery, so absence
from that response is not evidence that an exact decisions ID is unavailable.

Prices below are USD per million input tokens from the retained filtered response.
Every listed entry advertises zero output-token price. Prices can change; Mercury
and Solar pages display promotional pricing. Context is the catalog's token
count, not a guarantee that a provider reads that much evidence.

| Exact requested ID and official gateway page | Canonical slug in snapshot | Input / 1M | Advertised context | Input modalities |
| --- | --- | ---: | ---: | --- |
| [perplexity/pplx-decider-v1.1-27b](https://openrouter.ai/perplexity/pplx-decider-v1.1-27b) | `perplexity/pplx-decider-v1.1-27b-20261006` | $0.020 | 262,144 | Text, image |
| [upstage/solar-decide-flash](https://openrouter.ai/upstage/solar-decide-flash) | `upstage/solar-decide-flash-20261008` | $0.050 | 524,288 | Text |
| [openai/gpt-6-luna-decisions](https://openrouter.ai/openai/gpt-6-luna-decisions) | `openai/gpt-6-luna-decisions-20261006` | $0.100 | 1,050,000 | Text, image |
| [liquid/d1](https://openrouter.ai/liquid/d1) | `liquid/d1-20260930` | $0.040 | 65,536 | Text |
| [cloudflare/clef-flash](https://openrouter.ai/cloudflare/clef-flash) | `cloudflare/clef-flash` | $0.021 | 65,536 | Text, image |
| [togethercomputer/tev1-4b-experimental](https://openrouter.ai/togethercomputer/tev1-4b-experimental) | `togethercomputer/tev1-4b-experimental-20260923` | $0.042 | 32,768 | Text |
| [inception/mercury-decide](https://openrouter.ai/inception/mercury-decide) | `inception/mercury-decide-20260930` | $0.020 | 65,536 | Text |
| [respan/span-01](https://openrouter.ai/respan/span-01) | `respan/span-01-20260925` | $0.020 | Unspecified (`0` in catalog) | Text |

Span's zero context value is missing information, not a zero-length window or an
unbounded allowance. Clef Flash also reports 16,384 in its `top_provider` context
field, despite the model-level 65,536 value. Retain both values when comparing
provider behavior. The other advertised context values do not prove useful
long-document coverage either.

## Gateway contract and native interfaces

The [OpenRouter Decisions reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
specifies `POST https://openrouter.ai/api/alpha/decisions` with `model`, `state`,
and `questions`. State may be a string, JSON object, or array. Questions are a
mapping keyed by names. `noul` returns a yes/no probability; `choice` selects an
option and may include its probability distribution and confidence; `score`
returns an expected score and may include level probabilities, legend and
confidence. Missing probability fields remain unmeasured. The response also reports
model, provider, request ID, token usage, and cost. A valid typed response alone
does not establish that its probabilities are calibrated for PDF evidence.

OpenRouter normalizes native services into this gateway contract. Liquid d1,
Mercury Decide, and Solar Decide Flash advertise a System One interface; this
does not mean a native provider's host, authentication, or model ID can be used
unchanged with OpenRouter. The experiment uses the exact gateway IDs above and
records the served model and provider independently.

The [official OpenAI Decisions reference](https://developers.openai.com/api/reference/resources/decisions/methods/create)
uses a separate native `POST /v1/decisions` endpoint, model `gpt-6-luna`, shared
`input`, and an ordered questions array. Its yes/no primitive is `predicate`,
with a `probability` result. These differ from OpenRouter's `state`, named
question mapping, and `noul`. Native documentation therefore verifies the service
but does not replace the gateway request schema.

For gateway images, follow the
[OpenRouter multimodal Decisions guide](https://openrouter.ai/docs/guides/community/multimodal-decisions):
put an `image_url` part directly in the top-level state array, using a PNG, JPEG,
or WebP data URL. Plain text array items are strings. Gateway remote image URLs
are not fetched, nested image objects are not treated as image inputs, and
Responses-style `input_image` parts are rejected. Luna allows at most 128 images;
Clef and Clef Flash allow four. Native OpenAI image support has its own schema
and must not be copied into gateway calls.

## Interpretation limits that affect PDF experiments

**Clef Flash:** The same official multimodal guide states that the Workers AI
deployment reads roughly the first 2,000 text-state tokens and silently drops
the rest; images are counted separately. This is a provider-specific serving
limit, distinct from the catalog context window. Keep evidence compact and test
late-state facts before claiming document-wide coverage. Image admission also
estimates tokens from base64 length before inference, so large encoded images
can be refused before their actual model token count is known.

**Tev1:** The gateway page describes a Qwen3.5-4B supervised fine-tune with a
standard next-token head that emits one option letter over 2–24 choices through
chat completions. The
[Together-authored model card](https://huggingface.co/togethercomputer/Tev1-4B-experimental)
also describes this classifier interface and says calibration has not been
comprehensively evaluated. The filtered OpenRouter catalog nevertheless labels
its output modality `decisions`. The transformation from native letter output
to gateway probability distributions is unverified here. Preserve returned
fields, test gateway compatibility, and do not infer calibrated probabilities
from the catalog label or substitute a direct chat call into the comparison.

**Span-01:** [Respan's model documentation](https://www.respan.ai/docs/documentation/span-01/concept)
describes a first-party behavior scorer for text conversation traces. Its native
scores are `p_present`, `p_absent`, and `p_not_observable`, with the latter
representing insufficient evidence. The paid native ID is `span-01-pro`, called
through `/api/v1/scores`; that is a different interface from this experiment's
gateway ID. Behavior detection does not establish generic PDF relationship
competence, and the gateway's mapping to `noul` must not be assumed to preserve
native unknown-state semantics. Measure explicit insufficient-evidence cases.

## Reproduction in this repository

The existing runner accepts exact requested models through `--models` and selects
literal resolved spans through `--variant resolved`. Use one case per request
to separate model support from batching behavior. This is an opt-in paid command;
run it only within the authorized cumulative cap and persistent ledger described
in [DECISION_MODELS.md](DECISION_MODELS.md).

```bash
CUDA_VISIBLE_DEVICES='' uv run python -m bench.decisions --run-hosted \
  --models perplexity/pplx-decider-v1.1-27b upstage/solar-decide-flash \
  openai/gpt-6-luna-decisions liquid/d1 cloudflare/clef-flash \
  togethercomputer/tev1-4b-experimental inception/mercury-decide respan/span-01 \
  --variant resolved --batch-size 1
```

For a bounded compatibility probe, add `--single`; `--smoke` selects the runner's
small smoke subset. Run `--report-only` to analyze retained evidence locally
without making paid requests. Keep failures, refusals, malformed distributions,
served IDs, latency, and actual usage cost with successes. Full responses and
catalog snapshots remain ignored local artifacts; this Markdown catalog records
advertised facts, and the findings report records observed outcomes.


Provider-specific checks can add `--provider primeintellect` for Clef Flash. This
pins the exact provider tag without fallbacks, preserves existing price caps,
and adds the route to the cohort label. Use the provider's actual reported
identity and usage in comparisons. The runner caps native requests at 16
questions as well as 32,000 UTF-8 request bytes: some providers bill the shared
state separately for every question. These bounds keep the $0.30 reservation
conservative at the catalog's observed input prices; they are benchmark limits,
not a statement of every provider's maximum API capacity.
