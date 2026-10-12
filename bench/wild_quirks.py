"""Build the wild-v1 "PDF production quirks" DEV dataset, using CPU only.

Usage::

    python -m bench.wild_quirks --directory bench/results/pdf-master-artifacts/wild-v1

Writes ``quirks/{quirk_id}/{doc_id}.pdf`` for cases derived from a wild-v1
born-digital PDF (so the document's ``docs/{doc_id}/truth.json`` scores them)
and ``quirks/{quirk_id}/raw-{source_doc_id}.pdf`` for small hand-written PDFs
whose exact visible text is stored in the manifest as ``expected_text``.
``quirks/manifest.json`` records, per case, the quirk, tool versions and exact
commands, measured structure (header, producer, xref kind, object streams,
encryption, stream filters, fonts/encodings/ToUnicode, pages, SHA-256) and a
validation block with pypdf, pdftotext, PyMuPDF and pdfust text extraction.
Extraction failures are recorded as data. See ``bench/WILD_CORPUS.md``.

Families: producer, structure, encryption, filter (re-produced L0 PDFs) and
font_encoding, layout_transform, annotation_form (raw builders in
``bench/wild_quirks_raw.py``). No network, hosted model or GPU is used.
"""

# Heterogeneous manifest dictionaries retain tool observations and parameters.
# ruff: noqa: EM101, EM102, TRY003, PLR2004, PLR0912, C901, S603, PLC0415, ANN401, PLR0911, E501, D401

from __future__ import annotations

import argparse
import hashlib
import io
import json
import multiprocessing
import os
import re
import resource
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import warnings
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import wild_quirks_raw as raw
from bench.silver import guard_path
from bench.wild_flatten import SOURCE_DATE_EPOCH, Recorder

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
SCHEMA = 1
FAMILIES = ("producer", "structure", "encryption", "filter", "font_encoding", "layout_transform", "annotation_form")
OWNER_PASSWORD = "wild-owner"  # noqa: S105 - fixed synthetic test password, recorded in the manifest.
USER_PASSWORD = "wild"  # noqa: S105
NOTO = Path("/usr/share/fonts/noto")
NOTO_CJK = Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc")
CJK_INDEX = {"ja": 0, "ko": 1, "zh-CN": 2, "zh-TW": 3}
PDFA_DEF = Path("/usr/share/ghostscript/lib/PDFA_def.ps")
SRGB_ICC = Path("/usr/share/ghostscript/iccprofiles/srgb.icc")

# Measured by building the dataset twice: every other case is byte-identical.
NONDETERMINISTIC = {
    "pdftocairo_pdf": "Cairo writes the wall-clock CreationDate inside a compressed object stream "
    "and ignores SOURCE_DATE_EPOCH",
    "encrypt_aes256_r6": "qpdf draws random R6 validation/key salts and file encryption key",
    "encrypt_aes256_r6_user_password": "qpdf draws random R6 validation/key salts and file encryption key",
}

# ---------------------------------------------------------------------------
# Case plan. Document subsets are chosen where each quirk matters: CJK Type 3
# Chromium fonts, LibreOffice TrueType subsets, RTL, Cyrillic, multi-page.

GS_LEVELS = {"1.3": "13", "1.4": "14", "1.5": "15", "1.7": "17"}
GS_DOCS = ["w-ruled-invoice-01", "w-ruled-facture-03", "w-unnamed-journal-12", "w-negative-memo-22"]
DOC_PLAN: list[tuple[str, str, list[str], dict[str, Any]]] = [
    *[(f"gs_pdfwrite_{tag}", "producer", GS_DOCS, {"tool": "gs", "level": level}) for level, tag in GS_LEVELS.items()],
    ("gs_pdfa2b", "producer", ["w-ruled-invoice-01", "w-ruled-quarterly-02", "w-wrapped-delegacja-09"], {"tool": "gs_pdfa"}),
    ("ps2pdf_roundtrip", "producer",
     ["w-ruled-invoice-01", "w-ruled-facture-03", "w-ruled-quarterly-02", "w-unnamed-journal-12", "w-borderless-specsheet-04"],
     {"tool": "ps2pdf"}),
    ("pdftocairo_pdf", "producer",
     ["w-ruled-invoice-01", "w-ruled-facture-03", "w-merged-grant-13", "w-unnamed-labappendix-11"], {"tool": "pdftocairo"}),
    ("qpdf_object_streams", "structure",
     ["w-ruled-invoice-01", "w-ruled-quarterly-02", "w-mixed-research-16", "w-pairs-plans-19"],
     {"tool": "qpdf", "args": ["--object-streams=generate"]}),
    ("qpdf_uncompressed_classic", "structure", ["w-ruled-facture-03", "w-unnamed-journal-12", "w-merged-budget-15"],
     {"tool": "qpdf", "args": ["--object-streams=disable", "--compress-streams=n", "--decode-level=generalized"]}),
    ("qpdf_linearized", "structure", ["w-negative-newsletter-23", "w-mixed-research-16", "w-unnamed-labappendix-10"],
     {"tool": "qpdf", "args": ["--linearize"]}),
    ("qpdf_qdf", "structure", ["w-ruled-invoice-01", "w-wrapped-delegacja-09"],
     {"tool": "qpdf", "args": ["--qdf", "--object-streams=disable"]}),
    ("incremental_update", "structure",
     ["w-ruled-invoice-01", "w-ruled-facture-03", "w-merged-grant-13", "w-wrapped-expense-07"], {"tool": "incremental"}),
    *[
        (f"encrypt_{name}", "encryption", ["w-ruled-invoice-01", "w-unnamed-journal-12", "w-borderless-specsheet-04"],
         {"tool": "qpdf_encrypt", "bits": bits, "aes": aes, "user": ""})
        for name, bits, aes in (("rc4_40_r2", 40, False), ("rc4_128_r3", 128, False), ("aes128_r4", 128, True),
                                ("aes256_r6", 256, True))
    ],
    ("encrypt_aes256_r6_user_password", "encryption", ["w-ruled-facture-03", "w-negative-memo-22"],
     {"tool": "qpdf_encrypt", "bits": 256, "aes": True, "user": USER_PASSWORD}),
    *[
        (f"filter_{key}", "filter", ["w-ruled-invoice-01", "w-unnamed-journal-12", "w-wrapped-itinerary-08"],
         {"tool": "reencode", "filter": key})
        for key in raw.FILTER_ENCODERS
    ],
]  # fmt: skip

