"""Independent MCP tool for Turkish statute and court citations."""
from __future__ import annotations

from typing import Any

from .base import BaseMcpTool


class CitationGeneratorTool(BaseMcpTool):
    name = "turkey_citation_generator"
    description = "Türk kanun veya mahkeme kararı için atıf biçimi üretir."
    input_schema = {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["statute", "case"]},
            "instrument": {"type": "string"},
            "section": {"type": "string"},
            "court": {"type": "string"},
            "case_no": {"type": "string"},
            "decision_no": {"type": "string"},
            "decided_on": {"type": "string"},
        },
        "required": ["kind"],
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if arguments["kind"] == "statute":
            citation = f"{arguments['instrument']} m.{arguments['section']}"
        else:
            parts = [arguments.get("court", "Yargıtay")]
            if arguments.get("case_no"):
                parts.append(f"{arguments['case_no']} E.")
            if arguments.get("decision_no"):
                parts.append(f"{arguments['decision_no']} K.")
            if arguments.get("decided_on"):
                parts.append(f"{arguments['decided_on']} T.")
            citation = ", ".join(parts)
        return self.result({"citation": citation, "verification_required": True})

