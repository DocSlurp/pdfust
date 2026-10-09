# DEV reconstruction experiment plan

2026-10-08 local date; retained run timestamps use UTC. Initial analysis and
priorities below use completed DEV evidence. No complete production pipeline or
fresh held-out quality result has been validated.

## What the initial results support

The native boundary/visible-legend control and authored candidate oracle solve
30/30 related assembly controls. Perplexity improves from 20/30 with native
evidence to 23/30 with compact candidates and 26/30 with derived geometry facts.
Luna reaches 14/30 with verbalized facts but falls to 7/30 with derived facts.
Neither beats the native control. These are ten correlated templates with three
vocabularies, and candidates are handcrafted.
[Assembly results](results/evidence-repair.md).

Luna is more promising on relationship selection: 31/36 historically named
test observations and 8/8 region gates, compared with Perplexity's 30/36 and
6/8. Batched Jev reaches 25/36 resolved relationships with high API throughput,
but batching changes some answers. The exposed partitions are now DEV.
[Grouped rates and scores](results/model-experiment-rates.md).

The geometry cascade reaches 16/16 inspected related transformations and
35/35 corpus spot cells. Earlier transformation labels called “heldout” were
inspected and remain regression evidence. Full corpus matrices lack gold.
[Geometry study](results/geometry-cascade.md).
The contamination audit found 732 passing request invariance checks and no
direct gold/fixture/private-intent leak, but explicit synthetic notes, authored
candidate menus/ROIs, nuisance source IDs, and early code-hash omissions limit
the claims. Clean projection does not establish independent validation.
[Audit](results/evidence-contamination-audit.md).

## Ranked combinations to test

**This ranking sets the next experiment order**; it is not a validated deployment ranking.
Rate units below count partial-page observations per USD or summed HTTP minute;
they exclude CPU extraction, scheduling, telemetry, and concurrent throughput.
`~` denotes published-rate estimates when provider charges were zero/missing.

| Priority | Combination | Completed component evidence | Unmeasured part |
| --- | --- | --- | --- |
| 1 | Native extraction/cascade; Perplexity derived facts only for unresolved assemblies | Native control 30/30; Perplexity derived 26/30, 48,353 observations/$ and 198.4/min | Automatic candidate recall, fallback policy, combined exactness and full-path cost |
| 2 | Compact verbalized facts to Perplexity; derived-fact fallback for unresolved results | Facts 20/30, 175,768 observations/$ and 202.5/min | Per-case error overlap, acceptance rule, two-stage quality/cost; aggregate scores cannot predict the combination |
| 3 | Native records plus Luna as relationship specialist | 31/36 relationships, ~8,383 observations/$ and 200.2/min; 8/8 region gates | Whether better relationships produce better complete records |
| 4 | Batched resolved Jev for throughput-sensitive work | 25/36; 16,973 observations/$ and 1,258.3/min | New-domain correctness and batch/singleton differences |

Keep native output as the baseline. Model admission must name the retained
candidates, allow abstention, preserve each source ID once or unresolved, and
fail closed when the correct structure is absent from the menu. Freeze source
renumbering, prompts, model/provider, rates, scorer and code before each cohort.
Choose by exact reconstructed output and observed losses; confidence can be an
optional signal but is not calibrated correctness.

## New dataset readiness

The sanitized DEV dataset is ready for parsing, metadata queries, extraction,
and visual review: **104 files / 125 pages**, with 64 layout cases and 40 math
encoding probes. Its native baseline completed all files, matched all 1,576
literal anchors, and reproduced all warm outputs. These anchors do not score
math semantics, table reconstruction, or layout relations.
[Baseline and artifact identity](results/silver-challenge.md).

Visible titles now use generic Report/Reference names instead of layout-family
and encoding names before hosted testing. Family/encoding tags remain local
metadata. The original pre-sanitization DEV baseline is retained. Four siblings
share each layout template; four math expressions share ten producer variants.
This new collection broadens DEV interventions, not independent-producer
coverage. Math is mostly ASCII/block lettering and does not exhaust typography.

