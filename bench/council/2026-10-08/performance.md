# Performance Wizard proposal: spend on distinctions that change useful output

My competing proposal is a source-preserving native extractor with a compact relationship ranker, optional tiny visual evidence, and a page-level CPU raster cache. Choose the fastest and cheapest configuration that actually improves exact fields and complete tables. Score useful extraction before discussing probability calibration. Do not make every page pay a screenshot or hosted-call tax.

This is a read-only proposal, not an implementation or an inference run. I inspected the existing evidence projection, hosted request builder, assembly code, native rendering interfaces, and findings/catalog Markdown. I did not read credentials, new holdouts, or raw future-validation files. The linked `bench/results/decision-alternatives.md` is absent in this checkout. Luna 31/36, Perplexity 30/36, and Jev 24/36 are therefore task-provided development findings, not independently reproduced measurements. The repeatedly inspected 96 authored observations are DEV material. Their ambiguous author-intent labels cannot establish fresh generalization or select a final acceptance policy.

## What the repository already tells us

- `decision_evidence.project_case` exposes literal candidate spans but also repeats their text in a complete word list. This is safe provenance, but expensive representation. It remains worthwhile to compare it against compact rows plus explicit relation features.
- `decision_hosted.request_body` currently sends text/JSON and two yes/no questions per observation. It has no image-state adapter. The runner admits at most 32,000 total request bytes and 16 questions. Base64 images must fit inside that total or require a separately justified bounded adapter; silently removing the cap would defeat this experiment.
- `decision_assembly.apply_relations` checks provenance, conflicts, and cycles, but records edges rather than producing complete tables or field paths. Relationship accuracy is an intermediate measurement. A new experimental materializer is needed to assess actual assembly ability.
- `Page.get_pixmap(clip=...)` still rasterizes the entire page; it only reduces returned RGBA bytes. `render_pixmap_impl` creates a fresh hayro `RenderCache` per call. The immutable hayro PDF snapshot is reused, but repeated crop calls do not imply reused raster or persistent render-cache work. `render_pages` does reuse a cache within its serial call or bounded worker. A benchmark-side page raster cache is the immediate implementable remedy.
- The initial pilot found resolved Jev batching substantially cheaper and faster than Opus, but weak semantic relationships and run/format sensitivity remained. That establishes neither winner status over Luna/Perplexity nor safe whole-table assembly.

## The actual product experiment

For one immutable layout snapshot, produce a native table/field result and a bounded menu of competing wrap, header-scope, and value-owner operations. A model ranks these operations. Code materializes accepted operations using original source strings and reports unresolved words/fields. It never manufactures missing text.

For useful field assembly, compare two granularities: independent edges versus a Choice over 2–8 complete local hypotheses. A hypothesis may say “join these two physical rows; inherit this header path; assign these existing values.” Whole-hypothesis ranking can reduce HTTP calls and inconsistent local answers. Limit alternatives and report candidate recall: a ranker cannot select a correct hypothesis absent from its menu. Keep missing-text recovery as a separately timed lane.

The business sample weights are exactly one third financial, one third invoice, one third scientific. Keep table/prose, header, wrap, and assignment results separate as well. Do not let abundant easy numeric assignments conceal scientific header failure.

Primary metrics: exact requested field/value/path accuracy; value-owner F1; header-scope edge F1; wrap grouping F1; complete table exactness; source-word retention; missed/extra cells. Report macro-family scores and failures, with native extractor deltas. Secondary metrics: candidate recall, invalid patches, unresolved useful output, latency, API spend. Confidence scores can rank hypotheses; reliability analysis is descriptive and cannot substitute for quality.

## Executable hypothesis matrix

Each arm freezes identical PDF sources, target fields, candidate sets, gold annotations, model IDs, and same-region question wording. Only the named representation or request arrangement changes.

