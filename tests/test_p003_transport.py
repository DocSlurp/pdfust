from __future__ import annotations

import pytest
from bench.decision_gateway import _validate
from bench.decision_gateway_vision import validate_wire
from bench.p003_transport import gateway_wire
from bench.pipeline_run import body


def test_d1_native_wire_preserves_text_image_and_choices() -> None:
    original = body("liquid/d1", "literal source", {"table": "table", "prose": "prose"}, "data:image/png;base64,YQ==")
    wire, native = gateway_wire(original)
    assert native
    assert wire["input"][0]["content"] == [
        {"type": "input_text", "text": "literal source"},
        {"type": "input_image", "image_url": "data:image/png;base64,YQ==", "detail": "high"},
    ]
    assert wire["questions"][0]["choices"] == [
        {"value": "table", "description": "table"}, {"value": "prose", "description": "prose"},
    ]
    validate_wire(wire, 750_000)
    assert "state" in original


def test_laya_keeps_text_and_requires_boundless() -> None:
    original = body("convaiinnovations/laya", "literal source", {"yes": "yes", "no": "no"}, None)
    wire, native = gateway_wire(original)
    assert not native
    assert wire["state"] == "literal source"
    assert wire["providerOptions"] == {"gateway": {"only": ["boundless"]}}
    _validate(wire, 750_000)


def test_laya_image_refused_instead_of_silently_discarded() -> None:
    original = body("convaiinnovations/laya", "source", {"yes": "yes"}, "data:image/png;base64,YQ==")
    with pytest.raises(ValueError, match="text-only Laya"):
        gateway_wire(original)
