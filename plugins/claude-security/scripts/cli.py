#!/usr/bin/env python3
"""Run a scan of the Claude Security plugin from a shell.

Starts Claude Code inside the plugin's sandbox, runs the scan, shows it as it works, and writes
the same CLAUDE-SECURITY-<timestamp> directory as a scan in a session.

Exits 0 when the scan is complete or has nothing to scan, 2 when it cannot start or Claude Code
is not in auto mode, or in the sandbox has not loaded the plugin, before the scan's workflow or an
agent starts, and 1 otherwise, with or without a report.
Python 3.9, stdlib only. The sandbox needs 3.10 or newer: this one, or 3.10 to 3.14 in its folder.
"""

from __future__ import annotations

import argparse
import errno
import os
import re
import shutil
import signal
import sys
import tempfile
from contextlib import ExitStack, suppress
from functools import partial
from pathlib import Path
from urllib.parse import urlsplit

# lib/ lies beside this script, whose folder Python leaves off the import path under -I or -P.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import console, git, plugin
from lib.live import command, login, plain, report, sandbox, session
from lib.live.atlas import Atlas
from lib.live.scan import Scan, State, Target
from lib.live.terminal import console_mode
from lib.sandbox import provider
from lib.sandbox.plan import SWAPPED, UNGUARDED, SandboxError

from lib.views import show

_ENDINGS = [
    s for s in signal.Signals if s.name in {"SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT", "SIGBREAK"}
]
_MAC = sys.platform == "darwin"
_NOT_ON_MAC = "the command does not run on macOS: scan from a Claude Code session"
COST = "This scan may take a while and may use a significant number of tokens."
_PROVIDERS = {
    "anthropic": "the Claude API (api.anthropic.com)",
    "bedrock": "Amazon Bedrock",
    "vertex": "Google Cloud's Agent Platform (Vertex)",
    "foundry": "Microsoft Foundry",
}
_NO_PROVIDER = (
    f"say where your code goes: add --provider with one of {', '.join(_PROVIDERS)}. For another "
    "host, add --model-base-url too, and set its key, or your own sign-in can go there. If your "
    "organization chooses these, type /status in Claude Code in your terminal, and give the "
    "provider and URL that it shows. If it shows neither, ask your administrator."
)
_NO_SANDBOX = "To scan with no sandbox, add --no-sandbox in place of --provider and its URL."
_URL_TEXT = re.compile(r"((?![@?#])[!-~])+")
_REF = re.compile(r"[A-Za-z0-9_@][A-Za-z0-9._/@^~-]{0,199}")
_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/@\[\]-]{0,299}")
_WORDS = re.compile(r".+", re.DOTALL)
_FOLDER = r"[^\s\x00-\x1f\x7f,-][^\s\x00-\x1f\x7f,]*"
_SCOPE = re.compile(rf"{_FOLDER}(,{_FOLDER})*")


class StartError(Exception):
    """The scan cannot start; the message says why."""


class StoppedError(Exception):
    """The user stopped the scan after its session had started."""


# A path that cannot be resolved raises RuntimeError, ValueError or KeyError.
_REFUSALS = (StartError, OSError, RuntimeError, ValueError, KeyError, KeyboardInterrupt, EOFError)


class Args(argparse.Namespace):
    path: Path = Path()
    changes: bool = False
    base: str = ""
    commit: str = ""
    scope: str = ""
    effort: str = "medium"
    change_scan_effort: str = "low"
    model: str = ""
    output: Path | None = None
    provider: str = ""
    model_base_url: str = ""
    yes: bool = False
    sudo: bool = False
    no_cgroup: bool = False
    credential_command: str = ""
    no_sandbox: bool = False
    install: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.allow_read: list[str] = []

    @property
    def of_changes(self) -> bool:
        return bool(self.changes or self.base or self.commit)


def _matching(pattern: re.Pattern[str], value: str) -> str:
    if not pattern.fullmatch(value):
        msg = f"{value!r} is not accepted"
        raise argparse.ArgumentTypeError(msg)
    return value


