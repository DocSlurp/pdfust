# Independent held-out silver inventory

This release contains exactly 20 independently authored PDF documents and 26
pages. Twenty separate layout construction branches share only a generic raw-PDF
serializer, basic drawing operators, font declarations, and synthetic resources.
No development fixture generator code or reference cases were borrowed.

The documents span multiple columns, complex grids and forms, prose around
insets, multipage headers and footers, nested mathematics, mixed raster and text,
font and encoding variation, and rotated or overlapping content. Categories may
overlap. Semantic details and category membership remain protected.

The references are procedural silver targets authored alongside the source:
source text blocks, selected relationships, and visible formulas. They are not
human-adjudicated labels and were not substituted with extracted output.

All 20 PDFs passed strict pypdf parsing, direct font/CMap/image-resource checks,
and sequential CPU-only rendering of every page at 45 dpi. The custodian checked
rendering and construction; no human review or extractor-quality evaluation was
performed. Low-resolution validation does not establish visual correctness at
arbitrary zoom levels or reference completeness. Native imports contribute to
the process lifetime peak RSS; the protected validation record retains exact
resource measurements and scope.

`registry.json` exposes only opaque identities, document/page counts, source PDF
hashes, protected artifact hashes, and the local dataset locator. Its inventory
digest hashes canonical sorted-key JSON for the case inventory. The protected
freeze record pins the exact generator, references, manifest, dependency
versions, and validation records. All artifacts remain in the ignored prefix.

Read [AGENTS.md](AGENTS.md) before any handling. Developers and tuning agents may
use the inventory but must not follow its locator. Dataset access requires an
explicit evaluator authorization after candidate freeze or an explicit user
release. Separation is procedural under the same OS user, not enforced access
control. No network inference, GPU use, upload, publication, or push is involved.
