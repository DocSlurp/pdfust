# L001: decisions before PDF word assembly

Status: implementation and DEV screening in progress, 2026-10-09.

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
| Architect | Which native evidence exists and where a bounded hook belongs | Private Rust glyph snapshot before line clustering |
| Genius Inventor | Whether source encodings can reveal or mislead structural decisions | Crossed, render-equivalent PDFs and competing local groupings |
| Performance Wizard / evaluation builder | Whether gains survive a fair comparison and pay for their overhead | Bounded decoded-operator adapter, invariance and accounting gates |

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
| L001-W | Current assembled words suffice for local choices | Words and geometry, fixed grouping menu | Earlier evidence fixes repeatable misses |
| L001-G | Glyph advances and explicit characters recover lost boundaries | W plus native pre-clustering glyph records | No improvement or worse decisions despite larger inputs |
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

Starting conservative cumulative accounting: **$9.3899227568 / $15**, including
**$1.50 unresolved earlier reservations**. L001 uses a persistent **$1.50** wave
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
