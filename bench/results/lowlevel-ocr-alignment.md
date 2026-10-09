# Optional source-visible OCR alignment experiment

Implemented `bench/lowlevel_ocr_alignment.py` and `tests/test_lowlevel_ocr_alignment.py` in the isolated native worktree. This is a CPU-only DEV benchmark and action validator, with no production extraction changes, no document edits and no hosted calls. It provides nine natural source crops, frozen candidate evidence, separate single-review visible references, bounded character comparisons, and a strict provenance-sidecar action contract.

## Observations and fixture review

All nine 216-dpi white-background crops were rendered and visually inspected. References were transcribed directly from the rendered source, after source-aware review; they are neither blind nor independently adjudicated gold. Eight are legible enough for a single-review transcription; the damaged body crop is unavailable. Source hashes, page numbers, boxes, licenses and review caveats are frozen in `fixtures()`. PDFs are existing redistributable assets, not generated examples. Candidate `evidence.json` contains no visual reference or review note; these stay in separate `review-references.json`.

| Selector | PDF / zero-based page | Display bbox | Reviewed visible transcription | Native word view | Unicode edits after whitespace collapse |
|---|---|---|---|---|---:|
| edison-name | patent-us223898.pdf / 0 | [248,64,355,88] | T. A. EDISON. | T. A. ED IS ON, | 3 |
| edison-date | patent-us223898.pdf / 0 | [296,108,460,130] | Patented Jan. 27, 1880. | Patented Jan. 27, 188O. | 1 |
| edison-electric-agreement | patent-us223898.pdf / 0 | [248,86,357,108] | Electric-Lamp. | Electric-Lamp. | 0 |
| edison-electric-corruption | patent-us223898.pdf / 1 | [205,150,330,174] | ELECTRIC LAMP. | CR C AMP. | 6 |
| edison-watermark | patent-us223898.pdf / 2 | [284,7,404,62] | BEST AVAILABLE COPY | B EST ^VAILABLE COPY | 2 |
| edison-department | patent-us223898.pdf / 3 | [185,138,364,154] | DEPARTMENT OF THE INTERIOR, | DEPARTMBNT OF TRS INTBRIOB, | 5 |
| edison-degraded-body | patent-us223898.pdf / 1 | [61,571,263,602] | Unavailable: clipped lines, ink damage and touching characters | Preserved in evidence | Unknown |
| irs-label-agreement | f1040.pdf / 0 | [108,230,321,241] | Married filing separately (MFS). Enter spouse’s SSN above | Same | 0 |
| nics-numeric-agreement | nics-background-checks-2015-11.pdf / 0 | [118,79,179,88] | 18,870 23,022 | Same | 0 |

The date's digit zero is read from the visible year context; the glyph shape alone cannot discriminate zero from letter O. The NICS reference uses one space for a visible ruled-cell boundary, not a printed space glyph: its raw source callback concatenation is `18,87023,022`, while native word assembly correctly separates the cells. This is an assembly control, not OCR corruption. Comparison only collapses whitespace; punctuation, case, hyphens, ligature codepoints and Unicode remain distinct. No CER percentage or aggregate extraction accuracy is claimed.

Five patent crops disagree with the native word view; three controls agree; the damaged crop stays unscored. This is a deliberately selected disagreement/control collection, primarily one historical scan with poor OCR. It cannot estimate corpus-wide rates or compare model generalization. No heldout paths, existing scorer gold, test expectations, or retained model outputs were used for selection. No natural source-order bug or overprint failure is claimed.

## Evidence and action contract

Candidate evidence freezes the original PDF SHA-256, page and crop, rendered PNG SHA-256/DPI/background, complete selected source-order glyph rows and IDs, unchanged source text, native words, and missing-Unicode callback count. Selection is by baseline origin inside the crop for glyphs, and bbox center inside the crop for words. These two selectors can differ at clipped edges; the evidence explicitly does not assert pixel visibility or glyph-image correspondence.

Each action must have exactly these fields:

```json
{
  "fixture_id": "edison-name",
  "evidence_sha256": "the frozen evidence fingerprint",
  "source_ids": ["the complete ordered integer source ID sequence"],
  "decision": "propose_visual_transcription",
  "proposed_text": "T. A. EDISON.",
  "reason": "Explanation tied to visible crop evidence"
}
```

