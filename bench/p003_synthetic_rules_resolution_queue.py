"""Root-only isolated queue adapter for 10 predeclared synthetic resolution arms."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

from bench import p003_synthetic_rules_resolution_plan as plan
from bench import p003_synthetic_rules_resolution_run as runner
from bench import p003_synthetic_shared_queue as queue_contract
from bench.decision_hosted import ROOT
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, ANN401, PLC0415, PLR2004, S603
KIND = "synthetic_rules_resolution"
SEED = 20261010
SCOPE = "one relationship question per synthetic page; no complete extraction or quality claim"
CUTOFF = queue_contract.CUTOFF
QUEUE_SHA256 = queue_contract.QUEUE_SHA256


def runtime_authority(root: Path) -> dict[str, str]:
    """Require all 31 runtime files and this driver to equal Git HEAD before launch."""
    root = guard_path(root)
    git = shutil.which("git")
    if git is None or len(runner.CODE_FILES) != 31:
        raise ValueError("Git and the exact 31-file runtime inventory required")
    result = {}
    for name in (*runner.CODE_FILES, Path(__file__).name, "p003_synthetic_rules_resolution_plan.py"):
        data = (root / "bench" / name).read_bytes()
        approved = subprocess.check_output([git, "show", "HEAD:bench/" + name], cwd=root)
        if data != approved:
            raise ValueError("Runtime/driver differs from Git HEAD: " + name)
        if name in runner.CODE_FILES:
            result[name] = sha(approved)
    queue = (root / "bench/p003_parallel.py").read_bytes()
    if sha(queue) != QUEUE_SHA256:
        raise ValueError("Queue differs from the explicitly approved contract")
    return result


def queue_plan(source: Path, source_map: Path, images: Path, image_map: Path) -> list[dict[str, Any]]:
    """Convert the exact fixed model/edge inventory into core's literal argument schema."""
    return [
        {"name": arm["name"], "kind": KIND, "arguments": arm["args"]}
        for arm in plan.arms(source, source_map, images, image_map)
    ]


def validate_arguments(arm: dict[str, Any]) -> int:
    """Reject duplicate/injected options and admit only five models and new crop edges."""
    values = arm.get("arguments")
    if arm.get("kind") != KIND or not isinstance(values, list) or len(values) != 12:
        raise ValueError("Exact standalone resolution arguments required")
    options = dict(zip(values[::2], values[1::2], strict=True))
    if set(options) != {"--source", "--source-map", "--images", "--image-map", "--model", "--image-edge"}:
        raise ValueError("Exact source/image authorities, model and edge required")
    if options["--model"] not in runner.derivative.MODELS:
        raise ValueError("Fixed five-model inventory required")
    edge = int(options["--image-edge"])
    if edge not in runner.derivative.EDGES:
        raise ValueError("Only new predeclared edges admitted")
    for flag in ("--source", "--source-map", "--images", "--image-map"):
        guard_path(Path(options[flag]))
    return edge


