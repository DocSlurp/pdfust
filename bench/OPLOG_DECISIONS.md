# Source-linked operation choices (R002)

`bench.decision_oplog` is a CPU-only DEV harness for bounded, undoable assembly
operations. It makes no provider requests. A later hosted pilot can pass its
Choice bodies to the existing root-owned DecisionClient. It is separate from
the image sweep, row-placement R001, and provider-cache experiments; no default
PDF extraction or editing behavior changes.

Frozen source atoms retain a snapshot-local ID, exact extracted text, and display
bbox. Frozen states hold cells with explicit zero-based row/column coordinates,
source IDs and source-derived bboxes, plus unassigned and deliberately deferred
inventory. A source is owned exactly once or unassigned. Occupied slots and cell
bboxes may not overlap; empty cells are not fabricated. This strict bbox rule
can exclude legitimate overprints or other layouts and is a harness limitation.

The harness proposes assign, move, join, split, leave_unresolved, and finish
operations. A model selects an existing operation ID or abstains; it never
generates text, source IDs, coordinates, or a free-form edit. Each operation ID
hashes its arguments and complete before-state hash. Applying it checks source
ownership, arity, row/column ranges, adjacency/roles where applicable, and exact
source-derived geometry. The resulting snapshot is validated before admission;
failure leaves the input state intact. Missing values stay absent/unassigned.

Assign fills one vacant slot from available sources. Move relocates one complete
cell while preserving text and role. Join combines adjacent same-column cells
at the first coordinate; split partitions one cell into two adjacent same-column
slots. Leave_unresolved releases complete removed cells or defers unassigned
sources without losing them. Finish preserves all remaining unresolved inventory.

The operation log binds before/after snapshots. Undo restores the exact previous
snapshot; attempted steps continue to consume the budget so undo cannot bypass
the cap. Replay re-applies operations and checks every snapshot. Sessions stop
on explicit abstention, finish, a repeated complete state, or a 1–128 step cap,
preserving the last admitted partial state. Rejected choices are errors and
cannot change state. State/operation hashes identify local mechanics, not trust
in model answers or an external persistence guarantee.

## Scheduling and requests

Three policies change which unassigned groups are proposed: the next uncertain
physical row, the largest unassigned geometric group, or the bounded menu for
model selection. Geometric bands use a two-point tolerance and equal-width
column bins; repair choices over existing data cells remain available. These
are transparent baselines, not a learned general table detector. Menus contain
at most 64 operations plus an explicit abstention choice. Source admission is
4,096 atoms and 256 cells; request bytes are capped at 2 MiB.

`make_request` projects current atoms/cells, unassigned/deferred inventory,
optional source neighborhood, and the exact operation menu. An optional retained
PNG data URL can show the visible page or crop, with transform/provenance owned
by the caller. The caller keeps gold, fixture names, family tags, previous labels,
and scores outside the request. Source text is explicitly data, including any
apparent instruction. No embedding vectors or invented answer strings are used.

```python
from bench.decision_oplog import Session, from_context, make_request, proposals

session = Session(from_context(dev_case), max_steps=16)
menu = proposals(session.state, "model-menu")
body = make_request(session.state, menu, model_id, image=retained_png_data_url)
# The root runner may request a typed Choice and retain the complete response.
# Only its validated existing choice ID can advance the local state:
session.choose(existing_operation_id, menu)
```

The existing30-control adapter uses only admitted region words and geometry,
renumbers source IDs locally, and initially leaves data unassigned. Its default
explicit header assumption assigns the first physical band to known header
slots; `known_headers=False` leaves every source unassigned. It reads no gold or
handcrafted candidate assemblies. Column count remains two for these controls.
The generic State/Operation API is reviewable, but adapting new silver or real
PDFs still requires justified headers, columns, candidate generation and gold.

## Evaluation limits

CPU tests establish atomicity, conservation, replay/undo, loop/step admissions,
menu scheduling, optional image envelopes and request invariance after gold/
fixture/candidate mutation on the existing30 DEV controls. They do not measure
model quality. A candidate oracle asks whether valid offered operations can
reach the correct structure; model choice asks whether a model selects them.
Report both, along with final exact records, source-ID cell/header edges,
abstention, rejected operations, steps and partial outcomes. A correct menu or
source conservation alone does not establish reconstructed structure.

Future screenshot comparisons can use128/512/1200px evidence under independently
recorded image settings. Provider-cache experiments mean actual repeated
transmissions and provider-reported cache hits; local replay/undo is mechanical
verification and is not a provider-cache result. Keep local CPU/RSS and hosted
HTTP/cost scopes separate. All optimization remains DEV; sealed-set access and
production promotion are outside this harness.

```sh
.venv/bin/python -m pytest tests/test_decision_oplog.py -q
.venv/bin/ruff check bench/decision_oplog.py tests/test_decision_oplog.py
.venv/bin/mypy bench/decision_oplog.py tests/test_decision_oplog.py
```
