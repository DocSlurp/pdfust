"""Isolated rows/rules plus matched RGB resolution processor; root-only hosting."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from bench import p003_synthetic_resolution_run as base
from bench import p003_synthetic_rules_resolution as derivative
from bench.silver import guard_path

# ruff: noqa: EM101, TRY003, PLR0913, PLR0917, ANN401, TC003, SLF001
legacy = base.legacy
CODE_FILES = (
    *base.CODE_FILES,
    "p003_synthetic_rules_resolution.py",
    "p003_synthetic_rules_resolution_run.py",
    "p003_synthetic_rules_resolution_eval.py",
)


@contextmanager
def adapter(source: Path, source_map: Path, images: Path, image_map: Path) -> Iterator[dict[str, Any]]:
    """Reuse authenticated pixels in this process while overriding only new packet/config seams."""
    with base.adapter(source, source_map, images, image_map) as prepared:
        original = {name: getattr(legacy, name) for name in ("configuration", "rebuild_request", "CODE_FILES")}

        def configuration(
            model: str,
            *,
            mode: str = "rows_rules",
            image_edge: int = 0,
            viewport: str = "crop",
            transport_concurrency: int = 3,
        ) -> dict[str, Any]:
            if mode != "rows_rules" or image_edge not in derivative.EDGES:
                raise ValueError("Complete rows/rules evidence and fixed 400/768 edges required")
            config = original["configuration"](
                model,
                mode="text_geometry",
                image_edge=image_edge,
                viewport=viewport,
                transport_concurrency=transport_concurrency,
            )
            config["mode"] = "rows_rules"
            config["rows_rules_resolution"] = {"version": derivative.VERSION, "pixel_control_mode": "text_geometry"}
            return config

        def rebuild_request(
            pool: Path, record: dict[str, Any], config: dict[str, Any]
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            _, item = original["rebuild_request"](pool, record, config)
            raw = legacy._path(guard_path(images), item["path"]).read_bytes()
            return derivative.request(record, config["model"], item, raw), item

        try:
            legacy.configuration = configuration
            legacy.rebuild_request = rebuild_request
            legacy.CODE_FILES = CODE_FILES
            yield prepared
        finally:
            for name, value in original.items():
                setattr(legacy, name, value)


def execute(
    source: Path,
    source_map: Path,
    images: Path,
    image_map: Path,
    output: Path,
    model: str,
    edge: int,
    *,
    run_hosted: bool = False,
    client_factory: Any = legacy.client_for,
    entries_reader: Any = legacy.read_entries,
) -> dict[str, Any]:
    """Freeze all 24 complete requests before any root client; retain original strict parsing."""
    with adapter(source, source_map, images, image_map):
        if run_hosted:
            return legacy.run(
                source,
                source_map,
                output,
                model=model,
                mode="rows_rules",
                image_edge=edge,
                viewport="crop",
                transport_concurrency=3,
                run_hosted=True,
                client_factory=client_factory,
                entries_reader=entries_reader,
            )
        config = legacy.configuration(model, image_edge=edge)
        config["run_id"] = output.name
        return legacy.prepare(source, source_map, output, config)


def main() -> None:
    """Prepare by default; only an explicit root launch constructs a hosted client."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "source-map", "images", "image-map", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--model", choices=derivative.MODELS, required=True)
    parser.add_argument("--image-edge", type=int, choices=derivative.EDGES, required=True)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    result = execute(
        args.source,
        args.source_map,
        args.images,
        args.image_map,
        args.output,
        args.model,
        args.image_edge,
        run_hosted=args.run_hosted,
    )
    print(
        json.dumps(
            {
                "prepared": not args.run_hosted,
                "question_count": 24,
                "hosted_calls": 0 if not args.run_hosted else result["attempted_question_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
