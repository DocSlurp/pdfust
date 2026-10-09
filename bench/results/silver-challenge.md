# Sanitized silver DEV baseline

Run UTC: **2026-10-09 03:51:10**. This is a CPU-only extraction/metadata baseline,
with no model inference or hosted charge. Python3.14.7 on Linux7.2.5 x86_64,
8 logical CPUs, **one worker** and one fresh subprocess per document.

Dataset SHA-256:
`2e3b8c00f83375cc5d5e804ebe473f9ea0926f0ac2e1153996058381fdf02d21`.
Artifacts:
`bench/results/pdf-master-artifacts/silver-v1/2e3b8c00f83375cc/runs/20261009T035110-o22uv9uy/`.
The manifest and exact PDF/request-independent hashes identify inputs; raw PDFs,
outputs, metadata and gallery stay ignored. Runner hash:
`0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1`;
metadata-module hash:
`841dd3617ad0f10d3f9354d7f84c58e8c6a48e1aeaa0a4cacab53655ea941861`.

| Observation | Result |
| --- | ---: |
| Completed documents | 104/104 |
| Physical pages | 125 |
| Authored literal anchors found | 1,576/1,576 |
| Warm text and Markdown identical | 104/104 |
| Worker failures / metadata errors | 0 / 0 |
| Documents with warnings | 4 |
| Complete runner wall time | 22.154 s |
| Summed measured worker CPU | 4.756 s |
| Summed measured worker wall time | 4.617 s |
| Median / maximum worker lifetime peak RSS | 104.21 / 105.21 MiB |
| Median newly opened Document extraction wall / CPU | 16.424 / 16.723 ms |
| Median reused Document extraction wall / CPU | 0.377 / 0.376 ms |

The four warnings flag Type3 formula glyphs without Unicode mappings. Their
digital titles remain extractable. Perfect title/anchor recall is compatible
with missing formulas, so it is **not a math, table, or layout quality score**.
All outputs and warnings are retained; warm agreement measures reproducibility.

Worker CPU/wall counters cover input reading, metadata and cold/warm extraction
after imports and input validation. RSS is the full fresh worker lifetime,
including imports and validation. Instrumentation is `time.process_time`,
`os.times`, and Linux `/proc/self/status` `VmHWM`; other Unix platforms fall back
to `resource.getrusage(RUSAGE_SELF).ru_maxrss`. These are cumulative counters/
high-water RSS with no periodic sampling. RSS was available for all
104 workers. Parent scheduling/import/startup/output overhead contributes to
runner wall time and is outside the worker counters. Gallery generation is
outside these measurements. Peak RSS is an individual worker maximum, not
concurrent total memory. CPU ratios may exceed 100% when library threads run.

Metadata ran before the newly opened extraction Document, so “cold” does not
mean the first library operation in the process. Summed cold/warm extraction
wall time was 1.832 s / 0.044 s; summed extraction CPU was 1.866 s / 0.044 s.
Metadata wall time summed to 2.697 s. Linux VmHWM avoids a launcher high-water
RSS inherited across exec; prior run artifacts remain retained. These small authored inputs do not predict
large-document memory or production throughput.

## Coverage and readiness

There are 64 layout files: four variants of each of 16 families covering columns,
image/text placement, page furniture, rotations/crops, merged/grouped tables,
forms, sidebars/footnotes, source-versus-geometric reading order, overprints, and
vector decoration. Variants share templates, standard unembedded fonts, and a
common producer. Header versions/encodings/compression differ, but this does
not exercise every PDF-version feature or independent producer behavior.

The 40 math files repeat four expressions across ten encoding forms: literal
and kerned text, positioned powers/subscripts/fractions, mapped/multichar/unmapped
Type3, ActualText, vector paths, raster, and raster plus authored invisible text.
ASCII operator names and block glyphs limit typography coverage. Declared math
references are unadjudicated. See [coverage definitions](../SILVER_CHALLENGE.md).

Generic Report/Reference visible titles replace family/encoding names before
hosted tests to remove that shortcut. Metadata keeps descriptive local tags.
The pre-sanitization dataset `50a400f840cb5aac` and baseline remain retained as
separate DEV provenance, rather than overwriting their inputs.

Parsing, metadata exports (`metadata.jsonl/csv`, `pages.jsonl/csv`), extraction,
and local gallery are ready. The [authored structural baseline](silver-structure.md) is complete: native ruled grids recovered all 10 tables with no false tables on 115 negative pages.
New-dataset hosted complete assembly still needs a generic candidate/gold
adapter; the old 30-control menu is not a full-dataset evaluator. The planned
125-page table-presence gate will have a narrower outcome. The planned
RGB8/gray8/palette4 at 128/512/1200 px image sweep with nine matched blanks has
no result in this report. No full pipeline has been validated.

Separately, the custodian reports a sealed **20-file / 26-page** collection,
parse/render checks only, inventory
`c1f887661e3dd40faa15510001decba1c2cb0a1112bdbb1566286a6541e0fe8e`.
This report did not access its files or labels. Fresh independent construction
shares a serializer, and repository protection is procedural. Keep all tuning
on DEV, then freeze configuration before evaluator-only confirmation.

Reproduce DEV generation/measurement with:

```sh
uv sync --group bench --group bench-vision
.venv/bin/python -m bench.silver --build --benchmark --gallery --workers 1
```

See the [ranked experiment plan](../EXPERIMENT_PLAN.md) for completed component
results, remaining adapters, and the next model comparisons.
