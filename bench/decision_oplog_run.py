"""Freeze and optionally execute a separate bounded DEV operation-choice pilot."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, NoReturn

from bench.decision_context_cases import context_cases
from bench.decision_hosted import (
    ARTIFACTS,
    RESERVATION,
    ROOT,
    DecisionClient,
    accounted_cost,
    checkpoint,
    exclusive_lock,
    probability,
)
from bench.decision_image_matrix import VariantCache
from bench.decision_oplog import Atom, Session, State, from_context, make_request, proposals, validate
from bench.reprice_model_rates import request_cost
from bench.silver import rss_bytes

MODELS = ("openai/gpt-6-luna-decisions", "perplexity/pplx-decider-v1.1-27b")
CASE_INDICES = (0, 11, 22, 3, 14, 25, 6, 17, 28, 9)
MAX_BODY_BYTES = 750_000
MAX_PILOT_STEPS = 8
MAX_CALLS = len(CASE_INDICES) * len(MODELS) * MAX_PILOT_STEPS
SUM_TOLERANCE = 0.015000001
WAVE_LIMIT = 0.50
TAG_PREFIX = "oplog/"
DEFAULT_DIRECTORY = ARTIFACTS / "oplog-pilot-512"
CODE_PATHS = tuple(
    ROOT / "bench" / name
    for name in (
        "decision_oplog_run.py",
        "decision_oplog.py",
        "decision_context_cases.py",
        "decision_image_matrix.py",
        "decision_images.py",
        "decision_hosted.py",
        "reprice_model_rates.py",
    )
)


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


def _checked(path: Path) -> Path:
    for candidate in (path.absolute(), path.resolve()):
        if {"heldout-silver", "silver-heldout-v1"}.intersection(candidate.parts):
            _fail("Protected held-out paths are excluded")
    return path


def encode(body: dict[str, Any]) -> bytes:
    """Match the shared client's canonical body bytes for exact request identity."""
    return json.dumps(body, separators=(",", ":")).encode()


def prepare(
    directory: Path,
    *,
    image_edge: int = 512,
    max_steps: int = 8,
    models: tuple[str, ...] = MODELS,
    prices_path: Path | None = None,
) -> dict[str, Any]:
    """Freeze case, source, rendering, policy and code identities without credentials."""
    _checked(directory)
    if type(image_edge) is not int or image_edge not in {128, 512, 1200}:
        _fail("Image edge must be 128, 512 or 1200")
    if type(max_steps) is not int or not 1 <= max_steps <= MAX_PILOT_STEPS:
        _fail("Pilot step cap must be from one to eight")
    if not models or len(models) != len(set(models)) or not set(models) <= set(MODELS):
        _fail("Pilot models must be distinct admitted Luna/Perplexity IDs")
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "manifest.json"
    if manifest_path.exists():
        retained = json.loads(manifest_path.read_text())
        if (retained["image_edge"], retained["max_steps"], retained["models"]) != (image_edge, max_steps, list(models)):
            _fail("Frozen pilot differs; select a new directory")
        verify(directory, retained)
        return retained
    start, cpu = time.perf_counter(), time.process_time()
    all_cases = context_cases()
    cache = VariantCache(directory / "images")
    selected = []
    for index in CASE_INDICES:
        case = all_cases[index]
        if case.get("split") != "DEV":
            _fail("Pilot requires explicitly DEV cases")
        state = from_context(case)
        variant = cache.make_variant(case["pdf_bytes"], None, edge=image_edge, mode="rgb8", blank=False)
        data = variant["data"]
        image_name = f"page-{index:02d}.png"
        (directory / image_name).write_bytes(data)
        selected.append(
            {
                "index": index,
                "source_sha256": hashlib.sha256(case["pdf_bytes"]).hexdigest(),
                "initial_state_sha256": state.sha256,
                "image_file": image_name,
                "image_sha256": hashlib.sha256(data).hexdigest(),
                "image": {key: value for key, value in variant.items() if key != "data"},
            }
        )
    prices = {}
    price_source: dict[str, Any] = {}
    if prices_path is not None:
        price_source = json.loads(_checked(prices_path).read_text())
        prices = price_source.get("prices", {})
    manifest = {
        "schema": 1,
        "task": "DEV-operation-choice",
        "models": list(models),
        "image_edge": image_edge,
        "image_mode": "rgb8",
        "image_scope": "page",
        "max_steps": max_steps,
        "policy": "model-menu",
        "known_headers": True,
        "cohort_policy": (
            "Prespecified rotating vocabulary indices; one case per ten correlated templates, no quality selection"
        ),
        "cases": selected,
        "prices": prices,
        "pricing_provenance": {key: value for key, value in price_source.items() if key != "prices"},
        "code_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in CODE_PATHS},
        "prepared_at": time.time(),
        "max_call_ceiling": len(selected) * len(models) * max_steps,
        "preparation": {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "scope": "serial local preparation; process lifetime VmHWM; no sampling",
        },
        "candidate_oracle": "unmeasured: a valid operation menu is not proof that the target is reachable",
    }
    checkpoint(manifest_path, manifest)
    return manifest


