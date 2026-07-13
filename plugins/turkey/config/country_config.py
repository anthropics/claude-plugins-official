"""Country Config layer: a typed view over countries/tr/country.config.yaml.

Single Responsibility: load and expose Turkey's country metadata. Contains
no citation, search, or document logic -- those layers depend on this one
(Dependency Inversion: higher layers depend on this stable, simple data
shape), never the other way around.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..parser.yaml_parser import YamlFileParser
from ..paths import COUNTRY_CONFIG_PATH


@dataclass(frozen=True)
class BusinessCalendar:
    #: Day-of-week numbers considered non-business days, using the
    #: ISO-based-but-Sunday-first convention this repo's schema documents
    #: (0=Pazar/Sunday ... 6=Cumartesi/Saturday). See tools/business_day_calculator_tool.py
    #: for the conversion from Python's Monday-first `date.isoweekday()`.
    weekend_days: tuple[int, ...]
    holiday_source: str


@dataclass(frozen=True)
class ProfessionalRegulator:
    name: str
    referral_mechanism: str = ""


@dataclass(frozen=True)
class PrivilegeDoctrine:
    exists: bool
    name: str | None = None
    statutory_basis: str | None = None
    fallback_header: str | None = None


@dataclass(frozen=True)
class TurkeyCountryConfig:
    country_code: str
    country_name: str
    languages: tuple[str, ...]
    legal_family: str
    date_format: str
    currency: str
    business_calendar: BusinessCalendar
    professional_regulator: ProfessionalRegulator
    privilege_doctrine: PrivilegeDoctrine
    default_providers: dict[str, str] = field(default_factory=dict)
    coverage: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def load_country_config(
    path: Path = COUNTRY_CONFIG_PATH, parser: YamlFileParser | None = None
) -> TurkeyCountryConfig:
    """Load and adapt countries/tr/country.config.yaml into a typed
    TurkeyCountryConfig.

    `parser` is constructor-injectable so tests can supply a fake
    FileParser without touching disk (Dependency Inversion Principle).
    """
    parser = parser or YamlFileParser()
    raw = parser.parse(path)

    calendar_raw = raw.get("business_calendar", {}) or {}
    regulator_raw = raw.get("professional_regulator", {}) or {}
    privilege_raw = raw.get("privilege_doctrine", {}) or {}

    return TurkeyCountryConfig(
        country_code=raw["country_code"],
        country_name=raw["country_name"],
        languages=tuple(raw.get("languages", [])),
        legal_family=raw["legal_family"],
        date_format=raw.get("date_format", ""),
        currency=raw.get("currency", ""),
        business_calendar=BusinessCalendar(
            weekend_days=tuple(calendar_raw.get("weekend_days", [])),
            holiday_source=calendar_raw.get("holiday_source", ""),
        ),
        professional_regulator=ProfessionalRegulator(
            name=regulator_raw.get("name", ""),
            referral_mechanism=regulator_raw.get("referral_mechanism", ""),
        ),
        privilege_doctrine=PrivilegeDoctrine(
            exists=bool(privilege_raw.get("exists", False)),
            name=privilege_raw.get("name"),
            statutory_basis=privilege_raw.get("statutory_basis"),
            fallback_header=privilege_raw.get("fallback_header"),
        ),
        default_providers=dict(raw.get("default_providers", {}) or {}),
        coverage=dict(raw.get("coverage", {}) or {}),
        raw=raw,
    )
