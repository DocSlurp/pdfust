"""Frozen parent reuse, source-only packet identity and complete inventories."""

import hashlib
import json
from pathlib import Path

import pytest
from bench.lowlevel_cases import cases
from bench.lowlevel_compact import encoded, expand
from bench.lowlevel_evidence import MODELS, snapshot
from bench.lowlevel_evidence import request as original_request
from bench.lowlevel_packets import ARMS, prepare, request, verify


def write(path: Path, value: object) -> str:
    raw = encoded(value)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def parent(tmp_path: Path) -> Path:
    directory = tmp_path / "parent"
    directory.mkdir()
    pages = []
    records: list[dict[str, object]] = []
    observations = []
    fixtures = [cases()[0], cases()[39]]
    for case in fixtures:
        ident = case["id"]
        source_name, obs_name = f"source-{ident}.pdf", f"observation-{ident}.json"
        (directory / source_name).write_bytes(case["pdf_bytes"])
        observation = snapshot(case["pdf_bytes"], case["evidence"])
        observations.append(observation)
        pages.append(
            {
                "id": ident,
                "source_file": source_name,
                "source_sha256": hashlib.sha256(case["pdf_bytes"]).hexdigest(),
                "observation_file": obs_name,
                "observation_sha256": write(directory / obs_name, observation),
            }
        )
    for model in MODELS:
        name = f"request-{len(records)}.json"
        records.append(
            {
                "request": name,
                "sha256": write(directory / name, original_request(observations, model, "canonical")),
                "model": model,
                "arm": "canonical",
                "page_ids": [page["id"] for page in pages],
            }
        )
    catalog_hash = write(directory / "catalog-prices.json", {})
    target_hash = write(
        directory / "private-targets.json", [{"id": case["id"], "expected": case["expected"]} for case in fixtures]
    )
    write(
        directory / "manifest.json",
        {
            "schema": 1,
            "records": records,
            "pages": pages,
            "models": list(MODELS),
            "arms": ["canonical"],
            "catalog_sha256": catalog_hash,
            "targets_sha256": target_hash,
        },
    )
    return directory


def test_prepare_reuses_all_frozen_sources_and_verifies(
    parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbid_snapshot(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Packet preparation must never resnapshot")

    monkeypatch.setattr("bench.lowlevel_evidence.snapshot", forbid_snapshot)
    directory = tmp_path / "packets"
    manifest = prepare(parent, directory)
    assert verify(directory) == manifest
    assert manifest["experiment"] == "L004"
    assert manifest["arms"] == list(ARMS)
    assert len(manifest["records"]) == len(MODELS) * len(ARMS)
    assert all(record["body_bytes"] <= 32000 for record in manifest["records"])
    assert (directory / "private-targets.json").read_bytes() == (parent / "private-targets.json").read_bytes()
    for page in manifest["pages"]:
        for key in ("source_file", "observation_file"):
            assert (directory / page[key]).read_bytes() == (parent / page[key]).read_bytes()


def test_gold_mutation_changes_lineage_but_cannot_change_request_bodies(parent: Path, tmp_path: Path) -> None:
    first = prepare(parent, tmp_path / "first")
    original = json.loads((parent / "manifest.json").read_bytes())
    original["targets_sha256"] = write(
        parent / "private-targets.json", [{"expected": "invented gold", "family": "invented family"}]
    )
    write(parent / "manifest.json", original)
    second = prepare(parent, tmp_path / "second")
    assert first["records"] == second["records"]
    assert first["parent_manifest_sha256"] != second["parent_manifest_sha256"]
    assert all("invented" not in (tmp_path / "second" / record["request"]).read_text() for record in second["records"])


@pytest.mark.parametrize("tamper", ["source", "observation", "request", "parent", "catalog", "inventory"])
def test_verify_refuses_mutated_freezes(parent: Path, tmp_path: Path, tamper: str) -> None:
    directory = tmp_path / "packets"
    manifest = prepare(parent, directory)
    if tamper in ("source", "observation"):
        key = "source_file" if tamper == "source" else "observation_file"
        (directory / manifest["pages"][0][key]).write_bytes(b"changed")
    elif tamper == "request":
        (directory / manifest["records"][0]["request"]).write_bytes(b"changed")
    elif tamper == "parent":
        (parent / "manifest.json").write_bytes(b"changed")
    elif tamper == "catalog":
        (directory / "catalog-prices.json").write_bytes(b"changed")
    else:
        manifest["records"].pop()
        write(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match="L004"):
        verify(directory)


def test_request_scopes_and_packet_roundtrip_from_actual_sources(parent: Path) -> None:
    manifest = json.loads((parent / "manifest.json").read_bytes())
    observations = [json.loads((parent / page["observation_file"]).read_bytes()) for page in manifest["pages"]]
    body = request(observations, MODELS[0], "canonicalcompact")
    assert set(body["questions"]) == {"q0", "q1"}
    assert body["questions"]["q1"]["instructions"].startswith("Consider ONLY observations.q1.")
    first = expand(body["state"]["observations"]["q0"])
    assert "source_order" not in first["glyphs"][0]
    assert first["chunks"][0]["text"] == "12"
    observations[0]["operators"]["operators"] = [{"operator": "Tj", "operands": ["z" * 40000]}]
    with pytest.raises(ValueError, match="32000"):
        request(observations[:1], MODELS[0], "operatorscompact")
