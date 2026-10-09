# T001–T003 topology candidate coverage

Three generic configurations were committed in `fccc35a` before candidate
freezing or private scoring. The original assembler remains unchanged. New
hypotheses use observed multi-fragment physical bands as column seeds, then
assign source words to left-edge column corridors. This admits short tables
without requiring three recurring data-edge anchors and keeps left-aligned
headers associated with right-aligned numeric data. Empty slots remain empty;
headers retain unknown roles.

T001 retains physical bands as rows. T002 joins nearby sparse bands outside
numeric-column hypotheses. T003 joins nearby sparse bands without numeric
words. All share the same declared seed limit, column cap and geometry bounds.
The source-native vector prior retains merged topology without new span
inference. No literal hint, explanatory sentence meaning, class/family metadata
or scorer reference is used in generation. Every candidate preserves all word
IDs exactly once in cells or its unresolved inventory.

The scored freeze uses the original 28-page companion and neutralized 24-page
source export; explanatory statements, invariant title and footer were removed
from the latter before this new candidate freeze. The freeze SHA256 is
`9c7c7090ef78f1fdcaf9e8c6183559ba7204c0e35237b2da303f9d9c7b1ed16e`.
Earlier fresh 24 model admission results contain direct class cues and are
invalid for primary classification claims. After cue removal, the eight
narrative-intent labels are also visually ambiguous; their proposals below
measure authored-intent disagreement, not established admission errors.

| Config | Original table exact /12 | Original merged exact /4 | Neutral positive exact /16 | Neutral slot word IDs /294 | Original prose proposals /12 | Neutral narrative proposals /8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T001 physical corridors | 6 | 4 | 6 | 121 | 12 | 8 |
| T002 sparse corridors | 12 | 4 | 16 | 294 | 12 | 8 |
| T003 numeric-boundary corridors | 12 | 4 | 16 | 294 | 12 | 8 |

These are oracle upper bounds over complete unaccepted alternatives. Zero
positive pages lack a candidate; T001 has six original and ten neutral positive
pages with only incorrect candidates, while T002/T003 cover every positive.
Neither accepted-but-wrong tables nor abstention rates have been measured here:
no model was called. Automatically accepting geometry proposals would remain
unsafe. Correct source ownership does not establish that a prose layout should
be a table.

Each neutral positive has exact cell text, dimensions, spans and source word
placement in at least one T002/T003 candidate. The legacy scorer reports
243/245 owned values despite exact matrices because its global text-uniqueness
condition penalizes two legitimately repeated values. Authored placement
references independently establish 294/294 source IDs in their intended slots.
The original cohort has no independently annotated extractor-ID gold; its
ownership remains a text/slot proxy plus mechanical source conservation.

Configuration freezes produce at most three candidates per neutral page and
four per original page, including the preserved native prior. Union menus add
the existing physical/rolling proposals, deduplicate complete cell ownership
and spans, and use generic `c0`, `c1`, … IDs. Rule/seed names and provenance stay
outside model bodies. Union menus have at most eight candidates per page.

Matched image512 bodies use the unchanged P001 semantic record schema prompt,
full literal source words/geometry and actual downsampled whole-page pixels.
The 96-body union freeze has SHA256
`f3df6343ad8f0676867e492a12424c1785df64704aac9700e23f95d9ef9aeade`.
Four source-native grids remain zero-call routes. Root may execute the original
cohort for admission quality; neutral ambiguous negatives require a separately
labeled cue-dependence diagnostic until independent realism review.

CPU preparation of all three configs across 52 pages took 0.126 wall seconds,
0.126 process CPU seconds and 28.30 MiB lifetime peak RSS. Union image/request
preparation took 4.099 wall seconds, 4.077 process CPU seconds and 53.12 MiB peak
RSS. Measurements use perf_counter/process_time and Linux VmHWM, sequential
CPU, no periodic sampling. Ten CPU tests and Ruff checks pass; new topology
files have no mypy errors. Existing imported-module typing failures are being
handled separately. No credentials, GPU or paid calls were used.

```bash
python -m bench.rolling_topology source-original.json source-neutral.json \
  --output bench/results/pdf-master-artifacts/rolling-topology-v1/new-freeze
python -m bench.rolling_topology \
  --output bench/results/pdf-master-artifacts/rolling-topology-v1/new-freeze \
  --targets private-original.json private-neutral.json
```

The second command evaluates already frozen bytes and refuses changed source
identities. Full source/candidate/scoring/request artifacts remain ignored.
This is a DEV geometry diagnosis, not independent generalization or a default
extraction recommendation.
