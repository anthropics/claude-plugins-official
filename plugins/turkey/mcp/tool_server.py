"""Small MCP ``tools/list`` and ``tools/call`` dispatch surface."""
from __future__ import annotations

from typing import Any

from .client import McpClient, UnavailableMcpClient
from .tools import McpTool, discover_mcp_tools


class TurkeyMcpToolServer:
    def __init__(self, client: McpClient | None = None, tools: list[McpTool] | None = None):
        self._tools = tools or discover_mcp_tools(client or UnavailableMcpClient())
        self._by_name = {tool.name: tool for tool in self._tools}

    def list_tools(self) -> list[dict[str, Any]]:
        return [tool.definition() for tool in self._tools if hasattr(tool, "definition")]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._by_name[name].execute(arguments)
        except KeyError as error:
            raise ValueError(f"Unknown Turkey MCP tool: {name}") from error
