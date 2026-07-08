"""Citation risk classification. Single Responsibility: given a raw
citation string, decide how likely it is to be a fabricated/uncertain
pinpoint, using Turkey's known high-risk patterns (see
countries/tr/providers/citation-provider.tr.md)."""
from __future__ import annotations

import re

from core.engine.plugin_engine.contracts import PinpointPattern, RiskAssessment, RiskTier

_HIGH_RISK_PATTERNS: tuple[PinpointPattern, ...] = (
    PinpointPattern(
        pattern_name="madde-fikra",
        description="Madde içindeki fıkra/bent numarası",
        example="m.41/2",
    ),
    PinpointPattern(
        pattern_name="esas-karar-no",
        description="Yargıtay Esas/Karar numaraları",
        example="2021/1234 E.",
    ),
    PinpointPattern(
        pattern_name="kanun-no-karisikligi",
        description="Benzer konulu kanunların numara karışıklığı",
        example="4857 vs 6098",
    ),
)

_ESAS_KARAR_RE = re.compile(r"\d{4}/\d+\s*(E\.|K\.)")
_MADDE_FIKRA_RE = re.compile(r"m\.\d+/\d+")
_MADDE_RE = re.compile(r"\bm\.\d+\b")


class TurkishCitationRiskClassifier:
    def get_high_risk_pinpoint_patterns(self) -> list[PinpointPattern]:
        return list(_HIGH_RISK_PATTERNS)

    def classify(self, citation_text: str) -> RiskAssessment:
        if _ESAS_KARAR_RE.search(citation_text):
            return RiskAssessment(RiskTier.HIGH, "Esas/Karar numarası içeriyor")
        if _MADDE_FIKRA_RE.search(citation_text):
            return RiskAssessment(RiskTier.HIGH, "Madde/fıkra düzeyinde pinpoint atıf")
        if _MADDE_RE.search(citation_text):
            return RiskAssessment(RiskTier.MEDIUM, "Madde düzeyi atıf")
        return RiskAssessment(RiskTier.LOW, "Genel kurum/kanun adı referansı")
