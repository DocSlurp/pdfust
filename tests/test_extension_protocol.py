"""Source conservation and exact wire contracts for extension packets."""

# ruff: noqa: ANN401 - heterogeneous mocked research packets.

import json
from copy import deepcopy
from typing import Any

import pytest
from bench import extension_protocol as protocol
from bench import extension_registry as registry


def fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = {
        "page_size": [100, 100],
        "words": [
            {"id": "w0", "text": "alpha", "bbox": [1, 1, 10, 10]},
            {"id": "w1", "text": "beta", "bbox": [20, 1, 30, 10]},
        ],
    }
    table = {
        "row_count": 1,
        "col_count": 2,
        "bbox": [0, 0, 40, 15],
        "values": [["alpha", "beta"]],
        "cells": [{"source_ids": ["w0"], "role": "unknown"}, {"source_ids": ["w1"], "role": "unknown"}],
        "spans": [{"row": 0, "column": i, "row_span": 1, "column_span": 1} for i in range(2)],
    }
    return source, [{"tables": [table], "unresolved_ids": []}, {"tables": [], "unresolved_ids": ["w0", "w1"]}]


def packet(**kwargs: Any) -> dict[str, Any]:
    source, candidates = fixture()
    return protocol.build_request(source, candidates, model="typesafe/jev-1.13", **kwargs)


def response(p: dict[str, Any], choice: str | None = None) -> dict[str, Any]:
    options = [*p["choices_by_id"], "unresolved"]
    chosen = choice or options[0]
    return {
        "model": p["spec"]["canonical_ids"][-1],
        "answers": {
            "q0": {
                "type": "choice",
                "choice": chosen,
                "probabilities": {c: int(c == chosen) for c in options},
            }
        },
    }


def test_registry_distinct_identities_and_provider_modality() -> None:
    assert len(registry.OPENROUTER) == 16
    assert "jaredpalmer/kev-4b" in registry.OPENROUTER
    assert registry.model_spec("respan/span-01")["compatibility_only"]
    assert registry.model_spec("respan/span-01")["context_tokens"] is None
    assert registry.model_spec("liquid/d1")["input_modalities"] == ["text"]
    assert "image" in registry.model_spec("liquid/d1", "vercel")["input_modalities"]
    with pytest.raises(ValueError, match="Unknown extension"):
        registry.model_spec("~typesafe/jev-latest")


def test_freeze_dedup_order_and_no_target_fields() -> None:
    source, candidates = fixture()
    source["gold"] = "secret target"
    candidates[0]["expected"] = "secret target"
    a = protocol.build_request(source, [*candidates, candidates[0]], model="typesafe/jev-1.13")
    b = protocol.build_request(source, list(reversed(candidates)), model="typesafe/jev-1.13")
    assert a["body"] == b["body"]
    assert a["metadata"]["input_candidates"] == 3
    assert a["metadata"]["unique_candidates"] == 2
    assert "secret target" not in json.dumps(a)
    source["words"][0]["text"] = "altered-source-value"
    assert "altered-source-value" not in json.dumps(a)


def test_complete_local_admission_and_bounded_word_omissions() -> None:
    source = {"words": [{"id": f"w{i}", "text": str(i), "bbox": [0, 0, 1, 1]} for i in range(140)]}
    candidates = [{"tables": [], "unresolved_ids": [w["id"] for w in source["words"]]}]
    p = protocol.build_request(source, candidates, model="typesafe/jev-1.13", max_words=128)
    evidence = json.loads(p["body"]["state"])
    assert evidence["source_omitted_words"] == 12
    assert len(p["choices_by_id"]["c0"]["unresolved_ids"]) == 140
    assert len(evidence["source"]["words"]) == 128
    candidates[0]["unresolved_ids"].pop()
    with pytest.raises(ValueError, match="exactly one owner"):
        protocol.build_request(source, candidates, model="typesafe/jev-1.13", max_words=128)


def test_differences_keep_shape_and_omit_only_exact_common_cells() -> None:
    source, candidates = fixture()
    other = deepcopy(candidates[0])
    other["tables"][0]["bbox"] = [0, 0, 45, 15]
    p = protocol.build_request(source, [candidates[0], other], model="typesafe/jev-1.13", mode="differences")
    evidence = json.loads(p["body"]["state"])
    assert set(evidence["shared_baseline_cells_per_candidate"].values()) == {2}
    assert {tuple(v["tables"][0]["bbox"]) for v in evidence["candidates"].values()} == {(0, 0, 40, 15), (0, 0, 45, 15)}
    assert all(v["tables"][0]["shape"][0] == 1 for v in evidence["candidates"].values())


def test_capacity_refuses_before_partial_packet() -> None:
    with pytest.raises(protocol.EvidenceCapacityError):
        packet(max_bytes=50)


def test_native_identity_and_distribution_rejection() -> None:
    p = packet()
    answer = protocol.parse_choice(response(p), p)
    assert answer["selected_state"] == p["choices_by_id"][answer["choice"]]
    assert protocol.parse_choice(response(p, "unresolved"), p)["abstained"]
    bad = response(p)
    bad["model"] = "typesafe/jev-latest"
    with pytest.raises(ValueError, match="attested identity"):
        protocol.parse_choice(bad, p)
    bad = response(p)
    bad["answers"]["q0"]["probabilities"].pop("unresolved")
    with pytest.raises(ValueError, match="distribution"):
        protocol.parse_choice(bad, p)


def test_source_owned_values_cannot_be_authored() -> None:
    source, candidates = fixture()
    candidates[0]["tables"][0]["values"][0][0] = "invented"
    with pytest.raises(ValueError, match="literal cell sources"):
        protocol.build_request(source, candidates, model="typesafe/jev-1.13")


def test_vercel_d1_exact_known_native_wire() -> None:
    source, candidates = fixture()
    p = protocol.build_request(
        source, candidates, model="liquid/d1", provider="vercel", image_url="data:image/png;base64,eA=="
    )
    assert p["metadata"]["endpoint"] == registry.VERCEL_D1_ENDPOINT
    assert p["body"]["input"][0]["content"][1]["type"] == "input_image"
    raw = response(p)
    raw["answers"]["q0"]["name"] = "q0"
    assert not protocol.parse_choice(raw, p)["abstained"]
    with pytest.raises(ValueError, match="image input"):
        protocol.build_request(source, candidates, model="liquid/d1", image_url="data:image/png;base64,eA==")


def test_difference_reconstruction_with_empty_candidate() -> None:
    source, candidates = fixture()
    other = deepcopy(candidates[0])
    other["tables"][0]["bbox"] = [0, 0, 45, 15]
    p = protocol.build_request(source, [*candidates, other], model="typesafe/jev-1.13", mode="differences")
    evidence = json.loads(p["body"]["state"])
    reconstructed = protocol.reconstruct_descriptors(evidence)
    assert any(not state["tables"] for state in reconstructed.values())
    assert max(evidence["shared_baseline_cells_per_candidate"].values()) == 2
    assert all(
        all(type(i) is int for i in cell)
        for state in reconstructed.values()
        for table in state["tables"]
        for cell in table["cells"]
    )


def test_frozen_packet_tampering_is_rejected() -> None:
    p = packet()
    raw = response(p)
    p["choices_by_id"]["c0"]["unresolved_ids"].append("invented")
    with pytest.raises(ValueError, match="modified"):
        protocol.parse_choice(raw, p)
