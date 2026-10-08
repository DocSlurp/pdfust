# Private PDF-master research

Status: local development, publication hold, 2026-10-08. The GitHub repository
`justsml/pdf-master` is private and empty. Public remotes are removed; a local
pre-push hook blocks uploads. Previously published pylopdf history remains public.
GitHub Actions are disabled on the empty private repository during the hold.
Keep original license/attribution. `pdf-master` is a working name; the existing
Python import name remains `pylopdf` during experiments.

## Objective and decision rule

Recover exact table values, cell topology, and header/value relationships across
native, tagged, scanned and mixed PDFs, with the lowest measured total cost.
Optimize the accuracy/coverage/latency tradeoff rather than a single score.
Wrong accepted relationships count separately from abstentions. An exact text
inventory is necessary but cannot certify correct assignments or visible content.

Use native evidence before paid or generative inference. Retain immutable source
IDs, original text, logical and display geometry, spans, evidence and uncertainty.
Render Markdown, HTML, or key/value bullets only after choosing the structure.
Unresolved words remain attached to the result; they must not silently disappear.

## Business document coverage

The user prioritizes all three families equally: financial reports and statements;
invoices, purchase orders and forms; and scientific and technical tables.
Report accuracy, incorrect assignments, abstentions and latency separately for
each family so aggregate improvements cannot hide family-specific regressions.
Training, policy selection and evaluation must hold out entire issuers, vendors
and document templates. Existing synthetic and convenience-corpus measurements
do not yet establish this business-family coverage.

## Breadth-first hypothesis queue

| Priority | Hypothesis | Experiment and disproof condition |
| --- | --- | --- |
| Now | Explicit tags/MCIDs identify cells without raster inference | Audit real tag coverage; validate page/stream IDs and backlinks; corrupt/stale metadata must abstain. Finding Table tags alone is not success. |
| Now | Native vectors plus text geometry recover most digital tables cheaply | Compare ruled/text/network/partial-header paths, damaged rules and rotations; aligned prose and footnotes expose overreach. |
| Now | Small relationship decisions outperform whole-document generation on latency | Predict header scope or choose existing candidate edges; compare deterministic constraints, tiny learned ranker, and abstention. Score edges, not just text. |
| Now | Encoding variation can be separated from semantic difficulty | Metamorphic tests: Tj/TJ, split glyphs, hex, compressed streams, inherited resources, Form XObjects, crop and rotation. Same pixels should preserve values. |
| Next | Regional scan routing beats page-empty OCR rules | Digital title over raster table, raster table beside native table, logos/photos and redundant OCR layers. Route unresolved regions, not any image. |
| Next | Explicit semantic evidence can prevent confidently wrong headers | Identical visible tables with different author-declared header roles establish identifiability limits; compare inferred vs confirmed edges. |
| Next | Specialized non-generative structure models beat large VLM conversion | Matched Table Transformer, TableFormer fast/accurate, SLANet and wired/lineless models; reuse native words, measure initialization/render/model/assembly separately. |
| Next | Bounded header-guided body recovery fixes dense mixed-rule reports | Infer columns from header, find record starts and continuation lines, stop at footnotes/prose; inspect all unassigned source IDs. |
| Later | Page-to-page structure amortizes expensive inference | Learn boundaries from one accepted page, align subsequent pages; perturb widths, repeat headers, introduce schema changes. Invalidate on mismatch. |
| Later | Template fingerprints amortize extraction across document batches | Cluster font/line/anchor geometry; hold out entire issuers and template versions. Near-match templates must not silently reuse stale mappings. |
| Later | Arithmetic/unit constraints resolve ambiguous assignments | Check totals, currencies, units and accounting identities using exact decimals; contradictory or coincidentally balanced permutations must remain ambiguous. Never rewrite source numbers. |
| Later | Sparse global assignment beats greedy local decisions | Bipartite/min-cost matching or bounded constraint solving over row/column/header edges; abstain on near-equivalent solutions. Measure candidate growth. |
| Later | Uncertainty-directed crops are cheaper than whole-page models | Request a single boundary/edge decision with image+IDs; hold geometry proposals fixed; validate only allowed IDs/operations. Network overhead may dominate tiny models. |
| Later | Counterexample mining makes a tiny model useful | Train on actual heuristic disagreements, not easy template replicas. Hold out document families and calibration data; compare selective error curves to geometry. |
| Later | Cross-extractor disagreement detects silent corruption | Run a second parser only on suspicious fonts/regions; agreement is evidence, not truth, because parsers share failure modes. |
| Exploratory | Embedded XML/CSV/AcroForm is cheaper than reading the visual table | Inventory attachments/forms; match supported schema and provenance. Conflicting payload vs visible page must be surfaced. No automatic attachment execution. |
| Exploratory | Content operator graphs encode producer cell boundaries | Preserve text-object, marked-content and graphics-state locality; randomize producer paint order to expose overfitting. |
| Exploratory | Render residuals expose invisible, covered or missing text | Compare sparse crops against source glyph placements; test clips, overprints, broken ToUnicode and vectorized text. Avoid full-page rendering on ordinary pages. |
| Exploratory | A vector-only learned model avoids both raster and token generation | Graph/transformer over normalized words, rules, font/style and spans; outputs topology or edge labels only. Compare against a tiny CPU tree/logistic model first. |

