"""git calls, prompts suppressed, that change no file in the user's working tree and not its index:
a runner whose output is byte-faithful, `git apply --check`, and the paths that a patch names."""

from __future__ import annotations

import functools
import os
import subprocess
from pathlib import Path

REDIRECTS = frozenset({
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
})
# Under this setting git, from 2.38 on, finds no bare repository by its search.
GIT = ("git", "-c", "safe.bareRepository=explicit")
TIMEOUT = 30
APPLY_TIMEOUT = 60
# The `git diff` switches that print what git stores: no external driver, textconv or colour.
PLAIN_DIFF = ("--no-ext-diff", "--no-textconv", "--no-color")
# For `git diff` and `git log`: a configured diff.orderFile that git cannot read fails the call.
NO_ORDER_FILE = "-O/dev/null"
# The exit code of a fatal error of git: on a patch, or before git reads one.
FATAL = 128
# converter_named()'s read of git's settings, and the row of it that Git for Windows writes in the
# system's settings for every user, for documents such as *.pdf.
CONVERTER_READ = ("config", "--show-scope", "--get-regexp", r"^diff\.(.*\.textconv|submodule)$")
WINDOWS_CONVERTER = "system\tdiff.astextplain.textconv astextplain"
# A patch that git can read, so that _check() can take git's FATAL on it as no answer.
PROBE = b"--- /dev/null\n+++ b/.claude-security-probe\n@@ -0,0 +1 @@\n+probe\n"
ENV = {k: v for k, v in os.environ.items() if k not in REDIRECTS} | {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_DIFF_OPTS": "",
}


