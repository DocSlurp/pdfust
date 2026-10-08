"""CPU research controls for semantic recovery; pypdf remains optional."""

from __future__ import annotations

import io

import pytest

pytest.importorskip("pypdf")

from bench import semantic_probe as semantic
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject


@pytest.mark.parametrize("control", ["valid", "rolemap"])
def test_exact_cells_ids_and_headers(control: str) -> None:
    result = semantic.probe(semantic.synthetic_case(control))
    assert result["tagged_tables"] == 1
    assert len(result["tables"]) == 1
    table = result["tables"][0]
    assert [[cell["text"] for cell in row] for row in table] == [["Name", "Value"], ["Alpha", "42"]]
    assert table[0][0]["id_hex"] == b"name".hex()
    assert table[0][0]["object_id"] == (13, 0)
    assert table[0][0]["scope"] == "/Column"
    assert table[1][1]["headers_hex"] == [b"value".hex()]
    assert [cell["mcid"] for row in table for cell in row] == list(range(4))


@pytest.mark.parametrize(
    ("control", "reason"),
    [
        ("missing-mcid", "stale_parent_association"),
        ("bad-header", "unresolved_header"),
        ("stale-parent", "stale_parent_association"),
        ("duplicate-mcid", "reused_mcid"),
        ("cycle", "tree_limit_or_cycle"),
        ("nonvisible", "nonvisible_or_complex_text"),
    ],
)
def test_invalid_associations_expose_no_partial_table(control: str, reason: str) -> None:
    result = semantic.probe(semantic.synthetic_case(control))
    assert not result["tables"]
    assert reason in result["abstentions"]


def test_untagged_marked_content_is_not_a_table() -> None:
    result = semantic.probe(semantic.synthetic_case("untagged"))
    assert not result["struct_root"]
    assert result["tagged_tables"] == 0
    assert not result["tables"]


@pytest.mark.parametrize("stale", [False, True])
def test_attachment_name_does_not_validate_payload(stale: bool) -> None:  # noqa: FBT001
    result = semantic.probe(semantic.embedded_case(stale=stale))
    assert result["embedded_payload_names"] == ["table.csv"]
    assert not result["tables"]
    # The stale payload says 999 while visible content says 42; inventory must
    # never convert either attachment into a recovered table.


def test_tree_depth_and_width_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(semantic, "MAX_DEPTH", 2)
    monkeypatch.setattr(semantic, "MAX_NODES", 3)
    with pytest.raises(semantic.AbstainError, match="child_count"):
        semantic.children([NumberObject(0)] * 4)
    node = DictionaryObject()
    for _ in range(4):
        node = DictionaryObject({NameObject("/Kids"): node})
    with pytest.raises(semantic.AbstainError, match="tree_limit_or_cycle"):
        semantic.walk(node, "/Kids")


def test_input_cap_precedes_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(semantic, "MAX_BYTES", 2)
    with pytest.raises(semantic.AbstainError, match="input_limit"):
        semantic.probe(b"xxx")


def rewrite_font(encoding: str | None) -> bytes:
    """Change font metadata through a writer, preserving valid object offsets."""
    reader = PdfReader(io.BytesIO(semantic.synthetic_case()))
    resources = semantic.resolve(reader.pages[0]["/Resources"])
    font = semantic.resolve(semantic.resolve(resources["/Font"])["/F1"])
    if encoding is None:
        del font["/Encoding"]
    else:
        font[NameObject("/Encoding")] = NameObject(encoding)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize("encoding", [None, "/MacRomanEncoding"])
def test_font_encoding_is_never_guessed(encoding: str | None) -> None:
    result = semantic.probe(rewrite_font(encoding))
    assert not result["tables"]
    assert "unsupported_font" in result["abstentions"]


def test_role_cycle_abstains() -> None:
    node = {"/S": "/Foo"}
    with pytest.raises(semantic.AbstainError, match="role_cycle"):
        semantic.role(node, {"/Foo": "/Bar", "/Bar": "/Foo"})


def test_missing_mcid_stream_does_not_trust_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    def empty_marked_text(page: object, reader: object) -> dict[int, str]:
        del page, reader
        return {}

    monkeypatch.setattr(semantic, "marked_text", empty_marked_text)
    result = semantic.probe(semantic.synthetic_case())
    assert not result["tables"]
    assert "missing_marked_content" in result["abstentions"]


def test_explicit_winansi_preserves_exact_nonascii_text() -> None:
    data = semantic.synthetic_case().replace(b"(Alpha)", b"(caf\xe9!)")
    result = semantic.probe(data)
    assert result["tables"][0][1][0]["text"] == "caf\u00e9!"


def test_unsupported_winansi_codes_abstain() -> None:
    data = semantic.synthetic_case().replace(b"(Alpha)", b"(A\x7fpha)")
    result = semantic.probe(data)
    assert not result["tables"]
    assert set(result["abstentions"]) <= {"undecoded_text", "unsupported_winansi_code"}
