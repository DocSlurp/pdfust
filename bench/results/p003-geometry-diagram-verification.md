# P003 independent geometry-diagram replay

The `p003_geometry_diagram` processor receives independent replay through
`bench.p003_geometry_diagram_verification`. It preserves only actually selected
complete crop candidates, without baseline or duplicate-candidate credit.
Operationally incomplete pages can retain independently selected disjoint crops
for full-denominator quality. Their operational status remains an error. Any
positive geometry or slot conflict rejects the full positive composition;
the verifier never chooses an arbitrary conflicting winner.

Supply `--trusted-code` for the outer run and `--incremental-trusted-code` with
exact keys `pool`, `selector`, `source`, `input-0`, and `input-1`. Each value is an
independently authenticated digest map. Retained authority-file bytes must match
these maps and the pool's original authority receipts. Embedded provenance maps
are not authority. Archive code bytes, copied historical artifacts and source
records remain hash checked. The pool is rebuilt from original authenticated
source/generation/selector evidence, including every synthetic diagram, complete
candidate pool, request template and encoded wire body, before response replay.

Each returned choice must have the exact model, request-byte hash, run tag and
unique ledger index. The native parser and chooser replay the raw response, with
probability/mass checks unchanged. Selected canonical bytes and audit receipts
must exactly match immutable candidates. Unresolved, malformed, transport-failed,
unattempted and duplicate/no-question crops contribute no tables. First transport
failure stops subsequent attempts; repeated ledger tags and alternative-model
entries are rejected. Accounting is independently recomputed from the retained
attempt inventory; missing attempts remain unknown rather than zero.

Every page state, structure, Markdown, coverage count, operational status and
report outcome count is rebuilt. The primary selected-crop quality adapter
retains `selected_partial_crops` for scoring, while separate operational failures
and coverage fields remain explicit. Full-pipeline rates remain absent.
Question/minute and question/APIUSD concern incremental selection only;
historical acquisition, generation and original selector costs remain provenance.

Synthetic source-geometry diagrams and the explicit evidence instructions both
change in this treatment. It is not a pure causal pixel-visibility control.
Generated candidate text is not source conserved. Mechanical offline fixtures
do not establish model quality, cost or throughput.

Fifty-six focused verification/report/progress tests and Ruff passed. All 33
outer mock archive files were independently checked against Git `80e98c8`.
The real source-frozen mock-v7 replay verified all 16 page outputs, with 13
operationally complete pages and unknown mock accounting kept absent. Earlier
mock-v5/v6 receipts were rejected for missing or incorrect transmitted-body
attribution. The corrected offline fixture reconstructed insertion-order bodies
and checked their exact retained wire bytes; it made no API calls. These are
mechanical contract checks, without a model-quality claim.
