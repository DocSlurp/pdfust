"""Frozen-crop ranking keeps exact candidate provenance and atomic first-output fallback."""

import base64
import io
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import p003_candidate_run as runner
from bench import pipeline_vision_transcription as transcription
from bench.generalization_vision_regions import compose
from bench.silver import sha, write_json
from PIL import Image


def pixels(color: str = "white") -> tuple[str, bytes]:
    stream = io.BytesIO()
    Image.new("RGB", (4, 2), color).save(stream, format="PNG")
    data = stream.getvalue()
    return "data:image/png;base64," + base64.b64encode(data).decode(), data


def provider(value: str) -> dict[str, Any]:
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "answers": {
                                "q0": {
                                    "tables": [
                                        {
                                            "bbox": [0, 0, 1000, 1000],
                                            "matrix": [["Label", "Count"], [value, "20"]],
                                            "mergedspans": [],
                                        }
                                    ]
                                }
                            }
                        }
                    )
                },
            }
        ]
    }


def options_from_evidence(evidence: dict[str, Any]) -> list[str]:
    """Find the fake target in either complete or difference evidence."""
    if evidence.get("mode") == "differences":
        return [
            alias
            for t, r, c, slots in evidence["differing_slots"]
            for alias, value in slots.items()
            if (t, r, c) == (0, 1, 0) and value.get("value") == "second"
        ]
    return [alias for alias, tables in evidence["candidates"].items() if tables[0]["values"][1][0] == "second"]


class Client:
    """Typed deterministic fake with isolated ledger; no provider or credentials."""

    def __init__(
        self, directory: Path, *, abstain: bool = False, malformed: bool = False, fail_at: int | None = None
    ) -> None:
        """Create a separate ledger and declared answer mode."""
        self.ledger = directory / "mock-ledger.json"
        write_json(self.ledger, {"requests": []})
        self.abstain, self.malformed, self.fail_at = abstain, malformed, fail_at
        self.bodies: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], **options: Any) -> dict[str, Any]:  # noqa: ANN401
        """Retain an explicitly fake ranking charge and return a typed decision."""
        assert options["replay"] is False
        assert options["tag"].startswith("P003/")
        self.bodies.append(deepcopy(body))
        text = body["state"][0] if isinstance(body["state"], list) else body["state"]
        evidence = json.loads(text)
        selected = "unresolved" if self.abstain else next(alias for alias in options_from_evidence(evidence))
        options_list = body["questions"]["q0"]["criteria"]
        ledger = json.loads(self.ledger.read_bytes())
        entry = {
            "index": len(ledger["requests"]),
            "tag": options["tag"],
            "accounted_usd": 0.01,
            "cost_status": "provider-reported USD",
            "provider_reported_usd": 0.01,
        }
        ledger["requests"].append(entry)
        write_json(self.ledger, ledger)
        answer = {
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": selected,
                    "probabilities": {
                        alias: 0.9 if alias == selected else 0.1 / (len(options_list) - 1) for alias in options_list
                    },
                }
            }
        }
        if self.malformed or entry["index"] == self.fail_at:
            answer["answers"]["q0"]["choice"] = "invented"
        return {"entry": entry, "result": answer, "replayed": False}


