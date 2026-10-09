# A002 frozen candidate admission

The separate A001 source-only row assembler raises the borderless DEV exact
candidate ceiling from the native 2/12 to 12/12. Automatic acceptance would
also produce tables on 12/12 prose negatives. A002 tests admission of those
complete proposals rather than more table-presence gates.

The source-only native vector route retains four merged controls unchanged
with zero model calls. Each remaining page receives matched full literal
text/word-geometry evidence and a second arm adding the downsampled 512-pixel
whole source page. Source headings and explanatory prose remain visible.
Choices are `rolling`, `physical` when that complete layout differs,
`not_table`, and `unresolved`. Cell roles and header semantics stay unknown.
No model invents a cell or changes source words; each selection preserves the
complete source-ID inventory, including words outside table cells. These are
unaccepted experiment candidates and never alter default PDF extraction.

Two models ×24 pages ×two arms gives 96 frozen requests. The prepared manifest
is SHA256 `1606fcde633f3fe5b2c6a16d9476508e18644477bdd86dbefca020ed2f8f4cbb`.
Original A001 artifact SHA256 remains
`30044b381bb5d2cf3842a975f486b3f8c92c7c7a3b736efeecea52d6156dc75e`.
The run directory copies the exact source and candidate files, records their
hashes and verifies every frozen body before constructing the hosted client.
Private scorer references are opened only after every model body is frozen.

```bash
python -m bench.rolling_row_run \
  --directory bench/results/pdf-master-artifacts/evidence-designs/admission-v1 \
  --source path/to/source-evidence.json \
  --candidates path/to/rolling-v1.json
```

That command prepares only; it reads no keys and makes no paid call. Root can
run the already frozen directory with the authorized shared ledger:

```bash
python -m bench.rolling_row_run \
  --directory /home/dan/code/oss/pdf-master-designs/bench/results/pdf-master-artifacts/evidence-designs/admission-v1 \
  --targets /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/borderless-dev-v1/66c3cde77b110038/private-targets.json \
  --run-hosted \
  --report bench/results/rolling-admission.md
```

The runner holds the shared ledger's `run.lock`, applies a persistent $0.50
ceiling to the fixed `A002-rolling-admission/` tag prefix, and requires room for
the existing $0.30 per-call reservation before sending a new request. The
shared DecisionClient separately enforces the cumulative authorization. A
first network or response-validation failure stops that model persistently.
Failed identical calls are never retried. Successful frozen requests can replay.
An unsettled $0.30 failure may prevent another reservation under the $0.50
wave cap; the report retains every missing page in the original denominator.

Positive reported charges take precedence. Zero/missing reported charges use
`request_cost(entry, usage, catalog_rates)` and retain the original report plus
catalog provenance. Missing usage/rates stays unknown, and known partial costs
are not complete totals. Ledger reservations remain distinct. Retained call
records include provider/model metadata, usage, replay identity, elapsed HTTP
time and charge basis. CPU preparation and HTTP elapsed remain separate.

Preparation of all 96 bodies took 1.933 wall seconds, 1.923 process CPU seconds
and 53.35 MiB process lifetime peak RSS (perf_counter/process_time and Linux
VmHWM, sequential CPU, no sampling). Full artifacts are ignored; compact
Markdown reports retain wins, failures and unresolved pages together. No paid
requests were made during implementation.

The scorer reports every cohort's full 28 pages: 12 borderless positives, 12
numeric prose negatives, four native vector controls. Exact cells/spans,
intended slot values/words, source conservation, unresolved inventory, and
prose false admissions remain separate. Authored synthetic silver is not
independently adjudicated gold or real-world quality. Text grouping lacks
independent gold extractor IDs; neither source conservation nor confidence
alone proves correct cell ownership.
