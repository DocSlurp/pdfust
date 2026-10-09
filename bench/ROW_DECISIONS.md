# R001: row-at-a-time source decisions

R001 asks a model to place each retained source fragment into one proposed logical
row and column, or leave that fragment unassigned. The model chooses existing
source IDs; it never generates cell text, headers, new rows, or missing amounts.
This is an opt-in experiment in `bench/decision_rows.py`. It does not modify PDFs
or change default extraction behavior. No hosted requests have been made by the
implementation or its tests.

The generic input contains immutable word IDs, literal text and display bboxes;
fixed source-backed headers; row hypotheses; column slots with explicit source
header relationships; and disjoint fragments. Each fragment can carry a narrower
`allowed_slots` list. Optional context supplies literal notes, source words or
native drawing observations. Optional PNG evidence uses the same native image
variants as the separate image matrix. Labels and scoring metadata are stored
outside the model input.

There are at most 16 fragment questions, 64 row/column slots, 4,096 words,
64 KiB of source text, 8 KiB of context, and 512 KiB of PNG bytes. A complete
request is capped at 750,000 encoded bytes. A response must contain every
question exactly once, a distribution over precisely the declared options, and
a chosen maximum-probability option. Distributions allow the existing 0.02
sum tolerance; probabilities are not calibrated confidence.

## Existing DEV pilot

```python
from bench.decision_context_cases import context_cases
from bench.decision_image_matrix import VariantCache
from bench.decision_rows import build_request, pilot_case, score_response

case = context_cases()[0]
pilot = pilot_case(case)
image = VariantCache(artifact_directory / "images").make_variant(
    case["pdf_bytes"], case["evidence"]["current_region"], edge=512, mode="rgb8"
)
body = build_request(pilot["input"], model_id, image=image)
# The campaign coordinator explicitly admits and executes body through the ledger.
# score = score_response(pilot, hosted_result)
```

The adapter uses all 30 existing authored DEV cases: ten correlated templates
across three vocabularies. It fixes the description and amount headers and asks
three questions for the lead description, trailing description, and value
fragments. Source IDs are renumbered densely within this snapshot, with a private
mapping to the original extraction IDs. Earlier text and convention notes cannot
signal ownership through an offset in the displayed IDs.

Each fragment receives the same four placements and an unassigned option:

| Option | Candidate placement |
|---|---|
| `slot0` | Logical row `r0`, description column `c0` |
| `slot1` | Logical row `r0`, value column `c1` |
| `slot2` | Logical row `r1`, description column `c0` |
| `slot3` | Logical row `r1`, value column `c1` |
| `unassigned` | Preserve the fragment without deciding ownership |

The `r0` hypothesis spans both physical description lines; `r1` covers the second
line. Their overlap is deliberate: the candidate set can express a wrapped record
and a separate second record. Both hypotheses come from retained geometry,
independently of the authored choice. Columns and the candidate row count are
constructed by the harness. They are not discoveries made by the model.

The authored A target places lead and tail in `r0/c0` and value in `r0/c1`.
The B target places tail in `r1/c0` while retaining the first description and
amount in row zero. For the three unresolved cases, all three data fragments
remain unassigned and the headers stay fixed. This explicit header preservation
adapts the original unresolved assembly, which leaves all admitted words,
including headers, unresolved.

Images at 128, 512 and 1200 pixels can be attached without changing the source
candidate state. Region crops omit the explicit convention notes in two templates;
full-page images or explicitly admitted source context include those notes.
Full-source target recovery and admitted-evidence answerability are different
measurements. R001 does not invent visibility gold for resized images.

## Validation and scoring

Input validation requires headers and fragments to partition all admitted source
IDs exactly once. Header paths must refer to fixed retained headers. Assignments
must cover all fragments and select only their retained slots. Materialization
happens in local buffers after complete response validation, with no returned
partial assembly on failure. It preserves headers, unassigned source IDs and
source word order within cells. Every active logical row gets all declared slots,
including explicit empty value cells, and one source-linked record per value
column. Text comes only from the retained words.

The scorer reports candidate coverage independently of selector accuracy. Removing
a correct slot lowers the candidate ceiling even if the model follows every
remaining constraint. Complete records are compared by source ownership and
header paths, with precision, recall, F1 and whole-region semantic exactness.
Exactness also requires the authored assignments and unassigned data source set;
it does not compare guessed empty-cell geometry or model-generated cell IDs.
Invalid responses fail atomically and receive no materialized assembly.

CPU tests establish an oracle candidate ceiling of **90/90 covered fragment
targets and 30/30 fully covered regions**. Selecting those authored targets gives
complete-record F1 1.0 and exact semantic recovery in all 30 cases. These are
candidate-construction checks, not model accuracy results. Tests also cover
wrapping, separate records, malformed distributions, missing questions, unknown
source IDs, duplicate ownership, attempted header moves, immutable input,
unassigned conservation, candidate omissions, PNG attachment at all three sizes,
and request equality after private gold mutation.

The constructed candidates assume the correct fragment boundaries, two candidate
rows and two known columns. This small DEV pilot cannot establish row discovery,
transcription quality, real-world structural extraction, generalization, or
independence of its correlated templates. Independent decisions can also produce
inconsistent combinations; preservation and full-record scoring expose those
combinations rather than repairing them into a preferred answer.
