# P003 region gate evidence treatments

Implemented 2026-10-10 in `bench/p003_gate_packet.py`. This is an offline prompt/evidence sweep seam; it makes no inference calls, selects no model, and changes no existing processor or admission bytes.

`packet(source, bbox, pixels_available, style)` returns `(json_string, metadata)`. Supported styles are `fullwords`, `literalcoords` (an alias of fullwords), `compact`, `sample64`, `image_only`, and `lineflow`. `GATE_INSTRUCTIONS` is exported separately so evidence representation and instruction treatment can be varied independently. The caller can replace its question instructions with this constant while retaining its table/prose/unresolved choices and provider adapter. Existing legacy configuration remains the caller's default.

All styles first call the existing `pipeline_admission.admission_packet` on the **entire supplied snapshot**, including image-only and sampling treatments. Its 4,096-word, 16,000 id-plus-text-character, finite geometry, unique identity, and 256 KiB packet admissions apply before projection. A failure is a failure, never a truncated successful packet. Extraneous source fields are ignored. The snapshot hash covers canonical page size and literal id/text/bbox inventories; optional line metadata affects the lineflow evidence hash, not that shared literal inventory hash.

The requested box must have positive extent and lie inside the declared display viewport. Projection uses closed box intersection so edge-touching and zero-extent observed words remain eligible; crossing words are retained in full without clipping or invented text. Input order, distinct physical duplicates, and literal Unicode are preserved. The packet explicitly limits classification to the requested region and describes the completeness of the supplied snapshot and physical text as unknown. A declared page viewport does not prove that supplied words cover the page. Pixels are reported as supplied separately or unavailable; the function cannot inspect or verify them.

| Style | Evidence | Explicit loss or precision |
| --- | --- | --- |
| fullwords / literalcoords | Every intersecting source word as id/text/bbox objects | Exact retained display coordinates; outside-region inventory excluded |
| compact | Every intersecting word as `[literal_text,x0,y0,x1,y1]` | IDs omitted for admission only; integer quarter-point coordinates rounded to nearest, ties to even, maximum coordinate error 0.125 point |
| sample64 | At most 64 exact id/text/bbox objects, uniformly spaced in retained source order | For n > 64, indexes `floor(i*(n-1)/63)` retain first and last; explicit omitted word and text counts |
| image_only | Empty word inventory | All intersecting OCR words explicitly omitted; missing pixels remain explicitly unavailable |
| lineflow | Complete native sequence and mechanically derived geometric row bands | No region text omissions; both views repeat the same physical sources, and neither claims semantic reading order |

Metadata includes full-source, projected-region, evidence, and encoded-packet SHA-256 hashes; supplied, intersecting, selected, outside-region, omitted-region, and boundary-crossing word counts; exact literal text characters and UTF-8 bytes for supplied/region/evidence/omitted inventories; coordinate precision; identity retention; sampling; pixel availability; and encoded packet bytes. Text accounting counts literal word text without generated separators. Lineflow accounts unique physical inventories rather than counting both repeated views as two sources. The evidence hash covers the emitted evidence structure; packet hash also covers scope and availability. Both metadata and payload describe sampling and omissions explicitly.

Output is bounded by a fixed 256 KiB byte admission with an explicit error. There is no implicit truncation, automatic fallback, rolling context, tokenizer estimate, or provider-specific token promise. Rolling context belongs to a separate caller-controlled treatment and must carry its own scope. The separate instruction treatment asks about shared record/attribute structure versus independent prose, permits partial tables, and abstains when evidence cannot distinguish them. It requests admission rather than editing, transcription, or complete-page assembly.

## Offline DEV byte profile

Exactly the 16 authorized `pipeline-p002/natural16-yolo-ocr300-indices-haiku-512-columns/*-result.json` snapshots were profiled using only `source.page_size` and `source.words`. No reference boxes, model outputs, prior decisions, corpus-family rules, or protected heldout data entered packet generation. Requested regions were each entire declared viewport; smaller proposal crops can differ. Pixel availability was declared true solely to exercise encoding, with no inference or raster inspection. The complete per-snapshot metadata stays ignored at `bench/results/pdf-master-artifacts/pipeline-p003/gate-packets/natural16-whole-region-byte-profile.json` (SHA-256 `3d90b53737acffecc8c593f486df57f0859f3ccd820d205cb8372d7e9175eaff`).

All styles admitted 14 snapshots and refused the same two snapshots for existing complete-source text admission. The limit counts IDs as well as text. In particular, image-only cannot bypass this complete-source admission. Dense-page coverage therefore requires a separately reviewed admission policy; passing an already projected snapshot would lose the promised full-source admission invariant.

| Style | Admitted packet byte range | Aggregate bytes, same 14 snapshots |
| --- | ---: | ---: |
| fullwords | 2,732–73,301 | 447,286 |
| compact | 1,753–20,595 | 139,368 |
| sample64 | 2,780–10,384 | 111,216 |
| image_only | 1,139–1,198 | 16,603 |
| lineflow | 3,484–39,161 | 300,991 |

Compact reduced aggregate encoded bytes by 68.8% without omitting intersecting word text. This does not establish token reduction, provider admission, accuracy, or latency. The byte profile ran locally on CPU, serially, using Python JSON encoding; CPU time, RSS, and sampled utilization were unmeasured. No paid calls were made. A useful root-coordinated sweep is the five evidence styles crossed with legacy/targeted instructions and rolling-context absent/present, maintaining identical boxes, model, image dimensions, and gate choices across PPLX, Clef, and Luna. Retain actual request content and provider token-limit behavior rather than interpreting a returned choice as proof that every source token was consumed.

Validation: 39 offline new-packet and existing-admission tests pass, including duplicate preservation, full-source validation before sampling/image-only, uniform sample endpoints, quarter-point ties, Unicode byte accounting, projection boundaries, reading-view inventories, complete-source and final-packet refusal, and unchanged input dictionaries. Ruff and strict mypy pass for the new module and tests. Existing admission code and golden packet bytes are unchanged.
