"""The start file: a small file in ~/.local/bin that starts the installed plugin's CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from lib import plugin

from . import sandbox

_SOURCE = """\
#!/bin/sh
"exec" "python3" "-IS" "$0" "$@"
# Start the CLI of the installed Claude Security plugin. Outside Windows a shell runs the line
# above, and Python reads it as text. -IS keeps PYTHONPATH and .pth files from loading code.

import json
import os
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def installed():
    config = os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"
    try:
        path = Path(config, "plugins", "installed_plugins.json").expanduser()
        # A relative path would lead to the current folder, which can be the code to scan.
        if not path.is_absolute():
            return []
        records = json.loads(path.read_bytes())["plugins"][{installed!r}]
        scoped = [Path(r["installPath"]) for r in records if r["scope"] in ("user", "managed")]
        return [p for p in scoped if p.is_absolute()]
    except (OSError, RuntimeError, TypeError, ValueError, KeyError):
        return []


places = (Path(root, "scripts", "cli.py") for root in (*installed(), {root!r}))
cli = next(filter(os.path.isfile, places), None)
if cli is None:
    print("{name}: the Claude Security plugin could not be found", file=sys.stderr)
    sys.exit(2)
sys.argv[0] = str(cli)
runpy.run_path(str(cli), run_name="__main__")
"""


def install() -> str:
    """Write the start file into ~/.local/bin, and say where it is."""
    folder = Path.home() / ".local" / "bin"
    folder.mkdir(parents=True, exist_ok=True)
    source = _SOURCE.format(name=plugin.NAME, root=str(plugin.ROOT), installed=sandbox.installed())
    if os.name == "nt":
        (folder / f"{plugin.NAME}.py").write_text(source, encoding="utf-8")
        command = folder / f"{plugin.NAME}.cmd"
        command.write_text(f'@"{sys.executable}" -IS "%~dpn0.py" %*\n', encoding="utf-8")
    else:
        command = folder / plugin.NAME
        # A write through a link of this name would replace the file that the link leads to.
        command.unlink(missing_ok=True)
        command.write_text(source, encoding="utf-8")
        command.chmod(0o755)
    if folder in map(Path, os.get_exec_path()):
        return f"Installed {command}\nRun `{plugin.NAME} --help` in your shell."
    return f"Installed {command}\nAdd {folder} to your PATH to use it."
