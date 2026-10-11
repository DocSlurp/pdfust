"""Source-only crop resolution derivatives of the immutable synthetic24 protocol."""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import resource
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from PIL import Image

from bench import p003_synthetic_relations as evidence
from bench import p003_synthetic_relations_eval as evaluator
from bench import p003_synthetic_relations_run as legacy
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, PLR2004, C901, PLR0912, TC003, SLF001, SIM102
VERSION = "p003-synthetic-resolution-v1"
EDGES = (256, 400, 500, 768, 1024)
MODELS = tuple(legacy.IMAGE_MODELS)
IMAGE_CODE = tuple(
    dict.fromkeys(("p003_synthetic_resolution.py", "p003_synthetic_relations_eval.py", *evaluator.PURE_FILES))
)
MAX_FULL_RENDER_PIXELS = 16_000_000


@contextmanager
def extended_edges() -> Iterator[None]:
    """Temporarily admit new edges in this single standalone process, restoring originals."""
    original = evidence.EDGES
    if original not in ((128, 512), (128, 512, *EDGES)):
        raise ValueError("Unexpected immutable protocol edge inventory")
    evidence.EDGES = (128, 512, *EDGES)  # type: ignore[assignment]  # isolated extension of frozen two-edge annotation
    try:
        yield
    finally:
        evidence.EDGES = original


def viewport(record: dict[str, Any]) -> list[float]:
    """Require identical retained crop framing at both original control edges."""
    originals = [i for i in record["images"] if i["scope"] == "crop"]
    if len(originals) != 2 or {i["edge"] for i in originals} != {128, 512}:
        raise ValueError("Exact two original crop controls required")
    if originals[0]["viewport"] != originals[1]["viewport"]:
        raise ValueError("Original crop viewports differ")
    return list(originals[0]["viewport"])


def render(record: dict[str, Any], pdf: bytes, edge: int) -> tuple[bytes, dict[str, Any]]:
    """Reuse exact original RGB PNG/render/crop rounding at a new predeclared edge."""
    if edge not in EDGES or sha(pdf) != record["pdf_sha256"]:
        raise ValueError("New declared edge and exact original PDF required")
    bounds, page = viewport(record), record["source"]["page_size"]
    scale = edge / max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    full_pixels = math.ceil((page[2] - page[0]) * scale) * math.ceil((page[3] - page[1]) * scale)
    if full_pixels > MAX_FULL_RENDER_PIXELS:
        raise ValueError("Bounded full-page render pixels exceeded; no implicit rescaling")
    with extended_edges():
        raw = evidence.image(pdf, edge=edge, viewport=bounds)
    with Image.open(io.BytesIO(raw)) as image:
        dimensions = list(image.size)
        if image.mode != "RGB":
            raise ValueError("Exact RGB source pixels required")
    return raw, {
        "scope": "crop",
        "edge": edge,
        "viewport": bounds,
        "path": f"images/{record['id']}-crop-{edge}.png",
        "sha256": sha(raw),
        "encoded_bytes": len(raw),
        "dimensions": dimensions,
        "encoding": "Lossless actual source RGB PNG, compress6, no palette",
        "coordinate_mapping": (
            "Render source page at edge/max(viewport extent); "
            "round display viewport*scale to crop pixel bounds; no resampling"
        ),
        "all_source_words_inside_viewport": True,
        "source_pdf_sha256": record["pdf_sha256"],
        "estimated_full_render_pixels": full_pixels,
    }


def request(record: dict[str, Any], model: str, item: dict[str, Any], raw: bytes) -> dict[str, Any]:
    """Build unchanged native instructions/literals with explicit derived pixel scope."""
    if model not in MODELS or item["edge"] not in EDGES or sha(raw) != item["sha256"]:
        raise ValueError("Exact configured model, derived image and digest required")
    if item["viewport"] != viewport(record) or item["source_pdf_sha256"] != record["pdf_sha256"]:
        raise ValueError("Derived framing or source PDF changed")
    body = evidence.request(
        record, model, mode="text_geometry", image_url="data:image/png;base64," + base64.b64encode(raw).decode()
    )
    packet = json.loads(body["state"][0])
    packet["pixel_scope"] = {
        "scope": item["scope"],
        "viewport": item["viewport"],
        "dimensions": item["dimensions"],
        "encoding": item["encoding"],
        "coordinate_mapping": item["coordinate_mapping"],
        "peripheral_rules_may_be_clipped": True,
    }
    body["state"][0] = evidence.dump(packet)
    return body


