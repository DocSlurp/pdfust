"""Freeze authenticated source-only DEV crops before local structure inference."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import base64
import io
import json
import resource
import time
from pathlib import Path
from typing import Any

from PIL import Image

import pdfust
from bench.generalization_vision_regions import _crop
from bench.p003_gate_run import authenticate
from bench.p003_structure_geometry import digest, encode


def prepare(baseline: Path, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Retain all pages and all detector proposals without inspecting generated text."""
    started, cpu = time.perf_counter(), time.process_time()
    frozen, _ = authenticate(baseline, json.loads(trusted_code.read_bytes()))
    output.mkdir(parents=True, exist_ok=True)
    code = output / "code"
    code.mkdir(exist_ok=True)
    code_sha256 = {}
    for name in (
        "p003_structure_geometry.py",
        "p003_structure_geometry_prepare.py",
        "generalization_vision_regions.py",
    ):
        data = Path(__file__).with_name(name).read_bytes()
        (code / name).write_bytes(data)
        code_sha256[name] = digest(data)
    pages = []
    for record in frozen["records"]:
        result_path = baseline / f"{record['id']}-result.json"
        original = json.loads(result_path.read_bytes())
        source = original["source"]
        regions = [r for r in original["region_plan"]["regions"] if r["kind"] == "detector_proposal"]
        source_path = f"{record['id']}-source.json"
        (output / source_path).write_bytes(encode(source))
        crops = []
        if regions:
            with pdfust.open(stream=Path(record["pdf_path"]).read_bytes()) as document:
                page = document[record["page_number"]]
                page.set_rotation(original["effective_rotation"])
                image_bytes = page.render(
                    scale=4095 / max(page.rect.width, page.rect.height), background=(255, 255, 255)
                )
                with Image.open(io.BytesIO(image_bytes)) as rendered:
                    image = rendered.convert("RGB")
                viewport = list(source["page_size"])
                for region in regions:
                    url, metadata = _crop(image, viewport, region["bbox"], 1024, 90)
                    data = base64.b64decode(url.split(",", 1)[1], validate=True)
                    if digest(data) != metadata["image_sha256"]:
                        raise ValueError("Crop encoding receipt differs")
                    image_path = f"{record['id']}-{region['id']}.jpg"
                    (output / image_path).write_bytes(data)
                    crops.append(
                        {
                            "region_id": region["id"],
                            "bbox": region["bbox"],
                            "source_ids": region["source_ids"],
                            "source_owned_region_sha256": digest(encode(region)),
                            "image_path": image_path,
                            **metadata,
                        }
                    )
        pages.append(
            {
                "id": record["id"],
                "record": record,
                "source_path": source_path,
                "source_sha256": digest(encode(source)),
                "original_rotation": original["original_rotation"],
                "effective_rotation": original["effective_rotation"],
                "crops": crops,
                "baseline_result_sha256": digest(result_path.read_bytes()),
            }
        )
    manifest = {
        "baseline": str(baseline),
        "independent_trusted_code": str(trusted_code),
        "trusted_code_sha256": digest(trusted_code.read_bytes()),
        "pages": pages,
        "code_sha256": code_sha256,
        "selection": "every retained detector_proposal; no generated text, admission route, reference or score routing",
        "raster": {"render_edge": 4096, "crop_edge": 1024, "jpeg_quality": 90, "continuous_viewport": True},
        "references_read": False,
        "inference_calls": 0,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "self_cpu_seconds": time.process_time() - cpu,
            "peak_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "one CPU preprocessing process; lifetime getrusage RSS; no sampling; contended",
        },
    }
    (output / "manifest.json").write_bytes(encode(manifest))
    return manifest


def main() -> None:
    """Prepare source pixels and geometry; this process performs no model inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.baseline, args.trusted_code, args.output)
    print(
        json.dumps(
            {
                "pages": len(report["pages"]),
                "crops": sum(len(p["crops"]) for p in report["pages"]),
                "resources": report["resources"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
