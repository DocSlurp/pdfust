"""Offline exact-body replay of retained ownership decisions after composition repair.

Root supplies independent historical/current code maps. No request can reach a
provider, and original run outputs/errors remain immutable archived provenance.
"""

# ruff: noqa: ANN401, SLF001, EM101, TRY003, PLR2004
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_topology_run as runner
from bench.p003_boundary_run import _identifier
from bench.silver import guard_path, sha, write_json


def _bytes(body: dict[str, Any]) -> bytes:
    return json.dumps(body, separators=(",", ":"), allow_nan=False).encode()


class Transcript:
    """An isolated immutable body/response lookup, with no ledger or credentials."""

    def __init__(self, directory: Path, new_run_id: str) -> None:
        """Pin replay to a single independently authenticated original run."""
        self.directory, self.run_id = directory, new_run_id
        self.used: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return a retained response only when exact serialized body bytes match."""
        parts = kwargs["tag"].split("/")
        if len(parts) != 6 or parts[:2] != ["P003", self.run_id] or parts[4] not in {"row", "cell"}:
            raise ValueError("Unknown transcript identity")
        page, crop, stage, number = map(_identifier, parts[2:])
        stem = f"{page}-{crop}-{stage}-{number}"
        expected = runner.candidate._read(self.directory / f"{stem}-request.json")
        if runner.ownership._dump(body) != runner.ownership._dump(expected):
            raise ValueError("Transcript provider body bytes differ; reuse refused")
        response = runner.candidate._read(self.directory / f"{stem}-response.json")
        if not {"result", "entry"} <= set(response) or not isinstance(response.get("result"), dict):
            raise ValueError("Missing complete retained provider decision; no rescue")
        if response["entry"].get("request_sha256") != sha(_bytes(body)):
            raise ValueError("Original admitted provider serialization differs from current body bytes")
        self.used.append(
            {
                "stem": stem,
                "body_sha256": sha(_bytes(body)),
                "response_sha256": sha((self.directory / f"{stem}-response.json").read_bytes()),
                "original_entry": deepcopy(response["entry"]),
            }
        )
        return deepcopy(response)


def authenticate(directory: Path, trusted: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Check historical run code bytes against independently supplied operator map."""
    frozen = runner.candidate._read(directory / "frozen.json")
    report = runner.candidate._read(directory / "report.json")
    if frozen["config"].get("processor") != "p003_topology_source" or frozen["config"] != report["config"]:
        raise ValueError("Transcript must retain the original ownership run config")
    if any(frozen["config"].get(k) for k in ("geometry_only", "transcript_replay", "boundary_words")):
        raise ValueError("Correction replay supports original strict image ownership only")
    if not frozen["config"].get("run_hosted"):
        raise ValueError("Original transcript must be a hosted ownership treatment")
    hashes = frozen["code_sha256"]
    if not {"p003_topology_run.py", "p003_topology_ownership.py"} <= set(hashes):
        raise ValueError("Transcript lacks authenticated ownership code")
    for name, digest in hashes.items():
        _identifier(name)
        if trusted.get(name) != digest or sha(guard_path(directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Historical transcript code is not independently authenticated")
    for row in report["results"]:
        if runner.candidate._read(directory / f"{_identifier(row['id'])}-result.json") != row:
            raise ValueError("Historical result differs from original report")
    return frozen, report


def _check_partition(old: dict[str, Any], new: dict[str, Any]) -> None:
    """Allow only residual word-list order correction, retaining exact assignments."""
    if {k: v for k, v in old.items() if k != "regions"} != {k: v for k, v in new.items() if k != "regions"}:
        raise ValueError("Replay complete source plan differs")
    if len(old["regions"]) != len(new["regions"]):
        raise ValueError("Replay crop partition differs")
    for a, b in zip(old["regions"], new["regions"], strict=True):
        if {k: v for k, v in a.items() if k != "source"} != {k: v for k, v in b.items() if k != "source"}:
            raise ValueError("Replay source ownership assignments differ")
        if a["source"]["page_size"] != b["source"]["page_size"] or {w["id"]: w for w in a["source"]["words"]} != {
            w["id"]: w for w in b["source"]["words"]
        }:
            raise ValueError("Replay literal source words differ")


def run(
    directory: Path,
    trusted: dict[str, str],
    source_trusted: dict[str, str],
    topology_trusted: dict[str, str],
    output: Path,
) -> dict[str, Any]:
    """Authenticate and recompose identical retained choices in a fresh treatment."""
    directory, output = map(guard_path, (directory, output))
    frozen, original = authenticate(directory, trusted)
    config = {**frozen["config"], "run_hosted": False, "prepare_only": False, "transcript_replay": True}
    source, topology = directory / "source-baseline", directory / "topology-baseline"
    _sf, sr = runner.authenticate_source(source, source_trusted)
    tf, tr, _ = runner.candidate.authenticate(
        topology, topology_trusted, reviewed_parser_sha256=tuple(config.get("reviewed_parser_sha256", []))
    )
    sm, tm = ({r["id"]: r for r in report["results"]} for report in (sr, tr))
    preflight = Transcript(directory, _identifier(output.name))
    for old in original["results"]:
        if old.get("topology_regions"):
            work = runner.prepare_page(sm[old["id"]], tm[old["id"]], topology, tf["config"], config)
            _check_partition(runner.candidate._read(directory / f"{old['id']}-ownership-plan.json"), work["plan"])
            for crop in work["crops"]:
                old_packet = runner.candidate._read(directory / f"{old['id']}-{crop['id']}-snapshot.json")
                if old_packet != json.loads(crop["snapshot"].packet_json):
                    raise ValueError("Replay frozen source/topology/image snapshot differs")
                row_results = [
                    preflight.request(body, tag=f"P003/{output.name}/{old['id']}/{crop['id']}/row/{i}")["result"]
                    for i, body in enumerate(crop["row_bodies"])
                ]
                rows = runner.ownership.collect(crop["snapshot"], crop["row_bodies"], row_results)
                cell_bodies = runner.ownership.batches(
                    crop["snapshot"], config["model"], crop["url"], rows=rows, max_questions=config["max_questions"]
                )
                cell_results = [
                    preflight.request(body, tag=f"P003/{output.name}/{old['id']}/{crop['id']}/cell/{i}")["result"]
                    for i, body in enumerate(cell_bodies)
                ]
                runner.ownership.assemble(crop["snapshot"], crop["row_bodies"], row_results, cell_bodies, cell_results)
    transcript = Transcript(directory, _identifier(output.name))
    report = runner.run(source, topology, source_trusted, topology_trusted, output, config, transcript)
    archive = output / "original-ownership-run"
    archive.mkdir()
    inventory = {}
    for path in sorted(directory.iterdir()):
        if path.is_file():
            data = guard_path(path).read_bytes()
            (archive / path.name).write_bytes(data)
            inventory[path.name] = sha(data)
    (archive / "code").mkdir()
    for name in frozen["code_sha256"]:
        data = guard_path(directory / "code" / name).read_bytes()
        (archive / "code" / name).write_bytes(data)
        inventory["code/" + name] = sha(data)
    receipt = {
        "original_directory": str(directory),
        "copied_directory": "original-ownership-run",
        "file_sha256": inventory,
        "original_code_trusted_map": trusted,
        "original_report": original,
        "scope": "Offline identical-body ownership decisions; only residual composition order corrected",
        "retained_responses": transcript.used,
        "new_api_calls": 0,
        "original_failures_preserved": True,
    }
    current = runner.candidate._read(output / "frozen.json")
    current["transcript_origin"] = receipt
    write_json(output / "frozen.json", current)
    report["transcript_origin"] = receipt
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Require independent original/source/topology maps and a fresh local output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-run", type=Path, required=True)
    parser.add_argument("--original-trusted-code", type=Path, required=True)
    parser.add_argument("--source-trusted-code", type=Path, required=True)
    parser.add_argument("--topology-trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(
        args.original_run,
        runner.candidate._read(args.original_trusted_code),
        runner.candidate._read(args.source_trusted_code),
        runner.candidate._read(args.topology_trusted_code),
        args.output,
    )
    print(
        json.dumps(
            {
                "status_counts": report["incremental_ownership"]["status_counts"],
                "new_api_calls": 0,
                "retained_responses": len(report["transcript_origin"]["retained_responses"]),
            }
        )
    )


if __name__ == "__main__":
    main()
