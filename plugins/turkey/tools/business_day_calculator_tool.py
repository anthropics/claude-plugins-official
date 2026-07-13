"""Computes N business days from a date, honoring Turkey's weekend
definition from Country Config -- the 'calendar-deadline' Tool Registry
capability. Genuinely self-contained logic (no external system dependency).

Note on day-numbering conventions: countries/tr/country.config.yaml uses
0=Pazar(Sunday)...6=Cumartesi(Saturday) (see config/country_config.py's
BusinessCalendar docstring), while Python's `date.weekday()` is
Monday-first (0=Monday). `date.isoweekday() % 7` converts correctly:
Monday->1, ..., Saturday->6, Sunday->7%7=0 -- matching our Sunday-first
convention exactly.
"""
from __future__ import annotations

from datetime import date, timedelta

from ..config.country_config import TurkeyCountryConfig


class BusinessDayCalculatorTool:
    name = "calendar-deadline"

    def __init__(self, country_config: TurkeyCountryConfig):
        self._weekend_days = set(country_config.business_calendar.weekend_days)

    def _is_weekend(self, day: date) -> bool:
        return (day.isoweekday() % 7) in self._weekend_days

    def run(self, start: date, business_days: int) -> date:
        current = start
        step = 1 if business_days >= 0 else -1
        remaining = abs(business_days)
        while remaining > 0:
            current += timedelta(days=step)
            if not self._is_weekend(current):
                remaining -= 1
        return current
