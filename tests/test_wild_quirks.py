"""Fast checks for the wild-v1 production-quirks generator (bench/wild_quirks*.py)."""

from __future__ import annotations

import io
import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("pypdf")
pytest.importorskip("PIL")
pytest.importorskip("pymupdf")

from bench import wild_quirks as wq
from bench import wild_quirks_raw as raw
from pypdf import PdfReader
from pypdf.filters import ASCII85Decode, ASCIIHexDecode, FlateDecode, LZWDecode, RunLengthDecode

FRENCH = ["Atelier Lemoine & Fils", "Facture n° FA-2026-0127 — Échéance : 30/04/2026", "Total TTC : 14 259,12 €"]
GERMAN = ["Brenner Haustechnik GmbH · Quartalsbericht", "Kita „Sonnenblume“ – Gewerbepark Süd 7"]
ENGLISH = ["Halvorsen & Pike Engineering LLC", "Invoice INV-2026-0418", "Subtotal: $10,016.20"]
needs_pdftotext = pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext is not installed")


def pdftotext(data: bytes, tmp_path: Path, password: str = "") -> str:
    path = tmp_path / "case.pdf"
    path.write_bytes(data)
    argv = ["pdftotext", "-enc", "UTF-8", *(["-upw", password] if password else []), str(path), "-"]
    return subprocess.run(argv, capture_output=True, check=True).stdout.decode()  # noqa: S603


def words(text: str) -> list[str]:
    return text.split()


def test_encoding_tables_produce_expected_bytes() -> None:
    win = raw.encoding_table("WinAnsiEncoding")
    assert raw.encode("é€’–", win) == b"\xe9\x80\x92\x96"
    mac = raw.encoding_table("MacRomanEncoding")
    assert raw.encode("é“”", mac) == b"\x8e\xd2\xd3"
    assert not raw.can_encode("€", mac)  # PDF MacRomanEncoding has /currency at 0xDB, not /Euro.
    standard = raw.encoding_table("StandardEncoding")
    assert raw.encode("’‘–•ﬁ", standard) == b"\x27\x60\xb1\xb7\xae"
    assert raw.encode("α ≤", raw.encoding_table("Symbol")) == b"\x61\x20\xa3"
    assert raw.encode("✓", raw.encoding_table("ZapfDingbats")) == b"\x33"
    with pytest.raises(ValueError, match="not in the encoding"):
        raw.encode("ł", win)


def test_glyph_names_and_custom_codes() -> None:
    assert raw.glyph_name("é", "standard") == "eacute"
    assert raw.glyph_name("€", "standard") == "Euro"
    assert raw.glyph_name("é", "uni") == "uni00E9"
    assert raw.glyph_name("А", "afii") == "afii10017"
    assert raw.glyph_name("₽", "afii") == "uni20BD"
    codes = raw.custom_codes(["Aé€é"], keep_ascii=True)
    assert codes == {"A": 65, "é": 1, "€": 2}
    assert raw.custom_codes(["ab a"], keep_ascii=False) == {"a": 33, "b": 34, " ": 35}


def test_literal_and_tounicode_syntax() -> None:
    assert raw.pdf_literal(b"a(b)\\\n\xe9") == b"(a\\(b\\)\\\\\\012\\351)"
    cmap = raw.tounicode_cmap({1: "é", 2: "€"})
    assert b"<01> <00E9>" in cmap
    assert b"<02> <20AC>" in cmap
    assert b"2 beginbfchar" in cmap


def test_filter_encoders_round_trip() -> None:
    rng = random.Random(7)  # noqa: S311 - deterministic test data.
    samples = [
        b"",
        b"x",
        b"BT /F1 12 Tf (Hello) Tj ET\n" * 400,
        bytes(rng.randrange(256) for _ in range(12000)),
        bytes(rng.randrange(3) for _ in range(30000)),
    ]
    for data in samples:
        assert LZWDecode.decode(raw.lzw_encode(data)) == data
        assert RunLengthDecode.decode(raw.run_length_encode(data)) == data
        assert ASCIIHexDecode.decode(raw.ascii_hex_encode(data)) == data
        assert FlateDecode.decode(ASCII85Decode.decode(raw.FILTER_ENCODERS["ascii85_flate"][1](data))) == data