LATIN_DOCS = ["w-ruled-invoice-01", "w-ruled-facture-03"]
RAW_PLAN: list[tuple[str, str, list[str], dict[str, Any]]] = [
    ("std14_winansi", "font_encoding", ["w-ruled-facture-03", "w-ruled-quarterly-02", "w-borderless-jornadas-06"],
     {"builder": "simple", "encoding": "WinAnsiEncoding", "fonts": ["Helvetica", "Times-Roman", "Courier"]}),
    ("std14_macroman", "font_encoding", ["w-ruled-facture-03", "w-ruled-quarterly-02"],
     {"builder": "simple", "encoding": "MacRomanEncoding", "fonts": ["Times-Roman", "Helvetica"]}),
    ("std14_standard_encoding", "font_encoding", ["w-ruled-invoice-01", "w-negative-newsletter-23"],
     {"builder": "simple", "encoding": None, "fonts": ["Helvetica", "Times-Roman"]}),
    ("std14_differences_standard_names", "font_encoding",
     ["w-ruled-facture-03", "w-ruled-quarterly-02", "w-borderless-jornadas-06"], {"builder": "differences"}),
    ("type3_gnames_no_tounicode", "font_encoding", ["w-ruled-facture-03", "w-unnamed-journal-12"],
     {"builder": "type3", "scheme": "g", "tounicode": False}),
    ("type3_gnames_tounicode", "font_encoding", ["w-ruled-facture-03", "w-unnamed-journal-12"],
     {"builder": "type3", "scheme": "g", "tounicode": True}),
    ("type3_uninames_no_tounicode", "font_encoding",
     ["w-ruled-facture-03", "w-wrapped-itinerary-08", "w-borderless-agenda-05"],
     {"builder": "type3", "scheme": "uni", "tounicode": False}),
    ("type3_afii_no_tounicode", "font_encoding", ["w-unnamed-journal-12"],
     {"builder": "type3", "scheme": "afii", "tounicode": False}),
    ("type3_afii_tounicode", "font_encoding", ["w-unnamed-journal-12"],
     {"builder": "type3", "scheme": "afii", "tounicode": True}),
    ("symbol_bullets", "font_encoding", LATIN_DOCS, {"builder": "symbol", "font": "Symbol", "bullets": ["•", "→", "±"]}),
    ("zapfdingbats_bullets", "font_encoding", LATIN_DOCS,
     {"builder": "symbol", "font": "ZapfDingbats", "bullets": ["✓", "➔", "●", "❖"]}),
    ("embedded_opentype_identity_h", "font_encoding",
     ["w-ruled-facture-03", "w-unnamed-journal-12", "w-negative-memo-22", "w-mixed-research-17",
      "w-pairs-catering-21", "w-borderless-specsheet-04"], {"builder": "embedded", "strip": False}),
    ("embedded_opentype_no_tounicode", "font_encoding",
     ["w-ruled-facture-03", "w-unnamed-journal-12", "w-negative-memo-22", "w-borderless-specsheet-04"],
     {"builder": "embedded", "strip": True}),
    ("vertical_cjk_identity_v", "font_encoding",
     ["w-borderless-specsheet-04", "w-pairs-plans-19", "w-unnamed-labappendix-11"], {"builder": "vertical"}),
    ("form_xobject_twice", "layout_transform", LATIN_DOCS, {"builder": "form_twice"}),
    ("invisible_text_over_rect", "layout_transform", LATIN_DOCS, {"builder": "invisible"}),
    ("tz_tc_tj_false_gaps", "layout_transform", LATIN_DOCS, {"builder": "spacing"}),
    ("per_glyph_tm", "layout_transform", LATIN_DOCS, {"builder": "per_glyph"}),
    ("fake_bold_overprint", "layout_transform", LATIN_DOCS, {"builder": "fake_bold"}),
    ("text_outside_cropbox", "layout_transform", LATIN_DOCS, {"builder": "outside_crop"}),
    ("rotate_90", "layout_transform", LATIN_DOCS, {"builder": "rotate", "rotate": 90}),
    ("rotate_270", "layout_transform", LATIN_DOCS, {"builder": "rotate", "rotate": 270}),
    ("cropbox_nonzero_origin", "layout_transform", LATIN_DOCS, {"builder": "crop_origin"}),
    ("userunit_2", "layout_transform", LATIN_DOCS, {"builder": "user_unit"}),
    ("freetext_annotation", "annotation_form", LATIN_DOCS, {"builder": "freetext"}),
    ("acroform_appearance_only", "annotation_form", LATIN_DOCS, {"builder": "acroform", "stale": False}),
    ("acroform_stale_appearance", "annotation_form", LATIN_DOCS, {"builder": "acroform", "stale": True}),
]  # fmt: skip

