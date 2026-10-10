# P003 Gateway failure contract audit

The archived d1 and Laya gate requests match the published request shapes; this
static audit found **no proven schema mismatch**. The actual failure causes
remain unresolved because raw error bodies were not retained and the sanitized
receipts contain no recognized error types or field locations. Laya's effective
provider context budget is a plausible cause of its HTTP422, requiring a
separately labeled protocol probe rather than a retry of the quality experiment.

Only root-authorized DEV request/report artifacts were read:
`pipeline-p003/gate-gateway-d1-512-r0` and
`pipeline-p003/gate-gateway-laya-text-r0`. Each made one attempted request,
returned no decision, preserved its USD0.30 reservation, and stopped through
the circuit breaker. A reservation is not a confirmed charge. No credentials
or private remote endpoints were accessed; this agent made no inference calls.

| Static observation | d1 | Laya |
| --- | --- | --- |
| HTTP status | 400 | 422 |
| Endpoint | `/v1/decisions` | `/typesafe/v1/systemone` |
| Exact model | `liquid/d1` | `convaiinnovations/laya` |
| State UTF8 bytes / characters | 3,802 / 3,801 | 3,794 / 3,793 |
| Instruction characters | 818 | 818 |
| Question | Named Choice, three string options | Named Choice, three string criteria |
| Actual pixels | RGB PNG8, 512×125, 39,474 bytes | None |
| Explicit routing | Default d1 route | Boundless only |
| Error type / field diagnostic | Empty / empty | Empty / empty |

The d1 body contains one user message, an `input_text` part, one base64 data-URL
`input_image` with high detail, and a named Choice question using the documented
value/description array. The image validates and decodes completely. The native
route documents this image/message form, named choices and errors with type/code
and param; provider failures may use a different error envelope. This supports
schema conformity, not serving success.
[Official Gateway Decisions contract](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions).

Laya already uses a **plain string state**, a dictionary of typed questions,
Choice criteria descriptions, and the declared Boundless-only provider option.
This agrees with Gateway's TypeSafe-compatible contract and the serving
provider's example. Changing a list state to a string cannot fix this archived
request: it was a string when transmitted.
[Official Gateway TypeSafe contract](https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe),
[Boundless System One documentation](https://inference.boundless.network/docs/system-one).

Boundless documents default Laya budgets of 512 tokens for English and 1,024
for multilingual, covering state/question/options/special tokens for each
question. Its criteria budget is 48 tokens per entry. Overlength input or
criteria returns HTTP422 without truncation; direct requests can set `max_len`
through 8,192. The archived gate specifies no `max_len`. Gateway's public catalog
advertises Laya context8,192, but that does not establish the upstream budget
chosen for this request. Gateway forwarding of this provider-native override
has not been verified. No character-to-token estimate or exact overlength
claim is made. [Serving-provider limits](https://inference.boundless.network/docs/system-one).

An unauthenticated public catalog refresh at 2026-10-10 20:30 UTC still lists d1
text/image context65,536 and Laya text context8,192. d1's image capability is
also described in Vercel's October9 announcement. Liquid's earlier October5
announcement described the Gateway route as text-only then; that older note
cannot establish current support. Catalog advertisement and a valid input
contract do not identify why this particular HTTP400 occurred.
[Public catalog](https://ai-gateway.vercel.sh/v1/models),
[October9 Gateway announcement](https://vercel.com/changelog/liquid-ai-d1-is-available-on-ai-gateway),
[October5 Liquid announcement](https://www.liquid.ai/blog/d1-decision-model).

Before another root-controlled protocol experiment, preserve bounded error
body size/hash and extract only known machine codes, field paths and fixed
reason categories. Boundless's documented numeric string code`422` is outside
the current categorical allowlist; an error message without a known path prefix
also disappears from diagnostics. Context-budget and criterion-length categories
could be recognized without retaining the message or reflected source values.
Past failures cannot be reclassified from their empty diagnostic fields.

Prespecify minimal plain-text controls with short Choice instructions first.
For d1, follow a successful text control with the same minimal text plus the
same validated image, isolating image routing. For Laya, compare explicitly
bounded evidence/rubrics only after establishing a successful minimal request;
test increased context only after documenting Gateway forwarding. These are
protocol probes with fresh tags and reservations, separate from extraction
quality runs. Keep failures, circuit stops, raw metering and known/unknown
charges visible; no automatic retry or silent omission is justified.

Public responses were retained in ignored
`pipeline-p003/catalog/gateway-contract-audit/` with URLs, UTC retrieval times,
byte counts and SHA256s. Its manifest SHA256 is
`e987bfa975b1b735c82f09c9beaba964ba40b5ea0f637d2ac20df8aeccaa626f`.
Snapshots include both Gateway contracts, Boundless's contract, both dated d1
announcements, and the refreshed public catalog. They are copied to main and
the worktree; request source text and base64 pixels were not printed.
