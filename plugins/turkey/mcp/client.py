"""MCP client seam -- the boundary a real MCP transport would plug into.

`UnavailableMcpClient` is a Null Object: a Liskov-substitutable stand-in
for a future real client. Every method behaves exactly like a real client
that simply cannot reach its server -- never like success. Higher layers
code against `McpClient` today and receive a working implementation later
with no call-site changes (Open/Closed Principle)."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class McpClient(Protocol):
    def is_reachable(self) -> bool: ...

    def call_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]: ...


class UnavailableMcpClient:
    def __init__(self, reason: str = "no MCP transport configured for this binding yet"):
        self._reason = reason

    def is_reachable(self) -> bool:
        return False

    def call_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        raise ConnectionError(f"cannot call {tool_name!r}: {self._reason}")
