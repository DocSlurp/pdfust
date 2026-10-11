"""No-spend freeze and transport failure behavior for prospective repair arms."""

# ruff: noqa: ANN401 - mocked native transport receipts.
from pathlib import Path
from typing import Any

import pytest
from bench import p003_extension_run as runner
from bench.silver import sha, write_json


def frozen_arm(tmp_path: Path) -> Path:
    directory = tmp_path / "arm"
    (directory / "pages").mkdir(parents=True)
    (directory / "code").mkdir()
    rows = []
    for ident in ("a", "b"):
        path = directory / "pages" / f"{ident}.json"
        write_json(path, {"id": ident, "baseline_state": {"tables": [], "unresolved_ids": []},
                          "preparation_status": "ready", "packet": {"body": {"model": "typesafe/jev-1.13"}}})
        rows.append({"id": ident, "sha256": sha(path.read_bytes())})
    hashes = {}
    for name in runner.CODE_FILES:
        data = Path(runner.__file__).with_name(name).read_bytes()
        (directory / "code" / name).write_bytes(data)
        hashes[name] = sha(data)
    write_json(directory / "frozen.json", {"config": {"run_id": "extension-v1-test", "provider": "openrouter"},
                                          "pages": rows, "code_sha256": hashes, "resources": {}})
    return directory


class FailedClient:
    """Transport double that retains an unresolved reservation."""

    def __init__(self, root: Path) -> None:
        """Create a private test ledger."""
        self.ledger = root / "ledger.json"
        self.calls = 0
        write_json(self.ledger, {"requests": []})

    def request(self, _body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Record one failed attempt without making a network request."""
        self.calls += 1
        assert kwargs["replay"] is False
        write_json(self.ledger, {"requests": [{"tag": kwargs["tag"], "index": 0,
                                             "accounted_usd": 0.3, "cost_status": "reserved"}]})
        raise TimeoutError


def test_failed_transport_stops_arm_without_retry_or_baseline_credit(tmp_path: Path) -> None:
    directory = frozen_arm(tmp_path)
    client = FailedClient(tmp_path)
    report = runner.run(directory, client=client)
    assert client.calls == 1
    assert [row["status"] for row in report["results"]] == ["transport_error", "not_attempted"]
    assert report["intended_pages"] == 2
    assert report["selected_pages"] == 0
    assert report["costs"]["effective_usd"] is None
    assert report["costs"]["unresolved_reserved_usd"] == 0.3
    assert report["rates"]["intended_pages_per_dollar"] is None
    with pytest.raises(FileExistsError):
        runner.run(directory, client=client)
    assert client.calls == 1


def test_packet_mutation_fails_before_transport_or_start_marker(tmp_path: Path) -> None:
    directory = frozen_arm(tmp_path)
    client = FailedClient(tmp_path)
    (directory / "pages/a.json").write_text("{}")
    with pytest.raises(ValueError, match="Frozen page"):
        runner.run(directory, client=client)
    assert client.calls == 0
    assert not (directory / "started.json").exists()
