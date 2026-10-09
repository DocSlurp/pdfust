"""CPU-only SLANet-plus DPI/crop sweep with postfreeze relationship scoring."""

# ruff: noqa: ANN401
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import socket
import subprocess
import time
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pylopdf
from bench.borderless_challenge import score
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss
from bench.specialist_cpu import MAX_PIXELS, MODEL_SHA256, initialize, merge_regions, opaque_bgr, run_route
from bench.structure_core import geometry_tables

ROOT = Path("/home/dan/code/oss/pylopdf")
CORPUS = ROOT / "bench/results/pdf-master-artifacts/silver-realism-v2/124953db381d4aa6"
OUTPUT = ROOT / "bench/results/pdf-master-artifacts/specialist-resolution-v1/124953db381d4aa6"
PYTHON = "/home/dan/.cache/pdf-master-cpu/bin/python"
DPIS = (72, 120, 180)
ROUTES = ("page", "crop", "crop-pad4", "crop-pad12")
RSS_LIMIT = 2 * 1024**3
TIME_LIMIT = 600
MAX_SPAN = 64
POLYGON_COORDINATES = 8
BOX_COORDINATES = 4


def sha(path: Path) -> str:
    """Hash exact retained bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, value: Any) -> None:
    """Preserve first source/output snapshots instead of silently overwriting them."""
    if path.exists():
        message = f"Frozen artifact already exists: {path}"
        raise ValueError(message)
    path.write_text(json.dumps(value, indent=2))


def padded(regions: list[list[float]], rect: list[float], padding: float) -> list[list[float]]:
    """Apply explicitly declared padding to source-derived proposals only."""
    return merge_regions(
        [
            [
                max(rect[0], b[0] - padding),
                max(rect[1], b[1] - padding),
                min(rect[2], b[2] + padding),
                min(rect[3], b[3] + padding),
            ]
            for b in regions
        ]
    )


def freeze(output: Path) -> None:
    """Freeze native source inventory and raw geometric crops without reference files."""
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    pages = []
    began, cpu = time.perf_counter(), time.process_time()
    for case in manifest["cases"]:
        pdf = CORPUS / case["pdf_path"]
        if sha(pdf) != case["pdf_sha256"] or case["split"] != "DEV":
            message = "Source PDF identity or split changed"
            raise ValueError(message)
        start, clock = time.perf_counter(), time.process_time()
        with pylopdf.open(pdf) as doc:
            page = doc[0]
            words: list[dict[str, Any]] = [
                {"id": f"{case['id']}-w{i}", "text": w[4], "bbox": list(w[:4]), "logical_bbox": list(w[:4])}
                for i, w in enumerate(page.get_text("words"))
            ]
            native = {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - clock}
            rect = list(page.rect)
            lookup = {w["id"]: w for w in words}
            regions = [list(t.bbox) for t in page.find_tables()]
            for table in geometry_tables(words, wrapped=True):
                selected = [lookup[i] for row in table for cell in row for i in cell]
                if selected:
                    regions.append(
                        [
                            min(w["bbox"][0] for w in selected),
                            min(w["bbox"][1] for w in selected),
                            max(w["bbox"][2] for w in selected),
                            max(w["bbox"][3] for w in selected),
                        ]
                    )
            crops = padded(regions, rect, 0)
            pages.append(
                {
                    "id": case["id"],
                    "pdf_path": str(pdf),
                    "pdf_sha256": sha(pdf),
                    "words": words,
                    "rect": rect,
                    "native_resources": native,
                    "routes": {
                        "page": [rect],
                        "crop": crops,
                        "crop-pad4": padded(crops, rect, 4),
                        "crop-pad12": padded(crops, rect, 12),
                    },
                }
            )
    rss, tool = process_peak_rss()
    write_once(
        output / "source-frozen.json",
        {
            "pages": pages,
            "dpis": DPIS,
            "routes": ROUTES,
            "preparation": {
                "wall_seconds": time.perf_counter() - began,
                "cpu_seconds": time.process_time() - cpu,
                "peak_rss_bytes": rss,
                "measurement": tool + "; SELF time; serial CPU; no sampling",
            },
        },
    )


class MatrixParser(HTMLParser):
    """Parse explicit HTML cells/spans without guessing absent model structure."""

    def __init__(self) -> None:
        """Initialize row and cell records."""
        super().__init__()
        self.rows: list[list[dict[str, Any]]] = []
        self.cell: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Retain explicit row/cell structure and span attributes."""
        if tag == "tr":
            self.rows.append([])
        elif tag in {"td", "th"}:
            values = dict(attrs)
            self.cell = {
                "text": "",
                "row_span": int(values.get("rowspan") or 1),
                "column_span": int(values.get("colspan") or 1),
            }
        elif tag == "br" and self.cell is not None:
            self.cell["text"] += " "

    def handle_data(self, data: str) -> None:
        """Retain recognized matched HTML text."""
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag: str) -> None:
        """Close each HTML cell once."""
        if tag in {"td", "th"} and self.cell is not None:
            if not self.rows:
                self.rows.append([])
            self.rows[-1].append(self.cell)
            self.cell = None


