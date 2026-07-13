"""Provider layer: concrete implementations of core's Citation/Search/
Document Provider protocols for Turkey."""

from .legal_sources.base import LegalSourceProvider
from .legal_sources.registry import discover_legal_source_providers

__all__ = ["LegalSourceProvider", "discover_legal_source_providers"]
