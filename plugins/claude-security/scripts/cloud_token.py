#!/usr/bin/env python3
"""Gets an access token for the GitHub Action's scan, once or repeatedly.

Usage:
  cloud_token.py vertex FILE CREDENTIALS [--every SECONDS]
  cloud_token.py foundry FILE CLIENT TENANT [--every SECONDS]
  cloud_token.py anthropic FILE ORGANIZATION RULE SERVICE_ACCOUNT WORKSPACE [--every SECONDS]

FILE is where the relay reads its token. Give it a folder of its own: to end --every, remove that
folder. A new file replaces FILE, so a reader gets a whole token.

  vertex   Asks gcloud for a token for the sign-in by workload identity federation that the
           credentials file CREDENTIALS describes. Refuses an empty name for CREDENTIALS. Also
           refuses a file of any other kind, such as a service account's key, and a file whose
           service_account_impersonation_url is missing, blank or not text.
  foundry  Asks GitHub for an identity token, signs az in with it as the application CLIENT of
           TENANT, and asks az for a token for Microsoft Foundry.
  anthropic  Asks GitHub for an identity token, and trades it at the Claude API for a token, by
           the federation rule RULE of ORGANIZATION. SERVICE_ACCOUNT and WORKSPACE may be empty.

Neither gcloud nor az gets the job's CLOUDSDK_* or AZURE_* variables. Each try makes a new folder
beside FILE's folder for their files, which only the job's user can open, and removes it. Uses a
token in an answer from gcloud, az, GitHub or the Claude API only after it has printed the workflow
command that masks that token. A try that gets no token leaves FILE as it is, and says why.

Without --every, exits 0 only if FILE holds a new token, or for -h. With --every it waits SECONDS
and makes a try, again and again. It ends after the first wait that ends with FILE's folder removed.
Exits 2 on a usage error. Python 3.9 or newer, stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, NewType, cast

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import console, strictjson
from lib.sandbox_hosts import CLAUDE_API_HOST, Provider
from lib.strictjson import clean, is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager
    from typing import IO

PATIENCE_S = 120
CLAUDE_API = f"https://{CLAUDE_API_HOST}"


# A token whose mask is printed. In this file, only masked() may make one.
Masked = NewType("Masked", str)


class TokenError(Exception):
    """Why a try got no token, in words for whoever reads the job's log."""


class Args(argparse.Namespace):
    provider: str = ""
    file: Path = Path()
    every: float | None = None

    def __init__(self) -> None:
        super().__init__()
        self.given: list[str] = []


def say(line: str) -> None:
    """Prints `line` at once. All that a try prints goes through here."""
    print(line, flush=True)


def clock() -> str:
    """The time of day, in UTC."""
    return time.strftime("%H:%M:%S UTC", time.gmtime())


def masked(token: object, source: str) -> Masked:
    """Prints the workflow command that masks `token`, which `source` gave, then returns it.
    Refuses all but a bearer token's characters."""
    if not (is_str(token) and re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", token)):
        msg = f"the answer from {source} is not one token"
        raise TokenError(msg)
    say(f"::add-mask::{token}")
    return Masked(token)


def ask(home: str, *words: str, **more: str) -> str:
    """What gcloud or az prints to standard output, with its files in `home`. Prints what it writes
    to standard error, with each ::add-mask in it broken up, between two lines that keep a runner
    from reading a workflow command in it.
    TokenError if it takes longer than PATIENCE_S, or ends with a status other than 0."""
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith(("CLOUDSDK_", "AZURE_"))},
        "CLOUDSDK_CONFIG": home,
        "CLOUDSDK_CORE_DISABLE_USAGE_REPORTING": "true",
        "CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK": "true",
        "AZURE_CONFIG_DIR": home,
        "AZURE_CORE_COLLECT_TELEMETRY": "false",
        **more,
    }
    with subprocess.Popen(
        words, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, start_new_session=True
    ) as run:
        try:
            printed, errors = run.communicate(timeout=PATIENCE_S)
            ended = f"ended with status {run.returncode}" if run.returncode else ""
        except subprocess.TimeoutExpired as late:
            os.killpg(run.pid, signal.SIGKILL)
            printed, errors = b"", late.stderr or b""
            ended = f"took longer than {PATIENCE_S} s, and was ended"
    # Printed here, not by the tool, and with a line end: the mask printed next must start a line.
    text = errors.decode("utf-8", "replace").rstrip("\n").replace("::add-mask", ": :add-mask")
    if text:
        # Until the word comes again, the runner reads no workflow command in what the tool wrote.
        word = secrets.token_hex(16)
        say(f"::stop-commands::{word}\n{text}\n::{word}::")
    if ended:
        # Three words only: they name the call, and show no argument's value.
        msg = f"`{' '.join(words[:3])}` {ended}"
        raise TokenError(msg)
    return printed.decode("utf-8", "replace").strip()


