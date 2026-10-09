# L008 natural OCR agreement gate

Implemented `bench/lowlevel_ocr_gate.py` and `tests/test_lowlevel_ocr_gate.py` in the isolated native worktree. The gate compares the actual supplied `native_words_text` with its visible crop; it does not repair OCR, regroup words or apply a production default. No provider calls, credentials or source uploads were used by the agent.

## Frozen source and payload

The explicit parent is `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/decisions/lowlevel-v1/ocr-alignment`. It supplies nine evidence records, nine manually inspected PNGs and separate review references. Preparation validates the existing evidence fingerprints and image hashes, copies source evidence, and freezes every request before opening the separate reference file. The retained published catalog is copied and hashed separately.

Models are PPLX, Luna, Clef-flash and Clef. Three labels are frozen per crop/model: `rgb128`, `rgb512`, `native`. RGB conversion composites onto white; Pillow LANCZOS only downsamples. Native keeps actual dimensions. There is no upscaling or fictitious 1200-pixel native image. Actual dimensions and image hashes are retained in variants and aliases.

Model state contains exactly a JSON `native_words_text` field and one inline RGB PNG. Only generic Choice instructions/criteria accompany it. No fixture ID, source filename/path, review transcription/note, gold label, task family, source glyph records or crop-selection diagnosis is included. Declared choices are `agree`, `disagree`, `unresolved`; this task is never remapped to join/split. Whitespace collapse is the only comparison normalization; case, punctuation, hyphens, Unicode and ligature codepoints remain distinct. Instructions explicitly allow abstention for unreadable/cut-off text or visually indistinguishable characters.

## Deduplication and actual dimensions

The real-source offline preview is `.scratch/council/lowlevel-architect/L008-preview`. It has 108 labeled configurations and **84 unique bodies**. Per root's steering, identical evidence is submitted once and retains every configuration alias; L007 independently handles deliberate cache-repeat transmissions. Several 512/native pairs coincide because the original crop is smaller than 512.

| Crop | rgb128 pixels | rgb512 pixels | Native pixels |
|---|---:|---:|---:|
| Edison name | 128×29 | 321×72 | 321×72 |
| Edison date | 128×17 | 492×66 | 492×66 |
| Edison Electric-Lamp agreement | 128×26 | 327×66 | 327×66 |
| Edison ELECTRIC LAMP corruption | 128×25 | 375×72 | 375×72 |
| Edison watermark | 128×59 | 360×165 | 360×165 |
| Edison department | 128×11 | 512×46 | 537×48 |
| Edison degraded body | 128×20 | 512×79 | 606×93 |
| IRS label | 128×7 | 512×26 | 639×33 |
| NICS numeric cells | 128×19 | 183×27 | 183×27 |

Six crops share their 512/native body per model, removing 24 duplicate transmissions. These aliases share one answer and one physical charge; they are not independent samples or evidence of a resolution gain. Verification reconstructs every body and image from frozen sources, checks source/catalog/reference bytes and validates alias dimensions/image identities and complete inventory.

## Reference interpretation and reporting

References remain source-aware single-review observations, not blind independently adjudicated gold. Seven crops enter the primary literal-reference comparison: three agreements and four disagreements. The date's `188O` versus reviewed `1880` label is separately tagged `contextual-zero-O`, since the year context supplies the digit interpretation and the pixel shape alone does not distinguish it. The degraded crop's transcription is unavailable; it receives no expected label or invented unresolved gold.

The local scorer uses the same native word text supplied to the provider, not raw callback concatenation. This preserves the NICS control's legitimate inferred separation between two ruled numeric cells. It compares only whitespace-normalized literal strings. Zero/O and unavailable observations remain separate from primary match counts. Primary abstentions, decisive comparisons and wrong decisive comparisons are reported separately; a low-resolution abstention does not establish a source extraction defect. Review hashes are checked again at scoring time.

Responses require exactly the q0 answer and the declared gate probability keys, valid finite [0,1] scores, a sum within the existing rounding tolerance and a declared maximum choice. Tied maxima become unresolved. Raw and normalized distributions are retained without claiming calibration. Failed/provider-error responses stop that model without automatic retry.

Each model/arm report retains actual alias dimensions, predictions, reference tier, primary matches/abstentions and contextual/unavailable observations. Aggregate cost and throughput deduplicate physical ledger indexes; configuration aliases never multiply charges or physical-page throughput. Positive provider costs precede labeled retained-rate estimates; incomplete costs stay unknown, with known partial subtotals and unsettled reservations separate. Raw provider result and shared ledger entry remain available for routing/cost review. No visible text replacement or PDF mutation exists.

## Hosted boundary and resource admission

Only root-owned `--run-hosted` execution constructs a shared `DecisionClient`. It uses replay-enabled retained-body reuse and a persistent `L008/` USD 5 wave, with at most 108 admitted physical calls (84 unique in this freeze), alongside the client's global campaign/cumulative caps. Unique body hashes, persistent `l008-wave.json` identity and normal ledger replay prevent duplicate paid sends across slices or interrupted checkpoints. A previous failed identical request is not retried.

Request bodies cap at 200,000 bytes; source/variant PNGs at 2 MiB, image dimensions at 2 million pixels and native text at 8,192 UTF-8 bytes. JSON source/catalog artifacts have explicit 8MB admissions. Shared ledger reads have a separate **64MiB** allowance because the existing global ledger exceeds the ordinary artifact limit. Per-call byte/token price forecasts screen against the normal reservation before transmission.

Preparation and execution separately record CPU/wall time and current-exec peak RSS (`/proc/self/status` VmHWM on Linux, no sampling/workers). Execution wall includes HTTP waiting; provider CPU/RAM is unmeasured. The offline real-source preview's preparation/write phase recorded 0.2927s wall, 0.2889s CPU and 36,823,040 bytes peak RSS (35.1MiB); final reconstruction verification follows that recorded phase. It performs PNG decode/resampling only, with no new PDF interpretation or inference. Provider latency, charges, quality and throughput remain unmeasured until root runs it.

## Root commands

```sh
.venv/bin/python -m bench.lowlevel_ocr_gate --prepare \
  --parent bench/results/pdf-master-artifacts/decisions/lowlevel-v1/ocr-alignment \
  --catalog bench/results/pdf-master-artifacts/decisions/langfuse/catalog-prices.json \
  --directory <new-L008-directory>
.venv/bin/python -m bench.lowlevel_ocr_gate --directory <L008-directory>
.venv/bin/python -m bench.lowlevel_ocr_gate --run-hosted --directory <L008-directory> --max-requests 4
.venv/bin/python -m bench.lowlevel_ocr_gate --run-hosted --directory <L008-directory>
.venv/bin/python -m bench.lowlevel_ocr_gate --report-only --directory <L008-directory>
```

Offline verification never instantiates the credential-bearing client. All request bodies, image variants, source evidence, references, manifest, results and report remain in ignored artifacts; only the two owned source/test files are committed.

## Verification

Fifteen fake-client tests pass, covering payload allowlisting, exact native dimensions/no upscaling, alias deduplication and metering, zero/O/unavailable separation, literal whitespace-only comparison, strict distributions/tie abstention, repeated slices/ledger recovery, changed review/alias refusal, persistent failed-reservation/call bounds and an existing ledger larger than 8MB. The preceding 14-test version plus OCR alignment/cache/glyph regressions passed 63 tests; the added large-ledger regression also passes. Focused Ruff and mypy checks pass. No root inference state, extension, provider configuration or frozen source artifact changed.
