# Distribution and import names

The project is named **pdfust**. Its Python distribution is `pdfust` and new code
imports `pdfust`. Two earlier names remain as compatibility imports in the same
wheel and re-export the complete public API with identical object identities:

| Name | Role |
|---|---|
| `pdfust` | Canonical distribution and import; owns the implementation and the native extension `pdfust.pdfust_core` |
| `jev_pdf` | Compatibility import for the former `jev-pdf` distribution name |
| `pylopdf` | Compatibility import for the upstream `pylopdf` name; `pylopdf.PylopdfWarning` is `pdfust.PdfustWarning` |

Optional data packages follow the new name: `pdfust-fonts-{ar,he,hi,jp,ko,th,zh-cn,zh-tw}`
and `pdfust-ocr-models`. No `pdfust` distribution has been published; the earlier
`pylopdf-*` PyPI projects are upstream's or previously published history and are
not renamed in place. Publishing the renamed data packages requires registering new
PyPI projects and Trusted Publishers first.

Files compressed by earlier versions carry the private `/PylopdfQuality` marker;
`compress_images` still honors it and writes `/PdfustQuality` going forward.

Use a fresh environment, or uninstall any separately installed `jev-pdf` or
`pylopdf` distribution, before installing: two distributions would own
overlapping `jev_pdf` and `pylopdf` module files. Consumers that declare a
dependency on `jev-pdf` or `pylopdf` by name need to depend on `pdfust` instead;
preserving the import alone does not satisfy another distribution's requirement.

Experimental artifact paths (`bench/results/pdf-master-artifacts/`) keep their
historical name to preserve recorded provenance and frozen hashes. Original
author attribution, the MIT license and bundled dependency notices are unchanged.
