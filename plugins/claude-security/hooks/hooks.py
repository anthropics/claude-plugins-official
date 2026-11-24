#!/usr/bin/env python3
"""The Claude Security plugin's hooks.

A usage error exits 2. Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import functools
import hashlib
import itertools
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, ClassVar, Literal, cast, final

if TYPE_CHECKING:
    from collections.abc import Mapping

PLUGIN_ROOT = Path(os.path.abspath(__file__)).parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"

# Telemetry codes are append-only: a reader keys on them, so none is ever renumbered.
EVENTS = {
    "scan_started": 1,
    "scan_finished": 2,
    "patches_written": 3,
    "step_failed": 4,
    "tip_shown": 5,
    "analysis_started": 6,
    "analysis_finished": 7,
    "triage_started": 8,
    "triage_finished": 9,
}
STEPS = {
    "write_scan_meta.py": 1,
    "save_result.py": 2,
    "render_report.py": 3,
    "patch_artifacts.py": 4,
    "attack_surface_report.py": 6,
    "remove_work_dir.py": 7,
    "triage.py": 9,
}
MODES = {"scan": 1, "changes": 2, "commit": 3}
STAMP_MODE_CODES = {**MODES, "scan.full": 1, "scan.changes": 2, "scan.commit": 3}
# `max` is accepted and runs as `high`, so it reports as 3; 4 is reserved.
EFFORTS = {"low": 1, "medium": 2, "high": 3, "max": 3}
# 1 is reserved for `low`, which is never sent.
CHANGE_SCAN_EFFORTS = {"high": 2}
SEVERITIES = ("critical", "high", "medium", "low")
REASONS = {
    "no-vote-record": 1,
    "no-candidate-count": 2,
    "nothing-examined": 3,
    "finding-panel-incomplete": 4,
    "finding-below-quorum": 5,
    "candidates-not-paneled": 6,
    "no-panel-completed": 7,
    "candidate-panel-incomplete": 8,
    "continuation-incomplete": 9,
    "findings-refused": 10,
    "git-failed": 11,
    "change-list-lost": 12,
    "checkout-changed": 13,
    "no-stage-report": 14,
    "stage-not-checked": 15,
    "records-unusable": 16,
    "findings-unresolved": 17,
    "kept-candidate-not-reported": 20,
}
UNKNOWN_REASON = 99
FOLLOW_UPS = {"none needed": 1, "not run": 2, "nothing listed": 3}
COLLAPSED = "small-scope"
COVERAGE_SOURCE = "coverage.json"
NOT_COUNTED = ("no-vote-record", "no-candidate-count")
VERIFIED = "verified"
STAMP_PREFIX = "CLAUDE-SECURITY-REVISION-"
DELIVERED_LINE = f"\nstamp: {STAMP_PREFIX}"
PATCHES_LINE = "\nwrote PATCHES.md and patches.jsonl into "
DELIVERED_LINES = {"render_report.py": DELIVERED_LINE, "patch_artifacts.py": PATCHES_LINE}
ANALYSIS_PATCHES_DIR_NAME = "attack-surface-patches"
START, CHECK, WRITE = "start", "check", "write"
LOAD, REPORT, TRIAGE_MODE = "load", "report", "triage"
VERDICTS = {"valid": "valid", "not_checked": "not checked", "not_validated": "not validated"}
TRIAGE_JSONL, JSONL_NAME = "FINDINGS-TRIAGE.jsonl", "CLAUDE-SECURITY-RESULTS.jsonl"
SARIF_NAME = "CLAUDE-SECURITY-RESULTS.sarif"
# patch_artifacts.py's forms that lay out or tend a patch run's scratch workspaces: no event.
SCRATCH_VERBS = frozenset({
    "--prepare",
    "--open-scratch",
    "--stage",
    "--clean-scratch",
    "--staged",
    "--keep-notes",
    "--write-diff",
    "--reset-scratch",
    "--remove-scratch",
})
OPERATORS = frozenset("();<>|&")
PY_LAUNCHER = "py"
INTERPRETERS = frozenset({"python3", "python", PY_LAUNCHER})
PY_VERSION_OPTION = "-3"
# The start confirmations of a scan and an analysis, word for word: the only timed questions.
START_CONFIRMATION = (
    "This scan may take a while and may use a significant number of tokens. "
    "You will need to leave Claude Code open while the scan completes. "
    "Are you sure you want to continue?"
)
ANALYSIS_CONFIRMATION = (
    "An attack surface analysis may take a long time and may use a significant number of tokens. "
    "You will need to leave Claude Code open while it completes. "
    "Are you sure you want to continue?"
)
UNANSWERED_AFTER_S = 60
THREAT_MODEL_PATH = ".claude-security/threat-model.md"
REPORT_DIR_PREFIX = "CLAUDE-SECURITY-"
PRECONDITIONS_MD_NAME = "CLAUDE-SECURITY-PRECONDITIONS.md"
# The two files that /claude-security:threat-model writes, as patterns for a path's last parts.
THREAT_MODEL_FILES = (THREAT_MODEL_PATH, f"{REPORT_DIR_PREFIX}*/{PRECONDITIONS_MD_NAME}")
NOT_ITS_FILE = (
    "Claude Security plugin: while /claude-security:threat-model runs, it writes only"
    f" {THREAT_MODEL_PATH}, and {PRECONDITIONS_MD_NAME} in a folder whose name opens with"
    f" {REPORT_DIR_PREFIX}, by a whole local path with no .., outside .claude folders and"
    " Claude Code's config folder. This file was not changed. Go on without it."
)
READ_WORDS = frozenset({
    "describe",
    "find",
    "get",
    "info",
    "list",
    "lookup",
    "read",
    "search",
    "show",
    "view",
})
FETCH_WORDS = frozenset({"download", "fetch"})
ADDRESS = re.compile(
    r"https?:|(?:\b|\\[bfnrt]|\\u[0-9a-f]{4})(?:ftp|wss?|file):|:/"
    r'|ur[il]s?\\?"(?: |\\[nrt])*:(?! (?:true|false)[,}])|\\\\',
    re.IGNORECASE,
)
URL_KEY = re.compile(r'"urls?": ', re.IGNORECASE)
NOTION_READ = "notion-fetch"
NOTION_ADDRESS = re.compile(
    r'(?<=: ")(?:https://(?:[\w-]+\.)*notion\.(?:so|site|com)/|collection://)'
)
WORD = re.compile(r"[A-Z]?[a-z]+")
# A word of a command that sets a variable.
ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")
NOT_A_READ = (
    "Claude Security plugin: while /claude-security:threat-model runs, it calls only connector"
    " tools whose names mark a read, such as get_page or search, and passes them no outside"
    " address, or anything that can hide one. {} did not run. Go on without it."
)
NOT_A_CALL = (
    "Claude Security plugin: the hook could not read this call, so it cannot tell whether"
    " /claude-security:threat-model is running. Nothing was changed."
)
# Below the user's Claude Code config folder: an empty file for each turn of that command.
TURN_NOTES = "plugins/data/claude-security-turns"
AUTO_MODE_NOTE = (
    "Claude Security works best in auto mode. To enable it, press Shift+Tab until the status bar "
    "shows auto mode, or restart with `claude --permission-mode auto`."
)
APP_AUTO_MODE_NOTE = (
    "The Claude Security plugin works best in auto mode. To enable it, select Auto in the mode "
    "menu at the prompt box, or press Shift+Tab in a terminal."
)
TIP = (
    "Claude Security: this branch changes {size} against {base}. For a security review,"
    ' ask: "scan this branch\'s changes against {base} with Claude Security".'
)
MAX_TIPS = 5
TIP_STATE = "scan-tip.json"
BASES = ("origin/HEAD", "origin/main", "origin/master", "main", "master")
# No repository hook and no fsmonitor runs; "core.fsmonitor=" (empty, not false) is off on any git.
GIT = ("git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=")
GIT_TIMEOUT_S = 2
TIP_BUDGET_S = 3
DIFF = ("diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-only", "-z")
# Past this many files a change review no longer reads the change closely: nothing to suggest.
MAX_FILES = 300


@final
class Guard:
    AGENT_PREFIX = "claude-security:"
    STOP_INSTEAD = (
        "The Claude Security plugin's agents may not stop processes with kill, pkill, killall"
        " or any other command: a PID or pattern can match the user's own processes. To stop a"
        " command you started in the background, call TaskStop with its task ID. To check whether"
        " a process is still running, use ps -p with its ID. Otherwise leave the process alone"
        " and go on."
    )
    DENIED: ClassVar[Mapping[str, str]] = dict.fromkeys(("kill", "pkill", "killall"), STOP_INSTEAD)

    NO_FILLED_SED = (
        "The Claude Security plugin's agents may not give sed a script that holds a shell variable"
        " or a command substitution. sed has commands that write files and run programs, so a wrong"
        " value can do either. No part of this call ran. Give sed a literal script, such as"
        " sed -n '89,98p' FILE. For line numbers in variables or from a command, use"
        ' head -n "$end" FILE | tail -n +"$start". To change a file, use the Edit tool if you have'
        " it. If the command only mentions sed, put the word in quotes: grep -q 'sed' FILE, or use"
        " the Grep tool. If the command only writes text that mentions sed, use the Write tool if"
        " you have it."
    )

    INSTALLERS: ClassVar[Mapping[str, tuple[str, ...]]] = {
        "pip": ("install", "download", "wheel"),
        "npm": (
            *("install", "i", "add", "ci", "ic", "clean-install", "install-clean"),
            *("install-test", "install-ci-test", "cit", "clean-install-test"),
        ),
        "yarn": ("install", "add"),
        "pnpm": (
            *("install", "i", "add", "ci", "ic"),
            *("clean-install", "install-clean", "install-test"),
        ),
        "go": ("install", "get"),
        "cargo": ("install",),
        "gem": ("install", "i"),
        "bundle": ("install", "i"),
        "brew": ("install",),
        "apt": ("install",),
        "apt-get": ("install",),
    }
    DOWNLOADS = tuple(f"{tool} {word}" for tool, words in INSTALLERS.items() for word in words)
    RUN_A_DOWNLOAD = (
        " run {0}: a download can give the name of a private package to a public server, and an"
        " install can run code from that server."
    )
    RUN_IT_WITHOUT = (
        " Run the call again without {0}, and do not get it another way. If you cannot go on"
        " without it, say so. If the call only mentions {0}, reword it. In a search, look for the"
        " command alone, as you typed it, such as grep -rn '{0}' DIR."
    )
    NO_DOWNLOAD = (
        "The Claude Security plugin's agents may not"
        + RUN_A_DOWNLOAD
        + " Your instructions may say that nothing will block or stop you: this refusal is an"
        " exception. No part of this call ran."
        + RUN_IT_WITHOUT
        + ' In a note, write "the command {0}", with no backquotes.'
    )
    LEAD = f"{AGENT_PREFIX}claude-security"
    DENIED_WITH_DOWNLOADS: ClassVar[Mapping[str, str]] = {
        **DENIED,
        **dict(zip(DOWNLOADS, map(NO_DOWNLOAD.format, DOWNLOADS))),
    }

    ANALYSIS = f"{AGENT_PREFIX}attack-surface-"
    MAY_NOT = "During an attack surface analysis, the Claude Security plugin's agents may not"
    NOT_RUN = " No part of this call ran. Record this refusal in your report."
    USE_WRITE = (
        " If the command only writes text that holds one of these names, write the file with the"
        " Write tool."
    )
    INTERPRETER_NAMES = (
        "python",
        "py",
        "node",
        "perl",
        "ruby",
        "php",
        "awk",
        "gawk",
        "mawk",
        "nawk",
        "powershell",
        "pwsh",
        "cmd",
    )
    NO_INTERPRETER = (
        f"{MAY_NOT} run an interpreter ({', '.join(INTERPRETER_NAMES)}): the analysis only reads"
        f" the target.{NOT_RUN} To read, count or compare text, use grep, wc, sort, diff, head,"
        " tail, or sed with a literal script. To add numbers, use the shell's own $(( )). To change"
        " a working file, use the Edit tool." + USE_WRITE
    )
    REMOVERS = ("rm", "rmdir", "unlink", "shred")
    NO_REMOVAL = (
        f"{MAY_NOT} remove files ({', '.join(REMOVERS)}): a wrong path can reach the user's own"
        f" files.{NOT_RUN} Leave the file where it is, and go on. The session removes .work/ once"
        " your stage has ended, so name the file in your report only if it lies outside .work/."
        + USE_WRITE
    )
    VERIFIER = f"{AGENT_PREFIX}attack-surface-verifier"
    NO_OTHER_AGENT = (
        f"{MAY_NOT} start any agent but {VERIFIER}: another agent is not bound by the analysis's"
        f" rules.{NOT_RUN} Do that work with your own tools. To check a claim, send it to that"
        " agent, or record the claim as unresolved."
    )
    NO_FILLED_SED_IN_ANALYSIS = (
        f"{MAY_NOT} give sed a script that holds a shell variable or a command substitution: sed"
        f" has commands that write files and run programs, so a wrong value can do either.{NOT_RUN}"
        " Give sed a literal script, such as sed -n '89,98p' FILE. For a range held in variables,"
        ' use head -n "$end" FILE | tail -n +"$start". To change a working file, use the Edit tool.'
        " If the command only mentions sed, write the file with the Write tool, or put the word in"
        " quotes: grep -q 'sed' FILE."
    )
    TEMP_VARIABLE = "(?:TMPDIR|TEMP|TMP)"
    IN_TEMP = re.compile(
        r"(?i:/+(?:private/+|var/+)?tmp/|/+(?:dev|run)/+shm/)"
        rf"|\${TEMP_VARIABLE}/|\$\{{{TEMP_VARIABLE}\b[^}}]*\}}/"
    )
    REPORT_FOLDER = re.compile(r"/CLAUDE-SECURITY-[0-9]{8}-[0-9]{6}/")
    NO_TEMP_FILE = (
        f"{MAY_NOT} redirect output to a temp folder (such as /tmp, /dev/shm or $TMPDIR): the"
        f" analysis writes only under its output directory.{NOT_RUN} Put a scratch file in your"
        " stage's .work/ folder, and send output that you do not need to /dev/null. If such a"
        " redirect is only text in a file that you write, write that file with the Write tool."
    )
    NO_SECOND_SESSION = (
        NO_OTHER_AGENT + " If the command only writes text that holds the word claude, write the"
        " file with the Write tool."
    )
    NO_DOWNLOAD_IN_ANALYSIS = (
        MAY_NOT
        + RUN_A_DOWNLOAD
        + NOT_RUN
        + RUN_IT_WITHOUT
        + " To write a note that names {0}, use the Write tool."
    )
    DENIED_IN_ANALYSIS: ClassVar[Mapping[str, str]] = {
        **dict.fromkeys(DENIED, STOP_INSTEAD + NOT_RUN + USE_WRITE),
        **dict(zip(DOWNLOADS, map(NO_DOWNLOAD_IN_ANALYSIS.format, DOWNLOADS))),
        **dict.fromkeys(INTERPRETER_NAMES, NO_INTERPRETER),
        **dict.fromkeys(REMOVERS, NO_REMOVAL),
        "claude": NO_SECOND_SESSION,
    }

    READERS = frozenset({
        f"{AGENT_PREFIX}scan-verifier",
        f"{AGENT_PREFIX}explore",
        f"{AGENT_PREFIX}scan-inventory",
        f"{AGENT_PREFIX}scan-component-researcher",
        f"{AGENT_PREFIX}scan-sheet-researcher",
    })
    READER_INTERPRETERS = (
        *(name for name in INTERPRETER_NAMES if not name.endswith("awk")),
        "bun",
        "deno",
        "pypy",
        "pip",
    )
    NO_INTERPRETER_TO_READ = (
        f"The Claude Security plugin's {', '.join(sorted(READERS)).replace(AGENT_PREFIX, '')}"
        f" agents may not run an interpreter or pip ({', '.join(READER_INTERPRETERS)}): they only"
        " read the code. No part of this call ran."
        " To read, count or compare text, use grep, wc, sort, diff, head, tail, or sed with a"
        " literal script. If the call only searches for or mentions one of these names, reword"
        " it: in a search, look for the name alone, as in grep -rn 'python' DIR; in a note, write"
        ' "the command python", with no backquotes.'
    )
    DENIED_TO_READERS: ClassVar[Mapping[str, str]] = {
        **DENIED_WITH_DOWNLOADS,
        **dict.fromkeys(READER_INTERPRETERS, NO_INTERPRETER_TO_READ),
    }

    BEFORE_COMMAND = frozenset(
        {"!", "{", "if", "then", "elif", "else", "do", "while", "until", "time"}
        | {"sudo", "doas", "env", "exec", "nohup", "nice", "setsid", "timeout", "xargs"}
    )
    FIND_RUNS = frozenset({"-exec", "-execdir", "-ok", "-okdir"})
    RUNS_A_MODULE = frozenset({"python", "py"})
    WORD = r"""(?:[^\s'"\\;|&()<>]|\\.|'[^']*'|"(?:\\.|[^"\\])*")+"""
    SED_NAME = r"(?<![\w.$-])g?sed(?:\.exe)?"
    SED = re.compile(rf"{SED_NAME}((?:[ \t]+{WORD})+)", re.IGNORECASE)
    LATER_SED = re.compile(rf"{SED_NAME}$", re.IGNORECASE)
    EXPANSION = re.compile(
        r"""\\.|'[^']*'|"(?:\\.|[^"\\$`]|\$(?![\w{(@*#?!]))*"?|(?P<expansion>\$(?:[\w{(@*#?!]|$)|`)"""
    )
    SAFE_DIRECTORY = "safe.directory"
    GIT_SCOPES = ("global", "system")
    GIT_SCOPE_PREFIXES = tuple(scope[:n] for scope in GIT_SCOPES for n in range(1, len(scope)))
    GIT_SETTINGS = re.compile(
        r"""(?:(?<![\w.'"-])|(?<==["'])|(?<==\$["']))git\b[^;|&\n]{0,120}?\s"""
        rf"""(?:(?:-c\s+|--config-env[=\s]\s*)["']?{re.escape(SAFE_DIRECTORY)}"""
        rf"""|config\s[^;|&\n]{{0,60}}?(?:{re.escape(SAFE_DIRECTORY)}"""
        rf"""|--(?:(?:{"|".join(GIT_SCOPES)})\b"""
        rf"""|(?<![\w-]--)(?:{"|".join(GIT_SCOPE_PREFIXES)})(?![\w=-]))))"""
        rf"""|GIT_CONFIG_\w{{1,32}}=["']*{re.escape(SAFE_DIRECTORY)}""",
        re.IGNORECASE,
    )
    SHELL_SIGNS = re.compile(r"""\$?(['"])([\w./=$*~:@+-]*?)\1|\\(?=\S)""")
    NO_GIT_SETTINGS = (
        "The Claude Security plugin's agents may not run git config --global or --system, in full"
        " or shortened, or use safe.directory for git: those settings, and git's refusal of a"
        " repository that another user owns, are the user's to change. No part of this call ran."
        " Run the rest of it again without that git call. If git refused the repository, do not try"
        " another way to lift its refusal: go on without git, use the Read tool, and say in your"
        " answer that git refused to read the repository. To search a file for git config"
        " --global, use grep with git first in a quoted pattern: grep -n 'git config --global'"
        " FILE. If the command only writes text that holds such a git call, use the Write tool if"
        " you have it."
    )
    NO_GIT_SETTINGS_IN_ANALYSIS = (
        f"{MAY_NOT} run git config --global or --system, in full or shortened, or use"
        " safe.directory for git: those settings, and git's refusal of a repository that another"
        f" user owns, are the user's to change.{NOT_RUN} Run the rest of the call again without"
        " that git call. If git refused the repository, do not try another way to lift its refusal:"
        " go on without git, and use the Read tool. To search a file for git config --global, use"
        " grep with git first in a quoted pattern: grep -n 'git config --global' FILE. To write"
        " text that holds such a git call, use the Write tool."
    )

    PATCH_VERIFIER = f"{AGENT_PREFIX}patch-verifier"
    NOTES_WORD = "END_NOTES"
    KEEPS_NOTES = "--keep-notes"
    NOTES_OPEN = re.compile(rf"[^\n]*<<'{NOTES_WORD}'[ \t]*\n")
    SUBSTITUTION = re.compile(r"`|\$\(|\$\{[ \t|]")
    NOTES_END = f"\n{NOTES_WORD}\n"
    ONE_FORM_FOR_NOTES = (
        f"The Claude Security plugin's agents may not run patch_artifacts.py {KEEPS_NOTES} in any"
        f" form but this: that command alone on one line, which ends with <<'{NOTES_WORD}', the"
        f" notes on the next lines, and {NOTES_WORD} alone on the last line. In another form the"
        " shell can run a part of the notes as commands, such as what follows a line that is"
        f" {NOTES_WORD} alone. No part of this call ran. Send the notes again in that form, with no"
        f" carriage return and no other line that is {NOTES_WORD} alone."
    )


def obj(value: object) -> dict[str, object]:
    """value when it is a JSON object, else an empty one."""
    return cast("dict[str, object]", value) if isinstance(value, dict) else {}


def arr(value: object) -> list[object]:
    """value when it is a JSON array, else an empty one."""
    return cast("list[object]", value) if isinstance(value, list) else []


def parse(text: str | bytes) -> dict[str, object]:
    """The JSON object in text; an empty dict when text holds anything else."""
    try:
        return obj(cast("object", json.loads(text)))
    except (ValueError, RecursionError):
        return {}


def count(value: object) -> int | None:
    """value when it is a non-negative int (a bool is not one), else None."""
    return value if type(value) is int and value >= 0 else None


def code(table: dict[str, int], value: object) -> int:
    """The table's code for a word; 0 for anything it does not name."""
    return table.get(value, 0) if isinstance(value, str) else 0


def read(path: Path) -> bytes | None:
    """The file's bytes; None when it cannot be read."""
    try:
        return path.read_bytes()
    except (OSError, ValueError):
        return None


def manifest_version() -> str:
    """The version in the plugin's manifest; "" when there is not one."""
    manifest = parse(read(PLUGIN_ROOT / ".claude-plugin" / "plugin.json") or b"")
    version = manifest.get("version")
    return version if isinstance(version, str) else ""


def print_hook_output(event: Literal["PreToolUse", "PermissionRequest"], **fields: object) -> None:
    """Print a hook's event-specific output: the event's name and these fields."""
    answer = json.dumps({"hookSpecificOutput": {"hookEventName": event, **fields}})
    sys.stdout.buffer.write(answer.encode("ascii"))


def drawing() -> str:
    """The menu banner's greeting and drawing, for a monospaced font."""
    width = 53
    version = f" v{manifest_version() or 'unknown'} "
    box = [
        "      ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗",
        "     ██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝",
        "     ██║     ██║     ███████║██║   ██║██║  ██║█████╗",
        "     ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝",
        "     ╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗",
        "      ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝",
        "     ────────  S · E · C · U · R · I · T · Y  ────────",
        "  ┌" + "─" * width + "┐",
        "  │" + "Find and fix vulnerabilities in source code".center(width) + "│",
        "  └" + version.rjust(width - 3, "─") + "───┘",
    ]
    return "\nLaunching Claude Security...\n\n\n" + "\n".join(box) + "\n"


def banner(state: Path | None, *, terminal: bool) -> None:
    """Print the menu banner as a systemMessage and record in state that the menu was opened.

    The drawing is for the terminal. The note on auto mode is left out where the hook input on stdin
    names that mode.
    """
    in_auto_mode = parse(sys.stdin.buffer.read()).get("permission_mode") == "auto"
    if terminal:
        message = drawing() + ("" if in_auto_mode else f"\n{AUTO_MODE_NOTE}\n")
    else:
        message = "" if in_auto_mode else APP_AUTO_MODE_NOTE
    if message:
        sys.stdout.write(json.dumps({"systemMessage": message}))
    if state and not (record := TipState.load(state)).opened:
        record.opened = True
        with suppress(OSError):
            record.save()


def lex(command: str, *, comments: bool) -> list[str]:
    """A command's words, split roughly as sh would, each run of shell punctuation a word of its
    own; none when a quote is left open or the command ends in a lone backslash. With comments, a
    "#" starts a comment that runs to the end of the line, even mid-word."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = "#" if comments else ""
    try:
        return list(lexer)
    except ValueError:
        return []


def helper_words(command: str) -> list[str] | None:
    """The interpreter, script and argument words of a command that runs one of the plugin's
    helper scripts on its own; else None."""
    if any(mark in command for mark in ("\n", "\0", "`", "$(")):
        return None
    lexed = lex(command, comments=False)
    if any(word and set(word) <= OPERATORS for word in lexed):
        return None
    words = list(itertools.takewhile(lambda word: not word.startswith("#"), lexed))
    if words[:1] == ["env"]:
        words = list(itertools.dropwhile(ASSIGNMENT.match, words[1:]))
    if words[:2] == [PY_LAUNCHER, PY_VERSION_OPTION]:
        del words[1]
    if len(words) < 2 or words[0] not in INTERPRETERS:
        return None
    name = os.path.basename(words[1])
    own = os.path.realpath(SCRIPTS / name)
    return words if name in STEPS and os.path.realpath(words[1]) == own else None


def arguments(args: list[str]) -> tuple[list[str], dict[str, str | None]]:
    """A helper's positional arguments and its --options. Each --option takes the value after its
    "=", or else the next word, whatever that word is, or None where no word is left. A word with
    one dash is positional."""
    positionals: list[str] = []
    options: dict[str, str | None] = {}
    rest = iter(args)
    for arg in rest:
        if arg.startswith("--"):
            name, equals, value = arg.partition("=")
            options[name] = value if equals else next(rest, None)
        else:
            positionals.append(arg)
    return positionals, options


def scan_started(scan_root: str, options: dict[str, str | None]) -> dict[str, int | bool] | None:
    """The event for a write_scan_meta.py run; None unless it names a mode and an effort."""
    asked = (options.get("--effort") or "").strip().lower()
    mode, effort = code(MODES, options.get("--mode")), code(EFFORTS, asked)
    if not (mode and effort):
        return None
    root = os.path.normpath(scan_root)
    scope = (options.get("--scope") or "").split(",")
    scoped = any(os.path.normpath(os.path.join(root, entry.strip())) != root for entry in scope)
    return {"mode": mode, "effort": effort, "scoped": scoped, "py_minor": sys.version_info.minor}


def stamp_in(products: Path) -> dict[str, object]:
    """The one revision stamp in a directory of results; empty unless there is exactly one, and it
    reads as a JSON object."""
    try:
        (path,) = (
            p for p in products.iterdir() if p.name.startswith(STAMP_PREFIX) and p.suffix == ".json"
        )
    except (OSError, ValueError):
        return {}
    return parse(read(path) or b"")


def severities(stamp: dict[str, object]) -> dict[str, int | None]:
    """The stamp's counts of findings, by severity."""
    findings = obj(stamp.get("findings"))
    return {f"sev_{word}": count(findings.get(word)) for word in SEVERITIES}


def unverified_reason(stamp: dict[str, object]) -> int:
    """The code of the stamp's reason_kind word; 0 for a verified stamp, and UNKNOWN_REASON where
    the word is missing or not in REASONS."""
    verification = obj(stamp.get("verification"))
    if verification.get("status") == VERIFIED:
        return 0
    return code(REASONS, verification.get("reason_kind")) or UNKNOWN_REASON


def scan_finished(products: Path) -> dict[str, int | bool | None] | None:
    """The event for a render_report.py run, from the one revision stamp it wrote; else None. A
    count or a flag that was not read is None in the event."""
    stamp = stamp_in(products)
    if not stamp:
        return None
    verification = obj(stamp.get("verification"))
    shape = obj(stamp.get("run_shape"))
    dispatched = count(verification.get("researchers_dispatched"))
    returned = count(verification.get("researchers_returned"))
    coverage_read = shape.get("source") == COVERAGE_SOURCE
    votes_read = verification.get("reason_kind") not in NOT_COUNTED
    change_scan_effort = code(CHANGE_SCAN_EFFORTS, stamp.get("change_scan_effort"))
    return {
        "mode": code(STAMP_MODE_CODES, stamp.get("mode")),
        "effort": code(EFFORTS, stamp.get("effort")),
        **({"change_scan_effort": change_scan_effort} if change_scan_effort else {}),
        **severities(stamp),
        "candidates": count(verification.get("candidates")) if votes_read else None,
        "candidates_deduped": (
            count(verification.get("candidates_deduped")) if votes_read else None
        ),
        "unverified_reason": unverified_reason(stamp),
        "researchers_dispatched": dispatched,
        "researchers_lost": (
            None if dispatched is None or returned is None else max(dispatched - returned, 0)
        ),
        "panels_short": (
            count(verification.get("incomplete_panel_candidates")) if votes_read else None
        ),
        "findings_refused": len(arr(verification.get("refused_findings"))),
        "verify_runs": count(shape.get("verification_runs")),
        "collapsed": shape.get("collapsed") == COLLAPSED if coverage_read else None,
        "duration_s": count(stamp.get("duration_s")),
        "past_fix_researchers": (
            (count(shape.get("past_fix_researchers")) or 0) if coverage_read else None
        ),
        "past_fix_follow_up": (
            code(FOLLOW_UPS, shape.get("past_fix_follow_up")) if coverage_read else None
        ),
    }


def analysis_finished(products: Path) -> dict[str, int | bool | None] | None:
    """The event for an attack_surface_report.py write, from the one revision stamp and the patch
    files that it wrote; else None."""
    stamp = stamp_in(products)
    if not stamp:
        return None
    try:
        patches = (products / ANALYSIS_PATCHES_DIR_NAME).iterdir()
        patch_files = sum(path.suffix == ".patch" for path in patches)
    except OSError:
        patch_files = 0
    return {
        **severities(stamp),
        "unverified_reason": unverified_reason(stamp),
        "stages": len(arr(stamp.get("stages"))),
        "patch_files": patch_files,
    }


def triage_finished(output_file: Path) -> dict[str, int | bool] | None:
    """The event for a triage.py report run, from the two JSONL files that it wrote beside the run
    directory that the workflow's output file names; else None."""
    run_dir = obj(parse(read(output_file) or b"").get("result")).get("runDir")
    if not isinstance(run_dir, str):
        return None
    results = Path(run_dir).parent
    data = read(results / TRIAGE_JSONL)
    if data is None:
        return None
    rows = [row for row in map(parse, data.splitlines()) if row]
    grades = [str(row.get("severity")).lower() for row in rows]
    return {
        **{key: sum(row.get("verdict") == word for row in rows) for key, word in VERDICTS.items()},
        **{f"sev_{word}": grades.count(word) for word in SEVERITIES},
        "patchable": len((read(results / JSONL_NAME) or b"").splitlines()),
    }


def patches_written(patches_dir: Path) -> dict[str, int | bool | None] | None:
    """The event for a patch_artifacts.py run, from the patches.jsonl it wrote and its report's
    stamp; else None. A flag that was not read is None in the event."""
    data = read(patches_dir / "patches.jsonl")
    if data is None:
        return None
    rows = [row for row in map(parse, data.splitlines()) if row]
    statuses = [row.get("status") for row in rows]
    checks = [str(row.get("apply_check")) for row in rows]
    stamp = stamp_in(patches_dir.parent)
    return {
        "units": len(rows),
        "patches_written": statuses.count("patch_written"),
        "declined": statuses.count("declined"),
        "skipped_stale": statuses.count("skipped_stale"),
        "untested": sum(row.get("untested") is True for row in rows),
        "apply_clean": checks.count("clean"),
        "apply_conflicts": sum(check.startswith("conflicts") for check in checks),
        "after_triage": stamp.get("mode") == TRIAGE_MODE if stamp else None,
    }


def step_failed(script: str, data: dict[str, object]) -> dict[str, int | bool | None]:
    """The event for a helper call that reads as failed, from Claude Code's error text."""
    status = re.match(r"Exit code (\d+)", str(data.get("error", "")))
    interrupted = data.get("is_interrupt")
    return {
        "step": STEPS[script],
        "exit_code": min(int(status[1]), 255) if status else -1,
        "interrupted": interrupted if isinstance(interrupted, bool) else None,
    }


def metrics(failed: frozenset[str]) -> None:
    """Print the metrics object for the hook input on stdin, when it is a helper run.

    failed names the interpreters hooks.sh itself could not run; a call that starts with one of
    those names sends no step_failed.
    """
    data = parse(sys.stdin.buffer.read())
    cwd, event = data.get("cwd"), data.get("hook_event_name")
    words = helper_words(str(obj(data.get("tool_input")).get("command", "")))
    if words is None or not isinstance(cwd, str):
        return
    script = os.path.basename(words[1])
    positionals, options = arguments(words[2:])
    form = positionals[0] if script == "attack_surface_report.py" and positionals else ""
    if "-h" in positionals or "--help" in options or form == CHECK:
        return
    if script == "patch_artifacts.py" and options.keys() & SCRATCH_VERBS:
        return
    if script == "write_scan_meta.py" and options.get("--step") == "check":
        return
    failure = event == "PostToolUseFailure"
    delivered = script in DELIVERED_LINES and DELIVERED_LINES[script] in str(data.get("error"))
    if failure and not delivered:
        name, body = "step_failed", None
    elif event != "PostToolUse" and not failure:
        return
    elif script == "write_scan_meta.py" and len(positionals) >= 2:
        name, body = "scan_started", scan_started(os.path.join(cwd, positionals[1]), options)
    elif script == "render_report.py" and positionals:
        products = Path(cwd, options.get("--products-dir") or positionals[0])
        body = scan_finished(products) or scan_finished(Path(os.path.normpath(products)))
        name = "scan_finished"
    elif script == "patch_artifacts.py" and len(positionals) >= 2:
        patches_dir = Path(cwd, positionals[1])
        body = patches_written(patches_dir) or patches_written(Path(os.path.normpath(patches_dir)))
        name = "patches_written"
    elif form == START:
        name, body = "analysis_started", {}
    elif form == WRITE and len(positionals) >= 2:
        name, body = "analysis_finished", analysis_finished(Path(cwd, positionals[1]))
    elif script == "triage.py" and len(positionals) >= 2 and positionals[0] == LOAD:
        listed = Path(cwd, positionals[1])
        from_report = os.path.isdir(listed) or listed.name == SARIF_NAME
        name, body = "triage_started", {"from_report": from_report}
    elif script == "triage.py" and len(positionals) >= 2 and positionals[0] == REPORT:
        name, body = "triage_finished", triage_finished(Path(cwd, positionals[1]))
    else:
        return
    if body is None and failure and words[0] not in failed:
        name, body = "step_failed", step_failed(script, data)
    if body is not None:
        read_values = {key: value for key, value in body.items() if value is not None}
        sys.stdout.write(json.dumps({"metrics": {"ev": EVENTS[name], **read_values}}))


def unanswered() -> None:
    """Print a deny decision, after the wait, if the hook input asks a scan's or an analysis's start
    confirmation."""
    asked = arr(obj(parse(sys.stdin.buffer.read()).get("tool_input")).get("questions"))
    questions = [obj(question).get("question") for question in asked]
    if START_CONFIRMATION not in questions and ANALYSIS_CONFIRMATION not in questions:
        return
    time.sleep(UNANSWERED_AFTER_S)
    message = f"No answer after {UNANSWERED_AFTER_S} seconds, so nothing was run."
    print_hook_output("PermissionRequest", decision={"behavior": "deny", "message": message})


def denied_command(command: str, denied: Mapping[str, str]) -> str | None:
    """The first of the denied commands that a shell command seems to run, or None. The command is
    read whole, and each of its lines alone, with # comments dropped, and any reading that finds a
    name counts."""
    command = re.sub(rf"\\([{re.escape(''.join(OPERATORS))}]|$)", "_", command.replace("\\\n", ""))
    whole = command.replace("\n", "\n;")
    readings = (lex(text, comments=True) for text in [whole, *command.splitlines()])
    return next(filter(None, (denied_word(words, denied) for words in readings)), None)


def is_redirect(word: str) -> bool:
    """Whether a word is a redirection operator, such as > or >&; <( and >( are not."""
    return bool(word) and set(word) <= set("<>&|") and not set(word).isdisjoint("<>")


def changes_git_settings(command: str) -> bool:
    """Whether a shell command seems to run git config with --global or --system, in full or
    shortened, to name safe.directory to git config, or to override git's refusal of a
    repository."""
    raw = command.replace("\\\n", "")
    readings = (raw, Guard.SHELL_SIGNS.sub(r"\2", raw))
    return any(Guard.GIT_SETTINGS.search(text) for text in readings)


def strays_from_the_notes_form(command: str) -> bool:
    """Whether a shell command names --keep-notes, and its first line is not one plain command that
    ends with <<'END_NOTES', or more than white space follows the first line that is END_NOTES
    alone, or it holds a carriage return."""
    if Guard.KEEPS_NOTES not in command:
        return False
    if "\r" in command:
        return True
    first = command.partition("\n")[0]
    words = lex(first, comments=False)
    signs = [word for word in words if word.startswith("#") or set(word) <= OPERATORS]
    plain = signs == ["<<"] and not Guard.SUBSTITUTION.search(first)
    after_the_end = command.partition(Guard.NOTES_END)[2]
    return not (plain and Guard.NOTES_OPEN.match(command)) or bool(after_the_end.strip())


def redirects_to_temp(command: str) -> bool:
    """Whether a shell command seems to redirect output to a path in a temp folder. The path is read
    as it is written. The command is read whole, and each of its lines alone."""
    readings = (lex(text, comments=True) for text in [command, *command.splitlines()])
    return any(
        ">" in operator
        and set(operator) <= OPERATORS
        and Guard.IN_TEMP.match(target)
        and not Guard.REPORT_FOLDER.search(target)
        for words in readings
        for operator, target in zip(words, words[1:])
    )


def subcommand(words: list[str], start: int) -> str:
    """The first word at or after index start that is not an option, such as install in
    apt-get -y install. "" when there is none, or when --help comes straight after it."""
    for i in range(start, len(words)):
        if not words[i].startswith("-"):
            return "" if "--help" in words[i + 1 : i + 2] else words[i]
    return ""


def denied_word(words: list[str], denied: Mapping[str, str]) -> str | None:
    """The first of the denied commands that these words name where a command is expected. At the
    end of an interpreter's name, a version or ".exe" is ignored, and so is ".exe" at the end of any
    other name but kill, pkill and killall: python3.12 counts as python, and rm.exe as rm. A denied
    command can also be a name with its subcommand, and a version at the end of that name is ignored
    too: pip3.12 install counts as pip install. After python or py and words such as its one-word
    options, only such a pair is looked for: pip install in python3 -I -m pip install."""
    at_command = True
    after_python = False
    later: list[str] = []
    for i, word in enumerate(words):
        if word and set(word) <= OPERATORS:
            if not is_redirect(word):
                at_command, after_python = True, False
            continue
        for part in re.split(r"\$\(|`", word)[1:]:
            later += [";", *lex(part, comments=True)]
        if re.fullmatch(r"\d+(\.\d+)?[smhd]?|\{\}", word) or (i and is_redirect(words[i - 1])):
            continue
        at_command = at_command or word in Guard.FIND_RUNS
        name = os.path.basename(word)
        if not at_command or name in Guard.BEFORE_COMMAND or word.startswith("-") or "=" in word:
            continue
        plain = name.lower()
        stem = plain.removesuffix(".exe")
        bare = stem.rstrip("0123456789.")
        if (
            bare in Guard.INTERPRETER_NAMES or bare in Guard.READER_INTERPRETERS
        ) and bare in denied:
            return bare
        if bare in Guard.RUNS_A_MODULE:
            after_python = True
            continue
        key = plain if stem in Guard.DENIED else stem
        if not after_python and key in denied:
            return key
        if (pair := f"{bare} {subcommand(words, i + 1)}") in denied:
            return pair
        at_command = after_python = False
    return denied_word(later, denied) if later else None


def sed_scripts(words: list[str]) -> list[str]:
    """The words after sed to read as scripts. Every word that opens with - is one, as in -e"$x". So
    is the word after -e, after an option group that ends in e, or after --expression, which can be
    cut as short as --e. So is the first word that neither opens with - nor is '' or "". So is the
    first word of that kind after each later sed, such as gsed or dir/sed."""
    options = [word for word in words if word.startswith("-")]
    named = [
        value
        for option, value in zip(words, words[1:])
        if re.fullmatch(r"-\w*e", option)
        or (option.startswith("--e") and "--expression".startswith(option))
    ]
    # '' or "" is the empty suffix that macOS sed takes after -i.
    others = [word for word in words if not word.startswith("-") and word not in {"''", '""'}]
    later = [word for name, word in zip(others, others[1:]) if Guard.LATER_SED.search(name)]
    return [*options, *named, *others[:1], *later]


def fills_sed_script(command: str) -> bool:
    """Whether a shell command seems to give sed a script that the shell fills in."""
    return any(
        found["expansion"]
        for run in Guard.SED.finditer(command.replace("\\\n", ""))
        for script in sed_scripts(re.findall(Guard.WORD, run[1]))
        for found in Guard.EXPANSION.finditer(script)
    )


def refusal(agent: str, command: str, *, session: bool) -> str | None:
    """Why one of the plugin's agents may not run this command; None when it may. session says that
    the call is the session's own, not a subagent's."""
    analysis = agent.startswith(Guard.ANALYSIS)
    if analysis:
        denied = Guard.DENIED_IN_ANALYSIS
    elif agent in Guard.READERS:
        denied = Guard.DENIED_TO_READERS
    elif session and agent == Guard.LEAD:
        denied = Guard.DENIED
    else:
        denied = Guard.DENIED_WITH_DOWNLOADS
    if name := denied_command(command, denied):
        return denied[name]
    if fills_sed_script(command):
        return Guard.NO_FILLED_SED_IN_ANALYSIS if analysis else Guard.NO_FILLED_SED
    if analysis and redirects_to_temp(command):
        return Guard.NO_TEMP_FILE
    if changes_git_settings(command):
        return Guard.NO_GIT_SETTINGS_IN_ANALYSIS if analysis else Guard.NO_GIT_SETTINGS
    if agent == Guard.PATCH_VERIFIER and strays_from_the_notes_form(command):
        return Guard.ONE_FORM_FOR_NOTES
    return None


def guard() -> None:
    """Print a deny decision when the hook input on stdin comes from one of the plugin's own
    agents and breaks one of the guard's rules. hooks.json's matcher limits it to Bash calls."""
    data = parse(sys.stdin.buffer.read())
    agent = str(data.get("agent_type"))
    if not agent.startswith(Guard.AGENT_PREFIX):
        return
    command = str(obj(data.get("tool_input")).get("command"))
    if reason := refusal(agent, command, session="agent_id" not in data):
        print_hook_output("PreToolUse", permissionDecision="deny", permissionDecisionReason=reason)


def turn_note(config: Path, event: dict[str, object]) -> Path | None:
    """The path of the note for the event's prompt_id; None where the id is no plain name."""
    prompt = event.get("prompt_id")
    # An id with a slash or dots would name a file outside the notes' folder.
    if isinstance(prompt, str) and re.fullmatch(r"[\w-]+", prompt):
        return config / TURN_NOTES / prompt
    return None


def turn(config: Path) -> int:
    """Note the id of the prompt at which /claude-security:threat-model was typed. Where that
    fails on a bad id or a raised error, the exit code is not 0, and hooks.sh stops the command."""
    if not (note := turn_note(config, parse(sys.stdin.buffer.read()))):
        return 1
    note.parent.mkdir(parents=True, exist_ok=True)
    note.touch()
    return 0


def folded_path(path: str) -> PurePath:
    """The path in lower case, less the trailing dots and spaces on each part, which Windows can
    drop. A part left empty counts as ".."."""
    return PurePath(*(part.rstrip(". ") or ".." for part in PurePath(path.casefold()).parts))


def closed_to_the_command(config: PurePath, path: PurePath) -> bool:
    """Whether the path does not start at a plain root ("/", or a drive and a backslash) or names
    "..", or lies in the config folder, or in a .claude folder other than its worktrees. It reads
    the path's text alone, as folded_path gives it."""
    folded = folded_path(str(path))
    parts = folded.parts
    return (
        not re.fullmatch(r"/|[A-Za-z]:\\", path.anchor)
        or ".." in parts
        or folded_path(os.path.abspath(config)) in folded.parents
        or any(part == ".claude" and after != "worktrees" for part, after in zip(parts, parts[1:]))
    )


def reads(tool: str, tool_input: object) -> bool:
    """Whether a connector's call may run. The tool needs a word of READ_WORDS or FETCH_WORDS at
    the start or end of its name, or as the first word past those that the connector's own name
    holds. With a word of FETCH_WORDS there, tool_input must not fit ADDRESS; for NOTION_READ, what
    fits NOTION_ADDRESS is left out first. With none there, it must not fit URL_KEY. In each case
    it must be a JSON object."""
    if not isinstance(tool_input, dict):
        return False
    connector, _, name = tool.removeprefix("mcp__").rpartition("__")
    own = set(map(str.lower, WORD.findall(connector)))
    words = list(map(str.lower, WORD.findall(name)))
    past_own = [word for word in words if word not in own]
    looked_at = words[:1] + words[-1:] + past_own[:1]
    try:
        text = json.dumps(tool_input)
    except (ValueError, RecursionError):
        return False
    if FETCH_WORDS.isdisjoint(looked_at):
        return not (READ_WORDS.isdisjoint(looked_at) or URL_KEY.search(text))
    if name == NOTION_READ:
        text = NOTION_ADDRESS.sub("", text)
    return not ADDRESS.search(text)


def bound(config: Path) -> None:
    """Print a deny decision if parse finds the hook input empty. In the noted turn, print one too
    for a connector's call that reads() turns down, or if no pattern of THREAT_MODEL_FILES matches
    the path, or the path is closed to the command. The skill's header limits this hook to Write,
    Edit and connectors' tools."""
    call = parse(sys.stdin.buffer.read())
    if not call:
        print_hook_output(
            "PreToolUse", permissionDecision="deny", permissionDecisionReason=NOT_A_CALL
        )
        return
    if not ((note := turn_note(config, call)) and note.exists()):
        return
    tool = str(call.get("tool_name"))
    if tool.startswith("mcp__"):
        if not reads(tool, call.get("tool_input")):
            print_hook_output(
                "PreToolUse",
                permissionDecision="deny",
                permissionDecisionReason=NOT_A_READ.format(tool),
            )
        return
    path = PurePath(str(obj(call.get("tool_input")).get("file_path")))
    if closed_to_the_command(config, path) or not any(path.match(p) for p in THREAT_MODEL_FILES):
        print_hook_output(
            "PreToolUse", permissionDecision="deny", permissionDecisionReason=NOT_ITS_FILE
        )


def git(cwd: str, *args: str, deadline: float) -> str:
    """The stdout of `git -C <cwd> <args>` less its newline, or "" when git fails.

    Raises OSError when git cannot start, TimeoutExpired when it is slow or the deadline is past."""
    left = deadline - time.monotonic()
    if left <= 0:
        raise subprocess.TimeoutExpired(args, 0)
    out = subprocess.run(
        [*GIT, "-C", cwd, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=min(GIT_TIMEOUT_S, left),
        check=False,
    )
    text = out.stdout.decode("utf-8", "surrogateescape") if out.returncode == 0 else ""
    return text.rstrip("\r\n")


@dataclass
class TipState:
    """The tip's memory, a JSON file: whether the menu was opened, branches tipped, the last tip."""

    path: Path
    opened: bool
    shown: list[str]
    last: str

    @classmethod
    def load(cls, path: Path) -> TipState:
        """The record in the file at path; a missing or unreadable file is a fresh record."""
        raw = parse(read(path) or b"")
        shown, last = raw.get("shown"), raw.get("last")
        keys = cast("list[object]", shown) if isinstance(shown, list) else []
        kept = [key for key in keys if isinstance(key, str)]
        return cls(path, raw.get("opened") is True, kept, last if isinstance(last, str) else "")

    def save(self) -> None:
        """Write the record whole, so that a reader never meets a partial file."""
        fd, part = tempfile.mkstemp(prefix=self.path.name, dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                out.write(
                    json.dumps({"opened": self.opened, "shown": self.shown, "last": self.last})
                )
            Path(part).replace(self.path)
        except OSError:
            Path(part).unlink(missing_ok=True)
            raise

    @property
    def spent(self) -> bool:
        """Whether no branch is owed a tip any more: the menu was opened, or enough were shown."""
        return self.opened or len(self.shown) >= MAX_TIPS

    def seen(self, key: str) -> bool:
        """Whether the branch with this key was tipped, or was the last one noted."""
        return key == self.last or key in self.shown

    def note(self, key: str, *, counted: bool) -> None:
        """Record a tip for the branch with this key, counting it toward the limit or not."""
        self.last = key
        if counted:
            self.shown.append(key)
        self.save()


@dataclass(frozen=True)
class Branch:
    """The branch checked out in a directory: its work tree, repository, name and commit."""

    top: str
    repo: str
    name: str
    head: str

    @classmethod
    def at(cls, cwd: str, deadline: float) -> Branch | None:
        """The branch checked out at cwd; None outside a repository or off any branch."""
        run = functools.partial(git, cwd, deadline=deadline)
        place = run("rev-parse", "--show-toplevel", "--git-common-dir", "HEAD")
        try:
            top, common, head = place.split("\n")
        except ValueError:
            return None
        name = run("symbolic-ref", "-q", "--short", "HEAD")
        if not name:
            return None
        # The common git directory, so that every worktree of one repository is that repository.
        repo = os.path.realpath(os.path.join(cwd, common))
        return cls(top=top, repo=repo, name=name, head=head)

    def key(self, *, per_commit: bool) -> str:
        """An opaque key for this branch, or for this branch at this commit; it names neither."""
        parts = (self.repo, self.name, self.head if per_commit else "")
        return hashlib.sha256("\0".join(parts).encode("utf-8", "surrogateescape")).hexdigest()[:16]

    def change(self, deadline: float) -> tuple[int, str] | None:
        """(files changed, base) for this branch; None with no base, nothing ahead, or too much."""
        run = functools.partial(git, self.top, deadline=deadline)
        upstream = run("rev-parse", "--abbrev-ref", "@{upstream}")
        # The branch's own pushed copy (<remote>/<same name>, which `git push -u` sets) is no base.
        pushed_copy = upstream.partition("/")[2] == self.name
        for ref in (upstream, *BASES) if upstream and not pushed_copy else BASES:
            base = run("rev-parse", "--verify", "-q", "--abbrev-ref", ref)
            if base:
                break
        else:
            return None
        fork = run("merge-base", base, "HEAD")
        if not fork:
            return None
        files = run(*DIFF, fork, "HEAD").count("\0")
        return (files, base) if 0 < files <= MAX_FILES else None


def tip(state: Path | None, *, after_pr: bool, always: bool) -> None:
    """Print the tip when the hook input on stdin is a push, or a new pull request, of changes."""
    data = parse(sys.stdin.buffer.read())
    operation = obj(obj(data.get("tool_response")).get("gitOperation"))
    pushed = "push" in operation
    pr_opened = obj(operation.get("pr")).get("action") == "created"
    # One command can start both hook entries; only the push entry speaks for a command that pushed.
    published = (pr_opened and not pushed) if after_pr else pushed
    cwd = data.get("cwd")
    if not published or "agent_id" in data or not isinstance(cwd, str):
        return
    record = TipState.load(state) if state else None
    if record is None or (record.spent and not always):
        return
    started = time.monotonic()
    deadline = started + TIP_BUDGET_S
    with suppress(OSError, subprocess.TimeoutExpired):
        branch = Branch.at(cwd, deadline)
        if branch is None or record.seen(key := branch.key(per_commit=always)):
            return
        try:
            change = branch.change(deadline)
        except subprocess.TimeoutExpired:
            change = None
        # A branch slow to measure is noted even with nothing to show, and not measured again.
        if change is None and time.monotonic() - started < GIT_TIMEOUT_S:
            return
        record.note(key, counted=not always)
        if change is None:
            return
        files, base = change
        text = TIP.format(size="1 file" if files == 1 else f"{files} files", base=base)
        event = {"ev": EVENTS["tip_shown"]}
        sys.stdout.write(json.dumps({"systemMessage": text, "metrics": event}))


def tip_state_path(data_dir: str) -> Path | None:
    """The tip's state file in the plugin's data directory; None when Claude Code names none."""
    return Path(data_dir, TIP_STATE) if data_dir else None


def main(argv: list[str]) -> int:
    verb, args = (argv[0], argv[1:]) if argv else ("", [])
    if verb == "metrics" and set(args) <= INTERPRETERS:
        metrics(frozenset(args))
    elif verb == "unanswered" and not args:
        unanswered()
    elif verb == "guard" and not args:
        guard()
    elif verb == "turn" and len(args) == 1:
        return turn(Path(args[0]))
    elif verb == "bound" and len(args) == 1:
        bound(Path(args[0]))
    elif verb == "banner" and len(args) == 2:
        banner(tip_state_path(args[0]), terminal=args[1] == "cli")
    elif verb == "tip" and len(args) == 3 and args[0] in {"push", "pr"}:
        tip(tip_state_path(args[1]), after_pr=args[0] == "pr", always=args[2].lower() == "always")
    else:
        usage = (
            "usage: hooks.py metrics [failed-interpreter ...] | unanswered | guard | "
            "turn <config> | bound <config> | banner <data> <entry point> | "
            "tip push|pr <data> <mode>\n"
        )
        sys.stderr.write(usage)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