def verify(directory: Path, manifest: dict[str, Any]) -> None:  # noqa: C901 - explicit frozen admissions.
    """Refuse changed code, inputs, images, identities and exceeded admissions."""
    _checked(directory)
    if manifest.get("policy") != "model-menu" or manifest.get("task") != "DEV-operation-choice":
        _fail("Unexpected pilot policy or task")
    if (
        type(manifest["max_steps"]) is not int
        or not 1 <= manifest["max_steps"] <= MAX_PILOT_STEPS
        or not manifest["models"]
        or len(manifest["models"]) != len(set(manifest["models"]))
        or not set(manifest["models"]) <= set(MODELS)
        or type(manifest["image_edge"]) is not int
        or manifest["image_edge"] not in {128, 512, 1200}
        or manifest.get("image_scope") != "page"
        or manifest.get("image_mode") != "rgb8"
        or manifest.get("known_headers") is not True
    ):
        _fail("Frozen pilot admission changed")
    if tuple(row["index"] for row in manifest["cases"]) != CASE_INDICES:
        _fail("Prespecified cohort changed")
    if set(manifest["code_sha256"]) != {str(path) for path in CODE_PATHS}:
        _fail("Frozen code inventory changed")
    for path, digest in manifest["code_sha256"].items():
        if hashlib.sha256(_checked(Path(path)).read_bytes()).hexdigest() != digest:
            _fail("Frozen implementation changed before calls")
    cases = context_cases()
    for row in manifest["cases"]:
        case = cases[row["index"]]
        if hashlib.sha256(case["pdf_bytes"]).hexdigest() != row["source_sha256"]:
            _fail("Frozen PDF changed")
        if from_context(case).sha256 != row["initial_state_sha256"]:
            _fail("Frozen initial state changed")
        if Path(row["image_file"]).name != row["image_file"]:
            _fail("Image path escapes pilot directory")
        if hashlib.sha256(_checked(directory / row["image_file"]).read_bytes()).hexdigest() != row["image_sha256"]:
            _fail("Frozen image changed")


def parse_choice(result: dict[str, Any], options: set[str]) -> dict[str, Any]:
    """Require the declared Choice ID and its complete finite distribution."""
    answers = result.get("answers")
    if not isinstance(answers, dict) or set(answers) != {"q0"}:
        _fail("Response must contain exactly q0")
    answer = answers["q0"]
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        _fail("Response is not a typed Choice")
    raw = answer.get("probabilities")
    if not isinstance(raw, dict) or set(raw) != options:
        _fail("Choice distribution does not match the operation menu")
    distribution = {key: probability(value) for key, value in raw.items()}
    total = sum(distribution.values())
    choice = answer.get("choice")
    if abs(total - 1) > SUM_TOLERANCE or not isinstance(choice, str) or choice not in options:
        _fail("Choice probabilities or identity are invalid")
    if distribution[choice] != max(distribution.values()):
        _fail("Choice is not a maximum-probability operation")
    return {"choice": choice, "probabilities": distribution, "normalization_delta": total - 1}


