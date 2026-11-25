#!/usr/bin/env python3
"""Run a command in a Linux sandbox that has no network but the model, and writes to memory alone.

The command sees <folder>, what --read and --read-same name, the system's programs, this plugin,
this Python and its own program file; for a git worktree also the repository's folder, if it has
the same owner.
It may write to <folder>, but only in memory. When it has ended, the report files in the
CLAUDE-SECURITY-<timestamp> folders that it wrote are copied out, down to 32 folders deep and from
no folder that is hidden or that a plugin loads from, but its own. Each folder comes out directly in
--out. Without that option, one that lies directly in <folder> or directly in the command's folder
comes out where it lay, and any other directly in the command's folder, unless something of its name
stands where it lay. Of folders of one name that come out in one place, only the first one's files
come out, and none that comes out elsewhere than it lay, or in --out, joins one that stands there
already. A removal inside removes nothing outside. Claude Code inside finds a relay at a loopback
address and holds no real credential. The relay runs outside, passes model requests of the command's
own process alone, and adds the credential, if one goes.

--image, which is not supported, runs the same sandbox in a virtual machine of Apple's container
tool. It names the machine's Linux image, which holds a /run folder, and python3 3.9 or newer, env,
git and the command below /usr. The folders are copied into it.

Usage:
  sandbox.py [options] <folder> -- <command> [argument ...]
  sandbox.py [options] --check <folder>

The relay shows the client certificate that CLAUDE_CODE_CLIENT_CERT and CLAUDE_CODE_CLIENT_KEY name
together, with CLAUDE_CODE_CLIENT_KEY_PASSPHRASE if the key needs it.

Exits with the command's code, 124 at the time limit, 137 if INT, TERM, HUP or QUIT stopped the
command, 2 on a usage error, and 125 if the sandbox did not start or broke, stdin broke off, output
was lost, the copy of a report failed or, in place of 0, stderr names a report's file as removed in
the sandbox only or so many files were refused that the rest went unread. With --image a stop of the
command can drop output that is still in the machine, and end with 137 all the same.
Python 3.10 or newer for an https host, stdlib only. Linux 5.19 or newer, or Apple's container tool
for --image.
"""

from __future__ import annotations

import argparse
import errno
import os
import re
import shutil
import signal
import socket
import stat
import sys
import time
from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
if __name__ == "__main__" and sys.platform not in {"linux", "darwin"}:
    sys.stderr.write("sandbox: this runs on Linux only\n")
    sys.exit(125)
from lib import plugin, strictjson
from lib.link import is_link
from lib.sandbox import kernel, provider, streams
from lib.sandbox.keeper import Door, Keeper, become, harden, user
from lib.sandbox.machine import NO_LINK, PYTHON, Machine
from lib.sandbox.plan import (
    BROKEN,
    HIDDEN_FOLDERS,
    HOME,
    SWAPPED,
    SYSTEM_PATH,
    UNGUARDED,
    Message,
    Plan,
    SandboxError,
    identity,
)
from lib.sandbox.relay import Relay, tls_context
from lib.sandbox.results import Results, folder_of
from lib.strictjson import as_map, is_list, is_map, is_str

if TYPE_CHECKING:
    import pwd
    import threading
    from collections.abc import Callable, Mapping, Sequence

_MOST_SAID = 20
_MOST_MARKS = 20
_LARGEST_MARK = 1 << 16
_LONGEST_TEXT = 1 << 20
_DRAIN_SECONDS = 30
_MOST_LINKS = 40
_GONE = frozenset({errno.ENOENT, errno.ENOTDIR, errno.ELOOP})
_STOPPED = "the run was stopped"
_PASSED = re.compile(
    r"LANG|TZ|LC_(ALL|ADDRESS|COLLATE|CTYPE|IDENTIFICATION|MEASUREMENT|MESSAGES|MONETARY|NAME"
    r"|NUMERIC|PAPER|TELEPHONE|TIME)"
    r"|CLAUDE_CODE_(AUTO_MODE_SERVER|EFFORT_LEVEL|WORKFLOW_MAX_CONCURRENT_AGENTS)"
)
_FIXED = {
    "HOME": HOME,
    "USER": "sandbox",
    "SHELL": "/bin/bash",
    "TERM": "dumb",
    "TMPDIR": "/tmp",  # noqa: S108
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
}
_HOME_STORES = (
    ".claude/.credentials.json",
    ".claude.json",
    ".git-credentials",
    ".config/git/credentials",
    ".gitcookies",
)
_STORES_BY_NAME = ("gha-creds-*.json", ".gitcookies")
_GIT_REMOTES = ("remotes", "branches")
_GIT_FILES = re.compile(r"config|credential", re.IGNORECASE)
_GIT_LOGS = (
    "FETCH_HEAD",
    "COMMIT_EDITMSG",
    "MERGE_MSG",
    "NOTES_EDITMSG",
    "SQUASH_MSG",
    "TAG_EDITMSG",
    "GITGUI_MSG",
    "GIT_COLA_MSG",
)
_GIT_CONFIGS = ("config", "config.worktree")
_URL_USER = r"(?<=://)[^/\s]+@"
_GIT_LINE = r"(?:\\(?:\r?\n|.)|[^\n])*\n?"
# A line whose key holds one of these words, as "smtpPass" does, or the user part of a URL.
_GIT_SECRET = re.compile(
    r"(?im)(^|(?<=\]))[ \t]*[\w-]*(cookie|extraheader|helper|pass|proxy|token|secret)"
    rf"{_GIT_LINE}|{_URL_USER}"
)
_LINES = re.compile(_GIT_LINE)
_ESCAPED_OUT = re.compile(r'\\\r?\n|"')
_LONE_CR = re.compile(r"\r(?!\n)")
_HEADER = re.compile(r"[\w-]+:[\x20-\x7e]+", re.ASCII)
_MANAGED = Path(
    "/Library/Application Support/ClaudeCode" if sys.platform == "darwin" else "/etc/claude-code"
)
_NEVER_SHOWN = (*HIDDEN_FOLDERS, _MANAGED)
# The copy goes in as root before any wall stands, so it must not lie over an image's programs.
_IMAGE_PROGRAMS = ("/usr", "/bin", "/sbin", "/lib", "/lib64")
_MANAGED_SECRET = re.compile(r"env|headers|mcpServers|managedMcpServers|\w+(Helper|Refresh|Export)")
_MANAGED_ELSEWHERE = ("policyHelper", "forceRemoteSettingsRefresh")
_MEMORY_HELP = (
    "the cgroup's limit; half of it for files written inside (default: 3/4 of the RAM). "
    "With --image the machine gets a third more than this (default: half of the RAM)"
)
_USER_HELP = (
    "needed as root, on Linux 6.2 or newer: run the relay and copy out reports as this user; "
    "needs --out, but for --check: that folder is this user's to write, and best empty; the "
    "command has its own user"
)
_SAME_HELP = (
    "as --read, but the start is refused unless PATH leads, through no link, to the folder of this "
    "device and inode number"
)
_COMMAND_HELP = (
    "prints the key or token, or for Bedrock what 'aws configure export-credentials' prints; "
    "it runs outside, again after five minutes, or after ten seconds once it has failed or a "
    "401 or 403 has come. --check does not run it. With no --image it runs twice at the start. "
    "After its first run it then has no new privileges and runs behind the system call filter, "
    "so it can use no setuid program or key ring, and with --user it runs as that user. On the "
    "Claude API the answer goes as a bearer token, or as x-api-key where ANTHROPIC_API_KEY is "
    "set and ANTHROPIC_AUTH_TOKEN is not"
)
_FILE_HELP = (
    "holds a token for the Claude API that the caller renews; the relay reads it for each request, "
    "and waits a few seconds for a new one where the API says that it has ended"
)


