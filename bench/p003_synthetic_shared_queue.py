"""Standalone root-only shared-context queue adapter; active core files stay unchanged."""

# ruff: noqa: ANN401, C901, EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

import argparse
import json
import resource
import shutil
import subprocess
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

from bench import p003_synthetic_relations_multi as protocol
from bench import p003_synthetic_relations_multi_run as runner
from bench import p003_synthetic_relations_run as single
from bench.decision_hosted import ROOT
from bench.research_policy import P003_PAID_CUTOFF
from bench.silver import guard_path, sha, write_json

KIND = "synthetic_shared_context"
SEED = 20261010
QUEUE_SHA256 = "8b384404ad54c7a854f323cd567fa8c5e28eab285f85e51dcec53b46bfc464e6"
CUTOFF = 1791684720.0  # 2026-10-11 02:12 UTC, no extension.
SCOPE = "cross-page shared-context relationship questions; no isolation, server batching or complete extraction claim"


def generate_plan(pool: Path, source_map: Path) -> list[dict[str, Any]]:
    """Declare all 14 models by two sizes and two evidence modes, before deterministic shuffling."""
    pool, source_map = guard_path(pool), guard_path(source_map)
    if len(single.DECISION_MODELS) != 14:
        raise ValueError("The predeclared 14-model inventory changed")
    return [
        {
            "name": f"shared-m{index:02d}-q{size}-{mode.replace('_', '-')}",
            "kind": KIND,
            "arguments": [
                "--input",
                str(pool),
                "--trusted-code",
                str(source_map),
                "--model",
                model,
                "--group-size",
                str(size),
                "--evidence",
                mode,
            ],
        }
        for index, model in enumerate(single.DECISION_MODELS)
        for size in protocol.SIZES
        for mode in single.evidence.MODES
    ]


def runtime_authority(root: Path) -> dict[str, str]:
    """Compare exactly 25 current runtime files with independently read Git HEAD blobs."""
    root = guard_path(root)
    git = shutil.which("git")
    if git is None or len(runner.CODE_FILES) != 25:
        raise ValueError("Git and the exact 25-file runtime inventory required")
    authority = {}
    for name in runner.CODE_FILES:
        data = (root / "bench" / name).read_bytes()
        original = subprocess.check_output([git, "show", "HEAD:bench/" + name], cwd=root)  # noqa: S603
        if data != original:
            raise ValueError("Dirty runtime file differs from Git HEAD: " + name)
        authority[name] = sha(original)
    queue = (root / "bench/p003_parallel.py").read_bytes()
    if (
        sha(queue) != QUEUE_SHA256
        or subprocess.check_output([git, "show", "HEAD:bench/p003_parallel.py"], cwd=root) != queue  # noqa: S603
    ):
        raise ValueError("Current queue differs from the explicitly approved adapter contract")
    return authority


def validate_arguments(arm: dict[str, Any], pool: Path, source_map: Path) -> dict[str, Any]:
    """Refuse injected flags, duplicate options and a changed source/model/mode inventory."""
    values = arm["arguments"]
    if arm.get("kind") != KIND or len(values) != 10:
        raise ValueError("Only exact standalone shared-context arm arguments admitted")
    parsed = dict(zip(values[::2], values[1::2], strict=True))
    if set(parsed) != {"--input", "--trusted-code", "--model", "--group-size", "--evidence"}:
        raise ValueError("Exact source/model/group/evidence flags required")
    if guard_path(Path(parsed["--input"])) != guard_path(pool) or guard_path(
        Path(parsed["--trusted-code"])
    ) != guard_path(source_map):
        raise ValueError("Source authority must stay identical across the entire queue")
    return runner.configuration(
        parsed["--model"], size=int(parsed["--group-size"]), mode=parsed["--evidence"], transport_concurrency=3
    )


