# P002 retained vision format repair diagnostic

Keep the strict adapter as the default. Frozen conservative repairs admit an extra false table for Haiku without improving correct text anchors. Sonnet bbox clipping recovers admitted anchors, but this counterfactual does not justify broad live integration.

Rules were frozen in `e45f864` and typing/lint-only followup `ca24508`, with 21 synthetic tests, before loading gold scores. Only explicitly covered merged-continuation nulls may become empty strings; shorter nonempty rows may gain trailing empty slots within the maximum existing column count and valid span bounds; finite ordered normalized bboxes with positive page intersection may clip to 0..1000. Every invented blank and original bbox is retained. Literal values cannot move, duplicate, disappear, or change. Invalid spans, nonempty covered cells, ambiguous types, empty rows, malformed/refused/truncated/content-filter outputs are refused. No unit inference or rescaling occurs.

All 16 responses from each retained 1200-edge Sonnet/Haiku run were processed, including originally valid responses. Repairs and refusals were saved before opening the same frozen natural16 targets. The strict adapter matched the retained snapshots byte-for-byte. Raw source responses were checksum-verified unchanged. This is offline postprocessing reuse, not a provider cache hit, new paid run, or Pmin claim.

Authoritative results use the same `bench.generalization_scoring.score_dataset(targets,predictions)` natural-page scorer as the generalization report, including geometric table matching and owned anchor cells.

| Model | Errors strict→repair | Complete tables | Correct text anchors strict→repair | False positive tables strict→repair | False positive pages strict→repair | Exact pages |
|---|---:|---:|---:|---:|---:|---:|
| Sonnet | 1→0 | 3→3 / 53 | 299→317 / 2333 | 0→0 | 0→0 | 6→6 / 16 |
| Haiku | 3→2 | 2→2 / 53 | 245→245 / 2333 | 3→4 | 0→1 | 5→5 / 16 |

Sonnet: one normalized bbox `[113,777,899,1098]` clips its bottom to 1000. Errors fall 1→0 and correct text anchors rise 299→317, without new false positives or additional complete tables. The newly admitted bbox has approximately 0.337 IoU with its matched reference; admission does not establish correct pixel geometry.

Haiku: one ragged matrix gains an invented blank at row 1, column 6. That admits a false table on negative page `pdb4e1fa3babeca265abb`: false positive tables 3→4 and false positive pages 0→1, while correct text anchors remain 245 and complete tables remain 2. Penalized anchor denominator rises 2420→2441 and table denominator rises 56→57. Invalid merged spans and a nonempty covered cell still refuse. No rules were adjusted after scoring.

The initially retained auxiliary `pipeline_scoring` results used 2,344 row-major slots and reported Haiku three complete tables. Those metrics differ from the authoritative 2,333 owned-anchor denominator and geometry-aware matching, so they remain provenance-only under the original auxiliary filenames. They are not the reported natural-page quality result.

Authoritative local evaluation: wall 0.207s, process CPU 0.217s, executable peak RSS 60,481,536 bytes via /proc/self/status VmHWM (current executable). One process, serial 32 response revalidations; kernel high-water mark with no periodic sampler. No network, GPU or provider calls; no incremental provider charge. Original provider charges remain attributed to the original runs.

All structures, edits and raw-response hashes remain beside the authorized original runs. Authoritative scores use separately named `counterfactual-format-repair-authoritative-scored.json`, and the combined authoritative comparison is in the Sonnet directory. Original auxiliary scores and all raw requests, responses and frozen records remain intact.