def parse_matrix(text: str) -> dict[str, Any] | None:
    """Return row-major values/spans only when explicit HTML cells exist."""
    parser = MatrixParser()
    parser.feed(text)
    if not parser.rows or not any(parser.rows):
        return None
    occupied: dict[tuple[int, int], str | None] = {}
    spans = []
    anchors = []
    for row, cells in enumerate(parser.rows):
        col = 0
        for cell in cells:
            while (row, col) in occupied:
                col += 1
            rs, cs = cell["row_span"], cell["column_span"]
            if not 1 <= rs <= MAX_SPAN or not 1 <= cs <= MAX_SPAN:
                message = "HTML span exceeds bounded parser admission"
                raise ValueError(message)
            spans.append({"row": row, "column": col, "row_span": rs, "column_span": cs})
            anchors.append([row, col])
            for dr in range(rs):
                for dc in range(cs):
                    if (row + dr, col + dc) in occupied:
                        message = "Overlapping HTML spans"
                        raise ValueError(message)
                    occupied[row + dr, col + dc] = " ".join(cell["text"].split()) if dr == dc == 0 else None
            col += cs
    nrow = max(r for r, c in occupied) + 1
    ncol = max(c for r, c in occupied) + 1
    return {
        "row_count": nrow,
        "col_count": ncol,
        "values": [[occupied.get((r, c)) for c in range(ncol)] for r in range(nrow)],
        "spans": spans,
        "anchors": anchors,
    }


def ownership(page: dict[str, Any], outputs: list[dict[str, Any]], scale: tuple[float, float]) -> dict[str, Any]:
    """Map unambiguous source centers to predicted polygons, separately from matcher text."""
    cells: list[dict[str, Any]] = []
    for output_index, output in enumerate(outputs):
        boxes = output["cell_boxes"][0] if output["cell_boxes"] else []
        for cell_index, polygon in enumerate(boxes):
            if len(polygon) == POLYGON_COORDINATES:
                xs, ys = polygon[::2], polygon[1::2]
                box = [min(xs), min(ys), max(xs), max(ys)]
            elif len(polygon) == BOX_COORDINATES:
                box = polygon
            else:
                continue
            origin = output["pixel_box"][:2]
            box = [(box[i] + origin[i % 2]) / scale[i % 2] for i in range(4)]
            cells.append({"output": output_index, "cell": cell_index, "bbox": box, "source_ids": []})
    unresolved = []
    for word in page["words"]:
        x = (word["bbox"][0] + word["bbox"][2]) / 2
        y = (word["bbox"][1] + word["bbox"][3]) / 2
        matches = [c for c in cells if c["bbox"][0] <= x <= c["bbox"][2] and c["bbox"][1] <= y <= c["bbox"][3]]
        if len(matches) == 1:
            matches[0]["source_ids"].append(word["id"])
        else:
            unresolved.append(word["id"])
    counts = Counter(i for c in cells for i in c["source_ids"]) + Counter(unresolved)
    return {
        "cells": cells,
        "unresolved_ids": unresolved,
        "conserved": counts == Counter(w["id"] for w in page["words"]),
        "scope": "unambiguous predicted-cell center ownership; not matcher identity gold or pixel visibility",
    }


class TimedEngine:
    """Measure CPU inference and matching independently of the reusable route helper."""

    def __init__(self, engine: Any) -> None:
        """Retain the original initialized CPU engine."""
        self.engine = engine
        self.model_cpu = 0.0
        self.match_cpu = 0.0

    def table_structure(self, *args: Any) -> Any:
        """Measure model CPU time."""
        start = time.process_time()
        try:
            return self.engine.table_structure(*args)
        finally:
            self.model_cpu += time.process_time() - start

    def table_matcher(self, *args: Any) -> Any:
        """Measure matching CPU time."""
        start = time.process_time()
        try:
            return self.engine.table_matcher(*args)
        finally:
            self.match_cpu += time.process_time() - start


