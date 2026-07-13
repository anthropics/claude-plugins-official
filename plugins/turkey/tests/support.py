"""Test-only helpers that avoid coupling unit tests to optional engine dependencies."""
from __future__ import annotations

import sys
from types import ModuleType


def ensure_core_imports() -> None:
    """Allow contract-only tests when the optional ``jsonschema`` package is absent."""
    try:
        import jsonschema  # noqa: F401
    except ModuleNotFoundError:
        sys.modules.setdefault("jsonschema", ModuleType("jsonschema"))
