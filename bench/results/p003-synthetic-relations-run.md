# P003 synthetic relation hosted runner

`bench/p003_synthetic_relations_run.py` is opt-in and makes no request while
preparing. Root alone coordinates hosted arms and the shared ledger. Native
OpenRouter choice requests support all 14 registered decision models for text;
PPLX, Luna Decisions, Clef Flash, Clef and Clef Omni additionally admit images.
Modes are `text_geometry` or `rows_rules`; image edges are 0, 128 or 512, with
independent page/crop viewports. Viewport has no request effect when edge is0.
Gateway is not admitted. Concurrency defaults to3 using the existing
`P003ConcurrentClient` with its shared three-request limit and USD50 P003 policy;
serial1 uses the existing serial client. Each arm remains sequential over cases.

Preflight requires an **external** source authority: the six archived source
code basename/digest entries plus `source_frozen_sha256` equal to
`2ea7284702fa6499061325db7626ff174e977454ac2b21430c5d89541aed105f`.
Root must independently approve this map; the pool's own frozen hashes cannot
approve themselves. The runner verifies that source manifest, all archived code,
current pure replay dependencies, and every explicitly named artifact. It then
re-extracts all24 PDFs, complete literals/boxes, observed drawing segments and
exact pair mappings, re-renders all96 source image bytes and rebuilds all96
packet bytes. Missing/unmatched cases retain an explicit no-question refusal.
No generator `plans()` or `authored()` function executes in the runner.

Only source artifact paths under `pdfs/`, `sources/`, `packets/` and `images/`
are accepted. The runner never enumerates the pool or opens/copies the gold
sidecar. It copies explicit source artifacts plus approved archived code and
source authority so `authenticate(output/source, external_map)` can replay the
copied source evidence independently. All24 selected cases, canonical/native
wire requests and exact JSON transmission bytes freeze before client creation.
Actual image treatments declare their original display viewport, dimensions,
encoding and pixel mapping inside evidence. Crop treatments explicitly state
that peripheral rules may be clipped.

Fresh receipt validation requires exact requested model, tag and wire hash,
`replayed=False`, and one strict typed `q0` answer. Menu probabilities must
cover exactly same/separate/unresolved, be finite in[0,1], have raw mass within
the existing0.015+1e-9 tolerance and give the declared choice a raw maximum.
Extra fields, echoed names, repairs and probability renormalization are not
admitted. Raw confidence is preserved descriptively, not calibrated. Every
raw provider response is retained. Malformed answers continue to the next
distinct case; the first transport/admission failure stops subsequent cases,
preserving all24 rows as valid, malformed, transport-failed, refused or not
attempted. Client initialization failures also preserve the full denominator.
There is no retry, fallback, model/provider switch or source assignment.

Reports separate source/render/request preprocessing from sampled100ms parent
RSS and wall/CPU measurements of the attempt loop. Incremental API accounting
uses the existing shared positive-charge/estimate/reservation policy; missing
attempt accounting remains unknown. Rates are explicitly attempted or valid
nonabstaining **questions** per minute/dollar. Full-page extraction rates stay
`None`: there is one question/page, not complete extraction. No gold-based
quality is computed by the runner.

Verifier seams are pure `authenticate(pool, external_map)`,
`rebuild_request(pool, record, config)` and
`parse_response(record, actual_body, raw_result, config)`. Independent reporting
must authenticate the hosted code map separately, replay the source authority,
rebuild and compare canonical/wire/encoded requests, verify returned receipt
identity, then parse raw results. `frozen.json` retains `source_pool` authority
paths/hashes, complete `records`, all24 `selected`, exact current `code_sha256`
and copied-source/request `artifact_sha256`. Files are
`question-N-{canonical,wire}-request.json`, `question-N-wire-encoded.json`,
`question-N-response.json`, `question-N-result.json`, `results.json`,
`resources.json` and `report.json`. Original labels remain outside this tree.

Answerability must be conditioned on the actual evidence treatment. The
predeclared same/separate twins share target geometry; text geometry omits
ruling and cannot be assumed to recover the visually cued topology. Enriched
geometry or pixels expose different evidence. Six borderless cases are
deliberately underdetermined even with full pixels. Independent evaluation
should report author-label confusion separately from evidence limitations and
abstention, not claim24 uniformly recoverable answers. A stronger future
counterfactual would also reuse identical target/context literal strings across
paired PDFs while changing only visible separators; current unique opaque
literals avoid extraction ambiguity but do not make pixel-only causal claims.

The real source pool passed prepare-only CLI replay at
`pipeline-p003/synthetic-micro-preflight-v1`; its frozen request/code receipt
SHA256 is `bc80d2cea283b53a48f7edfc20e6a49b3a56a6004b99e2e47ef002443916bfd3`.
All24 rows are ready for the independently labeled PPLX rows/rules plus crop128
treatment, with exact wire sizes8,225–10,939 bytes and23 runtime code files.
No client was constructed. Standalone preflight CPU/RSS was not measured; the
hosted runner measures its own preprocessing separately when root invokes it.

Eleven tests use local generated sources and owned mock clients only. They
cover all14 text/five image configurations, complete replay with gold removed,
copied-source replay, external frozen-hash rejection, gold/path refusal, strict
probability failure modes, pre-client freezing, missing-accounting behavior and
malformed→valid→transport-error→21not-attempted control flow. Ruff and Mypy pass.

```sh
# No client construction by default; choose a fresh ignored output directory.
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=2 \
python -m bench.p003_synthetic_relations_run \
  --input bench/results/pdf-master-artifacts/pipeline-p003/synthetic-micro-relations-v1 \
  --trusted-code ROOT_APPROVED_SOURCE_CODE_AND_FROZEN_MAP.json \
  --output NEW_IGNORED_ARM_DIRECTORY \
  --model perplexity/pplx-decider-v1.1-27b \
  --evidence rows_rules --image-edge 128 --viewport crop
```

Root must add `--run-hosted` explicitly to construct the shared client.