def worker(output: Path) -> None:
    """Run the cached pinned CPU model without permitting network access."""
    rapid_table = importlib.import_module("rapid_table")

    np = importlib.import_module("numpy")
    rapid_path = rapid_table.__file__
    if rapid_path is None:
        message = "Installed specialist package path unavailable"
        raise RuntimeError(message)
    model = Path(rapid_path).parent / "models/slanet-plus.onnx"
    if not model.exists() or sha(model) != MODEL_SHA256:
        message = "Pinned cached model unavailable; downloads are forbidden"
        raise RuntimeError(message)

    def blocked(*_args: Any, **_kwargs: Any) -> None:
        message = "Specialist sweep forbids network access"
        raise RuntimeError(message)

    socket.socket.connect = blocked  # type: ignore[method-assign]
    start, cpu = time.perf_counter(), time.process_time()
    engine, info = initialize()
    info["initialization_cpu_seconds"] = time.process_time() - cpu
    info["initialization_wall_seconds"] = time.perf_counter() - start
    info["fixed_preprocess_max_side"] = 488
    info["preprocess_note"] = "SLANet-plus normalizes longest side to 488; DPI changes sampling, not tensor size."
    write_once(output / "model.json", info)
    timed = TimedEngine(engine)
    frozen = json.loads((output / "source-frozen.json").read_text())
    rows: list[dict[str, Any]] = []
    for page in frozen["pages"]:
        with pylopdf.open(page["pdf_path"]) as doc:
            for dpi in DPIS:
                start, clock = time.perf_counter(), time.process_time()
                rect = page["rect"]
                width, height = round((rect[2] - rect[0]) * dpi / 72), round((rect[3] - rect[1]) * dpi / 72)
                if width * height > MAX_PIXELS:
                    rows.extend(
                        {"id": page["id"], "dpi": dpi, "route": route, "error": "pixel admission refusal"}
                        for route in ROUTES
                    )
                    continue
                pix = doc[0].get_pixmap(dpi=dpi, background=(255, 255, 255))
                rgba = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 4)
                raster = opaque_bgr(rgba)
                render = {
                    "wall_seconds": time.perf_counter() - start,
                    "cpu_seconds": time.process_time() - clock,
                    "pixels": [pix.width, pix.height],
                }
                scale = (pix.width / (rect[2] - rect[0]), pix.height / (rect[3] - rect[1]))
                for route in ROUTES:
                    directory = output / f"{page['id']}-dpi{dpi}-{route}"
                    directory.mkdir()
                    start, clock = time.perf_counter(), time.process_time()
                    before_model, before_match = timed.model_cpu, timed.match_cpu
                    observed = run_route(timed, raster, page["words"], page["routes"][route], scale, directory, route)
                    matrices = [parse_matrix(o["html"]) for o in observed["outputs"]]
                    row = {
                        "id": page["id"],
                        "dpi": dpi,
                        "route": route,
                        "render_resources": render,
                        "native_resources": page["native_resources"],
                        "observed": observed,
                        "matrices": [m for m in matrices if m is not None],
                        "span_scored": all(m is not None for m in matrices) and bool(matrices),
                        "ownership": ownership(page, observed["outputs"], scale),
                        "wall_seconds": time.perf_counter() - start,
                        "cpu_seconds": time.process_time() - clock,
                        "model_cpu_seconds": timed.model_cpu - before_model,
                        "matching_cpu_seconds": timed.match_cpu - before_match,
                    }
                    row["peak_rss_bytes"], row["rss_tool"] = process_peak_rss()
                    write_once(directory / "frozen-output.json", row)
                    rows.append(row)
                    (output / "progress.json").write_text(json.dumps({"rows": rows}))
    write_once(output / "outputs-frozen.json", {"source_sha256": sha(output / "source-frozen.json"), "rows": rows})


def execute(output: Path) -> None:
    """Bound the isolated worker to ten minutes and 2 GiB sampled RSS."""
    env = {
        **os.environ,
        "CUDA_VISIBLE_DEVICES": "",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "2",
        "PYTHONPATH": str(ROOT / "src") + ":" + str(Path(__file__).resolve().parents[1]),
    }
    start = time.perf_counter()
    with (output / "worker.log").open("w") as log:
        process = subprocess.Popen(  # noqa: S603 -- fixed executable/module; guarded local artifact path
            [PYTHON, "-m", "bench.specialist_resolution", "--worker", "--output", str(output)],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).resolve().parents[1],
        )
        reason = None
        peak = 0
        while process.poll() is None:
            try:
                status = Path(f"/proc/{process.pid}/status").read_text()
                rss = next(int(line.split()[1]) * 1024 for line in status.splitlines() if line.startswith("VmRSS:"))
                peak = max(peak, rss)
            except (OSError, StopIteration):
                pass
            if peak > RSS_LIMIT or time.perf_counter() - start > TIME_LIMIT:
                reason = "RSS2GiB refusal" if peak > RSS_LIMIT else "ten-minute wall refusal"
                process.kill()
                process.wait()
                break
            time.sleep(0.1)
        write_once(
            output / "execution.json",
            {
                "returncode": process.returncode,
                "error": reason,
                "wall_seconds": time.perf_counter() - start,
                "sampled_worker_peak_rss_bytes": peak,
                "measurement": "parent /proc child VmRSS every 0.1s; single worker; no GPU; hard ten-minute cap",
            },
        )


