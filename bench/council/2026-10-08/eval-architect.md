# Builder: Evaluation Architect

Date: 2026-10-08. Read-only council proposal; no dataset creation, inference, GPU use, credential access, tracked-file edits, or publication. This is temporary exploration, not an adopted evaluation contract.

## Decision and present evidence

Decide whether a bounded relationship model improves **complete source-grounded table and field extraction**, at acceptable total CPU/API cost and latency, over the strongest implemented native pipeline. Choose the cheapest method that reaches the required quality; do not select by confidence or score formatting.

The supplied current leaders are Luna 31/36 and Perplexity 30/36, with Jev 24/36. All 96 repeatedly inspected observations, their existing calibration/test names, eight region controls, and every derivative routing result are **development data only**. These observations cannot confirm a new claim. A case's old `test` field does not make it held out again.

Repository evidence changes the task boundary:

- `bench/decision_cases.py` uses closely related authored templates, lexical unit clues, and some labels that rely on author intent. Such labels cannot establish visible reconstruction quality.
- `bench/decision_assembly.py` conserves words and validates isolated relations, but expressly does not reconstruct cells, a matrix, or Markdown. Its table edge is rows of word IDs, not a complete cell ownership map.
- `bench/decision_evidence.py` supplies literal candidate spans without gold fields, a useful starting seam.
- `bench/decision_routing.py` picks by calibration accuracy then HTTP latency; that is development analysis, not an independent quality result, and currently leaves indeterminate outcomes unscored.
- `bench/results/decision-findings.md` explicitly distinguishes gate success from dense-table recovery and illustrative geometry rules from the production extractor.
- Native APIs already expose `get_layout`, `find_tables`, `get_drawings`, structured text, and rendering. A model must beat this evidence, not just the earlier illustrative rule.

Platform: repository Python/Rust scripts installed; hosted runner implemented. Authentication unexamined and unconfirmed. Current proposal authorizes no data transmission or paid execution. Supplied campaign accounting is $2.04695453 reported plus $0.60 reserved against $15, leaving at most $12.35304547 available before other costs; later execution must reconcile the real ledger, not copy this estimate as authority.

## A useful quality contract

Evaluation unit is one complete bounded page-region extraction, including competing structures and surrounding decoys. A relation decision is a diagnostic unit. Independent unit for uncertainty is producer/template family, not word, relation, crop, or generated seed.

The output is a canonical semantic graph:

1. Immutable source words with snapshot-local IDs, original literal text, boxes, and source order.
2. Tables with ordered row/column slots, cells owning ordered source IDs, explicit empty cells, and rectangular spans. Covered merged slots reference an anchor rather than pretend to be independent text.
3. Directed header-to-cell scope, including hierarchical headers; directed wrap-to-cell membership; label-to-value field edges with units preserved literally.
4. Prose/unassigned source words retained alongside the graph. An undecidable relation remains unresolved; a negative relation explicitly rejects a candidate.

Allow equivalent linearizations of the same canonical graph. Do not compare Markdown formatting or guessed natural-language paraphrases. Normalization rules are frozen and narrow: normalize insignificant whitespace only, preserve digits, signs, punctuation, units, source-ID membership and span ownership. Public-library changes are out of scope; implement this as a benchmark-only assembler first.

| Claim/risk | Deterministic metric | Decision rule |
| --- | --- | --- |
| Correct cells | Exact cell source-ID ownership, anchor/span correctness, row/column order; cell precision/recall and exact complete-region match | Primary decision metric is exact complete-region match, domain macro average. Report cell metrics as diagnosis, not substitute success. |
| Correct headers | Exact directed header scope to cells, including nested paths | Wrong header scope makes the complete region wrong even when values are correct. |
| Correct fields | Exact label/value edges and complete record match | Unit compatibility alone is insufficient; distractor values and repeated labels must be included. |
| Correct continuation | Exact continuation membership/order in a cell or field | Wrongly joining adjacent records fails the complete region. |
| Useful negatives | False table, false join, false header, wrong value assignment rates | Always-no and empty-output baselines must fail positive recovery; report both rates. |
| Unidentifiable evidence | Correct unresolved relation count; hard assertions on genuinely unidentifiable cases | Never turn generator-private intent into public ground truth. Incorrect assertions fail the region. |
| Source conservation | Exact input/output word-ID multiset and literal text; one cell owner per owned word; no cross-snapshot reference | Zero violations; one violation blocks adoption regardless of mean quality. Header references may share words as references, not as duplicate content owners. |
| Full pipeline ability | Native candidate recall, oracle-selected candidate ceiling, achieved exact regions | Missing gold candidates are extraction failures. Never drop them from model denominators. |
| Cost/latency | PDF open, interpretation, candidate enumeration, raster/crop, encode, request, validate, assemble totals; median/p95, peak RSS, billed USD | Compare cold document and reused-document runs separately. Report failures, retries, cache hits and deadlines. |

