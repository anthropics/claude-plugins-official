"""Shared contract for Turkish external legal-source providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LegalSourceProvider(Protocol):
    """The uniform interface implemented by every legal source provider."""

    source_id: str
    source_name: str
    source_type: str

    def is_available(self) -> bool: ...

    def search(self, query: str) -> list[dict[str, Any]]: ...


class BaseLegalSourceProvider(ABC):
    """Honest default for a documented source without a live connector."""

    source_id: str
    source_name: str
    source_type: str

    def is_available(self) -> bool:
        return False

    def search(self, query: str) -> list[dict[str, Any]]:
        raise NotImplementedError(
            f"{self.source_name} provider is documented but not yet wired to a live connector"
        )

