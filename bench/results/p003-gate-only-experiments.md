# P003 fresh admission conditional on frozen generation

Prepared CPU-only on 2026-10-10. `bench.p003_gate_run` is a standalone opt-in
runner. Root supplies the coordinated serial or three-way transport client;
tests inject a fake client. There is no default inference and no repeated OCR,
source extraction, detector work, or generation. OpenRouter retains its existing default transport; explicit Gateway treatment
uses a separately frozen serial route.

The authorized baseline is
`pipeline-p003/screen-ordinal-ocr300-512-r0`; the independent root-approved code
map is `pipeline-p003/trusted-code/b773d57.json`. The runner requires that map,
authenticates every archived code file, verifies the necessary ordinal/source
ownership dependencies are present, checks source PDF hashes, and replays each
complete source/region state, composition, and exact Markdown. It retains the
whole intended inventory, including baseline errors. It copies all original
outputs, available request/response files, and code into `baseline/`, freezes
their hashes, and retains the immutable historical report. The self-recorded
trust-map hash is provenance; evaluators must receive the independent trusted
map separately.

The baseline contains 16 complete pages and 52 regions. Its existing policy
bypasses 34 residual or incomplete-context regions. The remaining 18 generated
regions receive fresh table/prose/unresolved gates. The runner independently
reproduces these bypasses from source fields and verifies that frozen bypass
states equal native states. It keeps the original generation state for table;
prose/unresolved selects exactly the existing no-table c0 alternative, preserving
all local source IDs. No other hypothesis generation or ranking is necessary.
A failed or missing admission leaves an explicit pending receipt and makes the
complete page fail atomically. It cannot silently inherit a positive baseline.

For each eligible region, the body uses the literal frozen regional source,
declared packet style, optional mechanical row context, frozen instruction
variant, independent gate edge and encoding. Defaults are compact/region/RGB512;
source packet scope is explicitly the supplied region, not the whole page.
Text gates perform no raster rendering. Generation pixels and outputs remain
historical provenance. Full source words/geometry/region plans are retained
locally even when a packet explicitly samples or omits text.

Clef Flash and Clef Workers AI receive a documented provider-state-truncation
risk flag: their provider may silently discard state text after roughly 2,000
tokens. The runner records literal evidence UTF-8 bytes, supplied/omitted word
counts, source/evidence/body hashes, raw reported token usage, and the risk flag.
It makes no conversion from characters to inferred token counts and no claim
that compact evidence necessarily reaches the model intact. The public provider
contract is documented in `p003-model-catalog.md`.

## Entry point and replay contract

Root can invoke `python -m bench.p003_gate_run --baseline <ordinal-dir>
--trusted-code <independent-map.json> --output <fresh-dir> --run-hosted --model
<exact-id> --gate-image-edge <128|256|400|512|768|1024> --gate-image-mode
<rgb|grayscale8|rgb_palette16> --gate-packet <style> --gate-instructions <style>
--transport-concurrency <1|3>`. `--text-gate` and `--gate-row-evidence` are
independent optional treatments. Three-way transport is labeled contended;
processing within one arm remains serial. Every request uses fresh P003 tags,
the existing USD50 wave reservation check and root client's global policy.

Pure seams for independent verification are `gate_request(region, config, url)`
returning actual body plus evidence metadata, `fallback_state(source)`,
`bypass_reason(region, baseline_config)`, and
`compose_selected(original, states, source_order)` returning complete state and
Markdown. The verifier must derive the prompt and selection from copied source
and frozen choices, rather than trust archived prompt strings or state hashes.

`frozen.baseline` contains `copied_directory`, `file_sha256`, `original_config`,
`source_order`, and `trusted_code_manifest_sha256`. `frozen.records` contains
source fields only. Current code and extraction runtime fingerprints are frozen.
`report.baseline_report` preserves historical timings, generation costs/calls,
and detector/OCR provenance. `report.incremental_gate` contains fresh all-attempt
`ledger_attempts`, `entries`, `cost_bases`, reported/effective/partial costs,
unresolved reservations, and `metrics`. Top-level pipeline pages-per-minute and
pages-per-dollar are null. These measurements are incremental and conditional
on frozen generation, never a new complete-pipeline cost or throughput result.

