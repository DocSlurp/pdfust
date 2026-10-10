# P002 raster-rule robustness screen

The combined contrast and bounded axis-gap repair arm recovers 19/22 controlled
positive shapes, versus 7/22 for the original detector. This gain does not
establish natural-document generalization: on natural16 it proposes fewer grids,
hits two bounded inventory refusals, and completes no official tables. Keep
`method="baseline"` as the default. All raster outputs require a separate
semantic gate: the subdivided-chart negative proposes a grid in every arm.

## Frozen source-only methods

The optional `contrast` arm estimates background as median luminance and requires
24 luminance levels of foreground contrast, reversing polarity on dark scans.
The optional `gap` arm keeps the original luminance threshold (<160) and joins
axis-aligned breaks up to `min(8, max(2, round(min_dimension * .006)))` pixels.
It admits stroke bands up to two percent of the smaller dimension and uses
half that admitted width plus one pixel for endpoint contact. `repair` combines
those two changes. Baseline keeps the original threshold, stroke admission,
endpoint tolerance, complete outer-edge requirement, and display mapping.
All arms retain the 2**22 pixel, 512 rule, and 4096 slot admissions. No family,
annotations, private targets, or text content determines detector thresholds.

## Controlled raster evidence

Thirty cases include 22 positives and eight negatives. The original 26-case
screen has 18 positives; four additional cases combine faint gray with gaps,
inversion with gaps, yellow with thick strokes, and gray with thick strokes and
gaps. Shapes and merged-cell spans are checked, not merely proposal presence.

| Arm | Original positives | Four combinations | Total positives | Unambiguous negatives proposing grids | Chart-grid proposal |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 7/18 | 0/4 | 7/22 | 0/7 | 1 |
| Contrast | 11/18 | 0/4 | 11/22 | 0/7 | 1 |
| Fixed-threshold gap/stroke repair | 11/18 | 0/4 | 11/22 | 0/7 | 1 |
| Contrast plus repair | 15/18 | 4/4 | 19/22 | 0/7 | 1 |

The combined arm still misses eight-pixel breaks at the 800×600 screen size and
one- and three-degree skew. It recovers faint gray, yellow rules, inversion,
eight- and twelve-pixel strokes, two- and four-pixel breaks, right-angle
rotation, and the rectangular merged cell. These are controlled geometric
capabilities, not evidence of table semantics or content extraction quality.

Exact baseline output equality against the original committed implementation
was checked on all 30 controlled cases and all 16 natural pages.

## Natural16 offline diagnosis

The predeclared DEV natural16 screen contains 12 pages with 53 official tables
and four no-table pages. All pages were rendered on CPU with the longest side
at approximately 1400 pixels. All four arms received identical image pixels
and display bounds. Source-only proposals and region-composed ownership states
were persisted before gold was opened for offline scoring. The frozen proposal
file SHA-256 is
`cb9dc407180d0c7afcb74ef0de8fdd505539a8588bf584d9f553d44c672aaa9a`.

| Arm | Proposed grids | Gold geometry overlap pool (IoU ≥ .5) | Gold matrix-shape pool | Complete official tables | Inventory refusals | No-table page proposals |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 5 | 4/53 | 4/53 | 0/53 | 0 | 0 |
| Contrast | 6 | 4/53 | 4/53 | 0/53 | 0 | 0 |
| Fixed-threshold gap/stroke repair | 5 | 5/53 | 2/53 | 0/53 | 1 | 0 |
| Contrast plus repair | 3 | 3/53 | 2/53 | 0/53 | 2 | 0 |

Overlap and shape pools are independent opportunity diagnostics; they do not
establish correct cell ownership, spans, reading order, or semantic admission.
The fixed-threshold repair arm refuses the dense multiple-table newspaper page
`p98d10ef50dee4b24506a`; combined repair also refuses
`p1bfa52a41a5e15015698`. Both failures are `Raster rule inventory exceeds
admission`, with no partial result. Relaxed continuity can connect text or
neighboring structures and increase rule inventory, so synthetic recovery does
not justify automatic fallback or replacement of baseline. All successful
region compositions conserved source IDs.

## Resources and validation

The natural source-only run took 6.09 seconds wall and 6.51 seconds process CPU,
including rendering, original-baseline comparison, four detector arms, and
region composition. Detector plus composition totals per arm were 1.00/1.04/
1.04/1.03 seconds wall and .99/1.04/1.04/1.02 seconds CPU in table order.
A psutil sampler at 100 ms measured 207.4 MiB peak RSS; `resource.getrusage`
reported 358.6 MiB process high-water RSS, capturing peaks missed by sampling.
Scope was one process and one sampler thread, no worker subprocesses, CPU only.

The controlled baseline run took .76 seconds wall/.99 seconds CPU. The three
optional controlled runs were concurrent independent CPU processes: wall times
were .74/.74/.74 seconds and CPU times .85/.85/.89 seconds for contrast/gap/
repair. Their sampled RSS was 44.8/44.2/44.8 MiB; baseline was 44.7 MiB. These
small-run timings are diagnostics, not a throughput claim. Natural arms ran
sequentially on the same render. No GPU, remote inference, or paid requests
were used.

`ruff check` and formatting passed for both changed Python files. Forty focused
Python tests passed across dense candidates and region composition. Tests cover
all four methods, display mapping, baseline identity, threshold isolation,
polarity, faint/color rules, bounded breaks, thick strokes, merged cells,
independent grids, open/nonrectangular grid rejection, admissions, negative
rectangles, chart ambiguity, and source conservation.

Raw inputs, frozen proposals, complete scores, and local screen scripts remain
ignored under `bench/results/pdf-master-artifacts/pipeline-p002/regions-audit/
raster-robustness/`. `build.py` generates the controlled cases; `screen.py
<prefix> <method>` runs one arm; `final-natural.py` freezes natural proposals and
then scores; `final-natural-score.py` scores the retained frozen proposals.
Run those scripts with this checkout on `PYTHONPATH` and the root Python
bench environment. Protected held-out silver paths were not accessed.
