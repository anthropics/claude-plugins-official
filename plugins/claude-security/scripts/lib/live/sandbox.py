"""Commands inside the plugin's sandbox: what a scan is shown, and how it signs in."""

from __future__ import annotations

import errno
import os
import re
import shlex
import stat
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from lib import console, display, git, plugin, strictjson
from lib.sandbox import provider
from lib.sandbox.plan import BROKEN, HIDDEN_FOLDERS, SWAPPED, SandboxError, identity
from lib.strictjson import JsonMap, as_map, clean, is_str, maps

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

_PROGRAM = plugin.ROOT / "scripts/sandbox.py"
_LINUX = sys.platform == "linux"
_WINDOWS = os.name == "nt"
_MINUTES = 24 * 60
_USAGE = 2
# The session's settings leave out what starts programs, holds secrets or changes how it runs.
_LEFT_OUT = frozenset({
    "env",
    "hooks",
    "statusLine",
    "subagentStatusLine",
    "fileSuggestion",
    "otelHeadersHelper",
    "enabledPlugins",
    "extraKnownMarketplaces",
    "additionalMarketplaces",
    "pluginConfigs",
    "processWrapper",
    "agent",
    "disableAllHooks",
    "apiKeyHelper",
    "awsAuthRefresh",
    "awsCredentialExport",
    "gcpAuthRefresh",
    "proxyAuthHelper",
})
_MANAGED = ("/etc/claude-code", "/Library/Application Support/ClaudeCode")
_REFUSING = (
    *("allowedProviders", "enforceAnthropicSignIn", "forceLoginGatewayUrl", "forceLoginMethod"),
    *("forceLoginOrgUUID", "disableSideloadFlags"),
)
_LOADS_CODE = (
    "BASH_ENV",
    "CLOUDSDK_PYTHON",
    "NODE_OPTIONS",
    "NODE_PATH",
    "PERL5LIB",
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONUSERBASE",
    "RUBYLIB",
)
_KEYS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")
KEY_HELPER, AWS_HELPER = _HELPERS = ("apiKeyHelper", "awsCredentialExport")
_SIGN_WITH_AWS = frozenset({
    "CLAUDE_CODE_USE_ANTHROPIC_AWS",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_MANTLE",
})
_SIGN_INS = (*_KEYS, KEY_HELPER, "ANTHROPIC_FEDERATION_RULE_ID", "ANTHROPIC_PROFILE")
# What Claude Code loads from its folder and a scan need not write. Each shows read-only.
LOADED_FOLDERS = (
    *("agents", "commands", "dev-mods", "output-styles", "plugins/cache", "plugins/marketplaces"),
    *("rules", "session-env", "skills", "workflows"),
)
LOADED_FILES = {
    ".claude.json": "{}",
    "CLAUDE.md": "",
    "loop.md": "",
    "settings.json": "{}",
    "remote-settings.json": "",
    "remote-settings.json.signature.json": "",
    "remote-settings.json.signature-iat.json": "",
    "remote-settings.json.synced-at": "",
    "plugins/installed_plugins.json": '{"version": 2, "plugins": {}}',
    # A file, so that no folder of this name can be made.
    "shell-snapshots": "",
}
# How the sandbox's own lines begin, and one that does not hold here: the command hands that env on.
_OWN = "sandbox: "
_NOT_HERE = f"{_OWN}the env of the managed settings is not used"
_CLOSED = (
    f"{_OWN}it cannot read the folder to scan. With --sudo, a folder that is closed to others must "
    "be yours and have your primary group"
)
# Only the process that the sandbox starts can reach the model, so the shell execs the command.
_ENTER = (
    'export CLAUDE_CONFIG_DIR="$2" CLAUDE_CODE_SHELL="$3" GIT_CONFIG_GLOBAL=/dev/null '
    'PYTHONNOUSERSITE=1; cd "$1" && command -p ls >/dev/null '
    f'|| {{ echo {shlex.quote(_CLOSED)} >&2; exit {BROKEN}; }}; shift 3; exec "$@"'
)
_SHELL = plugin.ROOT / "scripts/shell/bash"
# How the relay and the keeper tell of a refused call. In the check, each is a try of its own.
_TRIED = f"{_OWN}refused a "
# Claude Code drops a byte order mark from its JSON files.
_ENCODING = "utf-8-sig"


