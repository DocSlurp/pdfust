"""CPU-only construction and validation of frozen-generation P003 gate plans."""

# ruff: noqa: ANN401, PLR2004, S101, PLR0913, PLR0917, EM101, TRY003
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any, cast

from bench import p003_gate_run as gate
from bench.p003_gate_image import EDGES, MODES

IMAGE_MODELS = (
    ("pplx", "perplexity/pplx-decider-v1.1-27b"),
    ("luna", "openai/gpt-6-luna-decisions"),
    ("clef", "cloudflare/clef"),
    ("clefomni", "cloudflare/clef-omni"),
)
TEXT_MODELS = (
    *IMAGE_MODELS,
    ("jev", "typesafe/jev-1.13"),
    ("d1", "liquid/d1"),
    ("tev", "togethercomputer/tev1-4b-experimental"),
    ("solar", "upstage/solar-decide"),
    ("solarflash", "upstage/solar-decide-flash"),
    ("mercury", "inception/mercury-decide"),
    ("microsoft", "microsoft/microsoft-decision-1"),
    ("drex", "nace-ai/drex-v1.5"),
)


def parse_arguments(arguments: list[str]) -> Any:
    """Execute only the actual CLI's parser construction, never its runner."""
    function = ast.parse(inspect.getsource(gate.main)).body[0]
    assert isinstance(function, ast.FunctionDef)
    nodes = []
    for node in function.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "args" for target in node.targets
        ):
            break
        nodes.append(node)
    else:
        raise ValueError("Actual parser boundary missing; refuse execution")
    namespace = dict(vars(gate))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<actual-gate-cli-parser>", "exec"), namespace)  # noqa: S102
    return namespace["parser"].parse_args(arguments)


def validate_arm(arm: dict[str, Any], output: Path) -> dict[str, Any]:
    """Validate actual parser and pre-output treatment guards without authentication or I/O."""
    args = parse_arguments(
        [
            *arm["arguments"],
            "--output",
            str(output),
            "--run-hosted",
            "--transport-concurrency",
            "3",
        ]
    )
    config = {
        key: value
        for key, value in vars(args).items()
        if key
        not in (
            "baseline",
            "trusted_code",
            "output",
            "text_gate",
        )
    }
    config["gate_image"] = not args.text_gate
    function = ast.parse(inspect.getsource(gate.run)).body[0]
    assert isinstance(function, ast.FunctionDef)
    nodes = []
    recording = False
    for node in function.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "defaults" for target in node.targets
        ):
            recording = True
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "mkdir"
        ):
            break
        if recording:
            nodes.append(node)
    else:
        raise ValueError("Actual pre-output guard boundary missing; refuse execution")
    if not recording:
        raise ValueError("Actual treatment defaults missing; refuse execution")
    namespace = dict(vars(gate))
    namespace.update(config=config, output=output, original_frozen={"config": {"source_order": "original"}})
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<actual-gate-treatment-guards>", "exec"), namespace)  # noqa: S102
    return cast("dict[str, Any]", namespace["config"])