The **authored silver structural baseline is complete**; [table structure results](results/silver-structure.md) retain the separate cells, spans, ownership and false-positive scores. The existing hosted
assembly runner hardcodes the earlier 30 controls; full new-dataset assembly
requires a generic candidate/gold adapter and verified candidate oracle first.
A prepared adapter lets the planned table-presence gate over all 125 pages use
authored table definitions. **Gate accuracy does not measure full assembly.**

The custodian created a separate 20-file / 26-page sealed collection and checked
parsing/rendering only. Inventory identity:
`c1f887661e3dd40faa15510001decba1c2cb0a1112bdbb1566286a6541e0fe8e`.
Its construction is independent of DEV template builders but shares a low-level
serializer. Protection is procedural, not an OS boundary. Optimization work
must not access its files/labels. Freeze the final DEV-selected candidate,
adapter and scorer before any evaluator-only confirmation; do not tune afterward.

## Image experiments next

Test the four currently cataloged native image decision models: Luna Decisions,
Perplexity Decider 1.1, Clef Flash, and Clef. Catalog modality declarations require
compatibility probes on the actual provider and request envelope.
[Current survey and Vercel alternatives](IMAGE_MODEL_SURVEY.md).

The final user-requested matrix separates these changes:

- **Color:** 8-bit RGB, 8-bit grayscale, and 16-color palette PNG with 4-bit indices.
- **Resolution:** each color mode is tested independently at 128/512/1200 px long edge.
- **Controls:** nine real arms and nine matched blanks, plus native/current text controls; `palette4` does not combine with grayscale. Pair each real arm with a blank of the same dimensions, mode, and container bit depth.

Preserve aspect ratio and retain encoded bytes, decoded dimensions/pixels, exact transformation hashes, and provider tokens.

The planned first sweep uses the 30 existing native controls for assembly
comparison; a separate all-125-page silver gate measures table presence only.
Neither sweep has a result recorded in this plan. Larger RGB images, grayscale,
and palette reduction are distinct hypotheses. Compare each real arm with its
matched blank and native text/geometry; gains over deliberately insufficient
text alone cannot establish pixel benefit. Provider vision cost depends on its
image processing, not base64 byte count. Bounded provider-cache probes must
transmit repeated requests to the provider; local replay is a distinct condition
with no new inference. Preserve cache-hit usage/charges and original versus
repeat latency rather than assuming a discount from an identical body.

Report complete outputs/errors, exact assemblies and edge/cell metrics,
abstention, false table detections, oracle candidate recall, and source loss/
duplication. Record local preprocessing CPU/RSS and complete latency separately
from hosted HTTP time/cost. Positive reported costs take precedence; zero or
missing charges use published rates and reported tokens as labeled estimates.
Unknown tokens/rates remain unknown, partial sums stay partial, and reservations
remain separate. All development, prompt changes, and image selection occur on
DEV before the confirmation freeze.

## Separate row and operation-log experiments

R001 tests row membership and cell placement independently of the image sweep
and provider-cache work. Present each observed row with retained source IDs,
header/cell slot candidates, and a bounded multiple-choice assignment menu;
compare text/geometry with screenshots at 128/512/1200 px. Score source-ID
ownership, correct row/cell/header placement, abstention and complete records.
An authored candidate oracle measures whether the correct placement is offered;
model choice measures selection from that menu. Neither alone establishes
automatic candidate discovery or full-page reconstruction.

R002 proposes an operation-log harness over source-linked records. Retain
proposed assign/move/join/split operations and ask the model to choose among
bounded operations or abstain. Validate coordinates, target existence, schema,
and source conservation before applying an operation atomically; retain enough
prior state for undo and reject invalid operations without partial edits.
Compare a valid-operation oracle, native policy, and model-selected sequence;
score final structure plus rejected/undo operations. This is pending experimental
infrastructure, not a production editing API. R001/R002 supplement ongoing
images/caching; they do not replace those experiments or relax sealed-set rules.

## Next-wave hypotheses after the 2026-10-09 remote DEV comparisons

