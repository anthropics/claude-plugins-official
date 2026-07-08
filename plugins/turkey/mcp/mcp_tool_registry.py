"""Loads countries/tr/mcp/mcp-tool-registry.tr.yaml into typed bindings.

Single Responsibility: expose *what is configured*, never *whether it is
reachable right now* (that is Adapter.is_available()'s job -- see
adapters/base.py)."""
from __future__ import annotations

from pathlib import Path

from ..parser.yaml_parser import YamlFileParser
from ..paths import MCP_TOOL_REGISTRY_PATH
from .models import McpServerBinding


class TurkishMcpToolRegistry:
    def __init__(
        self,
        path: Path = MCP_TOOL_REGISTRY_PATH,
        parser: YamlFileParser | None = None,
    ):
        self._parser = parser or YamlFileParser()
        self._path = path
        self._bindings: list[McpServerBinding] | None = None

    def _load(self) -> list[McpServerBinding]:
        if self._bindings is None:
            raw = self._parser.parse(self._path)
            bindings: list[McpServerBinding] = []
            for entry in raw.get("bindings", []):
                server = entry.get("mcp_server", {}) or {}
                bindings.append(
                    McpServerBinding(
                        capability_id=entry["capability_id"],
                        tier=entry.get("tier", "free"),
                        server_name=server.get("name", ""),
                        url=server.get("url", ""),
                        transport=server.get("transport", "http"),
                        auth_type=entry.get("auth_type", "none"),
                        coverage_notes=entry.get("coverage_notes", ""),
                        degrades_gracefully=bool(entry.get("degrades_gracefully", False)),
                    )
                )
            self._bindings = bindings
        return self._bindings

    def get_bindings(self, capability_id: str) -> list[McpServerBinding]:
        return [b for b in self._load() if b.capability_id == capability_id]

    def all(self) -> list[McpServerBinding]:
        return list(self._load())
