"""Native streaming uses open files and restores writer state after failures."""

from __future__ import annotations

import io
import os
from typing import BinaryIO, cast

import pytest

from pdfust.pdfust_core import PdfError, _Document


@pytest.mark.parametrize("object_streams", [False, True])
def test_open_file_writer_matches_byte_writer(one_page_pdf: bytes, *, object_streams: bool) -> None:
    doc = _Document.load_bytes(one_page_pdf)
    expected = doc.save_bytes_with_object_streams() if object_streams else doc.save_bytes()
    target = io.BytesIO()

    doc.save_to_file(target, object_streams=object_streams)

    assert target.getvalue() == expected


@pytest.mark.parametrize("object_streams", [False, True])
def test_file_writer_failure_preserves_serialization_state(one_page_pdf: bytes, *, object_streams: bool) -> None:
    class RefusingFile:
        def write(self, _data: bytes) -> int:
            message = "simulated disk refusal"
            raise OSError(message)

        def flush(self) -> None:
            pass

    doc = _Document.load_bytes(one_page_pdf)
    expected = doc.save_bytes_with_object_streams() if object_streams else doc.save_bytes()
    with pytest.raises(PdfError, match="simulated disk refusal"):
        doc.save_to_file(cast("BinaryIO", RefusingFile()), object_streams=object_streams)

    actual = doc.save_bytes_with_object_streams() if object_streams else doc.save_bytes()
    assert actual == expected


def test_open_file_writer_handles_short_writes_and_bounds_copies(one_page_pdf: bytes) -> None:
    class ShortFile:
        def __init__(self) -> None:
            self.data = bytearray()

        def write(self, data: bytes) -> int:
            assert len(data) <= 64 * 1024
            count = min(len(data), 101)
            self.data.extend(data[:count])
            return count

        def flush(self) -> None:
            pass

    doc = _Document.load_bytes(one_page_pdf)
    doc.embfile_add("large", os.urandom(200_000), None, None, None)
    target = ShortFile()
    doc.save_to_file(cast("BinaryIO", target))
    assert bytes(target.data) == doc.save_bytes()


def test_encrypted_file_writer_repeats_password_validation(one_page_pdf: bytes) -> None:
    doc = _Document.load_bytes(one_page_pdf)
    target = io.BytesIO()
    with pytest.raises(PdfError, match="127"):
        doc.save_encrypted_to_file(target, "x" * 128, "owner", 0, bytes(32))
    assert target.getvalue() == b""
    assert doc.page_count() == 1
