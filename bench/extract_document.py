"""Experimental single-PDF entry point for retained CPU pipeline outputs."""

# Explicit experiment records are heterogeneous JSON, not a public library API.
# ruff: noqa: EM101, TRY003, PLC0415
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from bench.silver import guard_path, sha, write_json

MODES = ("native", "hybrid-haiku", "hybrid-sonnet")
MAX_PAGES = 4096
DEFAULT_MAX_PAGES = 128
MAX_PDF_BYTES = 64 * 1024 * 1024
MAX_COMBINED_BYTES = 64 * 1024 * 1024


def _invoke(command: list[str], log: Path) -> int:
    """Delegate assembly and metering to existing CLI code in a CPU child process."""
    with log.open("wb") as stream:
        completed = subprocess.run(  # noqa: S603 - explicit Python module and bounded validated arguments.
            command, stdout=stream, stderr=subprocess.STDOUT,
            env={**os.environ, "CUDA_VISIBLE_DEVICES": ""}, check=False,
        )
    return completed.returncode


def _provenance(row: dict[str, Any], mode: str) -> dict[str, Any]:
    """Describe retained literal/transcribed ownership without inventing labels."""
    tables = row.get("tables", [])
    labels = [table.get("text_provenance") for table in tables]
    explicit = row.get("text_provenance")
    native_validated = row.get("source_conserved") is True and (
        mode == "native" or (
            row.get("accounting_complete") is True and row.get("source_inventory_complete") is True
            and all(value == "native-source" for value in labels)
        )
    )
    if "model-transcribed" in labels:
        native_remaining = "native-source" in labels or bool(row.get("unresolved_ids"))
        label = (
            explicit if isinstance(explicit, str) and ("model-transcribed" in explicit or "mixed" in explicit)
            else "mixed native/OCR source-owned and model-transcribed" if native_remaining
            else "model-transcribed tables"
        )
    elif isinstance(explicit, str) and explicit and (native_validated or "model-transcribed" in explicit):
        label = explicit
    elif native_validated:
        label = "native/OCR source-owned"
    else:
        label = "unverified"
    return {
        "text_provenance": label,
        "table_text_provenance": [
            {"table_index": i, "text_provenance": table.get("text_provenance"),
             "source_conserved": table.get("source_conserved")}
            for i, table in enumerate(tables)
        ],
        "accounting_complete": row.get("accounting_complete"),
        "source_inventory_complete": row.get("source_inventory_complete"),
    }


