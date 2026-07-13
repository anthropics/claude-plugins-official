"""Convention-based discovery for Turkish legal-source providers.

Add a provider by creating one module in this package with one concrete
``BaseLegalSourceProvider`` subclass. No registry edit is required.
"""
from __future__ import annotations

from importlib import import_module
from inspect import getmembers, isclass
from pkgutil import iter_modules

from .base import BaseLegalSourceProvider, LegalSourceProvider


def discover_legal_source_providers() -> list[LegalSourceProvider]:
    """Instantiate every concrete provider module in deterministic order."""
    providers: list[LegalSourceProvider] = []
    package_name = __package__
    package = import_module(package_name)
    for module_info in sorted(iter_modules(package.__path__), key=lambda item: item.name):
        if module_info.name.startswith("_") or module_info.name in {"base", "registry"}:
            continue
        module = import_module(f"{package_name}.{module_info.name}")
        for _, candidate in getmembers(module, isclass):
            if candidate is not BaseLegalSourceProvider and issubclass(
                candidate, BaseLegalSourceProvider
            ):
                providers.append(candidate())
    return providers
