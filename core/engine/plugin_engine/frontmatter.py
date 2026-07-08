"""Minimal YAML-frontmatter parser for SKILL.md / interface .md files.

Every SKILL.md and core/engine/providers/*.interface.md in this repo starts
with a `---`-delimited YAML block followed by markdown body text. This
module extracts just that block without pulling in a markdown parser
dependency the rest of the repo doesn't have.
"""
from __future__ import annotations

from pathlib import Path

import yaml

FRONTMATTER_DELIMITER = "---"


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, remaining_body) for a markdown file.

    Returns ({}, full_text) if the file has no frontmatter block, or if the
    block does not parse into a mapping.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}, text
    try:
        end_index = next(
            i for i in range(1, len(lines)) if lines[i].strip() == FRONTMATTER_DELIMITER
        )
    except StopIteration:
        return {}, text
    front_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    data = yaml.safe_load(front_text) or {}
    if not isinstance(data, dict):
        return {}, text
    return data, body
