# OmniDocBench reference-derived TRAINING layouts

The reviewed v3.1 derivatives are recorded separately in
`synthetic-v3.1-registry.json`; v1/v2/v3 artifacts and earlier registries remain frozen.
The selected registry includes measured scalar/page metadata for grouping and comparison.
V3.1 fixes narrow vertical Latin credits found outside the page in frozen v3.
V3 treats masked regions as blank, suppresses discarded annotations and duplicate
list containers, measures line/grid geometry from reference pixels without OCR,
uses serif/sans/monospace and native CJK text, and adds vertical Chinese text,
page colors, highlights, and newly authored vector illustrations. Every page
has a measured v2/v3.1 ink-distribution comparison, including regressions.
These are approximate reference-derived training layouts, not independently
validated almost-clones. Handwriting, photographs, exact fonts, scan noise,
and source table internals remain limitations.

Both the 16 additional references and their synthetic derivatives are **TRAINING** data. They must never be presented as an independent DEV, evaluation or heldout corpus. The existing 16-page DEV sample is excluded by exact source ID and by inferred numbered-page filename parents. UUID filenames and several other filename formats do not supply reliable document identity; parent separation is incomplete and explicitly recorded.

References come from the official public `opendatalab/OmniDocBench` revision `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec`. The [dataset card](https://huggingface.co/datasets/opendatalab/OmniDocBench/blob/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/README.md) restricts use to research and excludes commercial use. These constraints also govern reference-derived synthetic layouts. Raw images and annotations remain ignored local artifacts; no original prose, formulas or photographs are copied into the synthetic pages.

[registry.json](registry.json) retains source links, hashes, categories, language/layout metadata and parent uncertainty. Sampling greedily covers metadata, category presence and density, with deterministic SHA256 ordering. Recognition answer strings, model results and quality scores are not selection inputs. `geometry-frozen.json` projects only block correspondence IDs, category, polygon-derived envelope, normalized envelope, reading order and ignore status. Synthetic generation consumes this frozen geometry contract, never text/html/latex recognition fields.

The earlier v2 derivative is a layout scaffold, not a validated almost-clone. It preserves page aspect ratio and the annotated block envelopes, authors complete small vector tables, English fictional prose, simple ASCII algebra and procedural RGB figures. It does not reproduce source language, font style, handwriting, photographs, scan noise, table internal geometry or decorative paint. Repeated prose and generic titles are known realism limitations. Tiny mask regions and overlapping annotation envelopes may produce very small text or overlap. The reviewed v3.1 handles masks and typography, with the remaining limitations above.

The retained v2 `synthetic-registry.json` records source/synthetic correspondence, hashes and explicitly defined layout distances. Zero envelope distance describes authored coordinates only; it is not measured ink coverage or visual similarity. Pixel similarity was unmeasured in v2; v3.1 adds coarse ink diagnostics, not a fidelity score. Private authored recipes are frozen after the source contract and before rendering/extraction. Their source block identities and authored table matrices are TRAINING references, never model-facing answers or independent human ground truth.

Artifacts live under `bench/results/pdf-master-artifacts/omnidoc-training-v1/`: reference images/annotations and geometry contract, then versioned `synthetic-v2/`, `synthetic-v3/` and selected `synthetic-v3.1/` PDFs, renders, complete source words, private authored recipes and a full manifest. `synthetic-v1/` retains the earlier larger-font prototype and is not the selected registry version. PDF metadata uses the existing `bench.silver_metadata.analyze_pdf` pipeline: version, file/content/string bytes, image placements and coverage, text geometry, paint and clipping operators and descriptive noise proxies. Five old v2 raw-string measurements report parser errors rather than fabricated totals. The scanner fix handles legal stream delimiters, and all v3.1 metadata errors are empty. Selected v3.1 artifacts also contain the comparison gallery and source geometry audit. No original PDF metadata is available for image references.

Reproduce acquisition with `python -m bench.omnidoc_training --annotations <pinned-OmniDocBench.json> --dev-registry bench/omnidoc-dev/registry.json --output <new-artifact-dir> --registry <new-registry.json>`. Build the retained comparison scaffold with `--build-synthetic-v2 --output <same-artifact-dir> --registry <new-v2-registry.json>`, then the selected reviewed revision with `--build-synthetic --output <same-artifact-dir> --registry <new-v3.1-registry.json>`. The reviewed builder checks the committed reference registry and requires the v2 renders for its paired ink diagnostics; it also requires NumPy, Pillow, the pinned CJK font and Liberation fonts recorded in the frozen design. Existing reference registries and synthetic directories cannot be overwritten. The selected artifacts were prepared with public read-only downloads and CPU-only generation; no hosted inference or GPU was used.
