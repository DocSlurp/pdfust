"""Emit Python-API reference output for the Node parity tests.

Usage: python parity.py <pdf> [max_pages]; prints one JSON document on stdout.
"""

from __future__ import annotations

import json
import sys

import pdfust


def scan_summary(page) -> dict:
    scan = page.scan()
    return {
        "stats": scan["stats"],
        "spans": len(scan["spans"]),
        "images": [[i["width"], i["height"], round(i["dpi"], 3), i["stencil"]] for i in scan["images"]],
        "first": [[s["text"], s["font"], s["render_mode"], s["glyphs"]] for s in scan["spans"][:5]],
    }


def main() -> None:
    path = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    doc = pdfust.open(path)
    out = {"pageCount": doc.page_count, "pages": []}
    for pno in range(min(doc.page_count, max_pages)):
        page = doc[pno]
        out["pages"].append(
            {
                "text": page.get_text("text"),
                "markdown": {
                    "lines": page.to_markdown(table_strategy="lines"),
                    "text": page.to_markdown(table_strategy="text"),
                    "none": page.to_markdown(table_strategy=None),
                },
                "size": [page.rect.width, page.rect.height],
                "rotation": page.rotation,
                "tables": [list(t.bbox) for t in page.find_tables("lines")],
                "annots": [[a["type"], list(a["rect"])] for a in page.annots()],
                "links": len(page.get_links()),
                "images": len(page.get_images()),
                "fonts": [[f["name"], f["type"], f["embedded"], f["has_tounicode"], f["is_type3"]] for f in page.get_fonts()],
                "widgets": [[w["kind"], w["name"], w["value"], w["filled"], w["read_only"], w["required"]] for w in page.widgets()],
                "scan": scan_summary(page),
            }
        )
    out["javascript"] = doc.has_javascript()
    out["ocgs"] = [[g["name"], g["visible"]] for g in doc.get_ocgs()]
    out["attachments"] = [[a["name"], a["size"]] for a in doc.embfile_info()]
    out["docFonts"] = len(doc.get_fonts())
    out["formFields"] = [[f["name"], f["type"], f["value"]] for f in doc.get_form_fields()]
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()