class _StoppedError(SandboxError):
    """A signal came during the start."""


class _TooLongError(SandboxError):
    """A file is too long for a git file."""


class Args(argparse.Namespace):
    """The parsed command line."""

    folder: str = ""
    command: Sequence[str] = ()
    check: bool = False
    sudo: bool = False
    user: pwd.struct_passwd | None = None
    image: str | None = None
    read: Sequence[str] | None = None
    read_same: Sequence[tuple[str, str]] | None = None
    env: Sequence[str] | None = None
    out: str | None = None
    minutes: float = 180
    memory: int | None = None
    no_cgroup: bool = False
    credential_command: str | None = None
    token_file: str | None = None


def _text(path: Path) -> str:
    """The text of a regular file whose absolute path holds no link, which could lead outside; else
    none. OSError if it cannot be read, or a folder on the way to it cannot be searched;
    _TooLongError if it is too long."""
    try:
        with folder_of(str(path)) as above:
            if not stat.S_ISREG(os.stat(path.name, dir_fd=above, follow_symlinks=False).st_mode):
                return ""
            file = os.open(path.name, NO_LINK, dir_fd=above)
        with os.fdopen(file, encoding="utf-8", errors="replace", newline="") as opened:
            text = opened.read(_LONGEST_TEXT + 1)
    except OSError as error:
        if error.errno in _GONE:
            return ""
        raise OSError(error.errno, error.strerror, str(path)) from error
    if len(text) > _LONGEST_TEXT:
        msg = f"{path} is too long for a git file"
        raise _TooLongError(msg)
    return text


def _is_file(path: Path) -> bool:
    """Whether `path` leads to a regular file. OSError if it cannot be looked at."""
    try:
        return stat.S_ISREG(path.stat().st_mode)
    except OSError as error:
        if error.errno in _GONE:
            return False
        raise


def _lies_in(path: Path, folder: str | Path) -> bool:
    """By the files, not by their names: another name can lead to the same place."""
    for place in (path, *path.parents):
        with suppress(OSError):
            if place.samefile(folder):
                return True
    return False


def _outer_git_folder(folder: Path) -> list[Path]:
    """The folder of the repository of which `folder` is a worktree, if it lies elsewhere, points
    back and has the same owner."""
    with suppress(OSError, ValueError):
        own = _resolved(folder / _text(folder / ".git").partition("gitdir:")[2].strip())
        # Only the repository's own word counts: nothing in the folder may bring another into view.
        if _lies_in(own, folder) or own.parent.name != "worktrees":
            return []
        outer = own.parent.parent
        back = _resolved(own / _text(own / "gitdir").strip())
        owners = {path.stat().st_uid for path in (folder, own, outer)}
        if back == folder / ".git" and len(owners) == 1 and _is_git_folder(outer):
            return [outer]
    return []


def _has_git_s_name(path: Path) -> bool:
    return path.name.lower() == ".git"


def _has_head(folder: Path) -> bool:
    # A link names its branch, and the branch's file may not be there.
    return is_link(folder / "HEAD") or os.path.isfile(folder / "HEAD")


def _is_git_folder(folder: Path) -> bool:
    return _has_head(folder) and all(os.path.isdir(folder / part) for part in ("objects", "refs"))


def _can_list(folder: Path) -> bool:
    """Whether `folder` is a folder that this user can list. No if it is a link or another kind of
    file, if it is closed and another's, or if the folder above it is closed. PermissionError if it
    is closed and the caller's, and another OSError if it cannot be found."""
    try:
        status = folder.lstat()
    except PermissionError:
        return False
    if not stat.S_ISDIR(status.st_mode):
        return False
    can_list = os.access(folder, os.R_OK | os.X_OK)
    if not can_list and status.st_uid == os.geteuid():
        raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), str(folder))
    return can_list