EMBED_FONTS: dict[str, tuple[Path, int]] = {
    "w-ruled-facture-03": (NOTO / "NotoSans-Regular.ttf", 0),
    "w-unnamed-journal-12": (NOTO / "NotoSans-Regular.ttf", 0),
    "w-negative-memo-22": (NOTO / "NotoSansArabic-Regular.ttf", 0),
    "w-mixed-research-17": (NOTO / "NotoSansDevanagari-Regular.ttf", 0),
    "w-pairs-catering-21": (NOTO / "NotoSansThai-Regular.ttf", 0),
    "w-borderless-specsheet-04": (NOTO_CJK, CJK_INDEX["ja"]),
    "w-pairs-plans-19": (NOTO_CJK, CJK_INDEX["zh-TW"]),
    "w-unnamed-labappendix-11": (NOTO_CJK, CJK_INDEX["zh-CN"]),
}


# ---------------------------------------------------------------------------
# Truth helpers


def load_truth(directory: Path, doc_id: str) -> dict[str, Any]:
    """Read one wild-v1 truth file."""
    return json.loads(guard_path(directory / "docs" / doc_id / "truth.json").read_text(encoding="utf-8"))


def base_pdf(directory: Path, doc_id: str) -> Path:
    """Born-digital L0 PDF for a document (tagged variant, falling back to source.pdf)."""
    tagged = guard_path(directory / "variants" / doc_id / "L0_tagged.pdf")
    return tagged if tagged.exists() else guard_path(directory / "docs" / doc_id / "source.pdf")


TEXT_KINDS = {"heading", "paragraph", "header", "footer", "callout", "sidebar", "footnote"}


def truth_text(truth: dict[str, Any]) -> str:
    """Native text expected in an L0 PDF: text blocks, lists, captions and non-image tables."""
    parts: list[str] = []
    for block in truth["blocks"]:
        kind = block["kind"]
        if kind in TEXT_KINDS:
            parts.append(block["text"])
        elif kind == "list":
            parts.extend(block["items"])
        elif kind == "table" and block.get("rendering") not in {"screenshot", "chart_data"}:
            parts.extend(" ".join(str(cell) for cell in row if cell) for row in block["values"])
            parts.append(block.get("caption") or "")
        elif kind == "figure":
            parts.append(block.get("caption") or "")
    return "\n".join(p for p in parts if p)


def truth_lines(
    truth: dict[str, Any], *, width: int, limit: int, accept: Callable[[str], bool], kinds: Iterable[str] = ()
) -> list[str]:
    """Pick up to ``limit`` wrapped lines from text blocks and table rows in reading order."""
    wanted = set(kinds) or {*TEXT_KINDS, "list", "table"}
    lines: list[str] = []
    seen: set[str] = set()
    for block in truth["blocks"]:
        kind = block["kind"]
        if kind not in wanted:
            continue
        if kind == "list":
            texts = block["items"]
        elif kind == "table":
            if block.get("rendering") in {"screenshot", "chart_data"}:
                continue
            texts = ["   ".join(str(cell) for cell in row if cell) for row in block["values"][:3]]
        else:
            texts = block["text"].split("\n")
        for text in texts:
            for line in raw.wrap(" ".join(text.replace("­", "").split()), width):
                if line in seen or not accept(line):
                    continue
                seen.add(line)
                lines.append(line)
                if len(lines) >= limit:
                    return lines
    return lines


def _encodable(table: dict[str, int]) -> Callable[[str], bool]:
    return lambda line: raw.can_encode(line, table) and len(line) > 2


def _named(line: str) -> bool:
    try:
        for char in set(line):
            raw.glyph_name(char, "standard")
    except ValueError:
        return False
    return len(line) > 2


def _covered(font_path: Path) -> Callable[[str], bool]:
    import pymupdf

    font = pymupdf.Font(fontfile=str(font_path))
    return lambda line: len(line) > 2 and all(c.isspace() or font.has_glyph(ord(c)) for c in line)


# ---------------------------------------------------------------------------
# Case specifications (built in the parent; executed in workers)


def plan(directory: Path) -> list[dict[str, Any]]:
    """Return every case specification in a fixed order."""
    cases: list[dict[str, Any]] = []
    for quirk_id, family, docs, params in DOC_PLAN:
        cases.extend(
            {"quirk_id": quirk_id, "family": family, "doc_id": doc, "source_doc_id": doc, "params": params,
             "case_id": f"{quirk_id}/{doc}", "relative_path": f"quirks/{quirk_id}/{doc}.pdf"}
            for doc in docs
        )  # fmt: skip
    for quirk_id, family, docs, params in RAW_PLAN:
        for index, doc in enumerate(docs):
            spec = {"quirk_id": quirk_id, "family": family, "doc_id": None, "source_doc_id": doc,
                    "case_id": f"{quirk_id}/raw-{doc}", "relative_path": f"quirks/{quirk_id}/raw-{doc}.pdf"}  # fmt: skip
            spec["params"] = {**params, **raw_inputs(load_truth(directory, doc), doc, index, params)}
            cases.append(spec)
    return cases


def _nfc_block(block: dict[str, Any]) -> dict[str, Any]:
    out = dict(block)
    if "text" in out:
        out["text"] = unicodedata.normalize("NFC", out["text"])
    if "items" in out:
        out["items"] = [unicodedata.normalize("NFC", item) for item in out["items"]]
    if "values" in out:
        out["values"] = [[unicodedata.normalize("NFC", str(c)) if c else c for c in row] for row in out["values"]]
    return out


