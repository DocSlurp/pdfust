# P001 complete page assembly proposal

This CPU-only experiment turns one source snapshot into alternatives for a complete
page. It does not read document identities, private targets, expected relationships,
model responses, or protected heldout inputs. Hosted selection and evaluation are
separate runner responsibilities.

`bench.pipeline_assembly.propose(page)` accepts literal `words` with `id`, `text`,
`bbox`, a `page_size` of `[width, height]` or `[x0, y0, x1, y1]`, and optional native
`vector_candidates` in `bench.silver_structure.observed_table` shape. Extra fields
are ignored. Native cell strings and diagnostic annotations are ignored too.

Every output is `{id, tables, unresolved_ids, description, mechanism}`. Tables
have `row_count`, `col_count`, `values`, `spans`, and flat row-major `cells` with
`source_ids` and `role="unknown"`. Values are literal source text joined in owned
ID order with spaces; empty uncovered slots use an empty string, while non-anchor
span-covered slots use `None`, derived exclusively from topology. Spans preserve
native merged topology. IDs are consecutive snapshot-local `cN`. Each source ID
occurs exactly once across cells and unresolved inventory in each alternative.
`validate(page, state)` checks ownership, dimensions, spans and literal values.
Spans must tile every slot exactly once: overlaps, duplicate anchors and holes
are rejected. `native_state(page)` builds and validates the native-only complete
page without invoking either heuristic proposal generator.

The declared proposal mechanisms are:

- No table admission, retaining the entire page as unresolved content.
- Native vector grids together, assigning words only when their centers have one
  unique cell owner across the full collection. Ambiguous boundary words remain
  unresolved rather than appearing twice.
- Full-page vertical gap regions with seed column corridors, under physical,
  sparse continuation and numeric-boundary continuation policies reused from
  `rolling_topology`. Per region, the proposal retaining the most source IDs wins,
  with the earliest seed breaking ties. Regions combine into one page alternative.
- The same corridor proposals filtered by the existing `corpus_routes` compact
  numeric admission rule. This exposes an explicit table-versus-prose alternative.
- Repeated-edge physical and rolling row proposals reused from `rolling_rows`.

Native-owned words are removed before residual geometry proposals. Vertical gaps
split regions only above both three median glyph heights and 2.5 median positive
inter-band gaps. All residual words remain available; no titles or footers are
removed using content labels. Distinct complete alternatives are deduplicated by
literal values, ownership, spans and unresolved IDs. Consequently an identical
physical proposal may retain the earlier `seed_physical` mechanism. A missing
native grid produces the same state as no table and retains mechanism `none`.

`packet(page, candidates, context_style="full")` emits generic selection
instructions, the full literal word inventory with geometry, and every complete
candidate table with source IDs and unresolved IDs. It does not include mechanism
labels, per-case questions, target chunks, scorer labels, or filename information.
The decision response is only `{"choice":"cN"}` or
`{"choice":"unresolved"}`; abstention is separate from choosing the no-table
candidate. Full-page raster evidence is supplied separately by the root runner.

Admission refuses more than 4,096 words, 16,000 aggregate source text/ID characters,
32 native tables, 4,096 slots per table, or 24 alternatives. Complete decision
packets above 25,000 Unicode characters are refused. There is no partial source
extraction or packet truncation. Candidate generation uses three frozen seed
policies and selects one extent hypothesis per region; it is not an exhaustive
search of all possible table assemblies.

Limitations include horizontally adjacent unruled tables without a vertical gap,
ambiguous column prose, native-grid word centers on cell boundaries, rotated
non-native content, and omitted extent alternatives when a larger corridor wins.
The decision model can select only retained alternatives or abstain. This is an
opt-in benchmark experiment; default extraction behavior is unchanged.

Validation: thirteen focused Python tests pass, covering source conservation, physical
and wrapped row alternatives, prose ambiguity, multiple native tables, separated
text tables, annotation mutation invariance, duplicate IDs, fabricated values,
empty pages, merged covered-slot representation and complete-packet refusal. Ruff passes. Checks run sequentially on
CPU with the existing main-worktree Python environment; no network or inference
requests were made. These checks are correctness checks, not performance
measurements; CPU utilization and RSS are unmeasured.


Source-only coverage probe on the frozen 181-page DEV manifest admitted 175 complete
packets. Extraction succeeded on all pages. Five pages refused complete packets at
the 25,000-character boundary (`p135b05c6626694a9e25a`,
`p2e823666719c13acd4b9`, `p5005dd1ec0a0e6595b89`,
`p6333ca96842cead34e25`, `pf2ab4d0b6b137ba48d77`). One native table
(`pfe3eba53239267b4e870`) exposed an incomplete observed span tiling and was
refused before proposal admission. No targets or references were opened. This
is source coverage, not table correctness or candidate quality scoring.

Admitted packets reached 21,761 Unicode characters; candidate count ranged up to
six. The sequential CPU probe measured 3.19 seconds elapsed, 3.25 seconds process
CPU and 538,996,736 bytes lifetime peak RSS using `perf_counter`, `process_time`
and `getrusage(RUSAGE_SELF)` with no sampling or workers. This scope includes PDF
loading, source extraction, proposal, validation, packet generation and local
artifact writes; interpreter imports preceded timing, but lifetime RSS includes
them. Usage is not separated into per-stage peaks. Source and candidate identities
remain under ignored artifacts in `pipeline-p001-source-coverage`; the provisional
probe is separate from root's final experiment freeze.
