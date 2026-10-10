"""Independent replay rejects tampering in mocked incremental source ownership."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_gate_run as gate
from bench import p003_topology_run as runner
from bench.p003_gate_verification import verify_gate
from bench.p003_incremental_verification import verify_topology
from bench.silver import sha, write_json
from test_p003_gate_run import baseline, settings
from test_p003_topology_run import Client, archives, config


@pytest.mark.parametrize("prepare", [True, False])
def test_topology_replay_authenticated_prepare_and_complete_output(tmp_path: Path, *, prepare: bool) -> None:
    source, topology = tmp_path / "source", tmp_path / "topology"
    source_trust, topology_trust = archives(source, topology)
    # The synthetic historical calls have no real body; retain an explicit test
    # body so the verifier still exercises required original request inventory.
    for i in range(16):
        write_json(source / f"p{i}-request-0.json", {"offline_fake_only": True})
    output = tmp_path / "prepared" if prepare else tmp_path / "completed"
    report = runner.run(
        source,
        topology,
        source_trust,
        topology_trust,
        output,
        config(prepare_only=prepare, run_hosted=not prepare),
        None if prepare else Client(tmp_path),
    )
    frozen = json.loads((output / "frozen.json").read_bytes())
    trust = {"source-baseline": source_trust, "topology-baseline": topology_trust}
    _, verified = verify_topology(output, report, frozen, trust)
    assert len(verified) == 16
    assert all(page["operational"] for page in verified.values())
    with pytest.raises(ValueError, match="independent source and topology"):
        verify_topology(output, report, frozen, None)
    question = output / "p0-topology-0-row-0-request.json"
    body = json.loads(question.read_bytes())
    body["state"][0] = "Tampered literal source context"
    write_json(question, body)
    with pytest.raises(ValueError, match="question changed"):
        verify_topology(output, report, frozen, trust)


@pytest.mark.parametrize("choice", ["table", "prose", "unresolved", "malformed"])
def test_frozen_generation_gate_replays_exact_provider_response_and_body(
    tmp_path: Path,
    choice: str,
) -> None:
    directory, trusted_path, record, _ = baseline(tmp_path)
    frozen_source = json.loads((directory / "frozen.json").read_bytes())
    trusted = json.loads(trusted_path.read_bytes())
    name = "decision_oplog_run.py"
    data = Path(gate.__file__).with_name(name).read_bytes()
    (directory / "code" / name).write_bytes(data)
    trusted[name] = frozen_source["code_sha256"][name] = sha(data)
    write_json(directory / "frozen.json", frozen_source)
    write_json(trusted_path, trusted)

    class FakeClient:
        def __init__(self) -> None:
            self.directory = tmp_path
            self.ledger = tmp_path / "offline-fake-ledger.json"
            write_json(self.ledger, {"requests": []})

        def request(self, body: dict, **options: object) -> dict:
            answer = {
                "type": "choice",
                "choice": choice,
                "probabilities": {key: float(key == choice) for key in ("table", "prose", "unresolved")},
            }
            raw = {"answers": {"q0": answer}, "usage": {"prompt_tokens": 10, "completion_tokens": 1}}
            response_file = "response-000.json"
            write_json(self.directory / response_file, raw)
            entry = {
                "index": 0,
                "tag": options["tag"],
                "request_sha256": sha(json.dumps(body, separators=(",", ":")).encode()),
                "response_file": response_file,
                "accounted_usd": 0.01,
                "provider_reported_usd": 0.01,
                "cost_status": "offline-fake-reported",
            }
            write_json(self.ledger, {"requests": [entry]})
            return {"result": raw, "entry": entry, "replayed": False}

    output = tmp_path / "fresh"
    report = gate.run(directory, trusted_path, output, {**settings(directory), "run_hosted": True}, FakeClient())
    frozen = json.loads((output / "frozen.json").read_bytes())
    _, verified = verify_gate(output, report, frozen, {"baseline": trusted})
    assert verified[record["id"]]["operational"] == (choice != "malformed")
    request = output / f"{record['id']}-request-0.json"
    body = json.loads(request.read_bytes())
    body["state"] = "Tampered source evidence"
    write_json(request, body)
    with pytest.raises(ValueError, match="source packet differs"):
        verify_gate(output, report, frozen, {"baseline": trusted})
