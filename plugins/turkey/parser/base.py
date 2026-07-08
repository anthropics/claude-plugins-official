"""Narrow FileParser protocol -- Interface Segregation Principle: callers
that only need "give me a parsed value from a path" depend on this, not on
a concrete YamlFileParser or MarkdownFileParser class."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class FileParser(Protocol[T]):
    def parse(self, path: Path) -> T: ...
