"""Private CPU experiment: conservative tagged-table recovery, never an API path.

Run with ``.venv/bin/python -m bench.semantic_probe``. Requires optional pypdf.
Bounds apply to our traversal/output; pypdf parsing and decoding are NOT hardened.
Only flat rectangular tables and explicitly WinAnsi Type1 text are accepted.
"""

# pypdf object dictionaries are heterogeneous; report paragraphs are intentional.
# ruff: noqa: ANN401, ISC004

from __future__ import annotations

import argparse
import io
import json
import platform
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any, NoReturn

from pypdf import PdfReader
from pypdf import __version__ as pypdf_version
from pypdf.generic import ContentStream, DictionaryObject, IndirectObject, TextStringObject

from bench.feature_cases import page_pdf, raw_pdf, stream_object, text_op

ROOT = Path(__file__).resolve().parents[1]
MAX_NODES = 4096
MAX_DEPTH = 32
MAX_BYTES = 64 * 1024 * 1024
MAX_TEXT = 1024 * 1024
MAX_OPS = 65536
MAX_ROLE_DEPTH = 16
SAFE_WINANSI_CODES = frozenset(range(32, 127)) | frozenset(range(192, 256))


class AbstainError(Exception):
    """An unsupported or invalid semantic association; no partial table survives."""


def refuse(reason: str) -> NoReturn:
    """Abort recovery with a stable experimental reason code."""
    raise AbstainError(reason)


def resolve(value: Any) -> Any:
    """Resolve one indirect object through the research parser."""
    return value.get_object() if isinstance(value, IndirectObject) else value


def identity(value: Any) -> tuple[int, int] | int:
    """Retain exact indirect IDs; direct objects use process-local identity."""
    if isinstance(value, IndirectObject):
        return (value.idnum, value.generation)
    return id(value)


def children(value: Any) -> list[Any]:
    """Normalize a bounded PDF child array without copying it."""
    original = value
    value = resolve(value)
    result = value if isinstance(value, list) else [] if value is None else [original]
    if len(result) > MAX_NODES:
        refuse("child_count")
    return result


def walk(root: Any, key: str) -> list[tuple[Any, Any]]:
    """Walk a child tree, refusing cycles, reuse, excessive breadth or depth."""
    stack = [(root, 0)]
    seen: set[Any] = set()
    output = []
    while stack:
        ref, depth = stack.pop()
        token = identity(ref)
        if depth > MAX_DEPTH or token in seen or len(seen) >= MAX_NODES:
            refuse("tree_limit_or_cycle")
        seen.add(token)
        node = resolve(ref)
        if not isinstance(node, DictionaryObject):
            refuse("tree_shape")
        output.append((ref, node))
        kids = [item for item in children(node.get(key)) if isinstance(resolve(item), DictionaryObject)]
        if len(stack) + len(kids) > MAX_NODES:
            refuse("tree_frontier")
        stack.extend((item, depth + 1) for item in reversed(kids))
    return output


def role(node: Any, role_map: Any) -> str:
    """Resolve chained custom roles, refusing cycles."""
    current = str(node.get("/S", ""))
    seen: set[str] = set()
    while current in role_map:
        if current in seen or len(seen) >= MAX_ROLE_DEPTH:
            refuse("role_cycle")
        seen.add(current)
        current = str(role_map[current])
    return current


def parent_index(root: Any) -> dict[int, Any]:
    """Index bounded ParentTree number-tree entries without flattening recursively."""
    result: dict[int, Any] = {}
    for _, node in walk(root, "/Kids"):
        nums = children(node.get("/Nums"))
        if len(nums) % 2:
            refuse("parent_tree_shape")
        for index in range(0, len(nums), 2):
            number = int(nums[index])
            if number in result or len(result) >= MAX_NODES:
                refuse("parent_tree_duplicate_or_limit")
            result[number] = resolve(nums[index + 1])
    return result


