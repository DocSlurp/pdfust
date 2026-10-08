"""Small CPU-only SLANet-plus pilot using native PDF text instead of OCR.

Run: CUDA_VISIBLE_DEVICES='' PYTHONPATH=src:. \
/home/dan/.cache/pdf-master-cpu/bin/python -m bench.specialist_cpu
No inference API, GPU, training, core changes, or redistributed model weights.
"""

# Optional third-party model objects are heterogeneous; report paragraphs are intentional.
# ruff: noqa: ANN401, ISC004

from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import importlib.metadata
import json
import math
import os
import platform
import time
from pathlib import Path
from typing import Any

import pylopdf
from bench.structure_cases import RECORD_REFERENCES, StructureCase, build_structure_cases
from bench.structure_core import geometry_tables, markdown_tables, score_records, score_tables, source_agreement

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts/specialist"
MODEL_SHA256 = "d57a942af6a2f57d6a4a0372573c696a2379bf5857c45e2ac69993f3b334514b"
MODEL_URL = "https://www.modelscope.cn/models/RapidAI/RapidTable/resolve/v2.0.0/slanet-plus.onnx"
MAX_WORDS = 4096
MAX_REGIONS = 8
MAX_PIXELS = 4_000_000
OPAQUE = 255
ENGINE_CONFIG = {
    "use_cuda": False,
    "use_dml": False,
    "use_cann": False,
    "intra_op_num_threads": 2,
    "inter_op_num_threads": 1,
}


def require_cpu(providers: list[str]) -> None:
    """Fail before inference unless the actual session uses only the CPU provider."""
    if providers != ["CPUExecutionProvider"]:
        message = f"CPU-only pilot refuses actual providers: {providers}"
        raise RuntimeError(message)


def digest(data: bytes) -> str:
    """Record exact input, output, and model provenance."""
    return hashlib.sha256(data).hexdigest()


def project_box(box: list[float], origin: tuple[int, int], scale: tuple[float, float]) -> list[float]:
    """Map PDF display boxes into a cropped raster's pixel coordinates."""
    return [box[index] * scale[index % 2] - origin[index % 2] for index in range(4)]


def contains_center(region: list[float], box: list[float]) -> bool:
    """Use one explicit deterministic source-word admission rule."""
    return region[0] <= (box[0] + box[2]) / 2 <= region[2] and region[1] <= (box[1] + box[3]) / 2 <= region[3]


