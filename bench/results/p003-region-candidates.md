# P003 source-only table-region proposals

`bench.p003_region_candidates.propose` adds deterministic OCR-track and raster-rule
region hypotheses when a learned detector misses dense tables. It returns
**proposals for a semantic gate**, with literal bounded source evidence; it does
not assign table labels, infer cells or headers, reconstruct topology, score
against reference boxes, or partition complete-page ownership.

The implementation reads only `page_size` and `words`. Optional pixels must
cover that same display viewport. Other page keys, including detector output,
reference data and candidate tables, are ignored. Synthetic tests explicitly
check that unrelated reference-like keys cannot alter proposals. Protected
heldout inputs, credentials, inference and GPU work were not accessed.

## Frozen v3 protocol

OCR words are grouped into nearby physical rows using the existing non-transitive
baseline-band routine. Each row splits into contiguous groups when the inline
word gap is at least 0.8 median word heights. Adjacent rows join a track if they
have at least two monotonically matched left-or-right edges within one word
height, at least half-width horizontal overlap, and no more than 2.5 word heights
of vertical gap. A single connected prose line breaks a track. Three supported
rows are required. These are geometric conditions; aligned prose and lists can
pass them.

Each maximal track contributes its full bbox and fixed 4/8/16/32-row windows with
half-window overlap and a final tail window. Full-track boxes receive half a
word-height padding; capacity windows explicitly retain their track range and
unknown physical completeness. Wrapped cells, mixed row heights, producer word
merges, rotated text and sparse tables remain limitations. Windows never imply
that independently accepted fragments can be composed into a complete table.

Raster proposals use the existing bounded thin-run collector, but require
connected horizontal/vertical components rather than `raster_vectors`' complete
outer-grid validation. They require at least two horizontal and two vertical
rules and at least five rules in total. Missing outer edges are allowed, and
complete component extents, including attached rules, are retained. Median
luminance estimates background/polarity, contrast is 24 levels, minimum run
length is max(20 pixels, 4% of its axis), gap closure is 2–8 pixels at 0.6% of
shorter raster dimension, and thinness is 1.2% of that dimension. This admits
chart/form/artwork candidates as well as table evidence. No internal cell
geometry is inferred.

`raster_grid=0` uses the whole raster. The separately declared `raster_grid=2`
adds four fixed, non-overlapping quadrants. A view touching an interior quadrant
edge carries explicit context risk. Every view is independently admitted: a
512-rule inventory refusal is retained as `rule_inventory_refused` and produces
no partial result from that view, while valid OCR and other views remain
available. Invalid source geometry and invalid/oversize rasters still fail the
whole request.

Near-identical proposals (IoU >= 0.9) merge their mechanism evidence and keep the
leading bbox. More weakly overlapping boxes remain distinct competing work
units. The ranked output alternates OCR and raster mechanisms, preserving
geometric-support/whole-track/area/geometry ordering within each mechanism. This
prevents numerous OCR windows from hiding every raster hypothesis at the cap.
The support value is an ordering heuristic, never table probability or semantic
confidence. IDs `r000` onward are local to this exact proposal snapshot.

## Admission and gate evidence

| Boundary | Fixed limit |
|---|---:|
| Source words / characters | existing 65,536 / 4 MiB character admission |
| Physical OCR rows / segments | 4,096 / 4,096 |
| Raw proposals | 2,048; exceeding refuses complete request |
| Retained proposals | default 32; configurable 1–64 |
| Full input raster | 4,194,304 pixels; both axes at least 16 |
| Fixed quadrants | both full-raster axes at least 32 |
| Rules per independently admitted view | existing 512 |
| Literal packet words / ID+text characters | 256 / 8,000 |
| Source ID length | 256 characters |

