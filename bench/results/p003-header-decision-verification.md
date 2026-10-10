# P003 independent factorized header verification

The new `p003_header_decision` scorer credits only actually selected complete
header alternatives. Fixed historical generation tables and combined outputs
remain separate provenance. Valid selected tables on an incomplete page retain
primary credit, while the page remains an operational failure. All 16 pages,
53 tables and 2,333 cells remain in the DEV denominator.

Verification requires an independently approved outer code map plus separate
`pool`, `header` and `generation` code authorities through
`--incremental-trusted-code`. Embedded maps and frozen artifact digests do not
establish their own authority. Current pure decoders must match the freeze;
archived source is authenticated but never executed.

Before scoring, the adapter authenticates the v4 source-only pool, original
PDF/generation/proposal provenance, all 80 pool request bodies and eight PNGs,
and the exact selected menu inventory. It reconstructs actual insertion-order
wire bytes, not sorted archived JSON, and binds every native response to the
requested model, request hash, tag and unique ledger index. It checks the full
probability receipt, exact selected table bytes, explicit refusals and
abstentions, first-transport-error stop, all attempted-charge inventories,
selected/fixed/combined states, strict Markdown and report counts. No alternative
model fallback or inline retry receives credit.

The final source-frozen mock-v2 passed full independent report replay using the
external Git-anchored 33-file `header-decision-mock-v2.json` map: all 16 page
artifacts, four mechanically injected choices and four selected tables replayed.
Its 26 fixed historical tables receive no model-only credit. Missing mock ledger
measurements remain unknown; fresh full-pipeline rates remain undefined. This
mock validates the artifact and failure contract and is not a model quality or
cost result. The source pool and mock source/code were frozen before analysis.

Focused tests reject a sorted-archive hash substituted for actual wire bytes,
selection after transport stop, attempted no-question refusals, malformed raw
probabilities retaining selected-table credit, and historical tables leaking
into partial-page primary quality. Reporter/progress regression checks also pass.
