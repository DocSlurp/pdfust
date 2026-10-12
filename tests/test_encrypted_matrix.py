"""Open every encryption variant with the right, owner, wrong and missing password.

Fixtures (assets/encrypted/matrix, see generate_matrix.sh) cover RC4-40/128,
AES-128, AES-256 R5/R6, empty vs user password, encrypted vs clear metadata, and
classic xref vs xref streams, with /Encrypt indirect (qpdf) or inline in the
trailer / xref stream (MuPDF).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import pdfust

MATRIX = Path(__file__).parent / "assets" / "encrypted" / "matrix"
FILES = sorted(MATRIX.glob("*.pdf"))
USER_FILES = [f for f in FILES if "-user-" in f.name]
EMPTY_FILES = [f for f in FILES if "-empty-" in f.name]
IDS = {f: f.stem for f in FILES}


def _text(path: Path, password: str | None) -> str:
    """First-page text, normalised so "page one" (qpdf set) and "page 1" (MuPDF set) match."""
    doc = pdfust.open(path, password=password) if password is not None else pdfust.open(path)
    return doc.get_page_text(0).lower().replace("page one", "page 1")


def test_matrix_is_populated() -> None:
    assert len(USER_FILES) >= 24
    assert len(EMPTY_FILES) >= 24


@pytest.mark.parametrize("path", FILES, ids=IDS.get)
def test_owner_password_opens_and_decrypts(path: Path) -> None:
    assert "page 1" in _text(path, "ownerpw")


@pytest.mark.parametrize("path", USER_FILES, ids=IDS.get)
def test_user_password_variants(path: Path) -> None:
    assert "page 1" in _text(path, "userpw")
    with pytest.raises(pdfust.PasswordError):
        pdfust.open(path, password="wrong")
    with pytest.raises(pdfust.EncryptedDocumentError):
        _ = pdfust.open(path).page_count


@pytest.mark.parametrize("path", EMPTY_FILES, ids=IDS.get)
def test_empty_user_password_opens_without_password(path: Path) -> None:
    assert "page 1" in _text(path, None)
    assert "page 1" in _text(path, "")


@pytest.mark.parametrize("path", FILES, ids=IDS.get)
def test_peek_metadata_with_passwords(path: Path) -> None:
    password = "userpw" if "-user-" in path.name else None
    meta = pdfust.peek_metadata(path, password=password) if password else pdfust.peek_metadata(path)
    assert meta["page_count"] == 2 if isinstance(meta, dict) else meta.page_count == 2
    owner = pdfust.peek_metadata(path, password="ownerpw")
    assert owner["page_count"] == 2 if isinstance(owner, dict) else owner.page_count == 2


def test_unsupported_security_handler_is_not_a_password_problem(tmp_path: Path) -> None:
    source = (MATRIX / "mu-aes-256-user-classic.pdf").read_bytes()
    assert b"/Filter/Standard" in source
    path = tmp_path / "custom-handler.pdf"
    path.write_bytes(source.replace(b"/Filter/Standard", b"/Filter/Standar2"))
    for password in (None, "userpw"):
        with pytest.raises(pdfust.UnsupportedEncryptionError, match="unsupported"):
            pdfust.open(path, password=password) if password else pdfust.open(path)
    assert issubclass(pdfust.UnsupportedEncryptionError, pdfust.PdfError)
    assert not issubclass(pdfust.UnsupportedEncryptionError, pdfust.PasswordError)


def test_unsupported_revision_is_not_a_password_problem(tmp_path: Path) -> None:
    source = (MATRIX / "q-aes-128-user-enc-classic.pdf").read_bytes()
    assert b"/R 4" in source
    path = tmp_path / "future-revision.pdf"
    path.write_bytes(source.replace(b"/R 4", b"/R 9"))
    for password in (None, "userpw"):
        with pytest.raises(pdfust.UnsupportedEncryptionError):
            pdfust.open(path, password=password) if password else pdfust.open(path)
