# L007 bounded provider cache repeat probe

Implemented `bench/lowlevel_cache.py` and `tests/test_lowlevel_cache.py` in the isolated native worktree. This deliverable prepares and verifies source-selected bodies offline, runs only under explicit root-owned hosted opt-in, and reports repeated-request observations. The agent made no provider calls, read no credentials, and prepared no real source upload. Tests use generated fake images and a fake client/ledger only.

## Existing harness assessment

`bench/decision_cache_probe.py` already provides correct insertion-order `body_sha`, provider-error screening, cache usage, positive-charge-first pricing, separately retained token estimates and repeat trial records. Those functions are reused. Its existing selector is restricted to two bodies per model, 24 transmissions and a USD 0.50 wave; it also selects from successful prior responses. It cannot directly represent the requested source-selected 4 × 2 × 3 × 3 design or prefix-specific USD 5 accounting. No changes to that harness or shared DecisionClient were made.

## Freeze and source selection

L007 admits the primary L006 `kind=focus` manifest only. Models are PPLX, Luna, Clef-flash and Clef; arms are exactly `focus-rgb-128` and `focus-rgb-512`. Three representatives are chosen without targets, scores or response access: lexicographically first source ID after unique full-page pixel hash grouping, from character boundary, line ownership without interpreted drawings, and line ownership with interpreted drawings strata. The drawings distinction describes interpreted source data, not visibility or quality. All three strata must exist; absent strata refuse preparation rather than substituting scorer-selected examples.

Every one of the 24 selected singleton request bodies is copied byte for byte. Verification checks parent manifest lineage, source observation hashes, selected PDF hashes, complete model/arm/page inventory, exact shared-client serialization hashes, request byte metadata, copied catalog hash, and one inline RGB8 PNG with the exact longest edge. No prompt, image, routing setting, model parameter or body key order is changed. Gold/private target files are never opened. Changing the frozen parent or a selected source refuses the probe.

## Actual-call and reservation contract

Three submissions per body are labeled initial, repeat-1 and repeat-2, for a maximum of 72 transmissions. Each call uses the shared `DecisionClient` with `replay=False`, the existing default per-call reservation and the persistent global ledger. The `L007/` prefix separately enforces USD 5 and 72-call limits, including failed/unsettled reservations; the shared client's campaign and cumulative user caps continue to apply. The prefix is independent from L006's USD 10 wave. The client remains the only network and credential boundary.

Hosted execution requires a completed, successful parent result and a retained valid original provider response for each exact selected body. Missing/failed originals stay explicitly unattempted; their cost and pages/USD stay unavailable. The first probe transmission is additional to its original L006 submission and may already encounter provider caching. No cold-cache or cache-warmth promise is made. A failed probe response stops that model without automatic retry.

A persistent `l007-wave.json` beside the shared ledger binds the run to one manifest fingerprint, so changing output directories cannot reset the wave. Resume reconciles exact deterministic trial tags with retained ledger responses, preventing retransmission after a checkpoint interruption. This is ledger recovery of an already charged transmission, not a new call or ordinary local response replay. Existing failed/incomplete transmissions are retained and not retried. Unexpected local response replay is rejected.

## Evidence and reporting

Each trial retains original provider entry index/route, requested model, served model/provider, body hash, source page/arm, trial number, raw usage, cached-token counter presence/validity, provider-reported cost including original zero, effective pricing basis, separate catalog token estimate, latency, local replay/recovery flags and parsed choice. Reusing an original request artifact does not make repeated actual calls free. Distinct charged indexes are counted separately even when body hashes are identical; original L006 charges are excluded from L007 cost totals.

Positive provider charges take precedence. Zero/missing charges use existing published catalog/provider token-rate accounting; missing tokens/rates or invalid cache counters preserve unknown totals. Observed cached tokens with missing cache prices likewise yield unknown estimates. Reservations are retained separately from observed/effective spend. Missing cache counters remain unknown cache observations even where the existing estimator explicitly assumes zero for an unverified uncached component.

The report includes global and per-model/size/trial effective cost, successful page-choice observations per USD, summed HTTP pages/minute, process wall pages/minute, known partial subtotals, unknown-charge counts, reported-zero counts, positive-read observations and complete-triplet choice consistency. Consistency is not semantic accuracy or gold agreement. Raw routing fields remain available to assess provider/model changes before attributing latency/cost differences to caching. Incomplete triplets do not become consistency successes.

Execution records process wall time, CPU time and current-exec peak RSS (`/proc/self/status` VmHWM on Linux), without sampling or workers. HTTP waiting is included in process wall; provider CPU/RAM is unmeasured. Preparation records separate CPU/RSS resources and reuses frozen source bytes without rendering. Real provider cost, cache counters, latency, throughput and quality observations remain unmeasured until root executes the probe.

## Root commands

```sh
.venv/bin/python -m bench.lowlevel_cache --prepare --parent <L006-focus-directory> --directory <L007-directory>
.venv/bin/python -m bench.lowlevel_cache --directory <L007-directory>
.venv/bin/python -m bench.lowlevel_cache --run-hosted --directory <L007-directory> --max-requests 6
.venv/bin/python -m bench.lowlevel_cache --run-hosted --directory <L007-directory>
.venv/bin/python -m bench.lowlevel_cache --report-only --directory <L007-directory>
```

The second command verifies offline and makes no provider calls. Root should complete the selected L006 originals before hosted L007 execution. Request bodies, manifest, results and report stay in the selected ignored artifact directory; the single persistent wave checkpoint stays beside the global ledger.

## Verification and scope

Ten fake-client tests pass: all 72 transmissions repeat exact bodies; missing counters stay unknown; reported zero survives estimation; missing cache rate leaves partial totals incomplete; no successful parent response yields 72 unattempted rows; deterministic ledger recovery adds no duplicate call; failed reservations and 72-call admission persist; source/body changes refuse execution. Combined with previous OCR/glyph tests, 49 tests pass. Focused Ruff and mypy checks pass. No shared harness, production extraction, root extension, frozen paid artifact, hosted provider configuration or credential file changed.
