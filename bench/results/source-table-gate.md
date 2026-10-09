# Source-only table-presence gate preparation

Frozen 28 original DEV pages: 96 image512 gate bodies (24 pages × two prompts ×
Luna/PPLX) and 4 separate zero-call native controls. No hosted call was sent. Gate state contains
only literal source OCR regions, geometry, display coordinates, image mapping and identical whole-page
pixels. Candidate matrices, row hypotheses, header policies, ownership suggestions and candidate choices are
absent.

G001 asks for semantic record/field relationships. G002 explicitly compares row relationships with
independently read prose columns. Both expose only table_present/not_table/unresolved. Their instructions
are generic and reference no fixture IDs, expected labels or model-specific behavior. Source inventories and
images are unchanged. Native controls retain the separate prior native-vector selection; they do not enter
gate bodies.

Labels and private targets were not loaded during preparation. No accuracy claim is made for fresh or
ambiguous pages; ambiguous cases must remain unscored. A later realistic corpus can use the same preparation
interface with its own frozen image admission directory and separate output path.

Actual gate provider costs must be reported independently by model and prompt, preserving reported charges
and labeled token estimates. Applying a frozen gate answer to retained admission outputs is an offline
routing simulation. Its combined cost is simulated gate plus retained admission accounting, not a fresh
provider cache, fresh cascade latency, or measured saving. Gate inference and admission inference latency
remain separate; skipped admission cost is a counterfactual only.

Preparation: 0.052s wall / 0.052s CPU,
888.7 MiB process-lifetime RSS. Measurement: perf_counter/process_time SELF; getrusage process-lifetime RSS; single CPU process; no children or periodic sampling.
Original OCR/render and prior admission costs are excluded. Manifest SHA256: `3bb0e4fe51bb083f6957de0be07fa1f88d3182f96a79611bfad75494a14eef13`.

Artifacts: `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/source-table-gate-original28-v1`. Reproduce with `python -m bench.source_table_gate --prepare --admission
<frozen-directory> --output <new-directory>`. Only source preparation is implemented; root owns any paid
execution and postfreeze scoring. No credentials, inference client, network, GPU, training or heldout access
is used.

The companion `python -m bench.source_table_gate_run --directory <gate-directory> --targets <private-targets> --report <report.md>` scores retained results without credentials. Add `--run-hosted` only for an authorized paid execution. It verifies every frozen hash before constructing the client, uses the shared ledger and persistent `G001-source-gate/` $0.50 prefix cap, stops each model after its first error, and records charged failures. The shared client also enforces the campaign cap. Actual gate costs and HTTP measurements are reported separately for every model/prompt; ambiguous references remain unscored. No offline cascade implementation is included.
