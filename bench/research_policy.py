"""Independent paid-admission bounds for the explicitly authorized P003 wave."""

from __future__ import annotations

import math
import time
from typing import Any

P003_LIMIT_USD = 180.0
P003_PAID_CUTOFF = 1791684720.0  # 2026-10-11 02:12 UTC; final report due 02:27.
P003_EXTENSION_PREFIX = "P003/extension-v1-"
P003_EXTENSION_CUTOFF = 1791741120.0  # 2026-10-11 17:52 UTC; report due 18:07.


def admit_wave(ledger: dict[str, Any], tag: str, reservation: float) -> None:
    """Check under the caller's ledger lock, before reserving or transmitting.

    Historic waves keep their existing admission behavior. P003 counts every
    retained charge and unresolved reservation, across providers and processes.
    """
    if tag.split("/", 1)[0] != "P003":
        return
    # The user's continuation (extended 2026-10-11 to 18:07 UTC) authorizes new
    # extension experiments without reviving historical queues.
    cutoff = P003_EXTENSION_CUTOFF if tag.startswith(P003_EXTENSION_PREFIX) else P003_PAID_CUTOFF
    if time.time() >= cutoff:
        message = "P003 paid-admission deadline reached"
        raise RuntimeError(message)
    amounts = [reservation]
    amounts.extend(
        row["accounted_usd"] for row in ledger["requests"] if row.get("tag", "").split("/", 1)[0] == "P003"
    )
    if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or v < 0 for v in amounts):
        message = "P003 accounting requires finite nonnegative amounts"
        raise ValueError(message)
    if math.fsum(amounts) > P003_LIMIT_USD:
        message = "P003 reservation exceeds its USD 180 wave cap"
        raise RuntimeError(message)