def vertex(home: str, credentials: str) -> Masked:
    """A token for Google Cloud."""
    if not credentials:
        msg = "no credentials file is given"
        raise TokenError(msg)
    try:
        file = strictjson.load(Path(credentials))
    except OSError as error:
        # The reason without the name: a workflow may give a key's text where the name belongs.
        msg = f"the credentials file cannot be read: {error.strerror}"
        raise TokenError(msg) from None
    except ValueError:
        file = None
    # The message is fixed: the file may be a private key, so nothing from it is shown.
    if not (
        is_map(file)
        and file.get("type") == "external_account"
        and clean(file.get("service_account_impersonation_url"))
    ):
        msg = (
            "the credentials file is not a workload identity federation file that names a service"
            " account"
        )
        raise TokenError(msg)
    words = ("gcloud", "auth", "application-default", "print-access-token")
    return masked(ask(home, *words, GOOGLE_APPLICATION_CREDENTIALS=credentials), "gcloud")


def token_in(answer: str, member: str, source: str) -> Masked:
    """The token that `answer`, a JSON object from `source`, holds as `member`."""
    try:
        said = strictjson.loads(answer)
    except ValueError:
        msg = f"the answer from {source} is not JSON"
        raise TokenError(msg) from None
    return masked(said.get(member) if is_map(said) else None, source)


def fetch(request: urllib.request.Request, timeout: float) -> AbstractContextManager[IO[bytes]]:
    """The answer to `request`. OSError if the request fails."""
    return cast(
        "AbstractContextManager[IO[bytes]]",
        urllib.request.urlopen(request, timeout=timeout),
    )


def identity_token(audience: str) -> Masked:
    """A GitHub identity token for `audience`. It lasts minutes."""
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    # action.yml masks this token first: the text of an error below can quote it.
    bearer = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not (url and bearer):
        msg = "the job lacks the permission id-token: write, so GitHub gives it no identity token"
        raise TokenError(msg)
    # Joined with "&": GitHub's URL has a query already.
    request = urllib.request.Request(f"{url}&audience={urllib.parse.quote(audience, safe='')}")
    # Unredirected: urllib sends a request's other headers on to the host that a redirect names.
    request.add_unredirected_header("Authorization", "Bearer " + bearer)
    try:
        with fetch(request, timeout=PATIENCE_S) as answer:
            text = answer.read().decode("utf-8", "replace")
    except OSError as error:
        msg = f"GitHub gave no identity token: {type(error).__name__}: {error}"
        raise TokenError(msg) from error
    return token_in(text, "value", "GitHub")


def foundry(home: str, client: str, tenant: str) -> Masked:
    """A token for Microsoft Foundry."""
    who = ("--service-principal", "--username", client, "--tenant", tenant)
    # az reads the value of "@FILE" from FILE, so GitHub's identity token is on no command line.
    with tempfile.NamedTemporaryFile("w", encoding="ascii", dir=home) as file:
        file.write(identity_token("api://AzureADTokenExchange"))
        file.flush()
        how = ("--federated-token", f"@{file.name}", "--allow-no-subscriptions", "--output", "none")
        ask(home, "az", "login", *who, *how)
    resource = ("--resource", "https://ai.azure.com", "--output", "json")
    return token_in(ask(home, "az", "account", "get-access-token", *resource), "accessToken", "az")