def _host(url: str) -> str:
    """The host and port of `url`; empty if the relay refuses it or it is not safe to print."""
    with suppress(ValueError):
        parts = urlsplit(url)
        local = parts.scheme == "http" and parts.hostname in {"127.0.0.1", "localhost", "::1"}
        if (local or (parts.scheme == "https" and parts.hostname)) and _URL_TEXT.fullmatch(url):
            return parts.netloc
    return ""


def parse(argv: list[str]) -> Args:
    parser = argparse.ArgumentParser(
        prog=plugin.NAME,
        description="Scan code for vulnerabilities with the Claude Security plugin.",
        allow_abbrev=False,
    )
    ref, model, scope, words = (partial(_matching, p) for p in (_REF, _MODEL, _SCOPE, _WORDS))
    parser.add_argument("path", nargs="?", type=Path, default=".", help="default: this folder")
    parser.add_argument("--version", action="version", version=plugin.version() or "unknown")
    what = parser.add_argument_group("what to scan")
    what.add_argument("--changes", action="store_true", help="scan this branch's changes")
    what.add_argument("--base", type=ref, metavar="REF", help="scan the changes since REF")
    what.add_argument("--commit", type=ref, metavar="SHA", help="scan the checked-out commit")
    what.add_argument("--scope", type=scope, metavar="DIRS", help="comma-separated folders to scan")
    what.add_argument("--effort", choices=("low", "medium", "high"), help="default: medium")
    what.add_argument(
        "--change-scan-effort", choices=("low", "high"), help="for a scan of changes (default: low)"
    )
    what.add_argument("--model", type=model, help="default: your Claude Code model")
    what.add_argument("--output", type=Path, metavar="DIR", help="where the report directory goes")
    show.add_options(parser)
    where = parser.add_argument_group("where your code goes")
    where.add_argument("--provider", choices=_PROVIDERS, help="required in the sandbox")
    where.add_argument("--model-base-url", type=words, metavar="URL", help="for another host")
    run = parser.add_argument_group("how to run it")
    run.add_argument("-y", "--yes", action="store_true", help="accept the time and token cost")
    run.add_argument(
        "--allow-read", type=words, action="append", metavar="PATH", help="let the scan read a path"
    )
    run.add_argument("--sudo", action="store_true", help="build the sandbox as root")
    run.add_argument("--no-cgroup", action="store_true", help="with --sudo: no cap on memory")
    run.add_argument(
        "--credential-command",
        type=words,
        metavar="COMMAND",
        help="prints the model's key or token",
    )
    run.add_argument("--no-sandbox", action="store_true", help="run Claude Code with no sandbox")
    run.add_argument("--install", action="store_true", help=f"write {plugin.NAME} to ~/.local/bin")
    args = parser.parse_args(argv, namespace=Args())
    if args.install and _MAC:
        parser.exit(2, f"{plugin.NAME}: {_NOT_ON_MAC}\n")
    if args.commit and (args.base or args.changes):
        parser.error("--commit scans one commit: leave out --base and --changes")
    if args.no_sandbox and (args.sudo or args.credential_command or args.allow_read):
        parser.error("--sudo, --credential-command and --allow-read need the sandbox")
    if args.no_sandbox and (args.provider or args.model_base_url):
        parser.error(
            "with --no-sandbox Claude Code chooses where your code goes: leave out --provider "
            "and --model-base-url"
        )
    if args.model_base_url and not _host(args.model_base_url):
        parser.error("--model-base-url must be an https address with no @, ? or #")
    if args.no_cgroup and not args.sudo:
        parser.error("--no-cgroup needs --sudo")
    high = args.change_scan_effort == plugin.CHANGE_SCAN_EFFORT_HIGH
    if high and not args.of_changes:
        parser.error("--change-scan-effort high needs --changes, --base or --commit")
    return args