def _listed(folder: Path) -> list[Path]:
    """What `folder` holds, and nothing where _can_list says no or the folder is gone.
    SandboxError at any other fault."""
    try:
        return [*folder.iterdir()] if _can_list(folder) else []
    except OSError as error:
        if error.errno in _GONE:
            return []
        msg = f"{folder} cannot be read, so its credentials cannot be blanked: {error.strerror}"
        raise SandboxError(msg) from error


def _inside(folder: Path) -> list[Path]:
    """What `folder` holds, but for links."""
    return [path for path in _listed(folder) if not is_link(path)]


def _below(folder: Path) -> list[Path]:
    """What `folder` holds at any depth, but for links."""
    found: list[Path] = []
    left = _inside(folder)
    while left:
        found.append(left.pop())
        left += _inside(found[-1])
    return found


def _shown_text(path: Path, *, sure: bool, carried: Callable[[Path], bool]) -> str | None:
    """What shows of `path`, a file of a git folder, or None if it shows as it is: the file less
    its secret lines and the user part of each address. `sure` says that the folder is surely
    git's; then a file that is too long, holds an address with a query or holds a carriage return
    alone raises SandboxError, and a regular file that _GIT_CONFIGS names, in any case of letters,
    comes back even with nothing taken out, where `carried` says that a copy can lie in its place.
    If not sure, a file that is too long shows nothing."""
    try:
        text = _text(path)
    except _TooLongError:
        if sure:
            raise
        return ""
    if sure and _has_query(text):
        cause = "an address with a query"
    elif sure and _LONE_CR.search(text):
        cause = "a carriage return alone"
    else:
        shown = _GIT_SECRET.sub("", text)
        copy = sure and path.name.lower() in _GIT_CONFIGS and _is_file(path) and carried(path)
        return shown if shown != text or copy else None
    msg = (
        f"{path} holds {cause}, and the sandbox cannot take out a secret alone: "
        "mend the file to scan in the sandbox"
    )
    raise SandboxError(msg)


def _has_query(text: str) -> bool:
    """Whether a line of `text`, as git reads lines, holds an address with a query: a "?" after
    "://", with git's continued lines joined and its double quotes left out."""
    return any(
        "?" in _ESCAPED_OUT.sub("", line.group()).partition("://")[2]
        for line in _LINES.finditer(text)
    )


def _shown_log(path: Path) -> str | None:
    """What shows of `path`, a log of a git folder: nothing if it holds the user part or the query
    of an address or is too long to look through, and None if it shows as it is."""
    with suppress(_TooLongError):
        text = _text(path)
        if not re.search(_URL_USER, text) and not _has_query(text):
            return None
    return ""


def _git_files(
    git: Path, *, sure: bool, carried: Callable[[Path], bool]
) -> dict[Path, Callable[[Path], str | None]]:
    """The files of `git`, and of the git folders of its worktrees and submodules, in which to
    look for a sign-in, each with the function that says what shows of it."""
    tops = [git, *_inside(git / "worktrees")]
    modules = [top / "modules" for top in tops]
    places = [*tops, *modules, *(path for folder in modules for path in _below(folder))]
    found = [path for place in places for path in _inside(place)]
    shown = partial(_shown_text, sure=sure, carried=carried)
    # Only a sure git folder looks wider: another can be a repository's own source files.
    if not sure:
        return {path: shown for path in found if path.name in _GIT_CONFIGS}
    named = (path for path in found if _GIT_FILES.search(path.name))
    remotes = (path for place in places for name in _GIT_REMOTES for path in _inside(place / name))
    logs = (path for place in filter(_has_head, places) for path in _below(place / "logs"))
    fetched = (path for path in found if path.name.upper() in _GIT_LOGS)
    return dict.fromkeys((*named, *remotes), shown) | dict.fromkeys((*logs, *fetched), _shown_log)


def _is_sign_in(path: Path, folders: Sequence[Path]) -> bool:
    """Whether `path`, a known place of a sign-in, leads to a regular file. No if it is
    too long to look up. SandboxError if it lies in `folders` and cannot be looked at."""
    try:
        return _is_file(path)
    except OSError as error:
        too_long = error.errno == errno.ENAMETOOLONG
        if too_long or not any(map(path.is_relative_to, folders)):
            return False
        msg = f"{path} cannot be looked at, so it cannot be blanked: {error.strerror}"
        raise SandboxError(msg) from error


def _link_on_the_way(name: str, folders: Sequence[Path]) -> Path | None:
    """The first link on the way to `name` that lies in one of `folders`, or the link past
    _MOST_LINKS links. Each of `folders` has a path with no link in it."""
    place, links = Path("/"), 0
    left = [*reversed(Path(name).absolute().parts[1:])]
    while left:
        part = left.pop()
        if part == "..":
            place = place.parent
            continue
        step = place / part
        if not is_link(step):
            place = step
            continue
        links += 1
        if links > _MOST_LINKS or any(map(step.is_relative_to, folders)):
            return step
        target = step.readlink()
        if target.is_absolute():
            place = Path("/")
        left.extend(reversed(target.parts[target.is_absolute() :]))
    return None