Three equal-weight domains: financial, invoice, scientific. Also report producer-level distributions and challenge slices. An improvement in invoices cannot mask degradation in scientific headers. Missing outputs, invalid schemas, timeouts, and rejected contradictory assemblies count as failed regions. Coverage is a secondary diagnostic, not an excuse to score only accepted records.

Provisional selection contract to register before new confirmation: at least +5 percentage points domain-macro exact-region accuracy versus the strongest native baseline; no negative domain delta; zero source-conservation violations; and no increase in unsupported hard assertions on unidentifiable controls. Require a producer-cluster paired interval whose lower bound exceeds zero for a confirmatory improvement claim. These are project acceptance choices, not proven statistical power. A small confirmation may be inconclusive. Report exact paired win/loss/tie counts and intervals; do not promote an inconclusive tiny result to release evidence. Keep at most one selected hybrid and one frozen ablation plus native baseline for final confirmation, reducing winner's curse and spend.

## Fresh evidence that vision can legitimately add

Build a **visible specification → renderer → PDF → native extraction/render → output** benchmark. The generator emits a semantic graph from an explicit visible layout design, but the graph is scorer-only. Humans must be able to read that graph from the document without generator notes. If they cannot, downgrade that relation to unidentifiable before freezing labels.

Construct matched pairs with identical literal words and positioned baselines but different visible grouping cues:

- Financial: identical balance/revenue/expense values under two competing stacked header groups. Change only visible ruling breaks and spanning bands so the group scopes differ. Include parentheses, signed amounts and an adjacent unrelated note.
- Invoice: identical descriptions, quantities and prices with a continuation line between neighboring items. Move the visible row separator or enclosing cell boundary, retaining text positions, so one version visibly joins the description and another begins a distinct record. Include SKU strings and notes with monetary values.
- Scientific: identical condition labels and repeated measurement values beneath hierarchical treatment/unit headers. Change which columns a top-level bracket or group border spans; include footnotes, missing values and uncertainty notation.

Use partial borders, thin strokes, lightly shaded cell backgrounds, bold/italic scope cues, and header bands as controlled features. Native baseline gets **the same underlying evidence**: source words, span font size/style/color where accessible, vector commands, stroke widths/colors, fill regions, and derived intersection/containment features. A model-only screenshot gain over words-only is a modality result; a gain over native geometry+vector+style is the actual engineering result. For inaccessible native styles, disclose the evidence gap rather than claim the images beat equivalent information.

Important fairness detail: `get_drawings()` is interpreted paint geometry, not pixel visibility, clipping structure, or text paint. Clean synthetic grouping tests should initially avoid ambiguous clip/overpaint effects. Later add clipping/occlusion as a separately named evidence-gap slice, with human-visible labels and image evidence openly richer than the native API.

Counterbalance cues across labels: a shaded box is sometimes prose; rules sometimes isolate notes; bold is sometimes emphasis; a nearby number sometimes belongs to another record. Do not encode `continued`, `record`, `true`, task names, filenames, model answers, expected relation IDs or semantic role metadata in PDF contents/properties or crops. No gold-colored overlay or candidate-validity rectangle. Any candidate overlay uses neutral colors and identical rendering rules across valid and invalid candidates; include a no-overlay control.

Use realistic but task-independent lexical distributions within all domains. Randomize content stream order separately from display order. Repeated values make literal string matching insufficient; randomize snapshot IDs. Include 0/90/180/270 rotations, ragged labels, clipped region context, blank cells, merged headers, multiple neighboring tables and multi-line cells. These are features of independent base documents, not new independent samples obtained by rotating one page.

Meaningful negative controls: numeric two-column prose, side-by-side key/value lists, aligned lab notes, invoice legal text, standalone captions, summaries outside tables, nested note boxes, incompatible competing ownership, and a candidate crossing two genuine tables. Meaningful unknown controls: remove the only distinguishing separator/style or crop away the governing header, leaving the competing graphs observationally identical. Annotate **relation-local** unknowns: do not discard an otherwise extractable table because one header scope is unresolved.

## Human oracle and independent producers

Two reviewers independently label from a legible reference raster and PDF display, never model output, authored gold, generator code or filenames. They record cells/edges and observable supporting cues. Third adjudication resolves disagreement; persistent ambiguity becomes an allowed set or explicit unresolved relation. Agreement statistics and exclusions are retained. Model judges do not establish gold.

Generator gold is accepted only after human visibility checks. Map authored text instances to extracted word IDs using coordinates/source tracking, with deterministic ambiguity detection; fail fixtures whose mapping is uncertain. Duplicate text requires instance ownership, not string equality. Check native extraction against authored literal text separately so missing text is diagnosed, never silently excluded from end-to-end quality.

