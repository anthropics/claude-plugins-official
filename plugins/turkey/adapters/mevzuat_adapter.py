"""Adapter for the Mevzuat Bilgi Sistemi (mevzuat.gov.tr). Same honest,
not-yet-wired posture as yargitay_adapter.py -- see that module's
docstring for the rationale."""
from __future__ import annotations

from typing import Any


class MevzuatBilgiSistemiAdapter:
    source_id = "mevzuat-bilgi-sistemi"

    def is_available(self) -> bool:
        return False

    def search(self, query: str) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "Mevzuat Bilgi Sistemi adapter is documented but not yet wired to a "
            "live MCP server -- see countries/tr/mcp/mcp-tool-registry.tr.yaml"
        )