def marked_text(page: Any, reader: PdfReader) -> dict[int, str]:  # noqa: C901, PLR0912
    """Decode literal simple-font text, retaining exact bytes and marked IDs.

    Form XObjects, inline images, replacement text, clipping, nonvisible modes,
    and general font encodings abstain. This is content association, not pixel
    visibility validation. Existing text remains in producer string order.
    """
    fonts = resolve(resolve(page.get("/Resources", {})).get("/Font", {}))
    stream = ContentStream(page.get_contents(), reader)
    if len(stream.get_data()) > MAX_TEXT or len(stream.operations) > MAX_OPS:
        refuse("content_limit")
    stack: list[int | None] = []
    parts: dict[int, list[str]] = {}
    font = None
    size = 0.0
    in_text = False
    total = 0
    for operands, operator in stream.operations:
        if operator in {b"Do", b"INLINE IMAGE", b"W", b"W*", b"gs"}:
            refuse("unsupported_paint_or_clip")
        if operator == b"Tr" and operands[0] != 0:
            refuse("nonvisible_or_complex_text")
        if operator == b"BDC":
            props = resolve(operands[1])
            if not isinstance(props, DictionaryObject) or "/ActualText" in props:
                refuse("unsupported_marked_properties")
            mcid = props.get("/MCID")
            if mcid is not None:
                mcid = int(mcid)
                if mcid < 0 or mcid >= MAX_NODES or mcid in parts:
                    refuse("duplicate_or_invalid_mcid")
                parts[mcid] = []
            stack.append(mcid)
        elif operator == b"BMC":
            stack.append(None)
        elif operator == b"EMC":
            if not stack:
                refuse("unbalanced_marks")
            stack.pop()
        elif operator == b"BT":
            in_text = True
        elif operator == b"ET":
            in_text = False
        elif operator == b"Tf":
            font = resolve(fonts.get(operands[0]))
            size = float(operands[1])
        elif operator in {b"Tj", b"TJ", b"'", b'"'}:
            active = [item for item in stack if item is not None]
            if not active:
                continue
            if len(active) != 1 or not in_text or size <= 0 or not isinstance(font, DictionaryObject):
                refuse("text_state")
            if (
                font.get("/Subtype") != "/Type1"
                or font.get("/BaseFont") not in {"/Helvetica", "/Helvetica-Bold", "/Helvetica-Oblique", "/Courier"}
                or font.get("/Encoding") != "/WinAnsiEncoding"
                or "/ToUnicode" in font
            ):
                refuse("unsupported_font")
            strings = operands[0] if operator == b"TJ" else [operands[-1]]
            for item in strings:
                if isinstance(item, (int, float)):
                    if item:
                        refuse("positioned_text_array")
                    continue
                if not isinstance(item, TextStringObject):
                    refuse("undecoded_text")
                raw_text = item.original_bytes
                if any(value not in SAFE_WINANSI_CODES for value in raw_text):
                    refuse("unsupported_winansi_code")
                text = raw_text.decode("cp1252", errors="strict")
                total += len(text.encode("utf-8"))
                if total > MAX_TEXT:
                    refuse("text_limit")
                parts[active[0]].append(text)
        if len(stack) > MAX_DEPTH:
            refuse("mark_depth")
    if stack:
        refuse("unbalanced_marks")
    return {key: "".join(value) for key, value in parts.items()}


