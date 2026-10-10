"""Freeze all matched YOLO table crops for CPU structure and literal placement controls."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLR2004, PLC0415, E501, PLR0913, PLR0917
from __future__ import annotations

import argparse
import base64
import io
import json
import resource
import time
from pathlib import Path
from typing import Any

from bench import p003_structure_geometry as geometry
from bench import p003_yolo_resolution as detector

CODE_FILES = (
    "p003_yolo_structure.py",
    "p003_yolo_structure_worker.py",
    "p003_yolo_resolution.py",
    "p003_yolo_resolution_worker.py",
    "p003_structure_geometry.py",
    "p003_structure_place.py",
    "generalization_vision_regions.py",
    "pipeline_assembly.py",
    "pipeline_repair.py",
    "silver.py",
)
WEIGHT_SHA = "9df416575a3a36ebd0129342d4f597f14d6e5170268f3d52d28584ab4466a501"
REVISION = "7587a7ef111d9dcbf8ac695f1376ab7014340a0c"


def ownership(source: dict[str, Any], boxes: list[dict[str, Any]], size: int) -> dict[str, Any]:
    """Freeze unique inclusive center ownership, retaining ambiguous centers and complete context."""
    from bench.pipeline_repair import _sources

    _sources(source)
    tables = [(i, b) for i, b in enumerate(boxes) if b["label"].lower() == "table"]
    proposals = [
        {
            "region_id": f"s{size}-b{i}",
            "bbox": b["global_bbox"],
            "detector_box_index": i,
            "detector_confidence": b["confidence"],
            "source_ids": [],
            "context_only_source_ids": [],
            "crossing_owned_word_ids": [],
            "source_kind": "matched_wholepage_yolo_table",
        }
        for i, b in tables
    ]
    decisions = []
    for word in source["words"]:
        b = word["bbox"]
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        hits = [
            i
            for i, p in enumerate(proposals)
            if p["bbox"][0] <= cx <= p["bbox"][2] and p["bbox"][1] <= cy <= p["bbox"][3]
        ]
        owned = hits[0] if len(hits) == 1 else None
        if owned is not None:
            proposals[owned]["source_ids"].append(word["id"])
            p = proposals[owned]["bbox"]
            if b[0] < p[0] or b[1] < p[1] or b[2] > p[2] or b[3] > p[3]:
                proposals[owned]["crossing_owned_word_ids"].append(word["id"])
        for i, p in enumerate(proposals):
            q = p["bbox"]
            if i != owned and min(b[2], q[2]) > max(b[0], q[0]) and min(b[3], q[3]) > max(b[1], q[1]):
                p["context_only_source_ids"].append(word["id"])
        decisions.append(
            {
                "source_id": word["id"],
                "region_id": proposals[owned]["region_id"] if owned is not None else None,
                "center_region_ids": [proposals[i]["region_id"] for i in hits],
                "reason": "unique_center_owner"
                if owned is not None
                else ("contested_center" if hits else "outside_all_proposals"),
            }
        )
    overlaps = []
    for i, a in enumerate(proposals):
        for b in proposals[i + 1 :]:
            x, y = a["bbox"], b["bbox"]
            area = max(0, min(x[2], y[2]) - max(x[0], y[0])) * max(0, min(x[3], y[3]) - max(x[1], y[1]))
            if area > 0:
                overlaps.append({"region_ids": [a["region_id"], b["region_id"]], "intersection_area": area})
    return {
        "proposals": proposals,
        "decisions": decisions,
        "overlapping_proposals": overlaps,
        "unowned_source_ids": [d["source_id"] for d in decisions if d["region_id"] is None],
        "policy": "center in exactly one inclusive proposal owns whole literal ID; multiple/no centers unresolved; crossing owned bboxes flagged; pixel context never owns IDs",
        "proposal_conflicts_not_silently_merged": True,
    }


def prepare(
    yolo: Path, yolo_trust: Path, baseline: Path, source_trust: Path, model: Path, output: Path
) -> dict[str, Any]:
    """Authenticate both authorities and finish all80 crop/source/model/code receipts before inference."""
    from PIL import Image

    import pylopdf
    from bench.generalization_vision_regions import _crop
    from bench.p003_gate_run import authenticate
    from bench.silver import guard_path

    yolo, yolo_trust, baseline, source_trust, model, output = [
        guard_path(p) for p in (yolo, yolo_trust, baseline, source_trust, model, output)
    ]
    started, cpu = time.perf_counter(), time.process_time()
    if output.exists():
        raise FileExistsError("New source freeze required")
    yf = json.loads((yolo / "frozen.json").read_bytes())
    yr = json.loads((yolo / "report.json").read_bytes())
    approved = json.loads(yolo_trust.read_bytes())
    for name, value in yf["code_sha256"].items():
        if (
            Path(name).name != name
            or approved.get(name) != value
            or detector.digest(yolo / "code" / name) != value
            or detector.digest(Path(__file__).with_name(name)) != value
        ):
            raise ValueError("YOLO code differs from independent Git authority")
    frozen, _ = authenticate(baseline, json.loads(source_trust.read_bytes()))
    if (
        yf["records"] != frozen["records"]
        or len(frozen["records"]) != 16
        or yr["source_manifest_sha256"] != detector.digest(yolo / "frozen.json")
        or yf["baseline_frozen_sha256"] != detector.digest(baseline / "frozen.json")
        or yf["baseline_report_sha256"] != detector.digest(baseline / "report.json")
        or yf["external_trusted_code_sha256"] != detector.digest(source_trust)
    ):
        raise ValueError("YOLO/source intended inventory or external source authority differs")
    provenance = json.loads((model / "provenance.json").read_bytes())
    if provenance["revision"] != REVISION or detector.digest(model / "model.safetensors") != WEIGHT_SHA:
        raise ValueError("Pinned original CPU structure checkpoint differs")
    for item in provenance["files"]:
        if detector.digest(model / item["name"]) != item["sha256"]:
            raise ValueError("Pinned model/config bytes changed")
    output.mkdir(parents=True)
    for folder in ("code", "source", "geometry", "placement", "trust"):
        (output / folder).mkdir()
    code = {}
    for name in CODE_FILES:
        data = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(data)
        code[name] = geometry.digest(data)
    for name, path in (("yolo", yolo_trust), ("source", source_trust)):
        (output / "trust" / f"{name}.json").write_bytes(path.read_bytes())
    pages = []
    if [p["id"] for p in yf["pages"]] != [r["id"] for r in frozen["records"]] or [p["id"] for p in yr["pages"]] != [
        r["id"] for r in frozen["records"]
    ]:
        raise ValueError("Missing/misordered YOLO source/result pages")
    for record, yp, receipt in zip(frozen["records"], yf["pages"], yr["pages"], strict=True):
        ident = record["id"]
        original_path = baseline / f"{ident}-result.json"
        original = json.loads(original_path.read_bytes())
        source = original["source"]
        if (
            yp["status"] != "ready"
            or detector.digest(yolo / yp["source_path"]) != yp["source_sha256"]
            or json.loads((yolo / yp["source_path"]).read_bytes()) != source
            or yp["baseline_result_sha256"] != detector.digest(original_path)
            or detector.digest(yolo / yp["image_path"]) != yp["image_sha256"]
        ):
            raise ValueError("Complete authenticated YOLO source/pixels changed")
        name = f"{ident}-source.json"
        (output / "source" / name).write_bytes(geometry.encode(source))
        page = {
            "id": ident,
            "record": record,
            "source_path": name,
            "source_sha256": geometry.digest(geometry.encode(source)),
            "baseline_result_sha256": detector.digest(original_path),
            "original_rotation": original["original_rotation"],
            "effective_rotation": original["effective_rotation"],
            "crops": [],
            "ownership_by_size": {},
            "yolo_results": [],
        }
        pdf = guard_path(Path(record["pdf_path"])).read_bytes()
        if geometry.digest(pdf) != record["pdf_sha256"]:
            raise ValueError("Original PDF bytes changed")
        with pylopdf.open(stream=pdf) as document:
            pdfpage = document[record["page_number"]]
            if (
                list(pdfpage.rect) != source["page_size"]
                or pdfpage.rotation != original["original_rotation"]
                or original["effective_rotation"] != original["original_rotation"]
            ):
                raise ValueError("Original display geometry/rotation differs; no normalization")
            raster = pdfpage.render(
                scale=4095 / max(pdfpage.rect.width, pdfpage.rect.height), background=(255, 255, 255)
            )
        with Image.open(io.BytesIO(raster)) as rendered:
            image = rendered.convert("RGB")
        if [r["imgsz"] for r in receipt["results"]] != list(detector.SIZES):
            raise ValueError("Incomplete YOLO arm inventory")
        for row in receipt["results"]:
            path = yolo / row["path"]
            prediction = json.loads(path.read_bytes())
            size = row["imgsz"]
            if (
                detector.digest(path) != row["sha256"]
                or prediction["status"] != "completed"
                or prediction["image_sha256"] != yp["image_sha256"]
                or prediction["boxes"]
                != detector.project(prediction["raw_boxes"], prediction["viewport"], prediction["image_size"])
                or prediction["viewport"] != source["page_size"]
                or prediction["configuration"] != detector.configuration(size)
            ):
                raise ValueError("Raw YOLO projection or source provenance differs")
            plan = ownership(source, prediction["boxes"], size)
            page["ownership_by_size"][str(size)] = plan
            page["yolo_results"].append({"imgsz": size, "path": str(path), "sha256": row["sha256"]})
            for proposal in plan["proposals"]:
                url, metadata = _crop(image, list(source["page_size"]), proposal["bbox"], 1024, 90)
                data = base64.b64decode(url.split(",", 1)[1], validate=True)
                image_name = f"{ident}-{proposal['region_id']}.jpg"
                (output / "source" / image_name).write_bytes(data)
                page["crops"].append({**proposal, "acquisition_size": size, "image_path": image_name, **metadata})
        pages.append(page)
    manifest = {
        "schema": 1,
        "pages": pages,
        "records": frozen["records"],
        "code_sha256": code,
        "baseline": str(baseline),
        "independent_trusted_code": str(source_trust),
        "trusted_code_sha256": detector.digest(source_trust),
        "yolo_directory": str(yolo),
        "yolo_external_trusted_code": str(yolo_trust),
        "yolo_trusted_code_sha256": detector.digest(yolo_trust),
        "yolo_frozen_sha256": detector.digest(yolo / "frozen.json"),
        "yolo_report_sha256": detector.digest(yolo / "report.json"),
        "acquisition_sizes": list(detector.SIZES),
        "thresholds": list(geometry.THRESHOLDS),
        "model_directory": str(model),
        "model": provenance,
        "raster": {
            "render_scale": "4095/max(display width,height), unchanged original rotation",
            "crop_edge": 1024,
            "jpeg_quality": 90,
            "continuous_viewport": True,
        },
        "old_640_tatr_reused": False,
        "old_640_identity_not_proven": True,
        "references_read": False,
        "inference_calls": 0,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Parent preparation process_time/perf_counter; getrusage lifetime peak; no sampling; contended",
        },
    }
    (output / "source" / "manifest.json").write_bytes(geometry.encode(manifest))
    return manifest


def place(directory: Path) -> dict[str, Any]:
    """Replay frozen logits and existing three literal policies, separately for every acquisition arm/page."""
    from bench import p003_structure_place as placement

    started, cpu = time.perf_counter(), time.process_time()
    manifest_path = directory / "source/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    report = json.loads((directory / "geometry/report.json").read_bytes())
    if report["source_manifest_sha256"] != detector.digest(manifest_path):
        raise ValueError("Frozen structure input changed")
    for name in ("p003_structure_place.py", "pipeline_assembly.py", "pipeline_repair.py", "p003_structure_geometry.py"):
        if detector.digest(Path(__file__).with_name(name)) != manifest["code_sha256"][name]:
            raise ValueError("Frozen placement/decoder differs")
    rows = []
    for page, measured in zip(manifest["pages"], report["pages"], strict=True):
        source_path = directory / "source" / page["source_path"]
        if (
            detector.digest(source_path) != page["source_sha256"]
            or page["id"] != measured["id"]
            or len(page["crops"]) != len(measured["crops"])
        ):
            raise ValueError("Source/prediction inventory differs")
        source = json.loads(source_path.read_bytes())
        pools: dict[tuple[int, float], list[dict[str, Any]]] = {
            (size, threshold): [] for size in detector.SIZES for threshold in geometry.THRESHOLDS
        }
        errors = []
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            path = directory / "geometry" / receipt["path"]
            prediction = json.loads(path.read_bytes())
            if detector.digest(path) != receipt["sha256"] or prediction["crop"] != crop:
                raise ValueError("Raw structure/crop receipt changed")
            if prediction["status"] != "completed":
                errors.append({"region_id": crop["region_id"], "error_type": prediction["error_type"]})
                continue
            for view in prediction["views"]:
                expected = geometry.project(prediction["queries"], crop["bbox"], report["labels"], view["threshold"])
                expected["topology"] = geometry.topology(expected)
                if view != expected:
                    raise ValueError("Frozen query projection/topology differs")
                pools[(crop["acquisition_size"], view["threshold"])].append(
                    {"region_id": crop["region_id"], "source_ids": crop["source_ids"], "topology": view["topology"]}
                )
        for (size, threshold), candidates in pools.items():
            for policy in placement.POLICIES:
                placed = placement.place(source, candidates, policy)
                name = f"{page['id']}-s{size}-t{threshold}-{policy}.json"
                payload = {
                    "id": page["id"],
                    "source": source,
                    "acquisition_size": size,
                    "threshold": threshold,
                    **placed,
                    "inference_errors": errors,
                    "complete_intended_page": True,
                    "prediction_provenance": "literal source IDs only; no generated cell strings",
                }
                path = directory / "placement" / name
                path.write_bytes(geometry.encode(payload))
                rows.append(
                    {
                        "id": page["id"],
                        "acquisition_size": size,
                        "threshold": threshold,
                        "policy": policy,
                        "path": name,
                        "sha256": detector.digest(path),
                        "tables": len(placed["state"]["tables"]),
                        "unresolved_words": len(placed["state"]["unresolved_ids"]),
                        "conflict_count": len(placed["conflicting_table_indices"]),
                        "inference_error_count": len(errors),
                    }
                )
    receipt = {
        "rows": rows,
        "source_manifest_sha256": detector.digest(manifest_path),
        "geometry_report_sha256": detector.digest(directory / "geometry/report.json"),
        "code_sha256": manifest["code_sha256"],
        "references_read": False,
        "new_api_calls": 0,
        "source_conserved": True,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    (directory / "placement/report.json").write_bytes(geometry.encode(receipt))
    return receipt


def main() -> None:
    """Freeze source-only crops or replay completed geometry into exact source placements."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", type=Path)
    for name in ("yolo", "yolo_trust", "baseline", "source_trust", "model", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path)
    args = parser.parse_args()
    if args.place:
        result = place(args.place)
        print(json.dumps({"page_treatments": len(result["rows"]), "resources": result["resources"]}))
    else:
        result = prepare(args.yolo, args.yolo_trust, args.baseline, args.source_trust, args.model, args.output)
        print(
            json.dumps(
                {
                    "pages": len(result["pages"]),
                    "crops": sum(len(p["crops"]) for p in result["pages"]),
                    "resources": result["resources"],
                }
            )
        )


if __name__ == "__main__":
    main()
