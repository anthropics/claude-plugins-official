#!/usr/bin/env python3
"""Read claude-code-action's record of the session, for three steps of the job.

Usage:
  session_status.py EXECUTION_FILE
  session_status.py --auto-mode EXECUTION_FILE
  session_status.py --fast-mode EXECUTION_FILE

EXECUTION_FILE is claude-code-action's record of the session, a JSON list of messages. If its last
result message is an error with an HTTP status from 100 to 599, prints one `::error::` line with
that status, and advice for 400, 401 and 502. If it reports tool calls as denied with a reason known
to mean that auto mode's classifier gave no verdict, prints one `::error::` line with their number.
Exits 0 if it printed a line, and 1 otherwise. From the record it prints only those two numbers,
never the host's own words.

With --auto-mode it exits 0 if each permission mode that a system message names is auto, and no tool
call was denied with such a reason. Otherwise it exits 1 after one `::error::` line on stderr, which
holds none of the record's text. A record that it cannot read, or that names no mode, fails this
check too.

With --fast-mode it prints one `::warning::` line unless the last result message says that the
session ended with fast mode on, and exits 0. A record that it cannot read gets that line too.

Exits 2 on a usage error. Python 3.9, stdlib only.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.strictjson import is_int, is_list, is_map, is_str, load

if TYPE_CHECKING:
    from lib.strictjson import JsonMap

RELAYS_LINE: Final = (
    " Look in the log of the scan's step for a line that begins with sandbox:. With no such line, "
    "the model's host may have given this status, or the line was lost."
)
ADVICE: Final = {
    400: (
        f" The sandbox's relay gives this status to a request that it refuses.{RELAYS_LINE} If "
        "fast mode is on, a model gateway or a model that refuses fast mode can give it too: turn "
        "it off, in a --settings of your own if the job gives one, or else in fast_mode."
    ),
    401: (
        " Check the credential that the job gives, such as model_auth_token, anthropic_api_key or "
        "the AWS keys. The job's own ANTHROPIC_AUTH_TOKEN does not reach the session. Where the "
        'action renews the token, look too for "no new token" in the log of the step "Remove '
        'the credential folders".'
    ),
    502: (
        " The sandbox's relay gives this status where the model's host did not answer, or the "
        f"credential was not at hand.{RELAYS_LINE}"
    ),
}

# Claude Code's own words, here and in LATEST: the check matches them as they stand.
NO_VERDICT_REASONS: Final = (
    "Classifier unavailable",
    "Auto mode unavailable",
    "Auto mode could not evaluate this action",
    "Stage 2 classifier error",
)
LATEST: Final = "Latest blocked action: "
NO_VERDICT_ERROR: Final = (
    "::error::Auto mode's classifier gave no verdict on {count} of the session's tool calls. "
    "Claude Code does not run such a call, so the session's work may be incomplete. This job "
    "fails, whatever the session found: it posts no review and records no scan. "
    "If you use a cloud provider or a model gateway, check that "
    "your account can call the classifier's model and its fallback, and that the gateway passes "
    "their replies on unchanged. This action's CI.md describes both models, under "
    '"Setup with a cloud provider". If that is in order, or you use neither, run the job again.'
)
ANOTHER_MODE_ERROR: Final = (
    "::error::The session did not report Claude Code's auto mode from start to end. This "
    "job fails, whatever the session found: it posts no review and records no scan. Use a model "
    "that supports auto mode, or remove disableAutoMode from the Claude Code settings the session "
    "loads. If neither applies, run the job again, and report it if it comes back."
)
UNCONFIRMED_ERROR: Final = (
    "::error::This check could not confirm that the session ran in Claude Code's auto mode. "
    "{why} This job fails whatever the session found."
)
NOT_FAST_WARNING: Final = (
    "::warning::The input fast_mode is true, but the session's record does not show that it ended "
    "in fast mode, so it may have run at standard speed, at least in part. Fast mode needs "
    "a provider and a model that have it, and an organization whose admin has turned it on. It "
    "pauses at its own rate limit, and a --settings in claude_args drops it. See "
    "https://code.claude.com/docs/en/fast-mode"
)


class Args(argparse.Namespace):
    execution_file: Path = Path()
    auto_mode: bool = False
    fast_mode: bool = False


def last_result(messages: list[JsonMap]) -> JsonMap:
    """The last result message among `messages`, as messages_of() gives them; empty if there is
    none."""
    for message in reversed(messages):
        if message["type"] == "result":
            return message
    return {}


def ending(messages: list[JsonMap]) -> str:
    """The line with the HTTP status that ended the session; empty if the last result message among
    `messages` is no error with an HTTP status."""
    result = last_result(messages)
    if result.get("is_error") is not True:
        return ""
    status = result.get("api_error_status")
    if not is_int(status) or not 100 <= status <= 599:
        return ""
    return (
        f"::error::The session failed: a model request ended with HTTP status {status}."
        f"{ADVICE.get(status, '')}"
    )


def messages_of(record: object) -> list[JsonMap]:
    """`record` as a list of messages; ValueError if it is not a list of objects that each have a
    type."""
    msg = "not a list of messages"
    if not is_list(record):
        raise ValueError(msg)
    messages = [m for m in record if is_map(m) and "type" in m]
    if len(messages) < len(record):
        raise ValueError(msg)
    return messages


def texts(values: list[object]) -> list[str]:
    """`values`; ValueError if one of them is not text."""
    found = [value for value in values if is_str(value)]
    if len(found) < len(values):
        msg = "a message gives a mode or a reason that is not text"
        raise ValueError(msg)
    return found


def permission_modes(messages: list[JsonMap]) -> set[str]:
    """The permission modes that the system messages among `messages` name; ValueError if one of
    those modes is not text."""
    named = [
        m["permissionMode"] for m in messages if m["type"] == "system" and "permissionMode" in m
    ]
    return set(texts(named))


def lost_calls(messages: list[JsonMap]) -> str:
    """The line with the number of tool calls that `messages` report as denied for one of
    NO_VERDICT_REASONS, empty if there is none; ValueError if a denied call's reason is not text."""
    reasons = [
        m["decision_reason"]
        for m in messages
        if m.get("subtype") == "permission_denied" and "decision_reason" in m
    ]
    count = sum(
        reason.rpartition(LATEST)[2].startswith(NO_VERDICT_REASONS) for reason in texts(reasons)
    )
    return NO_VERDICT_ERROR.format(count=count) if count else ""


