"""Selected-only visuals must never inherit retained fallback quality."""

from typing import Any

import pytest
from bench.p003_candidate_visual_review import selected_page
from bench.p003_visual_review import digest
from bench.silver import canonical


def test_selected_only_control_does_not_read_fallback_tables() -> None:
    """An abstained blank control stays empty despite a retained fallback table."""
    predictions = [{"id": "dev-page", "tables": [], "selected_model_regions": 0}]
    audit: dict[str, Any] = {
        "entry": {"primary_predictions_sha256": digest(canonical(predictions))},
        "primary_predictions": predictions,
        "results": [{"id": "dev-page", "tables": [{"values": [["fallback"]]}]}],
    }
    assert selected_page(audit, "dev-page")["tables"] == []
    audit["primary_predictions"][0]["tables"] = [{"values": [["fallback"]]}]
    with pytest.raises(ValueError, match="identity changed"):
        selected_page(audit, "dev-page")