**Planned work; none of the experiments in this appendix has been executed.**
The earlier rankings and completed options above remain retained comparisons,
not a deployment selection. This appendix prioritizes tests of insufficient
source evidence before more throughput tuning. It uses authored and natural DEV
only; no sealed collection is accessed or scored.

The frozen geometry gate resolves 8/16 known authored cases with zero wrong
choices and abstains on all eight ambiguous cases, but also abstains on every
natural condition, including 52 answerable conditions. Supplemental numeric
geometry can reduce Qwen's abstention, so adding accurate measurements does not
by itself teach evidence sufficiency. Generic identity wording improves Flash's
natural ambiguous-scope abstention from 5/44 to 19/44, while known-scope correct
choices fall from 35/52 to 32/52 and known abstentions rise. Intern's known score
is stable at image edges at least 256 px in the fresh authored matrix; that is
not evidence of a universal preprocessing floor or sufficient natural context.
Native Flash batch size two preserves all 216 singleton choices with an 8.1%
warm throughput improvement. Larger Clef batches lose quality in the retained
comparison. These findings motivate the paired controls below rather than one
combined “best” configuration.

### Freeze a broader DEV cohort before scoring

Use at least six source families: wrapped product descriptions, sparse forms,
dense ruled ledgers, borderless repeated records, multicolumn prose and OCR text
layers. Include multiple independently produced or redistributable natural
sources per family where feasible, with clean text and difficult raster cases
reported separately. Keep the existing authored 24 and natural 24 regions as
regression cohorts; 96 natural crop conditions remain treatments of one source
page, not 96 independent documents. Report producer/document clustering and the
available independent-document count before interpreting uncertainty.

Choose all eligible regions with source-only, fixed geometric/admission rules
and bounded per-document counts. Freeze source PDFs, retained target selectors,
context windows, availability features, rendering parameters, prompts, model
revisions, thresholds and planned treatment inventory before opening the new
references. Reference review should distinguish full-source structure from what
each admitted crop can establish, including genuine alternatives and reviewer
uncertainty. Candidate recall and source conservation are separate gates:
reject incomplete menus instead of attributing their errors to model selection.
No private reference, intended family label or case-specific answer appears in
an inference packet.

| Priority | Hypothesis | Paired controls | Advance or reject rule |
|---|---|---|---|
| 1 | A source-availability legend improves abstention by distinguishing observed structure from absent context. | Original versus fixed identity wording, crossed with no legend versus a compact legend of measured availability; use identical state, crop and decision options. Retain raw numerics alone as a separate older control. | Advance a legend only if ambiguous abstention improves by at least 10 percentage points on the broader DEV cohort, wrong-known rate does not increase and known-correct loss is at most 2 points. Report family-level reversals and intervals; retain a tradeoff as experimental if these gates conflict. |
| 2 | Adjacent record context and rolling-row evidence recover some abstentions without turning proximity into a same-cell claim. | Description-only crop, fixed immediate context and a bounded rolling window (one versus three neighboring rows), at fixed render scale; separately compare fixed long edge. Cross the strongest frozen wording with the same contextual controls. | Advance context only with a net gain in known exact partitions, no increase in wrong-known decisions and no reduction in ambiguous abstention. A fixed-edge gain without a fixed-scale gain remains a context/legibility confound. |
| 3 | A conservative geometry gate plus model fallback improves coverage while preserving visible structural certainty. | Native extraction proxy; frozen geometry only; model only; geometry gate then model on unresolved cases; and geometry with fixed availability legend but no automatic semantic override. | Require zero new wrong choices among geometry-admitted cases and source conservation throughout. Compare overall correctness/abstention with model-only and geometry-only. Reject routing if it increases wrong-known rate; abstention is an acceptable final output when alternatives survive. |
| 4 | Independent disagreement can catch insufficient evidence more reliably than one confident distribution. | Fixed Flash/PPLX consensus, Intern/Flash consensus and three-model unanimity, alongside each single model and the already declared majority rule. Freeze choices before any reference analysis. | Advance a consensus only when its reduction in wrong-known decisions and gain in ambiguous abstention justify measured correct-known losses and all additional calls. Confidence remains uncalibrated; an oracle union is an unattainable ceiling, never a runnable selector. |
| 5 | Small images and true batching reduce cost after evidence admission without changing decisions. | Intern at 256 versus 500/512 px on identical scopes; Flash native batch sizes one/two/four; Clef singleton versus separately admitted small batches. Cross only frozen evidence policies, with matched batch composition and padded-length measurements. | Require exact categorical and source-partition parity on all retained regressions and the broader paired cohort, with zero new errors and a repeatable end-to-end throughput or cost improvement. Keep singleton Clef when batch quality fails. A changed answer is a quality intervention, not a pure speedup. |

