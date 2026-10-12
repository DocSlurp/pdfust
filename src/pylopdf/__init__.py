"""Compatibility import for the former ``pylopdf`` name; use ``pdfust``.

The public API shares its implementation and object identities with ``pdfust``.
``PylopdfWarning`` remains an alias of ``pdfust.PdfustWarning``.
"""

from pdfust import *  # noqa: F403 - re-export the complete established public API.
from pdfust import PdfustWarning as PylopdfWarning
from pdfust import __all__ as _pdfust_all
from pdfust import __version__ as __version__

__all__ = [*_pdfust_all, "PylopdfWarning"]  # noqa: PLE0604 - extend the star-imported list.