def run(
    cwd: str,
    *args: str | bytes,
    timeout: int = TIMEOUT,
    env: dict[str, str] | None = None,
    exact: bool = False,
    ok: tuple[int, ...] = (0,),
) -> str | None:
    """The stdout of `git -C <cwd> <args>` without trailing CRs and newlines; None on any failure.
    `env` adds variables for this one call.
    `exact` keeps the trailing CRs and newlines, for a caller that splits the lines itself.
    `ok` names the exit codes that are an answer."""
    try:
        out = subprocess.run(
            [*GIT, "-C", cwd, *args],
            env=ENV | (env or {}),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if out.returncode not in ok:
        return None
    text = out.stdout.decode("utf-8", "surrogateescape")
    return text if exact else text.rstrip("\r\n")


def argument(text: str) -> str | bytes:
    """`text`, a name as git spells it, in the form to hand to run as an argument: the bytes that
    git printed or, on Windows, the text itself."""
    return text if os.name == "nt" else text.encode("utf-8", "surrogateescape")


def for_disk(text: str) -> str:
    """`text`, a name as git spells it, in the form to hand to the file system."""
    return os.fsdecode(argument(text))


def from_disk(text: str) -> str:
    """`text`, a name from the file system, as git spells it: the inverse of for_disk()."""
    return text if os.name == "nt" else os.fsencode(text).decode("utf-8", "surrogateescape")


def commit_id(cwd: str, name: str) -> str | None:
    """The full id of the commit `name` resolves to in the repository holding `cwd`; None when
    it resolves to none there."""
    return run(cwd, "rev-parse", "--verify", "--quiet", f"{name}^{{commit}}")


def toplevel(cwd: str) -> str | None:
    """The top level of the work tree holding `cwd`, as git spells it; None when git names none."""
    return run(cwd, "rev-parse", "--show-toplevel") or None


def is_top(folder: str, top: str) -> bool:
    """Whether `folder` is `top`, a top level as toplevel() gives it."""
    return os.path.realpath(for_disk(top)) == os.path.realpath(folder)


def plain_fits(scan_root: str) -> bool:
    """Whether a change scan's agents can type git with no -C: the working directory is the scan
    root, the user's GIT_LITERAL_PATHSPECS is off, no GIT_DIR or GIT_COMMON_DIR is exported, and
    converter_named() answers false there. False too where either folder cannot be examined."""
    if os.environ.get("GIT_LITERAL_PATHSPECS", "").lower() not in {"", "0", "false", "no", "off"}:
        return False
    if os.environ.get("GIT_DIR") or os.environ.get("GIT_COMMON_DIR"):
        return False
    try:
        if not Path(scan_root).samefile(os.curdir):
            return False
    except OSError:
        return False
    return not converter_named(scan_root)


def converter_named(folder: str) -> bool:
    """Whether git could start a text converter in a diff of the repository that holds `folder`:
    git's settings there name a textconv converter (but Git for Windows' own) or set diff.submodule
    to diff. True too where git cannot list its settings."""
    found = run(folder, *CONVERTER_READ, env={"LC_ALL": "C"}, ok=(0, 1))
    return found is None or not all(map(starts_nothing, found.splitlines()))


def starts_nothing(row: str) -> bool:
    """Whether a row of converter_named()'s read of git's settings can start no converter."""
    if row == WINDOWS_CONVERTER:
        return True
    key, _, value = row.partition("\t")[2].partition(" ")
    return key == "diff.submodule" and value != "diff"


def holder_of(folder: str) -> Path | None:
    """The nearest folder that holds a .git: `folder`, by its real path, or one above it. None if no
    folder does. It makes no call of git."""
    here = Path(os.path.realpath(folder))
    return next((p for p in (here, *here.parents) if os.path.lexists(p / ".git")), None)


def _run_apply(
    cwd: str, patch: Path | bytes, *flags: str
) -> subprocess.CompletedProcess[bytes] | None:
    """`git apply <flags>` in `cwd` on the file at `patch`, or, where `patch` is bytes, on those
    bytes through stdin. None where git did not run, was killed by a signal or took too long. Under
    --check or --numstat, it changes nothing."""
    source, stdin = ("-", patch) if isinstance(patch, bytes) else (str(patch), None)
    try:
        out = subprocess.run(
            [*GIT, "-C", cwd, "apply", *flags, source],
            input=stdin,
            env=ENV,
            capture_output=True,
            timeout=APPLY_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return None if out.returncode < 0 else out


def _check(cwd: str, patch: Path | bytes, *flags: str) -> subprocess.CompletedProcess[bytes] | None:
    """`git apply --check <flags>`, through _run_apply(). None too where git stops before it reads
    any patch in `cwd`."""
    out = _run_apply(cwd, patch, "--check", *flags)
    if out is not None and out.returncode == FATAL:
        probe = _run_apply(cwd, PROBE, "--check")
        return None if probe is None or probe.returncode == FATAL else out
    return out


def check_patch_file(cwd: str, patch: Path | bytes) -> tuple[bool, str] | None:
    """Whether git would apply the file `patch`, or a patch's bytes, in `cwd`, and the first
    line that git writes on stderr, if any. On a patch that git refuses, git is asked once more,
    with warnings on white space off, so the line is most often the cause. A relative path is taken
    from `cwd`, and must not open with "-". For bytes, git names the file "<stdin>". None where git
    gave no answer."""
    out = _check(cwd, patch)
    if out is None:
        return None
    if out.returncode:
        quiet = _check(cwd, patch, "--whitespace=nowarn")
        out = quiet if quiet is not None and quiet.returncode else out
    said = out.stderr.decode("utf-8", "replace").strip().splitlines()
    return out.returncode == 0, said[0] if said else ""


def check_patch_bytes(cwd: str, patch: bytes) -> bool | None:
    """Whether git would apply a patch's own bytes in `cwd`. None where git gave no answer."""
    out = _check(cwd, patch)
    return None if out is None else out.returncode == 0


@functools.cache
def patch_paths(cwd: str, patch: bytes, *, before: bool = False) -> frozenset[str] | None:
    """The paths of the files in a patch's bytes. A renamed or copied file gives its new path, or
    with `before` its old one. Any other file gives its one path either way. None where git gave no
    list."""
    reverse = ["-R"] if before else []
    out = _run_apply(cwd, patch, *reverse, "--whitespace=nowarn", "--numstat", "-z")
    if out is None or out.returncode:
        return None
    rows = out.stdout.split(b"\0")[:-1]
    return frozenset(row.split(b"\t", 2)[2].decode("utf-8", "surrogateescape") for row in rows)
