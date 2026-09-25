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
from pathlib import Path
from typing import cast

PLUGIN_ROOT = Path(os.path.abspath(__file__)).parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"

# Telemetry codes are append-only: a reader keys on them, so none is ever renumbered.
EVENTS = {
    "scan_started": 1,
    "scan_finished": 2,
    "patches_written": 3,
    "step_failed": 4,
    "tip_shown": 5,
}
STEPS = {
    "write_scan_meta.py": 1,
    "save_result.py": 2,
    "render_report.py": 3,
    "patch_artifacts.py": 4,
}
MODES = {"scan": 1, "changes": 2, "commit": 3}
# `max` is accepted and runs as `high`, so it reports as 3; 4 is reserved.
EFFORTS = {"low": 1, "medium": 2, "high": 3, "max": 3}
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
}
UNKNOWN_REASON = 99
COLLAPSED = "small-scope"
STAMP_PREFIX = "CLAUDE-SECURITY-REVISION-"
OPERATORS = frozenset("();<>|&")
PY_LAUNCHER = "py"
INTERPRETERS = frozenset({"python3", "python", PY_LAUNCHER})
PY_VERSION_OPTION = "-3"
# The scan recipes' start confirmation, word for word: the one question that is timed.
START_CONFIRMATION = (
    "This scan may take a while and may use a significant number of tokens. "
    "You will need to leave Claude Code open while the scan completes. "
    "Are you sure you want to continue?"
)
UNANSWERED_AFTER_S = 60
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


def count(value: object) -> int:
    """value when it is a non-negative int (a bool is not one), else 0."""
    return value if type(value) is int and value >= 0 else 0


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


def banner(state: Path | None) -> None:
    """Print the menu banner as a systemMessage and record in state that the menu was opened."""
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
    message = "\nLaunching Claude Security...\n\n\n" + "\n".join(box) + "\n"
    sys.stdout.write(json.dumps({"systemMessage": message}))
    if state and not (record := TipState.load(state)).opened:
        record.opened = True
        with suppress(OSError):
            record.save()


def helper_words(command: str) -> list[str] | None:
    """The interpreter, script and argument words of a command that runs one of the plugin's
    helper scripts on its own; else None."""
    if any(mark in command for mark in ("\n", "\0", "`", "$(")):
        return None
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    # A "#" begins a comment only at the start of a word, as in sh; shlex would break a word on one.
    lexer.commenters = ""
    try:
        lexed = list(lexer)
    except ValueError:
        return None
    if any(word and set(word) <= OPERATORS for word in lexed):
        return None
    words = list(itertools.takewhile(lambda word: not word.startswith("#"), lexed))
    if words[:2] == [PY_LAUNCHER, PY_VERSION_OPTION]:
        del words[1]
    if len(words) < 2 or words[0] not in INTERPRETERS:
        return None
    name = os.path.basename(words[1])
    own = os.path.realpath(SCRIPTS / name)
    return words if name in STEPS and os.path.realpath(words[1]) == own else None


def arguments(args: list[str]) -> tuple[list[str], dict[str, str | None]]:
    """A helper's positional arguments and its --options, each of which takes a value."""
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


def scan_finished(products: Path) -> dict[str, int | bool] | None:
    """The event for a render_report.py run, from the one revision stamp it wrote; else None."""
    try:
        (path,) = (
            p for p in products.iterdir() if p.name.startswith(STAMP_PREFIX) and p.suffix == ".json"
        )
    except (OSError, ValueError):
        return None
    stamp = parse(read(path) or b"")
    if not stamp:
        return None
    findings = obj(stamp.get("findings"))
    verification = obj(stamp.get("verification"))
    shape = obj(stamp.get("run_shape"))
    reason = code(REASONS, verification.get("reason_kind")) or UNKNOWN_REASON
    dispatched = count(verification.get("researchers_dispatched"))
    return {
        "mode": code(MODES, stamp.get("mode")),
        "effort": code(EFFORTS, stamp.get("effort")),
        "sev_critical": count(findings.get("critical")),
        "sev_high": count(findings.get("high")),
        "sev_medium": count(findings.get("medium")),
        "sev_low": count(findings.get("low")),
        "candidates": count(verification.get("candidates")),
        "candidates_deduped": count(verification.get("candidates_deduped")),
        "unverified_reason": 0 if verification.get("status") == "verified" else reason,
        "researchers_dispatched": dispatched,
        "researchers_lost": count(dispatched - count(verification.get("researchers_returned"))),
        "panels_short": count(verification.get("incomplete_panel_candidates")),
        "findings_refused": len(arr(verification.get("refused_findings"))),
        "verify_runs": count(shape.get("verification_runs")),
        "collapsed": shape.get("collapsed") == COLLAPSED,
        "duration_s": count(stamp.get("duration_s")),
    }


