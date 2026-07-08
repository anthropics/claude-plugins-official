"""YAML file parsing -- the only module in this package that imports
`yaml` directly, so a future change of YAML library touches one file
(Single Responsibility)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class YamlFileParser:
    """Parses a YAML file into a dict.

    Raises FileNotFoundError / yaml.YAMLError verbatim -- this class does
    not swallow or reinterpret errors; callers (config/, sources/, mcp/)
    decide how to handle a missing or malformed file.
    """

    def parse(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