Each result's `calls` are fresh gates; `historical_calls` are separate. Region
receipts include original/fallback/selected state hashes, original route,
explicit admission/bypass reason, request index, image and evidence metadata,
reported usage, and selected state. Pending/failed receipts contain no selected
state. Bodies are `<page>-request-<step>.json`. Exact provider response bytes,
including a charged attempt whose parsing failed, are copied from this run's
ledger-associated files to `<page>-response-<step>.json`; their receipts are in
`report.fresh_response_artifacts`. Original baseline response files are copied
where the historical archive already retains them.

## Offline diagnostics

The independently trusted 16-page baseline passed complete source/context
replay. With mocked all-table gates, all 16 complete structures and exact
Markdown outputs matched the baseline. With mocked all-prose gates, the 18
eligible states became c0 while the 34 bypasses retained their original states;
all 16 complete outputs still conserved source. These are deterministic software
diagnostics, not model quality results or paid decisions.

One contended CPU observation measured authentication at 0.644s wall/0.624s CPU;
mocked all-table rendering/body/composition at 1.896s wall/1.877s CPU, and
all-prose at 1.717s wall/1.712s CPU. Process-lifetime high-water RSS was
308,104 KiB via Linux `resource.getrusage`, with no sampling and no isolated
allocation-delta claim. Root paid workers were concurrently active. The ignored
artifact `pipeline-p003/gate-only-diagnostic/diagnostic.json` records source
baseline/trust-map hashes, complete output comparisons, per-page result hashes,
and timing scope; SHA-256
`5de1f4b0fc0ff144db415b29c0490062ed49210411b7b9a86dd7d144d96aa968`.

Twenty in-process tests cover positive/negative/abstained selections, atomic
transport failure, no repeated extraction/generation, exact c0 fallback,
independent trust refusal, malformed complete state refusal, baseline failures,
source-policy bypasses, no rendering for text gates, unknown/reserved cost
separation, frozen copies, explicit opt-in, and exact response byte preservation.
No subprocess or process-group cleanup occurs.


## Serial Gateway follow-up

`--gate-provider vercel` admits exactly `liquid/d1` or text-only
`convaiinnovations/laya`/`convaiinnovations/laya-free`, with transport concurrency
one. The existing authenticated `p003_transport.gateway_wire` preserves the
same literal packet and rubric. d1 uses documented native `/v1/decisions` input
text/image parts and question arrays. Laya uses TypeSafe
`/typesafe/v1/systemone`, literal string state, and Boundless-only routing.
Laya image treatments and Gateway concurrency three are rejected before output
creation. OpenRouter's default config omits `gate_provider`, and its bodies
retain their existing bytes.

The runner constructs only the selected Gateway client when no client is
injected; it does not construct an OpenRouter client. Gateway calls use the
existing shared persistent ledger, serving-specific prices, deadline/budget
policy, fresh tags, and no replay/retry. A per-arm circuit breaker stops calls
after a transport, admission, or typed-answer failure. Exact translated wire
bodies are archived; `evidence.request_sha256` remains the body SHA, while
`request_identity_sha256` additionally binds the serving endpoint. Original
provider response bytes remain preserved separately from normalized answers.

`frozen.gateway_pricing` records the exact client catalog and authenticated
endpoint before calls, and `gateway-prices.json` is bound by
`frozen.gateway_pricing_sha256`. The existing accounting gives positive
provider-reported charges precedence; missing or zero charges use only the
Gateway-specific serving rates/tokens where complete, otherwise reservations
remain unresolved. The tests use supplied fake clients/catalogs, never keys or
network requests. The pure verifier seam
`parse_gate_response(actual_body, raw_provider_response, config)` dispatches
only documented OR chat/native or Gateway TypeSafe/native normalizers and
strict existing choice parsers. Tests exercise d1/Laya wire/body identity,
raw-envelope decoding, serial circuit breaking, refusal of unsafe combinations,
Gateway catalog freezing, and isolation from OpenRouter transmission.
