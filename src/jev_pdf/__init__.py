"""Compatibility import for the former ``jev-pdf`` distribution name; use ``pdfust``.

The public API shares its implementation and object identities with ``pdfust``.
"""

from pdfust import *  # noqa: F403 - re-export the complete established public API.
from pdfust import __all__ as __all__
from pdfust import __version__ as __version__
