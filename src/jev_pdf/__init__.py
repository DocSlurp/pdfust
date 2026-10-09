"""PDF editing, rendering, extraction and generation under the jev-pdf name.

The public API shares its implementation and object identities with the compatible
``pylopdf`` import. The Rust extension remains private to that implementation.
"""

from pylopdf import *  # noqa: F403 - re-export the complete established public API.
from pylopdf import __all__ as __all__
from pylopdf import __version__ as __version__
