"""Fast checks for the wild-v1 flattening levels on a tiny generated PDF."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

pypdf = pytest.importorskip("pypdf")
pytest.importorskip("PIL")
pytest.importorskip("numpy")

from bench import wild_flatten  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from pypdf.generic import BooleanObject, DictionaryObject, NameObject, StreamObject, TextStringObject  # noqa: E402

import pylopdf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CJK_FONT = ROOT / "fonts/pylopdf-fonts-jp/src/pylopdf_fonts_jp/NotoSansJP-Regular.otf"


def _require(*tools: str) -> None:
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        pytest.skip(f"missing external tools: {', '.join(missing)}")


@pytest.fixture(scope="module")
def tagged_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Two text pages with an outline, Info, XMP and a minimal structure tree."""
    directory = tmp_path_factory.mktemp("wild-flatten-source")
    document = pylopdf.Document()
    for index in range(2):
        page = document.new_page(width=300, height=200)
        page.insert_text((20, 40), f"Quarterly report page {index + 1}", fontsize=14)
        page.insert_text((20, 80), "Invoice INV-1042 total 1,280.00 EUR", fontsize=11)
        if CJK_FONT.is_file():  # embedded subset font with a ToUnicode CMap
            page.insert_text((20, 120), "請求書 Invoice 1042", fontsize=12, fontfile=CJK_FONT)
    document.set_toc([[1, "Report", 1], [1, "Notes", 2]])
    document.set_metadata({"title": "Wild flatten fixture", "author": "Test"})
    plain = directory / "plain.pdf"
    document.save(plain)

    writer = pypdf.PdfWriter(clone_from=plain)
    root = writer._root_object  # noqa: SLF001
    tree = writer._add_object(DictionaryObject({NameObject("/Type"): NameObject("/StructTreeRoot")}))  # noqa: SLF001
    root[NameObject("/StructTreeRoot")] = tree
    root[NameObject("/MarkInfo")] = DictionaryObject({NameObject("/Marked"): BooleanObject(True)})
    root[NameObject("/Lang")] = TextStringObject("en-US")
    xmp = StreamObject()
    xmp.set_data(b'<?xpacket begin=""?><x:xmpmeta xmlns:x="adobe:ns:meta/"/><?xpacket end="w"?>')
    xmp[NameObject("/Type")] = NameObject("/Metadata")
    xmp[NameObject("/Subtype")] = NameObject("/XML")
    root[NameObject("/Metadata")] = writer._add_object(xmp)  # noqa: SLF001
    source = directory / "source.pdf"
    with source.open("wb") as handle:
        writer.write(handle)
    (directory / "truth.json").write_text(json.dumps({"languages": ["en", "ja"]}))
    return source


@pytest.fixture(scope="module")
def flattened(tagged_pdf: Path, tmp_path_factory: pytest.TempPathFactory) -> dict:
    _require("gs", "pdftoppm")
    out = tmp_path_factory.mktemp("wild-flatten-out")
    levels = ["L0_tagged", "L1_untagged", "L2_stripped", "L3_outlined", "L4_raster", "L9_broken_tounicode"]
    return {"out": out, "variants": wild_flatten.flatten(tagged_pdf, out, levels, seed="test")}


def test_source_fixture_has_structure(tagged_pdf: Path) -> None:
    measured = wild_flatten.measure(tagged_pdf)
    structure = measured["structure"]
    assert structure["struct_tree_root"]
    assert structure["mark_info"]
    assert structure["outline_count"] == 2
    assert structure["info_present"]
    assert structure["xmp_present"]
    assert measured["text_layer"] == "native"


def test_l1_removes_structure_but_keeps_text(flattened: dict) -> None:
    record = flattened["variants"]["levels"]["L1_untagged"]
    structure = record["measured"]["structure"]
    assert not structure["struct_tree_root"]
    assert not structure["mark_info"]
    assert structure["outline_count"] == 0
    assert structure["lang"] is None
    assert record["measured_text_layer"] == "native"
    assert record["measured"]["reference_char_recall"] > 0.95
    assert record["commands"][0]["argv"][0] == "gs"
    assert (flattened["out"] / "variants.json").is_file()


