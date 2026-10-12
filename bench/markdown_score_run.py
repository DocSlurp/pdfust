"""Convert every PDF in a directory with one tool and record resource usage.

Standalone so it runs unchanged in the project environment and in isolated
converter environments (MarkItDown, Docling, Marker). It imports only the
selected tool. Usage::

    python bench/markdown_score_run.py TOOL INPUT_DIR OUTPUT_DIR

Each ``<case>.pdf`` becomes ``OUTPUT_DIR/TOOL/<case>.md``; referenced image
assets are written next to it under ``<case>_assets/``. ``run.json`` records
versions, options, initialization time, per-case wall/CPU time, errors, and the
process peak RSS (``resource.getrusage``; whole process, including model
initialization). The first case is converted once as an unmeasured warmup.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import platform
import resource
import subprocess
import sys
import time
import traceback
from importlib import metadata
from pathlib import Path
from typing import Any

THREADS = int(os.environ.get("MARKDOWN_SCORE_THREADS", "4"))


def _version(*names: str) -> dict[str, str]:
    versions = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "not installed"
    return versions


def _pdfust(table_strategy: str) -> tuple[Any, str, dict[str, str]]:
    pdfust = importlib.import_module("pdfust")

    def convert(path: Path, _assets: Path) -> str:
        with pdfust.open(path) as doc:
            return str(doc.to_markdown(table_strategy=table_strategy))

    return convert, f"Document.to_markdown(table_strategy={table_strategy!r})", {"pdfust": pdfust.__version__}


def _pymupdf4llm(*, layout: bool) -> tuple[Any, str, dict[str, str]]:
    module = importlib.import_module("pymupdf4llm")
    module.use_layout(layout)

    def convert(path: Path, _assets: Path) -> str:
        options: dict[str, Any] = {"embed_images": True, "show_progress": False}
        if layout:
            options["use_ocr"] = False
        return str(module.to_markdown(str(path), **options))

    options = f"use_layout({layout}); embed_images=True" + ("; use_ocr=False" if layout else "")
    return convert, options, _version("pymupdf4llm", "pymupdf", "pymupdf-layout")


def _plain(tool: str) -> tuple[Any, str, dict[str, str]]:
    if tool == "pymupdf":
        pymupdf = importlib.import_module("pymupdf")

        def convert_pymupdf(path: Path, _assets: Path) -> str:
            with pymupdf.open(path) as doc:
                return "\n\n".join(page.get_text() for page in doc)

        return convert_pymupdf, "Page.get_text() plain text", _version("pymupdf")
    if tool == "pypdf":
        pypdf = importlib.import_module("pypdf")

        def convert_pypdf(path: Path, _assets: Path) -> str:
            return "\n\n".join(page.extract_text() or "" for page in pypdf.PdfReader(path).pages)

        return convert_pypdf, "Page.extract_text() plain text", _version("pypdf")
    pdfplumber = importlib.import_module("pdfplumber")

    def convert(path: Path, _assets: Path) -> str:
        with pdfplumber.open(path) as doc:
            return "\n\n".join(page.extract_text() or "" for page in doc.pages)

    return convert, "Page.extract_text() plain text", _version("pdfplumber")


def _markitdown() -> tuple[Any, str, dict[str, str]]:
    converter = importlib.import_module("markitdown").MarkItDown(enable_plugins=False)

    def convert(path: Path, _assets: Path) -> str:
        return str(converter.convert(str(path)).text_content)

    return convert, "MarkItDown(enable_plugins=False).convert()", _version("markitdown", "pdfminer.six")


def _docling(*, formulas: bool) -> tuple[Any, str, dict[str, str]]:
    # Same configuration as bench/model_features.py.
    accel = importlib.import_module("docling.datamodel.accelerator_options")
    input_format = importlib.import_module("docling.datamodel.base_models").InputFormat
    options_cls = importlib.import_module("docling.datamodel.pipeline_options").PdfPipelineOptions
    converter_module = importlib.import_module("docling.document_converter")
    image_ref_mode = importlib.import_module("docling_core.types.doc").ImageRefMode
    options = options_cls(
        do_ocr=False,
        do_formula_enrichment=formulas,
        generate_picture_images=True,
        accelerator_options=accel.AcceleratorOptions(device=accel.AcceleratorDevice.CPU, num_threads=THREADS),
    )
    converter = converter_module.DocumentConverter(
        format_options={input_format.PDF: converter_module.PdfFormatOption(pipeline_options=options)}
    )
    converter.initialize_pipeline(input_format.PDF)

    def convert(path: Path, _assets: Path) -> str:
        result = converter.convert(str(path))
        return str(result.document.export_to_markdown(image_mode=image_ref_mode.EMBEDDED))

    description = f"do_ocr=False; do_formula_enrichment={formulas}; embedded images; CPU {THREADS} threads"
    return convert, description, _version("docling", "docling-core", "torch")


def _marker() -> tuple[Any, str, dict[str, str]]:
    converter = importlib.import_module("marker.converters.pdf").PdfConverter(
        artifact_dict=importlib.import_module("marker.models").create_model_dict(),
        config={"mode": "fast", "disable_ocr": True, "use_llm": False, "disable_tqdm": True, "pdftext_workers": 1},
    )
    text_from_rendered = importlib.import_module("marker.output").text_from_rendered

    def convert(path: Path, assets: Path) -> str:
        text, _, images = text_from_rendered(converter(str(path)))
        if images:
            assets.mkdir(parents=True, exist_ok=True)
            for filename, image in images.items():
                buffer = io.BytesIO()
                image.save(buffer, format=image.format or "JPEG")
                (assets / Path(filename).name).write_bytes(buffer.getvalue())
            # Rewrite bare references to the retained asset directory.
            for filename in images:
                text = text.replace(f"]({filename})", f"]({assets.name}/{Path(filename).name})")
        return str(text)

    description = f"mode=fast; disable_ocr=True; use_llm=False; pdftext_workers=1; torch threads {THREADS}"
    return convert, description, _version("marker-pdf", "surya-ocr", "torch")


def _source() -> dict[str, Any]:
    """Record the checkout that produced these outputs (pdfust builds depend on it)."""
    root = Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()  # noqa: S607
        status = subprocess.check_output(["git", "status", "--porcelain", "--", "rust", "src"], cwd=root, text=True)  # noqa: S607
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}
    return {"commit": commit, "dirty": bool(status)}


TOOLS = {
    "pdfust": lambda: _pdfust("lines"),
    "pdfust-text-tables": lambda: _pdfust("text"),
    "pymupdf4llm-layout": lambda: _pymupdf4llm(layout=True),
    "pymupdf4llm-legacy": lambda: _pymupdf4llm(layout=False),
    "pymupdf": lambda: _plain("pymupdf"),
    "pypdf": lambda: _plain("pypdf"),
    "pdfplumber": lambda: _plain("pdfplumber"),
    "markitdown": _markitdown,
    "docling": lambda: _docling(formulas=False),
    "docling-formulas": lambda: _docling(formulas=True),
    "marker-fast": _marker,
}


def main() -> None:
    """Convert all inputs with one tool and write outputs plus run.json."""
    tool, input_dir, output_root = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if THREADS > 0 and tool in {"docling", "docling-formulas", "marker-fast"}:
        importlib.import_module("torch").set_num_threads(THREADS)
    output_dir = output_root / tool
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cpu_started = time.process_time()
    convert, options, versions = TOOLS[tool]()
    init = {"wall_ms": (time.perf_counter() - started) * 1000, "cpu_ms": (time.process_time() - cpu_started) * 1000}
    inputs = sorted(input_dir.glob("*.pdf"))
    if inputs:
        # The measured conversion below records any error.
        with contextlib.suppress(Exception):
            convert(inputs[0], output_dir / "_warmup_assets")
    cases = {}
    for path in inputs:
        assets = output_dir / f"{path.stem}_assets"
        wall, cpu = time.perf_counter(), time.process_time()
        try:
            text, error = convert(path, assets), None
        except Exception:  # failures are retained as results
            text, error = "", traceback.format_exc(limit=3)
        cases[path.stem] = {
            "wall_ms": (time.perf_counter() - wall) * 1000,
            "cpu_ms": (time.process_time() - cpu) * 1000,
            "error": error,
        }
        (output_dir / f"{path.stem}.md").write_text(text, encoding="utf-8")
    report = {
        "tool": tool,
        "options": options,
        "versions": versions,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "threads": THREADS,
        "source": _source(),
        "initialization": init,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "cases": cases,
    }
    (output_dir / "run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{tool}: {len(cases)} cases, {sum(c['error'] is not None for c in cases.values())} errors")


if __name__ == "__main__":
    main()
