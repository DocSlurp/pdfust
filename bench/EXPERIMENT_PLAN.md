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