def score(case: dict[str, Any], state: State) -> dict[str, Any]:
    """Score authored source grouping and mappable slots, separately from conservation."""
    if case.get("split") != "DEV":
        _fail("Scoring requires DEV labels")
    validate(state)
    aliases = {word["id"]: f"w{i}" for i, word in enumerate(case["evidence"]["words"])}
    if {atom.id for atom in state.atoms} != set(aliases.values()):
        _fail("Scored state inventory differs from authored source evidence")

    def target(choice: str) -> tuple[set[frozenset[str]], dict[str, tuple[int, int]], set[str]]:
        cells = case["evidence"]["assemblies"][choice]["cells"]
        groups: set[frozenset[str]] = set()
        slots = {}
        owned: set[str] = set()
        for cell in cells:
            ids = frozenset(aliases[source] for source in cell["source_ids"])
            if not ids:
                continue
            groups.add(ids)
            owned.update(ids)
            if cell["id"] in {"description_header", "value_header"}:
                coordinate = (0, int(cell["id"] == "value_header"))
            else:
                row, column = cell["id"].removeprefix("r").split("c")
                coordinate = (int(row) + 1, int(column))
            slots.update(dict.fromkeys(ids, coordinate))
        return groups, slots, set(aliases.values()) - owned

    observed = {frozenset(cell.source_ids) for cell in state.cells}
    actual_slots = {source: (cell.row, cell.column) for cell in state.cells for source in cell.source_ids}
    targets = {choice: target(choice) for choice in ("A", "B")}
    selected = next(
        (
            choice
            for choice, (groups, _, unassigned) in targets.items()
            if observed == groups and set(state.unassigned) == unassigned
        ),
        "other",
    )
    expected = case["gold"]["choice"]
    if expected == "unresolved":
        headers = {frozenset(cell.source_ids) for cell in from_context(case).cells}
        exact = observed == headers and set(state.unassigned) == set(from_context(case).unassigned)
        return {
            "expected": expected,
            "selected": "unresolved" if exact else selected,
            "source_group_exact": exact,
            "row_column_exact": None,
            "placement_scored_sources": 0,
            "placement_correct_sources": None,
            "pair_precision": None,
            "pair_recall": None,
            "conservation": True,
            "candidate_oracle": "unmeasured",
        }
    groups, positions, unresolved = targets[expected]

    def pairs(parts: set[frozenset[str]]) -> set[tuple[str, str]]:
        return {(left, right) for part in parts for left in part for right in part if left < right}

    actual_pairs, target_pairs = pairs(observed), pairs(groups)
    correct_pairs = len(actual_pairs & target_pairs)
    correct_positions = sum(actual_slots.get(source) == coordinate for source, coordinate in positions.items())
    return {
        "expected": expected,
        "selected": selected,
        "source_group_exact": observed == groups and set(state.unassigned) == unresolved,
        "row_column_exact": correct_positions == len(positions),
        "placement_scored_sources": len(positions),
        "placement_correct_sources": correct_positions,
        "pair_precision": correct_pairs / len(actual_pairs) if actual_pairs else None,
        "pair_recall": correct_pairs / len(target_pairs) if target_pairs else None,
        "conservation": True,
        "candidate_oracle": "unmeasured",
    }


def wave_admission(entries: list[dict[str, Any]]) -> None:
    """Persist the separate wave cap across directories, counting failed reservations."""
    retained = [entry for entry in entries if str(entry.get("tag", "")).startswith(TAG_PREFIX)]
    if (
        len(retained) >= MAX_CALLS
        or sum(accounted_cost(entry["accounted_usd"]) for entry in retained) + RESERVATION > WAVE_LIMIT
    ):
        message = "Operation pilot persistent wave cap exhausted"
        raise RuntimeError(message)


def _entries(client: Any) -> list[dict[str, Any]]:  # noqa: ANN401 - shared or mocked client.
    return json.loads(client.ledger.read_text())["requests"] if client.ledger.exists() else []


def run(directory: Path, manifest: dict[str, Any], *, client: Any = None) -> dict[str, Any]:  # noqa: ANN401
    """Execute explicitly invoked hosted work under the shared root lock, without retries."""
    verify(directory, manifest)
    result_path = directory / "results.json"
    if result_path.exists():
        return json.loads(result_path.read_text())
    client = DecisionClient() if client is None else client
    with exclusive_lock(client.ledger.parent / "run.lock"):
        if result_path.exists():
            return json.loads(result_path.read_text())
        return _run_locked(directory, manifest, client)