def raw_inputs(truth: dict[str, Any], doc: str, index: int, params: dict[str, Any]) -> dict[str, Any]:
    """Select the truth-derived lines each raw builder needs."""
    builder = params["builder"]
    win = _encodable(raw.encoding_table("WinAnsiEncoding"))
    title = truth["metadata"].get("title") or doc
    out: dict[str, Any] = {"title": title}
    if builder == "simple":
        out["font"] = params["fonts"][index % len(params["fonts"])]
        table = raw.encoding_table(params["encoding"] or "StandardEncoding")
        out["lines"] = truth_lines(truth, width=72, limit=10, accept=_encodable(table))
    elif builder == "differences":
        out["font"] = ["Helvetica", "Times-Roman", "Courier"][index % 3]
        # Prefer lines that actually need remapped (non-ASCII) glyph names.
        lines = truth_lines(truth, width=72, limit=40, accept=_named)
        accented = [line for line in lines if any(ord(c) > 0x7E for c in line)]
        out["lines"] = (accented + [line for line in lines if line not in accented])[:10]
    elif builder == "type3":
        accept = (lambda line: len(line) > 2) if params["scheme"] == "g" else _covered(raw.NOTO_SANS)
        # Bitmap glyphs are drawn per precomposed character, so decomposed (NFD) truth text is
        # composed first; expected_text records the NFC form that is actually drawn.
        nfc = {**truth, "blocks": [_nfc_block(b) for b in truth["blocks"]]}
        lines = truth_lines(nfc, width=64, limit=40, accept=_covered(raw.NOTO_SANS))
        lines = [line for line in lines if accept(line)]
        chosen: list[str] = []
        for line in lines:  # Keep at most 220 distinct characters for one simple font.
            if len(set("".join([*chosen, line]))) <= 220:
                chosen.append(line)
            if len(chosen) >= 8:
                break
        out["lines"] = chosen
    elif builder == "symbol":
        out["lines"] = truth_lines(truth, width=64, limit=5, accept=win, kinds={"list", "paragraph"})
    elif builder in {"embedded", "vertical"}:
        font_path, font_index = EMBED_FONTS[doc]
        out["font_path"], out["font_index"] = str(font_path), font_index
        cjk = font_path == NOTO_CJK
        if builder == "vertical":
            out["lines"] = truth_lines(
                truth, width=34, limit=8, accept=_covered(font_path), kinds={"heading", "paragraph", "header"}
            )
        else:
            out["lines"] = truth_lines(truth, width=30 if cjk else 64, limit=12, accept=_covered(font_path))
    elif builder in {"invisible", "outside_crop"}:
        out["visible"] = truth_lines(truth, width=72, limit=3, accept=win, kinds={"heading", "header"})
        out["hidden"] = truth_lines(truth, width=72, limit=4 if builder == "invisible" else 2, accept=win,
                                    kinds={"paragraph"})  # fmt: skip
    elif builder == "freetext":
        out["lines"] = truth_lines(truth, width=72, limit=6, accept=win, kinds={"heading", "paragraph"})
        out["note"] = truth_lines(truth, width=36, limit=2, accept=win, kinds={"callout", "footer", "footnote"}) or [
            "Reviewed and approved"
        ]
    elif builder == "acroform":
        pairs = []
        for line in truth_lines(truth, width=200, limit=60, accept=win, kinds={"paragraph"}):
            label, sep, value = line.partition(":")
            if sep and 0 < len(label) <= 28 and 0 < len(value.strip()) <= 44:
                pairs.append((label.strip() + ":", value.strip()))
        pairs = pairs[:5]
        out["labels"] = [p[0] for p in pairs]
        out["values"] = [p[1] for p in pairs]
        out["stored"] = [f"{v} (rev. 2)" if params["stale"] else None for v in out["values"]]
    else:
        out["lines"] = truth_lines(truth, width=72, limit=8, accept=win)
    return out


def build_raw(spec: dict[str, Any]) -> raw.RawResult:
    """Run the raw builder named in a case specification."""
    p = spec["params"]
    builder, title = p["builder"], p["title"]
    if builder == "simple":
        return raw.build_simple_encoding(p["lines"], p["font"], p["encoding"], title)
    if builder == "differences":
        return raw.build_differences_standard_names(p["lines"], p["font"], title)
    if builder == "type3":
        return raw.build_type3_names(p["lines"], p["scheme"], tounicode=p["tounicode"], title=title)
    if builder == "symbol":
        return raw.build_symbol_bullets(p["lines"], p["font"], p["bullets"], title)
    if builder == "embedded":
        result = raw.build_embedded(p["lines"], Path(p["font_path"]), title, font_index=p["font_index"])
        if p["strip"]:
            result.pdf, removed = raw.strip_tounicode(result.pdf)
            result.code_path += " + wild_quirks_raw.strip_tounicode"
            result.extra["tounicode_removed"] = removed
        return result
    if builder == "vertical":
        return raw.build_vertical(p["lines"], Path(p["font_path"]), title, font_index=p["font_index"])
    simple: dict[str, Callable[..., raw.RawResult]] = {
        "form_twice": raw.build_form_xobject_twice,
        "spacing": raw.build_spacing_operators,
        "per_glyph": raw.build_per_glyph_tm,
        "fake_bold": raw.build_fake_bold,
        "crop_origin": raw.build_cropbox_origin,
        "user_unit": raw.build_user_unit,
    }
    if builder in simple:
        return simple[builder](p["lines"], title)
    if builder == "invisible":
        return raw.build_invisible_over_rect(p["visible"], p["hidden"], title)
    if builder == "outside_crop":
        return raw.build_clipped_outside_cropbox(p["visible"], p["hidden"], title)
    if builder == "rotate":
        return raw.build_rotated_page(p["lines"], p["rotate"], title)
    if builder == "freetext":
        return raw.build_freetext(p["lines"], p["note"], title)
    if builder == "acroform":
        return raw.build_acroform(p["labels"], p["values"], stored=p["stored"], title=title)
    raise ValueError(f"unknown raw builder {builder}")


# ---------------------------------------------------------------------------
# Document-derived builders