@contextmanager
def adapt(core: Any, root: Path, authority: dict[str, str]) -> Iterator[None]:
    """Patch only this standalone process's queue namespace, restoring it on every exit."""
    if (
        sha(Path(core.__file__ or "").read_bytes()) != QUEUE_SHA256
        or core.MAX_CONCURRENT != 3
        or not hasattr(core, "QUESTION_SCOPES")
        or not hasattr(core, "next_launch_index")
        or core.P003_PAID_CUTOFF != CUTOFF
        or P003_PAID_CUTOFF != CUTOFF
    ):
        raise ValueError("Explicit current queue function bytes and cutoff required")
    originals = {
        name: getattr(core, name)
        for name in (
            "MODULES",
            "QUESTION_SCOPES",
            "command_for",
            "next_launch_index",
            "report_counts",
            "summarize_rates",
        )
    }
    base_command, base_next, base_counts, base_summary = [
        originals[k] for k in ("command_for", "next_launch_index", "report_counts", "summarize_rates")
    ]

    def command_for(arm: dict[str, Any], manifest: Path | None, output: Path) -> list[str]:
        if arm.get("kind") != KIND:
            raise ValueError("This standalone adapter admits only the new shared-context kind")
        map_path = output.parent / "trusted-code" / (arm["name"] + ".json")
        if map_path.exists():
            if runtime_authority(root) != authority:
                raise ValueError("Runtime code changed after frozen plan preparation")
            # Core created this fresh arm's map moments ago; replace it before Popen with exact Git authority.
            write_json(map_path, authority)
        return base_command(arm, manifest, output)

    def next_launch_index(ordered: list[dict[str, Any]], active: list[dict[str, Any]], limit: int) -> int | None:
        # Reuse the original three-heavy scheduler; only classify this new kind equivalently.
        normalized = [
            {**a, "kind": "synthetic_relations" if a.get("kind") == KIND else a.get("kind", "pipeline")}
            for a in ordered
        ]
        normalized_active = [
            {**a, "kind": "synthetic_relations" if a.get("kind") == KIND else a.get("kind", "pipeline")} for a in active
        ]
        return base_next(normalized, normalized_active, limit)

    def report_counts(status: dict[str, Any], report: dict[str, Any]) -> None:
        base_counts(status, report)
        status.update(
            intended_shared_requests=report["group_count"],
            attempted_shared_requests=report["attempted_group_count"],
            shared_request_status_counts=report["group_status_counts"],
            charge_scope="Once per shared request, never once per member question",
        )

    def summarize_rates(statuses: list[dict[str, Any]], wall: float, not_started: list[str]) -> dict[str, Any]:
        summary = base_summary(statuses, wall, not_started)
        arms = [s for s in statuses if s["kind"] == KIND]
        complete = (
            bool(arms)
            and all("attempted_shared_requests" in s and not s.get("report_metrics_error") for s in arms)
            and not not_started
        )
        count = sum(s.get("attempted_shared_requests", 0) for s in arms)
        summary["by_kind"][KIND].update(
            attempted_shared_requests_known=count,
            attempted_shared_requests_per_minute=count / wall * 60 if complete and wall else None,
            charge_scope="Shared request counted once",
        )
        return summary

    core.MODULES = {**core.MODULES, KIND: "bench.p003_synthetic_relations_multi_run"}
    core.QUESTION_SCOPES = {**core.QUESTION_SCOPES, KIND: SCOPE}
    core.command_for, core.next_launch_index, core.report_counts, core.summarize_rates = (
        command_for,
        next_launch_index,
        report_counts,
        summarize_rates,
    )
    try:
        yield
    finally:
        for name, value in originals.items():
            setattr(core, name, value)


def prepare(pool: Path, source_map: Path, output: Path, *, root: Path = ROOT, core: Any = None) -> dict[str, Any]:
    """Freeze all 56 plans and 252 complete requests without constructing clients or reading gold."""
    began, cpu = time.perf_counter(), time.process_time()
    if core is None:
        from bench import p003_parallel as core
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New queue preparation directory required")
    authority = runtime_authority(root)
    for name in (
        "p003_synthetic_relations_multi.py",
        "p003_synthetic_relations_multi_run.py",
        "p003_synthetic_relations_run.py",
        "p003_synthetic_relations.py",
        "feature_cases.py",
        "pipeline_row_evidence.py",
        "pipeline_regions.py",
        "silver.py",
    ):
        if sha(Path(runner.__file__).with_name(name).read_bytes()) != authority[name]:
            raise ValueError("Current executed pure preparation helper differs from runtime authority")
    source_trust = json.loads(guard_path(source_map).read_bytes())
    source_frozen, records = single.authenticate(pool, source_trust)
    plan = generate_plan(pool, source_map)
    with adapt(core, root, authority):
        ordered = core.validate_plan(plan, SEED)
        commands = [core.command_for(a, None, output / "future-hosted-queue" / a["name"]) for a in ordered]
    prepared = []
    output.mkdir(parents=True)
    (output / "requests").mkdir()
    (output / "trusted-code").mkdir()
    for arm, command in zip(ordered, commands, strict=True):
        cfg = validate_arguments(arm, pool, source_map)
        hashes = []
        for index, group in enumerate(protocol.groups(records, cfg["question_group_size"])):
            body = protocol.request(group, cfg)
            encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
            if len(encoded) > protocol.MAX_BODY_BYTES:
                raise ValueError("A complete planned request exceeds capacity; no truncated substitute")
            name = f"{arm['name']}-group-{index}.json"
            (output / "requests" / name).write_bytes(encoded)
            hashes.append(
                {
                    "path": "requests/" + name,
                    "sha256": sha(encoded),
                    "bytes": len(encoded),
                    "case_ids": [r["id"] for r in group],
                    "omitted_word_count": 0,
                }
            )
        prepared.append({"name": arm["name"], "config": cfg, "command": command, "requests": hashes})
    write_json(output / "plan.json", plan)
    write_json(output / "frozen-order.json", ordered)
    write_json(output / "trusted-code/runtime25.json", authority)
    receipt = {
        "prepared_at_unix": time.time(),
        "source_pool": str(guard_path(pool)),
        "source_map": str(guard_path(source_map)),
        "source_frozen_sha256": sha((pool / "frozen.json").read_bytes()),
        "source_map_sha256": sha(source_map.read_bytes()),
        "source_record_count": len(source_frozen["records"]),
        "plan": plan,
        "frozen_order": ordered,
        "seed": SEED,
        "prepared_arms": prepared,
        "runtime_code_sha256": authority,
        "driver_sha256": sha(Path(__file__).read_bytes()),
        "queue_sha256": QUEUE_SHA256,
        "arm_count": 56,
        "request_count": 252,
        "question_count_per_arm": 24,
        "cutoff": CUTOFF,
        "max_active_arms": 6,
        "max_heavy_arms": 3,
        "transport_slots": 3,
        "gold_read": False,
        "hosted_calls": 0,
        "scope": SCOPE,
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Preparation-only parent; unsampled lifetime RSS includes imports",
        },
    }
    write_json(output / "frozen.json", receipt)
    return receipt


