# Matched Claude 5.5 baselines

This opt-in baseline compares Opus 5.5, Sonnet 5.5 and Haiku 5.5 with the existing
PPLX/Luna expanded row/extent selector on reviewed DEV28: 16 authored tables,
eight prose controls and four explicitly unscored ambiguous pages. It measures
candidate selection, not unrestricted PDF extraction or natural-document
performance. The protected heldout corpus and TRAINING derivatives are excluded.

The parent frozen menu is `union-semantic-image512-extent-v1`, manifest SHA256
`a705a3cae9a298bcda489f926c0e699d2ae9ca76a13c27c4776043e424871935`.
The adapter preserves original source text, image blocks, semantic instructions
and candidate criteria. Chat transport uses a strict `answers.q0.choice` schema;
no invented confidence or answerability value is scored. Every body is frozen and
verified against its parent before private scorer references are opened.

All three models use explicit **medium** effort and a 4,096-token output cap.
There is no temperature override, forced tool call or assistant prefill. Medium
is Opus/Haiku's documented default; Sonnet's default is high, so this is explicitly
a medium-effort configuration rather than a claim about its maximum quality.
Models receive one page per request. Provider fallbacks are disabled, supported
parameters are required, and maximum provider prices are $4/M input and $20/M
output. Served model/provider, actual usage and response hashes are retained.

Verified 2026-10-09 against the [OpenRouter model catalog](https://openrouter.ai/api/v1/models)
and [Claude 5.5 migration guide](https://openrouter.ai/docs/cookbook/evaluate-and-optimize/model-migrations/claude-5-5).
[Anthropic announced Haiku 5.5 on October 7](https://www.anthropic.com/claude-haiku-5-5).

| Model ID | Input USD/M tokens | Output USD/M tokens |
| --- | ---: | ---: |
| anthropic/claude-opus-5.5 | 4 | 20 |
| anthropic/claude-sonnet-5.5 | 2 | 10 |
| anthropic/claude-haiku-5.5 | 0.10 | 0.50 |

These are standard catalog rates; Haiku has a higher tier above 100,000 prompt
tokens. Positive provider-reported charges take precedence. Missing/zero charges
use applicable retained pricing and observed tokens; missing components remain
unknown. Provider cache counters are retained when available, with no inference
of cache hits from local replay. All three model definitions/prices were synced
to Langfuse without conflicts.

The 84-call wave has a persistent $5 admission cap, including a $1.25 reservation
before each new transmission. The original cumulative $15 user cap remains
unchanged; conservative accounting before this run was $6.3056201568. The internal
campaign ceiling increased from $8 to $10 for this newly requested work. No ledger
history is reset. A failed model stops without an automatic retry; missing results
remain explicit. Before transmission, a conservative encoded-byte price estimate
plus the full output cap must fit the reservation. Local preparation CPU time and
peak RSS are separate from provider HTTP latency; remote CPU/RAM are unmeasured.

Use `python -m bench.anthropic_baseline --help` for offline preparation and explicit
`--run-hosted` execution. Raw frozen bodies, responses, usage and source assets stay
under ignored `bench/results/pdf-master-artifacts/decisions/anthropic55-baseline-v1/`.
Only code, tests and compact results are committed.
