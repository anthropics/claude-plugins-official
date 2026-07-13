"""Plain-markdown structural parsing for the knowledge/*.md files (these
have no YAML frontmatter -- see core.engine.plugin_engine.frontmatter for
files that do, e.g. SKILL.md and the *.interface.md contracts).

Single Responsibility: split a markdown file into (heading, body) sections
by heading level. No keyword scoring, no retrieval ranking -- that is
rag/keyword_retriever.py's job.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass(frozen=True)
class MarkdownSection:
    level: int
    heading: str
    text: str


@dataclass(frozen=True)
class MarkdownDocument:
    path: Path
    title: str
    sections: tuple[MarkdownSection, ...] = field(default_factory=tuple)


class MarkdownFileParser:
    def parse(self, path: Path) -> MarkdownDocument:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        title = path.stem
        sections: list[MarkdownSection] = []
        current_heading = ""
        current_level = 0
        buffer: list[str] = []

        def flush() -> None:
            if current_heading or buffer:
                sections.append(
                    MarkdownSection(current_level, current_heading, "\n".join(buffer).strip())
                )

        for line in lines:
            match = _HEADING_RE.match(line)
            if match:
                flush()
                level = len(match.group(1))
                heading = match.group(2).strip()
                if level == 1 and not sections:
                    title = heading
                current_heading, current_level = heading, level
                buffer = []
            else:
                buffer.append(line)
        flush()

        return MarkdownDocument(
            path=path,
            title=title,
            sections=tuple(s for s in sections if s.heading),
        )
