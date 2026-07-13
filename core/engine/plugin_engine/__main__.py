"""Run with: python -m core.engine.plugin_engine [repo_root]

Prints a full discover -> load -> validate -> register -> coverage report
for the given repository (defaults to the current working directory).
This is the engine's own smoke test: it is meant to be run against a real
checkout, not a mock, and its exit code is 0 only if every discovered
plugin reached the ACTIVE lifecycle state.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .loader import PluginEngine


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    repo_root = Path(argv[0]).resolve() if argv else Path.cwd()

    engine = PluginEngine(repo_root)
    report = engine.load_all()
    for line in report.summary_lines():
        print(line)

    failed = [lp for lp in report.loaded if lp.errors]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
