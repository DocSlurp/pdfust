# P003 fresh strict representation and decision-image preregistration

Prepared 2026-10-10, without inference. Root owns all transmissions, provider/account admission, shared ledger reconciliation and the existing P003 research deadline. Preparation does not reserve or spend money.

## Implemented configuration

`python -m bench.p003_run` now accepts `--transcription-representation legacy|matrix_strict|atomic_cells`, default `legacy`. The config key is `transcription_representation`. Nonlegacy modes are admitted only for `vision_regions` and `hybrid`; source-candidate and other processors reject them before client construction. The ordinary YOLO crop arm is the first matched comparison. Legacy actual request bytes remain identical before and after provider pinning.

`generalization_vision_regions.transcription_request(model,url,viewport,max_tokens=...,representation=...)` rebuilds actual system instructions and the strict response schema. Model, completion admission, image URL and transport remain the existing controls. `transcription_parse` chooses the strict atomic-cell parser only for `atomic_cells`; matrix_strict uses the unchanged strict matrix parser. No repair is enabled. Page composition retains the complete atomic slot and non-overlap admission; legacy composition is preserved verbatim as a separately fingerprinted helper. Page, every proposal (including unrequested proposals), and retained request metadata explicitly record `transcription_representation`.

The pipeline freezes `p003_transcription_design.py` only for nonlegacy treatments, along with its existing transitive adapter/frontier dependencies. The generalization verifier requires exact authenticated local representation helpers, rebuilds instructions/schema/model/tokens/provider pin from frozen config, compares actual retained bodies and their wire-body SHA/byte counts, and selects the frozen parser/compose treatment. It checks treatment bodies even on failed pages. Legacy archives retain their existing body-verification compatibility; reviewed legacy composition uses unchanged AST content. Actual wire hashes use the rebuilt insertion order, because archived JSON files are formatted with sorted keys. Neither a rewritten artifact hash nor self-declared successful metadata substitutes for the frozen-config request reconstruction.

A separate opt-in `--transport-concurrency 1|3`, default one, records the config field only when explicitly three. Three constructs `P003ConcurrentClient(ROOT)`, freezes `decision_concurrent.py`, requires P003/OpenRouter/one local worker, and labels frozen/report throughput as contended parallel-arm measurements. Serial defaults omit these additional labels and remain unchanged. Root must first reconcile the shared ledger's reviewed concurrent policy and complete its serial control queue. No automatic policy edits or activation occur here. The latest concurrent implementation permits identical request bytes under distinct full P003 repeat tags without injecting nonces or changing matched bodies.

## Four representation arms

Primary arms are Haiku (`anthropic/claude-haiku-5.5`, exact serving pin `anthropic`) and Luna (`openai/gpt-6-luna`, pin `openai`), each with `matrix_strict` and `atomic_cells`. Serving pins match the existing frozen P003 controls. Use the same 16 DEV source pages, CPU YOLO Table/.25 proposals, retained detector order, 1536 detector edge, original rotation, 4096 render cap, 1024 JPEG90 continuous crops, completion limit 16384, workers one, and order seed 20261010. Root rerenders from frozen PDFs and checks crop/proposal/image hash equality against the prepared inventory before attributing differences to representation. No reference box or previously generated value selects a crop.

Preparation reused only frozen records and source-derived proposal/image descriptors, plus the actual source-image URL parts in the completed Haiku control's request bodies. It did not reuse completion text. A concrete ignored plan contains all four arms and 76 fully constructed, provider-pinned request bodies (19 per arm), with wire-body hashes, sizes and image inventories:

`bench/results/pdf-master-artifacts/pipeline-p003/transcription-plans-v1/plan.json`

Plan SHA-256: `ab1588d10329b7a5775f48d37f28694a4d98641738477dad0ef1c1545bfa1d0b`. Largest prepared wire body: 428,395 bytes, below the existing 750,000-byte admission. Prepared bodies are evidence artifacts, not transmitted requests or cache hits. The root run must still freeze reviewed current code and source/runtime before calls. An early atomic failure can leave later crops unrequested; nineteen is the frozen maximum per arm, not a promise of submitted/completed attempts.