def _without_secrets(
    folders: list[Path],
    variables: Mapping[str, str],
    homes: Sequence[Path],
    carried: Callable[[Path], bool] = lambda _: True,
) -> dict[str, str]:
    """Files that can hold a sign-in, in `folders` or at known places that may not show, with the
    text to show instead. Each of `folders` has a path with no link in it. `carried` says where
    a copy of a git folder's config can lie in the file's place. SandboxError where a link in
    `folders`, or more than _MOST_LINKS links, is on the way to a file that a variable names."""
    given = [variables[name] for name in provider.CREDENTIAL_FILES if variables.get(name)]
    forms = (*given, *map(os.path.expanduser, given))
    named = {form: os.path.realpath(form) for form in forms}
    stored = (os.path.realpath(home / name) for home in homes for name in _HOME_STORES)
    one = [path for folder in folders for path in _listed(folder)]
    two = [path for place in one for path in _listed(place)]
    three = (path for place in two for path in _listed(place) if _has_git_s_name(path))
    plain = [path for path in (*folders, *one, *two, *three) if not is_link(path)]
    by_name = (path for path in plain if any(map(path.match, _STORES_BY_NAME)))
    known = (*map(Path, (*named.values(), *stored)), *by_name)
    signed_in = {path for path in known if _is_sign_in(path, folders)}
    for form, target in named.items():
        link = _link_on_the_way(form, folders) if Path(target) in signed_in else None
        if link:
            msg = (
                f"{link} is a link on the way to {form}, which names a sign-in file. The sandbox"
                " shows that file empty, and a link in a folder of the scan, or past"
                f" {_MOST_LINKS} links, could choose which file that is: name the file itself, or"
                " take the link out"
            )
            raise SandboxError(msg)
    gits = (path for path in plain if _has_git_s_name(path) or _is_git_folder(path))
    sure = ((git, _has_git_s_name(git) or git in folders) for git in gits)
    texts = (
        (path, shown(path))
        for git, is_sure in sure
        for path, shown in _git_files(git, sure=is_sure, carried=carried).items()
        if path not in signed_in
    )
    blanks = dict.fromkeys(map(str, signed_in), "")
    return {str(path): text for path, text in texts if text is not None} | blanks


def _shareable(value: object) -> object:
    """`value` less the keys, at any depth, that _MANAGED_SECRET names, and URLs' user parts."""
    if is_map(value):
        return {k: _shareable(v) for k, v in value.items() if not _MANAGED_SECRET.fullmatch(k)}
    if is_list(value):
        return [*map(_shareable, value)]
    return re.sub(_URL_USER, "", value) if is_str(value) else value


def _managed_drop_ins() -> list[Path]:
    """The .json files of managed-settings.d in the order of their names, less hidden ones, as
    Claude Code reads them. SandboxError if the folder cannot be listed."""
    folder = _MANAGED / "managed-settings.d"
    try:
        return sorted(path for path in folder.iterdir() if path.match("[!.]*.json"))
    except OSError as error:
        if error.errno in _GONE:
            return []
        msg = f"{folder} cannot be read: {error.strerror}"
        raise SandboxError(msg) from error


def _managed_settings() -> tuple[dict[str, str], dict[str, str]]:
    """The files of the organisation's policy for Claude Code by their names below /etc, as
    _shareable gives them, and the variables of its `env`, a later file's over an earlier one's.
    SandboxError if a part of the policy cannot be looked at, read or loaded inside."""
    shown: dict[str, str] = {}
    env: dict[str, str] = {}
    for path in (_MANAGED / "managed-settings.json", *_managed_drop_ins()):
        try:
            text = path.read_text(encoding="utf-8-sig") if _is_file(path) else ""
            settings = strictjson.loads(text) if text.strip() else None
        except (OSError, ValueError) as error:
            msg = f"{path} cannot be read: {error}"
            raise SandboxError(msg) from error
        if not is_map(settings):
            continue
        given = filter(settings.get, settings)
        if name := next((name for name in given if name.startswith(_MANAGED_ELSEWHERE)), None):
            msg = f"{path} sets {name}, whose policy cannot load in the sandbox"
            raise SandboxError(msg)
        if settings.get("hooks"):
            streams.say(f"{path} holds hooks: a hook cannot run if the sandbox hides its program")
        enabled = as_map(settings.get("sandbox")).get("enabled")
        if provider.setting_text(enabled) not in {"null", "false"}:
            streams.say(f"{path} asks for Claude Code's own sandbox, so shell commands can fail")
        if is_map(more := settings.get("env")):
            env |= {k: provider.setting_text(v) for k, v in more.items()}
        shown[f"claude-code/{path.relative_to(_MANAGED)}"] = strictjson.text(_shareable(settings))
    return shown, env


def _refuse_redirects_in_user_settings(options: Args) -> None:
    """SandboxError if the user's settings file sets variables that provider.routes_lacking()
    names. A check and a start with --user pass, and so does a file that cannot be read."""
    if options.check or options.user:
        return
    folder = os.environ.get("CLAUDE_CONFIG_DIR") or _home() / ".claude"
    try:
        settings = strictjson.load(Path(folder, "settings.json"), "utf-8-sig")
    except (OSError, ValueError):
        return
    env = provider.settings_env(as_map(settings))
    if names := provider.routes_lacking(env, os.environ):
        msg = (
            f"your Claude Code settings set {', '.join(names)}, which the relay does not read"
            " there: set each in this environment, to an empty value if the scan needs none"
        )
        raise SandboxError(msg)


def _home() -> Path:
    msg = "this user has no home folder: set HOME"
    if "HOME" in os.environ and not os.environ["HOME"]:
        raise SandboxError(msg)
    try:
        return Path.home()
    except (KeyError, RuntimeError) as error:
        raise SandboxError(msg) from error


def _sudo_user() -> pwd.struct_passwd | None:
    """The entry that SUDO_USER names."""
    with suppress(ValueError):
        return user(os.environ.get("SUDO_USER", ""))
    return None


def _homes(options: Args) -> list[Path]:
    """The caller's home folder, and those of the user behind sudo and of --user."""
    behind = _sudo_user()
    if not behind and (name := os.environ.get("SUDO_USER")):
        streams.say(f"no user is named {name}: the home of SUDO_USER is neither hidden nor blanked")
    entries = (options.user, behind)
    return [_home(), *(Path(entry.pw_dir) for entry in entries if entry and entry.pw_dir)]


def _trusted_owners() -> set[int]:
    """Root, and the user behind sudo if SUDO_USER and SUDO_UID name the same user."""
    entry = _sudo_user()
    if entry and os.environ.get("SUDO_UID") == str(entry.pw_uid):
        return {0, entry.pw_uid}
    return {0}


