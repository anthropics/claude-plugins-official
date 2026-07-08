"""Value objects for a country's concrete MCP tool bindings."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class McpServerBinding:
    capability_id: str
    tier: str
    server_name: str
    url: str
    transport: str
    auth_type: str
    coverage_notes: str = ""
    degrades_gracefully: bool = False
