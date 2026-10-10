# Source-only micro relationship inputs

`p003_micro_relations.freeze(source)` retains the complete authenticated source
inventory locally and declares a bounded, deterministic sample of adjacent-word
cell, logical-row and physical-line continuation questions. It does not infer
table membership from physical bands. There are no answers or reference scores
in preparation.

`body(plan, pair_id, model, mode="micro")` produces one native choice question
with a text-only state capped at 768 UTF-8 bytes. Both complete literal words,
their exact global boxes, page size and normalized relative geometry are kept.
Only derived geometry features are rounded. The state explicitly declares that
pixels, other words and table topology are omitted. A complete pair exceeding
the cap is refused, never truncated. `mode="verbose"` retains the same target
facts with longer field names, definitions and provenance as the input control.
Each model is an independent arm; this helper has no provider escalation,
fallback assignments, transport client or retry mechanism.

`receipt(...)` reconstructs the exact request and validates the native typed
answer, exact question ID, choice menu and supplied probabilities using the
existing strict decision parser. Raw probabilities remain uncalibrated.
`outcomes(...)` distinguishes transport errors, malformed responses, valid
abstentions and valid nonabstaining decisions, rejects duplicate pair/mode
attempts and mixed models, and never treats a valid answer as verified
correctness. No receipt applies an assignment to the original source.

The authenticated ordinal DEV16 source-only preflight prepares 988 questions:
372 cell, 486 row and 130 wrap. Every selected question fits the cap. The
complete source-derived inventory contains 21,524 candidate questions; 20,536
are explicitly omitted by the predeclared maximum of 64 samples per page and
even ordinal spread across the full inventory. This is an available question
pool, not a proposal to submit 988 paid calls.

Micro states occupy 470–730 bytes (mean 536.6), versus 1,862–2,115 bytes
(mean 1,923.6) for the verbose control. Complete native micro bodies occupy
859–1,150 bytes (mean 936.6), versus 2,334–2,617 bytes (mean 2,405.5).
These measurements establish input feasibility only; model acceptance and
relationship quality are unmeasured.

The fresh artifact directory is
`bench/results/pdf-master-artifacts/p003-micro-relations-v3`. It contains exact
request bodies, complete immutable page source plans, explicit sampled/omitted
question inventories, original source authentication and code/artifact hashes.
The CLI requires the explicit ordinal baseline and separately supplied root
trusted-code map. It has no inference option. Resource measurements cover local
authentication and artifact preparation using process CPU and Linux process
lifetime peak RSS; no full-pipeline throughput is reported.

Validation: five focused tests cover same-fact controls, complete Unicode-word
capacity refusal, immutable-source authentication, strict answer parsing and
independent-model fail-closed outcome accounting. Ruff passes.
