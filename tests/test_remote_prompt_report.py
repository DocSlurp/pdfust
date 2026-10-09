# ruff: noqa: ANN001, ANN002, ANN201, ANN202 - pytest fixtures and source-only test builder.
import base64
import hashlib
import io
import json

import pytest
from bench import remote_prompt_report as report
from bench.remote_prompt_packets import prepare
from PIL import Image


def fixture(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    image = io.BytesIO()
    Image.new("RGB", (512, 20), "white").save(image, format="PNG")
    png = image.getvalue()
    (source / "image.png").write_bytes(png)
    records = []
    originals = {}
    for number in range(24):
        identity = f"p{number:04d}"
        body = {
            "model": "native",
            "state": [
                f"literal evidence {number}",
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
            ],
            "questions": {
                "q0": {
                    "type": "choice",
                    "instructions": "Original question",
                    "criteria": {"join": "one group", "split": "two groups", "unresolved": "unknown"},
                }
            },
        }
        raw = json.dumps(body).encode()
        record = {"id": identity, "request_file": f"{identity}.json", "image_files": ["image.png"]}
        records.append(record)
        (source / record["request_file"]).write_bytes(raw)
        originals[identity] = {
            "row": {"arm": "fresh-rgb-512", "pixels": [512, 20]},
            "body": body,
            "raw": raw,
            "image": png,
            "stage": record,
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    manifest = source / "manifest.json"
    manifest.write_text(json.dumps({"records": records}))
    destination = tmp_path / "prompts"
    prepare(source, destination)
    return destination, manifest, originals


def test_exact_projection_verifies_without_targets(tmp_path):
    directory, packets, originals = fixture(tmp_path)
    verified = report.verify_prompts(directory, packets, originals)
    assert len(verified) == 96
    assert {row["variant"] for row in verified.values()} == set(report.VARIANTS)


def test_rehashed_unapproved_wording_refused(tmp_path):
    directory, packets, originals = fixture(tmp_path)
    provenance_path = directory / "provenance.json"
    provenance = json.loads(provenance_path.read_bytes())
    entry = provenance["mapping"][0]
    manifest = json.loads((directory / "manifest.json").read_bytes())
    row = next(row for row in manifest["records"] if row["id"] == entry["id"])
    request = directory / row["request_file"]
    body = json.loads(request.read_bytes())
    body["questions"]["q0"]["instructions"] = "Case-specific unauthorized wording"
    raw = json.dumps(body).encode()
    request.write_bytes(raw)
    entry["projected_request_sha256"] = hashlib.sha256(raw).hexdigest()
    provenance_path.write_text(json.dumps(provenance))
    with pytest.raises(ValueError, match="exact approved transform"):
        report.verify_prompts(directory, packets, originals)


def test_bad_projection_blocks_first_target_access(monkeypatch, tmp_path):
    monkeypatch.setattr(report, "verify_sources", lambda *_: ({}, {}))
    accesses = []

    def refuse(*_args):
        message = "unapproved source change"
        raise ValueError(message)

    monkeypatch.setattr(report, "verify_prompts", refuse)
    monkeypatch.setattr(report, "_verified", lambda path, _: accesses.append(path))
    with pytest.raises(ValueError, match="unapproved"):
        report.evaluate(tmp_path, tmp_path, tmp_path, tmp_path, {}, {})
    assert accesses == []


def observation():
    return {
        "target_atoms": [[{"id": "a", "text": "first"}], [{"id": "b", "text": "second"}]],
        "all_target_ids": ["a", "b"],
        "candidates": {"join": [["a", "b"]], "split": [["a"], ["b"]], "unresolved": []},
    }


def event(choice):
    return {
        "status": "ok",
        "response": {
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": {key: float(key == choice) for key in ("join", "split", "unresolved")},
                }
            }
        },
        "inference_wall_seconds": 1,
        "inference_cpu_seconds": 0.5,
        "peak_rss_bytes": 1024,
    }


def test_partial_denominators_and_conservative_ties():
    obs = observation()
    correct = report.scored_case(event("join"), obs, {"expected": "join"})
    ambiguous = report.scored_case(event("unresolved"), obs, {"expected": "unresolved"})
    missing = report.scored_case(None, obs, {"expected": "split"})
    metric = report.aggregate([correct, ambiguous, missing])
    assert metric["planned"] == 3
    assert metric["known_denominator"] == 2
    assert metric["ambiguous_denominator"] == 1
    assert metric["known_correct"] == 1
    assert metric["ambiguous_abstentions"] == 1
    assert metric["conservation"] == 2
    assert metric["inference_wall_seconds"] is None
    tied = event("join")
    tied["response"]["answers"]["q0"]["probabilities"] = {"join": 0.5, "split": 0.5, "unresolved": 0}
    result = report.scored_case(tied, obs, {"expected": "unresolved"})
    assert result["parsed"]["choice"] == "unresolved"
    assert result["parsed"]["tie_abstention"]


def test_paired_gains_losses_and_unpaired():
    obs = observation()
    baseline = [
        report.scored_case(event("split"), obs, {"expected": "join"}),
        report.scored_case(event("unresolved"), obs, {"expected": "unresolved"}),
        report.scored_case(None, obs, {"expected": "join"}),
    ]
    variant = [
        report.scored_case(event("join"), obs, {"expected": "join"}),
        report.scored_case(event("split"), obs, {"expected": "unresolved"}),
        baseline[2],
    ]
    metrics = report.paired(baseline, variant)
    assert metrics["known_gains"] == 1
    assert metrics["abstention_losses"] == 1
    assert metrics["unpaired"] == 1


def test_returned_request_hash_refused(tmp_path):
    (tmp_path / "status.json").write_text('{"status":"complete"}')
    rows = [
        {"id": "p", "event": "attempt_started"},
        {"id": "p", "event": "attempt_completed", "request_sha256": "forged"},
    ]
    (tmp_path / "attempts.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    with pytest.raises(ValueError, match="request hash"):
        report.events(tmp_path, {"p": {"sha256": "expected"}})