def anthropic(
    _home: str, organization: str, rule: str, service_account: str, workspace: str
) -> Masked:
    """A token for the Claude API."""
    optional = {"service_account_id": service_account, "workspace_id": workspace}
    fields = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": identity_token(CLAUDE_API),
        "federation_rule_id": rule,
        "organization_id": organization,
        **{name: value for name, value in optional.items() if value},
    }
    request = urllib.request.Request(
        f"{CLAUDE_API}/v1/oauth/token",
        strictjson.text(fields).encode(),
        {
            "content-type": "application/json",
            "anthropic-beta": "oauth-2025-04-20,oidc-federation-2026-04-01",
        },
    )
    try:
        with fetch(request, timeout=PATIENCE_S) as answer:
            text = answer.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        msg = f"the Claude API answered with HTTP {error.code}"
        raise TokenError(msg) from error
    except OSError as error:
        msg = f"the Claude API gave no answer: {type(error).__name__}: {error}"
        raise TokenError(msg) from error
    return token_in(text, "access_token", "the Claude API")


def put(held: int, name: str, token: Masked) -> None:
    """Replaces the file `name`, in the folder that `held` opens, with one that holds `token`."""
    staged = f"{name}.new"
    descriptor = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, dir_fd=held)
    with os.fdopen(descriptor, "w", encoding="ascii") as file:
        # Readable by all, whatever the umask: the folder's mode keeps others out.
        os.fchmod(descriptor, 0o644)
        file.write(f"{token}\n")
    os.replace(staged, name, src_dir_fd=held, dst_dir_fd=held)


class SignIn(NamedTuple):
    """How to get a provider's token, and the usage's names for what `get` takes after home."""

    get: Callable[..., Masked]
    arguments: tuple[str, ...]


PROVIDERS = {
    Provider.VERTEX.value: SignIn(vertex, ("CREDENTIALS",)),
    Provider.FOUNDRY.value: SignIn(foundry, ("CLIENT", "TENANT")),
    Provider.ANTHROPIC.value: SignIn(
        anthropic, ("ORGANIZATION", "RULE", "SERVICE_ACCOUNT", "WORKSPACE")
    ),
}


def renew(args: Args, held: int) -> None:
    """Gets a token, and replaces FILE with it in the folder that `held` opens."""
    with tempfile.TemporaryDirectory(dir=args.file.parent.parent) as home:
        token = PROVIDERS[args.provider].get(home, *args.given)
    put(held, args.file.name, token)
    digest = hashlib.sha256(token.encode()).hexdigest()[:8]
    say(f"{clock()}: a new access token; its SHA-256 begins {digest}")


def one_try(args: Args, held: int) -> int:
    """One try for a token. Returns 0 only if it replaced FILE in the folder that `held` opens.
    Otherwise it says why and returns 1, or raises if it cannot print."""
    try:
        renew(args, held)
    # With --every, no Exception in renew() may end the renewals.
    except Exception as error:
        kind = "" if isinstance(error, TokenError) else f"{type(error).__name__}: "
        # One line: a line end could start a command.
        why = " ".join(f"{kind}{error}".splitlines())
        say(f"{clock()}: no new token ({why})")
        return 1
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="cloud_token.py", allow_abbrev=False)
    providers = parser.add_subparsers(dest="provider", required=True)
    for name, sign_in in PROVIDERS.items():
        provider = providers.add_parser(name, allow_abbrev=False)
        provider.add_argument("file", type=Path, metavar="FILE")
        for argument in sign_in.arguments:
            provider.add_argument("given", action="append", metavar=argument)
        provider.add_argument("--every", type=float, metavar="SECONDS")
    args = parser.parse_args(argv, namespace=Args())
    console.print_in_the_paths_encoding()
    held = os.open(args.file.parent, os.O_RDONLY | os.O_DIRECTORY)
    if args.every is None:
        return one_try(args, held)
    while True:
        time.sleep(args.every)
        # The folder that it opened, not the path: a new folder of that name is another's.
        if not os.fstat(held).st_nlink:
            return 0
        one_try(args, held)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