| Hypothesis | Baseline and arms | Measurement that decides it |
| --- | --- | --- |
| Native structure needs no model on most pages | Production native `find_tables`/layout/field baseline; illustrative old geometry rule reported separately; native plus ranker on every ambiguity; native plus observable disagreement routing | Actual fields/table scores and end-to-end time. Report mistakes among unqueried regions too. |
| Literal text dominates raw coordinate arrays | Resolved current bundle; compact candidate text + neighboring rows; same plus code-derived geometry relations; original full word geometry | Exact paired decisions and assembled output; text/request bytes, billed input tokens, CPU projection time. |
| Geometry can be encoded cheaply without losing semantics | Full float boxes; crop-normalized coordinates quantized to 0–1000; derived alignment/overlap/leading/rule features; remove features | Quantization collision count and errors in narrow gutters/near-tied assignments; never quantize source boxes used by assembly. |
| Tiny pixels contribute layout evidence cheaply | Compact native evidence alone; plus long-edge 96, 192, 384 pixel real crop; one 768-pixel readable control | Paired score improvement and failures where visual ruling/typography actually distinguishes alternatives. Keep surrounding header plus two body rows. |
| Image encoding changes transport more than model tokens | Same raster encoded PNG, JPEG quality 40/70, WebP quality 40/70, and lossless WebP where supported | Bytes, base64 expansion, CPU encode time, reported image/input tokens and charge, decisions. Do not assume fewer bytes means fewer billed tokens. |
| Blur removes unnecessary text-reading while preserving structure | Sharp crop; Gaussian blur sigma 1 and 2 at fixed 192 pixels; image with text areas masked; rule-only crop; native vector schematic | Layout-sensitive improvement over text alone. Separate all these derived inputs from real crop provenance. Negative result is valuable. |
| Cropping destroys header context | Tight region; padded region retaining complete header and neighboring row; page thumbnail plus tight crop | Actual header/wrap ownership, bytes, and render cost. Full-page thumbnail is context, not a text-reading replacement. |
| Coherent batching saves round trips without changing answers | 1, 4, 16 questions sharing one region; equivalent singleton requests; 2, 3 repetitions for finalists | Paired flips, global assembly validity, HTTP p50/p95 only with enough repetitions, effective decisions/second, billed state replication. |
| Complete local hypotheses beat independent edges | Same evidence and alternatives; independent relation questions; Choice over bounded complete assemblies; deterministic constrained native assignment | Correct complete field sets, candidate recall, question count, construction CPU cost, rejected inconsistent edits. |
| Cache reuse beats optimizing only inference | Fresh Document/cold raster; reused Document; reuse page raster; response replay | Full-document wall time, peak RSS, disk read/encode cost, cache hit rates. Report first-use and repeat-use costs separately. |

Run the matrix sequentially, not as its full Cartesian product. Use the three tests below to eliminate branches before opening new arms.

## Thumbnail and cache implementation

Render each selected page once per required base scale on CPU, crop multiple regions from that retained raster, then downsample and encode derivatives. The base scale needed for a crop long edge L is `L / max(crop_width_pt, crop_height_pt)`. Because hayro renders the full page, full-page pixels are approximately `page_area_pt² × scale²`; a very tiny crop can require an expensive page raster even at a modest crop resolution. Log that amplification and enforce existing rendering limits. Prefer a page thumbnail for broad context, and pay for a separate higher-scale render only where the ambiguity needs readable detail.

Start with one bounded page raster cache in the experimental benchmark adapter, not a change to the library's persistent thread/cache contracts. For multiple regions, retain one highest-required-scale raster, derive lower scales from it, and cap retained raster bytes explicitly (e.g. 64 MiB LRU). Benchmark `Pixmap.samples` conversion costs: abi3 may copy, while supported version-specific builds expose a read-only buffer. Reusing cropped `get_pixmap` calls is the losing control, not the intended cache design.

Use separate keys:

1. Raster: PDF content hash plus generation, page, scale, display rotation/CropBox, background, fallback-font configuration, renderer build/version.
2. Derivative image: raster key, exact rounded pixel crop, resize/filter, blur/mask variant, encoding settings and encoder version.
3. Hosted response: exact canonical request bytes, prompt/schema version, requested model and provider routing. Store served identity. Cache successful identical requests only, as the runner already does; reparse safely when validators change.

Snapshot-local IDs cannot be reused on another page merely because its visual hash matches. Reject semantic response reuse after edits or source-ID remapping. Do not count response replay as live inference latency. A provider's advertised input-cache price is distinct from our measured cache-hit economics.

With 8,000 bytes of JSON/questions, the 32,000-byte runner cap leaves at most roughly 18,000 encoded image bytes before data-URL overhead, because base64 costs about four thirds. Preflight actual serialized bytes, try an admissible codec/resolution, and record admission failures rather than silently dropping evidence. Never send unsupported image modalities to the text-only models.

## First three discriminating tests

1. **Text representation and assembly ability.** Select 24 DEV regions, eight per family, balanced across the four tasks and including already known failures. Luna and Perplexity receive current resolved, compact literal, and compact-plus-derived-geometry evidence: 144 requests at singleton granularity. Materialize the same fixed hypotheses into actual fields/table fragments. Retain native results as the baseline. This answers whether semantics are already sufficient and whether representation compression buys speed without destroying real output. It is diagnostic only; repeated DEV improvements do not count as held-out quality.
2. **Can tiny visual evidence change a right answer?** On 18 DEV regions (six per family) selected by observable layout ambiguity before seeing new answers, test text only, plus 96px sharp, 192px sharp, 384px sharp, and 192px blurred: 180 requests across two models. Freeze crop scope and native candidates. CPU-only codec profiling first picks one admissible encoding without model calls; then test alternate encoding on disagreements only. Include a readable 768px control on failures only if the body cap permits it. If tiny images improve nothing while the readable control does, eliminate tiny-image routing instead of declaring visual reasoning ineffective.
3. **Request consolidation and cache break-even.** On 12 DEV regions (four per family), two finalist models, 1/4/16 coherent questions, three live repetitions: at most 216 requests. Compare identical total decisions, complete hypothesis ranking where applicable, and cold/warm CPU render paths. Keep unrelated-region mixing as a small explicit negative control. Select a candidate configuration by actual quality first and then time/cost; freeze it before a separately authored producer-disjoint evaluation created by another person/agent. I do not inspect that future holdout.

