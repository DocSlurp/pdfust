"""Freeze quality-blind full-page and padded residual TATR acquisition arms."""

# Complete source and public image receipts have heterogeneous JSON schemas.
# ruff: noqa: EM101, TRY003, C901, PLR2004
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import resource
import statistics
import time
from pathlib import Path
from typing import Any

from PIL import Image

import pdfust
from bench.generalization_vision_regions import _crop
from bench.p003_gate_run import authenticate
from bench.p003_structure_geometry import digest, encode
from bench.pipeline_repair import _sources
from bench.silver import guard_path

ARMS = ("fullpage", "residual")


def padded(box: list[float], viewport: list[float], heights: list[float]) -> tuple[list[float], float]:
    """Pad by measured word height with a fixed twelve-point cap and page clipping."""
    if (
        len(box) != 4
        or len(viewport) != 4
        or any(not math.isfinite(v) for v in box + viewport + heights)
        or box[0] >= box[2]
        or box[1] >= box[3]
        or viewport[0] >= viewport[2]
        or viewport[1] >= viewport[3]
        or any(h <= 0 for h in heights)
    ):
        raise ValueError("Invalid positive residual/page geometry")
    padding = min(12.0, 1.5 * statistics.median(heights)) if heights else 0.0
    bounds = [
        max(viewport[0], box[0] - padding),
        max(viewport[1], box[1] - padding),
        min(viewport[2], box[2] + padding),
        min(viewport[3], box[3] + padding),
    ]
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValueError("Residual outside page viewport")
    return bounds, padding


def proposals(source: dict[str, Any], regions: list[dict[str, Any]], arm: str) -> list[dict[str, Any]]:
    """Preserve exact full-page or original residual ownership irrespective of pixels."""
    lookup = _sources(source)
    viewport = source["page_size"]
    if arm not in ARMS:
        raise ValueError("Unknown frozen acquisition arm")
    if arm == "fullpage":
        return [
            {
                "region_id": "full_page",
                "bbox": viewport,
                "source_ids": [w["id"] for w in source["words"]],
                "source_kind": "full_page",
                "padding_points": 0.0,
                "context_only_source_ids": [],
            }
        ]
    result = []
    seen: set[str] = set()
    for region in regions:
        if region["kind"] != "residual":
            continue
        ids = region["source_ids"]
        allowed = set(ids)
        if len(ids) != len(allowed) or allowed - set(lookup) or seen & allowed:
            raise ValueError("Residual ownership duplicated or unknown")
        seen.update(allowed)
        if not ids:
            result.append(
                {
                    "region_id": region["id"],
                    "status": "no_owned_source_words",
                    "source_ids": [],
                    "original_bbox": region["bbox"],
                }
            )
            continue
        bounds, padding = padded(
            region["bbox"],
            viewport,
            [lookup[i]["bbox"][3] - lookup[i]["bbox"][1] for i in ids if lookup[i]["bbox"][3] > lookup[i]["bbox"][1]],
        )
        context = [
            w["id"]
            for w in source["words"]
            if w["id"] not in allowed
            and min(w["bbox"][2], bounds[2]) > max(w["bbox"][0], bounds[0])
            and min(w["bbox"][3], bounds[3]) > max(w["bbox"][1], bounds[1])
        ]
        result.append(
            {
                "region_id": region["id"],
                "bbox": bounds,
                "original_bbox": region["bbox"],
                "source_ids": [w["id"] for w in source["words"] if w["id"] in allowed],
                "source_kind": "retained_residual",
                "padding_points": padding,
                "context_only_source_ids": context,
                "source_owned_region_sha256": digest(encode(region)),
            }
        )
    return result