def config_folder() -> Path:
    """The folder that CLAUDE_CONFIG_DIR names, or ~/.claude where it is empty or not set."""
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude").expanduser().resolve()


def store_folder() -> Path:
    """The folder in which Claude Code keeps its login."""
    named = os.environ.get("CLAUDE_CONFIG_DIR", "")
    named = os.environ.get("CLAUDE_SECURESTORAGE_CONFIG_DIR", named)
    return Path(named or "~/.claude").expanduser().resolve()


def state_file() -> Path:
    """The file in which Claude Code keeps the account and its own state."""
    config = config_folder()
    with suppress(OSError):
        if (config / ".config.json").stat().st_size:
            return config / ".config.json"
    return (config if os.environ.get("CLAUDE_CONFIG_DIR") else Path.home()) / ".claude.json"


def stored(path: Path) -> JsonMap:
    """The JSON object in one of Claude Code's files. It is empty if the file holds none."""
    with suppress(OSError, ValueError):
        return as_map(strictjson.load(path, _ENCODING))
    return {}


def _user_settings() -> JsonMap:
    """The user's settings. They are empty if the file is absent, blank, or JSON that is no object.
    Raises OSError for a file that cannot be read, since the scan could lose its deny rules."""
    path = config_folder() / "settings.json"
    try:
        if path.is_file() and not path.read_text(encoding=_ENCODING).strip():
            return {}
        return as_map(strictjson.load(path, _ENCODING))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        msg = f"{path} cannot be read, so the scan could lose its deny rules: {error}"
        raise OSError(msg) from error


def installed() -> str:
    """The plugin's id, if Claude Code has this folder installed for every project."""
    listing = stored(config_folder() / "plugins/installed_plugins.json")
    for name, records in as_map(listing.get("plugins")).items():
        for record in maps(records):
            here = Path(clean(record.get("installPath"))).resolve() == plugin.ROOT
            if here and clean(record.get("scope")) in {"user", "managed"}:
                return name
    return ""


def _managed_settings() -> list[JsonMap]:
    """The organisation's settings, in the order in which Claude Code lays them over each other."""
    settings: list[JsonMap] = []
    for folder in map(Path, _MANAGED):
        settings.append(stored(folder / "managed-settings.json"))
        settings += map(stored, sorted(folder.glob("managed-settings.d/[!.]*.json")))
    return settings


def session_variables() -> dict[str, str]:
    """The environment, with what Claude Code's state file and settings files add to it. PATH stays
    as clear_path_of left it, since programs outside the sandbox are found there. HOME and
    CLAUDE_CONFIG_DIR stay too."""
    settings = (stored(state_file()), _user_settings(), *_managed_settings())
    added = {k: v for each in settings for k, v in provider.settings_env(each).items()}
    for name in ("HOME", "CLAUDE_CONFIG_DIR"):
        added.pop(name, None)
    return {**os.environ, **added, "PATH": os.pathsep.join(os.get_exec_path())}


def _shared_top(top: Path) -> Path:
    """For a linked worktree, the folder above the git folder that it shares, or that git folder
    itself if its name is not .git. Else `top`."""
    with suppress(OSError, ValueError):
        if (top / ".git").is_file():
            pointer = (top / ".git").read_text(encoding="utf-8", errors="replace")
            own = top / pointer.partition("gitdir:")[2].strip()
            if (own / "commondir").is_file():
                named = (own / "commondir").read_text(encoding="utf-8", errors="replace")
                shared = Path(os.path.realpath(own / named.strip()))
                if shared.is_dir():
                    return shared.parent if shared.name == ".git" else shared
    return top