def patches_written(patches_dir: Path) -> dict[str, int | bool] | None:
    """The event for a patch_artifacts.py run, from the patches.jsonl it wrote; else None."""
    data = read(patches_dir / "patches.jsonl")
    if data is None:
        return None
    rows = [row for row in map(parse, data.splitlines()) if row]
    statuses = [row.get("status") for row in rows]
    checks = [str(row.get("apply_check")) for row in rows]
    return {
        "units": len(rows),
        "patches_written": statuses.count("patch_written"),
        "declined": statuses.count("declined"),
        "skipped_stale": statuses.count("skipped_stale"),
        "untested": sum(row.get("untested") is True for row in rows),
        "apply_clean": checks.count("clean"),
        "apply_conflicts": sum(check.startswith("conflicts") for check in checks),
    }


def step_failed(script: str, data: dict[str, object]) -> dict[str, int | bool]:
    """The event for a helper run that failed, from Claude Code's error text."""
    status = re.match(r"Exit code (\d+)", str(data.get("error", "")))
    return {
        "step": STEPS[script],
        "exit_code": min(int(status[1]), 255) if status else -1,
        "interrupted": data.get("is_interrupt") is True,
    }


def metrics(failed: frozenset[str]) -> None:
    """Print the metrics object for the hook input on stdin, when it is a helper run.

    failed names the interpreters hooks.sh itself could not run; a failure under one is not sent.
    """
    data = parse(sys.stdin.buffer.read())
    cwd, event = data.get("cwd"), data.get("hook_event_name")
    words = helper_words(str(obj(data.get("tool_input")).get("command", "")))
    if words is None or not isinstance(cwd, str):
        return
    script = os.path.basename(words[1])
    positionals, options = arguments(words[2:])
    if "--remove-scratch" in options or "--prepare" in options:
        return
    if event == "PostToolUseFailure":
        if words[0] in failed:
            return
        name, body = "step_failed", step_failed(script, data)
    elif event != "PostToolUse":
        return
    elif script == "write_scan_meta.py" and len(positionals) >= 2:
        name, body = "scan_started", scan_started(os.path.join(cwd, positionals[1]), options)
    elif script == "render_report.py" and positionals:
        products = Path(cwd, options.get("--products-dir") or positionals[0])
        name, body = "scan_finished", scan_finished(products)
    elif script == "patch_artifacts.py" and len(positionals) >= 2:
        name, body = "patches_written", patches_written(Path(cwd, positionals[1]))
    else:
        return
    if body is not None:
        sys.stdout.write(json.dumps({"metrics": {"ev": EVENTS[name], **body}}))


def unanswered() -> None:
    """Print a deny decision, after the wait, if the hook input asks a scan's start confirmation."""
    asked = arr(obj(parse(sys.stdin.buffer.read()).get("tool_input")).get("questions"))
    if START_CONFIRMATION not in [obj(question).get("question") for question in asked]:
        return
    time.sleep(UNANSWERED_AFTER_S)
    message = f"No answer after {UNANSWERED_AFTER_S} seconds, so nothing was run."
    decision = {"behavior": "deny", "message": message}
    output = {"hookEventName": "PermissionRequest", "decision": decision}
    sys.stdout.write(json.dumps({"hookSpecificOutput": output}))


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
    elif verb == "banner" and len(args) == 1:
        banner(tip_state_path(args[0]))
    elif verb == "tip" and len(args) == 3 and args[0] in {"push", "pr"}:
        tip(tip_state_path(args[1]), after_pr=args[0] == "pr", always=args[2].lower() == "always")
    else:
        usage = (
            "usage: hooks.py metrics [failed-interpreter ...] | unanswered | banner <data> | "
            "tip push|pr <data> <mode>\n"
        )
        sys.stderr.write(usage)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
