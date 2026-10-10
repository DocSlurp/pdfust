"""Root-owned serial research client that stops an arm after a transport failure."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - constructor public type.
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


class P003ConcurrentClient(P003DecisionClient):
    """Root opt-in max-three transport with the serial arm circuit breaker.

    The exact underlying client preserves admission, accounting, and telemetry.
    Existing ledger policy must be reconciled offline by root before activation;
    this wrapper never edits policy or retries a failed request.
    """

    def __init__(self, root: Path | None = None, *, client: DecisionClient | None = None, opener: Any = None) -> None:  # noqa: ANN401
        """Construct only an exact shared client and fixed P003 admission policy."""
        from bench.decision_concurrent import ConcurrentDecisionClient  # noqa: PLC0415
        from bench.decision_hosted import ROOT  # noqa: PLC0415

        base = client if client is not None else DecisionClient(ROOT if root is None else root)
        self._concurrent = ConcurrentDecisionClient(
            base, max_inflight=3, wave_limits={"P003": 50.0}, opener=opener,
        )
        self.root, self.directory, self.ledger = base.root, base.directory, base.ledger
        self.stopped = False

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        """Settle independently reserved calls; stop this arm after any error."""
        self.ensure_active()
        try:
            return self._concurrent.request(body, **kwargs)
        except Exception:
            self.stopped = True
            raise