Example fresh serial arm, using the root natural16 source manifest:

```sh
.venv/bin/python -m bench.p003_run \
  --manifest bench/results/pdf-master-artifacts/pipeline-p002/screens/natural16/manifest.json \
  --output bench/results/pdf-master-artifacts/pipeline-p003/screen-crops-haiku-1024-matrix-strict-r0 \
  --preset vision_regions --image-edge 1024 \
  --generation-model anthropic/claude-haiku-5.5 --generation-provider anthropic \
  --transcription-representation matrix_strict --repeat-index 0 --order-seed 20261010
```

The other three arms substitute the predeclared representation/model/provider/run ID from the plan. Root alternates model/representation order across fresh repeat blocks rather than calling a retained response a repeat. Initial block uses index zero; repeat one and two are separate fresh requests after reviewing cost/failure evidence, with identical treatment and source/image hashes. Report every table/owned-cell denominator and all sixteen pages, all abnormal or malformed completions, composition conflicts, charged failures, false positives, complete outputs, strict cells/tables, actual tokens, positive reported charges or labeled estimates, and elapsed/CPU/RSS. Atomic-cell verbosity is measured, not assumed beneficial. Parent concurrency labels stay separate from serial timing.

## Decision image sweep

Preregister gate edges **128, 256, 400, 512, 768, 1024**, crossed with PPLX decider, Clef Flash and Luna Decisions, all catalog-confirmed image-capable models. These are eighteen arms before repeats; text-only models must not receive an image-size pseudo-treatment. Exact model IDs and other settings are in the same plan. The initial primary control uses source-owned `gated_ordinal`, OCR300 whitespace/native source order, compact gate packet, region-specific instructions, no rolling row context, and fixed Haiku generation at edge512 with pin `anthropic`. Gate evidence stays partial and source-scoped as declared by the packet; missing OCR or packet admission refusal remains an error/abstention observation.

Freeze identical source page/proposal inventory and literal word packets before the sweep. Change only `gate_image_edge` within a model: keep generation pixels edge512, assembly method, source ordering, native/OCR acquisition, gate choices, packet style, instruction treatment, provider path, candidate order, generation model, completion limits and context policy fixed. Record both actual gate-image and generation-image hashes/dimensions; do not relabel a source viewport after resampling. Keep all pages and negatives, including no-proposal pages. Outcomes should include gate decisions and abstentions, actual request admissions/failures/token telemetry, downstream strict complete output and false positives, and complete charged cost. Catalog image support does not prove a provider consumed all packet/image evidence. Existing provider silent input truncation makes retained request completeness, declared omissions and actual token-limit behavior necessary observations.

A text-only/no-pixel control and other packet/context treatments are separate arms, not members of the image-size comparison. Optional rolling-context-present blocks require their own preregistered frozen source-only context and matched image inventory; do not combine them with the primary image sweep. The sweep changes gate decisions and can therefore change which downstream generation requests occur; report this mediated end-to-end effect separately from gate-call latency and cost. No score-derived localization, image size or threshold is chosen from these retained runs.

## Validation

233 focused CPU-only tests pass, and Ruff/strict mypy pass on the changed modules and new tests. The existing pinned Haiku screen independently passes frozen-code verification and exact structure replay (15/16 operational), without reference scoring. Source-owned ordinal-parser dependencies are required only for processors that use them; irrelevant inherited indices config does not block a vision-only freeze.

Local fake clients exercise the actual `_transcribe` transport path for both models and all three modes, including provider pins, request JSON archival, wire-body hashes/sizes, strict schemas, strict parser selection, atomic failures with raw response/calls preserved, and frozen-config verifier rejection after body/treatment tampering. Empty CPU-only fixtures verify helper freezing and missing-dependency refusal without constructing a real client. A fake concurrent constructor verifies max-three config selection and contended labels; invalid Gateway/non-P003 settings refuse before files or clients.

No hosted calls, credentials, ledger policy changes or protected heldout data were used. Raw plan bodies and PDFs remain ignored and local.
