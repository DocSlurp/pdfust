# P003 independent synthetic relationship evaluation

The corrected real v2 preparation passed with no client construction or hosted
calls at `pipeline-p003/synthetic-micro-preflight-v2`. All 24 requests are ready;
wire sizes are 8,230–10,834 bytes for the PPLX rows/rules crop-128 treatment.
The first image state part is a plain string. Frozen preflight SHA256:
`d354cc268495940accef4c461487b006a71f3eaecb0ea653393163a3827f9529`.
This is request preparation, not a model-quality result.

`bench/p003_synthetic_relations_eval.py` verifies explicitly supplied hosted
directories with external source and runtime code authorities. Source authority
pins the six source code files and the immutable v2 source manifest. Runtime
authority independently approves all archived runtime files; exact current
equality is required only for the pure source/request/parser helpers executed
by replay. Unrelated changes to current detector dispatch code neither mutate
historical archives nor weaken request replay. Archived code is never executed.

Verification replays complete source evidence, checks copied source/code bytes,
rebuilds every canonical/native wire body and exact transmission bytes, and
checks all 24 saved outcome rows against the complete report. Each raw returned
receipt must match the reported receipt. Fresh valid admissions require exact
requested model, tag, request hash and strict single-question probabilities.
Malformed responses are reclassified from actual raw content, and the first
transport error must stop later attempts. No missing response receives credit.
Reported choices or probabilities cannot override the raw parser.

Retained financial entries must correspond to exact attempted tags/model/body
hashes, contain no duplicate attempts, and match returned receipts. Aggregates
are rebuilt from those entries, preserving positive reported charges, reported
zero values, labeled effective accounting, missing charges and unresolved
reservations separately. Missing attempt accounting remains unknown. Question
rates are recomputed using reported runtime wall time and effective costs;
sampled RSS peaks are checked against retained resource samples. Timings and
provider charges remain reported measurements, not cryptographic proof of
provider execution. The verifier does not read the shared ledger or make calls.
Complete-page and complete-pipeline rates remain absent.

Only **after every requested run verifies** does the separate evaluation path
open the explicitly supplied private gold sidecar, requiring its independently
supplied SHA256. It checks the source manifest identity, all 24 case identities,
PDF/source hashes, literal-to-ID mappings and generator membership receipts.
Opposing labels within each counterfactual pair are validated. The six
indeterminate cases must agree with the source-frozen identical-rule receipts.
The model-input runner never receives or reads this sidecar.

Scores preserve all 24 cases, with separate 18 visually cued and six
indeterminate partitions, per-kind counts, confusion, valid nonabstaining
answers, abstentions, malformed responses, transport errors and unattempted
cases. Strict author-label fractions retain the full intended denominator;
conditional decisive fractions are separately named. These are hidden
construction-label agreements, not a claim that every label was recoverable
from the supplied treatment. Per-arm configuration retains model, evidence,
image edge and viewport. Twins additionally report choice/raw-probability
consistency, abstention, author-label matches and exact request-byte equality.

Evidence-conditioned controls use actual request hashes. Deterministic identical
answers can match at most one opposing label per identical-evidence pair:
12/24 for plain text geometry, and at most 21/24 where rules or pixels distinguish
the nine cued pairs. A stochastic realization can fluctuate around the hidden
label expectation, so these bounds must not be presented as absolute ceilings
on sampled outcomes. Appropriate abstention has a separate interpretation.
No synthetic hosted quality has been evaluated in this implementation task.

Exports are `source_context`, `verify_run`, `load_gold`, `score` and `evaluate`.
`evaluate` receives parallel explicit lists of run directories and runtime maps,
verifies them all before reading gold, and writes independent verification/score
artifacts plus a summary. It does not enumerate queues or protected corpora.
Ten tests cover gold isolation, full and partitioned denominators, per-twin
controls, archived code and request tampering, raw probability alteration,
reported outcome/financial alteration, abstention/error handling and unknown
accounting. Ruff and Mypy pass; all transport in tests is owned in-memory mocks.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=2 \
python -m bench.p003_synthetic_relations_eval \
  --source-pool bench/results/pdf-master-artifacts/pipeline-p003/synthetic-micro-relations-v2 \
  --source-trusted-code bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/synthetic-micro-relations-v2.json \
  --run EXPLICIT_COMPLETED_ARM \
  --runtime-trusted-code INDEPENDENT_ARM_CODE_MAP.json \
  --gold bench/results/pdf-master-artifacts/pipeline-p003/synthetic-micro-relations-v2/private-gold.json \
  --gold-sha256 db0f5953579379fbf74ffba9faebf8c6acad1e622b70c4fae389d137d357e2ca \
  --output NEW_IGNORED_EVALUATION_DIRECTORY
```

Repeat `--run` and `--runtime-trusted-code` in matching order for additional
independent arms. Gold is permitted only in this scoring step; do not route
scoring results back into the immutable v2 source or active model prompts.
