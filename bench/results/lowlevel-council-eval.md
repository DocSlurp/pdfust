# Lower-level PDF decision experiment: evaluation and resource contract

Prepared 2026-10-09; analysis-only, CPU-only. No hosted request, credential read, new dependency, tracked edit, or protected-set access. Parent owns inference/accounting. Applied auto-tune-performance skill and its measurement design. This proposal is a new DEV experiment, not an extension of old scores or a production quality claim.

## Recommendation

Start with glyph-backed candidate grouping over two adjacent physical rows, then compare source-operator evidence as a nuisance-sensitive ablation. Ask d1 and Jev to choose complete existing local grouping alternatives, with an unresolved option. Do not make a provider request per glyph or let a model emit PDF operators. Glyphs are useful to remove mistakes introduced by word assembly; raw syntax is not necessarily useful evidence of logical structure.

The existing R001 fixes headers, column roles, and row candidates. R002 offers atomic conservation/replay but explicitly leaves reachability unmeasured, requires nonoverlapping source-derived cell boxes, and fixes headers by default. None is a general lower-level recovery baseline. The authored context suite already has a successful native-evidence baseline, so matching its handcrafted oracle cannot establish a useful model improvement. Use it only to prove instrumentation and request isolation.

## Immediately runnable feasibility

The current .venv has native pylopdf/jev_pdf, PyMuPDF, pypdf, psutil and Pillow. pikepdf and reportlab are absent. No installation is needed: bench.feature_cases.page_pdf builds exact uncompressed fixtures; pypdf.generic.ContentStream exposes parsed operator operands; PyMuPDF Page.get_texttrace exposes character Unicode, glyph index, origin, bbox, trace-run order and paint metadata. Retain only admitted fields with explicit extractor/version provenance. Public native extraction supplies spans/words, not raw glyph records. rust/src/extract.rs privately stores Unicode, origin, size, advance, direction, font and callback order; the Device callback currently discards draw mode. A later native glyph adapter is additional implementation, not present functionality.

A local in-memory feasibility probe rendered/parsed four identical-looking strings: one Tj, a one-element TJ, two adjacent Tj strings, and q/Q wrapping. All returned five identical glyph observations and native text `AB CD\n`; operators differed as expected. Split Tj still returned one trace run. Therefore trace run != source text-show operator and per-operator glyph linkage needs controlled authored mapping or interpreter instrumentation. Do not claim generic real-PDF glyph-to-operator provenance from PyMuPDF trace sequence numbers. Cross-extractor glyph IDs are not interchangeable.

One fresh serial process also probed page 0 of three explicitly named redistributable DEV corpus files:

| Source | Native words / tables | PyMuPDF glyphs / trace runs | Combined wall / CPU s | Process lifetime peak KiB |
|---|---:|---:|---:|---:|
| NICS November 2015 | 1504 / 1 | 4319 / 1098 | .0815 / .0788 | 132176 |
| Senate expenditures | 637 / 1 | 3880 / 220 | .0230 / .0233 | 135888 |
| Edison patent | 27 / 0 | 147 / 28 | .00377 / .00471 | 136416 |

Instrument: perf_counter/process_time and resource.getrusage(RUSAGE_SELF), no sampling; includes native plus competitor extraction in one process, imports outside phase, cumulative lifetime RSS, single runs, warm OS cache unspecified. These are feasibility observations, not timing comparisons or gold quality results. A dense page readily exceeds 4000 glyphs, which is another reason to crop/slice before provider transmission. A detected table is not a correct reconstructed matrix.

## Hypotheses and cheap disconfirmation

H1: Native word segmentation loses evidence needed for one local wrap/cell decision. Glyph-backed grouping improves complete record ownership on actual native failures. Disconfirm when glyph candidate oracle adds no reachable correct output, or native/word baseline already succeeds on every selected unit.

H2: Source operators supply a useful local hint beyond glyph positions and native rules. Disconfirm when matched operator arm does not improve exact records, or equivalent encoding changes decisions without changing visible evidence. Producer-syntax sensitivity is a regression even if one encoding gains.

H3: Batching several independent local decisions over one state saves total useful-work latency/charges. Disconfirm when batches flip previously correct decisions, produce ownership conflicts, or billed tokens increase without reducing end-to-end cost. Independent answers do not imply joint consistency.

H4: A lower-level arm earns its complexity by correcting realistic errors. Disconfirm when gains appear only in synthetic forms constructed to match the prompt, only with known gold headers/rows, or only in oracle-selected regions. Keep deterministic geometry repair as the simpler competing arm.

