"""Minimal MCP Tools standard contract for Turkey plugin tools."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class McpTool(Protocol):
    name: str
    description: str
    input_schema: dict[str, Any]

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]: ...


class BaseMcpTool(ABC):
    """Implements MCP ``tools/list`` metadata and ``tools/call`` responses."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    def result(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
            "structuredContent": data,
        }

    @abstractmethod
    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]: ...