Negative controls across these tests: blank/wrong-region screenshot with matching dimensions; OCR/native text that contradicts or omits the visual clue; swap candidate order and opaque IDs; duplicate numeric values with different source owners; change one header/unit while preserving geometry; footnote adjoining but outside a cell; visually indistinguishable alternative author roles; gold candidate intentionally absent. A good system should expose missing evidence or candidate omission, not win by template memorization. Gold for complete extraction must be adjudicated from visible content plus explicit requested-field semantics; unobservable author intent remains excluded from hard correctness labels.

## Cost forecast and stop conditions

I verified the public [OpenRouter decisions catalog](https://openrouter.ai/api/v1/models?output_modalities=decisions) and [multimodal guide](https://openrouter.ai/docs/guides/community/multimodal-decisions) on 2026-10-08 without authentication. The relevant advertised input prices are Perplexity $0.020/M, Luna $0.100/M, Clef Flash $0.021/M, Mercury $0.020/M, Liquid $0.040/M, Solar $0.050/M, Tev $0.042/M, Span $0.020/M; these entries advertise zero output-token charges. Luna/Perplexity/Clef Flash advertise image support. These facts do not establish PDF quality or realized billing. Clef Flash has a documented roughly 2,000-token text-serving truncation caveat and base64 admission estimate; it is a later compact-control arm, not an interchangeable default.

For equal Luna/Perplexity calls, the mean advertised price is $0.060/M input tokens. Planning assumptions, not observed usage:

| Stage | Calls | Assumed billed input/request before question replication | Nominal charge | If input were billed 16 times |
| --- | ---: | ---: | ---: | ---: |
| Text comparison | 144 | 2,000 | $0.01728 | $0.27648 |
| Tiny visual comparison | 180 | 8,000 | $0.08640 | $1.38240 |
| Batching/repetition | 216 | 4,000 | $0.05184 | $0.82944 |
| All stages | 540 | varying | $0.15552 | $2.48832 |

The 16-fold column is a conservative sensitivity example, not a billing claim; actual image token accounting and per-question reuse must be measured. Run a few admitted DEV probes first and calculate a forecast from returned usage before authorizing a whole stage. The current reported $2.04695453 plus $0.60 unresolved reservations equals $2.64695453 accounted exposure, leaving $12.35304547 under the $15 cumulative cap. Existing campaign and cumulative ledger checks still apply; `CAMPAIGN_LIMIT=3.0` must not be silently raised based on this aggregate calculation. The $0.30 per-request reservation can constrain concurrency even when realized costs are tiny.

Use an initial $1 total *incremental* stop budget with sequential stage allocations $0.15 / $0.50 / $0.35, subject to stricter existing ledger limits. Reduce calls/arms when actual billing exceeds assumptions; reserve unresolved spend throughout. This proposal authorizes no new paid calls. Do not retry failed identical requests automatically. Recheck catalog prices before any later campaign.

End-to-end model cost is `layout + candidate construction + optional full-page render + crop/encode + serialize + HTTP + validate/materialize`, not HTTP alone. Measure per-document p50/p95, peak RSS, bytes and dollars, alongside correct fields and complete tables. Export failures with wins. A useful decision is worth a higher price if it changes complete extraction quality; a screenshot that merely makes a confident answer more confident is overhead.

## Considered and rejected

- Full-page readable vision on every page: recurring raster and transport cost with no established benefit over native text.
- Cropping once per question: still full-page rendering, and duplicates work for header/wrap/assignment questions on the same page.
- Extensive probability fitting before ability tests: fails the user's quality-first objective and cannot repair missing candidates or author-intent labels.
- Fine-tuning/local GPU inference now: no clean generalization corpus yet, no local GPU authorization, and hosted costs are too small to establish a break-even argument.
- Compressing screenshots solely for billed-token savings: encoded bytes and image token pricing are different measurements.
- Reusing response decisions by visual similarity: source IDs and subtle semantic changes make it unsafe; cache exact evidence and requests.
- Promoting the old 96 cases back to held-out validation: repeated exposure and debatable labels make them development controls.

The distinctive decision this proposal could change is whether the best extraction system needs tiny vision at all, and whether one cached page plus one coherent ranked assembly can provide better fields with fewer calls than a large number of individually scored edges.
