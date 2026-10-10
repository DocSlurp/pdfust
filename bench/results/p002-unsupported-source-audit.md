# P002 native regional unsupported-source audit

Four intended pages in `native-regional-full-r2` have `unsupported_no_text`. This audit read only those exact frozen source records, matching per-page results and hash-verified PDFs. It collected fresh native text, image-placement and drawing counts and inspected 512-pixel source rasters. No references, hosted inference, OCR reruns, credentials or network requests were used.

Every retained result reports an RTen native CPU OCR attempt at 150 dpi with four threads and zero recognized regions. These failures do not demonstrate that OCR was disabled. The fresh native extraction returned zero characters on all four pages.

| Page ID | Source PDF SHA-256 | Native characters | Interpreted image placements | Interpreted drawing paths | Source-pixel observation |
| --- | --- | ---: | ---: | ---: | --- |
| p3537ba59f34ed944966f | da04b715cd876a00f79728faed5501e0697e4e0783201470a7f20eec67bd6e85 | 0 | 2 | 0 | Aged decorative cover with faint marks; no readable table text in the 512-pixel inspection |
| pd1a2dc76a3752f9861ee | dc213b3d2952f06517ac487d9892b11628f4b5bedc2ad8278a4c05c1b40be8f6 | 0 | 0 | 0 | Current renderer produces a white page; source contains a Type 3 glyph image-mask program |
| pfb20031e973ad29c7e43 | 9947d9c15d853823cedc1e87378dea89a665570e4f233b7a0ba215e5859134ab | 0 | 0 | 2 | A gray filled rectangle on white; no visible text |
| peb29c108f12d92347139 | ba14897a4139944e56674fefe176a56f29326e69ff2baf3e07ba096b520def78 | 0 | 1 | 0 | Uniform red image; no visible text |

The Type 3 page deserves a separate interpretation. Fresh extraction emits the known warning: glyphs lack Unicode mapping, for example Type 3 without a ToUnicode CMap. The source PDF has `/Subtype /Type3`, no ToUnicode mapping, three `(A) Tj` text operators and a CharProcs inline one-bit image mask. Its fresh white raster therefore must not be described as proof of a genuinely blank source page. Interpreted image/drawing counts are API observations; the zero image count does not erase the inline image present in the Type 3 program. This matches the repository's documented upstream Type 3 extraction gap; the audit does not change the font interpreter or invent source Unicode.

The other three pixel observations explain why a text-based source inventory remains empty without demonstrating a general table-extraction failure. The decorative cover may contain faint unreadable marks; this audit does not claim that every source pixel is semantically text-free. The gray rectangle and uniform red image provide no visibly readable words to recover. Their unsupported status remains an operational failure in complete-run reporting rather than being silently relabeled successful.

Exact frozen records, fresh source observations and source rasters remain in ignored `bench/results/pdf-master-artifacts/pipeline-p002/unsupported-source-audit/`. Original page rotations are zero. The source-only audit supplies evidence for failure classification; it supplies no structural accuracy score, no OCR performance claim and no justification for a speculative pipeline fix.
