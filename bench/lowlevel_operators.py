"""Bounded source-operator observations for trusted, small DEV PDF controls.

This experiment parses page content only. It does not interpret fonts, enter Form
XObjects, resolve visibility, or associate operators with interpreted glyph IDs.
"""

from __future__ import annotations

import hashlib
import math
import zlib
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    ByteStringObject,
    ContentStream,
    DictionaryObject,
    IndirectObject,
    NameObject,
    NullObject,
    StreamObject,
    TextStringObject,
)

MAX_PDF_BYTES = 2 * 1024 * 1024
MAX_DECODED_BYTES = 256 * 1024
MAX_OPERATORS = 4096
MAX_TEXT_BYTES = 65536
MAX_DEPTH = 32
MAX_STREAMS = 32
OPERATORS = frozenset(
    [
        "BT",
        "ET",
        "Tf",
        "Tm",
        "Td",
        "TD",
        "T*",
        "Tj",
        "TJ",
        "Tc",
        "Tw",
        "Tz",
        "TL",
        "Tr",
        "Ts",
        "BMC",
        "BDC",
        "EMC",
        "q",
        "Q",
        "cm",
    ]
)


def _refuse(reason: str) -> None:
    message = f"operator_evidence: {reason}"
    raise ValueError(message)


def _decode(stream: StreamObject, remaining: int) -> bytes:  # noqa: C901 - bounded filter admissions.
    filters = stream.get("/Filter")
    if isinstance(filters, ArrayObject):
        if len(filters) != 1:
            _refuse("only one FlateDecode filter is supported")
        filters = filters[0]
    if stream.get("/DecodeParms") not in (None, NullObject()):
        _refuse("DecodeParms are unsupported")
    # Encoded source stays borrowed; get_data() would allocate before admission.
    encoded = stream._data  # noqa: SLF001 - avoid unbounded pypdf filter decoding.
    if not isinstance(encoded, bytes):
        _refuse("content stream has no byte payload")
    if filters is None:
        if len(encoded) > remaining:
            _refuse("decoded content exceeds 256 KiB")
        return encoded
    if filters not in ("/FlateDecode", "/Fl"):
        _refuse("unsupported content filter")
    decoder = zlib.decompressobj()
    try:
        decoded = decoder.decompress(encoded, remaining + 1)
    except zlib.error as error:
        message = "operator_evidence: invalid Flate content"
        raise ValueError(message) from error
    if len(decoded) > remaining or decoder.unconsumed_tail:
        _refuse("decoded content exceeds 256 KiB")
    if not decoder.eof or decoder.unused_data:
        _refuse("incomplete or trailing Flate content")
    return decoded


def _preflight(data: bytes) -> None:  # noqa: C901, PLR0912 - explicit PDF token states.
    """Bound recursive operand shapes before pypdf materializes them."""
    stack: list[str] = []
    index = 0
    while index < len(data):
        token = data[index]
        if token == ord("%"):
            while index < len(data) and data[index] not in (10, 13):
                index += 1
            continue
        if token == ord("("):
            nesting = 1
            index += 1
            while index < len(data) and nesting:
                token = data[index]
                if token == ord("\\"):
                    index += 2
                    continue
                if token == ord("("):
                    nesting += 1
                    if nesting > MAX_DEPTH:
                        _refuse("literal string nesting exceeds depth")
                elif token == ord(")"):
                    nesting -= 1
                index += 1
            if nesting:
                _refuse("unterminated literal string")
            continue
        pair = data[index : index + 2]
        if pair == b"<<":
            stack.append("dict")
            index += 2
        elif pair == b">>":
            if not stack or stack.pop() != "dict":
                _refuse("unbalanced dictionary")
            index += 2
        elif token == ord("<"):
            end = data.find(b">", index + 1)
            if end < 0:
                _refuse("unterminated hex string")
            index = end + 1
        elif token == ord("["):
            stack.append("array")
            index += 1
        elif token == ord("]"):
            if not stack or stack.pop() != "array":
                _refuse("unbalanced array")
            index += 1
        else:
            index += 1
        if len(stack) > MAX_DEPTH:
            _refuse("operand nesting exceeds depth")
    if stack:
        _refuse("unterminated operand container")


