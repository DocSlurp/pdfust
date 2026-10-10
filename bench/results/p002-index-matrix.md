# P002 ordinal matrix control

The opt-in `bench.pipeline_index_matrix_generation` adapter replaces opaque source IDs in model evidence and output with exact zero-based integer word indexes. This is a format control for the output-length hypothesis. No provider requests, reference inspection, model quality measurements, or tokenizer estimates were used in its development.

The runner must call `freeze(source)` once for each complete admitted region and pass the same immutable snapshot to `request` and `parse`. The snapshot retains every original ID, literal text, coordinate, and source-order position locally. Requests preserve the existing positional signature and the explicit `objects`, `arrays`, or `quarter` evidence option. Only identity changes: object words expose `index`; array words replace their first field with the index. Existing quarter-coordinate evidence retains its explicitly selected rounding policy; parsing always uses the original coordinates. No source filtering, text corrections, additional rounding, or default parser changes occur.

The frozen output schema uses integer indexes from 0 through N−1, unchanged rectangular matrices and merged spans, at most 32 tables, 4,096 aggregate slots, and the existing 16,384-token upper bound. For N=0 each cell has `maxItems=0`, so only empty lists are admitted. Parsing refuses Boolean, floating-point, string, negative, or out-of-range indexes; repeated indexes within or across tables; invalid spans; abnormal completion finishes; refusal; duplicate JSON keys; nonfinite JSON; and malformed content. Ordered indexes expand locally to original IDs before the unchanged strict matrix parser validates ownership and computes implicit prose. Complete raw responses remain untouched.

A CPU-only constructed 512-word, 16×32 table serialization comparison used IDs `w0` through `w511`, literal integer text, and unrounded display boxes. Both formats recovered 512 cells and zero unresolved words. The compact JSON output decreased from 4,585 bytes with string IDs to 3,049 bytes with indexes (33.5%). Complete source packet sizes were:

| Evidence | String-ID bytes | Ordinal bytes |
| --- | ---: | ---: |
| Objects | 25,925 | 25,925 |
| Arrays | 16,513 | 14,980 |
| Quarter | 16,553 | 15,020 |

The object packet stays the same size because `index` is longer than `id`; output strings still lose their quotes and `w` prefix. These byte counts are not provider token counts and do not establish quality or length-failure improvements. The measurement used one Python process, no subprocesses or parallel work, `perf_counter`, `process_time`, and Linux `getrusage(RUSAGE_SELF)` high-water RSS: 0.0326 s wall time, 0.0324 s CPU time, and 26,176 KiB peak RSS. This process scope includes imports and the serialization/parse smoke workload; no utilization sampling was performed.

Validation covers Unicode literal text and opaque IDs including `r:w零`, immutable source snapshots, within-cell ordering, optional image preservation, all three evidence encodings, complete-source admission, cumulative slot admission, and strict malformed-response refusals. The new adapter has 29 passing offline tests. Matched hosted natural16 controls, costs, provider token counts, and quality remain pending root coordination. The existing source-ID matrix path remains the default.
