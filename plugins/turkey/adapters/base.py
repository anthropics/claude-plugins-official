"""Narrower than core's generic Adapter protocol (Interface Segregation):
adds exactly the two members a SearchProvider needs (`source_id`,
`search`), nothing about document/e-signature systems."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LegalResearchAdapter(Protocol):
    source_id: str

    def is_available(self) -> bool: ...

    def search(self, query: str) -> list[dict[str, Any]]: ...
