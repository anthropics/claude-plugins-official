"""The login that Claude Code has stored, in the form that the sandbox's relay takes."""

from __future__ import annotations

import math
import os
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass, field

from lib import strictjson
from lib.strictjson import JsonMap, as_int, as_map, clean, strings

from . import sandbox

TOKEN = "CLAUDE_CODE_OAUTH_TOKEN"  # noqa: S105
FILE = "token"
_RENEWED_WITHIN = 290
_STATUS_SECONDS = 60
_NOT_STORED = {
    "api_key_helper": "give the helper as --credential-command",
    "oauth_token": (
        "add --credential-command with a command that prints the token, and set "
        "ANTHROPIC_BASE_URL if that sign-in uses a host of its own"
    ),
    "third_party": (
        "set your provider's variables, or add --no-sandbox. --credential-command alone sends "
        "the scanned code to the Claude API or ANTHROPIC_BASE_URL"
    ),
}


@dataclass(frozen=True)
class Login:
    variables: dict[str, str] = field(repr=False)
    expires: float

    @property
    def ending(self) -> bool:
        return self.expires - time.time() < _RENEWED_WITHIN


def signed_in(claude: str, *, by_store: bool = False) -> bool:
    """Whether Claude Code has a way to sign in. It renews a login that is about to end. Raises
    TimeoutError if Claude Code does not answer, and OSError if it fails in any other way or, with
    `by_store`, if it names a way of _NOT_STORED. A way of another name passes."""
    try:
        done = subprocess.run(
            [claude, "auth", "status"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            cwd="/",
            timeout=_STATUS_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        msg = f"`claude auth status` did not answer in {_STATUS_SECONDS} seconds"
        raise TimeoutError(msg) from error
    status = _json(done.stdout.decode("utf-8", "replace"))
    if done.returncode == 0:
        if by_store and (way := clean(status.get("authMethod"))) in _NOT_STORED:
            msg = (
                f"Claude Code does not sign in with its stored login ({way}), and the sandbox "
                f"cannot sign in as it does: {_NOT_STORED[way]}"
            )
            raise OSError(msg)
        return True
    # Signed out, it exits with 1 and says so in JSON. A claude that cannot run can exit with 1 too.
    if status.get("loggedIn") is False:
        return False
    said = (done.stderr.strip() or done.stdout).decode("utf-8", "replace").strip()[-400:]
    msg = f"`claude auth status` failed with exit code {done.returncode}: {said or 'no message'}"
    raise OSError(msg)


def stored() -> Login | None:
    """The claude.ai login or the Console key that Claude Code keeps, if it keeps one."""
    file = sandbox.store_folder() / ".credentials.json"
    account = as_map(sandbox.stored(file).get("claudeAiOauth"))
    if token := clean(account.get("accessToken")):
        facts = {
            TOKEN: token,
            "CLAUDE_CODE_OAUTH_SCOPES": " ".join(strings(account.get("scopes"))),
            "CLAUDE_CODE_SUBSCRIPTION_TYPE": clean(account.get("subscriptionType")),
            "CLAUDE_CODE_RATE_LIMIT_TIER": clean(account.get("rateLimitTier")),
        }
        return Login(facts, as_int(account.get("expiresAt")) / 1000 or math.inf)
    key = clean(sandbox.stored(sandbox.state_file()).get("primaryApiKey"))
    return Login({"ANTHROPIC_API_KEY": key}, math.inf) if key else None


def owner() -> str:
    """The ids of the login's account and organization, joined; empty if Claude Code's state file
    names none or cannot be read."""
    named = as_map(sandbox.stored(sandbox.state_file()).get("oauthAccount"))
    return clean(named.get("accountUuid")) + clean(named.get("organizationUuid"))


def lay(token: str, folder: int) -> None:
    """Put `token` whole in FILE of the folder that the descriptor `folder` holds, for this user
    alone. OSError once that folder is removed, also where another has taken its name. Two calls
    must not overlap."""
    new = f"{FILE}.new"
    with suppress(FileNotFoundError):
        os.unlink(new, dir_fd=folder)
    opened = os.open(new, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=folder)
    with os.fdopen(opened, "wb") as file:
        file.write(token.encode())
    os.replace(new, FILE, src_dir_fd=folder, dst_dir_fd=folder)


def _json(text: str) -> JsonMap:
    with suppress(ValueError):
        return as_map(strictjson.loads(text))
    return {}
