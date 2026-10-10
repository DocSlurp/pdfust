"""Fresh P003 decision experiments using the retained complete-pipeline contract."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from bench import pipeline_run
from bench.decision_hosted import DECISION_MODELS
from bench.pipeline_frontier import MODELS as CHAT_MODELS
from bench.silver import guard_path

PRESETS = ("ordinal", "gated_ordinal", "hybrid", "vision_regions", "p003_regions")
HYBRID_EDGE = 1024
P003_TRANSPORT_CONCURRENCY = 3


def configuration(args: argparse.Namespace) -> dict[str, Any]:
    """Declare treatments explicitly; no reference labels or old answers are read."""
    config: dict[str, Any] = {
        "campaign": "P003", "run_id": args.output.name, "pilot": False,
        "order_seed": args.order_seed, "policy": "gated", "workers": 1,
        "model": args.model, "generation_model": args.generation_model,
        "generation_provider": args.generation_provider,
        "transcription_representation": args.transcription_representation,
        "generation_tokens": 8192, "image_edge": args.image_edge,
        "layout_detector": "yolo", "ocr_empty": True, "ocr_dpi": args.ocr_dpi,
        "ocr_edge": args.ocr_edge, "ocr_mode": "empty", "ocr_orientation": "fixed",
        "ocr_source": "whitespace", "source_order": "original",
        "normalize_rotation": True, "rotation_mode": "native",
        "processor": "regions", "assembly_method": "generate",
        "column_consensus": True, "context_rows": 1, "legend": True,
        "readable_packet": True, "packet_characters": 25000,
        "region_words": 1024, "region_characters": 16000,
        "generation_format": "indices", "generation_evidence": "arrays",
        "generation_prompt": "column_tracks", "generation_row_evidence": False,
        "gate_row_evidence": args.gate_row_evidence, "gate_review_model": None,
        "gate_image": not args.text_gate,
        "gate_provider": args.gate_provider,
        "answer_tokens": 2048, "raster_rules": False, "raster_edge": 1536,
        "detector_edge": 1536, "detector_tiles": "none", "detector_fusion": "none",
        "detector_residual": "retain", "detector_boundary": "retain",
        "repeat_index": args.repeat_index, "preset": args.preset,
    }
    if args.gate_image_mode != "rgb":
        config["gate_image_mode"] = args.gate_image_mode
    if args.transcription_wire_schema != "strict":
        config["transcription_wire_schema"] = args.transcription_wire_schema
    if args.transport_concurrency == P003_TRANSPORT_CONCURRENCY:
        config["transport_concurrency"] = 3
    if args.preset == "gated_ordinal":
        config["assembly_method"] = "gated_generate"
        config.update(gate_packet=args.gate_packet, gate_instructions=args.gate_instructions)
        if args.gate_image_edge is not None:
            config["gate_image_edge"] = args.gate_image_edge
    if args.preset in {"hybrid", "vision_regions"}:
        config.update(
            processor=args.preset, generation_tokens=16384, jpeg_quality=90,
            normalize_rotation=False, rotation_mode="preserve", native_table_orientation="logical",
        )
    if args.preset == "p003_regions":
        config.update(
            processor="p003_regions", generation_tokens=16384, jpeg_quality=90,
            normalize_rotation=False, rotation_mode="preserve",
            region_proposal_arm=args.region_proposal_arm, candidate_cap=32,
            proposal_edge=1536, gate_image_edge=512, gate_enabled=not args.ungated_regions,
            layout_detector="yolo" if args.region_proposal_arm in ("yolo", "yolo_fixed2") else "none",
            conflict_policy=args.region_conflict_policy,
        )
    return config


def main() -> None:
    """Run one predeclared fresh arm; shared locked policy enforces spend/deadline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preset", choices=PRESETS, required=True)
    parser.add_argument(
        "--model", choices=(*DECISION_MODELS, "convaiinnovations/laya", "convaiinnovations/laya-free"),
        default="perplexity/pplx-decider-v1.1-27b",
    )
    parser.add_argument("--generation-model", choices=CHAT_MODELS, default="anthropic/claude-haiku-5.5")
    parser.add_argument(
        "--generation-provider", help="Exact serving provider; disable fallbacks and require schema support",
    )
    parser.add_argument(
        "--transcription-representation", choices=("legacy", "matrix_strict", "atomic_cells"), default="legacy",
    )
    parser.add_argument("--transcription-wire-schema", choices=("strict", "simple"), default="strict")
    parser.add_argument("--image-edge", type=int, choices=(0, 128, 256, 400, 512, 768, 1024, 1200), default=512)
    parser.add_argument("--ocr-dpi", type=int, choices=(150, 300), default=300)
    parser.add_argument("--ocr-edge", type=int, choices=(0, 1536, 2048, 3072), default=0,
                        help="Use the existing fixed longest-edge OCR treatment; zero keeps explicit DPI")
    parser.add_argument("--gate-row-evidence", action="store_true")
    parser.add_argument("--text-gate", action="store_true", help="Omit gate pixels; keep generation image unchanged")
    parser.add_argument("--gate-provider", choices=("openrouter", "vercel"), default="openrouter")
    parser.add_argument(
        "--gate-packet", choices=("legacy", "fullwords", "compact", "sample64", "image_only", "lineflow"),
        default="legacy",
    )
    parser.add_argument(
        "--gate-instructions",
        choices=("legacy", "region", "visual_schema", "recall_first", "skeptical", "local_relations"), default="legacy",
    )
    parser.add_argument("--gate-image-mode", choices=("rgb", "grayscale8", "rgb_palette16"), default="rgb")
    parser.add_argument("--gate-image-edge", type=int, choices=(128, 256, 400, 512, 768, 1024))
    parser.add_argument(
        "--region-proposal-arm", choices=("tracks_whole", "tracks_fixed2", "yolo", "yolo_fixed2"),
        default="tracks_whole",
    )
    parser.add_argument(
        "--region-conflict-policy",
        choices=("table_probability_then_proposal_order_nonoverlap", "small_area_then_probability"),
        default="table_probability_then_proposal_order_nonoverlap",
    )
    parser.add_argument("--ungated-regions", action="store_true")
    parser.add_argument("--transport-concurrency", type=int, choices=(1, 3), default=1)
    parser.add_argument("--repeat-index", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--order-seed", type=int, default=20261010)
    args = parser.parse_args()
    if args.preset == "hybrid" and args.image_edge != HYBRID_EDGE:
        parser.error("The matched hybrid uses fixed 1024 px crops")
    if args.preset == "p003_regions" and args.image_edge != HYBRID_EDGE:
        parser.error("Source proposal treatments use fixed 1024 px transcription crops")
    if args.ungated_regions and (args.preset != "p003_regions" or args.region_proposal_arm != "yolo"):
        parser.error("Only the source-proposal YOLO control may disable its gate")
    if args.transcription_representation != "legacy" and args.preset not in {"vision_regions", "hybrid"}:
        parser.error("Nonlegacy transcription representations require vision_regions or hybrid")
    if args.transcription_wire_schema != "strict" and args.preset != "vision_regions":
        parser.error("Simple transcription wire schema requires vision_regions")
    if args.transport_concurrency == P003_TRANSPORT_CONCURRENCY and args.gate_provider != "openrouter":
        parser.error("Transport concurrency three requires OpenRouter")
    if args.gate_image_mode != "rgb" and (
        args.preset != "gated_ordinal" or args.text_gate or args.gate_provider != "openrouter"
    ):
        parser.error("NonRGB gate encoding requires gated_ordinal OpenRouter with pixels")
    if args.gate_instructions not in ("legacy", "region") and (
        args.preset != "gated_ordinal" or args.gate_provider != "openrouter"
    ):
        parser.error("Semantic gate variants require gated_ordinal OpenRouter")
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    report = pipeline_run.run(guard_path(args.manifest), guard_path(args.output), configuration(args))
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
