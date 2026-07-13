"""Adapter for Yargıtay Karar Arama (karararama.yargitay.gov.tr).

Honest by design: no live MCP/HTTP wiring exists yet in this repository
(see countries/tr/mcp/mcp-tool-registry.tr.yaml -- degrades_gracefully:
false for this exact binding). `is_available()` therefore always returns
False and `search()` raises rather than fabricate results. Swapping in a
real network-calling implementation later requires no change to
TurkishSearchProvider (Open/Closed Principle) -- only this file, since
both versions satisfy the same LegalResearchAdapter protocol (Liskov
Substitution)."""
from __future__ import annotations

from typing import Any


class YargitayKararAramaAdapter:
    source_id = "yargitay"

    def is_available(self) -> bool:
        return False

    def search(self, query: str) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "Yargıtay Karar Arama adapter is documented but not yet wired to a "
            "live MCP server -- see countries/tr/mcp/mcp-tool-registry.tr.yaml"
        )
