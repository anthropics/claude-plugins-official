"""One-module-per-source providers for Turkish legal authorities.

Create a new module containing one ``BaseLegalSourceProvider`` subclass to
make it available to the Turkey plugin automatically.
"""

from .base import BaseLegalSourceProvider, LegalSourceProvider
from .registry import discover_legal_source_providers

__all__ = [
    "BaseLegalSourceProvider",
    "LegalSourceProvider",
    "discover_legal_source_providers",
]