def request(args: Args) -> tuple[str, str]:
    """The kind of scan, in words for the user, and the request that the session gets."""
    options = f"--effort {args.effort}" + (f" --scope {args.scope}" if args.scope else "")
    if not args.of_changes:
        whole = "this scope" if args.scope else "the whole repository"
        return "Codebase scan", f"Scan the codebase, {whole}: {options}"
    if args.change_scan_effort == plugin.CHANGE_SCAN_EFFORT_HIGH:
        options += f" --change-scan-effort {args.change_scan_effort}"
    if args.commit:
        return "Commit scan", f"Scan changes: --commit {args.commit} {options}"
    base = f"--base {args.base} " if args.base else ""
    return "Change scan", f"Scan this branch's changes: {base}{options}"


def shown(args: Args) -> tuple[str, list[str]]:
    """The effort that runs and what the scan covers, in words for the user."""
    folders = list(filter(None, args.scope.split(",")))
    if args.commit:
        change = f"commit {args.commit}"
    elif args.base:
        change = f"the changes since {args.base}"
    elif args.changes:
        change = "this branch's changes"
    else:
        return args.effort, folders
    high = plugin.CHANGE_SCAN_EFFORT_HIGH
    return high if args.change_scan_effort == high else args.effort, [change, *folders]


def route(args: Args, variables: dict[str, str]) -> dict[str, str]:
    """The variables to add, so that the relay calls what the options name. StartError where they
    name no provider, or where `variables` select another provider or base URL."""
    if not args.provider:
        raise StartError(_NO_PROVIDER)
    cloud = args.provider.upper()
    switch, url = f"CLAUDE_CODE_USE_{cloud}", f"ANTHROPIC_{cloud}_BASE_URL"
    if args.provider == "anthropic":
        switch, url = "", "ANTHROPIC_BASE_URL"
    on = provider.clouds_on(variables)
    other = [name for name in on if name != switch]
    if variables.get(url, "") not in {"", args.model_base_url}:
        other.append(url)
    if switch and not on and variables.get("ANTHROPIC_BASE_URL"):
        other.append("ANTHROPIC_BASE_URL")
    if other:
        msg = (
            f"your environment or Claude Code's settings set {', '.join(other)}: give the same "
            "provider in --provider and the same URL, letter for letter, in --model-base-url, or "
            "unset these names. The sandbox serves one provider at a time, and only those of "
            f"--provider. {_NO_SANDBOX}"
        )
        raise StartError(msg)
    added = {switch: "1"} if switch and not on else {}
    if args.model_base_url and not variables.get(url):
        added[url] = args.model_base_url
    if fixed := sandbox.managed_names().intersection(added):
        msg = (
            f"your organization's managed settings turn off {', '.join(sorted(fixed))}, so the "
            "scan cannot go where --provider and --model-base-url say: ask your administrator"
        )
        raise StartError(msg)
    return added


def destination(args: Args, held: login.Login | None) -> str:
    """Where the code goes, and where its credential comes from."""
    if args.credential_command:
        how = "signed in by what --credential-command prints"
    elif held:
        kind = "login" if login.TOKEN in held.variables else "key"
        how = f"signed in by Claude Code's stored {kind}"
    else:
        how = "configured by environment variables"
        how += " and gcloud" if args.provider == "vertex" else ""
    host = _host(args.model_base_url)
    place = f"{host} (provider {args.provider})" if host else _PROVIDERS[args.provider]
    return f"Your code goes to {place}, {how}."


def confirm(args: Args) -> None:
    if args.yes:
        return
    if not sys.stdin.isatty():
        msg = f"{COST} To accept that, add --yes."
        raise StartError(msg)
    if input(f"{COST} Continue? [y/N] ").strip().lower() not in {"y", "yes"}:
        msg = "no scan was started"
        raise StartError(msg)


def ignore_endings() -> None:
    """Let no further signal cut short what ends the scan."""
    for number in _ENDINGS:
        signal.signal(number, signal.SIG_IGN)


def stop(running: session.Session) -> None:
    """End the session. No further signal cuts that short."""
    ignore_endings()
    running.stop()


def remove(run: Path) -> None:
    """Remove the scan's temporary folder, or say that it stays. No further signal cuts that
    short."""
    ignore_endings()
    shutil.rmtree(run, ignore_errors=True)
    if os.path.lexists(run):
        console.warn(f"{run} could not be removed whole")