Development producer groups are separate renderer/template implementations (for example direct PDF operators, generated reports, invoice layouts, and scientific typesetting families), not just random seeds in `decision_cases._spec`. Confirmation producer groups must be entirely new layout/template families, with different line-break, border, typeface and table-generation conventions. Deduplicate by template ancestry, normalized geometry/style signature and content fingerprint. Put all siblings, lexical rewrites, crops and modality variants in one split.

Initial sizes are planning targets, not a generated dataset: approximately 108 development regions balanced 36/domain, followed by 108 confirmation regions from 18 new producer families, six/domain. Within each domain balance answerable positives, contradicted candidates and genuinely unidentifiable relations, while retaining mixed end-to-end tasks on a page. Prefer fewer independent human-readable base documents over hundreds of correlated relation questions. Include separately labeled licensed real-producer documents if available; synthetic-only confirmation supports only synthetic-layout claims. If fewer independent producers are available, report a feasibility result and leave real-world accuracy unsupported.

## Paired experiment matrix

Same extracted snapshot, frozen candidate set, region and output schema for each paired arm. Pixel changes only where specified. Frozen source-ID scoring is common to all arms.

| Arm | Evidence/behavior | What it resolves |
| --- | --- | --- |
| N0 | Current public native bordered/text table extraction + field/header spatial rules, explicitly configured | Actual useful library baseline. |
| N1 | Native words + vectors + styles; boundary/containment/grouping rules; deterministic unit compatibility | Whether richer evidence fixes failures without inference. |
| O | Gold selector over the frozen N1 candidate set, scorer side only | Candidate ceiling and need for candidate-generation work. Never send gold to a model. |
| T | Luna or Perplexity; literal source spans + geometry/vector/style-derived facts; complete same-region relation bundle | Small-model semantic improvement without images. Jev is a cheap development comparator, not obligatory final arm. |
| V128/V256 | Same T text bundle plus tiny 128/256-pixel longest-side region raster | Whether cheaply retained grouping is sufficient. Raster-only readability is not required because text remains literal. |
| VB | Same dimensions/text + explicitly specified CPU Gaussian blur in raster pixels | Whether layout survives loss of fine glyph detail; blur is an intervention, not presumed cheapness. |
| V512 | Same text + legible 512-pixel crop | Whether tiny failures are insufficient visual evidence. Use only if V128/V256 differs meaningfully. |
| H | Frozen native pipeline, invoke selected T/V arm only for unresolved/conflicting candidate graphs | Product cost and whole-task quality, including router mistakes and missed regions. |

Do not run the entire cross product on every case. Development successive elimination: native evidence ceiling first, text vs tiny image on discriminating pairs second, one blur-size contrast third. Evaluate request formats on repeated identical development inputs to measure instability; use several questions about one region rather than unrelated cases in one request. Record provider model/version, output modality support, image encoding, prompt hash, exact data projection, preprocessing and transport settings. A decision endpoint may be text-only: an unavailable multimodal arm is unsupported, not silently replaced with another model.

Render a canonical high-resolution page once per document snapshot, then crop/downsample/blur deterministically CPU-only. Cache key includes PDF hash, snapshot/generation, page, display-coordinate crop, render settings, dimensions, blur parameters and codec. Measure cold render, warm raster reuse, encoded-crop reuse and hosted response replay separately. Replaying the exact response has no inference latency and must never inflate service throughput. Image dimensions/file bytes are not provider token cost; measure actual billing and include failed requests. PNG versus JPEG is a small development compression ablation only when pixel content/billing warrant it.

No confidence-driven router by default. Route by observable unresolved structure: competing header scopes, row boundaries crossing multiline spans, unassigned values, candidate contradictions or missing vector enclosure. This keeps ability primary. Confidence distributions can be retained for diagnosis, not quality selection or automatic correctness claims.

## Strict confirmation isolation: exact engineering protocol