def _pdfa_definition(work: Path) -> Path:
    """Copy Ghostscript's PDFA_def.ps with an absolute sRGB profile and no placeholder title."""
    text = PDFA_DEF.read_text(encoding="latin-1")
    text = text.replace("(srgb.icc)", f"({SRGB_ICC})")
    text = re.sub(r"^\[ /Title \(Title\).*\n\s*/DOCINFO pdfmark\n", "", text, flags=re.MULTILINE)
    path = work / "PDFA_def.ps"
    path.write_text(text, encoding="latin-1")
    return path


GS_BASE = ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite"]
QPDF_BASE = ["qpdf", "--warning-exit-0"]


def build_doc_case(spec: dict[str, Any], source: Path, out: Path, recorder: Recorder, work: Path) -> dict[str, Any]:
    """Produce one document-derived variant and return case-specific facts."""
    p = spec["params"]
    tool = p["tool"]
    facts: dict[str, Any] = {}
    if tool == "gs":
        recorder.run([*GS_BASE, f"-dCompatibilityLevel={p['level']}", "-o", out, source])
    elif tool == "gs_pdfa":
        definition = _pdfa_definition(work)
        recorder.run([*GS_BASE, f"--permit-file-read={SRGB_ICC.parent}/", "-dPDFA=2", "-dPDFACompatibilityPolicy=1",
                      "-sColorConversionStrategy=RGB", "-o", out, definition, source])  # fmt: skip
        facts["pdfa_def"] = (
            "Ghostscript lib/PDFA_def.ps with absolute iccprofiles/srgb.icc and the placeholder DOCINFO removed"
        )
    elif tool == "ps2pdf":
        postscript = work / "roundtrip.ps"
        recorder.run([*GS_BASE[:-1], "-sDEVICE=ps2write", "-o", postscript, source])
        recorder.run(["ps2pdf", postscript, out])
    elif tool == "pdftocairo":
        recorder.run(["pdftocairo", "-pdf", source, out])
    elif tool == "qpdf":
        recorder.run([*QPDF_BASE, "--deterministic-id", *p["args"], source, out])
    elif tool == "qpdf_encrypt":
        args = [*QPDF_BASE, "--static-id", "--static-aes-iv", "--allow-weak-crypto", "--encrypt",
                f"--user-password={p['user']}", f"--owner-password={OWNER_PASSWORD}", f"--bits={p['bits']}"]  # fmt: skip
        if p["bits"] == 128:
            args.append(f"--use-aes={'y' if p['aes'] else 'n'}")
        recorder.run([*args, "--", source, out])
        facts["passwords"] = {"user": p["user"], "owner": OWNER_PASSWORD}
    elif tool == "incremental":
        facts.update(incremental_update(source, out))
        recorder.steps.append("pypdf PdfWriter(incremental=True): Info update + FreeText annotation")
    elif tool == "reencode":
        data, count = raw.reencode_content_streams(source.read_bytes(), p["filter"])
        out.write_bytes(data)
        facts["reencoded_streams"] = count
        recorder.steps.append(f"wild_quirks_raw.reencode_content_streams({p['filter']}) via pypdf")
    else:
        raise ValueError(f"unknown tool {tool}")
    return facts


def incremental_update(source: Path, out: Path) -> dict[str, Any]:
    """Append one revision that edits Info and adds a FreeText note, keeping the original bytes."""
    from pypdf import PdfWriter
    from pypdf.annotations import FreeText

    writer = PdfWriter(str(source), incremental=True)
    writer.add_metadata({"/Title": "Revised copy (incremental update)", "/ModDate": "D:20260102000000Z"})
    box = writer.pages[0].mediabox
    note = "Revision 2: reviewed"
    rect = (float(box.left) + 36, float(box.bottom) + 20, float(box.left) + 236, float(box.bottom) + 44)
    writer.add_annotation(0, FreeText(text=note, rect=rect, font="Helvetica", font_size="10pt"))
    buffer = io.BytesIO()
    writer.write(buffer)
    data = buffer.getvalue()
    out.write_bytes(data)
    original = source.read_bytes()
    return {"original_prefix_preserved": data.startswith(original), "appended_bytes": len(data) - len(original),
            "added_annotation_text": note}  # fmt: skip


# ---------------------------------------------------------------------------
# Measurement


FILTER_RE = re.compile(rb"/Filter\s*(\[[^\]]*\]|/[A-Za-z0-9]+)")


def _subset_free(name: str) -> str:
    return re.sub(r"^[A-Z]{6}\+", "", name.lstrip("/"))


def _font_facts(font: Any) -> dict[str, Any]:
    subtype = str(font.get("/Subtype"))
    encoding = font.get("/Encoding")
    if encoding is None:
        encoding_text = "builtin"
    elif hasattr(encoding, "get_object") and hasattr(encoding.get_object(), "keys"):
        encoding = encoding.get_object()
        if "/UseCMap" in encoding or "/CMapName" in encoding:
            encoding_text = f"embedded CMap {encoding.get('/CMapName')}"
        else:
            base = encoding.get("/BaseEncoding")
            diffs = sum(1 for item in encoding.get("/Differences", []) if str(item).startswith("/"))
            encoding_text = f"dict(base={base or 'implicit'}, differences={diffs})"
    else:
        encoding_text = str(encoding)
    facts = {"subtype": subtype, "base_font": _subset_free(str(font.get("/BaseFont", ""))), "encoding": encoding_text,
             "tounicode": "/ToUnicode" in font}  # fmt: skip
    descriptor = font.get("/FontDescriptor")
    if subtype == "/Type0":
        descendant = font["/DescendantFonts"][0].get_object()
        facts["descendant"] = str(descendant.get("/Subtype"))
        descriptor = descendant.get("/FontDescriptor")
    embedded = None
    if descriptor is not None:
        descriptor = descriptor.get_object()
        for key in ("/FontFile", "/FontFile2", "/FontFile3"):
            if key in descriptor:
                embedded = key[1:]
                if key == "/FontFile3":
                    embedded += f"/{str(descriptor[key].get_object().get('/Subtype', '')).lstrip('/')}"
    facts["embedded"] = embedded or ("charprocs" if subtype == "/Type3" else None)
    return facts


