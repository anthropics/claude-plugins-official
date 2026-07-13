"""Independent MCP tools for Turkish legal workflows."""

from .base import McpTool
from .registry import discover_mcp_tools

__all__ = ["McpTool", "discover_mcp_tools"]
