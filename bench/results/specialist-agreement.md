# Offline source-only specialist/geometry agreement

Rules and agreement decisions were frozen before private targets were read. All 28 reviewed DEV pages Every configuration retains 16 borderless, 8 prose and 4 ambiguous pages. Nonagreement defers; it is not a successful extraction. Strict compares source-ID partitions, shape, explicit spans and complete text matrix; the weaker text-matrix arm omits ownership equality. All three T005 source configurations are retained. Missing predicted-cell/HTML anchor correspondence defers.

| Config/rule | Gate AND (offline) | Accepted correct tables | Accepted wrong tables | Prose FP | Deferred positives | Ambiguous accepted (unscored) |
|---|---|---:|---:|---:|---:|---:|
| T005-first-two-capped/strict | False | 7 | 0 | 0/8 | 9/16 | 2/4 |
| T005-first-two-capped/strict | True | 7 | 0 | 0/8 | 9/16 | 1/4 |
| T005-first-two-capped/text_matrix | False | 7 | 0 | 0/8 | 9/16 | 4/4 |
| T005-first-two-capped/text_matrix | True | 7 | 0 | 0/8 | 9/16 | 1/4 |
| T005-lower-quartile/strict | False | 7 | 0 | 0/8 | 9/16 | 2/4 |
| T005-lower-quartile/strict | True | 7 | 0 | 0/8 | 9/16 | 1/4 |
| T005-lower-quartile/text_matrix | False | 7 | 0 | 0/8 | 9/16 | 4/4 |
| T005-lower-quartile/text_matrix | True | 7 | 0 | 0/8 | 9/16 | 1/4 |
| T005-minimum-local/strict | False | 7 | 0 | 0/8 | 9/16 | 2/4 |
| T005-minimum-local/strict | True | 7 | 0 | 0/8 | 9/16 | 1/4 |
| T005-minimum-local/text_matrix | False | 7 | 0 | 0/8 | 9/16 | 4/4 |
| T005-minimum-local/text_matrix | True | 7 | 0 | 0/8 | 9/16 | 1/4 |

Source-ID mapping is validated against exact text/bbox inventory equality; specialist IDs are mapped to the identical native word IDs. Cell center ownership is source-only and conservative. Text matrix equality is a weaker agreement observation, not a substitute for that identity check.

The PPLX G001 conjunction uses retained actual source-gate answers only as an offline routing simulation. All model calls were already charged. No fresh inference, cost saving, provider cache, end-to-end latency or generalization claim is made. Missing/failed gate outputs defer. No confidence is calibrated.

CPU preparation: `{"wall_seconds": 0.19088625400036108, "cpu_seconds": 0.189959689, "peak_rss_bytes": 83722240, "measurement": "/proc/self/status VmHWM (current executable); SELF CPU; serial math only; no sampling"}`. Raw source matrices/partitions and scored outputs remain ignored. Frozen agreement SHA256: `a5f4be7a656b300f384225dbae57c9209d4aabb863f634e4a2fc2107b9f0fdc6`.

Artifacts: `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/specialist-resolution-v1/agreement-v1`. Reproduce: `python -m bench.specialist_agreement --freeze --report`.