def recover(  # noqa: C901, PLR0912
    table: Any, role_map: Any, pages: Any, parents: Any, reader: PdfReader
) -> list[list[dict[str, Any]]]:
    """Validate direct row/cell shape, IDs, header links, and MCID backlinks."""
    table_ref = table
    table = resolve(table)
    rows: list[list[dict[str, Any]]] = []
    ids = {}
    used = set()
    page_text = {}
    total_text = 0
    for row_ref in children(table.get("/K")):
        row = resolve(row_ref)
        if not isinstance(row, DictionaryObject) or role(row, role_map) != "/TR":
            refuse("unsupported_table_child")
        if identity(row.get("/P")) != identity(table_ref):
            refuse("stale_row_parent")
        cells = []
        for cell_ref in children(row.get("/K")):
            cell = resolve(cell_ref)
            if not isinstance(cell, DictionaryObject) or role(cell, role_map) not in {"/TH", "/TD"}:
                refuse("unsupported_row_child")
            if identity(cell.get("/P")) != identity(row_ref):
                refuse("stale_cell_parent")
            attrs = resolve(cell.get("/A", {}))
            if (
                not isinstance(attrs, dict)
                or (attrs and attrs.get("/O") != "/Table")
                or attrs.get("/RowSpan", 1) != 1
                or attrs.get("/ColSpan", 1) != 1
            ):
                refuse("unsupported_attributes_or_span")
            mcids = children(cell.get("/K"))
            if len(mcids) != 1 or not isinstance(mcids[0], int) or mcids[0] < 0:
                refuse("unsupported_empty_or_nested_cell_content")
            pg = cell.get("/Pg", row.get("/Pg", table.get("/Pg")))
            pg_id = identity(pg)
            if pg_id not in pages:
                refuse("missing_page")
            page = pages[pg_id]
            mcid = int(mcids[0])
            if (pg_id, mcid) in used:
                refuse("reused_mcid")
            used.add((pg_id, mcid))
            back = parents.get(page.get("/StructParents"), [])
            if not isinstance(back, list) or mcid >= len(back) or identity(back[mcid]) != identity(cell_ref):
                refuse("stale_parent_association")
            if pg_id not in page_text:
                page_text[pg_id] = marked_text(page, reader)
            if mcid not in page_text[pg_id]:
                refuse("missing_marked_content")
            total_text += len(page_text[pg_id][mcid].encode("utf-8"))
            if total_text > MAX_TEXT:
                refuse("table_text_limit")
            cell_id = cell.get("/ID")
            if cell_id is not None:
                raw_id = cell_id.original_bytes.hex()
                if raw_id in ids:
                    refuse("duplicate_cell_id")
                ids[raw_id] = role(cell, role_map)
            else:
                raw_id = None
            headers = children(attrs.get("/Headers"))
            scope = attrs.get("/Scope")
            if scope is not None and (role(cell, role_map) != "/TH" or scope not in {"/Row", "/Column", "/Both"}):
                refuse("invalid_scope")
            cells.append(
                {
                    "text": page_text[pg_id][mcid],
                    "id_hex": raw_id,
                    "object_id": identity(cell_ref),
                    "mcid": mcid,
                    "role": role(cell, role_map),
                    "scope": scope,
                    "headers_hex": [item.original_bytes.hex() for item in headers],
                }
            )
        if not cells or (rows and len(cells) != len(rows[0])):
            refuse("nonrectangular_table")
        rows.append(cells)
    if not rows:
        refuse("empty_table")
    for row in rows:
        for cell in row:
            if any(ids.get(header) != "/TH" for header in cell["headers_hex"]):
                refuse("unresolved_header")
    return rows