def baseline(
    directory: Path,
    value: str,
    *,
    color: str = "white",
    failed: bool = False,
    provider_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    directory.mkdir()
    url, data = pixels(color)
    viewport, crop_bounds = [0, 0, 200, 100], [10, 10, 190, 90]
    crop = {
        "index": 0,
        "request_index": 0,
        "viewport": crop_bounds,
        "detector_box": {"label": "Table", "confidence": 0.9, "bbox": crop_bounds},
        "status": "ok",
        "image": {"image_sha256": sha(data), "image_viewport": crop_bounds, "image_bytes": len(data)},
        "transcription_response": provider(value),
    }
    body = transcription.request("anthropic/claude-haiku-5.5", url, crop_bounds, 8192)
    if provider_name:
        body["provider"] = {"only": [provider_name], "allow_fallbacks": False, "require_parameters": True}
    crop["request"] = {"body_sha256": sha(json.dumps(body, separators=(",", ":")).encode())}
    crop["tables"] = transcription.parse(crop["transcription_response"], crop_bounds)["tables"]
    records, results = [], []
    for i in range(16):
        ident = f"p{i}"
        record = {"id": ident, "pdf_path": "unused-frozen-source.pdf", "pdf_sha256": "frozen-pdf", "page_number": i}
        regions = [deepcopy(crop)] if i == 0 else []
        state = compose(regions, viewport)
        result = {
            "id": ident,
            "status": "error" if failed and i == 0 else "ok",
            "tables": state["tables"],
            "pdf_sha256": "frozen-pdf",
            "route": "vision_transcription_regions",
            "source_conserved": False,
            "unresolved_ids": [],
            "text_provenance": "model-transcribed",
            "coverage": "unverified",
            "viewport": viewport,
            "original_rotation": 0,
            "proposal_count": len(regions),
            "transcription_regions": regions,
            "layout_detection": {
                "type": "result",
                "device": "cpu",
                "viewport": viewport,
                "boxes": [deepcopy(crop["detector_box"])] if regions else [],
            },
            "calls": [{"entry": {"index": i, "accounted_usd": 0.75}}],
            "wall_seconds": 5.0,
            "cpu_seconds": 1.0,
        }
        if result["status"] == "error":
            result.update(error="original page failure", error_type="ValueError")
        write_json(directory / f"{ident}-result.json", result)
        if result["status"] == "ok":
            write_json(directory / f"{ident}-structure.json", state)
            (directory / f"{ident}.md").write_text(transcription.markdown(state))
        if regions:
            write_json(directory / f"{ident}-request-0.json", body)
        records.append(record)
        results.append(result)
    (directory / "code").mkdir()
    trusted = {}
    root = Path(transcription.__file__).parent
    for name in (
        "pipeline_vision_transcription.py",
        "pipeline_frontier.py",
        "generalization_vision_run.py",
        "generalization_vision_regions.py",
        "pipeline_run.py",
    ):
        encoded = (root / name).read_bytes()
        (directory / "code" / name).write_bytes(encoded)
        trusted[name] = sha(encoded)
    write_json(
        directory / "frozen.json",
        {
            "config": {"processor": "vision_regions", "generation_provider": provider_name},
            "records": records,
            "manifest_sha256": "natural16-sources",
            "code_sha256": trusted,
        },
    )
    write_json(
        directory / "report.json",
        {
            "config": {"processor": "vision_regions", "generation_provider": provider_name},
            "results": results,
            "effective_usd": 12.0,
            "calls": 16,
            "metrics": {"wall_seconds": 80.0},
        },
    )
    return records[0], results[0], trusted


def config(**extra: Any) -> dict[str, Any]:  # noqa: ANN401
    return {"run_hosted": True, "image_edge": 0, "model": "typesafe/jev-1.13", "seed": 7, **extra}


@pytest.mark.parametrize("provider_name", [None, "anthropic"])
def test_authenticated_matched_pool_exact_candidate_and_separate_cost(
    tmp_path: Path,
    provider_name: str | None,
) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, original, trust0 = baseline(first, "first", provider_name=provider_name)
    _, _, trust1 = baseline(second, "second", provider_name=provider_name)
    prior_bytes = (first / "p0-structure.json").read_bytes()
    client = Client(tmp_path)
    output = tmp_path / "ranked"
    report = runner.run([first, second], [trust0, trust1], output, config(), client)
    page = report["results"][0]
    assert page["ranking_status"] == "completed"
    assert page["tables"][0]["values"][1][0] == "second"
    assert page["source_conserved"] is False
    assert page["calls"] == original["calls"]
    assert report["candidate_generation_reports"][0]["effective_usd"] == 12.0
    assert report["incremental_ranking"]["effective_usd"] == 0.01
    assert report["pages_per_minute"] is None
    assert (first / "p0-structure.json").read_bytes() == prior_bytes
    assert (output / "baseline-0/p0-structure.json").read_bytes() == prior_bytes
    assert len(client.bodies) == 1
    assert isinstance(client.bodies[0]["state"], str)
    assert "candidate-generator" not in client.bodies[0]["state"]
    assert (output / "p0-selector-0-response.json").exists()
    assert report["results"][1]["ranking_status"] == "not_applicable"


@pytest.mark.parametrize(
    ("abstain", "malformed", "expected"), [(True, False, "completed"), (False, True, "failed_retained_first")]
)
def test_abstention_and_malformed_selector_keep_original_output(
    tmp_path: Path, *, abstain: bool, malformed: bool, expected: str
) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first")
    _, _, b = baseline(second, "second")
    output = tmp_path / "ranked"
    report = runner.run(
        [first, second], [a, b], output, config(), Client(tmp_path, abstain=abstain, malformed=malformed)
    )
    assert report["results"][0]["ranking_status"] == expected
    assert json.loads((output / "p0-structure.json").read_bytes()) == json.loads(
        (first / "p0-structure.json").read_bytes()
    )
    assert (output / "p0.md").read_bytes() == (first / "p0.md").read_bytes()
    if malformed:
        assert report["incremental_ranking"]["ledger_attempts"] == 1
        assert report["results"][0]["ranking_errors"]
        assert report["results"][0]["ranking_regions"][0]["ranking_status"] == "failed_retained_first"


def test_mismatched_actual_crop_and_duplicate_pool_never_call_selector(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first")
    _, _, b = baseline(second, "second", color="black")
    client = Client(tmp_path)
    report = runner.run([first, second], [a, b], tmp_path / "mismatched", config(), client)
    assert report["results"][0]["ranking_status"] == "failed_retained_first"
    assert client.bodies == []
    third = tmp_path / "third"
    _, _, c = baseline(third, "first")
    report = runner.run([first, third], [a, c], tmp_path / "duplicates", config(), client)
    assert report["results"][0]["ranking_status"] == "not_applicable"
    assert client.bodies == []


def test_untrusted_code_original_error_and_image_capability_gates(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first", failed=True)
    _, _, b = baseline(second, "second")
    client = Client(tmp_path)
    with pytest.raises(ValueError, match="independent trusted"):
        runner.run([first, second], [{}, b], tmp_path / "untrusted", config(), client)
    with pytest.raises(ValueError, match="support"):
        runner.run([first, second], [a, b], tmp_path / "bad-image", config(image_edge=512), client)
    report = runner.run([first, second], [a, b], tmp_path / "skipped", config(), client)
    assert report["results"][0]["status"] == "error"
    assert report["results"][0]["ranking_status"] == "baseline_failed_skipped"
    assert report["results"][0]["error"] == "original page failure"
    assert client.bodies == []


def test_supported_image_model_records_actual_same_viewport_pixels(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first")
    _, _, b = baseline(second, "second")
    calls = []

    def image_factory(
        record: dict[str, Any], original: dict[str, Any], crop: dict[str, Any], edge: int
    ) -> tuple[str, dict[str, Any]]:
        calls.append((record["id"], edge))
        assert crop["viewport"] == original["transcription_regions"][0]["viewport"]
        url, data = pixels()
        return url, {
            "image_sha256": sha(data),
            "image_bytes": len(data),
            "image_viewport": crop["viewport"],
            "image_edge": edge,
            "image_size": [4, 2],
            "rerendered": True,
        }

    client = Client(tmp_path)
    report = runner.run(
        [first, second],
        [a, b],
        tmp_path / "image",
        config(image_edge=512, model="cloudflare/clef-omni"),
        client,
        image_factory=image_factory,
    )
    assert report["results"][0]["ranking_status"] == "completed"
    assert calls == [("p0", 512)]
    assert isinstance(client.bodies[0]["state"], list)
    assert client.bodies[0]["state"][1]["type"] == "image_url"
    assert report["results"][0]["ranking_regions"][0]["selector_image"]["image_bytes"] > 0


def test_invalid_other_baseline_is_provenance_not_partial_rescue(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first")
    _, _, b = baseline(second, "second", failed=True)
    client = Client(tmp_path)
    output = tmp_path / "invalid-other"
    report = runner.run([first, second], [a, b], output, config(), client)
    assert report["results"][0]["status"] == "ok"
    assert report["results"][0]["ranking_status"] == "not_applicable_baseline_failure"
    assert report["candidate_generation_reports"][1]["effective_usd"] == 12.0
    assert report["results"][0]["candidate_generation_provenance"][1]["status"] == "error"
    assert (output / "p0-structure.json").read_bytes() == (first / "p0-structure.json").read_bytes()
    assert client.bodies == []


@pytest.mark.parametrize(
    ("image_mode", "visibility"),
    [
        ("rgb_png", "source"),
        ("grayscale8", "source"),
        ("rgb_palette16", "source"),
        ("rgb_png", "blank"),
        ("rgb_palette16", "blur"),
    ],
)
def test_image_encoding_reaches_request_and_retains_original_provenance(
    tmp_path: Path, image_mode: str, visibility: str
) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first")
    _, _, b = baseline(second, "second")

    def image_factory(
        _record: dict[str, Any], _original: dict[str, Any], crop: dict[str, Any], edge: int
    ) -> tuple[str, dict[str, Any]]:
        stream = io.BytesIO()
        Image.new("RGB", (20, 10), (200, 30, 80)).save(stream, format="JPEG", quality=90)
        data = stream.getvalue()
        return "data:image/jpeg;base64," + base64.b64encode(data).decode(), {
            "image_sha256": sha(data),
            "image_bytes": len(data),
            "image_viewport": crop["viewport"],
            "image_edge": edge,
            "image_size": [20, 10],
            "image_codec": "JPEG",
            "image_quality": 90,
        }

    client = Client(tmp_path)
    output = tmp_path / "encoded"
    report = runner.run(
        [first, second],
        [a, b],
        output,
        config(image_edge=512, image_mode=image_mode, image_visibility=visibility, model="cloudflare/clef-omni"),
        client,
        image_factory=image_factory,
    )
    page = report["results"][0]
    assert page["ranking_status"] == "completed"
    metadata = page["ranking_regions"][0]["selector_image"]
    image_part = client.bodies[0]["state"][1]
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")
    assert metadata["selector_image_mode"] == image_mode
    assert metadata["source_image_codec"] == "JPEG"
    assert "p003_selector_image.py" in json.loads((output / "frozen.json").read_bytes())["code_sha256"]
    if visibility != "source":
        assert metadata["image_visibility"] == visibility
        assert metadata["visibility_source_sha256"]
        assert "p003_selector_visibility.py" in json.loads((output / "frozen.json").read_bytes())["code_sha256"]


def test_later_crop_selector_failure_rolls_back_whole_page(tmp_path: Path) -> None:
    paths = [tmp_path / "first", tmp_path / "second"]
    trusts = []
    for path, value in zip(paths, ("first", "second"), strict=True):
        _, page, trusted = baseline(path, value)
        trusts.append(trusted)
        crops = []
        for index, bounds in enumerate(([10, 10, 90, 90], [110, 10, 190, 90])):
            crop = deepcopy(page["transcription_regions"][0])
            crop.update(index=index, request_index=index, viewport=bounds)
            crop["detector_box"]["bbox"] = bounds
            crop["image"]["image_viewport"] = bounds
            url, _ = pixels()
            body = transcription.request("anthropic/claude-haiku-5.5", url, bounds, 8192)
            crop["request"]["body_sha256"] = sha(json.dumps(body, separators=(",", ":")).encode())
            crop["tables"] = transcription.parse(crop["transcription_response"], bounds)["tables"]
            write_json(path / f"p0-request-{index}.json", body)
            crops.append(crop)
        page["transcription_regions"] = crops
        page["proposal_count"] = 2
        page["layout_detection"]["boxes"] = [c["detector_box"] for c in crops]
        state = compose(crops, page["viewport"])
        page["tables"] = state["tables"]
        write_json(path / "p0-result.json", page)
        write_json(path / "p0-structure.json", state)
        (path / "p0.md").write_text(transcription.markdown(state))
        report = json.loads((path / "report.json").read_bytes())
        report["results"][0] = page
        write_json(path / "report.json", report)
    output = tmp_path / "atomic"
    report = runner.run(paths, trusts, output, config(), Client(tmp_path, fail_at=1))
    page = report["results"][0]
    assert page["ranking_status"] == "failed_retained_first"
    assert page["ranking_regions"][0]["ranking_status"] == "discarded_atomic_failure"
    assert page["ranking_regions"][1]["ranking_status"] == "failed_retained_first"
    assert report["incremental_ranking"]["ledger_attempts"] == 2
    assert (output / "p0-structure.json").read_bytes() == (paths[0] / "p0-structure.json").read_bytes()
    assert (output / "p0.md").read_bytes() == (paths[0] / "p0.md").read_bytes()


def test_reviewed_historical_parser_needs_explicit_independent_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, _, trusted = baseline(first, "first")
    _, _, other = baseline(second, "second")
    path = first / "code/pipeline_vision_transcription.py"
    path.write_bytes(path.read_bytes() + b"\n# Mock historical error-message-only adapter.\n")
    digest = sha(path.read_bytes())
    trusted["pipeline_vision_transcription.py"] = digest
    frozen = json.loads((first / "frozen.json").read_bytes())
    frozen["code_sha256"]["pipeline_vision_transcription.py"] = digest
    write_json(first / "frozen.json", frozen)
    with pytest.raises(ValueError, match="current strict"):
        runner.authenticate(first, trusted)
    with pytest.raises(ValueError, match="explicit root"):
        runner.authenticate(first, trusted, reviewed_parser_sha256=(digest,))
    # Simulate root reviewing this synthetic adapter, without executing archived code.
    monkeypatch.setattr(runner, "ROOT_REVIEWED_PARSER_SHA256", frozenset({digest}))
    with pytest.raises(ValueError, match="independent trusted"):
        runner.authenticate(first, {}, reviewed_parser_sha256=(digest,))
    result = runner.run(
        [first, second],
        [trusted, other],
        tmp_path / "reviewed",
        config(reviewed_parser_sha256=[digest]),
        Client(tmp_path),
    )
    assert result["results"][0]["ranking_status"] == "completed"
    archived = json.loads((tmp_path / "reviewed/frozen.json").read_bytes())
    assert archived["config"]["reviewed_parser_sha256"] == [digest]
    assert archived["code_sha256"]["pipeline_vision_transcription.py"] == sha(Path(transcription.__file__).read_bytes())


def test_candidate_concurrent_factory_is_root_client_and_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bench import p003_client  # noqa: PLC0415

    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first")
    _, _, b = baseline(second, "second")
    client, called = Client(tmp_path), []

    def factory() -> Client:
        called.append(True)
        return client

    monkeypatch.setattr(p003_client, "P003ConcurrentClient", factory)
    report = runner.run([first, second], [a, b], tmp_path / "concurrent", config(transport_concurrency=3))
    assert called == [True]
    assert report["config"]["transport_concurrency"] == 3
    assert report["metrics"]["concurrency"] == 1
    frozen = json.loads((tmp_path / "concurrent/frozen.json").read_bytes())
    assert "decision_concurrent.py" in frozen["code_sha256"]
    with pytest.raises(ValueError, match="concurrency"):
        runner.run([first, second], [a, b], tmp_path / "bad-control", config(transport_concurrency=2), client)


def test_difference_treatment_exact_request_and_atomic_capacity(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    _, original, trust0 = baseline(first, "first")
    _, _, trust1 = baseline(second, "second")
    client = Client(tmp_path)
    output = tmp_path / "diff"
    report = runner.run(
        [first, second], [trust0, trust1], output, config(evidence_mode="differences", evidence_max_bytes=4096), client
    )
    page = report["results"][0]
    assert page["tables"][0]["values"][1][0] == "second"
    evidence = json.loads(client.bodies[0]["state"])
    assert len(evidence["differing_slots"]) == 1
    assert (output / "p0-selector-0-evidence.json").exists()
    assert "p003_candidate_diff.py" in json.loads((output / "frozen.json").read_bytes())["code_sha256"]
    fail_client = Client(tmp_path)
    output = tmp_path / "capacity"
    report = runner.run(
        [first, second],
        [trust0, trust1],
        output,
        config(evidence_mode="differences", evidence_max_bytes=1),
        fail_client,
    )
    assert fail_client.bodies == []
    page = report["results"][0]
    assert page["ranking_status"] == "failed_retained_first"
    assert page["ranking_regions"][0]["ranking_status"] == "evidence_capacity_retained_first"
    assert page["calls"] == original["calls"]
    assert (output / "p0-structure.json").read_bytes() == (first / "p0-structure.json").read_bytes()


def test_precall_admission_failure_is_not_labeled_duplicate_pool(tmp_path: Path) -> None:
    class RefusingClient(Client):
        def request(self, body: dict[str, Any], **options: Any) -> dict[str, Any]:  # noqa: ANN401
            assert set(body["questions"]) == {"q0"}
            assert options["replay"] is False
            msg = "Request exceeds frozen model/input admission"
            raise ValueError(msg)

    first, second = tmp_path / "first", tmp_path / "second"
    _, _, a = baseline(first, "first")
    _, _, b = baseline(second, "second")
    output = tmp_path / "refused"
    report = runner.run([first, second], [a, b], output, config(), RefusingClient(tmp_path))
    page = report["results"][0]
    assert page["ranking_status"] == "failed_retained_first"
    assert page["ranking_regions"][0]["ranking_status"] == "failed_retained_first"
    assert len(page["ranking_regions"][0]["pool"]["candidates"]) == 2
    assert report["incremental_ranking"]["ledger_attempts"] == 0
    assert (output / "p0.md").read_bytes() == (first / "p0.md").read_bytes()