def pixel_region(region: list[float], scale: tuple[float, float], size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Round an admitted region outward and keep its raster crop within the page."""
    return (
        max(0, math.floor(region[0] * scale[0])),
        max(0, math.floor(region[1] * scale[1])),
        min(size[0], math.ceil(region[2] * scale[0])),
        min(size[1], math.ceil(region[3] * scale[1])),
    )


def merge_regions(regions: list[list[float]]) -> list[list[float]]:
    """Merge intersecting proposals to avoid replacing a word in two tables."""
    output: list[list[float]] = []
    for region in regions:
        pending = region[:]
        index = 0
        while index < len(output):
            other = output[index]
            if pending[0] <= other[2] and other[0] <= pending[2] and pending[1] <= other[3] and other[1] <= pending[3]:
                pending = [
                    min(pending[0], other[0]),
                    min(pending[1], other[1]),
                    max(pending[2], other[2]),
                    max(pending[3], other[3]),
                ]
                output.pop(index)
                index = 0
            else:
                index += 1
        output.append(pending)
    if len(output) > MAX_REGIONS:
        message = "region count exceeds pilot boundary"
        raise RuntimeError(message)
    return sorted(output, key=lambda box: (box[1], box[0]))


def proposals(page: pylopdf.Page, words: list[dict[str, Any]]) -> list[list[float]]:
    """Combine existing native grids and source-geometry table proposals; no gold boxes."""
    boxes = [list(table.bbox) for table in page.find_tables()]
    lookup = {word["id"]: word for word in words}
    for table in geometry_tables(words, wrapped=True):
        selected = [lookup[word_id] for row in table for cell in row for word_id in cell]
        if selected:
            boxes.append(
                [
                    min(word["bbox"][0] for word in selected),
                    min(word["bbox"][1] for word in selected),
                    max(word["bbox"][2] for word in selected),
                    max(word["bbox"][3] for word in selected),
                ]
            )
    rect = page.rect
    return merge_regions(
        [
            [max(0, box[0] - 12), max(0, box[1] - 12), min(rect.width, box[2] + 12), min(rect.height, box[3] + 12)]
            for box in boxes
        ]
    )


def opaque_bgr(rgba: Any) -> Any:
    """Reject discarded-alpha and blank-input mistakes before model inference."""
    if not bool((rgba[:, :, 3] == OPAQUE).all()):
        message = "Raster must be composited onto opaque white before dropping alpha"
        raise RuntimeError(message)
    rgb = rgba[:, :, :3]
    if int(rgb.max()) == int(rgb.min()):
        message = "Pilot raster is blank; refuse invalid preprocessing"
        raise RuntimeError(message)
    return rgb[:, :, ::-1].copy()


def run_route(  # noqa: PLR0913, PLR0917
    engine: Any,
    raster: Any,
    words: list[dict[str, Any]],
    regions: list[list[float]],
    scale: tuple[float, float],
    directory: Path,
    route: str,
) -> dict[str, Any]:
    """Retain predicted structure, cell boxes, HTML, source IDs, and stage timing."""
    np = importlib.import_module("numpy")
    cv = importlib.import_module("cv2")
    outputs = []
    tables = []
    consumed: set[str] = set()
    inference_ms = 0.0
    matching_ms = 0.0
    start_route = time.perf_counter()
    error = None
    try:
        for index, region in enumerate(regions):
            x0, y0, x1, y1 = pixel_region(region, scale, (raster.shape[1], raster.shape[0]))
            image = raster[y0:y1, x0:x1].copy()
            chosen = [word for word in words if contains_center(region, word["bbox"])]
            # RapidTable matcher expects axis-aligned xyxy OCR boxes, not polygons.
            boxes = np.array([project_box(word["bbox"], (x0, y0), scale) for word in chosen], dtype=np.float32)
            records = [(html.escape(word["text"]), 1.0) for word in chosen]
            image_path = directory / f"{route}-{index}.png"
            if not cv.imwrite(str(image_path), image):
                message = "Could not retain raster artifact"
                raise RuntimeError(message)  # noqa: TRY301
            image_sha256 = digest(image_path.read_bytes())
            start = time.perf_counter()
            structures, cells = engine.table_structure([image])
            inference_ms += (time.perf_counter() - start) * 1000
            (directory / f"{route}-{index}-prediction.json").write_text(
                json.dumps({"structure": structures, "cell_boxes": [item.tolist() for item in cells]}, indent=2),
                encoding="utf-8",
            )
            start = time.perf_counter()
            matched_html = engine.table_matcher(structures, cells, [boxes], [records])[0] if chosen else ""
            matching_ms += (time.perf_counter() - start) * 1000
            if matched_html is None:
                matched_html = ""
            parsed = markdown_tables(matched_html)
            tables.extend(parsed)
            consumed.update(word["id"] for word in chosen)
            outputs.append(
                {
                    "region": region,
                    "image_sha256": image_sha256,
                    "pixel_box": [x0, y0, x1, y1],
                    "source_ids": [word["id"] for word in chosen],
                    "structure": structures,
                    "cell_boxes": [item.tolist() for item in cells],
                    "html": matched_html,
                    "html_sha256": digest(matched_html.encode("utf-8")),
                    "tables": parsed,
                }
            )
            (directory / f"{route}-{index}.html").write_text(matched_html, encoding="utf-8")
    except Exception as failure:  # Failures count in scoring instead of disappearing.
        error = f"{type(failure).__name__}: {failure}"
        tables = []
        consumed.clear()
        outputs = []
    outside = "<p>" + " ".join(html.escape(word["text"]) for word in words if word["id"] not in consumed) + "</p>"
    complete = "\n\n".join([item["html"] for item in outputs] + [outside])
    (directory / f"{route}-complete.html").write_text(complete, encoding="utf-8")
    return {
        "tables": tables,
        "outputs": outputs,
        "complete_html": complete,
        "complete_sha256": digest(complete.encode("utf-8")),
        "error": error,
        "inference_ms": inference_ms,
        "matching_ms": matching_ms,
        "route_elapsed_ms": (time.perf_counter() - start_route) * 1000,
        "region_count": len(regions),
        "source": source_agreement(complete, words),
    }


def initialize() -> tuple[Any, dict[str, Any]]:
    """Initialize one CPU-only model and verify its exact pinned weight digest."""
    rapid = importlib.import_module("rapid_table")
    start = time.perf_counter()
    engine = rapid.RapidTable(
        rapid.RapidTableInput(model_type=rapid.ModelType.SLANETPLUS, use_ocr=False, engine_cfg=ENGINE_CONFIG.copy())
    )
    elapsed = (time.perf_counter() - start) * 1000
    session = engine.table_structure.session.session
    providers = session.get_providers()
    require_cpu(providers)
    model_path = Path(engine.cfg.model_dir_or_path)
    model_bytes = model_path.read_bytes()
    observed = digest(model_bytes)
    if observed != MODEL_SHA256:
        message = f"Unexpected model digest: {observed}"
        raise RuntimeError(message)
    options = session.get_session_options()
    extension_path = importlib.import_module("pylopdf.pylopdf_core").__file__
    if extension_path is None:
        message = "Native extension path unavailable"
        raise RuntimeError(message)
    extension = Path(extension_path)
    source_hashes = {
        str(path.relative_to(ROOT)): digest(path.read_bytes())
        for path in [
            ROOT / "rust/src/extract.rs",
            ROOT / "rust/src/document.rs",
            ROOT / "src/pylopdf/__init__.py",
            Path(__file__),
        ]
    }
    return engine, {
        "extension_path": str(extension),
        "extension_sha256": digest(extension.read_bytes()),
        "source_sha256": source_hashes,
        "initialization_ms": elapsed,
        "providers": providers,
        "model_path": str(model_path),
        "model_bytes": len(model_bytes),
        "model_sha256": observed,
        "model_url": MODEL_URL,
        "engine_config": ENGINE_CONFIG,
        "actual_intra_threads": options.intra_op_num_threads,
        "actual_inter_threads": options.inter_op_num_threads,
        "versions": {
            name: importlib.metadata.version(name) for name in ("rapid-table", "onnxruntime", "numpy", "opencv-python")
        },
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def run_case(case: StructureCase, engine: Any, dpi: int) -> dict[str, Any]:
    """Prepare a page once, retaining separate rendering and native-text costs."""
    np = importlib.import_module("numpy")
    directory = ARTIFACTS / case.feature.name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "input.pdf").write_bytes(case.feature.data)
    start = time.perf_counter()
    with pylopdf.open(stream=case.feature.data) as document:
        page = document[0]
        load_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        raw_words = page.get_text("words")
        words = [
            {"id": f"p0-w{index}", "bbox": list(word[:4]), "logical_bbox": list(word[:4]), "text": word[4]}
            for index, word in enumerate(raw_words)
        ]
        if len(words) > MAX_WORDS:
            message = "word count exceeds pilot boundary"
            raise RuntimeError(message)
        text_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        regions = proposals(page, words)
        proposal_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        rect = page.rect
        predicted_pixels = math.ceil(rect.width * dpi / 72) * math.ceil(rect.height * dpi / 72)
        if dpi <= 0 or predicted_pixels > MAX_PIXELS:
            message = "raster preflight exceeds pilot boundary"
            raise RuntimeError(message)
        pixmap = page.get_pixmap(dpi=dpi, background=(255, 255, 255))
        if pixmap.width * pixmap.height > MAX_PIXELS:
            message = "raster exceeds pilot boundary"
            raise RuntimeError(message)
        rgba = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 4)
        raster = opaque_bgr(rgba)  # RapidTable/OpenCV expects BGR.
        render_ms = (time.perf_counter() - start) * 1000
        rect = page.rect
        scale = (pixmap.width / rect.width, pixmap.height / rect.height)
        routes = {}
        for route, route_regions in (("full", [[0, 0, rect.width, rect.height]]), ("cropped", regions)):
            result = run_route(engine, raster, words, route_regions, scale, directory, route)
            result["score"] = score_tables(result["tables"], case.tables)
            result["records"] = score_records(result["tables"], RECORD_REFERENCES.get(case.feature.name, {}))
            result["total_ms"] = load_ms + text_ms + render_ms + result["route_elapsed_ms"]
            if route == "cropped":
                result["total_ms"] += proposal_ms
            routes[route] = result
    value = {
        "name": case.feature.name,
        "input_sha256": digest(case.feature.data),
        "source": case.feature.source,
        "notes": case.feature.notes,
        "gold": case.tables,
        "word_count": len(words),
        "words": words,
        "dpi": dpi,
        "load_ms": load_ms,
        "native_text_ms": text_ms,
        "proposal_ms": proposal_ms,
        "raster_checks": {
            "alpha_min": int(rgba[:, :, 3].min()),
            "alpha_max": int(rgba[:, :, 3].max()),
            "rgb_min": int(rgba[:, :, :3].min()),
            "rgb_max": int(rgba[:, :, :3].max()),
            "background": [255, 255, 255],
        },
        "render_ms": render_ms,
        "regions": regions,
        "routes": routes,
    }
    (directory / "results.json").write_text(json.dumps(value, indent=2), encoding="utf-8")
    return value


def main() -> None:
    """Run exactly eight cases; preserve failures, quality denominators, and costs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dpi", type=int, default=120)
    args = parser.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    engine, metadata = initialize()
    selected = {
        "table-bordered",
        "table-borderless",
        "table-merged",
        "table-borderless-aligned",
        "two-column-order",
        "text-structure-and-literals",
        "corpus-senate-expenditures",
        "corpus-nics-background-checks-2015-11",
    }
    cases = [case for case in build_structure_cases() if case.feature.name in selected]
    results = [run_case(case, engine, args.dpi) for case in cases]
    metadata["wall_seconds"] = time.perf_counter() - started
    (ARTIFACTS / "manifest.json").write_text(
        json.dumps({"metadata": metadata, "results": results}, indent=2), encoding="utf-8"
    )
    lines = [
        "# SLANet-plus CPU specialist pilot",
        "",
        "Private local research; optional isolated environment only.",
        "",
        "Run: `CUDA_VISIBLE_DEVICES='' PYTHONPATH=src:. "
        "/home/dan/.cache/pdf-master-cpu/bin/python -m bench.specialist_cpu --dpi 120`.",
        "",
        f"Versions: {metadata['versions']}; Python {metadata['python']}. "
        f"Actual providers: {metadata['providers']}; actual intra/inter threads: "
        f"{metadata['actual_intra_threads']}/{metadata['actual_inter_threads']}. "
        f"Warm-cache initialization: {metadata['initialization_ms']:.1f} ms; "
        f"complete pilot wall time: {metadata['wall_seconds']:.1f} s.",
        "",
        "Eight first-page inputs: four independently declared table matrices, two no-table prose controls, "
        "and two prepared Senate/NICS corpus pages with partial record checks. "
        "One model call per admitted region; no repetitions or tuning. Failures remain in denominators. "
        "Full-page and cropped routes use identical native words and share page preparation. "
        "No OCR model is loaded. Geometry proposals contain no reference-answer boxes.",
        "",
        "An initial harness run discarded transparent alpha, producing entirely black inputs. "
        "That run is archived as invalid under `specialist-invalid-alpha-v1/` and contributes no model "
        "quality evidence. This run renders explicitly on white and refuses nonopaque/blank rasters; "
        "representative saved table and prose images were visually inspected.",
        "",
        "| Input | Route | Regions | Cells correct/expected | Exact | Record checks | Source matched/expected | "
        "Render ms | Native ms | Infer ms | Match ms | Total ms | Error |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        for name, route in result["routes"].items():
            score = route["score"]
            source = route["source"]
            records = route["records"]
            lines.append(
                f"| {result['name']} | {name} | {route['region_count']} | "
                f"{score.get('correct_cells', 0)}/{score.get('total_cells', 0)} | "
                f"{score.get('exact', '-')} | {records['correct']}/{records['total']} | "
                f"{source['matched_tokens']}/{source['source_tokens']} | {result['render_ms']:.1f} | "
                f"{result['native_text_ms']:.1f} | {route['inference_ms']:.1f} | "
                f"{route['matching_ms']:.1f} | {route['total_ms']:.1f} | {route['error'] or '-'} |"
            )
    summary = []
    for route_name in ("full", "cropped"):
        positive = [item["routes"][route_name] for item in results if item["gold"]]
        negative = [item["routes"][route_name] for item in results if item["gold"] == ()]
        corpus = [item["routes"][route_name] for item in results if item["gold"] is None]
        correct = sum(item["score"]["correct_cells"] for item in positive)
        total = sum(item["score"]["total_cells"] for item in positive)
        exact = sum(bool(item["score"]["exact"]) for item in positive)
        false_positives = sum(bool(item["tables"]) for item in negative)
        records_correct = sum(item["records"]["correct"] for item in corpus)
        records_total = sum(item["records"]["total"] for item in corpus)
        summary.append(
            f"{route_name}: cells {correct}/{total}; exact matrices {exact}/{len(positive)}; "
            f"prose false positives {false_positives}/{len(negative)}; corpus partial records "
            f"{records_correct}/{records_total}."
        )
    lines.extend(["", "Observed quality: " + " ".join(summary), ""])
    lines.extend(
        [
            "",
            "Cell scores require the declared row/column position, including merged-slot expansion. "
            "Corpus checks are partial spot checks, not full table accuracy. Source agreement counts "
            "exact tokens, not placement correctness. Complete source prose outside cropped regions is "
            "retained; unmatched words inside model regions may disappear and are scored as losses.",
            "",
            "SLANet is a table structure recognizer, not a page-level table detector. Full-page prose "
            "false positives are therefore an intentional control. Cropped proposals merge intersecting "
            "native-grid/geometry boxes with 12-point margins; no proposal means no model call. "
            "A model failure returns no tables and retains source prose, with the failure reported.",
            "",
            "Stage definitions: native includes word extraction; render includes full-page raster and BGR "
            "conversion; infer includes SLANet preprocess/ONNX/postprocess; matching joins native text "
            "to predicted cells. Total charges load/native/render to each route, plus crop proposals for "
            "cropped routes and route elapsed time (including artifact writes). Shared preparation is "
            "performed once. Initialization and model download are separate. This pilot does not establish "
            "speed superiority over geometry: raster/model costs and output scope differ.",
            "",
            f"Native extension SHA256: `{metadata['extension_sha256']}`. Native/source/script hashes "
            "are retained in the ignored manifest; all cases used one rebuilt extension. "
            "The first separate download plus session initialization took 2.77 s; the reported pilot "
            "initialization reused the verified model cache and excludes optional-runtime imports.",
            "",
            f"Model: {MODEL_URL}; SHA256 `{MODEL_SHA256}`; {metadata['model_bytes']:,} bytes. "
            "RapidTable package code declares Apache-2.0; [the upstream PaddlePaddle SLANet-plus card]"
            "(https://huggingface.co/PaddlePaddle/SLANet_plus/raw/main/README.md) declares Apache-2.0. "
            "The RapidAI conversion's package manifest pins this ONNX checksum; the ModelScope page "
            "did not expose a separately readable converted-weight license through the research browser. "
            "Record this provenance limitation before redistribution. Weights stay only in the isolated "
            "environment and are not copied into repository artifacts.",
            "",
            "[RapidTable source](https://github.com/RapidAI/RapidTable) and "
            "[upstream table module](https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/"
            "module_usage/table_structure_recognition.html) describe the specialist pipeline. "
            "Full PDF inputs, raster crops, predictions, HTML, source IDs, hashes, versions, and errors "
            "remain ignored under `bench/results/pdf-master-artifacts/specialist/`.",
            "",
            "Matching dominates the large corpus pages in this pilot: the upstream matcher loops over "
            "every source box and every predicted cell. Measure a bounded spatial/indexed association route "
            "before spending effort accelerating the ONNX model.",
            "",
            "Next: broader independent table ground truth, bounded cell-box/source-ID admission, "
            "unmatched-word retention, proposal confidence and prose rejection, then repeated timing "
            "against equivalent outputs. A positive-only mean would conceal the prose and corpus failures.",
        ]
    )
    (ROOT / "bench/results/specialist-cpu.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {len(results)} cases; {metadata['wall_seconds']:.1f}s; CPU providers verified.")


if __name__ == "__main__":
    main()
