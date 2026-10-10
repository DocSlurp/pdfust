# P003 source-word geometry diagram control

This CPU-only preparation freezes synthetic occupancy diagrams for the existing Luna/P002 Sonnet whole-crop candidate selector. It preserves complete candidate content, aliases, per-crop alias seeds, native choice criteria, and the declared first-input fallback. No reference, fresh-confirmation result, hosted client, network request, GPU, OCR, detector, or model inference is used.

The matched completed selector is `pipeline-p003/parallel-mechanisms-generalization-v3/choice-pplx-128-rgb-r2-c6`, independently authenticated against its queue `trusted-code/choice-pplx-128-rgb-r2-c6.json`. Original generation inputs are `pipeline-p003/screen-crops-luna-1024-pinned-r0` and `pipeline-p002/natural16-vision-crops-sonnet-1024`, authenticated against their separately supplied P003 trust maps. Historical Sonnet parser SHA `8188aca8439f7c4bf455bf81b55a7a3e9f0789ca3590abbd3042d050b784591e` requires the existing explicit root approval. Complete literal source geometry comes from ordinal DEV16 `screen-ordinal-ocr300-512-r0` with external `trusted-code/b773d57.json`.

## Geometry treatment

Every diagram draws the retained source-word rectangles intersecting the exact selector crop viewport. Source IDs are stored in source order with their exact global bbox, clipping receipt, and outward integer pixel coverage. This mapping is computed uniformly from the complete source snapshot for every crop; it is a contextual inventory, not a disjoint page partition or claim of true cell ownership. Every selected ID is retained locally, including a not-drawable receipt if intersection has no positive area. Other-page omissions are counted explicitly. Source strings and IDs are never rendered as glyphs.

The canvas is white RGB; all rectangles use the same neutral `(96,96,96)` appearance. There are no table rules, candidate boxes, aliases, generated cell layouts, source text, ID-dependent colors, or score-dependent marks. Predeclared styles are filled rectangles and one-pixel outlines, each independently generated at edges 128, 400, and 512. Size follows the display-coordinate crop aspect ratio; rasterization directly projects geometry without resampling a source image. Output is lossless PNG with 8-bit RGB samples and color type 2. It contains two RGB color values, not a palette-indexed or reduced-bitdepth source image.

The native packet explicitly declares synthetic geometry-only evidence and the absence of source pixels, word glyphs and table rules. The same notice is added to instructions; the original reference to an attached source crop is changed to a synthetic diagram. All candidate arrays and choice criteria remain identical. This is an image **and instruction** treatment, not a pure pixel causal intervention. White canvas means no drawn retained bbox, not proof that the PDF is blank there. The complete comparison plus notice must fit the original 128 KiB text bound; otherwise the entire question is refused without implicit truncation.

## Source freeze and bounded hypothesis

Ignored final artifacts are in `pipeline-p003/geometry-diagram-v2/`. They retain all 16 pages and 10,778 source words, including two pages with no detector crop. The matched generation pool has 19 crops, three duplicate-only pools without a selector question, and 16 distinct pools. Six image treatments per distinct pool produce 96 prospective PPLX native request bodies, with zero transmissions. Crop-context word appearances total 2,205; this count is not a disjoint partition or correctness score.

One selector viewport combines a right-hand region on page `p98d10ef50dee4b24506a` where the ordinal detector plan has two smaller proposals. The first strict equality-based preparation stopped at this mismatch, leaving an explicitly failed partial artifact in `geometry-diagram-v1/`. Version 2 uses the same positive-intersection mapping policy for every crop, rather than aliasing the combined crop to a nearby detector ID. Candidate viewports, content and aliases are unchanged. This adjustment used geometry only, before any scoring.

Primary later test: PPLX filled 128 versus its matched RGB128 selector, with the same fallback and all16 denominator. Report source-only selection changes and independent strict cells, complete tables, negative-page false positives, abstentions and errors after the freeze. Filled 400/512 and outline styles are predeclared separate treatments, not a score-picked best image. No existing moderate branch is replaced or stopped. Blur controls already queued by root are not duplicated.

If diagrams retain much of RGB's selection benefit, that supports useful source geometry in this protocol. If they collapse, the missing information could be readable text, table rules, other graphics, context, source extraction error, or the changed instruction; the result cannot isolate text legibility alone. Any explanation must preserve this limitation and separate admission from transcription repair. No fresh48 tuning is authorized by this preparation.

## Replay, resources and receipts

`frozen.json` retains all intended source records, external source/selector/generation trust receipts, default selector seed `20261010`, exact per-model identity, styles/edges, fallback and explicit instruction-treatment flags. Per-crop `pool.json` preserves canonical candidate bytes and original input-index mapping. Image sidecars retain exact source-ID-to-pixel geometry; requests are archived separately. All 96 PNGs, sidecars, evidence packets, request bodies and compact wire hashes were rebuilt and checked before handoff. No archived code is executed. Future independent verification must supply external approved code maps rather than trusting hashes recorded by the artifact itself.

PNG sizes range from 163 to 12,601 bytes, totaling 137,332 bytes. Complete native text packets range from 1,392 to 21,470 UTF-8 bytes; none is refused. The 336 files occupy 8,033,297 bytes before the archival hash manifest. Preparation took 2.301 seconds wall / 2.272 seconds self CPU. Serial Python/Pillow used OMP/OpenBLAS/MKL environment bounds of one. Peak process-lifetime RSS was 539,156 KiB, including imports and authentication dependencies; timed wall/CPU excludes imports. Native thread counts are unmeasured, RSS is unsampled `getrusage`, and the host is contended. Subsequent diagnostic body reconstruction is outside those preparation timings. Python/Pillow versions are retained in `environment.json`.

Five targeted tests verify deterministic PNGs, independence from literal glyph content, physical duplicate ID preservation, clipping and separate outline treatment, identical candidate/criteria payloads with the explicit notice, invalid-ID/edge refusal, and complete-packet capacity refusal. Ruff and module mypy pass. Pure APIs are `diagram(source, source_ids, viewport, edge, style)` and `request(pool, model, url)`; both return their output with provenance metadata. No shared selector runtime or transport module changed.

Final hashes:

- Report: `a51cfe03d75858325e1e00ac3eeb8bce159af0b9753838b43890b87ed75763e9`.
- Frozen code/configuration: `8c0b636989e14f0bd8e289bb09ec54728eb3ac3e946a4232fa5c0f0bf68c23f6`.
- Archive manifest: `caf75bd4c6f088f059e42fda3f7e587d6200dc9ee2c4a2424fcbe189975235f4`.