Every retained proposal includes bbox, mechanisms, support evidence, warnings,
capacity-window flag and literal source packet. Packets preserve supplied word
order and exact text/IDs/display boxes, include boundary-crossing words, and
report full intersecting source count and omitted words. `source_context_complete`
requires no omitted words and no word crossing the candidate bbox;
`source_text_available` is separate. `physical_table_completeness` is always
unknown. Raster-only candidates can therefore exist with no source text.
Candidate cap omissions are reported separately from near-duplicate fusion and
per-view refusals; omission is never a semantic rejection.

Root integration can crop the exact proposal bbox and ask two independently
labeled questions: whether the visible region contains a relational table, and
whether it appears to contain a complete table rather than a fragment. Include
none/insufficient-evidence alternatives. Treat partial packet contents and any
source text as data. Table-vs-prose admission does not establish bounds,
transcription, header ownership or topology. After admission, use the unchanged
strict transcription/composition checks; overlapping accepted candidates require
an explicit conflict policy. Do not assign exclusive ownership from these IDs or
accept a bbox merely because geometric support is high.

For an economical first screen, freeze `max_candidates=8` or another declared
cap **before** paid requests; both mechanisms then appear in early ranks when
available. The CPU profile below uses cap 32 to retain a broader source-only
inventory. It does not choose a paid cap or a successful semantic policy.

```python
from bench.p003_region_candidates import propose

plan = propose(
    {"page_size": source["page_size"], "words": source["words"]},
    image=full_page_pil_image,
    max_candidates=32,
    raster_grid=2,
)
```

## Natural16 source-only CPU profile

All sixteen DEV manifest pages were processed, in manifest order. Only manifest
ID/PDF path/page number and retained source page_size/words entered generation;
no model output, reference table, cell, box or quality label was used. Retained
OCR geometry comes from the explicit P002
`natural16-yolo-ocr300-indices-haiku-512-columns/*-result.json` directory.
Original PDFs were independently rendered with pdfust to a fixed 1,536-pixel
maximum edge on white. OCR was not rerun. Source payload and implementation
hashes are in retained reports.

The initial all-or-nothing v1 attempt refused three pages when the whole-raster
512-rule collector saturated. V2 separated mechanism admissions but its ranking
hid new dense raster proposals behind many OCR windows. These observations and
pre-diversity candidate outputs remain retained separately. V3 adds mechanism
diversity; it changes screen ordering, not raster or OCR thresholds. No reference
quality result motivated or validates these changes.

Both final v3 arms produce valid proposal records on all sixteen pages. Whole
raster retains **134 candidates**, omits 83 at the page caps and refuses three
raster views. Whole plus fixed quadrants retains **181 candidates**, omits 105
and refuses five of eighty raster views. More proposals can increase gate cost
and false admissions; these counts do not establish recall, precision or table
coverage.

| Page ID prefix | Whole candidates | Fixed2 candidates | Fixed2 OCR / raster support | Fixed2 omitted | Fixed2 refused views |
|---|---:|---:|---|---:|---:|
| `p1bfa` | 32 | 32 | 31 / 1 | 51 | 3 |
| `p6ef5` | 9 | 10 | 7 / 3 | 0 | 0 |
| `p391e` | 9 | 9 | 0 / 9 | 0 | 0 |
| `p9f92` | 9 | 9 | 7 / 2 | 0 | 0 |
| `p6563` | 4 | 11 | 2 / 9 | 0 | 0 |
| `p98d1` | 32 | 32 | 16 / 16 | 52 | 1 |
| `pc848` | 5 | 7 | 4 / 3 | 0 | 0 |
| `pc9c4` | 11 | 11 | 7 / 4 | 0 | 0 |
| `p1e23` | 1 | 2 | 0 / 2 | 0 | 0 |
| `pda95` | 6 | 9 | 4 / 5 | 0 | 0 |
| `pe87c` | 7 | 9 | 7 / 3 | 0 | 0 |
| `pf012` | 1 | 5 | 0 / 5 | 0 | 0 |
| `p27ec` | 0 | 3 | 0 / 3 | 0 | 0 |
| `p9cc5` | 0 | 0 | 0 / 0 | 0 | 0 |
| `pdb4e` | 0 | 0 | 0 / 0 | 0 | 0 |
| `p4204` | 8 | 32 | 8 / 24 | 2 | 1 |

