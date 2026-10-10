"""Offline correction reuses only exact admitted requests and immutable decisions."""

import json
from pathlib import Path
from typing import Any

import pytest
from bench import p003_topology_replay as replay
from bench import p003_topology_run as runner
from bench.silver import sha, write_json
from test_p003_topology_run import Client, archives, config


class HashedClient(Client):
    """Retain a fake original admitted body hash alongside mocked responses."""

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        """Hash exact serialization just like the original hosted transport."""
        response = super().request(body, **kwargs)
        response["entry"]["request_sha256"] = sha(replay._bytes(body))  # noqa: SLF001
        return response


def test_complete_offline_replay_exact_bodies_cost_separation_and_provenance(tmp_path: Path) -> None:
    source, topology = tmp_path / "source", tmp_path / "topology"
    a, b = archives(source, topology)
    original = tmp_path / "old"
    runner.run(source, topology, a, b, original, config(run_hosted=True), HashedClient(tmp_path))
    trust = json.loads((original / "frozen.json").read_bytes())["code_sha256"]
    oldbytes = (original / "report.json").read_bytes()
    output = tmp_path / "corrected"
    report = replay.run(original, trust, a, b, output)
    assert report["incremental_ownership"]["returned_calls"] == 0
    assert report["incremental_ownership"]["attempts"] == []
    assert report["incremental_ownership"]["retained_response_count"] == 32
    assert report["incremental_ownership"]["status_counts"] == {"completed": 16}
    assert report["pages_per_minute"] is None
    assert report["transcript_origin"]["original_report"]["incremental_ownership"]["effective_usd"] == 0.32
    assert (original / "report.json").read_bytes() == oldbytes
    assert (output / "original-ownership-run/report.json").read_bytes() == oldbytes
    stem = report["transcript_origin"]["retained_responses"][0]["stem"]
    body = json.loads((original / f"{stem}-request.json").read_bytes())
    transcript = replay.Transcript(original, "test")
    # Crop identity itself contains a dash; use the known original question stem.
    tag = "P003/test/p0/topology-0/row/0"
    packet = json.loads((original / "p0-topology-0-snapshot.json").read_bytes())
    plan = runner.ownership.Plan(runner.ownership._dump(packet))  # noqa: SLF001
    body = runner.ownership.batches(plan, body["model"], body["state"][1]["image_url"]["url"])[0]
    transcript.request(body, tag=tag)
    unchanged = dict(body)
    body["model"] = "changed"
    with pytest.raises(ValueError, match="bytes differ"):
        transcript.request(body, tag=tag)
    response_path = original / "p0-topology-0-row-0-response.json"
    response = json.loads(response_path.read_bytes())
    response["entry"]["request_sha256"] = "wrong"
    write_json(response_path, response)
    with pytest.raises(ValueError, match="serialization differs"):
        transcript.request(unchanged, tag=tag)


def test_replay_refuses_changed_partition_before_any_reuse(tmp_path: Path) -> None:
    source, topology = tmp_path / "source", tmp_path / "topology"
    a, b = archives(source, topology)
    original = tmp_path / "old"
    runner.run(source, topology, a, b, original, config(run_hosted=True), HashedClient(tmp_path))
    trust = json.loads((original / "frozen.json").read_bytes())["code_sha256"]
    path = original / "p0-ownership-plan.json"
    plan = json.loads(path.read_bytes())
    plan["regions"][1]["source_ids"].reverse()
    write_json(path, plan)
    with pytest.raises(ValueError, match="assignments differ"):
        replay.run(original, trust, a, b, tmp_path / "refused")