An availability legend contains observations such as whether neighboring rows,
column anchors, complete separating rules, target glyphs and required context
were admitted. It never says “answerable,” supplies a reference-derived choice
or treats a gap as semantic proof. Geometric support should name its source and
limits: a complete visible rule is different from a hybrid inferred cell;
whitespace continuity and alignment permit alternatives. The model should
retain unresolved when either relation remains compatible with the supplied
source. Text projection and rendered pixels should agree on the admitted scope.

For rolling-row tests, define window boundaries and clipped-neighbor flags from
the PDF before scoring. Preserve the original target pair as the sole decision
unit; surrounding rows are evidence, not extra answers to count. Include text
plus geometry, crop-only and combined packets where supported. Keep missing
source operators, glyph mappings and unsupported modalities explicit instead of
silently imputing them. Representation refusals, including the initial numeric
packet failures, retain their original statuses and costs in separate protocols.

### Combine techniques without selecting answers from references

First diagnose retained misses by fixed source-feature strata: available versus
missing context, inline versus block relation, complete versus partial rules,
text-layer reliability and admitted neighboring anchors. Publish counts for
all planned regions, including correctly handled ones. This can identify a
family of evidence failures; it cannot justify a per-case reference oracle or
exclusion of difficult inputs. A later routing policy may inspect only those
source features, with thresholds frozen on DEV before its next comparison.

Add one mechanism at a time before testing the full combination. In particular,
compare the same identity wording with and without availability legends before
adding wider context or automatic geometry routing. Retain original wording,
raw geometry, moderate image edges and the older model arms. Use the same model
revision and native head/calibration for paired prompts. Keep stock generated
labels separate from native probability outputs; no confidence threshold is
accepted as calibrated correctness without its own frozen study.

Report known exactness, wrong-known decisions, known abstentions, ambiguous
abstentions and complete source partitions with their full planned denominators.
Separate true evidence ambiguity, missed candidates, schema/refusal errors and
missing results. Require conservation of source IDs and retain literal outputs;
correct two-chunk grouping does not claim full record/table reconstruction.
Report each document/family as well as pooled correlated render treatments.
Any numerical promotion thresholds above are predeclared DEV screening rules,
not significance claims or automatic production authorization.

Measure the complete path: source interpretation, fresh rendering, qualifier
extraction, packet creation, routing and every attempted inference call. A
geometry bypass pays its preprocessing cost; a disagreement rule pays both
model calls on every input because it cannot observe disagreement in advance.
Use matched GPU/runtime/concurrency settings, randomized blocked order and at
least three timing repeats once CPU-only preparation and compatibility pass.
Separate cold initialization, warm prediction, serial latency, concurrent global
wall/span and actual native batch work. A shared-server concurrent throughput
uses elapsed span, never the sum of overlapping request latencies.

Retain CPU time, sampled simultaneous process-tree RSS, native allocator peaks,
device utilization, actual pixels/PNG bytes and reported model tokens when
available. Record sampling interval and process scope; absent usage stays
unknown. Price published-rate warm estimates separately from positive billed
charges, failed/interrupted attempts, idle/loading time and unresolved ledger
reservations. Compare correct known regions and successfully handled ambiguous
regions per measured complete-path second and labeled estimated USD, alongside
raw inputs/min; none of these is full-page extraction throughput. New inference
requires a separately frozen wave and root's shared-budget coordination; this
planning appendix creates no calls or spending.
