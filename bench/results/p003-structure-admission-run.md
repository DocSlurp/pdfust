# Pure structure-admission runner

`bench.p003_structure_admission_run` consumes the frozen source-only admission pool and makes one model's retain/reject/unresolved decisions. Each invocation fixes the acquisition arm, geometry threshold, and image edge. OpenRouter is the only transport; capacities one and three are admitted, with three the default. No generation, OCR, TATR inference, model switch, inline retry, or baseline table credit occurs.

Root supplies two independent code maps: `--trusted-code` authenticates the admission pool's five archived files; `--source-trusted-code` authenticates the original ordinal baseline. The four executed geometry/source decoder helpers must also match current local code. The pool's unused historical `generalization_vision_regions.py` is authenticated archival provenance, never executed. Preparation authenticates original PDFs/source/results, replays all raw geometry through the current helpers, regenerates all 1,899 prospective bodies/images, and compares complete source, packets, PNGs, semantic bodies and original insertion-order wire hashes. All 216 candidates and 16 complete source snapshots are retained. No reference is read.

Only then does preparation create a fresh output and freeze current code, complete pool, all acquisition source/geometry trees, original baseline artifacts, selected candidate receipts, and exact encoded request bytes. All files receive hashes in `frozen.artifact_sha256`. The client factory runs after `frozen.json` exists. Root-only usage:

```bash
.venv/bin/python -m bench.p003_structure_admission_run \
  --input bench/results/pdf-master-artifacts/pipeline-p003/structure-admission-v3 \
  --trusted-code bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/structure-admission-v3.json \
  --source-trusted-code bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/b773d57.json \
  --output bench/results/pdf-master-artifacts/pipeline-p003/structure-pplx-detector05-rgb128-r0 \
  --model perplexity/pplx-decider-v1.1-27b \
  --acquisition detector --threshold 0.5 --image-edge 128 \
  --transport-concurrency 3 --run-hosted
```

Every admitted request is fresh (`replay=False`). The first transport/admission/settlement exception stops the remaining arm without more reservations. A malformed returned answer is retained and the next distinct candidate may proceed. Typed answers must contain exact question `q0`, exact retain/reject/unresolved probabilities, finite mass within the existing rounding tolerance, and a selected raw maximum. Raw probability and confidence fields are retained without calibration or a confidence gate.

Per-page output is atomic: if any of its candidates has a failed, malformed, not-attempted, or oversized-refused question, the entire page emits zero tables and all source IDs unresolved. Valid reject and unresolved choices do not admit their candidate; valid retains preserve the exact source-owned table. Conflicting positive geometry/source ownership is explicitly refused by the pure helper. No-candidate pages emit zero tables and all IDs unresolved. Source conservation is checked in every route. This cannot invent a word absent from the source inventory.

Independent verifier seam:

- `frozen.config.processor=p003_structure_admission`; `records`, original `manifest_sha256`, `pool` attestation, `source_trusted_code`, `baselines`, `code_sha256`, `artifact_sha256`, and `selected` are retained. Each selected item stores index/page/candidate/variant; its exact body is in `candidate-N-request.json`, exact transmitted encoding in `candidate-N-wire.json`.
- `candidate-N-response.json` retains every returned client receipt, and `candidate-N-result.json` retains status/model/raw typed receipt/error/usage/admission wait/client wall and CPU. `decision-results.json` is incrementally checkpointed.
- Each of the 16 `ID-result.json` rows has status `ok|error`, source, state, tables, unresolved_ids, admission_receipts, decision_results, decision_status (`evaluated|failed_closed|no_candidate`), source_conserved, model and pure_model. `ID-state.json`, `ID-structure.json`, and `ID.md` derive mechanically from those decisions. Failed pages keep their empty complete source-safe output and remain in the 16-page denominator.
- `report.decisions` and `decision_status_counts` distinguish retain/reject/unresolved/malformed_response/transport_error/not_attempted/no_question_refusal. `report.incremental_admission` holds resources, all-attempt charges, denominator 16, intended and valid-completed rates. These are explicitly incremental retained-evidence admission rates excluding OCR/TATR. Full-pipeline rates are undefined. Historical baseline metrics/costs appear separately in `historical_baseline_provenance`; no repayment or credit occurs.
- Preprocessing and request/assembly intervals separately measure CPU, wall and sampled RSS using `pipeline_run.Resources`; samples are retained in `preprocessing-resources.json` and `resources.json`. Missing attempt accounting leaves cost unknown.

CPU-only validation: real external-map authentication/reconstruction succeeded for all 16 pages and 216 candidates. Detector threshold 0.5/RGB128 freezes 19 questions for the selected model. Six runner tests plus seven pure-helper tests cover source ownership, exact wire order, all-input freezing, transport stop, abstention/rejection/refusal, malformed atomic page failure, and no baseline credit. No API calls, credentials or ledger access were used by the implementation agent.
