"""Write a one-page PDF whose only text is an invisible OCR-style layer with per-word sizes."""

from __future__ import annotations

import sys

import pdfust

doc = pdfust.Document()
page = doc.new_page(width=300, height=200)
page.insert_ocr_text_layer(
    [
        (10, 20, 40, 32, "Quarterly"),
        (44, 20, 70, 31, "report"),
        (74, 20, 100, 34, "summary"),
    ]
)
doc.save(sys.argv[1])
