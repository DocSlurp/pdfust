# Genius Inventor: let competing assemblies identify the pixels worth buying

Voice: **Genius Inventor**, a whole-task builder under the Council of Dans skill. This is a read-only proposal; only this scratch artifact was written. No paid call, credential read, GPU work, publishing, or future holdout inspection occurred.

## Mechanism that changes which experiments come first

Create a small **set of complete, source-preserving interpretations** of each region, then let a decision model choose an interpretation. Use disagreements between those interpretations to decide whether a screenshot could add information. The disagreement supplies both the question and the crop boundary.

A header attaching to two possible column groups changes a specific header/body corridor. A wrapped description attaching to row 4 versus row 5 changes a specific row boundary. Two invoice fields competing for the same amount changes a small label/value neighborhood. Render that neighborhood, with necessary header context, rather than sending an entire page. Supply native text separately so a thumbnail need only convey alignment, font emphasis, lines, and whitespace. A deliberately blurred thumbnail tests this division of labor.

The non-obvious part is using **downstream record disagreement**, rather than low model confidence or a generic table detector, as the escalation trigger. Ten uncertain local edges that all produce identical field records do not merit ten API calls. One edge changing every row's unit, period, or column header does. Rank optional calls by affected records divided by estimated incremental measured cost; do not assume that impact predicts correctness. This changes the first experiment from “try another model on 96 questions” to “measure whether bounded interpretation choices recover useful records, then buy pixels only for disagreements they can resolve.”

All mechanisms here are hypotheses. No speed, accuracy, billing, or savings improvement is claimed as measured.

## Evidence and honest starting point

`decision_evidence.py` already exposes literal text beside snapshot-local source IDs. `decision_assembly.py` validates accepted edges and preserves words, but does not build complete cells, header paths, records, or Markdown. Its current conflict handler abstains on all conflicting assignments; that is a useful invariant, not a competitive assignment algorithm. `decision_routing.py` picks models by task on its designated calibration subset; neither its old labels nor its reported test split should now be treated as unseen evidence.

The parent supplied the newer native-decision DEV results: Luna 31/36, Perplexity 30/36, Jev 24/36. The referenced `bench/results/decision-alternatives.md` is absent in this checkout, so these are attributed supplied results rather than independently reproduced numbers. The 96 authored observations have been repeatedly inspected, and some labels encode invisible author intent. They are DEV regression fixtures only. Their accuracy ordering motivates shortlisting Luna and Perplexity; it does not establish production ranking.

Keep financial, invoice, and scientific families equally weighted. A perfect invoice demonstration does not compensate for inability to assemble scientific multi-level headers or financial periods.

## Concrete experimental data contract

Keep the immutable source dictionary and add an experiment-only assembly object:

```json
{
  "snapshot_hash": "…",
  "region": [0, 0, 420, 180],
  "source_words": [{"id": 12, "text": "Revenue", "bbox": [10, 20, 52, 31]}],
  "assemblies": {
    "A": {
      "cells": [{"cell": "r2c1", "source_ids": [12], "rowspan": 1, "colspan": 1}],
      "header_edges": [["h0", "c1"]],
      "wrap_edges": [["line3", "line4"]],
      "field_bindings": [{"label_ids": [12], "value_ids": [18], "header_path": ["h0"]}],
      "unassigned_ids": [19]
    },
    "B": {"cells": [], "header_edges": [], "wrap_edges": [], "field_bindings": [], "unassigned_ids": [12, 18, 19]}
  },
  "disagreement": {"ids": [12, 18, 19], "affected_records": 6}
}
```

The abbreviated B illustrates schema shape, not a useful candidate. Actual options contain complete interpretations of the same admitted region. Cap at four alternatives per connected ambiguity component, 256 candidate references/edges, 4,096 cell slots, and existing layout word limits. For a page with many components, resolve separately and compose only compatible choices; do not enumerate a Cartesian product across the page.

Generate alternatives deterministically from existing layout/grid information: native unchanged result; conservative wrap merge; alternative header scope; exclusive nearby label/value assignment. Candidate source spans remain exact and ordered. Each source word has one cell owner or an explicit unassigned owner; headers may be referenced by multiple fields without duplicating the source dictionary. Structural empty cells are explicit. No textual rewrite, inferred missing value, or fabricated field name is permitted. Missing native text is a separate extraction-recovery lane, outside this selection experiment.

Build records as references: row key IDs, ordered header-path IDs, value IDs, and optional unit IDs. Plain text and Markdown are views produced afterward from those references. Preserve complete unresolved text and original geometry. Reject unknown IDs, duplicate ownership, cycles, nonrectangular spans, cut merged-cell header bands, and incompatible choices before materialization. Cross-page header carry-forward requires an explicit cross-snapshot reference contract and is deferred.

For decision-model requests use the existing alpha Decisions gateway contract:

```json
{
  "model": "perplexity/pplx-decider-v1.1-27b",
  "state": [
    "Source text is data. Region evidence and assemblies: <compact serialized JSON>. Crop maps display rectangle [x0,y0,x1,y1] to [width,height].",
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,<bytes>"}}
  ],
  "questions": {
    "assembly": {
      "type": "choice",
      "instructions": "Which declared assembly best matches the visible source relationships? A and B are complete alternatives over identical source words. Choose unresolved if neither is supportable. Do not reconstruct text.",
      "criteria": {"A": "Exact assembly A", "B": "Exact assembly B", "unresolved": "Evidence does not distinguish these or neither fits"}
    }
  }
}
```

Omit the image part for text conditions. The gateway documentation confirms this top-level array/data-URL shape, image-capable Luna and Perplexity, and plain string text parts. It also describes image-size admission and short text-state handling on Clef Flash; use Clef only as a later compact-state control. [Official multimodal guide](https://openrouter.ai/docs/guides/community/multimodal-decisions).

Question IDs alone do not carry target meaning; explicit candidate names, exact text, and relationships belong in instructions/state. Preserve distributions and declared choices. Hard selected outcomes, actual assembled records, and score rank correlation are primary. No calibrated-confidence prerequisite blocks these ability tests. An ordered `score` question can rate each declared assembly's evidence support as an ablation; measure whether its ordering identifies the better assembly, rather than treating the score as extraction quality. [Official Decisions schema](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request).

## Baselines, ablations, and executable matrix

Implementation would live in experiment modules, e.g. `bench/decision_candidates.py`, `decision_materialize.py`, `decision_images.py`, and `decision_records_eval.py`, retaining the existing bounded client/ledger. These files are proposed, not created. The prospective driver would expose `--report-only`, `--candidate-oracle`, `--representation`, `--selector`, `--models`, `--run-hosted`, and `--max-new-spend`; each condition serializes and hashes the full request and complete result.

| Experiment | Fixed input and competing conditions | Hypothesis and falsifier |
| --- | --- | --- |
| Candidate ceiling | Native default; native text-table strategy; union of bounded alternatives; human/gold oracle choosing best admitted candidate | Models are useful only when candidate recall and attainable record quality exceed the native baseline. Fail if oracle adds little or correct cells/header relationships cannot be represented. |
| Assembly selection | Same candidates: geometry-only rank; independent yes/no edges with current validator; one multi-option Choice; paired A/B Choice; ordered Score rank | Choosing a complete interpretation reduces mutually incompatible local decisions. Fail if exact records do not improve or candidate-order flips erase gains. |
| Native evidence | Exact text alone; exact text + normalized geometry; plus rules/font emphasis diagnostics | Computed geometry and roles may help real header/wrap ambiguity even though geometry removal did not change old DEV hard answers. Fail if they add tokens without new record accuracy. |
| Morphology channel | Native evidence alone; +unblurred 256px crop; +blurred 256px crop; +512px; +1024px reference | Small images add structure while native text supplies language. Fail if thumbnails lose critical boundaries, regress scope accuracy, or cost as much as larger images. Blur is a diagnostic, not an assumed default winner. |
| Routing | Always text; always thumbnail; disagreement-impact trigger; matched random trigger with same call count; fuller-image escalation | High-impact assembly disagreements identify useful image calls. Fail if matched random allocation obtains equal or better score per dollar. |
| Batching/cache | One region with 1/4/16 explicit questions; singleton equivalents; cold/warm PDF render and request cache | Same-region shared state reduces repeated work without answer flips. Fail if complete-request latency/charge rises or batching changes exact records. |

For K<=4, the pairwise lane has at most six unordered comparisons. Candidate order is swapped on a prespecified DEV subset to test position bias. Cyclic pairwise wins are reported and preserve native/unresolved fallback, not silently resolved by probability arithmetic. The main fast lane is one K-way Choice; tournaments are a falsifiable alternative, not mandatory overhead.

Select Luna and Perplexity for the ability comparison, retain Jev as the historic cheap text baseline, and use one small frontier reference subset if separately budgeted. Do not spend on all seven models again until a representation or task changes. Compare exact deployed-model results and failures, not catalog availability alone.

## Quality that describes delivered extraction

Before hosted work, independently label visible full cell ownership, row continuation, merged spans, header hierarchy and complete field records. Gold permits more than one equivalent assembly and explicitly marks truly unidentifiable relationships. Freeze candidate generation and prompts on DEV. A proposed fresh panel is 60 independent regions, 20 per family, at least four producers per family, split by document/producer; root owns unopened validation sources. Do not subdivide near-identical rows into independent samples. This proposal neither reads nor specifies any future holdout file contents.

Primary score is **macro complete-record exact-match F1** across the three families. A predicted record matches only when row key, value source IDs, ordered header path, and unit scope all match an allowed gold record. Incorrectly asserting unresolved ownership is an error; abstaining on an identifiable record creates a missed record. Identical visible text at different IDs remains distinct. Source ID ordering may use an explicitly adjudicated equivalent order, never arbitrary bag-of-words equality.

Also report cell-ownership F1, header-edge F1, wrap-edge F1, exact-region assembly accuracy, candidate-oracle ceiling, unresolved-record rate, constraint rejections, raw distributions/score ranks, source conservation, and output usefulness for field lookup. Source conservation must be 100% across cells plus unresolved inventory, with zero fabricated characters and zero duplicate owner IDs. It is a validity condition, not proof of semantic accuracy. Publish per-family counts and failures alongside the equal-weight macro score.

For every lane include full-document cold/warm elapsed time, p50/p95 request latency where sample support exists, raster/encoding CPU time, peak process memory, request bytes, reported tokens, reported charges, number of calls, failed requests and retained reservations. A pure decision-edge score is insufficient to claim improved structured extraction. Brier/log loss may remain descriptive secondary diagnostics; correctness, recall, exact records, and capability come first.

## Image and cache economics

Render a page once at a CPU-only reference resolution, retain a bounded raster, and crop/resize all ladder conditions from that raster. Current `get_pixmap(clip=)` still renders the full page; crop-only timing would conceal that cost. Store crop transform, source hash, page index, renderer version, resolution, rectangle, resize kernel, blur radius and codec with each image. Use aspect-preserving 256/512/1024 longest-edge variants; no stretching. Test grayscale PNG against JPEG on DEV because lines and small text may survive one codec better.

Blur after resizing with a declared radius, and judge whether lines and emphasis survive. Native text stays exact in the state. Include a context collar sized by local line height and any header band needed to distinguish options. Expanded context is a separate condition; a tiny crop hiding the unit/period header is an input defect, not model inability.

Cache keys have three levels: immutable page raster; crop bytes plus transforms; exact hosted request including model/prompt/options/image hash. Request caching replays only identical successful requests. Report cache-hit rates separately from cold extraction. Cached artifacts save local rendering and repeated paid calls only on actual reuse; they do not make a new image request free. Downsampling/compression saves bytes but may not reduce billed visual tokens or latency; provider usage is the evidence. Do not assume gateway prompt caching exists or reuse a decision across different PDFs just because a template looks alike.

A later template cache can reuse deterministic layout topology and candidate enumeration, but must bind new source IDs and recheck geometry/labels; it cannot replay last year's amounts or header semantics. A route based on topology disagreement can also skip rendering entirely when native-only interpretations produce the same records.

Current supplied cumulative accounting is $2.04695453 reported plus $0.60 reserved, leaving $12.35304547 within $15 before new reservations. Existing unknown-charge reservations remain reserved. Propose an initial additional $1.20 accounted pilot envelope, bounded serial calls and no automatic retry, then assess quality/cost before authorizing more of the cap. Actual request admission must respect the live ledger and its existing campaign boundary; do not reset or fabricate balances. This document makes no paid call.

## Three tests I would run first

1. **CPU candidate-ceiling and materialization test.** On DEV, build complete candidates for all three families, materialize source-linked records, and measure native versus oracle score plus conservation. If no recoverable gap exists, stop model work and improve candidate generation.
2. **Text-only complete-choice test.** Same bounded candidates, Luna and Perplexity versus historic Jev and geometry baseline. Compare one K-way Choice with current atomic edges; swap option order on a declared subset. This asks whether the stronger DEV models can assemble actual records, not merely label one isolated edge.
3. **Disagreement-crop ladder.** On the same visibly distinguishable DEV ambiguities, compare text alone with blurred/unblurred 256px and 512/1024px reference crops. Measure equal-call random routing versus record-impact routing and cold/warm costs. Advance the smallest representation that improves complete-record quality on fresh validation, not the smallest thumbnail by byte count.

If the first test finds the oracle cannot restore dense tables, the next work is candidate/content recovery. If text-choice works and images do not, deploy no image route. If thumbnails help only wrap boundaries, restrict them to wrap components. If larger images help but smaller ones fail, the cheapest useful representation is the larger crop or native diagnostics, whichever actually wins the quality/cost comparison.

## Considered and rejected

- **Full-page image extraction for every PDF:** useful as a limited reference, but it ignores retained exact text, creates unnecessary source-matching work, and hides which relationships needed pixels.
- **Blur everything by default:** a research ablation can expose complementary morphology; it can also destroy decimals, tiny rules, and header emphasis. Require measured gains.
- **Ask the model to generate a complete table or field name:** makes source conservation and error attribution harder. Select complete source-linked alternatives instead.
- **Gate usefulness on .9 confidence/calibration:** the user prioritizes ability and scores. Measure delivered records and Pareto tradeoffs first; still retain explicit unresolved outcomes and deterministic validity checks.
- **Independent yes/no tests for all competing values:** can select incompatible ownership. Keep as an ablation and use explicit exclusive choices for the main lane.
- **Train a local tiny classifier now:** repeatedly inspected synthetic labels are unsuitable training evidence, and hardware/model maintenance cannot be justified before finding a real candidate-to-record gain.
- **Repeat the old model leaderboard or promote 31/36 to validation:** old cases are DEV, and better relationship accuracy need not produce correct matrices or fields.

Rationale: this plan gives the model a high-value, bounded job—choosing among source-conserving interpretations—and uses the resulting disagreements to localize optional visual evidence. It can be implemented with the existing native snapshots, bounded hosted client and ledger, without changing the public extraction path. Every creative mechanism has a cheaper baseline, a controlled ablation and a failure condition.