def _operand(value: Any, text_budget: list[int], depth: int = 0) -> Any:  # noqa: ANN401, C901, PLR0911 - typed PDF shapes.
    if depth > MAX_DEPTH:
        _refuse("operand nesting exceeds depth")
    if isinstance(value, (TextStringObject, ByteStringObject)):
        raw = value.original_bytes if isinstance(value, TextStringObject) else bytes(value)
        text_budget[0] += len(raw)
        if text_budget[0] > MAX_TEXT_BYTES:
            _refuse("source string bytes exceed 65536")
        return {
            "kind": "pdf_string",
            "bytes_hex": raw.hex(),
            "parser_text": str(value) if isinstance(value, TextStringObject) else None,
            "unicode_status": "not_font_decoded",
        }
    if isinstance(value, NameObject):
        return {"kind": "name", "value": str(value)}
    if isinstance(value, IndirectObject):
        return {"kind": "reference", "object": value.idnum, "generation": value.generation}
    if isinstance(value, NullObject):
        return None
    if isinstance(value, (ArrayObject, list, tuple)):
        return [_operand(item, text_budget, depth + 1) for item in value]
    if isinstance(value, DictionaryObject):
        return {str(key): _operand(value.raw_get(key), text_budget, depth + 1) for key in sorted(value)}
    if isinstance(value, BooleanObject):
        return value.value
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            _refuse("nonfinite numeric operand")
        return int(value) if isinstance(value, int) else float(value)
    _refuse(f"unsupported operand type {type(value).__name__}")
    return None


def extract_operators(pdf_bytes: bytes, page_index: int = 0) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Return complete admitted page-content observations or refuse the result."""
    if not isinstance(pdf_bytes, bytes) or len(pdf_bytes) > MAX_PDF_BYTES:
        _refuse("PDF input must be bytes of at most 2 MiB")
    if type(page_index) is not int or page_index < 0:
        _refuse("page index must be a nonnegative integer")
    reader = PdfReader(BytesIO(pdf_bytes), strict=True)
    if reader.is_encrypted:
        _refuse("encrypted PDFs are unsupported")
    if page_index >= len(reader.pages):
        _refuse("page index is out of range")
    content = reader.pages[page_index].get("/Contents")
    content = content.get_object() if content is not None else None
    if isinstance(content, ArrayObject) and len(content) > MAX_STREAMS:
        _refuse("more than 32 content streams")
    streams = content if isinstance(content, ArrayObject) else ([] if content is None else [content])
    if len(streams) > MAX_STREAMS:
        _refuse("more than 32 content streams")
    combined = bytearray()
    for reference in streams:
        stream = reference.get_object()
        if not isinstance(stream, StreamObject):
            _refuse("content entry is not a stream")
        decoded = _decode(stream, MAX_DECODED_BYTES - len(combined))
        if len(combined) + len(decoded) + 1 > MAX_DECODED_BYTES:
            _refuse("decoded content exceeds 256 KiB")
        combined.extend(decoded)
        combined.extend(b"\n")
    data = bytes(combined)
    _preflight(data)
    source = StreamObject()
    source._data = data  # noqa: SLF001 - already bounded decoded input.
    parsed = ContentStream(source, reader)
    operations = parsed.operations
    if len(operations) > MAX_OPERATORS:
        _refuse("operator count exceeds 4096")
    trace = []
    unsupported = []
    budget = [0]
    graphics_depth = text_depth = marked_depth = 0
    for index, (operands, encoded_operator) in enumerate(operations):
        operator = encoded_operator.decode("ascii")
        if operator == "INLINE IMAGE":
            _refuse("inline images are unsupported")
        # Charge every source string, including omitted nontext operators.
        values = [_operand(value, budget) for value in operands]
        if operator in ("q", "BT", "BMC", "BDC"):
            graphics_depth += int(operator == "q")
            text_depth += int(operator == "BT")
            marked_depth += int(operator in ("BMC", "BDC"))
        elif operator in ("Q", "ET", "EMC"):
            graphics_depth -= int(operator == "Q")
            text_depth -= int(operator == "ET")
            marked_depth -= int(operator == "EMC")
        if min(graphics_depth, text_depth, marked_depth) < 0:
            _refuse("unbalanced graphics, text or marked-content scope")
        if max(graphics_depth, text_depth, marked_depth) > MAX_DEPTH:
            _refuse("scope nesting exceeds depth")
        if operator == "Do":
            unsupported.append({"operator_index": index, "operator": operator, "operands": values})
        if operator in OPERATORS:
            trace.append({"operator_index": index, "operator": operator, "operands": values})
    if graphics_depth or text_depth or marked_depth:
        _refuse("unterminated graphics, text or marked-content scope")
    return {
        "schema": "dev-source-operators-v1",
        "source_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "page_index": page_index,
        "decoded_sha256": hashlib.sha256(data).hexdigest(),
        "decoded_bytes": len(data),
        "operator_count": len(operations),
        "source_string_bytes": budget[0],
        "scope": "page_content_only; Form XObjects are not traversed",
        "complete_for_page": not unsupported,
        "unsupported_xobject_calls": unsupported,
        "glyph_operator_mapping": "unavailable",
        "operators": trace,
    }