def _as_root_resolved(name: str | Path) -> Path:
    """`name` with no link left. SandboxError at a link of another owner than root and the user
    behind sudo: it could make root show or write what that owner chooses."""
    owners = _trusted_owners()
    place, links = Path("/"), 0
    left = [*reversed(Path(name).absolute().parts[1:])]
    while left:
        part = left.pop()
        if part == "..":
            place = place.parent
            continue
        with folder_of(str(place / part)) as above:
            entry = os.open(part, os.O_PATH | os.O_NOFOLLOW, dir_fd=above)
        status = os.fstat(entry)
        if not stat.S_ISLNK(status.st_mode):
            os.close(entry)
            place /= part
            continue
        target = Path(os.readlink("", dir_fd=entry))
        os.close(entry)
        links += 1
        if links > _MOST_LINKS:
            raise OSError(errno.ELOOP, os.strerror(errno.ELOOP), str(name))
        if status.st_uid not in owners:
            msg = f"{place / part}: root follows no link of another user"
            raise SandboxError(msg)
        if target.is_absolute():
            place = Path("/")
        left.extend(reversed(target.parts[target.is_absolute() :]))
    return place


def _resolved(name: str | Path) -> Path:
    try:
        return Path(name).resolve(strict=True) if os.geteuid() else _as_root_resolved(name)
    except RuntimeError as error:
        raise OSError(errno.ELOOP, os.strerror(errno.ELOOP), str(name)) from error


def _shown(name: str | Path, homes: Sequence[Path]) -> Path:
    path = _resolved(name)
    hidden = (Path(os.path.realpath(place)) for place in (*_NEVER_SHOWN, *homes))
    if any(_lies_in(path, n) for n in _NEVER_SHOWN) or any(_lies_in(h, path) for h in hidden):
        msg = f"{path} is, holds or lies in a folder that the sandbox must hide"
        raise SandboxError(msg)
    if not (path.is_dir() or path.is_file()):
        msg = f"{path} is not a file or a folder"
        raise SandboxError(msg)
    return path


def _own_policy(passed: Mapping[str, str]) -> dict[str, str]:
    """The sandbox's own managed settings file, by its name below /etc."""
    body = os.fsencode(passed.get("CLAUDE_CODE_EXTRA_BODY", "{}")).decode("utf-8", "replace")
    env = {
        "CLAUDE_CODE_DISABLE_CRON": "1",
        "CLAUDE_CODE_EXTRA_BODY": body,
        "CLAUDE_CODE_SUBAGENT_PROMPT_SNAPSHOT": "0",
    }
    policy = {"crossSessionInbound": "refuse", "env": env}
    return {
        "claude-code/managed-settings.d/zz-claude-security-sandbox.json": strictjson.text(policy)
    }


def _python_notice(plan: Plan) -> str:
    """What shows of the prefix of the Python that runs here, where it lies outside /usr and no
    path of the plan shows it whole; else nothing."""
    prefix = Path(sys.base_prefix).resolve()
    shown = [Path(path) for path in (*plan["writable"], *plan["readable"])]
    inside = sorted(str(path.relative_to(prefix)) for path in shown if path.is_relative_to(prefix))
    whole = prefix.is_relative_to(Path("/usr").resolve()) or any(map(prefix.is_relative_to, shown))
    if whole or not inside:
        return ""
    return f"of {prefix}, where Python lies, only these show: {', '.join(inside)}"


def _program(name: str) -> Path:
    if (program := shutil.which(name)) is None:
        msg = f"{name} is not on PATH"
        raise SandboxError(msg)
    return Path(program)