@contextmanager
def adapt(core: Any, root: Path, authority: dict[str, str]) -> Iterator[None]:
    """Restore every patched namespace; use three existing global transports and heavy slots."""
    if (
        sha(Path(core.__file__).read_bytes()) != QUEUE_SHA256
        or core.MAX_CONCURRENT != 3
        or core.P003_PAID_CUTOFF != CUTOFF
    ):
        raise ValueError("Approved core bytes, three slots and exact cutoff required")
    original = {
        name: getattr(core, name)
        for name in ("MODULES", "QUESTION_SCOPES", "command_for", "validate_plan", "next_launch_index")
    }

    def command_for(arm: dict[str, Any], manifest: Path | None, output: Path) -> list[str]:
        validate_arguments(arm)
        if manifest is not None:
            raise ValueError("Resolution queue has no PDF extraction manifest")
        path = output.parent / "trusted-code" / (arm["name"] + ".json")
        if path.exists():
            if runtime_authority(root) != authority:
                raise ValueError("Runtime changed after preparation")
            write_json(path, authority)
        return [
            sys.executable,
            "-m",
            "bench.p003_synthetic_rules_resolution_run",
            "--output",
            str(output.resolve()),
            "--run-hosted",
            *arm["arguments"],
        ]

    def validate_plan(rows: Any, seed: int) -> list[dict[str, Any]]:
        ordered = original["validate_plan"](rows, seed)
        # Stable resolution bands preserve the core's seeded model shuffle within each edge.
        return sorted(ordered, key=validate_arguments)

    def next_launch_index(ordered: list[dict[str, Any]], active: list[dict[str, Any]], limit: int) -> int | None:
        def normalized(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return [{**row, "kind": "synthetic_relations"} for row in rows]

        return original["next_launch_index"](normalized(ordered), normalized(active), limit)

    core.MODULES = {**core.MODULES, KIND: "bench.p003_synthetic_rules_resolution_run"}
    core.QUESTION_SCOPES = {**core.QUESTION_SCOPES, KIND: SCOPE}
    core.command_for, core.validate_plan, core.next_launch_index = command_for, validate_plan, next_launch_index
    try:
        yield
    finally:
        for name, value in original.items():
            setattr(core, name, value)


def replay_preflight(preflight: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Reconstruct all 240 actual native bodies from source/image authorities without gold."""
    preflight = guard_path(preflight)
    frozen = json.loads((preflight / "frozen.json").read_bytes())
    rows = json.loads((preflight / "plan.json").read_bytes())
    if sha((preflight / "plan.json").read_bytes()) != frozen["plan_sha256"] or frozen["arm_count"] != 10:
        raise ValueError("Complete unchanged 10-arm preflight required")
    options = dict(zip(rows[0]["args"][::2], rows[0]["args"][1::2], strict=True))
    source, source_map, images, image_map = [
        Path(options[f]) for f in ("--source", "--source-map", "--images", "--image-map")
    ]
    if rows != plan.arms(source, source_map, images, image_map) or frozen["prepared_requests"] is not True:
        raise ValueError("Exact predeclared all-request plan required")
    receipts = {r["name"]: r for r in frozen["arm_receipts"]}
    if len(receipts) != 10 or frozen["intended_questions"] != 240:
        raise ValueError("All 240 questions required")
    with runner.adapter(source, source_map, images, image_map) as prepared:
        if (
            frozen["source_frozen_sha256"] != prepared["context"]["frozen_sha256"]
            or frozen["image_map_sha256"] != sha(image_map.read_bytes())
            or frozen["image_pool_sha256"] != sha((images / "frozen.json").read_bytes())
        ):
            raise ValueError("Preflight source/image authority changed")
        for arm in rows:
            directory = preflight / arm["name"]
            receipt = receipts[arm["name"]]
            if sha((directory / "frozen.json").read_bytes()) != receipt["frozen_sha256"] or receipt["ready"] != 24:
                raise ValueError("Frozen arm missing or refused questions")
            config = runner.legacy.configuration(arm["model"], image_edge=arm["image_edge"])
            config["run_id"] = arm["name"]
            for index, record in enumerate(prepared["context"]["records"]):
                body, _ = runner.legacy.rebuild_request(source, record, config)
                actual = (directory / f"question-{index}-wire-encoded.json").read_bytes()
                expected = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
                if actual != expected:
                    raise ValueError("Complete native wire replay differs")
    return frozen, queue_plan(source, source_map, images, image_map)


def prepare(preflight: Path, output: Path, *, root: Path = ROOT) -> dict[str, Any]:
    """Freeze launch commands and exact Git authority without constructing a client."""
    from bench import p003_parallel

    core: Any = p003_parallel

    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New queue preparation directory required")
    authority = runtime_authority(root)
    inputs, rows = replay_preflight(preflight)
    with adapt(core, root, authority):
        ordered = core.validate_plan(rows, SEED)
        commands = [core.command_for(arm, None, output / "future-hosted" / arm["name"]) for arm in ordered]
    output.mkdir(parents=True)
    result = {
        "preflight": str(guard_path(preflight)),
        "preflight_sha256": sha((preflight / "frozen.json").read_bytes()),
        "runtime_code_sha256": authority,
        "driver_sha256": sha(Path(__file__).read_bytes()),
        "plan": rows,
        "frozen_order": ordered,
        "commands": commands,
        "seed": SEED,
        "cutoff": CUTOFF,
        "arm_count": 10,
        "question_count": 240,
        "max_active_arms": 3,
        "max_heavy_arms": 3,
        "global_transport_slots": 3,
        "new_api_calls": 0,
        "gold_read": False,
        "image_pool_sha256": inputs["image_pool_sha256"],
        "scope": SCOPE,
    }
    write_json(output / "frozen.json", result)
    return result


def launch(prepared: Path, directory: Path, *, root: Path = ROOT) -> dict[str, Any]:
    """Root-only exact prepared launch; no retries, fallback, or extension of the cutoff."""
    from bench import p003_parallel

    core: Any = p003_parallel

    frozen = json.loads((guard_path(prepared) / "frozen.json").read_bytes())
    authority = runtime_authority(root)
    if (
        frozen["runtime_code_sha256"] != authority
        or frozen["driver_sha256"] != sha(Path(__file__).read_bytes())
        or frozen["cutoff"] != CUTOFF
        or frozen["seed"] != SEED
    ):
        raise ValueError("Prepared runtime, driver, seed or cutoff changed")
    preflight = Path(frozen["preflight"])
    if sha((preflight / "frozen.json").read_bytes()) != frozen["preflight_sha256"]:
        raise ValueError("Source-only request preflight changed")
    _, rows = replay_preflight(preflight)
    if rows != frozen["plan"]:
        raise ValueError("Full model/edge plan changed")
    with adapt(core, root, authority):
        ordered = core.validate_plan(rows, SEED)
        commands = [
            core.command_for(arm, None, guard_path(prepared) / "future-hosted" / arm["name"]) for arm in ordered
        ]
        if ordered != frozen["frozen_order"] or commands != frozen["commands"]:
            raise ValueError("Seeded breadth execution order or commands changed")
        return core.run_queue(
            rows, None, guard_path(directory), seed=SEED, cutoff=CUTOFF, root=root, max_parallel_arms=3
        )


def main() -> None:
    """Prepare by default; only root explicitly launches the new paid queue."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--exclusive-paid-work", action="store_true")
    args = parser.parse_args()
    if args.run_hosted:
        if not args.exclusive_paid_work or args.directory is None:
            raise ValueError("Root launch requires exclusive paid work and a new directory")
        launch(args.prepared, args.directory, root=args.root)
    else:
        if args.preflight is None:
            raise ValueError("Source-only request preflight required")
        result = prepare(args.preflight, args.prepared, root=args.root)
        print(
            json.dumps(
                {"arm_count": result["arm_count"], "question_count": result["question_count"], "hosted_calls": 0}
            )
        )


if __name__ == "__main__":
    main()
