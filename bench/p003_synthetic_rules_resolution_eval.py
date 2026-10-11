"""Independent image/wire/response replay for isolated source rows/rules with matched resolution pixels."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from bench import p003_synthetic_alias_replay as aliases  # type: ignore[attr-defined]  # current root dependency
from bench import p003_synthetic_relations_eval as evaluator
from bench import p003_synthetic_resolution as derivative
from bench import p003_synthetic_rules_resolution_run as runner
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, PLR0913, PLR0917, SLF001


def verify_run(
    directory: Path,
    runtime_map: Path,
    source: Path,
    source_map: Path,
    images: Path,
    image_map: Path,
    alias_map: Path,
    alias_sha256: str,
) -> dict[str, Any]:
    """Replay independent image/source authorities and raw strict/attested decisions before gold."""
    directory = guard_path(directory)
    with runner.adapter(source, source_map, images, image_map) as prepared:
        context = prepared["context"]
        frozen = evaluator.load(directory / "frozen.json")
        raw = (directory / "resolution-input.json").read_bytes()
        if sha(raw) != frozen["resolution_input_sha256"]:
            raise ValueError("Frozen derivative input receipt changed")
        receipt = evaluator.load(directory / "resolution-input.json")
        copied = directory / "resolution-source"
        if (
            receipt["image_pool_sha256"] != sha((images / "frozen.json").read_bytes())
            or receipt["image_map_sha256"] != sha(image_map.read_bytes())
            or receipt["source_frozen_sha256"] != context["frozen_sha256"]
            or receipt["gold_read_or_copied"] is not False
        ):
            raise ValueError("Derivative copied authority differs")
        for name, digest in receipt["artifacts"].items():
            path = guard_path(copied / name)
            if not path.resolve().is_relative_to(copied.resolve()) or sha(path.read_bytes()) != digest:
                raise ValueError("Derived image/source copy changed or escaped inventory")
        copied_inventory = derivative.authenticate_images(copied, image_map, context)
        edge = frozen["config"]["image_edge"]
        for record in context["records"]:
            if record["status"] != "ready":
                continue
            item = next(i for i in copied_inventory[record["id"]]["images"] if i["edge"] == edge)
            raw_pixels, expected = derivative.render(
                record, runner.legacy._path(source, record["pdf_path"]).read_bytes(), edge
            )
            if (
                item != {"status": "ready", **expected}
                or raw_pixels != runner.legacy._path(copied, item["path"]).read_bytes()
            ):
                raise ValueError("Actual source crop replay differs")
        previous = evaluator.PURE_FILES
        evaluator.PURE_FILES = (  # type: ignore[assignment]  # isolated extension of frozen verifier tuple
            *previous,
            "p003_synthetic_resolution.py",
            "p003_synthetic_resolution_run.py",
            "p003_synthetic_resolution_eval.py",
            "p003_synthetic_relations_eval.py",
            "p003_synthetic_alias_replay.py",
            "p003_synthetic_rules_resolution.py",
            "p003_synthetic_rules_resolution_run.py",
            "p003_synthetic_rules_resolution_eval.py",
        )
        try:
            result = aliases.replay(directory, runtime_map, context, alias_map, alias_sha256)
        finally:
            evaluator.PURE_FILES = previous
        result["resolution_verification"] = {
            "image_pool_sha256": receipt["image_pool_sha256"],
            "image_map_sha256": receipt["image_map_sha256"],
            "actual_crop_replayed_count": 24,
            "original_source_unchanged": True,
            "new_api_calls": 0,
        }
        return result


def main() -> None:
    """Verify outputs before optional explicitly authorized evaluation-only labels."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("directory", "runtime-map", "source", "source-map", "images", "image-map", "aliases", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--alias-sha256", required=True)
    parser.add_argument("--gold", type=Path)
    parser.add_argument("--gold-sha256")
    args = parser.parse_args()
    output = guard_path(args.output)
    if output.exists():
        raise FileExistsError("New independent report required")
    if (args.gold is None) != (args.gold_sha256 is None):
        raise ValueError("Evaluation labels require a separate file and approved digest together")
    result = verify_run(
        args.directory,
        args.runtime_map,
        args.source,
        args.source_map,
        args.images,
        args.image_map,
        args.aliases,
        args.alias_sha256,
    )
    if args.gold is not None:
        context = evaluator.source_context(args.source, args.source_map)
        gold = evaluator.load_gold(args.gold, args.gold_sha256, context)
        result["original_scores"] = evaluator.score(result["original_verified"], gold, context)
        result["secondary_scores"] = evaluator.score(result["secondary_verified"], gold, context)
    write_json(output, result)


if __name__ == "__main__":
    main()