def plans(baseline: Path, trust: Path) -> dict[str, list[dict[str, Any]]]:
    """Declare matched image factorial and a small staged prompt screen."""

    def arm(
        alias: str,
        model: str,
        edge: int = 512,
        mode: str = "rgb",
        packet: str = "compact",
        rubric: str = "region",
        *,
        image: bool = True,
    ) -> dict[str, Any]:
        name = f"gate-{alias}-{edge if image else 0}-{mode}-{packet}-{rubric}-r0-c3"
        arguments = [
            "--baseline",
            str(baseline),
            "--trusted-code",
            str(trust),
            "--model",
            model,
            "--gate-image-edge",
            str(edge),
            "--gate-image-mode",
            mode,
            "--gate-packet",
            packet,
            "--gate-instructions",
            rubric,
        ]
        if not image:
            arguments.append("--text-gate")
        return {"name": name, "kind": "gate", "arguments": arguments}

    image_arms = [arm(alias, model, edge, mode) for alias, model in IMAGE_MODELS for edge in EDGES for mode in MODES]
    # Core text controls plus paired image rubric treatments. RGB512/region image
    # controls are already present in the factorial and must be reused, not rerun.
    core = [arm(alias, model, image=False) for alias, model in TEXT_MODELS]
    core += [
        arm(alias, model, rubric=rubric)
        for alias, model in IMAGE_MODELS
        for rubric in ("visual_schema", "recall_first")
    ]
    # Prespecified follow-up limits coverage to two representative context sizes.
    followup = [
        arm(alias, model, packet=packet, image=False)
        for alias, model in (IMAGE_MODELS[0], IMAGE_MODELS[2])
        for packet in ("lineflow", "fullwords")
    ]
    followup += [
        arm(alias, model, rubric=rubric)
        for alias, model in (IMAGE_MODELS[0], IMAGE_MODELS[2])
        for rubric in ("skeptical", "local_relations")
    ]
    result = {"image-a": image_arms[:36], "image-b": image_arms[36:], "prompt-core": core, "prompt-followup": followup}
    for queue in result.values():
        assert len(queue) <= 64
        for item in queue:
            validate_arm(item, Path("/nonexistent-p003-plan-output") / item["name"])
    return result


def token_audit(status_path: Path) -> dict[str, Any]:
    """Inspect only named completed queue arms and their recorded fresh calls."""
    import json  # noqa: PLC0415
    from hashlib import sha256  # noqa: PLC0415

    status = json.loads(status_path.read_text())
    observations = []
    reports = {}
    attempts = []
    for arm in status["arms"]:
        directory = status_path.parent / arm["name"]
        report_path = directory / "report.json"
        report_bytes = report_path.read_bytes()
        reports[str(report_path)] = sha256(report_bytes).hexdigest()
        report = json.loads(report_bytes)
        accounting = arm.get("incremental_accounting", {})
        attempts.append(
            {
                "arm": arm["name"],
                "ledger_attempts": accounting.get("ledger_attempts"),
                "entries": len(accounting.get("entries", [])),
                "unresolved_reserved_usd": accounting.get("unresolved_reserved_usd"),
            }
        )
        for page in report["results"]:
            for field in ("ranking_calls", "repair_calls"):
                for call in page.get(field, []):
                    if field == "ranking_calls":
                        name = f"{page['id']}-selector-{call['crop_index']}-request.json"
                    else:
                        name = f"{page['id']}-{call['region_id']}-boundary-{call['batch_index']}-request.json"
                    path = directory / name
                    body_bytes = path.read_bytes()
                    body = json.loads(body_bytes)
                    state = body["state"]
                    if isinstance(state, str):
                        text, images = state, 0
                    else:
                        text = "\n".join(part for part in state if isinstance(part, str))
                        images = sum(isinstance(part, dict) and "image_url" in part for part in state)
                    observations.append(
                        {
                            "arm": arm["name"],
                            "model": body["model"],
                            "kind": field,
                            "request_file": str(path),
                            "request_file_sha256": sha256(body_bytes).hexdigest(),
                            "state_utf8_bytes": len(text.encode()),
                            "image_count": images,
                            "question_count": len(body["questions"]),
                            "reported_usage": call.get("usage", {}),
                            "provider_elapsed_ms": call.get("entry", {}).get("elapsed_ms"),
                        }
                    )
    return {
        "status_file": str(status_path),
        "status_sha256": sha256(status_path.read_bytes()).hexdigest(),
        "report_sha256": reports,
        "observations": observations,
        "attempt_inventory": attempts,
        "scope": (
            "Fresh ranking/repair calls only; historical generation excluded. State bytes exclude images/questions."
        ),
        "interpretation": "Reported input tokens do not prove provider retained all state; no inferred token counts.",
    }
