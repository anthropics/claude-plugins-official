#!/usr/bin/env python3
"""Print the git remotes of the repository holding the current directory.

Usage:
  list_remotes.py

One line for each distinct address of each remote, as configured or as git rewrites
it (url.<base>.insteadOf): the remote's name, a space, and the address as an https
URL without its user name or password. The name is spelled in graphic ASCII: a
backslash, a space and whatever else is not graphic ASCII are written as escapes.
With git 2.46 or newer, an empty remote.<name>.url value clears the addresses before
it. Only an address of a plain shape is printed: an http, https, ssh, git or git+ssh
URL, or an scp-like address. Its host may hold only letters, digits, "." and "-". Its
path may hold those and "_", "~" and "/". A remote whose name begins with ".", or
that names a helper (remote.<name>.vcs), or that has a url value that holds a newline,
even a cleared one, is left out whole. A WARNING on stderr counts the remotes that are
not listed in full: those left out whole, those with an address that is not printed, and
those whose fetch address cannot be read. Another says where git cannot list the remotes.
Exits 0 in all of these cases.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# lib/ lies beside this script, whose folder Python leaves off the import path under -I or -P.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import console, git, remote

_HOST, _PATH = r"[A-Za-z0-9.-]+", r"[A-Za-z0-9._~/-]+"
_SCHEME = "|".join(map(re.escape, sorted(remote.SCHEMES)))
_PLAIN = re.compile(
    rf"(?:{_SCHEME})://(?:[^/@?#\s]*@)?{_HOST}(?::[0-9]+)?/{_PATH}"
    rf"|(?:[A-Za-z0-9._-]+@)?{_HOST}:{_PATH}"
)


def _addresses(name: str, keys: frozenset[str]) -> set[str | None]:
    """The addresses of a remote that may be printed, and a None among them where the remote is
    not listed in full. `keys` holds the name of every key in git's configuration."""
    if name.startswith("."):
        return {None}
    if f"remote.{name}.vcs" in keys:
        return {None}
    configured = git.run(".", "config", "-z", "--get-all", git.argument(f"remote.{name}.url"))
    rewritten = git.run(".", "remote", "get-url", "--all", "--", git.argument(name), exact=True)
    if configured is None or rewritten is None:
        return {None}
    if "\n" in configured:
        return {None}
    live = set(configured.rpartition("\0\0")[2].split("\0")) - {""}
    if not live:
        return {None}
    raws = live | set(rewritten.split("\n")) - {""}
    return {remote.sanitize(raw) if _PLAIN.fullmatch(raw) else None for raw in raws}


def spelled(name: str) -> str:
    """A remote's name, with a backslash, a space and what is not graphic ASCII as escapes."""
    return name.encode("unicode_escape").decode("ascii").replace(" ", r"\x20")


def main() -> int:
    names = git.run(".", "remote", exact=True)
    listed = git.run(".", "config", "-z", "--name-only", "--list")
    if names is None or listed is None:
        console.warn("git could not list the remotes here")
        return 0
    keys = frozenset(listed.split("\0"))
    left_out = 0
    for name in filter(None, names.split("\n")):
        found = _addresses(name, keys)
        if None in found:
            left_out += 1
        for address in sorted(filter(None, found)):
            if sys.stdout:
                sys.stdout.buffer.write(f"{spelled(name)} {address}\n".encode("ascii"))
    if left_out:
        some = "1 remote is" if left_out == 1 else f"{left_out} remotes are"
        console.warn(
            f"{some} not listed in full: "
            "an address that cannot be read, or cannot be shown safely, is left out"
        )
    return 0


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main())
