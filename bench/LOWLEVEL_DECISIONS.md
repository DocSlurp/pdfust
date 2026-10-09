# L001: decisions before PDF word assembly

Status: initial 768-call screen complete; prompt/history and compact/frontier follow-ups, 2026-10-09.

The question is whether preserving evidence before glyph clustering improves
structured extraction. This wave does not replace deterministic PDF decoding,
enable network inference in the library, or claim natural-document generalization.

## Council and disposition

The explicitly requested `council-of-dans` skill ran three independent proposals
using `gpt-6.1-sol` with medium reasoning. The user requested experiments and full
documentation, so the proposals proceed into separate implementation worktrees.
The proposals remain distinct; their full text is retained locally under
`.scratch/council/lowlevel-{architect,inventor,eval}/proposal.md` and their attributed
findings will be summarized here after review.

| Persona | Decision it can change | Proposed artifact |
| --- | --- | --- |
| [Architect](results/lowlevel-council-architect.md) | Which native evidence exists and where a bounded hook belongs | Private Rust glyph snapshot before line clustering |
| [Genius Inventor](results/lowlevel-council-inventor.md) | Whether source encodings can reveal or mislead structural decisions | Crossed, render-equivalent PDFs and competing local groupings |
| [Performance Wizard / evaluation builder](results/lowlevel-council-eval.md) | Whether gains survive a fair comparison and pay for their overhead | Bounded decoded-operator adapter, invariance and accounting gates |

All three proposals completed; no dropout. Root selected the architect's bounded
hook, the inventor's encoding controls and the evaluation builder's invariance
gates. The evaluation builder preferred real-document recovery before broad model
screening; this wave deliberately retains the synthetic matrix as mechanism
screening, with natural-document validation still required. A hayro operator-map
fork, learned PDF grammar, per-glyph HTTP calls and inferred replacement Unicode
were considered and deferred/rejected with rationale in the separate proposals.

## Frozen experimental contract

- DEV only. Protected heldout files are neither inspected nor scored.
- A new authored cohort crosses logical cases with three PDF content encodings.
  Encoding siblings are one statistical unit, not independent documents.
- Target boundaries/regions are supplied consistently to every arm. This measures
  conditional grouping, not autonomous boundary discovery or full table extraction.
- Ordinary business headings, text and vector marks may provide evidence. No
  on-page extraction instructions or gold relations are inserted as model hints.
- Source projection is allowlisted; labels, family names, generator names,
  logical IDs and encoding names remain outside requests. Targets are read for
  scoring only after every request is frozen.
- Preserve source glyph IDs. Candidate actions can only group retained glyphs;
  unknown IDs, duplication, omission and text replacement fail validation.
- Use all scored cases in denominators, including abstention, malformed responses
  and refusals. Report ambiguous cases separately; they have no positive/negative
  extraction label. Evidence-limited arms may reasonably abstain where pixels or
  rules are needed; distinguish this from failed reconstruction against full evidence.
- Predeclare the complete screening matrix before requests. Retain all arms,
  including failures. A quality tie favors less evidence/cost; no default library
  change follows a small synthetic screening result.

| ID | Hypothesis | Evidence / treatment | Disconfirming result |
| --- | --- | --- | --- |
| L001-M | Semantic text alone explains apparent glyph gains | Literal native words and the same two source chunks, without geometry | Glyph evidence corrects additional cases |
| L001-W | Current assembled words suffice for local choices | Words and geometry, fixed grouping menu | Earlier evidence fixes repeatable misses |
| L001-G | Glyph advances and explicit characters recover lost boundaries | W plus native pre-clustering glyph records | No improvement or worse decisions despite larger inputs |
| L001-C | Removing paint-order nuisances improves encoding invariance | Geometrically sorted glyphs, excluding callback order and native words | More errors or unexplained encoding flips |
| L001-O | Text operator context contributes beyond interpreted glyphs | G plus bounded decoded content operators | Encoding-sensitive choices or no quality gain |
| L001-R | Observed prior geometry helps distinguish wraps | G plus deterministic prior-row summaries, no inferred labels | Summaries amplify incorrect row assumptions |
| L001-V | Vector marks explain relationships without rasterization | G plus interpreted drawing geometry | Equivalent or worse accuracy than a crop at higher cost |
| L001-I256 | A small crop supplies missing visual boundaries | G plus 256-pixel-longest-axis crop | No improvement over G/V |
| L001-I512 | Higher crop resolution recovers additional evidence | Same crop at 512 pixels | Same decisions with more bytes/tokens/latency |

