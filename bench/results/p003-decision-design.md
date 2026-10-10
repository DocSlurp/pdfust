# P003 rolling row-boundary decisions

This isolated source-owned experiment tests one specific remaining failure:
wrapped cell contents split into several physical rows by provisional assembly.
It does not generate tables from scratch or transcribe table text. No hosted
request has been made by this branch; natural-document quality, repeatability,
and provider cost remain unmeasured.

P002 found that gate-only row context helped a source-owned ordinal control,
while directly adding row context to matrix generation lost cells and increased
cost. The next mechanism therefore makes the decision surface explicit and small:
three scores per existing row boundary, with no cell strings or word-index matrix
in the answer. Several wrap boundaries can change together, unlike the existing
single-operation repair menu.

## Evidence and decoding

`bench/decision_p003_boundaries.py` freezes the complete admitted source word
inventory, literal strings and boxes in original order. Provisional cells retain
ordinal references to those words. Each boundary references a six-row rolling
window, observed occupied columns, signed inter-row gap, and repeated left/right
edge shifts. An optional bounded inline image can accompany the same packet.
The window contains the previous two rows, both boundary rows, and the following
two rows when available. These mechanical observations do not establish a table
or correct an OCR string. Dataset filenames, families, labels and gold are absent
from generation; tests establish invariance to added reference metadata.

The answer is an exact-ID object:

```json
{"t0b0":{"split":0.1,"join":0.9,"unresolved":0.0}}
```

Every frozen boundary must be present exactly once. Duplicate JSON fields,
non-finite numbers, extra fields, unfinished completions, refusals and incomplete
inventories fail atomically. Scores must sum to one within 0.001; they are
uncalibrated model scores, not probabilities of correctness. Default admission
requires join >= 0.8 and a >= 0.25 margin over both alternatives. Unresolved or
low-margin boundaries retain their original split.

A join also needs downward physical progression, a signed gap between -0.5 and
1.5 median word heights, a shared edge within one height, and following occupied
columns contained in the preceding occupied-column set. A dynamic program selects
jointly compatible joins maximizing join-minus-split score. It limits each logical
row to three physical rows and keeps at least two logical rows in each table.
Qualified joins blocked by those global constraints remain explicitly audited.
An exhaustive independent partition oracle checks the decoder objective on every
availability pattern of a seven-row example.

The decoder concatenates the existing cell source-ID lists in original row order
and rebuilds each value from the unchanged literal strings. Existing native vector
grids and every table with a merged span are protected. The table inventory,
column count, outside-word ownership and protected topology are preserved. Exact
source ownership and rectangular span tiling pass the existing strict validator
before any result is returned. Replay checks the complete frozen menu against the
current source/state, so modified or stale evidence cannot silently apply.

Source conservation establishes literal ownership, not correctness of grouping,
reading order, pixel visibility, or OCR coverage. This mechanism cannot recover
missing OCR strings, admit a missed detector region, reject a false-positive table,
split an already merged logical row, repair column placement, infer merged spans,
or resolve right-angle rotated continuations. Full table transcription remains a
separate provenance path when source text is missing. Long wraps, sparse genuine
records and multi-column wraps are deliberate risks to measure on fresh DEV data.

## Integration seam

Use the helper after the existing source-owned ordinal/geometry assembly and its
semantic table gate. Bypass inference when `menu["boundaries"]` is empty. Root
continues to own requests, reservations, pricing, retention and complete-page
admission. The helper performs no network activity and reads no credentials.

```python
from bench.decision_p003_boundaries import apply, parse, request

menu, body = request(source_page, validated_state, model, inline_region_image)
# Root sends body through its authorized hosted client and retains the full result.
answer = parse(retained_provider_result)
updated_state, audit = apply(source_page, validated_state, menu, answer)
```

`body` is a standard chat-completions request with strict JSON schema. Persist
`menu`, `body`, the complete provider result/errors, `answer`, `updated_state` and
`audit` together. Do not replace failed provider/page attempts with a synthetic
success. A paired unchanged-state control and several identical-input fresh runs
are needed before selecting thresholds or claiming a natural-table improvement.

Bounds are 4,096 retained words, 16,000 aggregate source-ID/text characters, 4,096
aggregate table slots, 128 complete boundaries, 256 KiB encoded evidence, 32 KiB
response JSON, and 16 MiB inline image URL. Complete evidence is refused rather
than silently truncated. Any need for chunking must be addressed by the root's
existing source-region pipeline, not by selecting reference-favorable rows.

## Offline validation and measurement