def collect_fonts(reader: Any) -> list[dict[str, Any]]:
    """Distinct font descriptions reachable from pages, Form XObjects and annotation appearances."""
    found: dict[str, dict[str, Any]] = {}
    seen: set[int] = set()

    def visit(resources: Any, depth: int) -> None:
        if resources is None or depth > 8:
            return
        resources = resources.get_object()
        for font in (resources.get("/Font") or {}).values():
            try:
                facts = _font_facts(font.get_object())
            except Exception as error:
                facts = {"error": f"{type(error).__name__}: {error}"}
            found.setdefault(json.dumps(facts, sort_keys=True), facts)
        for xobject in (resources.get("/XObject") or {}).values():
            stream = xobject.get_object()
            if id(stream) in seen:
                continue
            seen.add(id(stream))
            if stream.get("/Subtype") == "/Form":
                visit(stream.get("/Resources"), depth + 1)

    for page in reader.pages:
        visit(page.get("/Resources"), 0)
        for annot in page.get("/Annots") or []:
            appearance = (annot.get_object().get("/AP") or {}).get("/N")
            if appearance is not None and hasattr(appearance.get_object(), "get_data"):
                visit(appearance.get_object().get("/Resources"), 1)
    return sorted(found.values(), key=lambda f: json.dumps(f, sort_keys=True))


def measure_structure(path: Path, password: str) -> dict[str, Any]:
    """Byte-level and pypdf-level structure facts."""
    data = path.read_bytes()
    header = re.match(rb"%PDF-(\d\.\d)", data)
    has_table = re.search(rb"(?:^|[\r\n])xref[ \t]*[\r\n]", data) is not None
    has_stream = re.search(rb"/Type\s*/XRef\b", data) is not None
    filters: Counter[str] = Counter()
    for match in FILTER_RE.finditer(data):
        filters.update(name.decode() for name in re.findall(rb"/[A-Za-z0-9]+", match.group(1)))
    facts: dict[str, Any] = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "header_version": header.group(1).decode() if header else None,
        "xref_kind": "both" if has_table and has_stream else "table" if has_table else "stream" if has_stream else None,
        "xref_sections": len(re.findall(rb"startxref", data)),
        "eof_markers": data.count(b"%%EOF"),
        "object_streams": re.search(rb"/Type\s*/ObjStm\b", data) is not None,
        "image_xobjects": len(re.findall(rb"/Subtype\s*/Image\b", data)),
        "linearized": re.search(rb"/Linearized\s", data[:4096]) is not None,
        "stream_filters": dict(sorted(filters.items())),
    }
    try:
        from pypdf import PdfReader

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reader = PdfReader(io.BytesIO(data))
            encryption = None
            if reader.is_encrypted:
                encrypt = reader.trailer["/Encrypt"].get_object()
                cfm = None
                if "/CF" in encrypt:
                    cfm = str(encrypt["/CF"].get_object().get("/StdCF", {}).get("/CFM"))
                encryption = {"filter": str(encrypt.get("/Filter")), "V": int(encrypt.get("/V", 0)),
                              "R": int(encrypt.get("/R", 0)), "length_bits": int(encrypt.get("/Length", 40)),
                              "cfm": cfm, "decrypt": str(reader.decrypt(password))}  # fmt: skip
            facts["encryption"] = encryption
            metadata = reader.metadata
            facts["producer"] = str(metadata.get("/Producer")) if metadata and metadata.get("/Producer") else None
            catalog_version = reader.trailer["/Root"].get_object().get("/Version")
            facts["catalog_version"] = str(catalog_version).lstrip("/") if catalog_version else None
            facts["page_count"] = len(reader.pages)
            fonts = collect_fonts(reader)
            facts["fonts"] = fonts
            facts["font_subtypes"] = sorted({f.get("descendant", f.get("subtype")) for f in fonts if "subtype" in f})
            facts["font_encodings"] = sorted({f["encoding"] for f in fonts if "encoding" in f})
            with_map = sum(1 for f in fonts if f.get("tounicode"))
            facts["tounicode"] = "none" if not with_map else "all" if with_map == len(fonts) else "some"
    except Exception as error:
        facts["pypdf_structure_error"] = f"{type(error).__name__}: {error}"[:400]
    return facts


def _tokens(text: str) -> Counter[str]:
    return Counter(unicodedata.normalize("NFKC", text).split())


def token_recall(expected: str, actual: str | None) -> float | None:
    """Multiset recall of NFKC whitespace tokens; strict, so false gaps lower it."""
    if actual is None:
        return None
    wanted = _tokens(expected)
    total = sum(wanted.values())
    if not total:
        return None
    return round(sum((wanted & _tokens(actual)).values()) / total, 4)


def _visible_chars(text: str) -> int:
    return sum(1 for c in text if not c.isspace())


