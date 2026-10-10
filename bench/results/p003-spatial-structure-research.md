# P003 spatial structure mechanisms and selector falsification controls

Research date: 2026-10-10 UTC. Public primary papers and authors' code only;
no model weights, datasets, inference, credentials, or protected inputs were
accessed. Paper metrics are not estimates of performance on our DEV corpus.
The source-owned candidate and boundary ceiling reports remain separate
empirical experiments.

## Evidence from primary sources

GraphTSR constructs a nearest-neighbor graph over extracted PDF cell chunks,
then predicts horizontal adjacency, vertical adjacency, or no relation. Its
graph reduces edge count from quadratic to O(KN); features include positions,
sizes, distances, and axis overlap. This is cell/chunk adjacency, not a
pretrained word-to-cell classifier. Sparse graph construction can omit a true
edge before classification. The released SciTSR README warns that its
preprocessed chunks and relation labels can contain noise; the relation
format also records intervening blank cells. [Paper, sections 3.1–3.3](https://arxiv.org/pdf/1908.04729),
[authors' dataset/code](https://github.com/Academic-Hammer/SciTSR),
[geometry features](https://github.com/Academic-Hammer/SciTSR/blob/master/scitsr/graph.py).

ClusterTabNet predicts pairwise word relations for table, cell, row, column,
and header membership. It uses symmetric strong connections and directed
weak connections for spanning membership. The authors explicitly identify
false-positive connected-component edges as dangerous: one edge can merge
two clusters. Their experiments use 1,000-word sequences, and they discuss
overlapping splits for longer pages. Their bounding-box evaluation shrinks
reference objects to word extents, and their span definitions differ from
other methods. These results therefore do not establish our strict cell
accuracy. [Paper, sections 3.3–3.6 and 5.3](https://arxiv.org/html/2402.07502v1),
[authors' implementation, now archived](https://github.com/SAP-archive/clustertabnet).

Table Transformer predicts structural objects and uses geometric
postprocessing. The official code intersects row and column boxes to form
cells, handles supercells, assigns source tokens by their overlap fraction,
and adjusts geometry using retained tokens. Its implementation contains
content-based suppression and removal of empty rows/columns; copying those
policies wholesale could remove legitimate blank structure. Its overlap
scores are geometric heuristics, not calibrated correctness probabilities.
[PubTables-1M paper](https://arxiv.org/pdf/2110.00061),
[official postprocessing](https://github.com/microsoft/table-transformer/blob/main/src/postprocess.py).

TableFormer predicts structure and cell boxes together, then obtains text
from PDF source rather than generating it with a custom text decoder.
The current official Docling CellMatcher maps normalized boxes into page
coordinates and retains intersection-over-source-box matches. Despite a
docstring describing a unique highest match, `_intersection_over_pdf_match`
actually records every positive intersection; a downstream unique-ownership
policy remains necessary. This is the CVPR image-structure TableFormer, not
the similarly named ACL table-text reasoning model. [Paper](https://arxiv.org/pdf/2203.01017),
[official CellMatcher](https://github.com/docling-project/docling-ibm-models/blob/main/docling_ibm_models/tableformer/data_management/tf_cell_matcher.py).

TSRFormer separates row/column separator prediction from relation-based cell
merging. It regresses separator lines and then recovers spanning cells with
a relation module. This provides a different candidate language from joining
up to three existing physical rows: separator locations and spanning cells
can change. Its learned image model is not a CPU heuristic we have validated.
[Authors' paper](https://arxiv.org/abs/2208.04921).

## Three implementable mechanisms

The following are our proposed adaptations, not claims that a decision model
reproduces the papers' learned representations or results.

1. **Bounded source-group relations with conflict-aware decoding.** Freeze
   groups from source word IDs and geometry, preserving physical duplicates;
   retain both atomic words and mechanical line segments where grouping is
   ambiguous. Freeze directional nearest neighbors and overlapping-axis
   neighbors before consulting any reference. Ask bounded native questions
   about same cell, same row, same column, unrelated, or unresolved. Separate
   row and column questions avoid treating same-row and same-column as
   mutually exclusive. Span membership needs its own directed relation;
   otherwise an ordinary row equivalence relation cannot represent a cell
   covering several rows. Record all omitted pairs and disconnected groups.
   Decode a bounded component jointly: a cluster merge must satisfy all
   retained negative constraints and geometry/order constraints, rather than
   accepting any single positive edge. Retain competing feasible partitions,
   explicit abstention, and the authenticated source-owned fallback. This
   changes row/cell partition candidates instead of assigning to fixed labels.

2. **Explicit boundary and cell geometry before source ownership.** Extend a
   source-only proposal language to ordered row/column boxes or separator
   positions, rectangular span anchors, and declared empty cells. Generate
   alternatives from source clearances, raster/vector rules, and existing
   authenticated topology proposals; a later image model may select or
   supply strict geometry, with no generated cell strings. Reconcile boundary
   order and rectangular spans first, then score complete-source overlap
   assignments. A word crossing two cells remains unresolved unless a bounded
   global decision resolves it. This admits moving, adding, or deleting a
   separator and can change column count, which the completed fixed-topology
   pools cannot do. Empty cells require independent geometry evidence because
   word clusters alone cannot locate them.

3. **Joint partition and ownership constraints.** Enumerate a bounded set of
   source-derived separator configurations and local span choices, then
   maximize relation support plus geometry evidence subject to one owner per
   source ID, ordered boundaries, nonoverlapping rectangular spans, and native
   table protection. Exact dynamic programming or bounded factor elimination
   is preferable for small components; an ILP is an implementation option,
   not a method established by the cited papers. Refuse components exceeding
   the declared search bound and retain fallback. Keep heuristic overlap
   scores separate from model probabilities. The first useful CPU diagnostic
   is candidate-language coverage after freezing all states; an oracle using
   DEV references is a separately labeled opportunity ceiling, never model
   evidence or threshold selection.

Priority: implement mechanism 1 on adjacent source segments first, then use
mechanism 2 to expose movable column boundaries and blank/span geometry.
Mechanism 3 supplies consistency and bounded search rather than another
unconstrained generation stage. A graph prototype must include contradictory
triangle, missing-edge, multiline-cell, duplicate-word, and span tests, and
report graph coverage and refusal counts before any paid experiment.

## Source-only controls for selector image utility

Preregister controls against an immutable candidate pool, literal evidence
packet, prompt, authenticated fallback ID, and source order. No page-specific
answer, score, model identity, or reference appears in requests. These are
paired falsification tests; a null result does not prove that all visual
reasoning is absent.

| Control | Fixed elements and interpretation |
| --- | --- |
| White image | Replace pixels by opaque white at the same dimensions, color mode, format, and encoder settings. Keep image-present instructions identical. This removes spatial marks while preserving image admission; encoded size and provider token usage may differ and must be retained. |
| Blurred image | Blur the same rendered source image with a preregistered radius, for example longest edge / 64, before the same encoding. Preserve dimension and alignment. Blur changes both text legibility and rules; it is not a pure test of one feature. |
| Alias seed | Apply a seeded bijection of opaque candidate labels, including fallback, with an archived semantic-ID map. Keep candidate contents fixed and independently map results back to semantic IDs. Compare semantic decisions, not literal labels. |
| Candidate order | Swap or rotate candidate display order while leaving each alias-to-state mapping and the explicitly declared semantic fallback constant. Do not let fallback become whichever candidate appears first. |
| RGB/palette repeats | Repeat matched RGB and palette arms with identical frozen inputs and settings, counterbalanced across models and page order. Preserve every attempt, failure, returned distribution, and actual wire hash. This estimates stochastic variability and service-order effects before attributing differences to encoding. |

Report semantic selection changes per page and crop, disagreements with
fallback, unresolved/failed decisions, fresh usage/cost, and output-state
hashes before examining references. If scored later, report macro page
effects alongside micro cell counts and a preregistered sensitivity analysis
excluding the two largest source-word pages, selected using source counts
only. This detects concentration without selecting exclusions using answer
quality. Compare repeats and controls across all pages, including negatives.
Do not revise a prompt using which candidate won on a particular page.

## Public snapshot provenance

Exact public PDFs, HTML, README files, and source files are retained under
ignored `pipeline-p003/catalog/spatial-structure-research/`. The manifest
records UTC retrieval dates, URLs, byte counts, and SHA-256 digests. Branch
URLs are mutable, so the archived bytes are the reproducible evidence; no
third-party code was added to the runtime. The manifest digest is recorded
after retrieval in the commit receipt sent to root. No model or dataset
downloads were performed.
