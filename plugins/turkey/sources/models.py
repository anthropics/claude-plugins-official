"""Value objects for the Legal Source Registry layer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CitationFormat:
    pattern_description: str
    example: str = ""


@dataclass(frozen=True)
class LegalSource:
    source_id: str
    name: str
    source_type: str
    citation_format: CitationFormat
    primary_url_pattern: str = ""
    tier: str = "free"
    notes: str = ""
    hierarchy_level: str = ""
