# Private PDF-master: breadth-first findings

Local campaign, 2026-10-08. Nothing from this campaign was pushed. The private
`justsml/pdf-master` repository is empty; only local code, tests and experiment
artifacts exist. Public remotes were removed, default pushing disabled, and a
local pre-push hook blocks publication. Earlier public history is unchanged.
GitHub Actions are disabled on the private repository during this hold.

The current implementation direction is a cascade: preserve verified native
cells and spans; recover additional geometry conservatively; retain exact source
IDs; resolve header relationships only with sufficient evidence; use small
specialists on selected uncertain regions. Serialize the result to tables or
labeled bullets after the relationships are established. No learned model is
silently enabled in the public extraction API.

## What was implemented and tested

| Lane | Measured result | Decision |
| --- | --- | --- |
| Reusable spatial extraction | Single native interpretation produces text/table caches and immutable query snapshots. Exact regions, label candidates, source IDs, explicit grids and header ancestry have Python regressions. | Keep the API; explicit header roles and abstentions are production behavior. |
| Tiny CPU ranker | On 160 synthetic field cases, the geometric rule accepts 128 correct values and rejects 32 missing controls. The learned ranker accepts 104 correct, abstains on 56, and accepts no wrong values. | Keep learned coefficients opt-in; this experiment does not justify a learned default. |
| Semantic tags | 15 corpus PDFs: three structure trees, one Table candidate, zero supported validated table recoveries. Both authored positive controls work; nine other controls produce no table. | Useful niche route; next work is nested cell/Form association, not assuming tags solve general PDFs. |
| Encoding invariance | 13 native encodings recover identical known cells. Nine share exact raster hashes. Visibility controls show extracted content can be clipped, covered or invisible. | Keep separate source and visible-content semantics. |
| Mixed scan routing | Digital text over a scanned table defeats page-empty OCR routing. Image/area gates also route non-table illustration controls. | Need regional evidence and a detector; image presence is not a table decision. |
| Geometric cascade | 50 inputs, five methods, three fresh-document repetitions. The revised cascade passes 16/16 transformation regressions and both prose negatives; Senate/NICS retain 35/35 annotated spot cells. | Retain as experimental: shared templates and inspected regressions are not independent business accuracy. |
| Header semantics | 112 generated PDFs: constraints yield edge precision .933, recall .857, but 48 false edges remain. Identical PDF bytes can have different intended header roles. | Require caller/tag/schema evidence for confirmed semantics; keep inferred edges uncertain. |
| Fragmented vector borders | Eight identical-pixel fragmented/coalesced pairs exposed missing connectivity. Guarded repair changes fragmented recovery from 0/8 to 8/8 and preserves existing Form 1040 tables. | Keep narrow core repair with negative and corpus regressions. |
| SLANet-plus with native words | Crops recover 4/4 small authored tables, 35/35 cells; full pages recover none of those exact grids. Crops still misclassify 1/2 prose controls and recover only 17/35 dense corpus spot cells. | Use as a candidate regional specialist, not a general converter or table detector. |
| Bounded CPU cell matching | Identical associations and HTML on all 16 saved routes (15 nonempty). NICS full-page matching falls from 4,069 ms to 15.7 ms; cropped from 4,826 ms to 17.7 ms. | Keep the optimization prototype; it accelerates existing choices without fixing their semantic errors. |

The native border repair first attempted unconditional collinear unions. The
full suite caught loss of the Form 1040 grid: nearby supported form networks
merged into a larger unclosed component. The final implementation preserves
accepted original components, repairs only unaccepted components, and admits
only non-overlapping repaired candidates. It does not extend missing geometry.
All 326 focused tests, including the complete real-world suite, pass after repair.
Final full-suite validation: 1,273 passed, 16 skipped and two expected failures.
The isolated matcher environment additionally passes its 19 optional tests.
Ruff, formatting, mypy (57 source files), Clippy, API-snapshot validation, and
strict builds of all four documentation locales pass.

The SLANet harness initially discarded transparent alpha, making black-on-black
inputs. Visual inspection caught that error. The invalid run is archived and
excluded from model evidence. Corrected runs explicitly render onto opaque white,
check alpha/dynamic range, and retain inspected raster crops. The actual ONNX
session uses only CPUExecutionProvider with two intra-op and one inter-op threads.

## Speed and quality must be evaluated together

The final geometric cascade takes about 9.35 ms per transformation case including
opening and complete output, versus 8.80 ms for unrestricted geometry. The latter
produces tables for both prose controls. On Senate, the cascade takes 26.69 ms and
retains 23/23 annotated cells; on NICS it takes 97.28 ms versus native 69.07 ms, both
retaining 12/12 annotated cells. The extra work is not universally faster.

The SLANet pilot needs roughly 70–102 ms total for cropped small tables. Dense
page source-to-cell matching takes 1.57–5.68 seconds while inference takes around
110 ms. These are single-run exploratory measurements, not robust throughput
claims. Model, renderer, parser, matching and artifact-write scopes are retained
separately in the detailed report. The follow-up matcher experiment isolates
saved predictions so acceleration cannot be mistaken for better predictions.

That follow-up measured a 259–272× reduction in NICS matching time, including
input admission and the same HTML renderer. It precomputes cell boxes, scores
word/cell pairs in bounded NumPy chunks, and preserves floating-point operation
order and tie behavior. Association choices, region HTML, saved original HTML,
and complete HTML match across all 16 routes; the empty crop is a vacuous check.
Three repeated matcher-only runs exclude file reads, rasterization and inference.
This is not an end-to-end speedup claim. Unassigned source IDs remain separate
and visible; faster matching does not recover the model's missing cells.

## Next priorities

1. Evaluate complete independently annotated business tables, holding out whole
   issuers, template versions and document families. Current corpus labels are
   partial spot checks and cannot establish overall semantic correctness.
2. Promote only guarded geometry improvements; carry unassigned source words and
   explicit reasons for abstention through every fallback.
3. Compare bounded cell matching and region gating before paying for larger
   generative models. Add Table Transformer/TableFormer and wired/lineless models
   to a matched regional benchmark, preserving native text where available.
4. Test multi-page column transfer, template fingerprints, exact-decimal totals,
   units and sparse global assignments as additional evidence. Contradictory or
   equally plausible assignments must remain unresolved.
5. Train a small decision model on independently labeled disagreements only after
   simple rules are beaten on unseen families. The earlier LoRA template-learning
   win did not generalize to the original study; do not repeat that evaluation gap.

All current work is CPU-only. No additional remote rental or inference charges
were incurred; the previous reported total remains about $1.02 of the $15 cap.
No business document was sent to a third-party model in this campaign.

## Reproduction and evidence

- [Hypothesis queue and primary research sources](../PDF_MASTER_RESEARCH.md)
- [Spatial API/ranker](spatial-latest.md)
- [Semantic inventory](semantic-probe.md)
- [Encoding/visibility/OCR-routing audit](encoding-audit.md)
- [Geometry cascade, including losses](geometry-cascade.md)
- [Header relationships and counterexamples](header-relations.md)
- [Specialist CPU model and preprocessing controls](specialist-cpu.md)
- [Bounded cell matching and exact-output speed comparison](cell-matching.md)

Scripts live in `bench/`; tests in `tests/`. Full inputs, outputs, rejected
hypotheses, hashes and timing samples remain in ignored local artifact directories.
Old and new cohorts have separate denominators. None of these exploratory
results certifies broad production accuracy or justifies publishing the package.
