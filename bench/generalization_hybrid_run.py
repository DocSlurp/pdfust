"""Opt-in atomic native-source tables plus fresh CPU-detector crop transcription."""

# Experiment transport and retained result dictionaries contain heterogeneous JSON.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, TRY301, PLR2004
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from bench import generalization_run as native
from bench import generalization_vision_regions as regions
from bench import generalization_vision_run as vision
from bench.silver import guard_path, write_json


class NativeExcludingDetector:
    """Retain the original detector response before conservative native exclusion."""

    def __init__(self, detector: Any, boxes: list[list[float]], helper: Any) -> None:
        """Bind one page detector and the complete verified native table boxes."""
        self.detector = detector
        self.boxes = boxes
        self.helper = helper
        self.raw: dict[str, Any] | None = None
        self.filtered: dict[str, Any] | None = None
        self.excluded: list[dict[str, Any]] = []

    def detect(self, image_bytes: bytes, *, viewport: list[float]) -> dict[str, Any]:
        """Forward unchanged pixels and viewport, retaining both detector inventories."""
        if self.raw is not None:
            raise ValueError("Hybrid page detector may be called only once")
        self.raw = self.detector.detect(image_bytes, viewport=viewport)
        self.filtered, self.excluded = self.helper.exclude_native_proposals(self.raw, self.boxes)
        return self.filtered


def _structure(output: Path, identifier: str) -> dict[str, Any]:
    state = json.loads(guard_path(output / f"{identifier}-structure.json").read_bytes())
    if not isinstance(state, dict):
        raise TypeError("Child structure must be a canonical object")
    return state


