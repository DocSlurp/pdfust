"""Isolated process-local adapter for new synthetic crop resolutions; root-only hosting."""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_synthetic_relations_eval as evaluator
from bench import p003_synthetic_relations_run as legacy
from bench import p003_synthetic_resolution as derivative
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, PLR0913, PLR0917, PLR2004, SLF001, ANN401, TC003, PLW0603, C901
CODE_FILES = (
    *legacy.CODE_FILES,
    "p003_synthetic_resolution.py",
    "p003_synthetic_resolution_run.py",
    "p003_synthetic_resolution_eval.py",
    "p003_synthetic_relations_eval.py",
    "p003_synthetic_alias_replay.py",
)
_ACTIVE = False


@contextmanager
def adapter(source: Path, source_map: Path, images: Path, image_map: Path) -> Iterator[dict[str, Any]]:
    """Patch only this standalone process; every original function is restored on exit."""
    global _ACTIVE
    if _ACTIVE:
        raise ValueError("Nested resolution adapters are forbidden")
    if derivative.evidence.EDGES != (128, 512):
        raise ValueError("Unrelated process-local edge patch is active")
    source, source_map, images, image_map = [guard_path(p) for p in (source, source_map, images, image_map)]
    context = evaluator.source_context(source, source_map)
    inventory = derivative.authenticate_images(images, image_map, context)
    original = {name: getattr(legacy, name) for name in ("configuration", "rebuild_request", "prepare", "CODE_FILES")}
    pool_hash = sha((images / "frozen.json").read_bytes())

    def configuration(
        model: str,
        *,
        mode: str = "text_geometry",
        image_edge: int = 0,
        viewport: str = "crop",
        transport_concurrency: int = 3,
    ) -> dict[str, Any]:
        if (
            model not in derivative.MODELS
            or mode != "text_geometry"
            or image_edge not in derivative.EDGES
            or viewport != "crop"
            or transport_concurrency != 3
        ):
            raise ValueError("Five explicit image models/new crop edges/text geometry/transport concurrency 3 only")
        result = original["configuration"](
            model, mode=mode, image_edge=image_edge, viewport=viewport, transport_concurrency=transport_concurrency
        )
        result["resolution_derivative"] = {
            "version": derivative.VERSION,
            "image_pool_sha256": pool_hash,
            "controls_not_repurchased": [128, 512],
        }
        return result

    def rebuild_request(
        pool: Path, record: dict[str, Any], config: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if guard_path(pool).resolve() != source.resolve():
            raise ValueError("Exact original source pool required for derivative replay")
        matches = [i for i in inventory[record["id"]]["images"] if i["edge"] == config["image_edge"]]
        if len(matches) != 1 or matches[0]["status"] != "ready":
            raise ValueError("Selected resolution image refused; entire arm stops before client")
        item = deepcopy(matches[0])
        raw = legacy._path(images, item["path"]).read_bytes()
        body = derivative.request(record, config["model"], item, raw)
        return body, item

    def prepare(pool: Path, trusted_code: Path, output: Path, config: dict[str, Any]) -> dict[str, Any]:
        """Freeze original all 24 source/request serialization plus explicit derived pixel provenance."""
        result = original["prepare"](pool, trusted_code, output, config)
        copied = output / "resolution-source"
        copied.mkdir()
        receipt = {}
        frozen = evaluator.load(images / "frozen.json")
        names = [
            "frozen.json",
            "images.json",
            *["code/" + name for name in frozen["code_sha256"]],
            *frozen["image_sha256"],
        ]
        for name in names:
            target = copied / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(images / name, target)
            receipt[name] = sha(target.read_bytes())
        shutil.copyfile(image_map, copied / "trusted-code.json")
        receipt["trusted-code.json"] = sha(image_map.read_bytes())
        supplement = {
            "version": derivative.VERSION,
            "image_pool_sha256": pool_hash,
            "image_map_sha256": sha(image_map.read_bytes()),
            "artifacts": receipt,
            "source_frozen_sha256": context["frozen_sha256"],
            "gold_read_or_copied": False,
        }
        write_json(output / "resolution-input.json", supplement)
        result["frozen"]["resolution_input_sha256"] = sha((output / "resolution-input.json").read_bytes())
        write_json(output / "frozen.json", result["frozen"])
        return result

    _ACTIVE = True
    with derivative.extended_edges():
        try:
            legacy.configuration = configuration
            legacy.rebuild_request = rebuild_request
            legacy.prepare = prepare
            legacy.CODE_FILES = CODE_FILES
            yield {"context": context, "inventory": inventory, "configuration": configuration}
        finally:
            for name, value in original.items():
                setattr(legacy, name, value)
            _ACTIVE = False


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
    """Freeze all 24 requests/images before any client; reuse strict parser and actual accounting."""
    with adapter(source, source_map, images, image_map):
        if run_hosted:
            return legacy.run(
                source,
                source_map,
                output,
                model=model,
                mode="text_geometry",
                image_edge=edge,
                viewport="crop",
                transport_concurrency=3,
                run_hosted=True,
                client_factory=client_factory,
                entries_reader=entries_reader,
            )
        config = legacy.configuration(
            model, mode="text_geometry", image_edge=edge, viewport="crop", transport_concurrency=3
        )
        config["run_id"] = output.name
        return legacy.prepare(source, source_map, output, config)


def main() -> None:
    """Prepare by default; explicit hosted mode retains the root shared ledger and circuit."""
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
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