def launch(prepared: Path, directory: Path, *, root: Path = ROOT, core: Any = None) -> dict[str, Any]:
    """Root-only launch of the exact prepared 56-arm plan, with owned-process cleanup and strict cutoff."""
    if core is None:
        from bench import p003_parallel as core
    frozen = json.loads((guard_path(prepared) / "frozen.json").read_bytes())
    authority = runtime_authority(root)
    if (
        frozen["runtime_code_sha256"] != authority
        or frozen["driver_sha256"] != sha(Path(__file__).read_bytes())
        or frozen["cutoff"] != CUTOFF
    ):
        raise ValueError("Prepared runtime/driver authority or cutoff changed")
    pool, source_map = Path(frozen["source_pool"]), Path(frozen["source_map"])
    if frozen["plan"] != generate_plan(pool, source_map) or frozen["arm_count"] != 56 or frozen["request_count"] != 252:
        raise ValueError("Full predeclared plan differs")
    if (
        sha(source_map.read_bytes()) != frozen["source_map_sha256"]
        or sha((pool / "frozen.json").read_bytes()) != frozen["source_frozen_sha256"]
    ):
        raise ValueError("Source authority changed after preparation")
    _source, records = single.authenticate(pool, json.loads(source_map.read_bytes()))
    if len(frozen["prepared_arms"]) != 56:
        raise ValueError("Complete preflight request inventory required")
    by_name = {a["name"]: a for a in frozen["prepared_arms"]}
    if len(by_name) != 56:
        raise ValueError("Unique prepared arms required")
    for arm in frozen["plan"]:
        cfg = validate_arguments(arm, pool, source_map)
        entry = by_name[arm["name"]]
        if entry["config"] != cfg:
            raise ValueError("Prepared arm configuration differs")
        expected = []
        for index, group in enumerate(protocol.groups(records, cfg["question_group_size"])):
            body = protocol.request(group, cfg)
            encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
            relative = f"requests/{arm['name']}-group-{index}.json"
            if (guard_path(prepared) / relative).read_bytes() != encoded:
                raise ValueError("Complete preflight literal wire replay differs")
            expected.append(
                {
                    "path": relative,
                    "sha256": sha(encoded),
                    "bytes": len(encoded),
                    "case_ids": [r["id"] for r in group],
                    "omitted_word_count": 0,
                }
            )
        if entry["requests"] != expected:
            raise ValueError("Prepared source/request receipts differ")
    with adapt(core, root, authority):
        if core.validate_plan(frozen["plan"], SEED) != frozen["frozen_order"]:
            raise ValueError("Deterministic execution order changed")
        return core.run_queue(
            frozen["plan"], None, guard_path(directory), seed=SEED, cutoff=CUTOFF, root=root, max_parallel_arms=6
        )


def main() -> None:
    """Use prepare-only by default; paid launch requires root's explicit exclusivity acknowledgment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--trusted-code", type=Path)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--exclusive-paid-work", action="store_true")
    args = parser.parse_args()
    if args.run_hosted:
        if args.prepare_only or not args.exclusive_paid_work or args.directory is None:
            raise ValueError("Hosted launch requires exclusive paid work and a new directory, not prepare-only")
        result = launch(args.prepared, args.directory, root=args.root)
        print(json.dumps({"arm_status_counts": dict(Counter(r["status"] for r in result["arms"])), "cutoff": CUTOFF}))
    else:
        if args.input is None or args.trusted_code is None:
            raise ValueError("Preparation requires explicit source pool and source authority")
        result = prepare(args.input, args.trusted_code, args.prepared, root=args.root)
        print(
            json.dumps({"arm_count": result["arm_count"], "request_count": result["request_count"], "hosted_calls": 0})
        )


if __name__ == "__main__":
    main()