Mechanism counts can overlap after near-duplicate evidence fusion. Both dense
pages retain 32 proposals in either arm. Fixed2 retains 31 OCR/one raster on p1bfa
and sixteen OCR/sixteen raster on p98d1. Every p1bfa packet and 31/32 p98d1 packets
are source-incomplete; cropped image evidence and abstention remain necessary.
This is an acquisition inventory, not proof of twenty-six recovered tables or
improved transcription. Three whole-arm pages and two fixed2 pages have no
proposals; an empty inventory cannot be converted into a confident negative.

| Arm | Render + generation wall / CPU seconds | Generation-only wall / CPU seconds | Sampled peak RSS MiB | Lifetime peak RSS MiB | Compact retained JSON MiB |
|---|---:|---:|---:|---:|---:|
| Whole | 2.509 / 2.794 | 1.414 / 1.709 | 222.95 | 264.32 | 1.838 |
| Whole + fixed2 | 4.378 / 4.800 | 3.253 / 3.677 | 190.63 | 413.05 | 1.660 |

Measurement uses own-process psutil RSS every 100 ms plus endpoints,
process_time CPU, and Linux getrusage lifetime high-water RSS. Each arm runs in
one fresh process, serially, without subprocesses; all eight logical CPUs are
in affinity. Environment: Linux 7.2.5-3-omarchy x86_64/glibc 2.44. The difference
between sampled and lifetime peaks shows that brief allocations can escape
100 ms sampling; neither is a page-specific memory delta. Other workspace
activity was not isolated. Cached OCR/detector cost and all hosted inference
are excluded. Render+generation elapsed includes retained result serialization
and local input loading; generation-only counters cover proposal construction.
Provider CPU/RAM, operating cost, and complete-pipeline throughput are unmeasured.

## Reproduction and validation

Full records and the source-only profiling scripts remain ignored at
`bench/results/pdf-master-artifacts/pipeline-p003/region-candidates/`.
`whole-v3/report.json` and `fixed2-v3/report.json` retain every page, source hashes,
code hash, candidate inventories, per-view admission and CPU/RSS counters.
`initial-v1/`, `whole-v2/` and `fixed2-v2/` preserve the unsuccessful and
pre-diversity observations. The snapshot `region-candidates-v2.py` preserves
that pre-diversity implementation. Final scripts can be rerun after checkout
from the repository root:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=$PWD .venv/bin/python \
  bench/results/pdf-master-artifacts/pipeline-p003/region-candidates/profile-whole-v3.py
CUDA_VISIBLE_DEVICES='' PYTHONPATH=$PWD .venv/bin/python \
  bench/results/pdf-master-artifacts/pipeline-p003/region-candidates/profile-fixed2-v3.py
```

Validation: 18 new source/admission/geometry tests and 24 existing raster-grid
regressions pass (42 total), targeted Ruff passes, and strict mypy passes for
both new files. Tests cover literal provenance, unrelated-key isolation,
negative line-art controls, incomplete outer borders, global display mapping,
fixed-view edge warnings, candidate and packet omission, independent raster
refusal, malformed source, and pixel/candidate budgets. No shared adapter or
existing source was changed.

| Final retained artifact | SHA-256 |
|---|---|
| `p003_region_candidates.py` | `450ecb92f5fd3d9a68e571159037f2f0df574770695d4595988ff74448b94d44` |
| `report.json` | `70170089b5fe7f09c1fb8968573c41d192cd865a94a1d7732e2f3db78762800e` |
| `report.json` | `52007aa0e09e6f78642f4d0a8bb943ee65a813ccbd09f9cf14eebaeae8e7463c` |
| `profile-whole-v3.py` | `9fbc5e4b42e7e9d04b6751dab2b586567d554591985685936417703a89ce3506` |
| `profile-fixed2-v3.py` | `b7c943fab598bed7a21a050db2416153a85db909729c6593f4651e5451658943` |