def extract_all(path: Path, password: str) -> dict[str, dict[str, Any]]:
    """Run pypdf, pdftotext, PyMuPDF and pdfust text extraction; failures become data."""
    results: dict[str, dict[str, Any]] = {}

    def attempt(name: str, function: Callable[[], str]) -> None:
        start = time.perf_counter()
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                text = function()
            results[name] = {"ok": True, "chars": _visible_chars(text), "text": text, "warnings": len(caught)}
        except Exception as error:
            results[name] = {
                "ok": False,
                "chars": None,
                "text": None,
                "error": f"{type(error).__name__}: {error}"[:400],
            }
        results[name]["seconds"] = round(time.perf_counter() - start, 4)

    def with_pypdf() -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        if reader.is_encrypted:
            reader.decrypt(password)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def with_pdftotext() -> str:
        argv = ["pdftotext", "-enc", "UTF-8"]
        if password:
            argv += ["-upw", password]
        result = subprocess.run([*argv, str(path), "-"], capture_output=True, check=False, timeout=120)
        if result.returncode:
            raise RuntimeError(f"exit {result.returncode}: {result.stderr.decode(errors='replace').strip()[-300:]}")
        return result.stdout.decode("utf-8", errors="replace")

    def with_pymupdf() -> str:
        import pymupdf

        with pymupdf.open(str(path)) as document:
            if document.needs_pass and not document.authenticate(password):
                raise RuntimeError("authentication failed")
            return "\n".join(page.get_text() for page in document)

    def with_pdfust() -> str:
        import pdfust

        document = pdfust.open(str(path), password=password or None)
        try:
            return document.get_text()
        finally:
            document.close()

    attempt("pypdf", with_pypdf)
    attempt("pdftotext", with_pdftotext)
    attempt("pymupdf", with_pymupdf)
    attempt("pdfust", with_pdfust)
    return results


def validate(path: Path, password: str, reference: str, hidden: str = "") -> dict[str, Any]:
    """Validation block: open/extract per tool plus token recall against the reference text.

    ``hidden_token_recall`` measures how much text that should not be visible
    (render mode 3, outside the CropBox) each tool still returned.
    """
    block: dict[str, Any] = {}
    for tool, result in extract_all(path, password).items():
        text = result.pop("text")
        result["token_recall"] = token_recall(reference, text)
        if hidden:
            result["hidden_token_recall"] = token_recall(hidden, text)
        block[tool] = result
    block["pypdf_opens"] = block["pypdf"]["ok"]
    return block


# ---------------------------------------------------------------------------
# Worker


def run_case(arguments: tuple[dict[str, Any], str]) -> dict[str, Any]:
    """Build, measure and validate one case in a worker process."""
    spec, directory_text = arguments
    directory = Path(directory_text)
    out = guard_path(directory / spec["relative_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    start, usage = time.perf_counter(), _usage()
    record: dict[str, Any] = {key: spec[key] for key in ("case_id", "quirk_id", "family", "doc_id", "source_doc_id")}
    record["path"] = spec["relative_path"]
    record["tool"] = spec["params"].get("tool", "raw")
    password = ""
    with tempfile.TemporaryDirectory(prefix="wild-quirks-") as temp:
        work = Path(temp)
        recorder = Recorder(replacements={temp: "$WORK", str(directory): "$WILD"})
        try:
            if spec["doc_id"]:
                source = base_pdf(directory, spec["doc_id"])
                record["base_pdf"] = str(source.relative_to(directory))
                record["params"] = spec["params"]
                record["facts"] = build_doc_case(spec, source, out, recorder, work)
                password = spec["params"].get("user", "")
                reference = truth_text(load_truth(directory, spec["doc_id"]))
            else:
                result = build_raw(spec)
                out.write_bytes(result.pdf)
                record["params"] = {k: v for k, v in spec["params"].items() if k not in {"lines", "visible", "hidden",
                                                                                         "note", "labels", "values"}}  # fmt: skip
                record["expected_text"] = result.expected_text
                record["expected_lines"] = result.expected_lines
                record["hidden_text"] = result.hidden_lines
                record["notes"] = result.notes
                record["facts"] = result.extra
                recorder.steps.append(result.code_path)
                reference = result.expected_text
        except Exception as error:
            record["build_error"] = f"{type(error).__name__}: {error}"[:800]
            record["commands"] = recorder.commands
            record["steps"] = recorder.steps
            return record
        record["commands"] = recorder.commands
        record["steps"] = recorder.steps
    record["password"] = password or None
    record["measured"] = measure_structure(out, password)
    record["validation"] = validate(out, password, reference, "\n".join(record.get("hidden_text") or []))
    end = _usage()
    record["resources"] = {"wall_seconds": round(time.perf_counter() - start, 3),
                           "cpu_seconds": round(end["cpu"] - usage["cpu"], 3),
                           "child_peak_rss_kib": max((c["peak_rss_kib"] for c in record["commands"]), default=None)}  # fmt: skip
    return record


def _usage() -> dict[str, float]:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"cpu": own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime,
            "self_rss": own.ru_maxrss, "children_rss": children.ru_maxrss}  # fmt: skip


def baseline(arguments: tuple[str, str]) -> tuple[str, dict[str, Any]]:
    """Validation block for one base L0 PDF, for comparison with its derived cases."""
    doc, directory_text = arguments
    directory = Path(directory_text)
    source = base_pdf(directory, doc)
    block = validate(source, "", truth_text(load_truth(directory, doc)))
    return doc, {"path": str(source.relative_to(directory)), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                 "validation": block}  # fmt: skip


def tool_versions() -> dict[str, str | None]:
    """Versions of every external tool and library used by the builders and validators."""

    def first_line(argv: list[str]) -> str | None:
        if shutil.which(argv[0]) is None:
            return None
        result = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=30)
        lines = (result.stdout or result.stderr).strip().splitlines()
        return lines[0] if lines else None

    import PIL
    import pymupdf
    import pypdf

    import pdfust

    return {
        "ghostscript": first_line(["gs", "--version"]),
        "qpdf": first_line(["qpdf", "--version"]),
        "pdftocairo": first_line(["pdftocairo", "-v"]),
        "pdftotext": first_line(["pdftotext", "-v"]),
        "python": sys.version.split()[0],
        "pypdf": pypdf.__version__,
        "pymupdf": pymupdf.VersionBind,
        "pdfust": pdfust.__version__,
        "pillow": PIL.__version__,
    }


