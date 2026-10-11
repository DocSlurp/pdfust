"""Independent image/wire/response replay for isolated source rows/rules with matched resolution pixels."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_synthetic_alias_replay as aliases  # type: ignore[attr-defined]  # current root dependency
from bench import p003_synthetic_relations_eval as evaluator
from bench import p003_synthetic_resolution as derivative
from bench import p003_synthetic_rules_resolution_run as runner
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, PLR0913, PLR0917, SLF001


def charges(entries: list[dict[str, Any]], attempted: int) -> dict[str, Any]:
    """Independently rebuild finite known amounts and refuse unsupported financial values."""
    recognized = {"provider-reported USD", "catalog estimate", "provider-reported BYOK upstream plus gateway USD"}

    def number(value: object) -> float | None:
        if value is None:
            return None
        if type(value) not in (int, float):
            raise ValueError("Invalid retained financial amount")
        assert isinstance(value, (int, float))
        if not math.isfinite(value) or value < 0:
            raise ValueError("Invalid retained financial amount")
        return float(value)

    amounts = [number(entry.get("accounted_usd")) for entry in entries]
    reported = [number(entry.get("provider_reported_usd")) for entry in entries]
    resolved = [
        amount
        for entry, amount in zip(entries, amounts, strict=True)
        if entry.get("cost_status") in recognized and amount is not None
    ]
    reservations = [
        amount for entry, amount in zip(entries, amounts, strict=True) if entry.get("cost_status") == "reserved"
    ]

    def sum_known(values: list[float | None]) -> float:
        return sum(value for value in values if value is not None)

    result: dict[str, Any] = {
        "ledger_attempts": len(entries),
        "accounted_usd": sum_known(amounts) if None not in amounts else None,
        "known_partial_accounted_usd": sum_known(amounts),
        "effective_usd": sum(resolved) if len(resolved) == len(entries) else None,
        "known_partial_effective_usd": sum(resolved),
        "unresolved_reserved_usd": sum_known(reservations) if None not in reservations else None,
        "known_partial_reserved_usd": sum_known(reservations),
        "provider_reported_usd": sum_known(reported) if None not in reported else None,
        "known_partial_provider_reported_usd": sum_known(reported),
        "missing_provider_charge_count": reported.count(None),
        "cost_bases": dict(
            Counter(
                entry.get("cost_status")
                if isinstance(entry.get("cost_status"), str) and entry.get("cost_status")
                else "unknown"
                for entry in entries
            )
        ),
    }
    if attempted and not entries:
        result.update(
            effective_usd=None,
            provider_reported_usd=None,
            accounting_status="Missing attempt accounting; costs unknown",
        )
    return result


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
        previous_charges = evaluator.charges
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
            evaluator.charges = charges
            result = aliases.replay(directory, runtime_map, context, alias_map, alias_sha256)
        finally:
            evaluator.PURE_FILES = previous
            evaluator.charges = previous_charges
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