def _run_locked(directory: Path, manifest: dict[str, Any], client: Any) -> dict[str, Any]:  # noqa: ANN401, C901
    cases = context_cases()
    sessions = {
        (model, item["index"]): Session(from_context(cases[item["index"]]), manifest["max_steps"])
        for model in manifest["models"]
        for item in manifest["cases"]
    }
    report: dict[str, Any] = {
        "schema": 1,
        "status": "running",
        "calls": [],
        "sessions": [],
        "wave_limit_usd": WAVE_LIMIT,
        "candidate_oracle": "unmeasured",
    }
    result_path = directory / "results.json"
    checkpoint(result_path, report)
    stopped: set[str] = set()
    budget_exhausted = False
    for step in range(manifest["max_steps"]):
        for item in manifest["cases"]:
            for model in manifest["models"]:
                session = sessions[model, item["index"]]
                if session.stop_reason or model in stopped or budget_exhausted:
                    continue
                menu = proposals(session.state)
                data = _checked(directory / item["image_file"]).read_bytes()
                image = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
                region_ids = {word["id"] for word in cases[item["index"]]["evidence"]["words"]}
                neighborhood = tuple(
                    Atom(f"n{i}", word["text"], tuple(word["bbox"]))
                    for i, word in enumerate(cases[item["index"]]["source_words"])
                    if word["id"] not in region_ids
                )
                body = make_request(session.state, menu, model, image=image, neighborhood=neighborhood)
                encoded = encode(body)
                if len(encoded) > MAX_BODY_BYTES:
                    _fail("Adaptive operation body exceeds the shared image admission")
                digest = hashlib.sha256(encoded).hexdigest()
                filename = f"request-{digest}.json"
                (directory / filename).write_bytes(encoded)
                row: dict[str, Any] = {
                    "model": model,
                    "case_index": item["index"],
                    "step": step,
                    "before_state_sha256": session.state.sha256,
                    "request_sha256": digest,
                    "request_file": filename,
                    "status": "pending",
                    "menu": [asdict(op) for op in menu],
                }
                report["calls"].append(row)
                checkpoint(result_path, report)
                entries = _entries(client)
                known = next((entry for entry in entries if entry.get("request_sha256") == digest), None)
                try:
                    if known is not None and not known.get("response_file"):
                        message = "Previously failed identical operation request; no retry"
                        raise RuntimeError(message)  # noqa: TRY301
                    if known is None:
                        wave_admission(entries)
                    response = client.request(
                        body, tag=f"{TAG_PREFIX}{model}/{item['index']}/{step}", max_body_bytes=MAX_BODY_BYTES
                    )
                    row.update(
                        entry=response["entry"],
                        usage=response["result"].get("usage", {}),
                        replayed=response["replayed"],
                    )
                    row["cost"] = request_cost(response["entry"], row["usage"], manifest["prices"].get(model, {}))
                    row["http_elapsed_ms"] = response["entry"].get("elapsed_ms")
                    answer = parse_choice(response["result"], set(body["questions"]["q0"]["criteria"]))
                    session.choose(answer["choice"], menu)
                    row.update(
                        status="ok",
                        answer=answer,
                        after_state_sha256=session.state.sha256,
                        stop_reason=session.stop_reason,
                    )
                except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
                    row.update(status="failed", error=type(error).__name__)
                    retained = next(
                        (entry for entry in _entries(client) if entry.get("request_sha256") == digest), None
                    )
                    if retained is not None:
                        row.setdefault("entry", retained)
                        row.setdefault("usage", {})
                        row.setdefault("cost", request_cost(retained, row["usage"], manifest["prices"].get(model, {})))
                    if "persistent wave cap exhausted" in str(error):
                        budget_exhausted = True
                        row.update(status="unattempted", reason="persistent wave cap exhausted")
                    else:
                        stopped.add(model)
                        row["reason"] = "model stopped after failed call or invalid response; no retry"
                checkpoint(result_path, report)
    for (model, index), session in sessions.items():
        reason = session.stop_reason or (
            "model-failed" if model in stopped else "budget-exhausted" if budget_exhausted else "step-cap"
        )
        report["sessions"].append(
            {
                "model": model,
                "case_index": index,
                "stop_reason": reason,
                "final_state": asdict(session.state),
                "history": [asdict(entry) for entry in session.history],
                "score": score(cases[index], session.state),
            }
        )
    report.update(status="complete", budget_exhausted=budget_exhausted, stopped_models=sorted(stopped))
    checkpoint(result_path, report)
    return json.loads(result_path.read_text())


def main() -> None:
    """Prepare without credentials, run only on explicit flag, or read local reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--run-hosted", action="store_true")
    actions.add_argument("--report-only", action="store_true")
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--image-edge", type=int, choices=(128, 512, 1200), default=512)
    parser.add_argument("--max-steps", type=int, default=8)
    args = parser.parse_args()
    _checked(args.directory)
    if args.report_only:
        print(json.dumps(json.loads((args.directory / "results.json").read_text()), indent=2))
        return
    prices = ARTIFACTS / "langfuse/catalog-prices.json"
    manifest = prepare(
        args.directory,
        image_edge=args.image_edge,
        max_steps=args.max_steps,
        prices_path=prices if prices.exists() else None,
    )
    if args.run_hosted:
        result = run(args.directory, manifest)
        print(
            json.dumps(
                {"status": result["status"], "calls": len(result["calls"]), "sessions": result["sessions"]}, indent=2
            )
        )
    else:
        print(
            json.dumps(
                {"status": "prepared", "directory": str(args.directory), "max_calls": manifest["max_call_ceiling"]},
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
