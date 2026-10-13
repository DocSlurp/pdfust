"""Hold the Rust Markdown port byte-identical to the Python builder.

`rust/src/markdown.rs` ports the single-page form of `_markdown.py` so the Node
binding can produce Markdown without Python. `_Document.page_markdown` runs that
port; these tests compare it with `Page.to_markdown()` so drift in either
implementation fails the ordinary Python suite, not only the Node parity tests.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from conftest import build_raw_pdf

import pdfust

ASSETS = Path(__file__).parent / "assets" / "real_world"
MAX_PAGES = 8
STRATEGIES: tuple[str | None, ...] = ("lines", "text", None)


def _rust_markdown(doc: pdfust.Document, pno: int, strategy: str | None, max_size: int | None = 64 << 20) -> str:
    return doc._doc.page_markdown(pno + 1, strategy, max_size)  # noqa: SLF001 - the Rust port has no public entry


def _assert_parity(doc: pdfust.Document, pno: int, label: str) -> None:
    for strategy in STRATEGIES:
        expected = doc[pno].to_markdown(table_strategy=strategy)  # type: ignore[arg-type]
        actual = _rust_markdown(doc, pno, strategy)
        assert actual == expected, f"{label} p{pno + 1} table_strategy={strategy!r}"


@pytest.mark.parametrize("name", sorted(path.name for path in ASSETS.glob("*.pdf")))
def test_rust_markdown_matches_python_on_real_world_pages(name: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        doc = pdfust.open(ASSETS / name)
        for pno in range(min(doc.page_count, MAX_PAGES)):
            _assert_parity(doc, pno, name)


def _text(x: float, y: float, size: float, text: str, mode: int = 0) -> str:
    return f"BT {mode} Tr /F1 {size} Tf {x} {y} Td ({text}) Tj ET\n"


def _generated(*, invisible: bool = False) -> pdfust.Document:
    """Headings, wrapped prose, lists, a ruled and a borderless table, optional OCR-style text."""
    content = "".join(
        [
            _text(50, 780, 22, "Quarterly report"),
            _text(50, 750, 16, "Summary"),
            _text(50, 720, 11, "The committee simplified the review"),
            _text(50, 706, 11, "process and kept the old deadlines."),
            _text(50, 680, 11, "- first item with * and _ marks"),
            _text(50, 666, 11, "2. second item"),
        ]
    )
    left, top, width, height = 50, 640, 240, 60
    for row in range(4):
        y = top - row * height / 3
        content += f"{left} {y} m {left + width} {y} l S\n"
    for col in range(4):
        x = left + col * width / 3
        content += f"{x} {top} m {x} {top - height} l S\n"
    for row, values in enumerate((("Name", "Qty", "Cost"), ("Bolt", "4", "1.20"), ("Nut", "9", "0.35"))):
        for col, value in enumerate(values):
            content += _text(left + 5 + col * width / 3, top - 14 - row * height / 3, 10, value)
    for row, values in enumerate(
        (("Part", "Count", "Price"), ("Washer", "12", "0.05"), ("Screw", "30", "0.10"), ("Rivet", "7", "0.40"))
    ):
        for col, value in enumerate(values):
            content += _text(50 + col * 90, 540 - row * 14, 10, value)
    if invisible:
        content += _text(50, 400, 11, "hidden layer words", mode=3)
    objects: dict[int, bytes | str] = {
        1: "<< /Type /Catalog /Pages 2 0 R >>",
        2: "<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
        3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        4: (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>"
        ),
        5: f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
    }
    return pdfust.open(stream=build_raw_pdf(objects))


def test_rust_markdown_matches_python_on_generated_structure() -> None:
    doc = _generated()
    _assert_parity(doc, 0, "generated")


def test_rust_markdown_follows_invisible_text_setting() -> None:
    doc = _generated(invisible=True)
    _assert_parity(doc, 0, "invisible")
    assert "hidden layer words" in _rust_markdown(doc, 0, None)
    doc.skip_invisible_text = True
    _assert_parity(doc, 0, "invisible-skipped")
    assert "hidden" not in _rust_markdown(doc, 0, None)


def test_rust_markdown_rejects_bad_strategy_and_output_over_limit() -> None:
    doc = _generated()
    with pytest.raises(ValueError, match="table_strategy"):
        _rust_markdown(doc, 0, "grid")
    with pytest.raises(pdfust.LimitError) as exc:
        _rust_markdown(doc, 0, None, 8)
    assert exc.value.code == "markdown_output_size"
