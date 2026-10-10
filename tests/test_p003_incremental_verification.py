"""Independent replay rejects tampering in mocked incremental source ownership."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bench import p003_topology_run as runner
from bench.p003_incremental_verification import verify_topology
from bench.silver import write_json
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