def _plan(options: Args, chosen: provider.Provider, etc: Mapping[str, str]) -> Plan:
    variables = os.environ
    homes = _homes(options)
    may_show = partial(_shown, homes=homes)
    others = [home for home in homes if not _lies_in(Path(os.path.realpath(home)), "/usr")]
    is_needed = partial(_shown, homes=others)
    folder = may_show(options.folder)
    if options.sudo and os.geteuid() not in {0, folder.stat().st_uid}:
        # The command would see it as its owner does, and so more of it than the caller can.
        msg = f"{folder} belongs to another user"
        raise SandboxError(msg)
    writable = [folder, *map(may_show, _outer_git_folder(folder))]
    program = None if options.image else _program(options.command[0])
    needed = [plugin.ROOT]
    system = list[Path]()
    if program:
        prefix = is_needed(sys.base_prefix)
        python_folders = (prefix / name for name in ("bin", "lib", "lib64", "libexec"))
        needed += [*filter(Path.is_dir, python_folders), program]
        system += [Path("/usr")]
    covered = [*writable, *system]
    pinned: dict[Path, str] = {}
    for path, pin in options.read_same or ():
        absolute, seen = Path(os.path.abspath(path)), None
        with suppress(OSError), folder_of(str(absolute / "any")) as place:
            seen = identity(os.fstat(os.dup(place)))
        if seen != pin or may_show(absolute) != absolute:
            msg = f"{path} {SWAPPED}"
            raise SandboxError(msg)
        pinned[absolute] = pin
    named = set(pinned)
    for path in options.read or ():
        given = Path(os.path.abspath(path))
        below = any(map(given.is_relative_to, pinned))
        if below and Path(os.path.realpath(path)) != given:
            msg = f"{given} {SWAPPED}"
            raise SandboxError(msg)
        real = may_show(path)
        named.add(given if below else real)
    if clash := named.intersection(writable):
        msg = f"--read or --read-same names {min(clash)}, which the command may write"
        raise SandboxError(msg)
    wanted = named | {is_needed(path) for path in needed}

    def shown_by(path: Path) -> Sequence[Path]:
        """What makes a mount of `path`'s own needless."""
        if path not in named:
            return (*covered, *(wanted - {path}))
        if path in pinned or any(map(path.is_relative_to, writable)):
            return ()
        return (*system, *(named - {path}))

    # What --read or --read-same names stays read-only, even below a folder the command may write.
    readable = [path for path in wanted if not any(map(path.is_relative_to, shown_by(path)))]
    for path in (*writable, *readable) if options.image else ():
        if any(_lies_in(path, system) for system in _IMAGE_PROGRAMS):
            msg = f"{path} would lie over the image's programs in the virtual machine"
            raise SandboxError(msg)

    def visible(path: Path) -> bool:
        return any(map(path.is_relative_to, (*covered, *readable)))

    if options.token_file and visible(_resolved(options.token_file)):
        msg = f"{options.token_file} holds the token, and would show inside the sandbox"
        raise SandboxError(msg)
    first, search = options.command[0], SYSTEM_PATH
    if program:
        # A link keeps its name where it shows inside: some programs act by their name.
        linked = program.parent.resolve() / program.name
        first = str(linked if visible(linked) else linked.resolve())
        reached = filter(visible, (Path(os.path.realpath(entry)) for entry in os.get_exec_path()))
        own = f"{Path(sys.base_prefix).resolve()}/bin"
        search = tuple(dict.fromkeys((*map(str, reached), own, *SYSTEM_PATH)))
    passed = {
        name: value
        for name, value in variables.items()
        if name in (options.env or ())
        or _PASSED.fullmatch(name)
        or provider.SETTINGS.fullmatch(name)
    }
    overlaid = [path for path in (*writable, *readable) if path.is_dir()]

    def bare(path: Path) -> bool:
        """Whether `path` shows with no layer over it, so that nothing can lie in its place."""
        return visible(path) and (path in readable or not any(map(path.is_relative_to, overlaid)))

    def carried(path: Path) -> bool:
        """Whether a copy can lie in `path`'s place: on Linux, a layer carries it, and no other
        name of the file shows what it hides. A machine takes its files in once, at the start. A
        copy is searched for credentials, as a blank is; a clean file with no copy is not."""
        return not options.image and not bare(path) and path.stat().st_nlink == 1

    folders = sorted({*writable, *readable, *named})
    replaced = _without_secrets(folders, variables, homes, carried=carried)
    for path in () if options.image else map(Path, replaced):
        if path.stat().st_nlink > 1:
            msg = f"{path} can hold a credential, and a hard link to it could show in the sandbox"
            raise SandboxError(msg)
    for path in filter(bare, map(Path, replaced)):
        msg = f"{path} can hold a credential, and would show inside the sandbox"
        raise SandboxError(msg)
    swappable = [path for path in pinned if any(map(path.is_relative_to, system))]
    cut = _without_secrets(folders, variables, homes, carried=lambda _: False) if swappable else {}
    for path in map(Path, cut):
        if any(map(path.is_relative_to, swappable)):
            msg = (
                f"{path} can hold a credential, which a swap of folders below /usr could show in"
                " the sandbox: mend or remove the file, or move the folder out of /usr"
            )
            raise SandboxError(msg)
    if any(word.startswith("--managed-settings") for word in options.command):
        streams.say("with --managed-settings the sandbox adds no managed settings of its own")
    else:
        etc = {**etc, **_own_policy(passed)}
    here = Path.cwd().resolve()
    memory = (
        os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") * 3 // (8 if options.image else 4)
    )
    plan = Plan(
        command=[first, *options.command[1:]],
        environment={**passed, **_FIXED, **chosen.inside, "PATH": os.pathsep.join(search)},
        cwd=str(here if here.is_relative_to(folder) else folder),
        writable=[*map(str, writable)],
        readable=[*map(str, readable)],
        pinned={str(path): pin for path, pin in pinned.items()},
        replaced=replaced,
        etc=etc,
        seconds=options.minutes * 60,
        memory=options.memory << 20 if options.memory else memory,
        cgroup=not options.no_cgroup,
        user=0,
    )
    _refuse_a_leak(plan, variables, chosen.credential.seen)
    return plan


def _refuse_a_leak(plan: Plan, variables: Mapping[str, str], seen: set[str]) -> None:
    """Refuse a plan that shows one of `seen`, or passes on a variable of provider.SECRETS."""
    held = [
        name
        for name, value in plan["environment"].items()
        if (name in provider.SECRETS and value and value == variables.get(name))
        or any(secret in value for secret in seen)
    ]
    if held:
        msg = f"the credential would show inside, in these variables: {', '.join(sorted(held))}"
        raise SandboxError(msg)
    shown = "\0".join((*plan["command"], *plan["etc"].values(), *plan["replaced"].values()))
    if any(secret in shown for secret in seen):
        msg = "the credential would show inside: see the command, managed settings and git's files"
        raise SandboxError(msg)


def _custom_headers(variables: Mapping[str, str]) -> dict[str, str]:
    lines = variables.get("ANTHROPIC_CUSTOM_HEADERS", "").splitlines()
    pairs = (line.partition(":") for line in lines if line.strip())
    headers = {name.strip().lower(): value.strip() for name, _, value in pairs}
    if not all(_HEADER.fullmatch(f"{name}:{value}") for name, value in headers.items()):
        msg = "ANTHROPIC_CUSTOM_HEADERS holds a line that is no header"
        raise SandboxError(msg)
    return headers


def _mounts_below(folders: Sequence[str]) -> list[str]:
    """The mount points below `folders`, but for those that `folders` names. An overlay shows one
    file system, so a mount does not show, and what lies under it can."""
    below = tuple(f"{folder}/" for folder in folders)
    points = kernel.mount_points()
    return [point for point in points if point.startswith(below) and point not in folders]


