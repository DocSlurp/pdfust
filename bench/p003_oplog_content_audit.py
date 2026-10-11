"""Source-first R002 replay and conditional body-content diagnostics."""

# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR0912, PLR2004, S603, S607, ANN401
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

VERSION = "p003-r002-body-content-v1"
INDICES = (0, 11, 22, 3, 14, 25, 6, 17, 28, 9)
POLICY = {
    "scope": "Conditional region body assembly; supplied headers and neighborhood excluded",
    "matrix": "Declared occupied body coordinates; preserve internal blank rows; trim trailing unused rows",
    "text": "Join retained atom text in exact cell source-ID order; no generated corrections",
    "partial": "All final states receive emitted-body diagnostics, including abstention and loop",
    "completion": "Only finished sessions can receive completed-content recovery; stops stay in intended denominator",
    "missing_annotation": (
        "No content comparison or imputed gold; retain source/group/stop metrics and explicit exclusion"
    ),
    "author_unresolved": "No unique content target; retain unresolved/group correctness and explicit exclusion",
    "targets": "Only original selected A/B assembly cells with strict rNcM IDs; no prediction-based slot repair",
    "oracle": "Unmeasured; no full-page or candidate-reachability credit",
}


def digest(data: bytes) -> str:
    """Hash exact retained bytes."""
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    """Read a guarded retained JSON object."""
    from bench.silver import guard_path

    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("JSON object required")
    return value


def state_from(raw: dict[str, Any]) -> Any:
    """Restore and validate immutable source ownership."""
    from bench.decision_oplog import Atom, Cell, State, validate

    state = State(
        tuple(Atom(a["id"], a["text"], tuple(a["bbox"])) for a in raw["atoms"]),
        tuple(
            Cell(c["id"], c["row"], c["column"], tuple(c["source_ids"]), tuple(c["bbox"]), c["role"])
            for c in raw["cells"]
        ),
        tuple(raw["unassigned"]),
        tuple(raw["deferred"]),
        tuple(raw["bounds"]),
        raw["rows"],
        raw["columns"],
        raw["finished"],
    )
    validate(state)
    return state


def body_table(state: Any, initial: Any) -> dict[str, Any] | None:
    """Conserve the source and exclude supplied headers by immutable source identity."""
    from bench.decision_oplog import validate

    validate(state)
    validate(initial)
    if state.atoms != initial.atoms or state.bounds != initial.bounds or state.columns != 2:
        raise ValueError("Original source, bounds and two columns required")
    headers = {c.id: c for c in initial.cells}
    if any(c.role != "header" or c.row != 0 for c in initial.cells):
        raise ValueError("Initial cells must be supplied row-zero headers")
    if {c.id: c for c in state.cells if c.role == "header"} != headers:
        raise ValueError("Supplied headers changed")
    header_ids = {i for c in initial.cells for i in c.source_ids}
    cells = [c for c in state.cells if c.role == "data"]
    if any(c.row < 1 or header_ids.intersection(c.source_ids) for c in cells):
        raise ValueError("Body cannot reuse supplied header source or row zero")
    if not cells:
        return None
    values = [["", ""] for _ in range(max(c.row for c in cells))]
    atoms = {a.id: a.text for a in state.atoms}
    for cell in cells:
        values[cell.row - 1][cell.column] = " ".join(atoms[i] for i in cell.source_ids)
    return {"row_count": len(values), "col_count": 2, "values": values, "spans": []}


def parse_choice(raw: dict[str, Any], options: set[str]) -> dict[str, Any]:
    """Independently enforce the historical finite distribution contract."""
    if not isinstance(raw.get("answers"), dict) or set(raw["answers"]) != {"q0"}:
        raise ValueError("Exactly q0 required")
    answer = raw["answers"]["q0"]
    if answer.get("type") != "choice" or set(answer.get("probabilities", {})) != options:
        raise ValueError("Exact Choice distribution required")
    probabilities = answer["probabilities"]
    if any(
        isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or not 0 <= v <= 1
        for v in probabilities.values()
    ):
        raise ValueError("Finite probability required")
    total = sum(probabilities.values())
    choice = answer.get("choice")
    if abs(total - 1) > 0.015000001 or choice not in options or probabilities[choice] != max(probabilities.values()):
        raise ValueError("Historical Choice contract differs")
    return {"choice": choice, "probabilities": probabilities, "normalization_delta": total - 1}