def test_raw_builders_are_deterministic_and_open() -> None:
    first = raw.build_differences_standard_names(FRENCH, "Helvetica", "t").pdf
    assert first == raw.build_differences_standard_names(FRENCH, "Helvetica", "t").pdf
    reader = PdfReader(io.BytesIO(first))
    font = reader.pages[0]["/Resources"]["/Font"]["/F1"].get_object()
    assert "/ToUnicode" not in font
    assert "/eacute" in [str(item) for item in font["/Encoding"]["/Differences"]]
    assert first.startswith(b"%PDF-1.4\n")


@needs_pdftotext
@pytest.mark.parametrize(
    ("lines", "base", "encoding"),
    [
        (FRENCH, "Helvetica", "WinAnsiEncoding"),
        (GERMAN, "Times-Roman", "WinAnsiEncoding"),
        (FRENCH[:2], "Times-Roman", "MacRomanEncoding"),
        (["It’s “fine” – ﬁxture • ok"], "Helvetica", None),
    ],
)
def test_simple_encodings_extract_with_pdftotext(
    lines: list[str], base: str, encoding: str | None, tmp_path: Path
) -> None:
    result = raw.build_simple_encoding(lines, base, encoding, "t")
    assert len(PdfReader(io.BytesIO(result.pdf)).pages) == 1
    assert words(pdftotext(result.pdf, tmp_path).replace("ﬁ", "fi")) == words(result.expected_text.replace("ﬁ", "fi"))


@needs_pdftotext
def test_differences_and_type3_extract_with_pdftotext(tmp_path: Path) -> None:
    differences = raw.build_differences_standard_names(FRENCH, "Helvetica", "t")
    assert words(pdftotext(differences.pdf, tmp_path)) == words(differences.expected_text)
    mapped = raw.build_type3_names(["Журнал поверки"], "g", tounicode=True, title="t")
    assert words(pdftotext(mapped.pdf, tmp_path)) == ["Журнал", "поверки"]
    unmapped = raw.build_type3_names(["Журнал поверки"], "g", tounicode=False, title="t")
    assert words(pdftotext(unmapped.pdf, tmp_path)) != ["Журнал", "поверки"]


@needs_pdftotext
def test_layout_and_form_builders_extract(tmp_path: Path) -> None:
    rotated = raw.build_rotated_page(ENGLISH, 90, "t")
    assert words(pdftotext(rotated.pdf, tmp_path)) == words(rotated.expected_text)
    assert PdfReader(io.BytesIO(rotated.pdf)).pages[0]["/Rotate"] == 90
    form = raw.build_acroform(["Purchase order:"], ["KPC-PO-26-0091"], stored=[None], title="t")
    assert "KPC-PO-26-0091" in pdftotext(form.pdf, tmp_path)
    assert form.expected_lines == ["Purchase order: KPC-PO-26-0091"]
    invisible = raw.build_invisible_over_rect(ENGLISH[:1], ENGLISH[1:], "t")
    assert invisible.expected_lines == ENGLISH[:1]
    assert invisible.hidden_lines == ENGLISH[1:]


def test_truth_lines_wraps_and_filters() -> None:
    truth = {
        "blocks": [
            {"kind": "heading", "text": "Faktura łączna"},
            {"kind": "paragraph", "text": "One two three four five six seven eight nine ten"},
            {"kind": "table", "rendering": "screenshot", "values": [["x"]]},
        ]
    }
    accept = wq._encodable(raw.encoding_table("WinAnsiEncoding"))  # noqa: SLF001
    assert wq.truth_lines(truth, width=20, limit=5, accept=accept) == [
        "One two three four",
        "five six seven eight",
        "nine ten",
    ]
    assert "Faktura" in wq.truth_text(truth)


def _raw_spec(quirk_id: str, params: dict[str, object]) -> dict[str, object]:
    return {
        "quirk_id": quirk_id,
        "family": "font_encoding",
        "doc_id": None,
        "source_doc_id": "w-test-01",
        "case_id": f"{quirk_id}/raw-w-test-01",
        "relative_path": f"quirks/{quirk_id}/raw-w-test-01.pdf",
        "params": params,
    }