def _refuse_a_credential_out_of_reach(how: str, chosen: provider.Provider) -> None:
    """Refuse a start for which this process, as `how` says that it now runs, cannot get the
    credential."""
    chosen.credential.forget(soonest=0)
    try:
        chosen.sign("", b"")
    except _StoppedError:
        raise
    except SandboxError as error:
        msg = f"{how}: {error}"
        raise SandboxError(msg) from error


def _drained(outputs: Sequence[threading.Thread], given_up: Callable[[], bool]) -> bool:
    """Whether all that the command wrote has gone out, with no write held up too long and no
    word from `given_up`."""
    began = time.monotonic()
    while any(output.is_alive() for output in outputs):
        if given_up() or time.monotonic() - max(began, streams.last_write()) >= _DRAIN_SECONDS:
            return False
        time.sleep(0.05)
    return True


def _run(options: Args) -> int:
    if UNGUARDED:
        if not provider.has_plain_host(os.environ):
            raise SandboxError(UNGUARDED)
        streams.say(UNGUARDED)
    box: Keeper | Machine | None = None
    relay: Relay | None = None
    signals = 0

    def stop() -> None:
        if relay:
            relay.close()
        if box:
            box.stop()

    def stop_by_signal(*_signal: object) -> None:
        nonlocal signals
        raising = not (box or signals)
        signals += 1
        if raising:
            raise _StoppedError(_STOPPED)
        stop()

    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
        if signal.getsignal(number) != signal.SIG_IGN:
            signal.signal(number, stop_by_signal)
    etc, managed = _managed_settings()
    if managed:
        streams.say("the env of the managed settings is not used, by the relay or inside")
    for name in filter(provider.ROUTE.fullmatch, managed):
        if os.environ.get(name, "") != managed[name] and not options.check:
            msg = f"the managed settings set {name}, and this environment must hold the same value"
            raise SandboxError(msg)
    _refuse_redirects_in_user_settings(options)
    variables = {"ANTHROPIC_API_KEY": "not-needed-for-a-check"} if options.check else os.environ
    command = "" if options.check else options.credential_command or ""
    file = "" if options.check else options.token_file or ""
    chosen = provider.select(variables, command, file)
    added = _custom_headers(os.environ)
    tls = tls_context(os.environ)
    plan = _plan(options, chosen, etc)
    for folder in plan["writable"][1:]:
        streams.say(f"it also shows {folder}, to which .git points")
    for point in [] if options.image else _mounts_below([*plan["writable"], *plan["readable"]]):
        streams.say(f"what is mounted at {point} does not show; what lies under it can, unsearched")
    if not options.image and (said := _python_notice(plan)):
        streams.say(said)
    if os.geteuid() and not (options.sudo or options.image):
        streams.say("without --sudo it has no user of its own and no memory cap")
    out = _resolved(options.out) if options.out else Path(plan["writable"][0])
    start = Path(plan["cwd"]).relative_to(plan["writable"][0]).parts
    around = (*Path(plan["cwd"]).parts, *out.parts)
    if not options.check and any(map(plugin.REPORT_DIR_RE.match, around)):
        msg = "neither the command's folder nor --out may be a report folder, or lie below one"
        raise SandboxError(msg)
    results = Results(out, start, in_place=not options.out)
    reports = out if options.out else plan["cwd"]
    if not (options.check or os.access(reports, os.W_OK)):
        msg = f"reports cannot be written to {reports}"
        raise SandboxError(msg)
    outputs: list[threading.Thread] = []
    faults: list[str] = []
    marks: list[Message] = []
    removed = 0
    named: list[str] = []
    note = ""
    code = None
    made = Machine(plan, options.image) if options.image else Keeper(plan, sudo=options.sudo)
    if options.user:
        become(options.user, f"/proc/self/fd/{results.folder}")
        name = options.user.pw_name
        if not (options.check or os.access(".", os.W_OK | os.X_OK, dir_fd=results.folder)):
            msg = f"{name} cannot write in {out}: give --out a folder where it can"
            raise SandboxError(msg)
        _refuse_a_credential_out_of_reach(f"as {name}", chosen)
    elif not options.image:
        harden()
        _refuse_a_credential_out_of_reach("behind the system call filter (see --help)", chosen)
    box = made

    def fail(why: str) -> None:
        faults.append(why)
        stop()

    def save(file: Message) -> None:
        try:
            results.save(file.text, file.files[0])
        except OSError as error:
            fail(f"{file.text} was not copied out: {error.strerror}")

    messages = box.messages()
    for message in messages:
        if message.kind == "relay":
            listener = (socket.socket if options.image else Door)(fileno=message.files[0])
            relay = Relay(listener, chosen, added, tls, fail)
        elif message.kind == "streams":
            stdin, stdout, stderr = message.files
            signal.signal(signal.SIGTTIN, signal.SIG_IGN)
            streams.copy_in(0, stdin, fail)
            outputs = [streams.copy_out(stdout, 1, fail), streams.copy_out(stderr, 2, fail)]
        elif message.kind == "file":
            is_mark = Path(message.text).name == plugin.COMPLETE_NAME
            if not (is_mark and results.may_come_out(message.text)):
                save(message)
            elif len(marks) < _MOST_MARKS and (os.fstat(message.files[0]).st_size <= _LARGEST_MARK):
                marks.append(message)
            else:
                os.close(message.files[0])
                results.refused += 1
        elif message.kind == "removed":
            is_mark = Path(message.text).name == plugin.COMPLETE_NAME
            if not (options.out or is_mark) and results.may_come_out(message.text):
                removed += 1
                if removed <= _MOST_SAID:
                    named.append(message.text)
        elif message.kind == "exit":
            code = int(message.text)
        elif message.kind == "note":
            note = message.text
        else:
            faults.append(message.text)
        if results.flooded:
            break
    messages.close()
    stop()
    ended = box.wait()
    if ended and not (faults or results.flooded):
        faults.append(f"the sandbox ended with exit code {ended}")
    elif code is None and not (faults or results.flooded):
        faults.append("the sandbox ended with no exit code")
    elif not (outputs or note or faults):
        faults.append("the sandbox ended before the command started")
    if not _drained(outputs, lambda: signals > 1):
        faults.append("the command's output was not read to its end")
    if signals and code is None:
        faults.insert(0, _STOPPED)
    try:
        for mark in marks:
            results.claim(mark.text)
    except OSError as error:
        fail(f"the place of a report folder could not be looked at: {error.strerror}")
    for mark in marks:
        if faults or results.refused or removed:
            break
        save(mark)
    more = " or more" if results.flooded else ""
    if results.clashed:
        said = "something of their report folder's name came first"
        streams.say(f"{results.clashed}{more} files may not come out: {said}")
    if others := results.refused - results.clashed:
        streams.say(f"{others}{more} files may not come out, by their name or the limits")
    for name in [*results.moved][:_MOST_SAID]:
        streams.say(f"{name} came out in {reports}")
    if len(results.moved) > _MOST_SAID:
        streams.say(f"{len(results.moved) - _MOST_SAID} more report folders came out there")
    for name in named:
        streams.say(f"{name} was removed in the sandbox only")
    if removed > _MOST_SAID:
        streams.say(f"{removed - _MOST_SAID} more files were removed in the sandbox only")
    if relay and relay.refused and not options.check:
        streams.say(f"the relay refused {relay.refused} of the command's calls")
    for fault in faults[:_MOST_SAID]:
        streams.say(fault)
    if len(faults) > _MOST_SAID:
        streams.say(f"and {len(faults) - _MOST_SAID} more faults")
    if note:
        streams.say(note)
    if faults or code is None or ((results.flooded or removed) and not code):
        return BROKEN
    return code