def report(output: Path) -> None:  # noqa: C901
    """Read private targets only after retained outputs are frozen, keeping every denominator."""
    frozen_path = output / "outputs-frozen.json"
    path = frozen_path if frozen_path.exists() else output / "progress.json"
    rows = json.loads(path.read_text())["rows"] if path.exists() else []
    if frozen_path.exists() and json.loads(frozen_path.read_text())["source_sha256"] != sha(
        output / "source-frozen.json"
    ):
        message = "Frozen output/source identity mismatch"
        raise ValueError(message)
    targets = {p["id"]: p for p in json.loads((CORPUS / "private-targets.json").read_text())}
    lookup = {(r["id"], r["dpi"], r["route"]): r for r in rows}
    scores = []
    for dpi in DPIS:
        for route in ROUTES:
            for identifier, target in targets.items():
                row = lookup.get((identifier, dpi, route))
                scored = target["kind"] != "ambiguous"
                observed = row.get("matrices", []) if row else []
                scores.append(
                    {
                        "id": identifier,
                        "dpi": dpi,
                        "route": route,
                        "kind": target["kind"],
                        "scored": scored,
                        "error": not row or bool(row.get("error")) or bool(row.get("observed", {}).get("error")),
                        "scores": score(target, observed) if scored else None,
                        "source_conservation": row.get("ownership", {}).get("conserved") if row else None,
                        "span_available": row.get("span_scored", False) if row else False,
                    }
                )
    if not (output / "private-scores.json").exists():
        write_once(output / "private-scores.json", scores)
    lines = [
        "# CPU SLANet-plus resolution and source-crop sweep",
        "",
        (
            "All 28 reviewed DEV pages stay in each configuration denominator. Ambiguous cases are unscored. "
            "Source-only native geometry selected crops before any reference read. Source crop,+4pt,+12pt are "
            "explicitly frozen alternatives; no gold crop or OCR input is supplied."
        ),
        "",
        (
            "| DPI/route | Borderless exact | Prose false table | Native controls exact | "
            "Ambiguous unscored | Errors/refusals |"
        ),
        "|---|---:|---:|---:|---:|---:|",
    ]
    for dpi in DPIS:
        for route in ROUTES:
            selected = [s for s in scores if s["dpi"] == dpi and s["route"] == route]
            counts = []
            for kind, key in [
                ("borderless", "exact_page"),
                ("prose", "false_positive_page"),
                ("ruled-control", "exact_page"),
            ]:
                cohort = [s for s in selected if s["kind"] == kind]
                counts.append(f"{sum(bool(s['scores'][key]) for s in cohort)}/{len(cohort)}")
            lines.append(
                f"| {dpi}/{route} | {' | '.join(counts)} | "
                f"{sum(s['kind'] == 'ambiguous' for s in selected)} | {sum(s['error'] for s in selected)} |"
            )
    lines += [
        "",
        (
            "| DPI/route | Exact cell matrices | Exact spans | Intended values owned | "
            "Intended words owned | Source IDs conserved |"
        ),
        "|---|---:|---:|---:|---:|---:|",
    ]
    positive_targets = [t for t in targets.values() if t["kind"] == "borderless"]
    value_total = sum(
        bool(v) for t in positive_targets for table in t["tables"] for row in table["values"] for v in row
    )
    word_total = sum(
        len(v.split()) for t in positive_targets for table in t["tables"] for row in table["values"] for v in row if v
    )
    for dpi in DPIS:
        for route in ROUTES:
            selected = [s for s in scores if s["dpi"] == dpi and s["route"] == route]
            positive = [s for s in selected if s["kind"] == "borderless"]
            lines.append(
                f"| {dpi}/{route} | {sum(s['scores']['exact_cells'] for s in positive)}/{len(positive)} | "
                f"{sum(s['scores']['exact_spans'] for s in positive)}/{len(positive)} | "
                f"{sum(s['scores']['owned_values'] for s in positive)}/{value_total} | "
                f"{sum(s['scores']['owned_words'] for s in positive)}/{word_total} | "
                f"{sum(s['source_conservation'] is True for s in selected)}/{len(selected)} |"
            )
    lines += ["", "| DPI/route | Model wall/CPU s | Matching wall/CPU s | Route wall/CPU s |", "|---|---:|---:|---:|"]
    for dpi in DPIS:
        for route in ROUTES:
            observed = [r for r in rows if r["dpi"] == dpi and r["route"] == route and "observed" in r]

            totals = {
                key: sum(r.get(key, 0.0) for r in observed)
                for key in ("model_cpu_seconds", "matching_cpu_seconds", "wall_seconds", "cpu_seconds")
            }

            model_wall = sum(r["observed"]["inference_ms"] for r in observed) / 1000
            match_wall = sum(r["observed"]["matching_ms"] for r in observed) / 1000
            lines.append(
                f"| {dpi}/{route} | {model_wall:.3f}/{totals['model_cpu_seconds']:.3f} | "
                f"{match_wall:.3f}/{totals['matching_cpu_seconds']:.3f} | "
                f"{totals['wall_seconds']:.3f}/{totals['cpu_seconds']:.3f} |"
            )
    frozen_source = json.loads((output / "source-frozen.json").read_text())
    native_wall = sum(p["native_resources"]["wall_seconds"] for p in frozen_source["pages"])
    native_cpu = sum(p["native_resources"]["cpu_seconds"] for p in frozen_source["pages"])
    renders = {(r["id"], r["dpi"]): r["render_resources"] for r in rows if "render_resources" in r}
    render_wall = sum(r["wall_seconds"] for r in renders.values())
    render_cpu = sum(r["cpu_seconds"] for r in renders.values())
    lines += [
        "",
        (
            f"Native load/text preparation: {native_wall:.3f}s wall/{native_cpu:.3f}s CPU. "
            f"Rendering (84 distinct page/DPI rasters, each shared by four routes): "
            f"{render_wall:.3f}s wall/{render_cpu:.3f}s CPU. "
            "Source proposal and preparation resources remain in source-frozen.json. "
            "Stage-summed CPU is measured process CPU, not a complete worker total; imports and global output "
            "serialization excluded. Worker RSS is sampled separately from the preparation parent."
        ),
        "",
        (
            "Background: the root image sweep was network-bound and another agent could render 16 training "
            "derivatives concurrently. Timings describe this run, not a throughput ceiling. No repeats were run."
        ),
    ]
    model = (
        json.loads((output / "model.json").read_text())
        if (output / "model.json").exists()
        else {"error": "unavailable"}
    )
    execution = json.loads((output / "execution.json").read_text())
    lines += [
        "",
        "Model initialization/provenance: `"
        + json.dumps(
            {
                k: model.get(k)
                for k in (
                    "model_sha256",
                    "providers",
                    "initialization_cpu_seconds",
                    "initialization_wall_seconds",
                    "actual_intra_threads",
                    "actual_inter_threads",
                    "versions",
                    "fixed_preprocess_max_side",
                )
            }
        )
        + "`.",
        "",
        "Worker resources: `" + json.dumps(execution) + "`.",
        "",
        (
            "Routes retain HTML structure, cell boxes, row-major matrices/spans, exact source text/IDs, "
            "model/matching CPU and wall timings, render/native timings and RSS. Exact cells/spans and intended-word "
            "slot ownership are postfreeze scores in private-scores.json; raw string retention is not quality. "
            "Cell center ownership conserves IDs with ambiguous hits unresolved. It is separate "
            "from matcher text alignment and independently annotated source-ID gold. Missing HTML spans are unscored, "
            "not inferred. Empty source proposals perform zero model calls and remain full-denominator outcomes."
        ),
        "",
        (
            "SLANet-plus fixes the longest side at 488 before a 488×488 tensor. The DPI sweep tests "
            "raster sampling/crop context, not larger model tensors. No input-size override was attempted. CPU-only "
            "cached pinned weights, two intra-op and one inter-op threads, no network access. Provider cost $0."
        ),
        "",
        f"Artifacts: `{output}`. Source hash `{sha(output / 'source-frozen.json')}`. Raw outputs stay ignored.",
        "",
    ]
    (Path(__file__).parent / "results/specialist-resolution.md").write_text("\n".join(lines))


def main() -> None:
    """Freeze, run bounded CPU inference, and score only postfreeze outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    output = guard_path(args.output)
    if args.freeze:
        freeze(output)
    if args.worker:
        worker(output)
    if args.run:
        execute(output)
    if args.report:
        report(output)


if __name__ == "__main__":
    main()