def _fixture_corpus(tmp_path: Path) -> Path:
    directory = tmp_path / "wild"
    (directory / "variants/w-test-01").mkdir(parents=True)
    (directory / "docs/w-test-01").mkdir(parents=True)
    source = raw.build_simple_encoding(FRENCH, "Helvetica", "WinAnsiEncoding", "Facture").pdf
    (directory / "variants/w-test-01/L0_tagged.pdf").write_bytes(source)
    truth = {
        "doc_id": "w-test-01",
        "metadata": {"title": "Facture"},
        "blocks": [{"kind": "paragraph", "text": t} for t in FRENCH],
    }
    (directory / "docs/w-test-01/truth.json").write_text(json.dumps(truth), encoding="utf-8")
    return directory


def _doc_spec(quirk_id: str, family: str, params: dict[str, object]) -> dict[str, object]:
    return {
        "quirk_id": quirk_id,
        "family": family,
        "doc_id": "w-test-01",
        "source_doc_id": "w-test-01",
        "case_id": f"{quirk_id}/w-test-01",
        "relative_path": f"quirks/{quirk_id}/w-test-01.pdf",
        "params": params,
    }


@needs_pdftotext
def test_run_case_records_and_manifest_schema(tmp_path: Path) -> None:
    directory = _fixture_corpus(tmp_path)
    specs = [
        _raw_spec(
            "std14_winansi",
            {"builder": "simple", "encoding": "WinAnsiEncoding", "font": "Helvetica", "lines": FRENCH, "title": "t"},
        ),
        _doc_spec("filter_lzw", "filter", {"tool": "reencode", "filter": "lzw"}),
        _doc_spec("incremental_update", "structure", {"tool": "incremental"}),
    ]
    records = [wq.run_case((spec, str(directory))) for spec in specs]
    for record in records:
        assert "build_error" not in record, record.get("build_error")
        assert record["validation"]["pdftotext"]["token_recall"] == 1.0
        assert record["validation"]["pypdf_opens"]
    winansi, lzw, incremental = records
    assert winansi["expected_text"] == "\n".join(FRENCH)
    assert winansi["measured"]["font_encodings"] == ["/WinAnsiEncoding"]
    assert winansi["measured"]["tounicode"] == "none"
    assert lzw["measured"]["stream_filters"].get("/LZWDecode") == 1
    assert incremental["facts"]["original_prefix_preserved"]
    assert incremental["measured"]["xref_sections"] == 2
    manifest = {"schema": 1, "tools": {}, "case_count": 3, "summary": wq.summarize(records),
                "build_resources": {}, "baselines": {}, "cases": records}  # fmt: skip
    assert wq.manifest_errors(manifest) == []
    broken = {**manifest, "cases": [{**records[0], "family": "nope", "expected_text": ""}]}
    assert len(wq.manifest_errors(broken)) >= 2


@pytest.mark.skipif(shutil.which("qpdf") is None or shutil.which("gs") is None, reason="qpdf/gs not installed")
@needs_pdftotext
def test_tool_cases_encrypt_and_redistill(tmp_path: Path) -> None:
    directory = _fixture_corpus(tmp_path)
    user = _doc_spec(
        "encrypt_aes256_r6_user_password",
        "encryption",
        {"tool": "qpdf_encrypt", "bits": 256, "aes": True, "user": wq.USER_PASSWORD},
    )
    record = wq.run_case((user, str(directory)))
    assert record["measured"]["encryption"]["R"] == 6
    assert record["password"] == wq.USER_PASSWORD
    assert record["validation"]["pdftotext"]["token_recall"] == 1.0
    weak = _doc_spec("encrypt_rc4_40_r2", "encryption", {"tool": "qpdf_encrypt", "bits": 40, "aes": False, "user": ""})
    assert wq.run_case((weak, str(directory)))["measured"]["encryption"]["R"] == 2
    gs = wq.run_case((_doc_spec("gs_pdfwrite_15", "producer", {"tool": "gs", "level": "1.5"}), str(directory)))
    assert gs["measured"]["header_version"] == "1.5"
    assert "Ghostscript" in (gs["measured"]["producer"] or "")
    assert gs["validation"]["pdftotext"]["token_recall"] == 1.0