def prepare(directory: Path, output: Path) -> dict[str, Any]:
    """Freeze exact source/wire/output evidence without importing target generators."""
    from bench.decision_oplog import Atom, Session, make_request, proposals
    from bench.p003_render_reuse import Monitor
    from bench.silver import guard_path, write_json

    directory, output = guard_path(directory), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh output required")
    manifest = read_json(directory / "manifest.json")
    report = read_json(directory / "results.json")
    if tuple(c["index"] for c in manifest["cases"]) != INDICES or not manifest["known_headers"]:
        raise ValueError("Original fixed R002 cohort required")
    if report["status"] != "complete" or len(report["sessions"]) != 20 or len(report["calls"]) != 83:
        raise ValueError("Complete twenty-session/83-call pilot required")
    git_authority = {}
    for original, expected in manifest["code_sha256"].items():
        relative = "bench/" + Path(original).name
        revisions = subprocess.check_output(["git", "log", "--format=%H", "--", relative], text=True).splitlines()
        match = next(
            (
                rev
                for rev in revisions
                if digest(subprocess.check_output(["git", "show", f"{rev}:{relative}"])) == expected
            ),
            None,
        )
        if match is None:
            raise ValueError("Historical code is not authenticated by Git")
        git_authority[relative] = {"sha256": expected, "git_revision": match}
    core = Path(__file__).with_name("decision_oplog.py")
    if digest(core.read_bytes()) != git_authority["bench/decision_oplog.py"]["sha256"]:
        raise ValueError("Executed source helper differs from authenticated history")
    artifacts = {}

    def load(path: Path) -> bytes:
        data = guard_path(path).read_bytes()
        artifacts[str(path)] = digest(data)
        return data

    load(directory / "manifest.json")
    load(directory / "results.json")
    rows = []
    identities = {(m, i) for m in manifest["models"] for i in INDICES}
    if {(s["model"], s["case_index"]) for s in report["sessions"]} != identities:
        raise ValueError("Complete unique original identities required")
    resources = Monitor()
    with resources:
        for original in report["sessions"]:
            calls = [
                c
                for c in report["calls"]
                if (c["model"], c["case_index"]) == (original["model"], original["case_index"])
            ]
            if [c["step"] for c in calls] != list(range(len(calls))):
                raise ValueError("Call sequence differs")
            initial = state_from(original["history"][0]["before"] if original["history"] else original["final_state"])
            case = next(c for c in manifest["cases"] if c["index"] == original["case_index"])
            if initial.sha256 != case["initial_state_sha256"]:
                raise ValueError("Initial source snapshot differs")
            image_bytes = load(directory / case["image_file"])
            if digest(image_bytes) != case["image_sha256"]:
                raise ValueError("Retained pixels changed")
            session = Session(initial, max_steps=manifest["max_steps"])
            for call in calls:
                if call["status"] != "ok" or session.stop_reason is not None:
                    raise ValueError("Original call status/sequence differs")
                encoded = load(directory / call["request_file"])
                if digest(encoded) != call["request_sha256"]:
                    raise ValueError("Retained wire changed")
                wire = json.loads(encoded)
                visible = json.loads(wire["state"][0]["text"])
                neighborhood = tuple(Atom(a["id"], a["text"], tuple(a["bbox"])) for a in visible["source_neighborhood"])
                menu = proposals(session.state)
                rebuilt = make_request(
                    session.state,
                    menu,
                    original["model"],
                    image="data:image/png;base64," + base64.b64encode(image_bytes).decode(),
                    neighborhood=neighborhood,
                )
                if json.dumps(rebuilt, separators=(",", ":")).encode() != encoded:
                    raise ValueError("Native source/menu request does not reproduce")
                if (
                    json.loads(json.dumps([asdict(op) for op in menu])) != call["menu"]
                    or session.state.sha256 != call["before_state_sha256"]
                ):
                    raise ValueError("Retained operation menu differs")
                entry = call["entry"]
                if (
                    entry["requested_model"] != original["model"]
                    or entry["request_sha256"] != call["request_sha256"]
                    or entry["tag"] != f"oplog/{original['model']}/{original['case_index']}/{call['step']}"
                ):
                    raise ValueError("Receipt request attribution differs")
                name = entry["response_file"]
                if name != f"response-{entry['index']}.json":
                    raise ValueError("Only referenced raw receipt allowed")
                raw = json.loads(load(directory.parent / name))
                if raw["model"] != entry["served_model"]:
                    raise ValueError("Returned model differs from receipt")
                answer = parse_choice(raw, set(wire["questions"]["q0"]["criteria"]))
                if answer != call["answer"]:
                    raise ValueError("Retained parsed Choice differs")
                session.choose(answer["choice"], menu)
                if session.state.sha256 != call["after_state_sha256"] or session.stop_reason != call["stop_reason"]:
                    raise ValueError("Atomic state/stop replay differs")
            if (
                json.loads(json.dumps(asdict(session.state))) != original["final_state"]
                or json.loads(json.dumps([asdict(e) for e in session.history])) != original["history"]
                or session.stop_reason != original["stop_reason"]
            ):
                raise ValueError("Complete final state/history replay differs")
            rows.append(
                {
                    "model": original["model"],
                    "case_index": original["case_index"],
                    "stop_reason": original["stop_reason"],
                    "initial_state": asdict(initial),
                    "final_state": original["final_state"],
                    "body_table": body_table(session.state, initial),
                    "original_score": original["score"],
                    "call_count": len(calls),
                }
            )
    output.mkdir(parents=True)
    write_json(output / "source-output.json", {"records": rows})
    frozen = {
        "version": VERSION,
        "policy": POLICY,
        "directory": str(directory),
        "artifact_sha256": artifacts,
        "historical_git_authority": git_authority,
        "source_output_sha256": digest((output / "source-output.json").read_bytes()),
        "code_sha256": {
            n: digest(Path(__file__).with_name(n).read_bytes())
            for n in ("p003_oplog_content_audit.py", "decision_oplog.py")
        },
        "sessions": 20,
        "calls": 83,
        "new_api_calls": 0,
        "target_interpretation": False,
        "resources": resources.metrics(),
    }
    write_json(output / "frozen.json", frozen)
    return frozen


def main() -> None:
    """Prepare source-only evidence; target evaluation requires separate approval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.directory, args.output)


if __name__ == "__main__":
    main()
