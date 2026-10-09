# Vercel AI Gateway decision-model expansion

Catalog checked on 2026-10-09 against all 413 entries from the live
[Vercel model catalog](https://ai-gateway.vercel.sh/v1/models), compared with the
[OpenRouter decisions catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions).
Frozen full responses are local ignored artifacts at
`lowlevel-v1/vercel-catalog.json` and `lowlevel-v1/catalog-all-decisions.json`.

| Candidate | What it adds | Catalog input | Input USD / million tokens | Status |
| --- | --- | --- | ---: | --- |
| `convaiinnovations/laya` | New decision-model family absent from OpenRouter | Text; 8,192 context | 0, promotional | Include text grouping and compact evidence controls |
| `convaiinnovations/laya-free` | Same named family, alternate free route; not an independent architecture | Text; 8,192 context | 0, promotional | Include availability/parity pilot; do not double-count model diversity |
| `liquid/d1` via Gateway | A vision route missing from OpenRouter's advertised d1 capability | Text and image; 65,536 context | 0.04 | Include matched image sweep after route smoke test |
| `typesafe-ai/jev` | Gateway name for Jev; not evidence of a new checkpoint | Text; 32,000 context | 0.042 | Optional route control; do not count as Gateway-exclusive family |
| `openai/gpt-6-luna-decisions` | Existing model through another gateway | Catalog says text; description says text and image | 0.10 input; output missing in this catalog | Route capability needs confirmation; existing OpenRouter vision comparison remains |

The catalog has exactly five `type=evaluation` entries. Other language models
whose descriptions contain "decision" are not silently classified as dedicated
System One models. Laya and its free alias share the same named family; equality
of actual served checkpoints is unverified. [Vercel's Laya page](https://vercel.com/ai-gateway/models/laya-free)
states promotional pricing ends October 31, 2026. A zero-price catalog is retained
as zero, not replaced with another provider's paid rate or called infinite efficiency.

Use the native [Gateway decision endpoint](https://vercel.com/docs/ai-gateway/modalities/decision)
or the [TypeSafe-compatible endpoint](https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe),
with explicit model/provider identity and no model fallback. The newer
[OpenAI-compatible Decisions documentation](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions)
(last updated October 8) supports image parts, whereas an October 5 comparison
article says it rejects images. Prefer current endpoint documentation plus a bounded
live smoke test over either a stale article or a capability inferred from a model name.
[Liquid's official release](https://www.liquid.ai/blog/d1-decision-model)
also documents d1 vision, including image-patch input billing. Direct Liquid access
is a separate provider route, not proof that every gateway forwards images.

## Planned L009 comparison

Freeze text-only source projections for Laya before reading labels. Keep the same
choice instructions used by existing runs and stay below the smallest serving
context with conservative body admission. Select evidence through source-only rules;
no model-specific label hints or result-driven source omission. Run one route smoke,
then the complete declared text matrix if accepted.

Translate the four-model image sweep into an explicitly named Gateway d1 route,
preserving the exact rendered image and text/question content. Keep request-body,
transport, model and provider identifiers distinct so an OpenRouter response cannot
be replayed as a Gateway measurement. Provider-reported usage and positive charges
win; otherwise use this route's retained published rates with reported tokens.
Keep unknown output/cache price components unknown. All calls must enter the same
USD 100 cumulative ledger and retain Langfuse usage/cost provenance.

At discovery time no `AI_GATEWAY_API_KEY`, Gateway alias key, `VERCEL_OIDC_TOKEN`
or `LIQUID_API_KEY` was configured in the process environment, `.env` or
`.env.remote-hosts`; `.env.local` did not exist. Only credential presence/names were
reported. The user was asked to configure `AI_GATEWAY_API_KEY` locally. At that discovery checkpoint no Gateway inference had been performed; the live results below supersede that status.

## Live pilot update

The user configured the Gateway key locally. L009 text pilot produced six d1 and
four Laya successes; both Laya aliases returned HTTP 422 on a compact-canonical
packet. Four Gateway d1 image requests then succeeded. Preserve the failed bodies
and their unresolved reservations; the cause of Laya's payload rejection is under
investigation and is not treated as a classification mistake. No model fallback
was configured. Gateway identities, raw responses, provider metadata and usage are
retained separately in the shared ledger. Langfuse has route-specific priced models
`vercel/convaiinnovations/laya`, `vercel/convaiinnovations/laya-free` and
`vercel/liquid/d1`.

L009 vision uses the exact 24 copied observations from the L006 focus freeze. An
independent audit compared all 432 requests: question text/scope, literal state JSON,
image coordinates and PNG data URLs match the corresponding PPLX input. Only the
provider transport/model changes. There are 428 distinct image URLs; image treatments
and model repeats are not independent document samples.

## L010 state serialization control

Hypothesis: serializing the complete compact state to a JSON string may avoid a
route-specific nested-state admission issue. All values round-trip exactly and
questions remain unchanged; L010 is a separately frozen experiment, not an
identical-body retry. It contains 216 records / 144 distinct bodies. The initial
12 transmissions produced six d1 and four Laya successes, plus one HTTP 422 for
each Laya alias on compact-canonical inputs. This rejects serialization alone as
a compatibility fix; the underlying failure remains under investigation. No
failed body, original response, or reservation was removed.
