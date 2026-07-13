"""Case-law citation formatting -- the Yargıtay Esas/Karar pattern:
"Yargıtay [Daire]. Hukuk Dairesi, [Esas] E., [Karar] K., [Tarih] T."
Single Responsibility: formatting only, no lookup/search."""
from __future__ import annotations

from typing import Any


class TurkishCaseCitationFormatter:
    def format(self, **fields: Any) -> str:
        court = fields.get("court", "Yargıtay")
        chamber = fields.get("chamber")  # e.g. "9. Hukuk Dairesi"
        case_no = fields.get("case_no")  # Esas No, e.g. "2021/1234"
        decision_no = fields.get("decision_no")  # Karar No
        decided_on = fields.get("decided_on")  # e.g. "15.03.2022"

        citation = court
        if chamber:
            citation += f", {chamber}"
        if case_no:
            citation += f", {case_no} E."
        if decision_no:
            citation += f", {decision_no} K."
        if decided_on:
            citation += f", {decided_on} T."
        return citation