def extract(  # noqa: C901, PLR0912 - bounded admission, dispatch and artifact refusal remain explicit.
    pdf: Path, output: Path, *, mode: str = "native", pages: list[int] | None = None,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> dict[str, Any]:
    """Freeze source-only records and retain complete/partial document artifacts."""
    import pylopdf

    if mode not in MODES:
        raise ValueError("Unknown experimental extraction mode")
    if type(max_pages) is not int or not 1 <= max_pages <= MAX_PAGES:
        raise ValueError("max_pages must be an integer from 1 through 4096")
    pdf, output = guard_path(pdf), guard_path(output)
    if output.exists():
        raise FileExistsError("Document output directory must be new")
    with pdf.open("rb") as stream:
        data = stream.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise ValueError("Experimental document input exceeds 64 MiB")
    with pylopdf.open(stream=data) as document:
        page_count = len(document)
    if (pages is None and page_count > max_pages) or (pages is not None and len(pages) > max_pages):
        raise ValueError("Requested page count exceeds max_pages admission")
    if pages is not None and (
        not pages or any(type(page) is not int or not 0 <= page < page_count for page in pages)
        or len(set(pages)) != len(pages)
    ):
        raise ValueError("Requested pages must be distinct valid zero-based indices")
    requested = list(range(page_count)) if pages is None else sorted(pages)
    if not requested or len(requested) > max_pages:
        raise ValueError("Requested page count exceeds max_pages admission")
    fingerprint = sha(data)
    del data
    records: list[dict[str, Any]] = [
        {"id": "p" + sha(f"{fingerprint}:{page}".encode())[:20], "pdf_path": str(pdf),
         "pdf_sha256": fingerprint, "page_number": page}
        for page in requested
    ]
    output.mkdir(parents=True, exist_ok=False)
    manifest = output / "source-manifest.json"
    write_json(manifest, {"schema": 1, "split": "DEV", "pages": records})
    # Source-only DEV marks the inference boundary; this wrapper creates no gold
    # annotations, scoring identity or reference files for the arbitrary PDF.
    run_id = "document-" + uuid.uuid4().hex
    # CLI output basename becomes the paid tag's run_id; use a unique child name.
    pipeline = output / run_id
    module = "bench.generalization_run" if mode == "native" else "bench.generalization_hybrid_run"
    command = [sys.executable, "-m", module, "--manifest", str(manifest), "--output", str(pipeline)]
    if mode == "native":
        command += ["--policy", "native", "--rotation-mode", "preserve", "--ocr-source", "whitespace"]
    else:
        model = "anthropic/claude-" + mode.split("-", 1)[1] + "-5.5"
        command += [
            "--generation-model", model, "--generation-tokens", "16384", "--ocr-source", "whitespace",
            "--native-table-orientation", "logical",
        ]
    command += ["--ocr-dpi", "150"]
    wrapper_path = Path(__file__).resolve()
    (output / "extract_document.py").write_bytes(wrapper_path.read_bytes())
    write_json(output / "document-input.json", {
        "pdf_path": str(pdf), "pdf_sha256": fingerprint, "source_page_count": page_count,
        "requested_pages": requested, "max_pages": max_pages, "max_pdf_bytes": MAX_PDF_BYTES,
        "mode": mode, "command": command, "wrapper_sha256": sha(wrapper_path.read_bytes()),
        "local_gpu_used": False, "pipeline_directory": pipeline.name,
    })
    started = time.perf_counter()
    exit_code = _invoke(command, output / "pipeline.log")
    report_path = pipeline / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    predictions = {row["id"]: row for row in report.get("results", [])}
    summary: list[dict[str, Any]] = []
    fragments: list[str | Path] = []
    for record in records:
        ident, page = record["id"], record["page_number"]
        row = predictions.get(ident, {})
        markdown_path = pipeline / f"{ident}.md"
        structure_path = pipeline / f"{ident}-structure.json"
        successful = row.get("status") == "ok" and markdown_path.is_file() and structure_path.is_file()
        item = {
            "id": ident, "page_number": page, "status": "ok" if successful else "error",
            "source_conserved": row.get("source_conserved", False) if successful else False,
            **(_provenance(row, mode) if successful else {"text_provenance": "unavailable"}),
            "result": str((pipeline / f"{ident}-result.json").relative_to(output)),
        }
        fragments.append(f"## Page {page + 1}\n\n")
        if successful:
            item.update(
                markdown=str(markdown_path.relative_to(output)), structure=str(structure_path.relative_to(output))
            )
            fragments.extend([markdown_path, "\n\n"])
        else:
            reason = row.get("error_type", "MissingCompletePageOutput")
            item["error_type"] = reason
            fragments.append(f"[Page {page + 1} extraction failed; see retained page diagnostics.]\n\n")
        summary.append(item)
    selected_complete = exit_code == 0 and all(row["status"] == "ok" for row in summary)
    complete = selected_complete and len(requested) == page_count
    result = {
        "schema": 1, "status": "complete" if complete else "partial", "complete": complete,
        "requested_pages_complete": selected_complete, "source_page_count": page_count,
        "requested_page_count": len(requested), "successful_pages": sum(row["status"] == "ok" for row in summary),
        "pdf_sha256": fingerprint, "mode": mode, "pages": summary, "pipeline_exit_code": exit_code,
        "pipeline_report": str(report_path.relative_to(output)), "pipeline_directory": pipeline.name,
        "costs": {key: report.get(key) for key in (
            "calls", "ledger_attempts", "accounted_usd", "effective_usd", "provider_reported_usd", "cost_bases",
        )},
        "pipeline_resources": report.get("metrics"),
        "layout_detector_initialization": report.get("layout_detector_initialization"),
        "wrapper_dispatch_wall_seconds": time.perf_counter() - started,
        "measurement_scope": "pipeline_resources measures runner child process; detector worker separate; "
        "dispatch wall includes child startup and aggregation; wrapper CPU/RSS unmeasured",
        "local_gpu_used": False,
        "combined_max_bytes": MAX_COMBINED_BYTES,
        "combined_markdown_complete": True,
    }
    status_line = (
        f"Status: {result['status']}; {len(requested)} of {page_count} source pages requested, "
        f"{result['successful_pages']} successfully extracted.\n\n"
    )
    heading = "# PDF extraction\n\n" + status_line
    total_bytes = len(heading.encode()) + sum(
        fragment.stat().st_size if isinstance(fragment, Path) else len(fragment.encode()) for fragment in fragments
    )
    if total_bytes > MAX_COMBINED_BYTES:
        result.update(
            status="partial", complete=False, combined_markdown_complete=False,
            combined_output_error="CombinedMarkdownSizeLimit", combined_requested_bytes=total_bytes,
        )
        combined = (
            "# PDF extraction\n\nStatus: partial. Combined Markdown exceeds its UTF-8 size limit. "
            "Complete individual page artifacts remain retained; see document.json.\n"
        )
    else:
        combined = heading + "".join(
            fragment.read_text() if isinstance(fragment, Path) else fragment for fragment in fragments
        )
    (output / "document.md").write_text(combined)
    write_json(output / "document.json", result)
    return result


def main() -> None:
    """Extract an arbitrary local PDF without constructing a scoring corpus."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=MODES, default="native")
    parser.add_argument("--page", type=int, action="append", help="Zero-based index; repeat for a subset, default all")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    args = parser.parse_args()
    result = extract(args.pdf, args.output, mode=args.mode, pages=args.page, max_pages=args.max_pages)
    print(json.dumps({key: value for key, value in result.items() if key != "pages"}, indent=2))
    if not result["complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
