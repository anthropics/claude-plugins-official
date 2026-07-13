"""Independent MCP tool for cautious legal-text risk flagging."""
from __future__ import annotations

import re
from typing import Any

from .base import BaseMcpTool

_RISK_PATTERNS = {
    "deadline": r"\b(süre|gün|tebliğ|zamanaşımı)\b",
    "sanction": r"\b(ceza|idari para|yaptırım)\b",
    "personal-data": r"\b(kişisel veri|kvkk|açık rıza)\b",
}


class RiskAnalyzerTool(BaseMcpTool):
    name = "turkey_risk_analyzer"
    description = "Metindeki süre, yaptırım ve kişisel veri risk sinyallerini işaretler."
    input_schema = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        text = arguments["text"]
        flags = [name for name, pattern in _RISK_PATTERNS.items() if re.search(pattern, text, re.I)]
        return self.result({"risk_flags": flags, "review_required": bool(flags)})

