"""Python-coverage-guided fuzzing of public workflows and native failures.

The normal extension build does not provide Rust branch coverage to Atheris.
See fuzz/README.md for the distinction and native instrumentation requirements.
"""

from __future__ import annotations

import contextlib
import sys
import warnings

import atheris

with atheris.instrument_imports():
    import pdfust

_MAX_INPUT_BYTES = 1_048_576
_MAX_PAGES = 2
_MIB = 1024 * 1024
_FUZZ_LIMITS = pdfust.DocumentLimits(
    max_file_size=4 * _MIB,
    max_pages=_MAX_PAGES,
    max_objects=20_000,
    max_decompressed_size=16 * _MIB,
    max_page_content_size=4 * _MIB,
    max_total_decompressed_size=32 * _MIB,
    max_object_depth=64,
    max_text_size=_MIB,
    max_text_glyphs=16_384,
    max_interpretation_size=8 * _MIB,
)


def _inspect_document(doc: pdfust.Document) -> None:
    """Exercise bounded tree readers without abandoning later steps."""
    readers = (doc.get_toc, doc.get_form_fields, doc.get_page_labels, doc.embfile_names)
    for reader in readers:
        with contextlib.suppress(pdfust.PdfError):
            reader()
    with contextlib.suppress(pdfust.PdfError):
        doc.get_pdfa_claim(max_size=_MIB)
    with contextlib.suppress(pdfust.PdfError):
        _ = doc.complexity, doc.metadata


def _inspect_page(page: pdfust.Page, selector: int) -> None:
    """Exercise independent interpreters and navigation under their fixed caps."""
    readers = (page.get_drawings, page.get_images, page.find_tables, page.get_links)
    with contextlib.suppress(pdfust.PdfError):
        readers[selector % len(readers)]()
    with contextlib.suppress(pdfust.PdfError):
        page.to_markdown(max_size=_MIB)


def test_one_input(data: bytes) -> None:
    """Exercise parsing, extraction, rendering, editing, saving, and reopening."""
    if not data or len(data) > _MAX_INPUT_BYTES:
        return

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", pdfust.PdfustWarning)
        try:
            with pdfust.open(
                stream=data,
                limits=_FUZZ_LIMITS,
            ) as doc:
                _inspect_document(doc)
                page_count = min(doc.page_count, _MAX_PAGES)
                for page_number in range(page_count):
                    page = doc[page_number]
                    _inspect_page(page, len(data) + data[len(data) // 2] + page_number)
                    with contextlib.suppress(pdfust.PdfError):
                        page.get_text("dict")
                        page.search_for("pdf")
                    with contextlib.suppress(pdfust.PdfError):
                        page.get_pixmap(dpi=18)

                doc.set_metadata({"producer": "pdfust fuzz"})
                saved = doc.tobytes(garbage=True, deflate=True, object_streams=True, max_size=8 * _MIB)

            with pdfust.open(
                stream=saved,
                limits=_FUZZ_LIMITS,
            ) as reopened:
                if reopened.page_count:
                    reopened[0].get_text()
        except pdfust.PdfError:
            # Invalid or unsupported PDFs are expected. Crashes, panics, and
            # exceptions outside pdfust's documented error hierarchy are not.
            return


def main() -> None:
    """Configure Atheris and enter the libFuzzer loop."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        main()