def _project_settings(root: Path) -> dict[Path, JsonMap]:
    """The settings files of the project at `root`, in the order in which a later one wins."""
    top = git.holder_of(str(root)) or root
    shared, local = ".claude/settings.json", ".claude/settings.local.json"
    files = (top / shared, root / shared, root / local, top / local, _shared_top(top) / local)
    user = config_folder() / "settings.json"
    return {file: stored(file) for file in dict.fromkeys(files) if not _same(file, user)}


def routes_not_loaded(
    root: Path, variables: Mapping[str, str], *, by_command: bool = False
) -> dict[str, Path]:
    """What the project's settings files set to choose a host, a way to it or a sign-in, and
    `variables` do not name, each with its file. The session does not load those files.
    ANTHROPIC_API_KEY names KEY_HELPER too. With `by_command`, where a command prints the
    credential, no name of _SIGN_INS counts, nor AWS_HELPER."""
    read = _project_settings(root).items()
    given = {k: (v, f) for f, settings in read for k, v in provider.settings_env(settings).items()}
    given |= {k: (v, f) for f, each in read for k in _HELPERS if is_str(v := each.get(k))}
    held = {**variables, KEY_HELPER: ""} if "ANTHROPIC_API_KEY" in variables else variables
    on_aws = _SIGN_WITH_AWS.intersection(provider.clouds_on(variables))
    also = () if by_command else (*_SIGN_INS, *([AWS_HELPER] if on_aws else []))
    names = provider.routes_lacking({k: v for k, (v, _) in given.items()}, held, also)
    return {name: given[name][1] for name in names}


def uses_login(variables: Mapping[str, str]) -> bool:
    """Whether the session signs in with what Claude Code has stored, and not with a variable."""
    return not provider.clouds_on(variables) and not any(map(variables.get, _KEYS))


def has_key_helper() -> bool:
    """Whether the settings name a command that Claude Code would ask for its key."""
    return any(each.get("apiKeyHelper") for each in (_user_settings(), *_managed_settings()))


def managed_names() -> set[str]:
    """The variables that the managed settings set."""
    return {name for each in _managed_settings() for name in provider.settings_env(each)}


def refusing_settings() -> list[str]:
    """The managed settings that can keep Claude Code from starting in the sandbox."""
    merged = {name: value for each in _managed_settings() for name, value in each.items()}
    return [name for name in _REFUSING if merged.get(name, False) is not False]


def kept_settings() -> dict[str, object]:
    """The user's settings that a session in the sandbox keeps."""
    return {k: v for k, v in _user_settings().items() if k not in _LEFT_OUT}


def clear_path_of(root: Path) -> None:
    """Take relative entries and the folders in `root` off PATH, and the current folder out of
    Windows's search for a program: a program found there would run outside the sandbox."""
    for env in (os.environ, git.ENV):
        folders = filter(os.path.isabs, os.get_exec_path(env))
        outside = (f for f in folders if not Path(os.path.realpath(f)).is_relative_to(root))
        env["PATH"] = os.pathsep.join(outside)
        env["NoDefaultCurrentDirectoryInExePath"] = "1"


def _may_lead_into(root: Path, value: str) -> bool:
    """Whether a path in `value` lies in `root` or passes through it, or cannot be judged. A path
    begins at the start of `value`, or after a blank, a quote, "=" or the separator of lists."""
    text = os.path.expanduser(os.path.expandvars(value))  # noqa: PTH111
    signs = rf"\s=\"'{os.pathsep}"
    if os.pardir in re.split(f"[{signs}/]", text) or re.search(r"[$`]|\A~", text):
        return True
    ends = [end.start() for end in re.finditer(rf"[{signs}/]|\Z", text)]
    for start in (0, *(cut.end() for cut in re.finditer(f"[{signs}]", text))):
        for end in (at for at in ends if at > start):
            path = os.path.realpath(Path("/", text[start:end]))
            if Path(path).is_relative_to(root):
                return True
            if text.startswith("/", end) and not os.path.lexists(path):
                break
    return False