Reject wholesale glyph classification, every-glyph hosted inference, confidence-as-calibration, full-page raw operator dumps, generated text corrections, invented missing amounts, and label-encoded source IDs. Do not discard paint observations merely to satisfy R002's overlap constraint: explicit overlapping/invisible text needs separate treatment or an admitted unsupported label.

## Freeze before paid transmission

Freeze a manifest containing code and dirty-patch hashes, selected PDF bytes/page/crop hashes, extractor/build versions, glyph map and visible render hash, gold version, candidate generator, request allowlist, model IDs, serving/pricing snapshot, policy, seeds, per-request bytes, wave cap, max calls and stopping rules. Bodies must be fully prepared before the parent accepts the wave. Resume only against the same identity; changed code/evidence is a new run. Errors, skipped inputs, truncation, absence of a feasible gold alternative and partial assemblies remain in denominators.

Choose 12 base synthetic regions, 4 equivalent encodings each (48 mechanical cases), spanning wrap, negative aligned prose, merged header, repeated labels, missing value, multichar/ligature mapping, right-angle rotation, overprint and invisible OCR. Some strata may overlap; finalize counts before running. Start inference only on four representative base regions ×2 primary arms ×2 models =16 requests, with at most four questions each. Encodings should enter a later bounded invariance wave after the mechanics pass. Do not assume the old runner's admitted models include d1; shared DecisionClient supports liquid/d1 but the R002 runner currently hardcodes different models.

At $9.3899227568 conservative cumulative spend, remaining authorization is $5.6100772432 before any concurrent parent work. Parent must recompute this value from the ledger. Provisional screening wave maximum $0.50 effective/unknown-reserved spend; subsequent fresh DEV confirmation wave maximum $0.50, admitted only if screening succeeds and cumulative cap permits it. $0.30 reservations can sharply limit simultaneous calls despite tiny observed eventual charges; serialize admissions. Never pre-admit all 16 calls from an expected cheap total. No automatic retries.

## Request and encoding invariance

Have one whitelisted projection consume only source observations plus geometric, label-blind proposals. IDs are opaque snapshot-local aliases, stable under a recorded evaluation correspondence but never borrowed from filename, gold row, family, parent template or author intent. A candidate description resolves its actual source IDs and literal text. Evaluation-side correspondence may match equivalent encodings; it must not change the public body based on expected grouping.

Mechanical checks: mutate gold, template name, source filename, family, split, author reference, previous prediction and scorer mode and require byte-identical body. Change only an option's opaque alias/order and require equivalent reconstructed selection after inverse mapping. Remove one correct candidate and require scorer to report omission instead of blaming ranking. Deliberately skip a source and duplicate a source to prove the conservation oracle fails. Opposing-intent fixtures with identical evidence must yield identical bodies and be labeled unknown for that evidence, not judged against hidden author intent.

Encoding cohort: literal vs hex strings; Tj vs equivalent TJ; split/combined text shows; extra q/Q; whitespace/comments; stream compression; object renumbering; resource-name changes. Include positioning variants only when matrices/advances are equivalent. Preserve paint order for overprints/transparent text; arbitrary operator reordering is not an equivalence transform. Verify native and competitor raster hashes at a fixed resolution, decoded glyph text/origins/bboxes, drawn rules and candidate sets before declaring two encodings equivalent. If hashes differ, quarantine the pair and investigate; do not waive equivalence to obtain results. Equivalent pixel evidence can still encode different logical metadata, so mark intended semantics ambiguous when it is unobservable in admitted evidence.

Main glyph arm includes glyph ID/text/origin/bbox/baseline/font-size and explicit paint inventory; no parser-derived Tj grouping. Operator ablation adds bounded parsed local operand/state facts without filenames or metadata, with unknown mapping stated. A source-index-blind geometric arm removes callback/operator indices. This distinguishes useful geometry from accidental serialization shortcuts. Keep request text length/options matched where practical and report remaining size confounds.

## Scoring that measures actual reconstruction

Unit is a complete selected region, clustered by original document/base template. Score strict literal source ownership, ordered glyph membership of cells, physical row/column placement, cell role, header-to-value edges, and complete record tuples `(ordered row-key atoms, ordered value atoms, ordered header path, ordered unit atoms)`. Empty/missing values remain missing. Source conservation alone receives no correctness credit. Raw character accuracy cannot replace matrix/record correctness.

Report exact complete regions (all cells/edges/unresolved inventory), record exact precision/recall/F1, ownership-edge precision/recall, reading-order errors, lost/duplicated atoms, invalid/rejected operations, unresolved regions, candidate oracle coverage, and all-attempt forced accuracy. Keep exact original Unicode separate from an explicitly labeled optional normalization score. Multichar glyphs are single source atoms with exact Unicode payload; do not split them into fabricated glyph IDs. Snapshot-specific IDs must be compared through evaluation-side correspondence across encodings, never raw alias equality. Compare each arm to native full extraction, deterministic local repair, and a menu oracle. Known headers/rows/regions are separate oracle-assisted conditions; do not silently transfer their gains to generic discovery.

