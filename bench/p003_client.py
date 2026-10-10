"""Root-owned serial research client that stops an arm after a transport failure."""

from __future__ import annotations

from typing import Any

from bench.decision_hosted import DecisionClient


class P003DecisionClient(DecisionClient):
    """Preserve one failed reservation and prevent spending on subsequent pages."""

    stopped = False

    def ensure_active(self) -> None:
        """Reject a stopped arm without creating another reservation."""
        if self.stopped:
            message = "P003 arm stopped after a transport/admission failure; investigation required"
            raise RuntimeError(message)

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401 - match shared keyword transport.
        """Transmit through the unchanged shared ledger, stopping on any client error."""
        self.ensure_active()
        try:
            return super().request(body, **kwargs)
        except Exception:
            self.stopped = True
            raise
