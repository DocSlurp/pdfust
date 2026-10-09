# Deterministic divider baseline and prospective routing

Commit 53ff0da adds bench/lowlevel_geometry.py and nine Python tests in the
isolated experiment/lowlevel-corpus worktree. Ruff, mypy and all nine tests pass.
The source-only grouping function accepts interpreted drawings, two selector
boxes and task type. It receives no text, family, expected choice, fixture ID or
model probability. Character-boundary tasks always abstain.

## Frozen policy before scoring

Policy divider-v1 and module SHA-256
`b3c8fdd6ec73d8330df0c33965a960bc17ab439d17f139131a1d18cf29ca178a`
were written to geometry-policy.json before cohort decisions or scoring. No
hosted result files were read. Thresholds are 0.25 display units, 4,096 paths
and 16,384 commands. Coordinates must be finite, non-boolean and within one
billion display units; target rectangles must have positive dimensions.
Malformed admission stops rather than returning a partial decision.

A straight horizontal solid-painted stroke covering the complete horizontal
union of both description boxes splits them when it lies strictly between their
vertical centers. Without such a divider, a genuine four-edge closed axis-aligned
rectangle enclosing both boxes joins them. A partial interior stroke or vertical
interior rule prevents joining. Curves, unclosed paths, duplicate rectangle edges,
non-stroke paints and absent solid stroke color do not establish enclosure.
All other source observations remain unresolved.

Center-based between-line geometry is explicit: initial selectors are loose
sampling regions (179..196 and 197..214), while the physical divider is at y201.
The divider intersects the second selector rectangle but precedes its visible
glyphs. Strict rectangle-gap testing would miss it. This center approximation
can misclassify a rule through glyph ink on other PDFs. Interpreted drawings
also lack clip-resolved visibility; patterns/fills and fragmented outer borders
are intentionally not admitted. These are restrictions and known limitations,
not measured production guarantees.

## CPU results by type

| Cohort/type | Logical cases / PDFs | Full-source exact logical cases | Decisive geometry logical cases | Correct decisive cases | Unresolved logical cases |
|---|---:|---:|---:|---:|---:|
| Basic character boundary | 12 / 36 | 4 / 12 | 0 | 0 | 12 |
| Basic wrap | 12 / 36 | 12 / 12 | 8 | 8 | 4 |
| Separate history | 12 / 36 | 6 / 12 | 0 | 0 | 12 |

All three encodings yield identical decisions for every logical case. Basic
wrap decisions are four joins, four splits and four unresolved. Its unruled
controls remain unresolved. Boundary and history cases abstain throughout;
their exact matches merely count expected-unresolved labels and are not a
recovery claim. History conventional joins remain tentative gold as documented
in followup.md.

Basic source inputs comprise 109,204 bytes across 72 PDFs; source geometry
payloads total 18,660 JSON bytes (83..683 per page). History source inputs comprise
140,484 bytes across 36 PDFs; geometry payloads total 2,988 bytes (83 each).
Geometry payload byte counts are serialized drawings/boxes/task, not provider
tokens or an inference bill.

The audit process extracted full native snapshots, including unused glyphs,
operators and crops, before the small geometry decision. That serial CPU run
took 9.769s wall and 9.551s process CPU, with lifetime peak RSS 375,070,720 bytes
using perf_counter/process_time/getrusage; no sampling. This is preparation
scope, not the latency or memory of a geometry-only stage. A production experiment
should collect drawings directly and time the baseline separately.

## Routing and model comparison

The prospective DEV policy bypasses the model on admitted geometry join/split,
and routes unresolved to a chosen model or preserves the unresolved sources.
Admission failures stop. It would bypass eight of the 24 basic logical regions
(24 of 72 encoded observations), and none of the twelve history regions. This
is potential observation reduction. No actual cascade was executed, no provider
cache behavior was observed, and no saved dollars or latency are claimed.

Root can replay already frozen model outputs on routed regions as an offline
diagnostic. Report direct-model results, deterministic-stage decisions and the
replayed hybrid separately. Real batching changes when regions are removed:
regrouping may alter model responses, fixed three-region batches can retain
overhead, and skipping an observation is not necessarily skipping a request.
An offline replay does not measure actual cascade cost.

On this simple cohort all decisive vector grouping is solved deterministically
without language semantics. A model win over text-only evidence should therefore
be described as resolving missing rule evidence, not as learned structural
reasoning outperforming this baseline. Independent DEV documents should add
fragmented borders, decorative lines, clipping, overlapping marks and loose
selectors before routing is considered beyond these controls. Preserve unknown
cases and source coverage throughout.

No Rust or runtime behavior changed; no hosted calls, credentials or sealed
corpora were used. Full local measurements and the frozen policy remain in this
ignored scratch directory as geometry-data.json and geometry-policy.json.
