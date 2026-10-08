# Semantic fast-path CPU experiment

Private local research; no core API or dependencies changed.

Run: `.venv/bin/python -m bench.semantic_probe --repeat 7`. pypdf 6.15.0; Python 3.14.7; Linux x86_64; median of 7 fresh-reader runs; input bytes already in RAM. Load, inventory, and attempted recovery are included; Python import and disk read are excluded.

Denominators: 15 bundled corpus PDFs; 11 authored controls. Corpus is a convenience sample, not a deployment prevalence estimate.

Observed corpus coverage: 3/15 have StructTreeRoot; 1/15 have any Table candidate; 0/15 yield validated tables. 3/15 expose form leaves; 0/15 expose attachment names. Both authored positive tables recover exactly; all nine other controls yield zero tables. No geometric speed comparison is claimed because corpus recovery outputs are not equivalent.

| Input | Tagged table candidates | Validated tables | Form leaves | Embedded names | Median ms | Outcome |
|---|---:|---:|---:|---:|---:|---|
| tests/assets/real_world/bill-hr815.pdf | 0 | 0 | 1 | 0 | 0.687 | ok |
| tests/assets/real_world/bunka-kokugo-series-019-p4.pdf | 0 | 0 | 0 | 0 | 0.378 | ok |
| tests/assets/real_world/f1040.pdf | 1 | 0 | 199 | 0 | 106.024 | unsupported_empty_or_nested_cell_content |
| tests/assets/real_world/mhlw-doc.pdf | 0 | 0 | 0 | 0 | 9.053 | ok |
| tests/assets/real_world/nics-background-checks-2015-11.pdf | 0 | 0 | 0 | 0 | 0.158 | ok |
| tests/assets/real_world/patent-us223898.pdf | 0 | 0 | 0 | 0 | 0.394 | ok |
| tests/assets/real_world/pdf20-simple.pdf | 0 | 0 | 0 | 0 | 0.136 | ok |
| tests/assets/real_world/pdfium-jpx-lzw.pdf | 0 | 0 | 0 | 0 | 0.143 | ok |
| tests/assets/real_world/pdfium-links-highlights-annots.pdf | 0 | 0 | 4 | 0 | 0.371 | ok |
| tests/assets/real_world/pdfium-smask-blend.pdf | 0 | 0 | 0 | 0 | 0.083 | ok |
| tests/assets/real_world/pdfium-type3.pdf | 0 | 0 | 0 | 0 | 0.074 | ok |
| tests/assets/real_world/senate-expenditures.pdf | 0 | 0 | 0 | 0 | 0.120 | ok |
| tests/assets/real_world/usrguide.pdf | 0 | 0 | 0 | 0 | 3.376 | ok |
| tests/assets/real_world/wdl6812-manuscript.pdf | 0 | 0 | 0 | 0 | 0.365 | ok |
| bench/assets/rich/omml-equations.pdf | 0 | 0 | 0 | 0 | 0.777 | ok |
| valid | 1 | 1 | 0 | 0 | 0.959 | ok |
| rolemap | 1 | 1 | 0 | 0 | 0.970 | ok |
| missing-mcid | 1 | 0 | 0 | 0 | 0.959 | stale_parent_association |
| bad-header | 1 | 0 | 0 | 0 | 1.007 | unresolved_header |
| stale-parent | 1 | 0 | 0 | 0 | 0.971 | stale_parent_association |
| duplicate-mcid | 1 | 0 | 0 | 0 | 1.002 | reused_mcid |
| cycle | 0 | 0 | 0 | 0 | 0.135 | tree_limit_or_cycle |
| untagged | 0 | 0 | 0 | 0 | 0.078 | ok |
| nonvisible | 1 | 0 | 0 | 0 | 0.844 | nonvisible_or_complex_text |
| embedded-consistent | 0 | 0 | 0 | 1 | 0.125 | ok |
| embedded-stale | 0 | 0 | 0 | 1 | 0.123 | ok |

Recovery requires rectangular Table/TR/TH/TD rows, unique cell IDs/MCIDs, resolvable Headers, valid Scope, matching page StructParents/ParentTree backlinks, and real marked content. Custom RoleMap chains are accepted with cycle checks. IDs are preserved as byte-exact hex; text comes from explicitly encoded Type1 WinAnsi literal bytes, never /Alt or guessed metadata.

The f1040 candidate has eight rows, an empty header spacer, nested /P text cells with page references on descendants, and /Form cells containing annotation /OBJR links. It needs explicit form/empty-cell/nested-content integration; it is not merely missing a /Pg key.

Unsupported: merged cells, nested cell elements/MCR dictionaries, font subsets/CMaps, nonzero TJ spacing, WinAnsi codes outside printable ASCII/Latin accents (192-255), Form XObjects, /ActualText, nonvisible text, clipping, and graphics-state dictionaries. Consistent but semantically wrong producer tags cannot be detected by backlinks alone. This validates associations, not PDF/UA conformance or pixel visibility.

Caps: 64 MiB input; 4,096 traversal nodes/children/pages/MCIDs; depth 32; role depth 16; 65,536 content operations; 1 MiB decoded page content/text and recovered table text. Important limitation: pypdf parsing, page-tree walking, and stream decoding occur before some checks, so these are experimental traversal/output bounds, not a hardened untrusted-input guarantee.

Forms and attachment names are alternate-source presence signals only. Neither implies table rows/cells. Embedded payloads were not decoded or trusted; a future CSV/JSON path needs a declared schema plus document/version binding and stale-payload controls.

Next hypotheses: collect licensed tagged financial tables with ground truth; join validated MCIDs to the existing glyph interpreter (arbitrary CMaps and geometry); support nested cell content and spans; check IDTree consistency; validate attachment schemas and document binding. Benchmark these routes against equivalent complete outputs before claiming superiority over geometric recovery.

Primary syntax references: [PDF Association tagged-PDF guide](https://pdfa.org/download-area/publications/Tagged-PDF-Best-Practice-Guide.pdf) and [ISO 32000-2 document-interchange errata](https://pdf-issues.pdfa.org/32000-2-2020/clause14.html). Complete results and authored PDFs remain ignored under `bench/results/pdf-master-artifacts/semantic/`.
