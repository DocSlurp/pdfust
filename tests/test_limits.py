"""Resource-policy tests for untrusted PDF processing."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import build_pdf, build_raw_pdf

import pdfust

REAL_WORLD = Path(__file__).parent / "assets" / "real_world"


def _error_code(error: pdfust.LimitError) -> str:
    """Read the stable resource identifier."""
    return error.code


def _filter_chain_pdf(count: int) -> bytes:
    filters = " ".join(["/FlateDecode"] * count)
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents 4 0 R >>",
            4: f"<< /Length 0 /Filter [{filters}] >>\nstream\n\nendstream",
        }
    )


def _page_content_array_pdf(count: int) -> bytes:
    refs = " ".join(["4 0 R"] * count)
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents [{refs}] >>",
            4: "<< /Length 0 >>\nstream\n\nendstream",
        }
    )


def _deep_page_tree_pdf(internal_nodes: int) -> bytes:
    objects: dict[int, str | bytes] = {
        1: "<< /Type /Catalog /Pages 2 0 R >>",
    }
    for offset in range(internal_nodes):
        object_number = 2 + offset
        child_number = object_number + 1
        objects[object_number] = f"<< /Type /Pages /Kids [{child_number} 0 R] /Count 1 >>"
    page_number = 2 + internal_nodes
    objects[page_number] = f"<< /Type /Page /Parent {page_number - 1} 0 R /MediaBox [0 0 100 100] >>"
    return build_raw_pdf(objects)


def _indirect_kids_pdf(reference_depth: int) -> bytes:
    objects: dict[int, str | bytes] = {
        1: "<< /Type /Catalog /Pages 2 0 R >>",
        2: "<< /Type /Pages /Kids 3 0 R /Count 1 >>",
    }
    for offset in range(reference_depth - 1):
        object_number = 3 + offset
        objects[object_number] = f"{object_number + 1} 0 R"
    array_number = 2 + reference_depth
    page_number = array_number + 1
    objects[array_number] = f"[{page_number} 0 R]"
    objects[page_number] = "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>"
    return build_raw_pdf(objects)


def test_document_limits_validate_values() -> None:
    assert pdfust.DocumentLimits().max_pages is None
    with pytest.raises(TypeError, match="max_pages"):
        pdfust.DocumentLimits(max_pages=True)
    with pytest.raises(TypeError, match="max_pages"):
        pdfust.DocumentLimits(max_pages=1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_pages"):
        pdfust.DocumentLimits(max_pages=0)
    with pytest.raises(ValueError, match="cannot both"):
        pdfust.Document(
            stream=build_pdf(["one"]),
            max_decompressed_size=1024,
            limits=pdfust.DocumentLimits(max_pages=1),
        )


def test_limit_error_is_machine_readable_pdf_error() -> None:
    data = build_pdf(["one"])
    with pytest.raises(pdfust.LimitError) as caught:
        pdfust.Document(
            stream=data,
            limits=pdfust.DocumentLimits(max_file_size=len(data) - 1),
        )
    assert isinstance(caught.value, pdfust.PdfError)
    assert _error_code(caught.value) == "file_size"
    assert caught.value.args[0] == "file_size"
    assert str(caught.value).startswith("PDF input is")


def test_file_size_limit_precedes_path_read(tmp_path: Path) -> None:
    path = tmp_path / "input.pdf"
    data = build_pdf(["one"])
    path.write_bytes(data)
    with pytest.raises(pdfust.LimitError) as caught:
        pdfust.open(
            path,
            limits=pdfust.DocumentLimits(max_file_size=len(data) - 1),
        )
    assert _error_code(caught.value) == "file_size"


def test_page_and_object_limits() -> None:
    data = build_pdf(["one", "two", "three"])
    with pytest.raises(pdfust.LimitError) as pages:
        pdfust.open(stream=data, limits=pdfust.DocumentLimits(max_pages=2))
    assert _error_code(pages.value) == "page_count"

    with pytest.raises(pdfust.LimitError) as objects:
        pdfust.open(stream=data, limits=pdfust.DocumentLimits(max_objects=4))
    assert _error_code(objects.value) == "object_count"


@pytest.mark.parametrize(
    ("objects", "message"),
    [
        pytest.param(
            {
                1: "<< /Type /Catalog /Pages 2 0 R >>",
                2: "<< /Type /Pages /Kids [2 0 R] /Count 1 >>",
            },
            "cycle",
            id="cycle",
        ),
        pytest.param(
            {
                1: "<< /Type /Catalog /Pages 2 0 R >>",
                2: "<< /Type /Pages /Kids [3 0 R 3 0 R] /Count 2 >>",
                3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>",
            },
            "reuses object",
            id="reused-page",
        ),
        pytest.param(
            {
                1: "<< /Type /Catalog /Pages 2 0 R >>",
                2: "<< /Type /Pages /Kids 3 0 R /Count 1 >>",
                3: "3 0 R",
            },
            "Kids contains a reference cycle",
            id="kids-reference-cycle",
        ),
    ],
)
@pytest.mark.parametrize(
    "limits",
    [
        pytest.param(
            pdfust.DocumentLimits(max_pages=10),
            id="page-count-policy",
        ),
        pytest.param(
            pdfust.DocumentLimits(max_page_content_size=1024),
            id="page-content-policy",
        ),
    ],
)
def test_bounded_page_tree_walk_rejects_cycles_and_reuse(
    objects: dict[int, str | bytes],
    message: str,
    limits: pdfust.DocumentLimits,
) -> None:
    with pytest.raises(pdfust.PdfError, match=message):
        pdfust.open(
            stream=build_raw_pdf(objects),
            limits=limits,
        )


def test_unbounded_open_defers_malformed_page_tree_rejection_to_indexing() -> None:
    pdf = build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [2 0 R] /Count 1 >>",
        }
    )
    doc = pdfust.open(stream=pdf)
    assert doc.limits.max_pages is None

    # Failed indexing must never install an empty or partial cached order.
    for _ in range(3):
        with pytest.raises(pdfust.PdfError, match="cycle"):
            _ = doc.page_count
    with pytest.raises(pdfust.PdfError, match="cycle"):
        _ = doc.complexity


def test_bounded_page_tree_walk_has_an_iterative_depth_boundary() -> None:
    exact = pdfust.open(
        stream=_deep_page_tree_pdf(256),
        limits=pdfust.DocumentLimits(max_pages=1),
    )
    assert exact.page_count == 1

    unbounded_exact = pdfust.open(stream=_deep_page_tree_pdf(256))
    assert unbounded_exact.page_count == 1
    assert unbounded_exact.complexity["page_count"] == 1

    with pytest.raises(pdfust.PdfError, match="256-level safety limit"):
        pdfust.open(
            stream=_deep_page_tree_pdf(257),
            limits=pdfust.DocumentLimits(max_pages=1),
        )
    unbounded_deep = pdfust.open(stream=_deep_page_tree_pdf(257))
    with pytest.raises(pdfust.PdfError, match="256-level safety limit"):
        _ = unbounded_deep.page_count


def test_bounded_page_tree_walk_limits_indirect_kids_references() -> None:
    exact = pdfust.open(
        stream=_indirect_kids_pdf(32),
        limits=pdfust.DocumentLimits(max_pages=1),
    )
    assert exact.page_count == 1

    with pytest.raises(pdfust.PdfError, match="32-reference-depth safety limit"):
        pdfust.open(
            stream=_indirect_kids_pdf(33),
            limits=pdfust.DocumentLimits(max_pages=1),
        )


def test_bounded_page_tree_walk_limits_edges_by_object_count() -> None:
    pdf = build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [null null null] /Count 0 >>",
        }
    )
    with pytest.raises(pdfust.PdfError, match="edge object-count safety limit"):
        pdfust.open(
            stream=pdf,
            limits=pdfust.DocumentLimits(max_pages=1),
        )


def test_direct_object_depth_limit_ignores_reference_cycles() -> None:
    nested = "[" * 8 + "0" + "]" * 8
    pdf = build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>",
            4: nested,
            5: "<< /Next 6 0 R >>",
            6: "<< /Next 5 0 R >>",
        }
    )
    with pytest.raises(pdfust.LimitError) as depth:
        pdfust.open(stream=pdf, limits=pdfust.DocumentLimits(max_object_depth=4))
    assert _error_code(depth.value) == "object_depth"

    doc = pdfust.open(stream=pdf, limits=pdfust.DocumentLimits(max_object_depth=16))
    assert doc.page_count == 1


def test_direct_object_depth_handles_wide_dictionaries_iteratively() -> None:
    entries = " ".join(f"/K{index} [[0]]" for index in range(4_096))
    pdf = build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>",
            4: f"<< {entries} >>",
        }
    )

    doc = pdfust.open(stream=pdf, limits=pdfust.DocumentLimits(max_object_depth=4))
    assert doc.complexity["max_object_depth"] == 4

    with pytest.raises(pdfust.LimitError) as depth:
        pdfust.open(stream=pdf, limits=pdfust.DocumentLimits(max_object_depth=3))
    assert _error_code(depth.value) == "object_depth"


def test_page_content_and_general_stream_limits_are_independent() -> None:
    page_content = b" " * 200
    unused = b"x" * 200
    pdf = build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Contents 4 0 R >>",
            4: b"<< /Length 200 >>\nstream\n" + page_content + b"\nendstream",
            5: b"<< /Length 200 >>\nstream\n" + unused + b"\nendstream",
        }
    )
    with pytest.raises(pdfust.LimitError) as content:
        pdfust.open(
            stream=pdf,
            limits=pdfust.DocumentLimits(max_page_content_size=100),
        )
    assert _error_code(content.value) == "page_content_size"

    doc = pdfust.open(
        stream=pdf,
        limits=pdfust.DocumentLimits(
            max_page_content_size=200,
            max_decompressed_size=200,
        ),
    )
    assert doc.page_count == 1


def test_bounded_decoding_caps_filter_chain_length() -> None:
    exact = pdfust.open(
        stream=_filter_chain_pdf(16),
        limits=pdfust.DocumentLimits(max_decompressed_size=1),
    )
    assert exact.page_count == 1

    with pytest.raises(pdfust.LimitError) as caught:
        pdfust.open(
            stream=_filter_chain_pdf(17),
            limits=pdfust.DocumentLimits(max_decompressed_size=1),
        )
    assert _error_code(caught.value) == "stream_filter_count"


def test_page_content_limit_preflights_raw_contents_array() -> None:
    exact = pdfust.open(
        stream=_page_content_array_pdf(4096),
        limits=pdfust.DocumentLimits(max_page_content_size=1),
    )
    assert exact.page_count == 1

    with pytest.raises(pdfust.PdfError, match="4096-entry safety limit"):
        pdfust.open(
            stream=_page_content_array_pdf(4097),
            limits=pdfust.DocumentLimits(max_page_content_size=1),
        )


def test_cumulative_decompressed_limit() -> None:
    stream = b"x" * 60
    pdf = build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>",
            4: b"<< /Length 60 >>\nstream\n" + stream + b"\nendstream",
            5: b"<< /Length 60 >>\nstream\n" + stream + b"\nendstream",
        }
    )
    with pytest.raises(pdfust.LimitError) as total:
        pdfust.open(
            stream=pdf,
            limits=pdfust.DocumentLimits(max_total_decompressed_size=100),
        )
    assert _error_code(total.value) == "total_decompressed_size"


def test_eager_object_stream_uses_cumulative_limit_code() -> None:
    with pytest.raises(pdfust.LimitError) as total:
        pdfust.open(
            REAL_WORLD / "f1040.pdf",
            limits=pdfust.DocumentLimits(max_total_decompressed_size=100),
        )
    assert _error_code(total.value) == "total_decompressed_size"


def test_text_budget_is_cumulative_across_interpreted_pages() -> None:
    doc = pdfust.open(
        stream=build_pdf(["ABC", "DEF", ""]),
        limits=pdfust.DocumentLimits(max_text_size=5),
    )
    assert "ABC" in doc[0].get_text()
    with pytest.raises(pdfust.LimitError) as text:
        doc[1].get_text()
    assert _error_code(text.value) == "text_size"
    # A failed text-heavy page does not consume the remaining budget.
    assert doc[2].get_text() == ""


def test_text_budget_remains_active_on_generated_documents() -> None:
    doc = pdfust.Document(limits=pdfust.DocumentLimits(max_text_size=2))
    page = doc.new_page()
    page.insert_text((20, 20), "ABC")
    with pytest.raises(pdfust.LimitError) as text:
        page.get_text()
    assert _error_code(text.value) == "text_size"


def test_text_glyph_budget_is_cumulative_without_double_charging_pages() -> None:
    exact = pdfust.open(
        stream=build_pdf(["ABC"]),
        limits=pdfust.DocumentLimits(max_text_glyphs=3),
    )
    assert exact[0].get_text("words")
    assert exact[0].find_tables().tables == []

    cumulative = pdfust.open(
        stream=build_pdf(["ABC", "DEF", ""]),
        limits=pdfust.DocumentLimits(max_text_glyphs=5),
    )
    assert "ABC" in cumulative[0].get_text()
    with pytest.raises(pdfust.LimitError) as glyphs:
        cumulative[1].get_text("dict")
    assert _error_code(glyphs.value) == "text_glyph_count"
    # A rejected page does not consume the remaining glyph budget.
    assert cumulative[2].get_text() == ""


def _visible_and_hidden_pdf(pages: list[tuple[str, str]]) -> bytes:
    """One page per ``(visible, invisible)`` pair; invisible text uses render mode 3."""
    count = len(pages)
    objects: dict[int, bytes | str] = {
        1: "<< /Type /Catalog /Pages 2 0 R >>",
        2: "<< /Type /Pages /Kids [{}] /Count {} >>".format(" ".join(f"{4 + 2 * i} 0 R" for i in range(count)), count),
        3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    for index, (visible, hidden) in enumerate(pages):
        content = f"BT /F1 12 Tf 20 150 Td ({visible}) Tj ET\nBT 3 Tr /F1 12 Tf 20 100 Td ({hidden}) Tj ET"
        objects[4 + 2 * index] = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * index} 0 R >>"
        )
        objects[5 + 2 * index] = f"<< /Length {len(content)} >>\nstream\n{content}\nendstream"
    return build_raw_pdf(objects)


def test_reread_by_another_reader_is_not_limited_to_the_first_readers_charge() -> None:
    # Text leaves out glyphs without Unicode; the scan counts them. A scan after
    # text must get the budget other pages leave, not exactly what text used.
    path = Path(__file__).parent / "assets" / "real_world" / "pdfium-type3.pdf"
    doc = pdfust.open(path, limits=pdfust.DocumentLimits(max_text_glyphs=3))
    with pytest.warns(pdfust.PdfustWarning):
        doc[0].get_text()
    assert doc[0].scan()["stats"]["glyphs"] == 3

    # Same with invisible text left out of extraction but reported by the scan.
    hidden = pdfust.open(
        stream=_visible_and_hidden_pdf([("AB", "CDEF")]),
        limits=pdfust.DocumentLimits(max_text_glyphs=6),
    )
    hidden.skip_invisible_text = True
    assert hidden[0].get_text() == "AB\n"
    assert hidden[0].scan()["stats"]["invisible"] == 4
    assert hidden[0].get_text() == "AB\n"
    assert hidden[0].to_markdown() == "AB"


def test_reread_charges_a_page_at_its_largest_reader() -> None:
    doc = pdfust.open(
        stream=_visible_and_hidden_pdf([("AB", "CDEF"), ("GH", "")]),
        limits=pdfust.DocumentLimits(max_text_glyphs=6),
    )
    doc.skip_invisible_text = True
    assert doc[0].get_text() == "AB\n"
    doc[0].scan()
    # Page 1 is now charged 6 glyphs (its scan), leaving nothing for page 2.
    with pytest.raises(pdfust.LimitError) as exc:
        doc[1].get_text()
    assert _error_code(exc.value) == "text_glyph_count"
    # Re-reading an admitted page still never fails or double-charges.
    assert doc[0].get_text() == "AB\n"
    doc[0].scan()


def test_interpretation_budget_bounds_original_and_edited_snapshots(tmp_path: Path) -> None:
    source = build_pdf(["one"])
    exact_source = pdfust.open(
        stream=source,
        limits=pdfust.DocumentLimits(max_interpretation_size=len(source)),
    )
    assert "one" in exact_source[0].get_text()

    bounded_source = pdfust.open(
        stream=source,
        limits=pdfust.DocumentLimits(max_interpretation_size=len(source) - 1),
    )
    assert bounded_source.page_count == 1
    with pytest.raises(pdfust.LimitError) as source_error:
        bounded_source[0].get_text()
    assert _error_code(source_error.value) == "interpretation_size"

    path = tmp_path / "oversized-interpretation.pdf"
    path.write_bytes(source)
    bounded_path = pdfust.open(
        path,
        limits=pdfust.DocumentLimits(max_interpretation_size=len(source) - 1),
    )
    assert bounded_path.page_count == 1
    with pytest.raises(pdfust.LimitError) as path_error:
        bounded_path[0].get_text()
    assert _error_code(path_error.value) == "interpretation_size"

    baseline = pdfust.Document()
    baseline.new_page()
    snapshot_size = len(baseline.tobytes(max_size=None))

    exact_edited = pdfust.Document(
        limits=pdfust.DocumentLimits(max_interpretation_size=snapshot_size),
    )
    exact_edited.new_page()
    assert exact_edited[0].get_text() == ""

    bounded_edited = pdfust.Document(
        limits=pdfust.DocumentLimits(max_interpretation_size=snapshot_size - 1),
    )
    bounded_edited.new_page()
    with pytest.raises(pdfust.LimitError) as edited_error:
        bounded_edited[0].get_text()
    assert _error_code(edited_error.value) == "interpretation_size"
    assert bounded_edited.page_count == 1


def test_empty_get_text_batch_skips_interpretation_snapshot() -> None:
    source = build_pdf(["one"])
    bounded = pdfust.open(
        stream=source,
        limits=pdfust.DocumentLimits(max_interpretation_size=len(source) - 1),
    )
    assert bounded.get_text([]) == ""
    with pytest.raises(pdfust.LimitError) as error:
        bounded.get_text()
    assert _error_code(error.value) == "interpretation_size"


def test_limits_revalidate_after_authentication() -> None:
    encrypted = (Path(__file__).parent / "assets" / "encrypted" / "user-aes-256.pdf").read_bytes()
    doc = pdfust.open(
        stream=encrypted,
        limits=pdfust.DocumentLimits(max_pages=1),
    )
    assert doc.is_encrypted
    with pytest.raises(pdfust.LimitError) as pages:
        doc.authenticate("userpw")
    assert _error_code(pages.value) == "page_count"


def test_complexity_requires_no_stream_decoding() -> None:
    data = build_pdf(["one"])
    doc = pdfust.open(stream=data)
    facts = doc.complexity
    assert facts["page_count"] == 1
    assert facts["object_count"] == 5
    assert facts["stream_count"] == 1
    assert facts["encoded_stream_bytes"] > 0
    assert facts["max_object_depth"] >= 2


@pytest.mark.parametrize("name", ["f1040.pdf", "bunka-kokugo-series-019-p4.pdf"])
def test_web_profile_accepts_representative_vector_and_scan_pdfs(name: str) -> None:
    doc = pdfust.open(REAL_WORLD / name, limits=pdfust.DocumentLimits.web())
    assert doc.page_count >= 1


def test_malformed_input_stays_inside_pdf_error_hierarchy() -> None:
    with pytest.raises(pdfust.PdfError):
        pdfust.open(
            stream=b"%PDF-1.7\nnot a document",
            limits=pdfust.DocumentLimits.web(),
        )