def build_images(source: Path, source_map: Path, output: Path) -> dict[str, Any]:
    """Authenticate original source and freeze120 new crop images without private labels."""
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New immutable derived image pool required")
    began, cpu = time.perf_counter(), time.process_time()
    context = evaluator.source_context(source, source_map)
    output.mkdir(parents=True)
    (output / "images").mkdir()
    (output / "code").mkdir()
    rows = []
    for record in context["records"]:
        row = {
            "id": record["id"],
            "kind": record["kind"],
            "status": record["status"],
            "source_pdf_sha256": record["pdf_sha256"],
            "images": [],
        }
        for edge in EDGES:
            if record["status"] != "ready":
                row["images"].append({"edge": edge, "status": "source_refused"})
                continue
            try:
                raw, item = render(record, legacy._path(source, record["pdf_path"]).read_bytes(), edge)
            except ValueError as error:
                row["images"].append({"edge": edge, "status": "render_refused", "reason": str(error)})
            else:
                (output / item["path"]).write_bytes(raw)
                row["images"].append({"status": "ready", **item})
        rows.append(row)
    write_json(output / "images.json", {"version": VERSION, "records": rows, "edges": EDGES})
    code = {}
    for name in IMAGE_CODE:
        path = Path(__file__) if name == Path(__file__).name else Path(legacy.__file__).with_name(name)
        raw = path.read_bytes()
        (output / "code" / name).write_bytes(raw)
        code[name] = sha(raw)
    frozen = {
        "version": VERSION,
        "source": str(source.resolve()),
        "source_map": str(source_map.resolve()),
        "source_map_sha256": context["map_sha256"],
        "source_frozen_sha256": context["frozen_sha256"],
        "images_sha256": sha((output / "images.json").read_bytes()),
        "code_sha256": code,
        "image_sha256": {
            item["path"]: item["sha256"] for row in rows for item in row["images"] if item["status"] == "ready"
        },
        "gold_read_or_copied": False,
        "new_api_calls": 0,
        "case_count": 24,
        "new_edges": EDGES,
        "retained_controls": [128, 512],
        "max_full_render_pixels": MAX_FULL_RENDER_PIXELS,
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    write_json(output / "frozen.json", frozen)
    return frozen


def authenticate_images(pool: Path, trusted_map: Path, context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Check independently approved image/source/code receipts without importing archived code."""
    pool, trusted_map = guard_path(pool), guard_path(trusted_map)
    approved = evaluator.load(trusted_map)
    if sha((pool / "frozen.json").read_bytes()) != approved["derived_frozen_sha256"]:
        raise ValueError("Derived pool differs from independent frozen authority")
    frozen = evaluator.load(pool / "frozen.json")
    if (
        frozen["source_frozen_sha256"] != context["frozen_sha256"]
        or frozen["source_map_sha256"] != context["map_sha256"]
        or frozen["gold_read_or_copied"] is not False
        or frozen["new_edges"] != list(EDGES)
        or frozen["case_count"] != 24
    ):
        raise ValueError("Derived pool source/policy identity differs")
    if set(frozen["code_sha256"]) != set(IMAGE_CODE):
        raise ValueError("Exact derivative image code inventory required")
    for name, digest in frozen["code_sha256"].items():
        current = Path(__file__) if name == Path(__file__).name else Path(legacy.__file__).with_name(name)
        if (
            approved.get(name) != digest
            or sha((pool / "code" / name).read_bytes()) != digest
            or sha(current.read_bytes()) != digest
        ):
            raise ValueError("Derived image archived/current code differs from authority")
    raw = (pool / "images.json").read_bytes()
    if sha(raw) != frozen["images_sha256"]:
        raise ValueError("Derived image manifest changed")
    records = evaluator.load(pool / "images.json")["records"]
    by_id = {r["id"]: r for r in records}
    if len(records) != 24 or set(by_id) != {r["id"] for r in context["records"]}:
        raise ValueError("Complete unique24 derived source inventory required")
    for original in context["records"]:
        row = by_id[original["id"]]
        if row["kind"] != original["kind"] or row["source_pdf_sha256"] != original["pdf_sha256"]:
            raise ValueError("Derived source identity changed")
        if [i["edge"] for i in row["images"]] != list(EDGES):
            raise ValueError("All five new resolutions required")
        for item in row["images"]:
            if item["status"] == "ready":
                if (
                    item["viewport"] != viewport(original)
                    or frozen["image_sha256"].get(item["path"]) != item["sha256"]
                    or sha(legacy._path(pool, item["path"]).read_bytes()) != item["sha256"]
                ):
                    raise ValueError("Derived image/frame/inventory bytes changed")
    return by_id


def main() -> None:
    """Prepare new source-only pixels; no hosted or label option exists."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-map", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_images(args.source, args.source_map, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