def not_auto(path: Path) -> str:
    """The line that says why the record at `path` fails --auto-mode; empty if it passes."""
    try:
        messages = messages_of(load(path))
        modes, lost = permission_modes(messages), lost_calls(messages)
    except (OSError, ValueError) as error:
        why = (
            "It could not read the permission mode or the reason for a denied tool call in the "
            f"session's record: {type(error).__name__}."
        )
        return UNCONFIRMED_ERROR.format(why=why)
    if not modes:
        why = "No system message in the session's record names a permission mode."
        return UNCONFIRMED_ERROR.format(why=why)
    return lost if modes == {"auto"} else ANOTHER_MODE_ERROR


def ended_in_fast_mode(path: Path) -> bool:
    """Whether the last result message of the record at `path` says that the session ended in fast
    mode; False for a record that it cannot read."""
    try:
        messages = messages_of(load(path))
    except (OSError, ValueError):
        return False
    return last_result(messages).get("fast_mode_state") == "on"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    form = parser.add_mutually_exclusive_group()
    form.add_argument(
        "--auto-mode",
        action="store_true",
        help="check the mode, and that no call was denied with a reason known to mean no verdict",
    )
    form.add_argument(
        "--fast-mode", action="store_true", help="warn unless the session ended in fast mode"
    )
    parser.add_argument(
        "execution_file", type=Path, help="claude-code-action's record of the session"
    )
    args = parser.parse_args(namespace=Args())
    if args.auto_mode:
        if line := not_auto(args.execution_file):
            print(line, file=sys.stderr)
        return 1 if line else 0
    if args.fast_mode:
        if not ended_in_fast_mode(args.execution_file):
            print(NOT_FAST_WARNING)
        return 0
    try:
        messages = messages_of(load(args.execution_file))
    except (OSError, ValueError):
        return 1
    said = [ending(messages)]
    with contextlib.suppress(ValueError):
        said.append(lost_calls(messages))
    for line in filter(None, said):
        print(line)
    return 0 if any(said) else 1


if __name__ == "__main__":
    sys.exit(main())