Text arms run Jev 1.13, d1, PPLX decider and Luna decisions. Image arms run
PPLX and Luna only: the current OpenRouter catalog lists Jev and d1 as text-only.
Model probabilities are retained observations, not calibrated correctness.
Primary decisions use the highest-probability choice; ties abstain. No tuned
confidence threshold may turn a wrong decision into a hidden exclusion.

## Cost, performance and acceptance

Starting conservative cumulative accounting: **USD 9.3899227568 / USD 15**, including
**USD 1.50 unresolved earlier reservations**. L001 uses a persistent **USD 1.50** wave
ceiling, including reservations; the shared ledger also enforces campaign and
cumulative caps. Root alone makes paid calls. Stop a model after its first
transport/schema failure; do not retry by silently changing the request.

Positive reported usage/cost wins. For zero or missing dollars, preserve the
original value and compute separately labeled estimates from reported tokens and
retained published catalog rates. Unknown cost components stay unknown. Local
artifact replay is neither a provider cache hit nor a fresh timing sample.

Report exact grouping by task/encoding, abstentions, source conservation,
encoding-invariant decisions, candidate coverage, native baseline, and retained
complete outputs. Cost rates are physical page observations per USD and per
summed HTTP minute, clearly conditional on supplied regions. Also report unique
logical cases so repeats are not mistaken for corpus breadth.

Local preprocessing and hosted orchestration use wall time, process CPU time and
peak RSS. Capture measurement method, process scope, machine, thread settings,
build identity and per-stage timing. Remote CPU/RAM is unmeasured. GPU inference
is not involved in these native-parser/hosted-decision experiments.

The screening acceptance gate is at least one corrected logical case with no
new errors on an important slice, unchanged source conservation and no unexplained
encoding sensitivity. This earns a follow-up, not production acceptance. Examine
all losses and formulate the next experiment from its failure mechanism. Sparse
routing and full-document benefit need separate confirmation; never infer them
from the conditional decision score.

## External checks

