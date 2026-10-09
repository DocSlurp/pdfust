"""Check the new distribution identity and shared compatible Python surface."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

import jev_pdf
import pylopdf


def test_both_imports_share_the_complete_public_api() -> None:
    assert jev_pdf.__version__ == pylopdf.__version__
    assert jev_pdf.__all__ == pylopdf.__all__
    for name in pylopdf.__all__:
        assert getattr(jev_pdf, name) is getattr(pylopdf, name)


def test_new_api_creates_pdfs_readable_through_compatible_import() -> None:
    with jev_pdf.Document() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Shared PDF API")
        data = document.tobytes()
    with pylopdf.open(stream=data) as document:
        assert "Shared PDF API" in document[0].get_text()
        assert isinstance(document, jev_pdf.Document)


def test_distribution_metadata_and_typing_files() -> None:
    distribution = metadata.distribution("jev-pdf")
    assert distribution.metadata["Name"] == "jev-pdf"
    assert distribution.version == jev_pdf.__version__
    assert distribution.metadata["Author-email"] == "Yusuke Hayashi <yusuke8h@gmail.com>"
    assert all(
        "pylopdf-fonts-" in dependency or "pylopdf-ocr-models" in dependency
        for dependency in distribution.requires or []
    )
    assert Path(jev_pdf.__file__).with_name("__init__.pyi").is_file()
    assert Path(jev_pdf.__file__).with_name("py.typed").is_file()
    assert Path(pylopdf.__file__).with_name("py.typed").is_file()