def test_l2_removes_info_and_xmp(flattened: dict) -> None:
    record = flattened["variants"]["levels"]["L2_stripped"]
    structure = record["measured"]["structure"]
    assert not structure["info_present"]
    assert not structure["xmp_present"]
    assert record["measured_text_layer"] == "native"
    reader = pypdf.PdfReader(flattened["out"] / "L2_stripped.pdf")
    assert "/Info" not in reader.trailer
    assert "/Metadata" not in reader.trailer["/Root"]


def test_l3_has_no_text_and_renders_the_same(flattened: dict) -> None:
    record = flattened["variants"]["levels"]["L3_outlined"]
    assert record["measured"]["total_chars"] == 0
    assert record["measured_text_layer"] == "none"
    assert record["verification"]["visually_unchanged"]


def test_l4_is_image_only(flattened: dict) -> None:
    record = flattened["variants"]["levels"]["L4_raster"]
    assert record["measured_text_layer"] == "none"
    assert record["measured"]["image_xobjects_per_page"] == [1, 1]
    assert record["measured"]["fonts_per_page"] == [0, 0]
    assert record["measured"]["page_sizes"] == [[300.0, 200.0], [300.0, 200.0]]


def test_l9_deletes_tounicode(flattened: dict) -> None:
    record = flattened["variants"]["levels"]["L9_broken_tounicode"]
    if CJK_FONT.is_file():
        assert record["rewrite"]["tounicode_deleted"] >= 1
        assert "請" not in record["survival"]["pylopdf"]["sample_after"]
    # Simple Standard-encoded fonts still decode without ToUnicode; the survival record shows how much.
    assert record["measured_text_layer"] in {"native", "partial", "broken", "none"}
    reader = pypdf.PdfReader(flattened["out"] / "L9_broken_tounicode.pdf")
    for page in reader.pages:
        for reference in page["/Resources"]["/Font"].values():
            font = reference.get_object()
            assert "/ToUnicode" not in font
            for descendant in font.get("/DescendantFonts", []):
                assert "/ToUnicode" not in descendant.get_object()
    assert "pylopdf" in record["survival"]


def test_records_are_complete_and_deterministic(flattened: dict, tagged_pdf: Path, tmp_path: Path) -> None:
    variants = flattened["variants"]
    for level, record in variants["levels"].items():
        assert record["expected_text_layer"] == wild_flatten.LEVELS[level]
        if level != "L9_broken_tounicode":
            assert record["matches_expected"], level
        assert len(record["output_sha256"]) == 64
        assert record["page_count"] == 2
        assert record["resources"]["wall_seconds"] >= 0
    again = wild_flatten.flatten(tagged_pdf, tmp_path, ["L2_stripped"], seed="test")
    assert again["levels"]["L2_stripped"]["output_sha256"] == variants["levels"]["L2_stripped"]["output_sha256"]


def test_language_selection_records_missing_data() -> None:
    selection = wild_flatten.select_ocr_languages(["ja", "zh-TW", "en", "xx"], {"eng", "osd"})
    assert selection["wanted"] == ["jpn", "chi_tra", "eng"]
    assert selection["used"] == ["eng"]
    assert selection["missing_traineddata"] == ["jpn", "chi_tra"]
    assert selection["unmapped_tags"] == ["xx"]
    fallback = wild_flatten.select_ocr_languages(["ar"], {"eng"})
    assert fallback["fallback_to_eng"]


def test_degradations_are_seeded() -> None:
    page = Image.new("RGB", (240, 320), "white")
    ImageDraw.Draw(page).text((20, 20), "Invoice 1042", fill="black")
    first, params = wild_flatten.phone_scan(page, wild_flatten._rng("s", "L6", 0))  # noqa: SLF001
    second, _ = wild_flatten.phone_scan(page, wild_flatten._rng("s", "L6", 0))  # noqa: SLF001
    assert first.tobytes() == second.tobytes()
    assert 0.6 <= abs(params["rotation_degrees"]) <= 2.0
    assert 55 <= params["jpeg_quality"] <= 65
    copy, copy_params = wild_flatten.photocopy(page, wild_flatten._rng("s", "L7", 0))  # noqa: SLF001
    assert copy.mode == ("1" if copy_params["bitonal"] else "L")
    assert 0.3 <= abs(copy_params["rotation_degrees"]) <= 1.0


def test_guard_rejects_heldout_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Held-out"):
        wild_flatten.flatten(tmp_path / "heldout-silver" / "x.pdf", tmp_path, seed="test")
