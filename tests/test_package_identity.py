"""Check the new distribution identity and shared compatible Python surface."""

from __future__ import annotations

import jev_pdf
import pylopdf


def test_new_api_creates_pdfs_readable_through_compatible_import() -> None:
    with jev_pdf.Document() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Shared PDF API")
        data = document.tobytes()
    with pylopdf.open(stream=data) as document:
        assert "Shared PDF API" in document[0].get_text()
        assert isinstance(document, jev_pdf.Document)


