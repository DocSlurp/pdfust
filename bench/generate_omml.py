"""Create the repository-authored Office Math fixture and optionally export PDF.

Use ``uv run python bench/generate_omml.py --export`` with LibreOffice installed.
Export uses a temporary isolated LibreOffice profile. The PDF is bundled so
routine feature studies do not require an office suite.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

DESTINATION = Path(__file__).resolve().parent / "assets" / "rich"
DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
<w:body>
<w:p><w:r><w:rPr><w:b/><w:sz w:val="36"/></w:rPr><w:t>Native Office equation</w:t></w:r></w:p>
<w:p><w:r><w:t>This document contains an OMML fraction and superscripts, not an equation screenshot.</w:t></w:r></w:p>
<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Bold body</w:t></w:r>
<w:r><w:t xml:space="preserve"> and </w:t></w:r>
<w:r><w:rPr><w:i/></w:rPr><w:t>Italic body</w:t></w:r></w:p>
<w:p><m:oMathPara><m:oMath>
<m:f><m:num><m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup>
<m:r><m:t>+1</m:t></m:r></m:num><m:den><m:r><m:t>y</m:t></m:r></m:den></m:f>
<m:r><m:t>=</m:t></m:r><m:sSup><m:e><m:r><m:t>z</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup>
</m:oMath></m:oMathPara></w:p>
<w:p><w:r><w:t>Unicode fixture: café é \u65e5\u672c\u8a9e 😀 👩🏽‍💻 𠮷</w:t></w:r></w:p>
<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body></w:document>"""
CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml"
ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
RELATIONSHIPS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
Target="word/document.xml"/>
</Relationships>"""


def main() -> None:
    """Write deterministic DOCX source and export with a separate office profile."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    DESTINATION.mkdir(parents=True, exist_ok=True)
    document = DESTINATION / "omml-equations.docx"
    with zipfile.ZipFile(document, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in {
            "[Content_Types].xml": CONTENT_TYPES,
            "_rels/.rels": RELATIONSHIPS,
            "word/document.xml": DOCUMENT_XML,
        }.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, value.encode("utf-8"))
    if args.export:
        executable = shutil.which("libreoffice")
        if executable is None:
            parser.error("--export requires LibreOffice on PATH")
        with tempfile.TemporaryDirectory(prefix="pdfust-omml-") as profile:
            subprocess.run(  # noqa: S603 - resolved executable and repository-authored input.
                [
                    executable,
                    "--headless",
                    f"-env:UserInstallation={Path(profile).as_uri()}",
                    "--convert-to",
                    "pdf:writer_pdf_Export",
                    "--outdir",
                    str(DESTINATION),
                    str(document),
                ],
                check=True,
                timeout=60,
            )
    print(document)


if __name__ == "__main__":
    main()
