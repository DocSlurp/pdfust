# Frozen lower-level follow-up audit

This is a read-only audit of `basic-final`, `history-v2`, and `prompt-factors` on 2026-10-09. No credentials or hosted calls were used. Exact snapshot hashes, per-case transitions and independent projected-source collisions are retained in `followup-stats.json`; `analyze_followups.py` reproduces those analyses. The snapshots were complete for d1, PPLX and Luna. JeV stopped after one failed history request; its missing follow-up outcomes do not establish low quality.

The useful positive result is PPLX's response to explicit item IDs and to the resolved crop prompt. The runs do not show a general benefit from adding glyphs/operators/history or a native extraction win. They also expose a substantial recovery barrier: several arms intentionally omit the source evidence that distinguishes authored labels.

## History evidence is not one quality tier

There are 12 logical history cases, crossed with three correlated encodings: three description pairs × four variants. `multiline` has a consistent prior pattern and a tentative authored join label. `new_identifier` adds visible item 105 beside the second target line and has a stronger split label. `absent` and `singleline` remain ambiguous. Each category has nine page variants; these are three logical examples, not nine independent documents.

| Model / arm | Tentative multiline joins / 9 | Visible-ID splits / 9 | Ambiguous abstentions / 18 |
|---|---:|---:|---:|
| PPLX words | 9 | 8 | 0 |
| PPLX glyphs | 8 | 9 | 0 |
| PPLX operators | 8 | 9 | 0 |
| PPLX rolling | 7 | 9 | 0 |
| PPLX crop512 | 8 | 9 | 0 |
| d1 glyphs | 2 | 9 | 0 |
| d1 rolling | 1 | 9 | 2 |
| Luna glyphs | 9 | 0 | 0 |
| Luna minimal | 0 | 0 | 18 |

PPLX glyphs' 17/18 is eight tentative joins plus nine visible-ID splits. It joins all 18 ambiguous absent/singleline cases, so this score is not a safe relationship decision gate. Luna's rich arms mostly choose join throughout; d1 canonical chooses split throughout. Their perfect encoding consistency is largely a constant-choice effect.

The whole page is already in words/glyph evidence. `rolling` adds a compression of existing prior physical lines, not new information. Paired against glyphs, PPLX rolling changes only one successful multiline join into a split. d1 rolling gains one known outcome, loses two, and adds two correct ambiguous abstentions. Luna adds one ambiguous abstention. There is no measured incremental history-summary benefit.

PPLX's remaining glyph multiline miss is `Site inspection` / `weekend service hours` in array encoding. Rolling adds a miss for `Valve assembly` / `pressure-rated fittings` in positioned encoding. No attempt should label these conventional joins as certain table structure.

## Prompt comparisons use the same selected source pages

The prompt-factor preparer selected one shortest source encoding per identical full-page raster without reading targets. Comparisons below pair each follow-up with the initial result on that exact page and base arm. There are 16 known and eight ambiguous inputs per arm; encoding consistency is unmeasured in this one-encoding cohort.

| Model / factor | Known before → after | Known gains / losses | Ambiguous abstentions before → after |
|---|---:|---:|---:|
| PPLX crop512 resolved | 13 → 15 | 2 / 0 | 0 → 1 |
| PPLX vectors resolved | 12 → 12 | 3 / 3 | 0 → 3 |
| PPLX vectors both | 12 → 9 | 1 / 4 | 0 → 2 |
| PPLX crop512 singleton | 13 → 12 | 1 / 2 | 0 → 0 |
| PPLX vectors singleton | 12 → 11 | 2 / 3 | 0 → 0 |
| d1 minimal both | 9 → 9 | 2 / 2 | 0 → 2 |
| Luna vectors resolved | 8 → 3 | 3 / 8 | 0 → 7 |
| Luna vectors both | 8 → 6 | 5 / 7 | 0 → 6 |
| Luna vectors singleton | 8 → 9 | 1 / 0 | 0 → 0 |

PPLX crop512 resolved fixes Qty/Unit `34` / `KG` and `56` / `HR` and abstains on one unruled wrap. Its remaining known miss is Qty/Unit `12` / `EA`, which it joins. The gain is promising but tiny, exposed DEV evidence. Boundary labels depend on authored header conventions rather than independent producer truth.

