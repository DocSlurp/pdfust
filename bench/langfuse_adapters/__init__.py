"""Experiment adapters for the Langfuse backfill.

Every module in this package that defines ``NAME`` and
``collect(artifacts: Path) -> Iterable[Experiment]`` is discovered
automatically. See ``base.py`` for the data shape and adapter rules.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


def discover() -> list[ModuleType]:
    """Import every adapter module in this package."""
    modules = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda info: info.name):
        if info.name.startswith("_") or info.name == "base":
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(module, "NAME") and hasattr(module, "collect"):
            modules.append(module)
    return modules
