"""Optional isolated codec gates and unchanged synthetic accounting flow."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from bench import decision_concurrent as concurrent
from bench import decision_hosted as hosted
from bench import p003_json_codec_perf as perf


@pytest.fixture
def codec():  # noqa: ANN201 - optional native module.
    directory = Path.home() / ".cache/jev-pdf-p003-codec/orjson-3.13.0"
    if not directory.is_dir():
        pytest.skip("Explicit isolated pinned codec not installed; no project dependency")
    return perf.load_codec(directory)


def test_exact_type_and_float_bit_comparison() -> None:
    assert not perf.exact(1, 1.0)
    assert not perf.exact(True, 1)
    assert not perf.exact(-0.0, 0.0)
    assert perf.exact({"float": -0.0}, {"float": -0.0})


def test_nonfinite_never_silently_becomes_null(codec) -> None:  # noqa: ANN001 - native module fixture.
    facade = perf.CodecFacade(codec)
    for value in (math.nan, math.inf, -math.inf):
        encoded = facade.dumps({"value": value}, ensure_ascii=False, indent=2)
        assert "null" not in encoded
        decoded = facade.loads(encoded)["value"]
        assert perf.exact(value, decoded)
        with pytest.raises(ValueError, match="Out of range"):
            facade.dumps(value, allow_nan=False)
    assert facade.counts["dumps_stdlib_unsafe_tree"] == 3


def test_boundaries_preserve_exact_integer_float_unicode_and_request_bytes(codec) -> None:  # noqa: ANN001
    facade = perf.CodecFacade(codec)
    for value in (2 ** 53 + 1, 2 ** 63, 2 ** 64 - 1, 2 ** 64, -(2 ** 63) - 1,
                  10 ** 100, -0.0, 5e-324, 1.7976931348623157e308, "surrogate\ud800"):
        assert perf.exact(value, facade.loads(facade.dumps(value, ensure_ascii=False, indent=2)))
    body = {"model": "independent", "state": "Unicode Δ", "value": 0.3}
    assert facade.dumps(body, separators=(",", ":"), allow_nan=False) == json.dumps(
        body, separators=(",", ":"), allow_nan=False)
    assert perf.compatibility(codec, 1000)["exact_fixture_roundtrip"]


def test_scoped_override_restores_references_on_error(codec) -> None:  # noqa: ANN001
    before = hosted.json, concurrent.json
    def interrupted() -> None:
        with perf.isolated_override(perf.CodecFacade(codec)):
            assert hosted.json is concurrent.json
            message = "synthetic interruption"
            raise RuntimeError(message)
    with pytest.raises(RuntimeError, match="synthetic"):
        interrupted()
    assert (hosted.json, concurrent.json) == before


