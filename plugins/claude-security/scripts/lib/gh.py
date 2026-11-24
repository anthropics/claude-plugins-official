"""The GitHub CLI as the review runs it: found once, run without prompts, its answer or its
complaint read back."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from . import git, strictjson
from .gfm import plain_line
from .strictjson import is_map

if TYPE_CHECKING:
    from .strictjson import JsonMap

TIMEOUT_S = 120
COMPLAINT_LIMIT = 300
_HTTP_STATUS_RE = re.compile(r"\(?HTTP ([0-9]{3})\)?\s*$", re.MULTILINE)
_COMMAND_MARK_RE = re.compile(r"#[^\x00-\x7f]*#[^\x00-\x7f]*(?=\[)")
# What gh rewrites in GitHub's answers: it prints ^[ for the character ESC, and \^[ for \u001b.
_REWRITTEN_RE = re.compile(
    r"[\x00-\x07\x0e-\x1f\x80-\x9f]"
    r"|(?<=[\\\x1c\x9c])(?:u00[19][cC])*u00(?:0[0-8cefCEF]|[189][0-9a-fA-F])"
)


def in_carets(text: str) -> str:
    """`text` in caret form, for comparing: a text and what gh prints of it have the same one."""

    def carets(found: re.Match[str]) -> str:
        codes = [int(code, 16) for code in found[0].split("u00")[1:]] or [ord(found[0])]
        return "".join("^" + chr(code % 32 + 64) for code in codes)

    return _REWRITTEN_RE.sub(carets, text)


class GhRun(NamedTuple):
    """One GitHub CLI call's exit code, stdout and stderr."""

    code: int
    out: str
    err: str

    @property
    def status(self) -> int | None:
        """The HTTP status that ends a line of gh's error output, white space aside: the last such
        line's. None when there is none."""
        found: list[str] = _HTTP_STATUS_RE.findall(self.err)
        return int(found[-1]) if found else None

    def complaint(self) -> str:
        """One line saying why the call failed: gh's error output, clipped to COMPLAINT_LIMIT with
        its HTTP status kept, or how gh ended. It holds no ##[, but it can start with ::, so print
        words of your own before it."""
        silent = f"gh exited with status {self.code} and printed no error message"
        text = plain_line(self.err) or silent
        line = _COMMAND_MARK_RE.sub(r"\g<0> ", text)
        if len(line) <= COMPLAINT_LIMIT:
            return line
        status = self.status
        return line[:COMPLAINT_LIMIT] + "…" + (f" (HTTP {status})" if status else "")

    def all_records(self) -> list[JsonMap] | None:
        """Each non-empty line of the output, parsed; None when one of them is not a JSON object."""
        found: list[JsonMap] = []
        # splitlines() also splits at U+0085, U+2028 and U+2029, which a JSON string may hold raw.
        for line in filter(None, self.out.split("\n")):
            try:
                value = strictjson.loads(line)
            except ValueError:
                return None
            if not is_map(value):
                return None
            found.append(value)
        return found


class Gh(NamedTuple):
    """A GitHub CLI that may be run: the path locate() found."""

    exe: str

    def run(self, *args: str, stdin: str | None = None) -> GhRun:
        """One GitHub CLI call to the job's own server, with prompts, update checks and forced
        colour off, TIMEOUT_S seconds at most."""
        env = dict(
            os.environ,
            # Else gh sends the job's token to github.com, or to the job's own GH_HOST.
            GH_HOST=os.environ.get("GITHUB_SERVER_URL", "").partition("://")[2],
            GH_PROMPT_DISABLED="1",
            GH_NO_UPDATE_NOTIFIER="1",
            CLICOLOR_FORCE="0",
            GH_FORCE_TTY="",
        )
        try:
            out = subprocess.run(
                [self.exe, *args],
                env=env,
                input=None if stdin is None else stdin.encode("utf-8"),
                capture_output=True,
                timeout=TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            return GhRun(1, "", str(error))
        return GhRun(
            out.returncode,
            out.stdout.decode("utf-8", "replace"),
            out.stderr.decode("utf-8", "replace"),
        )


def locate() -> Gh | str:
    """The gh that PATH resolves, unless it, or the folder where PATH finds it, lies inside the
    checkout under review once links are followed; else the reason there is none to run."""
    exe = shutil.which("gh")
    if exe is None:
        return "the GitHub CLI (gh) is not on PATH"
    top = os.path.realpath(git.toplevel(os.curdir) or os.curdir)
    # Its folder too: a link named gh there can lead to a program that runs the checkout's files.
    if any(Path(os.path.realpath(at)).is_relative_to(top) for at in (exe, Path(exe).parent)):
        return (
            f"PATH resolves gh to {exe}, inside the checkout under review or linked into it; "
            "only a gh installed outside it can be run"
        )
    return Gh(exe)
