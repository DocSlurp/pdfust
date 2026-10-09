# Architect proposal: admission first, modality second

Decision question: given 125 synthetic DEV pages and 16 OmniDocBench DEV images,
which two experiments most improve structured extraction quality/cost within
roughly 100 remaining minutes, a $15 cumulative cap, and CPU-only local work?

I propose measuring automatic candidate coverage before spending on model
selection, then testing whether bounded CPU OCR supplies usable external source
evidence. These are competing priorities to a broad vision/provider sweep: they
identify where the pipeline can succeed and whether the real page-image domain
has the source records its downstream decisions require. Neither changes the
production extraction defaults.

## Experiment 1: source conservation and candidate recall audit

Budget 35–45 minutes; $0 incremental inference. Run existing native extraction
and conservative table/candidate generation on all 125 synthetic DEV pages,
keeping complete outputs. Evaluate authored structural gold only in the scoring
layer. Compute candidate recall, exact retained-source ownership, complete table
cells/spans, false table detections, and reconstruction exactness by family.
Count duplicate/missing source IDs explicitly. Preserve the native policy as
baseline; compute an oracle selector only as a diagnostic upper bound on the
retained menu, never as evidence supplied to any model or as an automatic
production repair. Include failures as well as wins.

This answers a specific architecture question: do errors require better candidate
construction, better selection, or better extraction evidence? A model cannot
select a structure absent from its menu. Existing 30/30 native assembly controls
and 16/16 transformed cases do not establish automatic full-corpus recall.

Freeze the candidate builder and scorer before the cohort. Select interventions
by geometry/metadata families, not whichever examples happen to score badly.
If time permits, test one narrowly motivated geometry change as a paired DEV
ablation, using the entire cohort and reporting all regressions.

Stop gates: abandon selector inference if candidate recall is below 95% or any
source-conservation invariant fails. Keep the current candidate policy if a
change lowers complete-record exactness or introduces any false table on an
existing no-table control. Stop implementation at 45 minutes and deliver the
failure categories even when no candidate improves. These thresholds are DEV
engineering gates, not a calibrated deployment-quality guarantee.

## Experiment 2: bounded external page-image evidence probe

Budget 40–50 minutes; $0 incremental hosted inference initially. The frozen
16-row OmniDocBench registry spans all 10 document sources, five languages, and
five layouts. The pinned dataset revision has images and no original PDFs.
Native extraction from synthetic image-carrier PDFs is necessarily empty;
calling this a native extraction error would route optimization incorrectly.
Run the already installed CPU OCR engine only if model assets are available,
with one admitted page at a time and a small capped cohort fixed by registry
order. Use English and simplified-Chinese as supported-language strata; treat
other scripts as explicit unsupported/unknown controls, not accidental model
failures. Do not download new model weights or assume language support from a
dictionary filename. Record actual model/dictionary identities.

Compare a fixed small pair of input scales (e.g. 100 and 150 DPI carriers) on the
same metadata-selected pages. Retain all OCR tokens/boxes and the transformed
image identities. Score text only against the isolated annotation scorer;
record strict and normalized edit similarity separately, without claiming they
measure math transcription or table semantics. Use annotation polygons for a
separate diagnostic of box coverage/missed regions only. Never give annotation
answers, category gold, source intent, or expected field/cell mappings to the OCR
or candidate builder. Source IDs must derive from OCR observations.

This answers whether external pixels yield reliable positioned text and what
CPU/RAM cost that admission entails. It directly tests the bottleneck between
images and the source-linked structural pipeline. If OCR output is poor, a
provider comparison on clean native evidence would not establish an external
page-image solution.

Stop gates: first page above 30 seconds or 1 GiB measured process RSS stops the
scale sweep; retain the run as a resource failure. Stop after four paired pages
or at 50 minutes, whichever comes first. If native OCR assets are unavailable,
deliver that blocked admission fact and run only the already completed 16-image
carrier baseline; do not fabricate text accuracy. Prefer the smaller scale only
if it loses no more than 0.02 normalized similarity on every supported-script
pair and reduces observed CPU time by at least 20%; otherwise preserve the
higher-resolution baseline and report the tradeoff. These tiny DEV observations
do not establish a general OCR throughput or quality claim.

## Considered and rejected for this wave

- A full nine-image-arm × provider sweep: may identify provider behavior, but
  automatic candidate coverage and the image-to-text admission are unmeasured;
  it consumes the remaining clock before clarifying the structural bottleneck.
- More prompt variants on the existing 30 assembly controls: the native control
  already solves them and synthetic correlations limit external information.
- Fine-tuning or a new local GPU model: violates the local-compute constraint
  and cannot be developed, validated, and attributed within this clock.
- Operation-log editing: a useful later architecture, but it introduces another
  state machine before the evidence and candidate-admission limits are known.
- Treating image-carrier empty text as extraction failure or using annotation
  text to manufacture a purported native PDF: confounds the input domain.

## Measurement and handoff

For each run retain exact inputs, outputs, code/configuration hashes, library and
model versions, one-worker concurrency, elapsed wall time, process-tree CPU time,
and peak RSS measured with a named tool and scope. Prefer `/usr/bin/time -v` for
isolated CPU runs and label process-lifetime RSS where only `getrusage` is used;
no sampling interval applies to those tools. Separate local work from hosted
latency/cost and leave remote measurements unmeasured when not run. These two
experiments spend no new provider budget, keeping the $15 cumulative balance
available for a later selector test only after candidate recall is adequate.

The existing DEV annotations can score observations; they must remain absent
from inference evidence. Public OmniDocBench pretraining exposure is unknown.
The sample card restricts use to noncommercial research. Do not access sealed
silver material or call either DEV cohort heldout confirmation. At the end freeze
one candidate/configuration/scorer, publish paired gains and losses, and retain
unsupported-domain and resource failures as first-class findings.
