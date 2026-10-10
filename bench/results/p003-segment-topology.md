# P003 bounded source-segment topology opportunity

This CPU-only experiment freezes geometry-derived alternatives before an independent DEV scorer reads references. It changes row and column topology rather than selecting another assignment into fixed cells. It performs no hosted calls, OCR, model inference, network requests, or fresh-confirmation access. No quality result is claimed here.

The source is the complete retained ordinal DEV16 baseline at `pipeline-p003/screen-ordinal-ocr300-512-r0`, authenticated using the separately supplied `pipeline-p003/trusted-code/b773d57.json`. All 16 intended pages remain in the denominator. Proposal generation reads retained literal words, source ownership, detector crop bounds, and page geometry; historical generated strings and scores do not enter proposals. Baseline authentication replays historical outputs solely to establish provenance.

## Frozen language

Complete-link physical lines require center drift at most 0.35 times the smaller actual word height and vertical overlap at least 0.5 times that height. Competing line matches start a separate band; a bridge word cannot union existing bands. Contiguous spatial segments use a gap at most 1.5 times the line's median actual word height. IDs within every group retain original source order, including physical duplicates. These measurements are bbox heights, not font-size estimates or probabilities.

Column proposals come from segment gaps supported by at least two physical lines. They rank by supporting-line count, gap width, then coordinate. At most four distinct column boundaries survive; near-duplicate and capped probes receive explicit refusal receipts. Adjacent physical-line joins require a nonnegative vertical gap at most 1.5 smaller median word heights and at least 0.5 horizontal overlap relative to the smaller line width. The four smallest normalized gaps survive, with explicit receipts for the remaining eligible joins.

All binary combinations of these at most eight disputed boundaries are enumerated, at most 256 per crop. Identical full states are deduplicated. The first candidate is the geometry control: all retained column splits active, no row joins. Column toggles change the entire grid's column count; adjacent-line joins change logical row count and can combine continuation strings. Every resulting cell is rectangular and atomic. Strings are rebuilt only by joining complete literal source IDs in source order, without normalization, generated text, or word splitting.

Words outside the crop, with nonpositive geometry, or crossing an active column boundary remain unresolved. Every full-page source ID appears exactly once in assigned cells or unresolved ownership. Composition validates each selected state before rejecting all table pairs with overlapping bboxes or shared source IDs. It does not rank, merge, or silently retain one conflicting hypothesis.

The language is intentionally restricted: at most five columns, at most four joins, no asymmetric row spans, no partial-cell continuation across otherwise separate rows, no new crop acquisition, and no transcription correction. Prepared crops do not include a semantic no-table alternative; admission is a separate experiment. An oracle over this pool would establish opportunity only within this declared language and matching/composition policy, not a global model ceiling.

## Source-only inventory

Final artifacts are in ignored `pipeline-p003/segment-topology-v4/`. They preserve 16 complete source snapshots, 20 detector crops, 324 physical lines, 708 physical segments, and 1,190 distinct legal crop states. Nineteen crops have alternatives with different row/column dimensions. There are 35 column and 42 row boundaries in the bounded menus, 410 explicit proposal refusal receipts, and 47 words excluded from assignment because their geometry is outside or nonpositive within the exact crop. No crop-owned literal payload is omitted.

Full-page source inventory contains 10,778 words; detector crops own 2,205. Two pages have no detector crop and remain explicit all-unresolved controls. Composed geometry controls retain 18 tables after overlap conflicts and leave 9,826 source IDs unresolved. These are ownership counts, not cell correctness or semantic admission measurements. The largest complete archived plan is 206,554 bytes; no model question packet or implicit evidence truncation is constructed.

Candidate counts in frozen crop order are `32, 1, 2, 32, 32, 4, 32, 16, 6, 256, 256, 256, 12, 2, 224, 3, 16, 2, 2, 4`. The 80 artifact files occupy 30,813,519 bytes before the archival hash manifest.

Versions 1–3 remain retained as preparation diagnostics. Version 2 added validation of each selected source partition before composition; later versions corrected resource reporting to distinguish import lifetime RSS from timed preparation and record the actual thread environment. All four versions have the same proposal policy and 1,190 candidate states; no scoring or reference access occurred between them.

## Reproduction and scoring seam

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m bench.p003_segment_topology_prepare \
  --baseline bench/results/pdf-master-artifacts/pipeline-p003/screen-ordinal-ocr300-512-r0 \
  --trusted-code bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/b773d57.json \
  --output bench/results/pdf-master-artifacts/pipeline-p003/segment-topology-new
```

The prepare module refuses to overwrite existing output. `frozen.json` archives policy, complete intended records, external source-trust receipt, and local helper hashes before proposals. `report.json` retains every page's source/control hashes and every crop's ownership, omissions, refusals, shapes, plan and candidate hashes. Each crop folder has complete `plan.json` and `candidates.json`; source snapshots are stored once per page. `manifest.json` hashes every retained file except itself.

Pure APIs are `freeze(source, source_ids, bbox)`, `candidates(source, plan)`, `decode(source, plan, active_boundary_ids)`, and `compose(source, selected_crop_states)`. An independent verifier should authenticate the code against a separately approved map, authenticate baseline source through the original external map, rebuild plans and all candidate states, and validate page composition. Candidate generation and scoring remain separate. Crop-wise optimistic scores must not be presented as attainable page scores unless an explicit legal page combination and fixed matching are reconstructed.

Six targeted tests verify actual topology changes, literal duplicate preservation, the eight-boundary/256-state cap with explicit refusals, crossing-word abstention, source/menu authentication, no-crop behavior, and validation before conflict removal. Ruff and module mypy pass. Preparation is serial Python with OMP/OpenBLAS/MKL set to one, no subprocess workers, and no GPU. Final preparation took 17.913 seconds wall / 17.800 seconds self CPU with 539,156 KiB process-lifetime peak RSS. Wall/CPU timing includes authentication and preparation but excludes imports; peak RSS is process-lifetime `getrusage`, including imports, without sampling. Native thread counts are unmeasured and the machine is contended.

Final receipt hashes:

- Report: `3f28881fc7f7430715aa544ba22321409af631ab2bab59e2d1992c977ea61b2a`.
- Frozen configuration/code provenance: `51e76380b5efe2a176c3cf5017bf9649cb582cf921e7c9717d3ee13797285b5b`.
- Archival file manifest: `95f84dd87da2779f14d5532a3334fa59c5f6b8944b5c2c7ba55c501c20c41d3d`.

All 20 candidate files were confirmed byte-identical across versions 1–4; revisions did not alter the opportunity pool.
