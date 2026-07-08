"""Adapter for the Resmi Gazete (Official Gazette) archive. Same honest,
not-yet-wired posture as yargitay_adapter.py -- see that module's
docstring for the rationale."""
from __future__ import annotations

from typing import Any


class ResmiGazeteAdapter:
    source_id = "resmi-gazete"

    def is_available(self) -> bool:
        return False

    def search(self, query: str) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "Resmi Gazete adapter is documented but not yet wired to a live "
            "MCP server -- see countries/tr/mcp/mcp-tool-registry.tr.yaml"
        )