def unset_code_variables(root: Path) -> None:
    """Unset each variable of _LOADS_CODE that may lead into `root`, with a warning. `root` must be
    a real path."""
    for name in _LOADS_CODE:
        if _may_lead_into(root, os.environ.get(name, "")):
            del os.environ[name]
            why = 'names the folder to scan, or holds a ".." or a sign that a shell expands'
            console.warn(f"{name} {why}, so the command has unset it")


def _others_write(path: Path, status: os.stat_result) -> bool:
    """Whether the mode in `status`, of what `path` leads to, can let a user other than its owner
    write: all may, or a group may where it is not the owner's own, a name is unknown, or a POSIX
    access list stands. OSError if that list cannot be looked at."""
    import grp
    import pwd

    if status.st_mode & stat.S_IWOTH:
        return True
    if not status.st_mode & stat.S_IWGRP:
        return False
    if sys.platform == "linux":
        try:
            return bool(os.getxattr(path, "system.posix_acl_access"))
        except OSError as error:
            if error.errno not in {errno.ENODATA, errno.EOPNOTSUPP}:
                raise
    with suppress(KeyError):
        owner, group = pwd.getpwuid(status.st_uid).pw_name, grp.getgrgid(status.st_gid)
        first = (user.pw_name for user in pwd.getpwall() if user.pw_gid == status.st_gid)
        return {group.gr_name, *group.gr_mem, *first} != {owner}
    return True


def _distrust(path: Path, owners: set[int]) -> str | None:
    """Why `path` is not to be trusted: another user owns it or what it leads to, or may write
    that, or one of them cannot be looked at. None where `owners` own both, and by its mode no
    user but its owner may write what it leads to."""
    try:
        if os.lstat(path).st_uid not in owners:
            return "belongs to another user"
        status = path.stat()
        if status.st_uid not in owners:
            return "leads to a folder of another user"
        if _others_write(path, status):
            return "can be written by another user"
    except OSError as error:
        return f"cannot be looked at ({error.strerror})"
    return None


def _owners(root: Path) -> set[int]:
    """The caller, and whoever owns `root`."""
    return {os.geteuid(), root.stat().st_uid}


def _pinned(folder: Path, owners: set[int]) -> str:
    """The option that shows `folder` only if the same folder lies there when the sandbox opens it.
    SandboxError if it cannot be opened through no link, or none of `owners` owns it."""
    from lib.sandbox.results import folder_of

    with suppress(OSError), folder_of(str(folder / "any")) as found:
        status = os.fstat(os.dup(found))
        if status.st_uid in owners:
            return f"--read-same={identity(status)}:{folder}"
    msg = f"{display.written_out(str(folder))} {SWAPPED}"
    raise SandboxError(msg)


def _trusted(root: Path, *paths: Path, scan_from: Path | None = None) -> bool:
    """Whether the caller or whoever owns `root` owns each of `paths`, and what it leads to, and by
    its mode no user but its owner may write that. Else it warns, and names `scan_from`, if given,
    as the folder to scan from."""
    owners = _owners(root)
    for path in paths:
        if why := _distrust(path, owners):
            way_on = scan_from and (
                f". If {display.written_out(str(scan_from))} is a repository, and you trust all "
                "who can write there, scan from there with --scope"
            )
            console.warn(
                f"{display.written_out(str(path))} {why}, so the command does not add the "
                f"repository to what the sandbox shows{way_on or ''}"
            )
            return False
    return True


def _may_be_there(path: Path) -> bool:
    try:
        os.lstat(path)
    except OSError as error:
        return error.errno not in {errno.ENOENT, errno.ENOTDIR}
    return True


def _with_settings(*folders: Path) -> list[Path]:
    """The git folders, and each settings file that may lie in them."""
    files = (folder / name for folder in folders for name in ("config", "config.worktree"))
    return [*folders, *filter(_may_be_there, files)]


