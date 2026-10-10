# P003 factorized header decisions

`bench.p003_header_decision_run` is an opt-in root-launched experiment over the
authenticated `header-packets-v4` pool. It asks four independent table-header
questions with 3/3/3/5 complete alternatives. Each alternative preserves the
original generated body strings and table box. The hypothesized header spans
are proposals, not established physical boundaries. This experiment does not
conserve an extracted source-word inventory (`source_conserved: false`).

Each arm declares one model, `full` or `local_header` evidence, and image edge
0, 128 or 512. Jev is text-only; PPLX, Luna Decisions and Clef Omni have separate
text/image arms. There is no model fallback, response replay or retry. Full
evidence includes the complete body once. Local evidence explicitly records
all omitted body row, cell and UTF-8 counts. Either treatment refuses the whole
question if its complete evidence exceeds 128 KiB. Images use the authenticated
generation crop and complete table viewport; they do not guess header height.

Authentication requires externally supplied pool, header-source and generation
code maps. The runner authenticates archived bytes, requires matching current
decoder code, and replays all 80 source-only packet variants and eight images
before freezing its selected request bodies. It never executes archived code.
The client is constructed only after this preparation finishes.

```sh
python -m bench.p003_header_decision_run \
  --pool /absolute/path/header-packets-v4 \
  --pool-trusted-code /absolute/path/header-packets-v4.json \
  --header-trusted-code /absolute/path/header-proposals-v5.json \
  --generation-trusted-code /absolute/path/screen-crops-luna-1024-pinned-r3-c6.json \
  --output /absolute/path/fresh-run \
  --model typesafe/jev-1.13 --evidence-mode local_header --image-edge 0 \
  --transport-concurrency 3
```

Without `--run-hosted`, this command only prepares inputs. Root adds that flag
to authorize paid execution. Capacity is explicitly 1 or 3; Gateway is not
admitted. A transport failure stops remaining calls before reservation.
Malformed returned decisions are retained and permit the next distinct menu.

The primary per-page `state`, `tables`, `*-structure.json` and Markdown contain
only actually selected complete header alternatives. Missing, malformed,
unresolved or unasked menus receive no primary table credit. Disjoint selected
tables survive partial operational failures. All positive participants in an
overlap conflict are refused. `fixed_state` retains unchanged historical
tables separately; `combined_state` is a derived composition diagnostic.
Neither receives model-only credit. The original failed page and its errors
remain in immutable historical provenance. A comparison of combined output
against the original generation is therefore a composition comparison, not a
pure selector score. All 16 original pages remain in the denominator.

`selection_status` distinguishes complete selection, partial selection,
no ambiguous header, failed-closed output and composition conflicts. Page
operational `status` is separate from primary partial output. Menu decisions
retain raw probabilities, optional uncalibrated confidence, usage, ledger
entry, admission wait and client wall/CPU times. Actual broker entries must
attribute the requested model, exact transmitted compact-body SHA-256, unique
attempt index and P003 tag. Sorted request JSON is archival convenience;
`menu-N-wire.json` is the exact transmitted serialization.

The frozen contract includes `config`, `records`, `manifest_sha256`,
`literal_generation_config`, parent pool/report hashes, `code_sha256`,
`historical_provenance`, `independent_authorities`, selected menus/evidence and
request hashes, the complete artifact inventory, preparation resources, and
`all_inputs_frozen_before_client: true`. Per-page selected, fixed and combined
states are archived alongside composition receipts and the original status.

Fresh accounting is under `incremental_header_selection`, with execution
metrics and all attempt charges, including failures. Original generation and
source acquisition costs remain historical. Incremental intended-pages rates
use the 16-page denominator and exclude preparation, generation and acquisition;
full-pipeline rates are undefined. Preparation CPU/wall/lifetime RSS is separate.
Execution samples own-process RSS every 100 ms and records own-process CPU.
Missing attempt accounting stays unknown.

CPU validation: 23 focused runner/packet/header tests passed, including strict
parsing, abstention, partial output, conflict rejection and first-error circuit
stop. A complete v4 authenticated fake-client run froze all 16 pages, asked four
menus, retained four selected tables and 26 separately labeled historical
tables. Preparation took 3.07 seconds wall / 2.97 seconds CPU; fake execution
took 0.18 seconds wall. These timings describe offline validation, not hosted
throughput or quality. No API requests, credentials, ledger access, reference
reads or paid work were used.
