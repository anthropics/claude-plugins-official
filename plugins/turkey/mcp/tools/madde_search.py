"""Independent MCP tool for article-level lookup inside supplied text."""
from __future__ import annotations

import re
from typing import Any

from .base import BaseMcpTool


class MaddeSearchTool(BaseMcpTool):
    name = "turkey_madde_search"
    description = "Verilen hukuk metninde madde numarasını ve ilgili metni arar."
    input_schema = {
        "type": "object",
        "properties": {"text": {"type": "string"}, "article": {"type": "string"}},
        "required": ["text", "article"],
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        pattern = re.compile(rf"(?:MADDE|Madde|m\.)\s*{re.escape(arguments['article'])}\b[^\n]*(?:\n(?!MADDE|Madde).*)*", re.I)
        return self.result({"matches": pattern.findall(arguments["text"])})