## Layers and acceptance gates

1. Freeze inputs, independent expected values/relationships, and negative controls.
2. Run cheap alternatives across all families before deepening one path.
3. Preserve failed inputs, full decisions, versions, source hashes and timing samples.
4. Use findings to pick a small second round, retaining the original comparison.
5. Integrate only a measured win with regression tests; keep exploratory inference
   opt-in until independent document-family evaluation supports a default.

Report exact grid success, cell precision/recall, header/value edge precision and
recall, missing/duplicated source IDs, accepted wrong values, abstentions and false
positive tables. Separate complete annotations from corpus spot checks. Report
fresh-document end-to-end latency, reuse latency, p50/p95, initialization, peak
memory and remote dollars where actually measured. Concurrent CPU experiments
are exploratory timings; rerun finalists serially before speed comparisons.

All local processing, model training and tests stay CPU-only. No new remote spend
is needed for this first layer. Prior study reported $1.024262108 of the authorized
$15 total, leaving approximately $13.98 subject to later billing adjustments.
Remote model experiments must use one coordinated cost ledger and a destruction
watchdog. Business documents must not be sent to third-party inference by default.

## Primary-source research leads

- [PDF Association tagging guide](https://pdfa.org/resource/tagged-pdf-best-practice-guide-syntax/):
  explicit table roles and header attributes can carry relationships, when present.
- [pdfplumber structure access](https://github.com/jsvine/pdfplumber/blob/stable/docs/structure.md):
  structure trees, MCIDs, attributes and page references are already exposed by another parser.
- [Camelot parser mechanisms](https://github.com/camelot-dev/camelot/blob/master/docs/user/how-it-works.rst):
  alignment networks and hybrid line/text evidence are established approaches worth benchmarking.
- [Table Transformer / PubTables-1M / GriTS](https://github.com/microsoft/table-transformer):
  structure and functional-role recognition plus metrics beyond Markdown appearance.
- [TableFormer paper](https://arxiv.org/abs/2203.01017) and
  [Docling options](https://docling-project.github.io/docling/reference/pipeline_options/):
  predicted table structure with source-text cell matching; fast and accurate modes.
- [RapidTable](https://github.com/RapidAI/RapidTable) and
  [TableStructureRec](https://github.com/RapidAI/TableStructureRec):
  lightweight sequence and wired/lineless structure alternatives; upstream timing and
  accuracy claims are not measurements on our inputs.
- [Graph-based PDF extraction](https://arxiv.org/abs/2208.11203):
  an existing research direction for using native PDF information without losing it to OCR.
- [PDF Association Factur-X presentation](https://pdfa.org/wp-content/uploads/2022/05/1145-Pitman.pdf):
  embedded machine-readable invoice data provides an additional source, requiring consistency checks.

Sources checked 2026-10-08. These support hypotheses, not claims that our implementation
already handles their full scope. Model/data licenses need review before redistribution;
no model weights or new upstream code are being redistributed in this research layer.
