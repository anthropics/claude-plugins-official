"""Statute citation formatting. Single Responsibility: turn a
(instrument, section, subsection) triple into Turkey's standard citation
string -- "[Kanun No] sayılı [Kanun Adı] m.[Madde No]". Nothing else."""
from __future__ import annotations


class TurkishStatuteCitationFormatter:
    def format(self, instrument: str, section: str, subsection: str | None = None) -> str:
        citation = f"{instrument} m.{section}"
        if subsection:
            citation += f"/{subsection}"
        return citation
