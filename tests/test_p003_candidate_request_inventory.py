"""Failed generation tails must not invent original request files."""

import pytest
from bench.p003_report import candidate_original_requests


def test_failed_page_tail_preserves_only_actual_requests() -> None:
    page = {"id": "page", "status": "error", "transcription_regions": [
        {"status": "error", "request_index": 0, "request": {"body_sha256": "actual"}},
        {"status": "not_requested", "request_index": 1, "request": None, "call_indexes": []},
    ]}
    assert candidate_original_requests(page) == {"page-request-0.json"}


@pytest.mark.parametrize(("field", "value"), [("request", {}), ("call_indexes", [0])])
def test_never_requested_cannot_hide_attempt_evidence(field: str, value: object) -> None:
    crop = {"status": "not_requested", "request_index": 1, "request": None, "call_indexes": []}
    crop[field] = value
    with pytest.raises(ValueError, match="attempted request"):
        candidate_original_requests({"id": "page", "status": "error", "transcription_regions": [crop]})


def test_successful_page_cannot_have_unrequested_crops() -> None:
    with pytest.raises(ValueError, match="successful page"):
        candidate_original_requests({"id": "page", "status": "ok", "transcription_regions": [
            {"status": "not_requested", "request_index": 1, "request": None, "call_indexes": []},
        ]})