The example's source-ID placeholder is explanatory, not executable. `action-template.json` provides actual integer IDs and fingerprints with abstention actions. The three allowed decisions are `retain_source`, `propose_visual_transcription`, and `abstain`. Retain/abstain require `proposed_text=null`; visual proposals require bounded nonempty text. All require a bounded nonempty reason. Stale evidence, changed source data, incomplete/reordered/boolean IDs, unknown fields/decisions and duplicate actions are rejected. Missing submissions remain explicitly unsubmitted.

Accepted results retain original source text, native word text, exact source IDs, source path/hash/crop and evidence fingerprint. Proposed visible text is recorded separately with `status=proposal-sidecar-only` and `source_modified=false`; no replacement operation exists. Source glyph conservation cannot remove OCR-encoded spaces or fix source character substitutions. Scorer results are relative to the separate single-review reference; absent references yield `proposal_exact_match=null` and unknown edit counts for every action. Neither a model proposal nor reference availability establishes edit authorization or calibrated confidence.

## Bounds and considered alternatives

The fixed-path collection caps fixtures/actions at 12, source input at 10 MiB, full-page rasterization at 8 million pixels, selected glyphs at 1,024, crop/proposal/reason UTF-8 at 8,192 bytes and action JSON at 65,536 bytes. Documents use `DocumentLimits.web()` plus the finite private snapshot defaults. Edit-distance inputs cap at 1,024 Unicode characters and use linear scratch memory. File hash verification precedes interpretation. Crop rendering still rasterizes the full page internally; therefore the page-level pixel preflight is necessary. Returned evidence preserves interpretation warnings and missing-Unicode counts.

Considered and rejected: geometry-only glyph grouping cannot correct genuine OCR substitutions; silent text replacement would erase source provenance; a reviewer-copy repair baseline is tautological and is not reported as a model result; automatic OCR invocation would introduce model/version/configuration differences before this evidence contract is frozen; transcription of damaged body text would fabricate a reference. A simple whitespace-folded comparison was chosen over NFKC or punctuation folding because the latter can conceal the discrepancies being studied. Agreement controls prevent interpreting every raw callback gap as OCR failure.

Recommendation: independently review the eight available transcriptions, then freeze that review before submitting a visual transcriber. Compare native retention, explicit abstention and provenance-preserving proposals; report unavailable references and omitted actions separately. Keep visual corrections optional sidecars until a separately authorized editing API specifies visibility, overlap and conflict semantics.

## Reproduction, CPU resources and verification

From `/home/dan/code/oss/jev-pdf-lowlevel-native`:

```sh
.venv/bin/python -m bench.lowlevel_ocr_alignment --output /home/dan/code/oss/pylopdf/.scratch/council/lowlevel-architect/ocr-alignment/build
.venv/bin/python -m bench.lowlevel_ocr_alignment --output /home/dan/code/oss/pylopdf/.scratch/council/lowlevel-architect/ocr-alignment/build --actions /home/dan/code/oss/pylopdf/.scratch/council/lowlevel-architect/ocr-alignment/build/native-actions.json
```

The retained `native-actions.json` is a native-only retention baseline, not visual repair: nine bound actions, zero source edits, zero model calls. `native-comparison.json` retains source/word edit observations independently of submitted actions. Complete evidence, references, cropped images, action templates/results and resource summary stay in ignored local artifacts.

Final clean CPU run: 0.7335 s wall, 0.7517 s process CPU, Linux process VmHWM 84,268 KiB (82.3 MiB), no workers or GPU. Measurement uses `perf_counter`, `process_time`, and `/proc/self/status` VmHWM with no sampling; it covers fixture building, source/word interpretation, rendering, output serialization and local scoring. `getrusage(RUSAGE_SELF).ru_maxrss` separately reported 415,136 in this launcher, reflecting a possible inherited pre-exec maximum; it is not used as this process's peak RSS. Non-Linux VmHWM stays unmeasured rather than guessed. The earlier natural-survey resource artifact used getrusage alone and may share this launcher inflation; its wall/CPU observations remain valid.

Verification: 24 new tests plus 15 existing glyph snapshot tests passed (39 total); focused Ruff and mypy checks pass. Regressions cover source-preserving proposals, Unicode/punctuation distinctions, unavailable-reference handling, refusal of partial/stale/tampered/unbounded actions, incorrect proposals, reference hash/page/crop binding, and actual invisible OCR spaces bound to a hash-verified patent crop. No Rust rebuild or production edits were needed.