Checked 2026-10-09 against the installed hayro-interpret 0.7.0 interface and
[its Device documentation](https://docs.rs/hayro-interpret/0.7.0/hayro_interpret/trait.Device.html).
Glyph callbacks expose transforms, paint and draw mode; marked-content callbacks
exist. They do not expose a general glyph-to-`Tj`/`TJ` operator map. The initial
native hook therefore must not invent stream IDs or operator ownership.

[Liquid's d1 announcement](https://www.liquid.ai/blog/d1-decision-model) describes
vision through its direct API and text-only gateway availability. Actual model
modalities and prices for this wave are frozen from the
[OpenRouter decisions catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions)
under the ignored L001 artifact directory. No new provider credentials are needed.

Raw sources, glyph snapshots, operators, request/response bodies, output groups,
catalog snapshot and measurements belong under
`bench/results/pdf-master-artifacts/decisions/lowlevel-v1/`.
Commit code, tests, this plan, Markdown results and `EXPERIMENTS_LOG.md` only.

## Preflight results and revised priorities

- The initial 24 logical cases produce 72 physical pages with identical pixels
  across all three encodings at both 72 and 144 dpi. Requests cover seven text
  evidence arms across four models and two crop arms across two models:
  **768 requests / 2,304 page decisions**. Each request has at most three pages.
- A source-only collision audit proves that initial text-only wrap evidence
  cannot distinguish four triples of join/split/unknown cases. Full-source scores
  therefore cannot establish text-only reasoning ability for those cases. Vector
  marks and corrected crops distinguish them. See the
  [evidence audit](results/lowlevel-evidence-audit.md).
- Boundary labels are authored business interpretations; code/unit conventions
  are not independently adjudicated gold. Every arm receives the same literal
  glyph-derived chunks, including the words arm. Native word-atom coverage and
  model selection accuracy are different measurements.
- The first unpaid preparation incorrectly discarded transparency into black
  crops. It was rejected before any inference. White alpha compositing and
  nonblank/distinct-image regression checks fixed it. A second unpaid preparation
  was superseded because canonical glyph evidence still included native words.
  Both artifacts remain locally with verdicts; paid input is `basic-final/`.
- The audit found a real native word-order defect under reversed glyph painting.
  It is being investigated in a separate worktree; frozen model evidence retains
  the original interpretation. A deterministic fix takes priority over paying a
  model to repair that same defect.
- The [CPU comparison](results/lowlevel-native-performance.md) found snapshot plus
  text costs 2.09× on original104 and 1.68× on the small new controls, with about
  0.84 MiB additional median process peak RSS. This is the cost of a fresh second
  interpretation; no extraction speedup is claimed.
- A [separate history cohort](results/lowlevel-history-design.md) adds 12 logical
  pages / 36 physical pages. Its three conventional continuation labels are
  tentative; visible new item identifiers and ambiguous cases are reported
  separately. Prior history is already in full-page input: summary arms test
  representation, not newly acquired evidence. Three-page operator packets
  exceeded the 200,000-byte cap during an unpaid preparation; source-only batch
  splitting produced the admitted `history-v2/` freeze, without dropping pages.

Reproduction (all preparation is offline):

```sh
.venv/bin/python -m bench.lowlevel_evidence --directory <new-basic-directory>
.venv/bin/python -m bench.lowlevel_evidence --cohort history --directory <new-history-directory>
.venv/bin/python -m bench.lowlevel_run --directory <frozen-directory> --report
# Explicitly metered, shared ledger and remaining cumulative cap apply:
.venv/bin/python -m bench.lowlevel_run --directory <frozen-directory> --run-hosted
```

## Expanded authorization and next waves (2026-10-09)

The user raised the cumulative research authorization to **USD 100**, replacing
the earlier USD 15 ceiling. Earlier charges and unresolved reservations still count.
The shared client now enforces USD 100 cumulative and USD 98 within its ledger;
root alone sends inference. L001 and L004 each have a persistent USD 5 wave cap,
and L003 has USD 15. These are admission ceilings, not expenditure targets.

| Wave | Frozen comparison | Purpose and limitations |
| --- | --- | --- |
| L001 initial | 72 encoded pages, nine evidence arms, four decision models | 768 successful calls; 24 logical authored cases, not 72 independent cases |
| L001 history | 36 pages, prior-row patterns versus original evidence | Tentative conventional joins must remain separate from explicit-ID splits |
| L002 prompt factors | 24 pixel-distinct representatives, prompt/typed-state/singleton factors | 544 records but 512 distinct bodies; aliases do not increase throughput numerators |
| L003 frontier | All nine initial arms and 72 pages, Claude Opus/Sonnet/Haiku 5.5 | Same evidence and literal decision instructions through strict chat choices; no invented confidence |
| L004 compact | All 36 history and 72 basic pages, four lossless compact source packets | 32,000-byte full-body admission; jointly changes prompt/representation/batching, not a causal compression estimate |
| L005 | Raw and compact canonical packets with identical singleton batching | Isolate representation effects using the same source facts and resolved instructions |
| L006 | All four catalog image-capable decision models; multiple image sizes and independent color/bit-depth factors | Matched bounded text prevents known serving-path truncation; retain every admitted model |

Jev's L001 history request returned HTTP 400. Its original request and USD 0.30
unresolved reservation remain retained, and the L001 stop remains active. The
provider endpoint advertises a 32,000-token prompt limit despite a 64,000-token
general context listing. This suggests, but does not prove, the cause. L004 uses
new lossless packets admitted under a conservative 32,000-byte full-body boundary;
it does not resend the failed body. No tokenizer-equivalence claim is made.

The history controls have no vector rules: their geometry hint is always unresolved.
That arm tests a constant defer cue. Only the separate basic ruled controls can test
useful divider evidence. All raw freezes remain unchanged after the native word-order
fix, so newly corrected extraction cannot leak into historical comparisons.

## Follow-up layers

| Wave | Frozen comparison | Current purpose |
| --- | --- | --- |
| L007 | Three provider transmissions of 24 exact source-selected image bodies | Measure reported provider caching, never infer hits from local replay |
| L008 | Natural OCR/source agreement; 128, 512 and native downsample-only crops | Detect when glyph conservation cannot recover visible text |
| L009 | Gateway Laya aliases/d1 text and matched d1 images | Test catalog-exclusive family and route capability |
| L010 | Lossless string serialization of L009 text state | Compatibility and packaging sensitivity; did not fix Laya compact HTTP 422 |
| L011 | Natural Senate row pairs, description/record context and fresh 512/1200 renders | Source-aware reference agreement with scope uncertainty; one page |
| L013 | Frozen divider policy plus retained model outputs | Offline paired composition; no measured cascade savings |

The L013 result motivates testing deterministic geometry before cheap semantic
decisions: Jev words reaches 40/48 authored known choices from 28/48, while
unknown abstention remains 0/24. This does not justify applying the loose-selector
policy to production. Natural decorative/fragmented/clipped-rule cases and a
fresh metered singleton cascade remain necessary. Preserve older evidence arms
and all losses; do not prune them solely because another arm leads on one cohort.
