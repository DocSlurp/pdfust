# Synthetic shared-context multi-question treatment

The experiment asks four or eight independent local relationship questions in one native OpenRouter decision request. It reuses the unchanged, authenticated synthetic 24-page v2 source pool. This is **cross-page shared context**, rather than isolated server batching. Vercel's primary documentation explicitly distinguishes multiple questions about shared state from unrelated inputs that require separate calls. The treatment tests whether scoped multi-question prompts are usable, including their interference and throughput costs; it does not assert that providers isolate the questions. [Vercel decisions contract](https://vercel.com/i/ai-sdk-evaluation-to-decisions), accessed 2026-10-10.

The synthetic pool has one question per page. A natural same-page treatment would avoid this mismatch but require a separately frozen source-only relation inventory, with no existing synthetic labels. This experiment keeps the present dataset and exposes that tradeoff. It makes no balanced-label or counterfactual-twin promise to the model.

## Frozen policy

All 24 source records, PDFs, extracted literal IDs/boxes, observed drawings, stored packets and actual images are authenticated against the external v2 authority before any client is constructed. Runtime source copies use an explicit artifact whitelist: no gold sidecar is read, listed or copied. Grouping orders the opaque source IDs by `SHA256("p003-shared-context-source-order-20261010-v1/" + source_id)`, with source-ID tie breaking. No labels, twin metadata, model outputs or generator layout parameters enter this selection. Every source ID occurs in exactly one group; there are six groups of four or three groups of eight.

The native body contains a plain string `state`, holding `questions.q0` through `questions.qN`. Each entry preserves the complete original `text_geometry` or `rows_rules` packet, including every literal word and physical ID. Each typed choice question has the unchanged same/separate/unresolved criteria, the original relationship instructions, and an additional explicit notice to use only its own scoped entry. This notice and qN positions are part of the treatment, so measured differences are not attributed solely to amortized request overhead. The provider may still use other entries. State beyond 128 KiB or a whole request beyond 750,000 bytes refuses the complete group; no word truncation or regrouping is allowed.

All 14 registered decision models are eligible independently. This initial treatment is text only. For each model, two evidence modes and two group sizes create four arms: 56 arms and 252 requests across the full screen. The existing single-question arms provide source-ID matched controls. Native probabilities remain raw and uncalibrated; no mass normalization, answer-name stripping or partial repair is applied.

Clef and ClefFlash have a previously recorded catalog warning about silently discarded context around 2,000 input tokens. Larger shared states can aggravate that risk. Frozen UTF-8 state sizes, complete word counts, omitted-word counts and returned usage remain available; byte counts are not inferred token counts and do not establish which evidence the provider retained. A context failure would remain a result of this treatment rather than silently selecting a shorter prompt.

## Operational and verification rules

`p003_synthetic_relations_multi_run.py` prepares by default. Root alone opts into `--run-hosted`. The shared P003 client uses one explicit model, concurrency 1 or 3, the existing ledger/circuit breaker and a USD 0.30 reservation per group. There is one fresh attempt per group, no retry, provider/model fallback or source assignment. A transport failure stops subsequent groups. A malformed or incomplete answer envelope rejects **every** question in that group, then may continue to the next distinct group. Source or capacity refusal also leaves every group member refused. All 24 individual outcomes survive these failures.

One financial entry belongs to each attempted group request. It is never duplicated into per-case receipts. Reported charges, unresolved reservations, known partial amounts and unknown totals retain their existing distinctions. Rates count attempted requests and attempted/classified questions separately. Page/table extraction rates are `None`. Local authentication/rendering/freezing CPU and lifetime RSS are separate from the sampled client-loop resources and service rates.

The independent evaluator authenticates all archived runtime bytes against an external map and requires exact current bytes for executed pure replay helpers. It reconstructs full grouping, literal packets, instructions, canonical JSON, encoded native wire bytes, fresh model/tag/request receipts and all atomic outcomes. Updating self-recorded request hashes cannot bypass source replay. It recomputes shared financial totals once per request and rates from retained resources. Only after all arms are independently verified does it open the separately authorized generator-label sidecar.

Scoring retains all 24, the 18 visually cued cases, the six indeterminate cases and each relation kind. Twin reporting calls equality **identical local evidence**; co-context and qN positions can differ, so the single-question identical-request deterministic bound is not applied. Optional independently verified single-question controls expose matched choice changes and raw-probability deltas, without claiming that stochastic repetition, instruction changes or financial contention are controlled.

## Reproduction

```sh
python -m bench.p003_synthetic_relations_multi_run \
  --input /explicit/synthetic-micro-relations-v2 \
  --trusted-code /external/synthetic-micro-relations-v2.json \
  --output /new/arm --model perplexity/pplx-decider-v1.1-27b \
  --group-size 4 --evidence rows_rules --transport-concurrency 3
```

Add `--run-hosted` only in the root-coordinated queue. Before launch, root must create an independent Git-authenticated runtime map for all names in `CODE_FILES` (25 files). The request protocol is `p003_synthetic_relations_multi.request(records, config)`; strict atomic parser is `parse(records, actual_body, raw_provider_result, config)`. Frozen selections map each `case_ids` entry to the corresponding `question_keys` entry. Requests, responses and result receipts use `group-N-*` filenames. `report.json` retains complete `groups` and flattened `results`; charges stay in `report.charges.entries` once per request.

```sh
python -m bench.p003_synthetic_relations_multi_eval \
  --source-pool /explicit/synthetic-micro-relations-v2 \
  --source-trusted-code /external/source.json \
  --run /completed/arm --runtime-trusted-code /external/arm.json \
  --gold /evaluation-only/private-gold.json --gold-sha256 EXACT_SEPARATE_SHA \
  --output /new/evaluation
```

Optional repeated `--single-run` and `--single-runtime-trusted-code` arguments independently authenticate equal-model, equal-evidence, text-only controls before labels are opened. The pure comparison seam is `compare(single_verified, multi_verified)`.

## Validation and source-only preparation

Four prepare-only PPLX arms are retained in the ignored main workspace at `pipeline-p003/synthetic-shared-context-preflight-v1`. They include group sizes four/eight and both evidence modes, complete 24-case inventories, exact request bytes and source/runtime snapshots. No client, credentials, hosted calls or label reads were involved. `summary.json` records the exact arm freezes, packet sizes and local CPU/RSS measurements; its runtime archives precede any root merge and are preparation evidence, not permission to launch a hosted arm using unapproved code.

All four real-source preflights were ready: 18 shared requests in total, each arm retaining all 24 cases. Geometry-only shared states were 3,794–3,801 bytes for groups of four and 7,535–7,540 bytes for groups of eight. Rows/rules states were 20,621–22,266 and 42,659–43,843 bytes respectively. Request bodies ranged from 8,014 to 56,056 bytes. Preparation took 2.369–2.558 seconds of wall time and 2.316–2.516 seconds of CPU time per arm. Unsampled parent lifetime RSS peaked at 119,204 KiB; this includes imports and previous arms, not isolated per-arm memory. The sequential parent used OMP/BLAS/MKL one thread and Rayon two threads. Exact hashes and individual measurements are retained in the ignored summary.

Fourteen mock/replay tests cover complete literal preservation, order independence, exact envelope/malformed behavior, continued distinct groups then circuit stopping, shared charge/reservation accounting, no label access during verification, request/probability/financial tamper rejection, operational denominators and matched-control comparison. The combined synthetic regression suite passed 41 tests; targeted Ruff and type checks pass. No hosted correctness or throughput result is available from this preparation.
