#!/usr/bin/env python3
"""The Claude Security plugin's hooks.

A usage error exits 2. Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import itertools
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import cast

PLUGIN_ROOT = Path(os.path.abspath(__file__)).parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"

# Telemetry codes are append-only: a reader keys on them, so none is ever renumbered.
EVENTS = {"scan_started": 1, "scan_finished": 2, "patches_written": 3, "step_failed": 4}
STEPS = {
    "write_scan_meta.py": 1,
    "save_result.py": 2,
    "render_report.py": 3,
    "patch_artifacts.py": 4,
}
MODES = {"scan": 1, "changes": 2, "commit": 3}
EFFORTS = {"low": 1, "medium": 2, "high": 3, "max": 4}
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
COLLAPSED = ("small-diff", "small-scope")
STAMP_PREFIX = "CLAUDE-SECURITY-REVISION-"
OPERATORS = frozenset("();<>|&")


def obj(value: object) -> dict[str, object]:
    """value when it is a JSON object, else an empty one."""
    return cast("dict[str, object]", value) if isinstance(value, dict) else {}


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


def banner() -> None:
    """Print the menu banner as a systemMessage."""
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


def helper_words(command: str) -> list[str] | None:
    """The words of a command that runs one of the plugin's helper scripts on its own; else None."""
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
    if len(words) < 2 or words[0] != "python3":
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
    mode, effort = code(MODES, options.get("--mode")), code(EFFORTS, options.get("--effort"))
    root = os.path.normpath(scan_root)
    scope = (options.get("--scope") or "").split(",")
    scoped = any(os.path.normpath(os.path.join(root, entry.strip())) != root for entry in scope)
    return {"mode": mode, "effort": effort, "scoped": scoped} if mode and effort else None


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
    refused = verification.get("refused_findings")
    refusals = len(cast("list[object]", refused)) if isinstance(refused, list) else 0
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
        "findings_refused": refusals,
        "verify_runs": count(shape.get("verification_runs")),
        "collapsed": shape.get("collapsed") in COLLAPSED,
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


def metrics() -> None:
    """Print the metrics object for the hook input on stdin, when it is a helper run."""
    data = parse(sys.stdin.buffer.read())
    cwd, event = data.get("cwd"), data.get("hook_event_name")
    words = helper_words(str(obj(data.get("tool_input")).get("command", "")))
    if words is None or not isinstance(cwd, str):
        return
    script = os.path.basename(words[1])
    positionals, options = arguments(words[2:])
    if "--remove-scratch" in options:
        return
    if event == "PostToolUseFailure":
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


def main(argv: list[str]) -> int:
    hooks = {"banner": banner, "metrics": metrics}
    if len(argv) != 1 or argv[0] not in hooks:
        sys.stderr.write("usage: hooks.py banner|metrics\n")
        return 2
    hooks[argv[0]]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