def process(record: dict[str, Any], config: dict[str, Any], output: Path, client: Any) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Compose successful native and crop children; expose no partial page tables."""
    from bench import pipeline_hybrid_composition as helper

    began, cpu = time.perf_counter(), time.process_time()
    identifier = record["id"]
    result: dict[str, Any] = {
        "id": identifier,
        "status": "error",
        "processor": "hybrid",
        "route": "hybrid",
        "tables": [],
        "calls": [],
        "unresolved_ids": [],
        "source_conserved": False,
        "source_inventory_complete": False,
        "accounting_complete": False,
        "output_atomic": True,
        "coverage": "unverified",
        "child_artifacts": {"native": "native", "vision": "vision"},
    }
    stage = "config"
    wrapper = None
    output.mkdir(parents=True, exist_ok=True)
    structure_path, markdown_path = output / f"{identifier}-structure.json", output / f"{identifier}.md"
    structure_path.unlink(missing_ok=True)
    markdown_path.unlink(missing_ok=True)
    try:
        if (
            config.get("campaign", "P002") != "P002"
            or config.get("policy", "gated") != "gated"
            or config.get("layout_detector") != "yolo"
            or config.get("image_edge", 1024) != 1024
            or config.get("jpeg_quality", 90) != 90
            or config.get("normalize_rotation", False)
            or config.get("rotation_mode", "preserve") != "preserve"
            or config.get("native_table_orientation", "physical") not in {"physical", "logical"}
            or config.get("_layout_detector") is None
        ):
            raise ValueError("Hybrid control requires P002 gated CPU YOLO, preserved rotation and fixed JPEG90 crops")
        native_output, vision_output = output / "native", output / "vision"
        native_output.mkdir(exist_ok=True)
        vision_output.mkdir(exist_ok=True)
        native_config = {
            **config,
            "processor": "regions",
            "policy": "native",
            "layout_detector": "none",
            "normalize_rotation": False,
            "rotation_mode": "preserve",
            "ocr_source": config.get("ocr_source", "whitespace"),
            "ocr_dpi": config.get("ocr_dpi", 150),
            "ocr_empty": True,
            "raster_rules": False,
        }
        native_config.pop("_layout_detector", None)
        stage = "native"
        child = native.process(record, native_config, native_output, None)
        result["native_result"] = child
        result["calls"].extend(child.get("calls", []))
        if child.get("status") != "ok":
            if child.get("status") == "unsupported_no_text":
                result["status"] = "unsupported_no_text"
            raise ValueError("Native child did not produce complete source output")
        if child.get("calls"):
            raise ValueError("Native-only hybrid child unexpectedly made model calls")
        state = _structure(native_output, identifier)
        cleaned, warnings = native.sanitize_vectors(child["source"])
        result["native_warnings"] = warnings
        source = helper.sanitize_vectors(cleaned)
        result.update(source=source, native_state=state)
        boxes = helper.native_boxes(source, state)
        result["native_boxes"] = boxes
        if config.get("native_table_orientation", "physical") == "logical":
            import pylopdf
            from bench import pipeline_native_orientation as orientation

            stage = "native_orientation"
            data = guard_path(Path(record["pdf_path"])).read_bytes()
            from bench.silver import sha

            if sha(data) != record["pdf_sha256"]:
                raise ValueError("Frozen source PDF changed before native orientation")
            with pylopdf.open(stream=data) as document:
                result["native_orientation_evidence"] = orientation.evidence(document[record["page_number"]], boxes)
        wrapper = NativeExcludingDetector(config["_layout_detector"], boxes, helper)
        vision_config = {**config, "processor": "vision_regions", "_layout_detector": wrapper}
        stage = "vision"
        child = regions.process(record, vision_config, vision_output, client)
        result["vision_result"] = child
        result["calls"].extend(child.get("calls", []))
        result["viewport"] = child.get("viewport")
        result["original_rotation"] = child.get("original_rotation")
        result["rotation_normalized"] = False
        if child.get("status") != "ok":
            raise ValueError("Vision child did not produce complete atomic output")
        vision_state = _structure(vision_output, identifier)
        stage = "compose"
        if config.get("native_table_orientation", "physical") == "logical":
            composed = orientation.compose(source, state, vision_state, result["native_orientation_evidence"])
        else:
            composed = helper.compose(source, state, vision_state)
        result["composition"] = composed
        if composed.get("status") != "ok":
            raise ValueError("Hybrid composition abstained")
        rendered = helper.markdown(composed)
        write_json(structure_path, composed)
        markdown_path.write_text(rendered)
        result.update({key: value for key, value in composed.items() if key not in {"markdown", "status", "route"}})
        result["status"] = "ok"
    except Exception as error:
        result.update(error_stage=stage, error_type=type(error).__name__, tables=[])
        if isinstance(error, (ValueError, KeyError)):
            result["error"] = str(error)[:500]
    if wrapper is not None:
        result.update(
            raw_layout_detection=wrapper.raw,
            filtered_layout_detection=wrapper.filtered,
            excluded_native_proposals=wrapper.excluded,
        )
    result.update(wall_seconds=time.perf_counter() - began, cpu_seconds=time.process_time() - cpu)
    write_json(output / f"{identifier}-result.json", result)
    return result


def main() -> None:
    """Expose a separate explicit P002 hybrid CLI using root's metered run dispatcher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generation-model", choices=vision.MODELS, default=vision.MODELS[1])
    parser.add_argument("--generation-tokens", type=int, choices=(4096, 8192, 16384), default=16384)
    parser.add_argument("--ocr-source", choices=("reextract", "whitespace"), default="whitespace")
    parser.add_argument("--ocr-dpi", type=int, choices=(100, 150, 200, 300), default=150)
    parser.add_argument("--ocr-edge", type=int, choices=(0, 1536, 2048, 3072), default=0)
    parser.add_argument("--ocr-mode", choices=("empty", "uncovered_images"), default="empty")
    parser.add_argument("--ocr-orientation", choices=("fixed", "candidates"), default="fixed")
    parser.add_argument("--native-table-orientation", choices=("physical", "logical"), default="physical")
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    config = {key: value for key, value in vars(args).items() if key not in {"manifest", "output"}}
    config.update(
        run_id=args.output.name,
        campaign="P002",
        processor="hybrid",
        policy="gated",
        layout_detector="yolo",
        normalize_rotation=False,
        rotation_mode="preserve",
        image_edge=1024,
        jpeg_quality=90,
        model=args.generation_model,
        order_seed=20261010,
        ocr_empty=True,
    )
    report = vision.baseline.run(args.manifest, args.output, config)
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