def led_astray(given: Path, root: Path) -> str | None:
    """Why the scan must not start: the caller or the superuser does not have the real path `root`
    to themselves, and `given`, from PWD, is another name. With no other name it warns."""
    why = _distrust(root, {0, os.geteuid()})
    if not why:
        return None
    named = os.path.abspath(Path(os.environ.get("PWD", ""), given))
    real = display.written_out(str(root))
    if named == str(root):
        console.warn(f"{real} {why}: scan it only if you trust all who can write there")
        return None
    link = display.written_out(named)
    return f"{link} leads to {real}, which {why}. To scan it, name that path"


def find_program(name: str) -> Path | None:
    """The program on PATH, from absolute entries alone, and on Windows with an ending that can
    start."""
    endings = [".COM", ".EXE", ".BAT", ".CMD"] if _WINDOWS else [""]
    folders = filter(os.path.isabs, os.get_exec_path())
    places = (Path(folder, name + ending) for folder in folders for ending in endings)
    return next((p for p in places if os.path.isfile(p) and os.access(p, os.X_OK)), None)


def refuse_hidden(claude: Path) -> None:
    """Raises SandboxError where the real path of `claude` lies in one of HIDDEN_FOLDERS."""
    real = claude.resolve()
    if any(map(real.is_relative_to, HIDDEN_FOLDERS)):
        msg = (
            f"{real} lies in a folder that the sandbox hides. If it wraps Claude Code, and the "
            "scan may go without what it adds, put the folder of Claude Code itself first on PATH. "
            "Else install Claude Code in another folder"
        )
        raise SandboxError(msg)


def newer_python() -> str:
    """The newest of python3.10 to python3.14 in this Python's real folder, or nothing."""
    if not sys.executable:
        return ""
    folder = Path(os.path.realpath(sys.executable)).parent
    beside = (folder / f"python3.{minor}" for minor in range(14, 9, -1))
    return next((str(p) for p in beside if os.path.isfile(p) and os.access(p, os.X_OK)), "")


def refuse_other_systems() -> None:
    """Raises SandboxError where the command has no sandbox."""
    if not _LINUX:
        msg = "the command's sandbox runs on Linux alone"
        raise SandboxError(msg)


def _same(path: Path, other: Path) -> bool:
    """Whether the two paths lead to one file, by whatever links or relative steps."""
    with suppress(OSError):
        return path.samefile(other)
    return False


def _git_folder(root: Path) -> list[Path]:
    """The repository that holds `root`, a real path, and the git folder of a worktree or a
    submodule. It is `root` alone where no repository holds it, where that one holds the home
    folder too or does not hold `root`, or where _trusted() refuses a repository above `root`, its
    `.git`, a folder from there down to `root`, the git folder that a `.git` file points to, a
    worktree's repository, or a settings file in one of these git folders."""
    top = git.holder_of(str(root))
    if top is None or Path.home().resolve().is_relative_to(top):
        return [root]
    if not root.is_relative_to(top):
        return [root]
    way = [step for step in (root, *root.parents) if step.is_relative_to(top)]
    plain = os.path.isdir(top / ".git") and os.path.realpath(top / ".git") == str(top / ".git")
    judged = (*way, *_with_settings(top / ".git"))
    if top != root and not _trusted(root, *judged, scan_from=top if plain else None):
        return [root]
    if (top / ".git").is_dir() or (top / ".git").is_symlink():
        return [top]
    pointer = (top / ".git").read_text(encoding="utf-8", errors="replace")
    own = Path(os.path.realpath(top / pointer.partition("gitdir:")[2].strip()))
    outer = [own.parent.parent] if own.parent.name == "worktrees" else []
    if not _trusted(root, *_with_settings(own, *outer)):
        return [root]
    # The scanned folder names this path, so the path must lie outside it and name it in turn.
    if own.is_relative_to(top):
        return [top]
    tree = git.run("/", "config", "--file", str(own / "config"), "core.worktree")
    if tree and _same(own / tree, top):
        return [top, own]
    if own.parent.name == "worktrees":
        with suppress(OSError):
            named = (own / "gitdir").read_text(encoding="utf-8", errors="replace").strip()
            if _same(own / named, top / ".git"):
                return [top, own.parent.parent]
    if os.path.isfile(own / "HEAD"):
        console.warn(
            f"the git folder {display.written_out(str(own))} does not name the scanned folder in "
            "turn, so the sandbox hides it and git fails there, unless --allow-read names it"
        )
    return [top]