Unknown adjudicated targets evaluate abstention, not arbitrary binary accuracy. All-unresolved can be safe but is not successful extraction. Report raw full distributions, selected probability and margin; no tuned threshold on screening outcomes. Existing Wilson upper bounds are descriptive and fail to account for clustered templates/multiple tuning. A dozen DEV regions cannot establish production risk bounds. Compute paired base-document differences and present individual outcomes; do not count 48 encodings or 16 related questions as 48 or16 independent documents.

## Operational and resource comparison

Make code handle deterministic glyph-to-word grouping first and ask only uncertain boundaries or candidate memberships. Cap source atoms/bytes, question count, option count and final assembly size before copying/serialization. One choice among 2–4 complete mutually exclusive local alternatives plus unresolved avoids independently high conflicting edges. At most four questions in the first pilot; test 1 vs4 questions later against exactly the same total decisions and evidence. A second dependent stage requires a new request after locally validating the first result. Batch throughput includes rejected/failed attempts in cost and wall totals.

Separate PDF opening/interpretation, glyph export, candidate generation, JSON serialization, crop rendering/encoding, hosted HTTP, response parse/validation, assembly and scoring. For CPU phases use a fresh subprocess per document, perf_counter/process_time and child-aware cpu_times; sample parent plus children at 20ms using psutil, retaining peak simultaneous tree RSS, not a sum of each child's unrelated peak. Report missed/short-lived processes and sampling blind spots. Also keep process lifetime VmHWM, distinguish it from per-phase sampled RSS, and record actual interpreter/CPU/RAM/thread/concurrency settings. Provider CPU/RAM remain unmeasured. Match fresh/warm documents and cache scope; randomize balanced paired arm order. Retain tracing runs separately from performance samples.

Useful cost/throughput numerator is exact correctly assembled regions or records, not transmitted pages. Report USD/attempt, USD/correct complete region, bytes/tokens/request, total questions, total calls, wall/CPU time, peak RSS, errors, cache/replay status and small-sample latency spread. Preserve positive reported charges; reported zero plus catalog estimates stay explicitly distinct. Unknown tokens/rates remain unknown; reservations are not realized charges. End-to-end includes local prep and validation; API-only latency is separately labeled.

## Stage gates and real DEV failure inspection

Stage0 (CPU mechanics): all projection-isolation, conservation, encoding verification and replay checks pass; 100% synthetic menu reachability; sources not representable are explicitly rejected before inference. If malformed or unmapped extraction is the failure, stop model ranking and add an extraction-recovery diagnosis instead.

Stage1 (paid screen): to continue, glyph arm must recover at least two independently adjudicated real native-failure regions versus the word/native arm, lose zero previously correct negative controls, and show no unexplained alias/encoding decision flips. This is a prespecified practical screening threshold, not a significance or reliability claim. A schema/provider failure freezes that model arm for investigation; candidate absence reports coverage failure. If improvements occur only with handcrafted choices, continue only as a representation feasibility finding.

Stage2 (fresh DEV): freeze winner and inspect four preselected additional source documents/producer strata with no prompt changes during execution; retain successes and failures. Demand zero source fabrication/duplication, exact-match benefit on at least two fresh regions, no increased wrong automatic assignment on matched known-good regions, and no more than20% median local CPU/RSS regression absent a documented quality tradeoff. CPU/RSS comparison requires repeated runs and matching environment; small noisy differences remain inconclusive. If any critical gate fails, keep simpler baseline and publish rejection. This is still DEV, not sealed confirmation or production promotion.

Before inference, inspect bounded regions in NICS and Senate where merged headers, wrapped entries or sparse row dividers actually fail strict manual reconstruction; page0 presence counts above do not establish failures. Review extracted cells, glyph source memberships, source crop and full surrounding page together. Add patent reading-order/overprint or LaTeX ligature regions only when the selected failure matches the lower-level hypothesis. Record exact document/page/crop, native output, intended source-backed record, visible-evidence answerability, candidate omission vs wrong grouping, and whether deterministic repair already fixes it. Read source-only DEV report links rather than searching artifact trees. Select a fixed small random sample from an explicit known DEV manifest alongside these deliberate hard cases to expose easy-case regressions and avoid failure-selection bias. Unmapped Type3 math and scans without source text need another recovery lane; no glyph menu can select absent Unicode. Literal anchor success in silver is explicitly not math/table/layout success.

Nothing here authorizes protected-set access, network inference by a delegated agent, local training or default-library behavior changes.