More explicit alternatives often exchange accepted errors for abstentions and discard correct answers. Luna resolved vectors loses all eight previously correct known outcomes while gaining three different ones. Aggregate net scores hide this movement. Typed transport alone is mostly neutral or worse here. Singleton packaging is not uniformly better. Preserve moderate `words`, `glyphs`, `operators` and original `rolling` controls rather than comparing only the newest prompt.

## Identical evidence can carry conflicting document labels

An independent equality audit of each projected source observation found conflicting wrap labels in minimal, words, glyphs, canonical, operators and rolling: all 36 wrap pages representing 12 logical cases. Rule-free inputs cannot distinguish the enclosing rectangle, internal row divider and unruled variant because those features were deliberately omitted. The operator arm removes drawing operators and their count. Vector evidence has no such conflicts in this cohort; the crop arm supplies the missing pixels.

Keep the frozen primary authored score, but report these input-equivalence classes as arm-inaccessible evidence. Do not describe failure to recover a hidden divider as failed semantic comprehension. Three-observation batching can make identical regions receive different predictions because the surrounding independent observations differ; that is a packaging sensitivity, not recovered source information.

## Accounting findings and fixes

Prompt-factor manifest has 544 records but 512 distinct body hashes: 400 completed bodies cover 424 records, and 112 refused bodies cover 120 records. Reporting 400/544 mixes units. The runner/scorer delta `45bc5a4` separates bodies, records and refusals, stratifies history recoverability, and uses the manifest experiment in report titles. HTTP durations must be complete finite nonnegative observations before a complete API throughput rate is reported; valid zero remains measured and has no finite throughput quotient. Current retained snapshots had no missing fresh ledger durations.

A material runner bug was found: newly completed identities were not added to the in-loop completed set. Later identical aliases replayed and overwrote the existing result's fresh flag. Twelve prompt singleton rows were consequently reported as local replays despite their first transmission occurring in that freeze. Prior published prompt-factor cost/throughput summaries undercount fresh calls until repaired. Quality outcomes are unchanged. The fix retains the first completed body immediately. Root is preserving exact pre-repair result bytes and repairing only the twelve singleton identities proven by original ledger tag and absence from the explicit basic/history manifests; historical cross-freeze replays and the ledger remain unchanged. Repair provenance should remain in `accounting_audit_notes`.

## Three next experiments

1. **Matched source-packet and prompt controls.** Keep raw and lossless compact singleton packets for the same pages, exact task-specific prompt, typed transport, alternatives and model. Compare literal round-trip equality, request bytes, admission failures and paired choices. Only then vary batching. Accept a serialization claim only when all source values round-trip, every selected page is retained, and source-equivalent packaging preserves choices or reports every discordance. L004 as proposed changes prompt, transport, compression and batch grouping together; it establishes operational feasibility, not causal compression gain. L005 matched singleton controls address this confound.

2. **Identifier sensitivity without optimistic history gold.** Retain words/glyphs/operators/rolling and compact representations. Cross explicit row IDs present/absent with consistent/inconsistent prior wrapping, while holding target text and amount constant. Score explicit-ID splits separately; treat conventional joins as hypotheses and unknown cases as abstention controls. Include related and unrelated continuation text to test semantic association bias. Reject a proposed gate if it accepts all absent-history continuations or ignores visible new IDs. Freeze all levels, source-selected encodings and target definitions before requests; report paired source changes and encoding disagreements without removing inconvenient cases.

3. **Geometry accessibility and lexical counterfactuals.** Retain matched original vectors and crop512, plus geometry-hint and resolved-prompt variants. Include ruled joins, ruled splits and unruled controls, and swap description/header vocabulary while preserving source geometry. A deterministic hint on history-only pages is always unresolved because those PDFs contain no vector rules; that comparison tests an added constant abstention cue, not geometry recovery. Accept a routing claim only when decisive source geometry agrees with its independent control and abstention is preserved on inaccessible/ambiguous cases. Boundary header hypotheses should remain separately labeled; no full field/cell reconstruction claim follows from these two-chunk choices.

None of these controls is a fresh independent-document test. After choosing a frozen mechanism, inspect source-only real DEV failures with explicit source ownership and admission bounds; manually audit headers, identifiers, hidden/overprinted text and visibility before defining any new structural gold. Do not access the protected held-out silver cohort during this work.
