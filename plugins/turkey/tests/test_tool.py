from __future__ import annotations

import unittest

from plugins.turkey.mcp import TurkeyMcpToolServer


class _McpClient:
    def is_reachable(self) -> bool:
        return True

    def call_tool(self, tool_name: str, **kwargs: str) -> dict[str, object]:
        return {"tool_name": tool_name, "query": kwargs["query"]}


class ToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = TurkeyMcpToolServer(client=_McpClient())

    def test_tools_publish_mcp_metadata(self) -> None:
        definitions = self.server.list_tools()
        self.assertEqual(len(definitions), 9)
        self.assertTrue(all("inputSchema" in definition for definition in definitions))

    def test_source_tool_delegates_to_mcp_client(self) -> None:
        result = self.server.call_tool("turkey_mevzuat_search", {"query": "İş Kanunu"})
        self.assertEqual(result["structuredContent"]["tool_name"], "mevzuat.search")

    def test_local_risk_tool_returns_structured_result(self) -> None:
        result = self.server.call_tool("turkey_risk_analyzer", {"text": "KVKK cezası ve süre"})
        self.assertIn("personal-data", result["structuredContent"]["risk_flags"])