def prepare(original: Path, output: Path) -> dict[str, Any]:
    """Authenticate original source and freeze both acquisition inventories before inference."""
    started, cpu = time.perf_counter(), time.process_time()
    original, output = guard_path(original), guard_path(output)
    old_raw = (original / "source/manifest.json").read_bytes()
    old = json.loads(old_raw)
    baseline, trusted = guard_path(Path(old["baseline"])), guard_path(Path(old["independent_trusted_code"]))
    if digest(trusted.read_bytes()) != old["trusted_code_sha256"]:
        raise ValueError("Independent source trust changed")
    frozen, _ = authenticate(baseline, json.loads(trusted.read_bytes()))
    if [r["id"] for r in frozen["records"]] != [r["id"] for r in old["pages"]]:
        raise ValueError("Incomplete original16page source inventory")
    output.mkdir(parents=True, exist_ok=False)
    code = output / "code"
    code.mkdir()
    code_hashes = {}
    for name in (
        "p003_structure_acquisition.py",
        "p003_structure_acquisition_infer.py",
        "p003_structure_geometry.py",
        "generalization_vision_regions.py",
    ):
        raw = Path(__file__).with_name(name).read_bytes()
        (code / name).write_bytes(raw)
        code_hashes[name] = digest(raw)
    (output / "frozen.json").write_bytes(
        encode(
            {
                "arms": list(ARMS),
                "source_manifest_sha256": digest(old_raw),
                "raster": {"render_edge": 4096, "crop_edge": 1024, "jpeg_quality": 90},
                "residual_padding": "min(12 points,1.5 median positive actualwordheight); clip displaypage",
                "source_ownership": ("fullpage all IDs; residual original IDs; pixel context never owns IDs"),
                "references_read": False,
                "code_sha256": code_hashes,
            }
        )
    )
    pages: dict[str, list[dict[str, Any]]] = {a: [] for a in ARMS}
    for page in old["pages"]:
        result_raw = (baseline / (page["id"] + "-result.json")).read_bytes()
        result = json.loads(result_raw)
        source_raw = (original / "source" / page["source_path"]).read_bytes()
        source = json.loads(source_raw)
        if (
            digest(result_raw) != page["baseline_result_sha256"]
            or digest(source_raw) != page["source_sha256"]
            or result["source"] != source
        ):
            raise ValueError("Source/result differs from authenticated original")
        inventories = {a: proposals(source, result["region_plan"]["regions"], a) for a in ARMS}
        with pdfust.open(stream=Path(page["record"]["pdf_path"]).read_bytes()) as doc:
            pdfpage = doc[page["record"]["page_number"]]
            pdfpage.set_rotation(page["effective_rotation"])
            raster = pdfpage.render(
                scale=4095 / max(pdfpage.rect.width, pdfpage.rect.height), background=(255, 255, 255)
            )
        with Image.open(io.BytesIO(raster)) as image:
            rgb = image.convert("RGB")
        for arm in ARMS:
            directory = output / arm / "source"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / page["source_path"]).write_bytes(source_raw)
            crops = []
            omissions = []
            for proposal in inventories[arm]:
                if proposal.get("status") == "no_owned_source_words":
                    omissions.append(proposal)
                    continue
                url, metadata = _crop(rgb, list(source["page_size"]), proposal["bbox"], 1024, 90)
                image_bytes = base64.b64decode(url.split(",", 1)[1], validate=True)
                if digest(image_bytes) != metadata["image_sha256"]:
                    raise ValueError("Crop bytes differ from receipt")
                name = f"{page['id']}-{proposal['region_id']}.jpg"
                (directory / name).write_bytes(image_bytes)
                crops.append({**proposal, "image_path": name, **metadata})
            pages[arm].append(
                {
                    **{k: v for k, v in page.items() if k != "crops"},
                    "crops": crops,
                    "omitted_regions": omissions,
                    "acquisition_arm": arm,
                }
            )
    manifests = {}
    for arm in ARMS:
        value = {
            **{k: v for k, v in old.items() if k not in ("pages", "resources", "selection", "raster", "code_sha256")},
            "pages": pages[arm],
            "code_sha256": code_hashes,
            "selection": arm
            + " quality-blind source acquisition; every intended page; no generated states/references/scores",
            "acquisition_arm": arm,
            "references_read": False,
            "inference_calls": 0,
            "parent_source_manifest_sha256": digest(old_raw),
            "raster": {"render_edge": 4096, "crop_edge": 1024, "jpeg_quality": 90, "continuous_viewport": True},
        }
        path = output / arm / "source/manifest.json"
        path.write_bytes(encode(value))
        manifests[arm] = {
            "path": str(path),
            "sha256": digest(path.read_bytes()),
            "pages": len(pages[arm]),
            "crops": sum(len(p["crops"]) for p in pages[arm]),
            "owned_words": sum(sum(len(c["source_ids"]) for c in p["crops"]) for p in pages[arm]),
            "context_only_words_count_with_duplicates": sum(
                sum(len(c["context_only_source_ids"]) for c in p["crops"]) for p in pages[arm]
            ),
        }
    receipt = {
        "arms": manifests,
        "references_read": False,
        "inference_calls": 0,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": (
                "Linux self getrusage lifetime RSS/process_time; "
                "one CPU process, contended, no sampling; includes authentication/rendering"
            ),
        },
    }
    (output / "report.json").write_bytes(encode(receipt))
    return receipt


def main() -> None:
    """Prepare two complete coverage arms with no model or paid inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.original, args.output), indent=2))


if __name__ == "__main__":
    main()
