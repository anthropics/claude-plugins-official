"""Reusable MCP-source search tool base; transport is injected, never embedded."""
from __future__ import annotations

from typing import Any

from ..client import McpClient
from .base import BaseMcpTool


class SourceSearchTool(BaseMcpTool):
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Arama sorgusu"}},
        "required": ["query"],
        "additionalProperties": False,
    }
    source_tool_name: str

    def __init__(self, client: McpClient):
        self._client = client

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments["query"]
        if not self._client.is_reachable():
            raise ConnectionError(f"{self.name} için MCP kaynağı erişilebilir değil")
        return self.result(self._client.call_tool(self.source_tool_name, query=query))