def summarize(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Per-family counts and extraction health."""
    summary: dict[str, Any] = {}
    for family in FAMILIES:
        rows = [r for r in records if r["family"] == family]
        entry: dict[str, Any] = {"cases": len(rows), "build_errors": sum(1 for r in rows if "build_error" in r)}
        for tool in ("pypdf", "pdftotext", "pymupdf", "pdfust"):
            results = [r["validation"][tool] for r in rows if "validation" in r]
            recalls = [x["token_recall"] for x in results if x["token_recall"] is not None]
            entry[tool] = {
                "ok": sum(1 for x in results if x["ok"]),
                "nonempty": sum(1 for x in results if x["ok"] and x["chars"]),
                "mean_chars": round(sum(x["chars"] or 0 for x in results) / len(results), 1) if results else None,
                "mean_token_recall": round(sum(recalls) / len(recalls), 4) if recalls else None,
            }
        summary[family] = entry
    return summary


CASE_KEYS = {"case_id", "quirk_id", "family", "doc_id", "source_doc_id", "path", "tool", "params", "commands", "steps"}
MEASURED_KEYS = {
    "sha256", "header_version", "producer", "xref_kind", "object_streams", "encryption", "stream_filters",
    "fonts", "font_subtypes", "font_encodings", "tounicode", "page_count",
}  # fmt: skip
VALIDATION_TOOLS = ("pypdf", "pdftotext", "pymupdf", "pdfust")


def manifest_errors(manifest: dict[str, Any]) -> list[str]:
    """Return schema violations in a quirks manifest (empty when valid)."""
    errors: list[str] = []
    required = ("schema", "tools", "case_count", "summary", "build_resources", "baselines", "cases")
    errors.extend(f"manifest lacks {key}" for key in required if key not in manifest)
    cases = manifest.get("cases", [])
    if manifest.get("case_count") != len(cases):
        errors.append("case_count does not match cases")
    seen: set[str] = set()
    for case in cases:
        name = case.get("case_id", "?")
        if name in seen:
            errors.append(f"{name}: duplicate case_id")
        seen.add(name)
        if "build_error" in case:
            continue
        errors.extend(f"{name}: missing {key}" for key in sorted(CASE_KEYS - case.keys()))
        if case.get("family") not in FAMILIES:
            errors.append(f"{name}: unknown family {case.get('family')}")
        if case.get("doc_id") is None and not case.get("expected_text"):
            errors.append(f"{name}: raw case without expected_text")
        if case.get("doc_id") is not None and case.get("path") != f"quirks/{case['quirk_id']}/{case['doc_id']}.pdf":
            errors.append(f"{name}: path does not follow quirks/{{quirk_id}}/{{doc_id}}.pdf")
        measured = case.get("measured", {})
        errors.extend(f"{name}: measured lacks {key}" for key in sorted(MEASURED_KEYS - measured.keys()))
        if measured.get("xref_kind") not in {"table", "stream", "both"}:
            errors.append(f"{name}: bad xref_kind {measured.get('xref_kind')}")
        validation = case.get("validation", {})
        for tool in VALIDATION_TOOLS:
            result = validation.get(tool)
            if not isinstance(result, dict) or not {"ok", "chars", "token_recall"} <= result.keys():
                errors.append(f"{name}: validation lacks {tool}")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    """Build every quirk case and write the manifest."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--only", nargs="*", help="Restrict to these quirk IDs")
    args = parser.parse_args(argv)
    directory = guard_path(args.directory)
    for tool in ("gs", "ps2pdf", "qpdf", "pdftocairo", "pdftotext"):
        if shutil.which(tool) is None:
            print(f"warning: {tool} is missing; dependent cases will record build errors", file=sys.stderr)
    os.environ["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    start, usage = time.perf_counter(), _usage()
    specs = plan(directory)
    if args.only:
        specs = [s for s in specs if s["quirk_id"] in set(args.only)]
    quirk_root = guard_path(directory / "quirks")
    quirk_root.mkdir(parents=True, exist_ok=True)
    docs = sorted({s["doc_id"] for s in specs if s["doc_id"]})
    # Spawned workers are direct children, so RUSAGE_CHILDREN covers them and their tools.
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=max(1, args.workers), mp_context=context) as pool:
        records = list(pool.map(run_case, [(s, str(directory)) for s in specs]))
        baselines = dict(pool.map(baseline, [(d, str(directory)) for d in docs]))
    for record in records:
        print(f"{record['case_id']}: {record.get('build_error', 'ok')}")
    end = _usage()
    manifest = {
        "schema": SCHEMA,
        "dataset": "wild-v1/quirks",
        "description": "Production-quirk derivatives of wild-v1 L0 PDFs and hand-written raw PDFs (DEV only).",
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "tools": tool_versions(),
        "families": list(FAMILIES),
        "nondeterministic_quirks": NONDETERMINISTIC,
        "raw_case_paths": "quirks/{quirk_id}/raw-{source_doc_id}.pdf; doc_id is null and expected_text is exact",
        "case_count": len(records),
        "summary": summarize(records),
        "build_resources": {
            "wall_seconds": round(time.perf_counter() - start, 2),
            "cpu_seconds": round(end["cpu"] - usage["cpu"], 2),
            "peak_rss_kib_parent": end["self_rss"],
            "peak_rss_kib_largest_child": end["children_rss"],
            "workers": args.workers,
            "measurement": "resource.getrusage RUSAGE_SELF + RUSAGE_CHILDREN deltas over the whole build "
            "(children include pool workers and their tool subprocesses); ru_maxrss is the largest single process.",
        },
        "baselines": baselines,
        "cases": records,
    }
    path = quirk_root / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    errors = sum(1 for r in records if "build_error" in r)
    print(f"wrote {len(records)} cases ({errors} build errors) to {path}")
    problems = manifest_errors(manifest)
    for problem in problems:
        print(f"schema: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