def scratch(stack: ExitStack, *, sandboxed: bool) -> Path:
    """A new temporary folder, which goes when `stack` closes."""
    # TMPDIR can name a folder that the sandbox must hide.
    place = "/tmp" if sandboxed else None  # noqa: S108
    folder = Path(tempfile.mkdtemp(prefix="claude-security-", dir=place)).resolve()
    stack.callback(remove, folder)
    return folder


def start(args: Args, stack: ExitStack) -> tuple[Scan, session.Session]:
    """Check what the scan needs, ask for the user's yes, and start the session."""
    root = args.path.resolve()
    output = (args.output or root).resolve()
    if missing := next((p for p in (root, output) if not p.is_dir()), None):
        msg = f"{missing} is not a folder"
        raise StartError(msg)
    if not os.access(output, os.W_OK | os.X_OK):
        msg = f"the report cannot be written in {output}: name a folder with --output"
        raise StartError(msg)
    if _MAC:
        raise StartError(_NOT_ON_MAC)
    sandbox.clear_path_of(root)
    found = sandbox.find_program("claude")
    if not found:
        msg = "claude is not on PATH, or lies in the folder to scan: install Claude Code first"
        raise StartError(msg)
    python = sys.executable
    if not args.no_sandbox:
        sandbox.refuse_other_systems()
        if UNGUARDED and not (python := sandbox.newer_python()):
            msg = (
                f"{UNGUARDED}, or install Python 3.10 to 3.14 in the same folder as this "
                "Python's real file"
            )
            raise StartError(msg)
        sandbox.refuse_hidden(found)
        sandbox.unset_code_variables(root)
        if why := sandbox.led_astray(args.path, root):
            raise StartError(why)
    claude = str(found)
    variables = sandbox.session_variables()
    if not args.no_sandbox:
        variables |= route(args, variables)
    by_command = bool(args.credential_command)
    if routes := sandbox.routes_not_loaded(root, variables, by_command=by_command):
        named = ", ".join(f"{name} ({file})" for name, file in routes.items())
        msg = (
            f"the project's settings set {named}. The scan does not load them, so it could use "
            "another host or sign-in than Claude Code uses in this project. Set each name in your "
            "environment, or under env in your own Claude Code settings. With an empty value, "
            "your key or sign-in goes to the provider's own host, or to a host that you have set. "
            "A cloud's variable, such as a region or a profile, can need a value. Copy the "
            "project's value only if you trust it. In the sandbox, a provider goes in --provider, "
            "and its URL in --model-base-url."
        )
        if sandbox.KEY_HELPER in routes:
            msg += (
                f" For {sandbox.KEY_HELPER}, set ANTHROPIC_API_KEY. In the sandbox, with no cloud "
                "provider on, you can also give the helper as --credential-command."
            )
        if sandbox.AWS_HELPER in routes:
            msg += (
                f" For {sandbox.AWS_HELPER}, in the sandbox on Bedrock, --credential-command can "
                "print the keys as `aws configure export-credentials` does."
            )
        raise StartError(msg)
    held = None
    helper_first = sandbox.uses_login(variables | {login.TOKEN: ""}) and not args.no_sandbox
    if helper_first and not args.credential_command and sandbox.has_key_helper():
        msg = "apiKeyHelper does not run in the sandbox: give it as --credential-command"
        raise StartError(msg)
    if (
        helper_first
        and args.credential_command
        and login.TOKEN in variables
        and "authorization" in variables.get("ANTHROPIC_CUSTOM_HEADERS", "").lower()
        and (sandbox.has_key_helper() or sandbox.KEY_HELPER in sandbox.routes_not_loaded(root, {}))
    ):
        variables["ANTHROPIC_AUTH_TOKEN"] = variables[login.TOKEN]
    if sandbox.uses_login(variables) and not args.credential_command:
        if not login.signed_in(claude, by_store=not args.no_sandbox):
            msg = "Claude Code is not signed in: run `claude auth login`"
            raise StartError(msg)
        if not (args.no_sandbox or (held := login.stored())):
            msg = (
                "the sandbox cannot read Claude Code's login: set CLAUDE_CODE_OAUTH_TOKEN to the "
                "token that `claude setup-token` prints, or add --credential-command"
            )
            raise StartError(msg)
    owner = login.owner()
    run = scratch(stack, sandboxed=not args.no_sandbox)
    for name in ("start", "reports"):
        (run / name).mkdir()
    box = token = folder = None
    if args.no_sandbox:
        console.warn("Claude Code runs in auto mode with no sandbox, with your user's access")
    else:
        if held and login.TOKEN in held.variables:
            token = scratch(stack, sandboxed=True) / login.FILE
            # Never closed: a renewal can outlast the folder, whose name can then be another's.
            folder = os.open(token.parent, os.O_RDONLY)
            login.lay(held.variables[login.TOKEN], folder)
        reads = [Path(path).resolve() for path in args.allow_read]
        options = ["--sudo"] if args.sudo else []
        options += ["--no-cgroup"] if args.no_cgroup else []
        options += [f"--credential-command={asked}"] if (asked := args.credential_command) else []
        options += [f"--token-file={token}"] if token else []
        signed = held.variables if held else {}
        passed = [name for name in signed if name not in provider.SECRETS]
        box = sandbox.Sandbox(root, run, variables | signed, passed, reads, options, python)
        print(destination(args, held), file=sys.stderr)
    confirm(args)
    if box:
        box.check()
    mode, words = request(args)
    effort, scope = shown(args)
    target = Target(
        name=root.name,
        mode=mode,
        effort=effort,
        scope=scope,
        branch=git.run(str(root), "branch", "--show-current") or "",
        version=plugin.version() or "",
        sandboxed=box is not None,
        hosts=["the model"] if box else [],
        writable=["the report", "memory"] if box else [],
    )
    scan = Scan(target, Atlas.of(root))
    argv = session.command(claude, run, args.model, sandboxed=box is not None)
    # Reports that lie elsewhere stay out: a copy would show them to a scan in the sandbox.
    places = [place for place in dict.fromkeys((output, root)) if place.is_relative_to(root)]
    earlier = [] if args.of_changes else report.recall(places, run / "reports")
    job = box.popen(argv) if box else session.popen(argv, root)
    running = session.Session(job, scan, root, run / "reports", output, earlier)
    stack.callback(stop, running)
    try:
        running.start(words)
        if held and folder is not None:
            running.keep_signed_in(claude, held, owner, folder)
    except KeyboardInterrupt as error:
        raise StoppedError(session.STOPPED) from error
    return scan, running


