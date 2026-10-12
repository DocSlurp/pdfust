"""The pdfust import is canonical; jev_pdf and pylopdf remain compatible aliases."""

from __future__ import annotations

import warnings

import pytest

import jev_pdf
import pdfust
import pylopdf


def test_legacy_imports_share_objects_with_pdfust() -> None:
    assert jev_pdf.Document is pdfust.Document is pylopdf.Document
    assert pylopdf.PylopdfWarning is pdfust.PdfustWarning
    assert set(pdfust.__all__) <= set(pylopdf.__all__)


def test_documents_round_trip_through_a_legacy_import() -> None:
    with pdfust.Document() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Shared PDF API")
        data = document.tobytes()
    with pylopdf.open(stream=data) as document:
        assert "Shared PDF API" in document[0].get_text()
        assert isinstance(document, pdfust.Document)


def test_legacy_warning_alias_catches_new_warning() -> None:
    with pytest.warns(pylopdf.PylopdfWarning):
        warnings.warn("legacy", pdfust.PdfustWarning, stacklevel=1)