def holds(errors: str, *left_out: str) -> str:
    """`errors` less the sandbox's line that does not hold for the command, and less the lines
    that begin with one of `left_out`."""
    lines = errors.splitlines(keepends=True)
    return "".join(s for s in lines if not s.startswith((_NOT_HERE, *left_out)))


def own_lines(errors: str) -> str:
    """What scripts/sandbox.py itself says in `errors`."""
    return "".join(s for s in errors.splitlines(keepends=True) if s.startswith(_OWN))


class Sandbox:
    """The limits of one scan of the real path `root`.

    `run` is the scan's own folder, `variables` are the
    relay's, `passed` names those that the session sees too, `reads` are more paths to show, and
    `options` go to sandbox.py."""

    def __init__(
        self,
        root: Path,
        run: Path,
        variables: Mapping[str, str],
        passed: Iterable[str],
        reads: Sequence[Path],
        options: Sequence[str],
        python: str,
    ) -> None:
        code = _git_folder(root)
        for folder in (*code, *reads):
            if any(path.is_relative_to(folder) for path in (config_folder(), store_folder(), run)):
                msg = (
                    f"{folder} holds Claude Code's own folder or the scan's temporary folder, "
                    "which the sandbox must hide"
                )
                raise SandboxError(msg)
        self._root: Path = root
        self._run: Path = run
        # Claude Code loads the last folder too, since --add-dir names the one above it.
        folders = [*(run / "home" / name for name in LOADED_FOLDERS), run / "reports/.claude"]
        for folder in folders:
            folder.mkdir(parents=True)
        for name, text in LOADED_FILES.items():
            (run / "home" / name).write_text(text, encoding="utf-8")
        fixed = (run / "start", *folders, *(run / "home" / name for name in LOADED_FILES))
        owners = _owners(root)
        below = {root}.difference(code)
        self._variables: Mapping[str, str] = variables
        self._start: list[str] = [
            *(python, "-I", "-S", str(_PROGRAM), f"--minutes={_MINUTES}", *options),
            *(_pinned(folder, owners) for folder in code),
            *(f"--read={path}" for path in (*below, *reads, *fixed)),
            *(f"--env={name}" for name in passed),
        ]

    def check(self) -> None:
        """Try the walls from inside. With --sudo, sudo can ask for a password here."""
        done = subprocess.run(
            [*self._start, "--minutes=5", "--check", str(self._run)],
            cwd="/",
            env=self._variables,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        if failed := re.findall(r"(?m)^FAILED (.+)$", done.stdout):
            msg = f"the sandbox did not hold ({'; '.join(failed)}), so nothing was scanned"
            raise SandboxError(msg)
        errors = holds(done.stderr, _TRIED)
        if done.returncode:
            said = errors.strip()
            # After a usage error the reason stands below the list of options.
            said = said.rpartition("\n")[2] if done.returncode == _USAGE else said
            msg = f"the sandbox did not start (exit code {done.returncode}): {said}"
            raise SandboxError(msg)
        # Its limits on this machine, such as a mount that does not show.
        sys.stderr.write(own_lines(errors))

    def popen(self, command: Sequence[str]) -> subprocess.Popen[bytes]:
        """Start `command` in the scan root, with three pipes. Its program file shows inside."""
        program, *rest = os.path.realpath(command[0]), *command[1:]
        places = (self._root, self._run / "home", _SHELL)
        enter = ("/bin/sh", "-c", _ENTER, "sh", *map(str, places))
        return subprocess.Popen(
            [*self._start, f"--read={program}", str(self._run), "--", *enter, program, *rest],
            cwd=self._run / "reports",
            env=self._variables,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
