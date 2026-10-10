# P002 retained vision format repair diagnostic

Keep the strict adapter as the default. The frozen conservative repairs admit an additional false table for Haiku without improving correct slots. Sonnet bbox clipping recovers slots, but this small counterfactual does not justify broad live integration.

Rules were frozen in `e45f864` and its typing/lint-only followup `ca24508`, with 21 synthetic tests, before loading gold scores. Only explicitly covered merged continuation nulls may become empty strings; shorter nonempty rows may gain trailing empty slots within the maximum existing column count and valid span bounds; finite ordered normalized bboxes with positive page intersection may clip to 0..1000. Every invented blank and original bbox is retained. Values cannot move, duplicate, disappear, or change. Invalid spans, nonempty covered cells, ambiguous types, empty rows, malformed/refused/truncated/content-filter outputs are refused. No unit inference or geometry rescaling occurs.

All 16 responses from each retained 1200-edge Sonnet/Haiku run were processed, including every originally valid response. All repairs and refusals were saved before opening the same frozen natural16 targets. The current strict adapter matched each retained adapter snapshot byte-for-byte. Raw response files were checksum-verified unchanged. This is offline postprocessing reuse, not a provider cache hit, new paid run, or Pmin claim.

| Model | Errors strict → repair | Auxiliary complete tables | Correct slots strict → repair | False positive tables strict→repair | False positive pages strict→repair | Exact pages |
|---|---:|---:|---:|---:|---:|---:|
| Sonnet | 1→0 | 3→3 / 53 | 302→328 / 2344 | 0→0 | 0→0 | 6→6 / 16 |
| Haiku | 3→2 | 3→3 / 53 | 267→267 / 2344 | 3→4 | 0→1 | 5→5 / 16 |

These are auxiliary `pipeline_scoring` slot metrics, including covered merge slots (2,344), not the authoritative `generalization_report` anchor-cell metrics (2,333). Its table matching also differs: it counts three strict Haiku tables where the authoritative report counts two. Do not combine these scores with the main comparison; the new negative-page false positive independently rejects broad repair.

Sonnet: one normalized bbox `[113,777,899,1098]` clips its bottom to 1000. Errors fall 1 → 0; correct slots 302 → 328, with no new false positives and complete tables unchanged at 3. The scorer does not assess bbox accuracy, so increased cell admission does not verify the clipped geometry.

Haiku: one ragged matrix gains an invented blank at row 1, column 6. That repair admits a false table on negative page `pdb4e1fa3babeca265abb`: false positive tables 3 → 4 and false positive pages 0 → 1, while correct slots remain 267. Penalized slot denominator 2,474 → 2,495 and complete-table denominator 56 → 57 make the corresponding penalized scores worse. The invalid merged-span output and a nonempty covered merged cell still refuse; no values were deleted to force admission. No thresholds or case-specific rules were adjusted after these scores.

Local evaluation: wall 0.046 s, process CPU 0.057 s, executable peak RSS 49,618,944 bytes via `/proc/self/status` VmHWM (current executable). One Python process, serial 32 response revalidations, kernel high-water mark with no periodic sampling. No network, GPU or inference calls; no incremental provider charge. Original provider charges remain attributed to their original runs, not this diagnostic.

Complete counterfactual structures, edit provenance and page-level false-positive changes are retained beside each authorized original run in `counterfactual-format-repair-before-score.json` and `counterfactual-format-repair-scored.json`; combined comparison is in the Sonnet directory. Raw requests, responses and frozen run records remain untouched.
