"""Root-owned serial research client that stops an arm after a transport failure."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator  # noqa: TC003 - context manager annotation.
from contextlib import ExitStack, contextmanager
from pathlib import Path  # noqa: TC003 - constructor public type.
from typing import Any

from bench.decision_hosted import DecisionClient


@contextmanager
def transport_slot(directory: Path, *, enabled: bool = False, timeout: float = 120.0) -> Iterator[float]:
    """Bound waiting outside paid admission with three process-safe Linux locks.

    This reserves no money and transmits nothing. The ledger independently
    enforces its existing three-request limit after a slot is acquired.
    """
    if not enabled:
        yield 0.0
        return
    import fcntl  # noqa: PLC0415 - opt-in Linux research scheduler only.

    started = time.monotonic()
    with ExitStack() as stack:
        handles = [stack.enter_context((directory / f"p003-transport-slot-{i}.lock").open("a+b")) for i in range(3)]
        while time.monotonic() - started < timeout:
            for handle in handles:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                try:
                    yield time.monotonic() - started
                    return
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            time.sleep(0.05)
    message = "P003 transport slot wait expired before any paid admission"
    raise TimeoutError(message)


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
            base, max_inflight=3, wave_limits={"P003": 280.0}, opener=opener, allow_matched_replicates=True,
        )
        self.root, self.directory, self.ledger = base.root, base.directory, base.ledger
        self.stopped = False
        slot_mode = os.environ.get("JEV_P003_TRANSPORT_SLOTS")
        if slot_mode not in (None, "3"):
            message = "P003 transport slots must be absent or exactly three"
            raise ValueError(message)
        self.wait_for_slot = slot_mode == "3"

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        """Settle independently reserved calls; stop this arm after any error."""
        self.ensure_active()
        try:
            with transport_slot(self.directory, enabled=self.wait_for_slot) as waited:
                result = self._concurrent.request(body, **kwargs)
            if self.wait_for_slot:
                result["transport_admission"] = {
                    "slots": 3, "wait_seconds": waited,
                    "scope": "Local pre-admission wait; excluded from provider latency and no extra request",
                }
            return result  # noqa: TRY300 - circuit covers slot, transport and annotation failures.
        except Exception:
            self.stopped = True
            raise