`35 passed` across new decision tests and existing repair/stitch controls:

```bash
/home/dan/code/oss/pylopdf/.venv/bin/python -m pytest \
  tests/test_decision_p003_boundaries.py tests/test_pipeline_repair.py \
  tests/test_pipeline_row_stitch.py -q
/home/dan/code/oss/pylopdf/.venv/bin/ruff check \
  bench/decision_p003_*.py tests/test_decision_p003_boundaries.py
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.decision_p003_offline --iterations 100
```

The standalone offline entry creates only synthetic PDF-source row evidence,
uses clearly labeled fake scores, and retains complete inputs/request/fake-answer/
output/audit under ignored
`bench/results/pdf-master-artifacts/p003-decisions/offline-replay.json`.
It does not read a PDF corpus or make provider requests.

On Linux 7.2.5 x86_64, CPython 3.14.7, one serial CPU process, 100 maximum-boundary
replays took 1.0561 s wall and 1.0526 s process CPU (99.67% utilization), or about
10.56 ms/replay. Post-exec peak RSS was 22,588 KiB. The 129 physical rows had 128
boundary decisions and became the expected 65 logical rows. JSON evidence and
answer sizes with the measurement encoder were 34,373 and 7,058 bytes. This is a
synthetic correctness/resource smoke measurement, not a natural-quality or
production-throughput claim. Timing excludes Python startup and module imports;
RSS includes the post-exec process lifetime. There are no workers/subprocesses.

Elapsed/CPU measurements use `perf_counter`/`process_time`. Peak memory uses Linux
`/proc/self/status` `VmHWM`, an OS high-water counter with no polling interval.
`getrusage(RUSAGE_SELF).ru_maxrss` was also retained: it reported 422,964 KiB even
for a plain tiny Python process whose post-exec VmHWM was 10,592 KiB. The tool
launcher appears to preserve pre-exec RSS in that counter; it is labeled separately
and is not presented as the replay peak. Hosted inference, model quality and
provider charges are unmeasured/not applicable here.

## Native typed decision transport

`bench/decision_p003_native.py` adds the preferred native decision-endpoint arm.
`decision_batches(page, state, model, url=None, max_questions=16)` returns the
original complete frozen menu and a list of bodies in the existing pipeline
`model/state/questions` format. Every body has at most sixteen exact boundary-ID
questions with `type="choice"` and `split/join/unresolved` criteria. Its shared
state is literal text followed by an optional high-detail inline image. Text
contains only the union of the batch's complete local rolling windows and their
relevant words, with original global word indexes retained. It does not resend
the whole table inventory or complete page word evidence on every call.

```python
from bench.decision_p003_native import decision_batches, apply_decision_batches

menu, bodies = decision_batches(source_page, validated_state, model, inline_region_image)
# Root reserves and retains each request/result through the shared hosted client.
# Submit no calls when bodies is empty. No intermediate state is materialized.
updated_state, audit = apply_decision_batches(
    source_page, validated_state, menu, bodies, retained_provider_results
)
```

`parse_decision_batch(body, result)` validates actual typed responses of the form:

```json
{"answers":{"t0b0":{"type":"choice","choice":"join","probabilities":{"split":0.10,"join":0.89,"unresolved":0.00},"confidence":0.123}}}
```

It checks exact batch IDs, exact declared probability options, finite [0,1]
values, and an argmax declared choice. As in `decision_choice`, independently
rounded probabilities may differ from unit mass by at most 0.015 + 1e-9. The
parser normalizes that admitted rounding drift for the unchanged decoder while
retaining `raw_probabilities`, `normalization_delta`, and `raw_confidence`.
Confidence is provenance only and never alters selection. No scores are claimed
calibrated. The full batch union must cover every boundary exactly once; duplicate
batches, modified questions/evidence, missing responses, or any failed response
raise before decoding. Original inputs remain unchanged and no partial successful
state is returned.

The chat control remains available, now wrapping its score mapping under the sole
`answers` field so the shared client's answer-count accounting can read it. Its
strict schema and parser require that envelope. Chat responses retain the tighter
0.001 score-mass tolerance; native rounded responses are normalized before they
reach the same decoder.

Five additional native-transport tests cover sixteen-question batching with local
evidence, actual typed choice payloads, rounding/raw-confidence provenance,
atomic failure, exact IDs, question limits, modified evidence, native-grid bypass,
gold invariance, and the chat `answers` accounting envelope. Together with the
original boundary tests and existing repair/stitch controls, **40 tests pass**.
No inference or additional profiling was performed for this transport follow-up.