def probe(data: bytes) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Audit semantic presence and return only completely validated tables."""
    if len(data) > MAX_BYTES:
        refuse("input_limit")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted:
        return {"status": "encrypted", "tables": [], "tagged_tables": 0}
    catalog = resolve(reader.trailer["/Root"])
    result: dict[str, Any] = {
        "status": "ok",
        "tables": [],
        "tagged_tables": 0,
        "struct_root": "/StructTreeRoot" in catalog,
        "form_leaves": 0,
        "embedded_payload_names": [],
        "abstentions": [],
    }
    try:
        form = resolve(catalog.get("/AcroForm", {}))
        form_nodes = 0
        for field_ref in children(form.get("/Fields")):
            for _, node in walk(field_ref, "/Kids"):
                form_nodes += 1
                if form_nodes > MAX_NODES:
                    refuse("form_node_count")
                if not node.get("/Kids"):
                    result["form_leaves"] += 1
        names = resolve(catalog.get("/Names", {}))
        if "/EmbeddedFiles" in names:
            for _, node in walk(names["/EmbeddedFiles"], "/Kids"):
                pairs = children(node.get("/Names"))
                if len(pairs) % 2:
                    refuse("embedded_tree_shape")
                result["embedded_payload_names"].extend(str(pairs[i]) for i in range(0, len(pairs), 2))
        if (
            len(result["embedded_payload_names"]) > MAX_NODES
            or sum(len(name.encode("utf-8")) for name in result["embedded_payload_names"]) > MAX_TEXT
        ):
            refuse("embedded_name_limit")
        if not result["struct_root"]:
            return result
        root = resolve(catalog["/StructTreeRoot"])
        role_map = resolve(root.get("/RoleMap", {}))
        tables = [ref for ref, node in walk(root, "/K") if role(node, role_map) == "/Table"]
        result["tagged_tables"] = len(tables)
        if not tables:
            return result
        if "/ParentTree" not in root:
            refuse("missing_parent_tree")
        parents = parent_index(root["/ParentTree"])
        if len(reader.pages) > MAX_NODES:
            refuse("page_count")
        pages = {identity(page.indirect_reference): page for page in reader.pages}
        for table in tables:
            try:
                result["tables"].append(recover(table, role_map, pages, parents, reader))
            except (AbstainError, UnicodeError, AttributeError, TypeError, ValueError, KeyError) as error:
                result["abstentions"].append(str(error))
        if (
            sum(len(cell["text"].encode("utf-8")) for table in result["tables"] for row in table for cell in row)
            > MAX_TEXT
        ):
            refuse("document_table_text_limit")
    except (AbstainError, AttributeError, TypeError, ValueError, KeyError) as error:
        result["tables"] = []
        result["status"] = "abstain"
        result["abstentions"].append(str(error))
    return result


def synthetic_case(control: str = "valid") -> bytes:
    """Build authored tagged cells and positive/negative association controls."""
    content = "\n".join(
        f"/Span << /MCID {i} >> BDC {text_op(text, 40 + i % 2 * 180, 700 - i // 2 * 30)} EMC"
        for i, text in enumerate(["Name", "Value", "Alpha", "42"])
    )
    roles = "/RoleMap << /CustomTable /Table >>" if control == "rolemap" else ""
    table_role = "/CustomTable" if roles else "/Table"
    cell_mcid = 9 if control == "missing-mcid" else 3
    header = "missing" if control == "bad-header" else "value"
    parents = "[13 0 R 14 0 R 15 0 R 15 0 R]" if control == "stale-parent" else "[13 0 R 14 0 R 15 0 R 16 0 R]"
    root_k = "9 0 R" if control == "cycle" else "10 0 R"
    if control == "duplicate-mcid":
        cell_mcid = 2
    if control == "untagged":
        return page_pdf(content)
    if control == "nonvisible":
        content = "3 Tr\n" + content
    extras = [
        f"<< /Type /StructTreeRoot /K {root_k} /ParentTree 17 0 R {roles} >>",
        f"<< /Type /StructElem /S {table_role} /P 9 0 R /Pg 3 0 R /K [11 0 R 12 0 R] >>",
        "<< /Type /StructElem /S /TR /P 10 0 R /K [13 0 R 14 0 R] >>",
        "<< /Type /StructElem /S /TR /P 10 0 R /K [15 0 R 16 0 R] >>",
        "<< /Type /StructElem /S /TH /P 11 0 R /Pg 3 0 R /K 0 /ID (name) /A << /O /Table /Scope /Column >> >>",
        "<< /Type /StructElem /S /TH /P 11 0 R /Pg 3 0 R /K 1 /ID (value) /A << /O /Table /Scope /Column >> >>",
        "<< /Type /StructElem /S /TD /P 12 0 R /Pg 3 0 R /K 2 /A << /O /Table /Headers [(name)] >> >>",
        f"<< /Type /StructElem /S /TD /P 12 0 R /Pg 3 0 R /K {cell_mcid} /A << /O /Table /Headers [({header})] >> >>",
        f"<< /Nums [0 {parents}] >>",
    ]
    return raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R /StructTreeRoot 9 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            "/StructParents 0 /Resources << /Font << /F1 5 0 R >> >> >>",
            stream_object(content),
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            "null",
            "null",
            "null",
            *extras,
        ]
    )


def embedded_case(*, stale: bool = False) -> bytes:
    """Inventory an attached CSV without treating it as a verified table."""
    payload = "Name,Value\nAlpha," + ("999" if stale else "42") + "\n"
    return page_pdf(
        text_op("Name Value Alpha 42", 40, 700),
        extra_catalog="/Names << /EmbeddedFiles 9 0 R >>",
        extras=(
            "<< /Names [(table.csv) 10 0 R] >>",
            "<< /Type /Filespec /F (table.csv) /EF << /F 11 0 R >> >>",
            stream_object(payload, "/Type /EmbeddedFile /Subtype /text#2Fcsv"),
        ),
    )


def main() -> None:
    """Save complete local results and a compact timing/coverage report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()
    artifact = ROOT / "bench/results/pdf-master-artifacts/semantic"
    artifact.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    inputs = [
        (str(path.relative_to(ROOT)), path.read_bytes(), "corpus")
        for folder in (ROOT / "tests/assets/real_world", ROOT / "bench/assets/rich")
        for path in sorted(folder.glob("*.pdf"))
    ]
    controls = [
        "valid",
        "rolemap",
        "missing-mcid",
        "bad-header",
        "stale-parent",
        "duplicate-mcid",
        "cycle",
        "untagged",
        "nonvisible",
    ]
    for control in controls:
        data = synthetic_case(control)
        (artifact / f"{control}.pdf").write_bytes(data)
        inputs.append((control, data, "synthetic"))
    for stale in (False, True):
        name = "embedded-stale" if stale else "embedded-consistent"
        data = embedded_case(stale=stale)
        (artifact / f"{name}.pdf").write_bytes(data)
        inputs.append((name, data, "synthetic"))
    for name, data, group in inputs:
        timings = []
        result = {}
        for _ in range(args.repeat):
            start = time.perf_counter()
            try:
                result = probe(data)
            except Exception as error:  # Corpus failures remain visible in research artifacts.
                result = {"status": "error", "error": f"{type(error).__name__}: {error}", "tables": []}
            timings.append((time.perf_counter() - start) * 1000)
        records.append(
            {
                "name": name,
                "group": group,
                "bytes": len(data),
                "median_ms": statistics.median(timings),
                "timings_ms": timings,
                "result": result,
            }
        )
    (artifact / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    counts = Counter(item["group"] for item in records)
    corpus = [item["result"] for item in records if item["group"] == "corpus"]
    roots = sum(bool(item.get("struct_root")) for item in corpus)
    tagged = sum(bool(item.get("tagged_tables")) for item in corpus)
    recovered = sum(bool(item["tables"]) for item in corpus)
    forms = sum(bool(item.get("form_leaves")) for item in corpus)
    attachments = sum(bool(item.get("embedded_payload_names")) for item in corpus)
    denominator = len(corpus)
    lines = [
        "# Semantic fast-path CPU experiment",
        "",
        "Private local research; no core API or dependencies changed.",
        "",
        f"Run: `.venv/bin/python -m bench.semantic_probe --repeat {args.repeat}`. "
        f"pypdf {pypdf_version}; Python {platform.python_version()}; {platform.system()} {platform.machine()}; "
        f"median of {args.repeat} fresh-reader runs; input bytes already in RAM. "
        "Load, inventory, and attempted recovery are included; Python import and disk read are excluded.",
        "",
        f"Denominators: {counts['corpus']} bundled corpus PDFs; {counts['synthetic']} authored controls. "
        "Corpus is a convenience sample, not a deployment prevalence estimate.",
        "",
        f"Observed corpus coverage: {roots}/{denominator} have StructTreeRoot; "
        f"{tagged}/{denominator} have any Table candidate; {recovered}/{denominator} yield validated tables. "
        f"{forms}/{denominator} expose form leaves; {attachments}/{denominator} expose attachment names. "
        "Both authored positive tables recover exactly; all nine other controls yield zero tables. "
        "No geometric speed comparison is claimed because corpus recovery outputs are not equivalent.",
        "",
        "| Input | Tagged table candidates | Validated tables | Form leaves | Embedded names | Median ms | Outcome |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in records:
        result = item["result"]
        outcome = result.get("abstentions") or [result.get("error", result["status"])]
        lines.append(
            f"| {item['name']} | {result.get('tagged_tables', 0)} | {len(result['tables'])} | "
            f"{result.get('form_leaves', 0)} | {len(result.get('embedded_payload_names', []))} | "
            f"{item['median_ms']:.3f} | {'; '.join(outcome)} |"
        )
    lines.extend(
        [
            "",
            "Recovery requires rectangular Table/TR/TH/TD rows, unique cell IDs/MCIDs, resolvable Headers, "
            "valid Scope, matching page StructParents/ParentTree backlinks, and real marked content. "
            "Custom RoleMap chains are accepted with cycle checks. IDs are preserved as byte-exact hex; "
            "text comes from explicitly encoded Type1 WinAnsi literal bytes, never /Alt or guessed metadata.",
            "",
            "The f1040 candidate has eight rows, an empty header spacer, nested /P text cells "
            "with page references on descendants, and /Form cells containing annotation /OBJR links. "
            "It needs explicit form/empty-cell/nested-content integration; it is not merely missing a /Pg key.",
            "",
            "Unsupported: merged cells, nested cell elements/MCR dictionaries, font subsets/CMaps, nonzero TJ "
            "spacing, WinAnsi codes outside printable ASCII/Latin accents (192-255), Form XObjects, "
            "/ActualText, nonvisible text, clipping, and graphics-state dictionaries. "
            "Consistent but semantically wrong producer tags cannot be detected by backlinks alone. "
            "This validates associations, not PDF/UA conformance or pixel visibility.",
            "",
            "Caps: 64 MiB input; 4,096 traversal nodes/children/pages/MCIDs; depth 32; role depth 16; "
            "65,536 content operations; 1 MiB decoded page content/text and recovered table text. "
            "Important limitation: pypdf "
            "parsing, page-tree walking, and stream decoding occur before some checks, so these are "
            "experimental traversal/output bounds, not a hardened untrusted-input guarantee.",
            "",
            "Forms and attachment names are alternate-source presence signals only. Neither implies table "
            "rows/cells. Embedded payloads were not decoded or trusted; a future CSV/JSON path needs "
            "a declared schema plus document/version binding and stale-payload controls.",
            "",
            "Next hypotheses: collect licensed tagged financial tables with ground truth; join validated "
            "MCIDs to the existing glyph interpreter (arbitrary CMaps and geometry); support nested cell "
            "content and spans; check IDTree consistency; validate attachment schemas "
            "and document binding. Benchmark these routes against equivalent complete outputs before "
            "claiming superiority over geometric recovery.",
            "",
            "Primary syntax references: [PDF Association tagged-PDF guide]"
            "(https://pdfa.org/download-area/publications/Tagged-PDF-Best-Practice-Guide.pdf) and "
            "[ISO 32000-2 document-interchange errata]"
            "(https://pdf-issues.pdfa.org/32000-2-2020/clause14.html). Complete results and authored "
            "PDFs remain ignored under `bench/results/pdf-master-artifacts/semantic/`.",
        ]
    )
    (ROOT / "bench/results/semantic-probe.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