def _pin(text: str) -> tuple[str, str]:
    """The path in DEVICE:INODE:PATH, and the rest as identity() writes it."""
    device, _, rest = text.partition(":")
    inode, _, path = rest.partition(":")
    if not (device.isdecimal() and inode.isdecimal() and path):
        msg = f"{text!r} is not DEVICE:INODE:PATH"
        raise argparse.ArgumentTypeError(msg)
    return path, f"{int(device)}:{int(inode)}"


def _options(argv: Sequence[str]) -> Args:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add = parser.add_argument
    add("folder", help="the folder to scan")
    add("--check", action="store_true", help="try files, network and processes from inside")
    add("--sudo", action="store_true", help="build the sandbox as root: its own user, and a cgroup")
    add("--user", metavar="NAME", type=user, help=_USER_HELP)
    add("--image", help="not supported: run in a virtual machine with this image, on macOS")
    add("--read", action="append", metavar="PATH", help="show this too, read-only")
    add("--read-same", action="append", metavar="DEVICE:INODE:PATH", type=_pin, help=_SAME_HELP)
    add("--env", action="append", metavar="NAME", help="pass it on, unless the sandbox sets it")
    add("--out", metavar="FOLDER", help="report folders come out directly in this folder")
    add("--minutes", type=float, help=f"the time limit (default: {Args.minutes})")
    add("--memory", type=int, metavar="MIB", help=_MEMORY_HELP)
    add("--no-cgroup", action="store_true", help="as root, run with no cap on memory")
    add("--credential-command", metavar="COMMAND", help=_COMMAND_HELP)
    add("--token-file", metavar="FILE", help=_FILE_HELP)
    # argparse would also take a "--" out of the command.
    split = argv.index("--") if "--" in argv else len(argv)
    options = parser.parse_args(argv[:split], namespace=Args())
    options.command = argv[split + 1 :]
    if not (0 < options.minutes < 1e6 and (options.memory is None or options.memory > 0)):
        parser.error("--minutes must lie between 0 and a million, and --memory above 0")
    given = (options.out, options.image, options.credential_command, options.token_file)
    if "" in {options.folder, *given, *(options.read or ())}:
        parser.error(
            "the folder, --out, --read, --image, --credential-command and --token-file may not be "
            "empty"
        )
    if options.check == bool(options.command):
        parser.error("give a command after --, or --check")
    if options.image and options.image.startswith("-"):
        parser.error("--image names an image, not an option")
    if sys.platform == "darwin" and not options.image:
        parser.error(
            "macOS needs --image, which is not supported: run this on Linux, or in a Linux VM"
        )
    if options.image and (options.sudo or options.user or options.no_cgroup):
        parser.error("--image takes no --sudo, --user or --no-cgroup")
    if options.user and os.geteuid():
        parser.error("--user needs root")
    if not (options.user or os.geteuid()):
        other = "" if options.image else ", or name one with --user"
        parser.error(f"the relay may not be root: start as a plain user{other}")
    if options.user and not options.user.pw_uid:
        parser.error("--user cannot be root")
    if options.user and not (options.out or options.check):
        parser.error("--user needs --out")
    if options.check:
        check = plugin.ROOT / "scripts/sandbox_walls.py"
        options.env = None
        python = PYTHON if options.image else os.path.realpath(sys.executable)
        options.command = [python, "-I", "-S", str(check), str(_home())]
    return options


def _open_closed_streams() -> None:
    """A stream left closed lends its number to the next file that is opened, and an import may
    have taken it by now."""
    while (file := os.open(os.devnull, os.O_RDWR)) <= 2:
        pass
    for number, stream in enumerate((sys.__stdin__, sys.__stdout__, sys.__stderr__)):
        if stream is None:
            os.dup2(file, number)
    os.close(file)


def main() -> int:
    try:
        _open_closed_streams()
        return _run(_options(sys.argv[1:]))
    except (OSError, SandboxError) as error:
        streams.say(str(error))
    except (Exception, KeyboardInterrupt) as error:
        streams.say(f"it broke: {type(error).__name__}")
    return BROKEN


if __name__ == "__main__":
    sys.exit(main())