def main(argv: list[str]) -> int:
    args = parse(argv)
    for number in _ENDINGS:
        # A signal that is ignored, as under nohup, stays ignored.
        if signal.getsignal(number) is not signal.SIG_IGN:
            signal.signal(number, signal.default_int_handler)
    with ExitStack() as stack:
        try:
            if args.install:
                print(command.install())
                return 0
            watch = plain.run
            watch = show.watcher(args, stack)
            scan, running = start(args, stack)
        except StoppedError as error:
            sys.stderr.write(f"{plugin.NAME}: {error}\n")
            return 1
        except SandboxError as error:
            advice = "" if SWAPPED in str(error) else f"{_NO_SANDBOX}\n"
            sys.stderr.write(f"{plugin.NAME}: {error}\n{advice}")
            return 2
        except _REFUSALS as error:
            sys.stderr.write(f"{plugin.NAME}: {str(error) or 'no scan was started'}\n")
            return 2
        with suppress(KeyboardInterrupt, EOFError):
            watch(scan)
        stop(running)
        with console_mode(1):
            print(f"\n{plain.summary(scan)}", flush=True)
        if running.refused:
            return 2
        return 0 if scan.result.state in {State.DONE, State.SKIPPED} else 1


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    try:
        sys.exit(main(sys.argv[1:]))
    except OSError as error:
        if error.errno not in {errno.EPIPE, errno.EIO}:
            raise
        # What reads the output has gone, and Python's flush at exit must not fail as well.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
