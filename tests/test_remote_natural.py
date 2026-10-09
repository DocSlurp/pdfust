# ruff: noqa: ANN001, ANN201, ANN202, ANN002, SLF001 - source-only mocked freeze fixtures.
import base64
import hashlib
import json

import pytest
from bench import remote_natural as natural


def source(tmp_path, monkeypatch):
    directory = tmp_path / "source"
    directory.mkdir()
    records = []
    pages = [{"id": f"region{number}"} for number in range(24)]
    for page in pages:
        for arm in natural.ARMS:
            body = {
                "model": "original-frozen-model",
                "state": [
                    f" literal {page['id']} {arm} ",
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + base64.b64encode(b"source PNG").decode()},
                    },
                ],
                "questions": {
                    "q0": {
                        "type": "choice",
                        "instructions": "Frozen question",
                        "criteria": {"join": "one cell", "split": "two rows", "unresolved": "unclear"},
                    }
                },
            }
            raw = (json.dumps(body, indent=2) + "\n").encode()
            filename = f"request-{len(records):04d}.json"
            (directory / filename).write_bytes(raw)
            records.append(
                {
                    "request": filename,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "model": body["model"],
                    "arm": arm,
                    "page_ids": [page["id"]],
                    "body_bytes": len(raw),
                    "non_image_bytes": 100,
                }
            )
    manifest = {"experiment": "L011-source", "pages": pages, "records": records, "source_sha256": "source-digest"}
    (directory / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(natural, "source_verify", lambda _: manifest)
    return directory


def test_prepare_exact96_source_bytes_no_references(tmp_path, monkeypatch):
    directory = source(tmp_path, monkeypatch)
    original_reader = natural._read

    def read(path):
        assert "private" not in path.name
        return original_reader(path)

    monkeypatch.setattr(natural, "_read", read)
    packets = natural.prepare(directory, tmp_path / "packets")
    manifest, inventory = natural.verify_stage(directory, packets)
    assert len(inventory) == 96
    assert len(manifest["pages"]) == 24
    staged = json.loads(packets.read_bytes())
    assert set(staged) == {"records"}
    assert len({row["id"] for row in staged["records"]}) == 96
    assert not (packets.parent / "private-references.json").exists()
    assert all(set(row) == {"id", "request_file", "image_files"} for row in staged["records"])
    with pytest.raises(FileExistsError):
        natural.prepare(directory, packets.parent)


def test_rehashed_staged_request_mutation_refused(tmp_path, monkeypatch):
    directory = source(tmp_path, monkeypatch)
    packets = natural.prepare(directory, tmp_path / "packets")
    first = json.loads(packets.read_bytes())["records"][0]
    (packets.parent / first["request_file"]).write_text('{"state":"changed"}')
    with pytest.raises(ValueError, match="source request differs"):
        natural.verify_stage(directory, packets)


def test_separate_full_source_and_scope_agreement():
    reference = {
        "choice": "split",
        "scope_references": {"record": {"choice": "split"}, "description": {"choice": "unresolved"}},
    }
    assert natural.agreement("split", reference, "description-512") == {
        "full_match": True,
        "scope_match": False,
        "scope_abstention": False,
    }
    assert natural.agreement("unresolved", reference, "description-1200") == {
        "full_match": False,
        "scope_match": True,
        "scope_abstention": True,
    }


def test_returned_hash_failures_precede_references(monkeypatch, tmp_path):
    monkeypatch.setattr(natural, "verify_stage", lambda *_: ({}, {}))
    reads = []
    monkeypatch.setattr(natural, "_json", reads.append)

    def refuse(*_args):
        message = "worker request hash differs"
        raise ValueError(message)

    monkeypatch.setattr(natural, "verify_events", refuse)
    with pytest.raises(ValueError, match="hash differs"):
        natural.evaluate(tmp_path, tmp_path, {"mock": tmp_path}, references_dir=tmp_path)
    assert not reads


def test_completed_request_hash_is_verified(tmp_path):
    (tmp_path / "status.json").write_text('{"status":"complete"}')
    records = [
        {"id": "opaque", "event": "attempt_started"},
        {"id": "opaque", "event": "attempt_completed", "request_sha256": "forged"},
    ]
    (tmp_path / "attempts.jsonl").write_text("\n".join(json.dumps(row) for row in records))
    with pytest.raises(ValueError, match="request hash"):
        natural.verify_events(tmp_path, {"opaque": {"record": {"sha256": "original"}}})


def test_warm_estimates_preserve_unknowns():
    summary = {"inference_seconds": 12.0, "counts": {"completed": 24}}
    result = natural.warm_rates(summary, 1.275)
    assert result["warm_inference_estimated_usd"] == pytest.approx(1.275 * 12 / 3600)
    assert result["warm_region_inputs_per_minute"] == 120
    summary["inference_seconds"] = None
    assert natural.warm_rates(summary, 1.275)["warm_inference_estimated_usd"] is None
    assert natural.warm_rates(summary, None)["warm_region_inputs_per_estimated_usd"] is None
    with pytest.raises(ValueError, match="finite"):
        natural.warm_rates(summary, float("nan"))


def test_stock_labels_require_explicit_opt_in():
    response = {"backend": "stock-vllm-json", "answers": {"q0": {"type": "choice", "choice": "unresolved"}}}
    with pytest.raises(ValueError, match="opt-in"):
        natural.parse_decision(response)
    parsed = natural.parse_decision(response, allow_exploratory_stock=True)
    assert parsed["choice"] == "unresolved"
    assert parsed["probabilities"] is None
    assert not parsed["tie_abstention"]


@pytest.mark.parametrize(
    "extra", [{"probabilities": {}}, {"confidence": 0.9}, {"decision": "join"}, {"choice": "invented"}]
)
def test_stock_invalid_probabilities_and_aliases_refused(extra):
    response = {"backend": "stock-vllm-json", "answers": {"q0": {"type": "choice", "choice": "split", **extra}}}
    with pytest.raises(ValueError, match=r"stock|Stock"):
        natural.parse_decision(response, allow_exploratory_stock=True)


def test_concurrent_throughput_uses_global_elapsed():
    rates = natural.concurrent_rates({"lanes": 8, "wall_seconds": 6, "concurrent_request_span_seconds": 5}, 96)
    assert rates["wall_seconds_inputs_per_minute"] == 960
    assert rates["concurrent_request_span_seconds_inputs_per_minute"] == 1152
    assert rates["concurrent"]
    unknown = natural.concurrent_rates({"lanes": 8, "wall_seconds": float("nan")}, 96)
    assert unknown["wall_seconds_inputs_per_minute"] is None