1. Mark every current case/output and every previously viewed future case as DEV in a durable adopted contract. Old manifests stay intact; a classification registry makes the status explicit.
2. Create and review development-only cases/scorers. Validate scorers with deliberately wrong cell ownership, duplicate IDs, wrong span anchors, wrong header scope, unsupported assignments, unidentifiable assertions and equivalent valid graphs. Freeze normalization and graph matching before confirmation exists.
3. Tune N1, candidate generator, assembler, prompts, image sizes, routing and model choice **using DEV only**. Select one hybrid plus one prespecified modality ablation. Record exact code commit, lockfile, model IDs, prompt/projection hashes, candidate cap, router, crop/blur settings, timeout/retry policy, scorer hash, comparison endpoints and acceptance rules.
4. Freeze the candidate bundle as a local immutable artifact. Its inference code may read PDF/source evidence, but has no ability to read gold, generator secrets, split metadata, scorer outputs or confirmation trace files.
5. Only after freeze, a separate human custodian or isolated evaluation service authors/adjudicates new producer cases and gold, records document/gold/manifest digests and ancestry, and stores them outside the tuning workspace. **Do not create them during this council task.** The tuning agent must not inspect them or their per-case labels.
6. Run the immutable candidate inside a separate process/container identity: read-only inputs mounted for inference; no gold mount; no tuning repo write mount; restricted result sink. The scoring process has gold and predictions but no path back to change candidates. The custodian runs all frozen arms once. API access and spend require separate user authorization and ledger reservation under the existing cap.
7. Return aggregate domain/producer paired wins/losses/ties, full failure denominator, conservation gates and total cost/latency. Prevent human/agent tuning through per-case screenshots, trace mining, case IDs or scorer feedback during confirmation. The evaluator may internally inspect failures to certify scoring without coaching the tuning team.
8. If the metric or parser is wrong, quarantine the run; document the defect. Any changes that depend on confirmation evidence retire that whole confirmation set to DEV and require an entirely new producer split after the new freeze. Do not patch a prompt and rerun on the same set claiming confirmation.
9. After the adoption decision is fixed, the custodian may release cases for diagnosis; they are then DEV and cannot confirm the resulting repairs. Record exposure and artifact lineage explicitly.

One Unix user and a shared repo cannot provide this isolation by `chmod` or an ignored directory. If there is no separate custodian/service/identity, state that strict confirmation is unavailable, stop at development evidence, and do not claim a clean held-out result. Aggregate feedback repeatedly used to tune also contaminates confirmation, even if cases were never opened.

Before actual confirmation, promote the reviewed plan to the project's existing durable decision record (`bench/DECISION_MODELS.md` or a reviewed linked plan); keep raw PDFs, gold, outputs and ledgers in protected/ignored artifacts with digest/retention metadata. This scratch proposal alone cannot authorize a release decision.

## First three tests and what each can reject

**1. Native evidence + oracle ceiling, no model spend.** On development-only human-adjudicated visible-layout pairs, compare N0/N1 and oracle candidate selection. Audit one example of each domain and failure mechanism. If native richer evidence solves the cells/headers, reject paying a model for those cases. If gold graphs are missing from candidates, reject relationship-model tuning as the current bottleneck and improve candidate enumeration. If reviewers cannot agree from pixels, reject those labels as known ground truth. This is the highest-information first test.

**2. Paired literal text/native facts versus tiny visual evidence.** Run the selected strong text model(s) on a small development set where visible separators actually distinguish identical words/geometry. Compare T, V256 and N1; exact-region graphs are the endpoint. Fix candidates and change only image evidence. If V256 adds no complete-region wins over N1/T, reject a screenshot path for this scope. If images help only when N1 lacks accessible paint evidence, label the gain correctly and decide whether exposing that native evidence is cheaper. Reject any result whose graph assembler cannot turn relation correctness into records.

**3. One practical hybrid with image fidelity/cache contrast.** On unresolved development regions, compare V256 versus one blurred V256 or V128 arm; include deterministic same-region bundling and measured cold/warm reuse. Freeze the better quality-preserving setting and compare H to always-text and native complete outputs. Reject tiny/blurred crops if even one essential grouping cue systematically disappears. Reject caching as an inference-quality argument; it only helps raster/transport costs. Reject the hybrid if the router misses recoverable regions or introduces wrong headers/values despite better conditional model accuracy.

## Alternatives considered and rejected

- More provider shopping on the old 96: inexpensive but cannot establish correct cells or independent ability; current strong models are enough to test whether the task/evidence architecture works.
- Confidence/ECE-first optimization: these can reward abstaining on nearly everything and do not establish useful extraction. Retain diagnostics separately.
- Free-text screenshot-to-Markdown as primary output: permits silent omissions, duplicate text, hallucinated headers and untraceable value ownership. Use source-grounded graphs; optional generated Markdown is scored after deterministic materialization.
- Always screenshot every page: incurs rendering, encoding and image-token costs even when native vectors supply exact structure. Prefer region-specific development evidence, then freeze a measured router.
- Hidden author-intent labels and random page-seed holdouts: the former lacks an observable target; the latter shares generator/producer conventions and understates generalization risk.
- Hundreds of trivial synthetic cases: numerical sample size does not create independent producers or realistic header scope problems.
- Simple possession of a protected directory in the same agent workspace: does not enforce held-out separation. Require a real custodian boundary or leave confirmation unsupported.

Recommended next route: review this contract, construct development data and validate the graph scorer, then run native/oracle diagnostics. No new confirmation cases should be created or opened until the candidate and scorer are frozen. No runtime model default is proposed.
