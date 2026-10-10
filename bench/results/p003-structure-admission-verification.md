# P003 independent structure-admission verification

The `p003_structure_admission` reporter replays every frozen retain/reject/unresolved answer and assembles only exact admitted source-owned tables. A page with malformed, failed, refused or unattempted questions predicts zero tables and keeps every source word unresolved. No baseline output receives quality credit. All 16 pages remain in the quality and failure denominator.

Use the existing reporter CLI with an independently authenticated run code map and a separate JSON map for the source evidence:

```text
--trusted-code RUN_CODE_MAP.json
--incremental-trusted-code SOURCE_MAPS.json
```

`SOURCE_MAPS.json` must contain exactly `pool` (the independently Git-authenticated admission pool helper map) and `source` (the original ordinal b773d57 map). Embedded maps are provenance and cannot authorize themselves.

The verifier authenticates original PDFs and source snapshots; regenerates the raw geometry, complete packets and source pixels through current authenticated helpers; compares all selected request objects and exact transmitted JSON bytes; checks each response's requested model, tag, unique ledger index and body hash; and replays strict raw native probabilities. It enforces distinct once-only attempts and admission stop after the first transport error. Malformed answers retain explicit parse failures and may be followed only by a different declared question.

It independently rebuilds the complete source-owned state, table output and Markdown for every page, including failures and no-candidate pages. Immutable archive hashes, source inventory, historical baseline copies, report counts and all-attempt accounting are checked. Missing or reserved accounting stays unknown. New API cost, preprocessing resources and admission resources remain separate from historical OCR/TATR acquisition. Full-pipeline rates are undefined; incremental valid-page and intended-page rates are computed from verified counts.

Validation includes real source-only authentication of all 16 pages and all 1,899 prospective bodies, plus receipt tests rejecting changed hashes/models/tags, invalid probabilities, replay credit, transport-stop violations and oversized-question attempts. A bounded offline fixture exercises retained malformed/transport failures without inference, labels fake accounting unknown and makes no quality claim.
