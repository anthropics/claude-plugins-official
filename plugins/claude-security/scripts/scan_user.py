#!/usr/bin/env python3
"""Give the GitHub Action's relay its own user, limited to the addresses that model requests go to.

Usage:
  scan_user.py host PROVIDER URL
  scan_user.py rules HOST:PORT FOLDER
  scan_user.py start FOLDER -- COMMAND...
  scan_user.py session FOLDER -- ARGUMENTS...
  scan_user.py view FOLDER VARIABLES -- COMMAND...
  scan_user.py alone FOLDER VARIABLES -- COMMAND...
  scan_user.py end REPORTS OUTCOME
  scan_user.py check HOST:PORT
  scan_user.py sweep

The user claude-security-scan already exists.

  host     Prints the `host:port` that model requests go to: the one that URL names or, if URL
           is empty, PROVIDER's own.
  rules    Looks up the host's IPv4 addresses once. Writes into FOLDER `hosts`, a copy of /etc/hosts
           that also maps the host to them, and `iptables` and `ip6tables`, for iptables-restore and
           ip6tables-restore with --noflush.
  start    Execs COMMAND as the user, through sudo and `view`. COMMAND gets $PATH and $HOME, and
           those of the caller's other variables that handed_on() picks.
  session  Execs sandbox.py as root, through sudo and `alone`, with the lines of the file
           claude-security-sandbox-arguments beside FOLDER, then ARGUMENTS. It gets the same
           variables and those that name sign-in files, which it hides, and goes on as the user once
           its keeper runs. Of the same variables, the command inside gets those that relay_alone()
           does not keep back, those that the action's input names, and what sandbox.py itself
           passes: the names of models, regions and the Vertex project.
  view     Run as root in its own mount namespace, lays FOLDER's `hosts` over /etc/hosts. Then it
           execs COMMAND with the variables in the file VARIABLES, which it removes.
  alone    As `view`, but it lays an empty tmpfs over /run, COMMAND runs as process 1 of a PID
           namespace of its own, and this verb stays. It turns INT, TERM and HUP into a TERM for
           COMMAND, and exits as COMMAND does.
  end      Waits for the last process of the user and of the sandbox's user ids to end, or kills
           what is left and fails. Once a look finds nothing, it kills as each of those ids what
           the look missed, and looks again. It fails if that kill fails, or if a file below
           REPORTS has a second name. Otherwise it makes the caller the owner of REPORTS, and
           closes that folder to other users.
           OUTCOME is that of the scan's step. Where it is `cancelled`, this verb kills what is
           left at once, and again until a kill passes and nothing is left, fails if that has not
           happened after at least a minute, and leaves REPORTS as it is.
  check    Run as the user, connects to the host and finds what else the firewall does not
           refuse.
  sweep    Run as root, kills every process of the user and of the sandbox's user ids with one
           signal for each id, which no fork can outrun, and fails if a kill fails.

Needs Linux and sudo without a password. Exits 0, or as what it execs does; 1, with the reason on
standard error. Python 3.9, stdlib only.
"""

from __future__ import annotations

import errno
import ipaddress
import os
import re
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, NoReturn, final

# Under -I, -P or PYTHONSAFEPATH Python leaves this script's folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sandbox.plan import FREE_IDS
from lib.sandbox.provider import CREDENTIAL_FILES
from lib.sandbox_hosts import HostError, Provider, allowed

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence


@final
class Scan:
    """The user, whose group and chain share its name, and the values the verbs use."""

    USER = "claude-security-scan"
    ARGUMENTS = "claude-security-sandbox-arguments"
    OWNERS = ",".join((USER, *map(str, FREE_IDS)))
    NAMED_BY = (
        "The name comes from model_base_url or, if that is empty, from the job's provider settings."
    )
    PRIVATELY = "Please report this privately, as this action's SECURITY.md describes."
    POLLS = 600
    POLL_S = 0.1
    CANCELLED = "cancelled"
    TEST_NET = "192.0.2.1"
    AZURE_PLATFORM = "168.63.129.16"
    RESOLVER = "127.0.0.53"
    DNS_PORT = 53
    HOSTS = "hosts"
    TIMEOUT_S = 10
    VARIABLES_FILE_PREFIX = "claude-security-variables-"
    SET_ELSEWHERE = frozenset({"PATH", "HOME", "USER", "LOGNAME"})
    HANDED_ON = frozenset({
        "CI",
        "CLOUD_ML_REGION",
        "GITHUB_ACTIONS",
        "GITHUB_WORKSPACE",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_KEY_1",
        "GIT_CONFIG_KEY_2",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CONFIG_VALUE_0",
        "GIT_CONFIG_VALUE_1",
        "GIT_CONFIG_VALUE_2",
        "GIT_NO_LAZY_FETCH",
        "GIT_TERMINAL_PROMPT",
        "LANG",
        "NODE_EXTRA_CA_CERTS",
        "TZ",
    })
    PREFIXES = ("ANTHROPIC_", "CLAUDE_", "LC_")
    BEDROCK = "CLAUDE_CODE_USE_BEDROCK"
    FOR_BEDROCK = frozenset({
        "AWS_ACCESS_KEY_ID",
        "AWS_BEARER_TOKEN_BEDROCK",
        "AWS_REGION",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
    })
    INPUT = "scan_variables"
    MORE = "CLAUDE_SECURITY_SCAN_VARIABLES"
    # These hold or mint the job's tokens. scripts/sandbox/sandboxed-claude.sh unsets them too.
    TOKENS = frozenset({
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "OVERRIDE_GITHUB_TOKEN",
        "DEFAULT_WORKFLOW_TOKEN",
        "ALL_INPUTS",
        "ACTIONS_RUNTIME_TOKEN",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
        "ACTIONS_ID_TOKEN_REQUEST_URL",
    })
    RELAY_ALONE = (
        "ANTHROPIC_",
        "AWS_",
        "CLAUDE_CODE_CLIENT_",
        "NODE_EXTRA_CA_CERTS",
    )
    SECRET = re.compile(r"TOKEN(?!S)|SECRET|KEY|PASS|CREDENTIAL", re.IGNORECASE)


class ScanUserError(Exception):
    """Why the work was not done, in words for whoever reads the job's log."""


@dataclass(frozen=True)
class Launch:
    """The words to put before a command, and the variables that the whole line starts under."""

    before: tuple[str, ...]
    variables: Mapping[str, str]


def host(provider: str, url: str) -> None:
    print(allowed(Provider(provider), os.environ, url))


def address(target: str) -> tuple[str, int]:
    """The host and the port of `target`, as `host` prints it."""
    name, _, port = target.rpartition(":")
    return name, int(port)


def chain(accepted: Iterable[str]) -> str:
    """What iptables-restore or ip6tables-restore reads: the user's chain, the jump to it, and the
    rejection of the sandbox's ids."""
    user = Scan.USER
    return "\n".join((
        "*filter",
        f":{user} - [0:0]",
        *accepted,
        f"-A {user} -j REJECT",
        # Inserted first, so that no one else's ACCEPT comes before them.
        f"-I OUTPUT 1 -m owner --uid-owner {user} -j {user}",
        f"-I OUTPUT 1 -m owner --uid-owner {FREE_IDS[0]}-{FREE_IDS[-1]} -j REJECT",
        "COMMIT",
        "",
    ))


def rules(target: str, folder: str) -> None:
    name, port = address(target)
    try:
        found = socket.getaddrinfo(name, port, socket.AF_INET, socket.SOCK_STREAM)
    except socket.gaierror as error:
        msg = (
            f"This runner found no IPv4 address for {name}, the host that model requests go to "
            f"({error.strerror}). Nothing was scanned. {Scan.NAMED_BY} Check that the name is "
            "right and that this runner can look it up. Then run the job again."
        )
        raise ScanUserError(msg) from error
    addresses = sorted({str(place[0]) for *_, place in found})
    parsed = map(ipaddress.IPv4Address, addresses)
    if bad := ", ".join(
        str(a)
        for a in parsed
        if a.is_link_local or a.is_loopback or a.is_unspecified or str(a) == Scan.AZURE_PLATFORM
    ):
        msg = (
            f"{name}, the host that model requests go to, resolves to {bad}. The action does not "
            "support a model host at a loopback or link-local (169.254.0.0/16) address, at "
            f"0.0.0.0, or at {Scan.AZURE_PLATFORM} (Azure's platform services). Nothing was "
            f"scanned. {Scan.NAMED_BY}"
        )
        raise ScanUserError(msg)
    hosts = Path("/etc/hosts").read_text(encoding="utf-8").rstrip("\n")
    for file, text in {
        Scan.HOSTS: "\n".join((hosts, *(f"{one} {name}" for one in addresses), "")),
        "iptables": chain(
            f"-A {Scan.USER} -d {one} -p tcp --dport {port} -j ACCEPT" for one in addresses
        ),
        "ip6tables": chain(()),
    }.items():
        (Path(folder) / file).write_text(text, encoding="utf-8")
    # The user reads it as its /etc/hosts, whatever the job's umask.
    (Path(folder) / Scan.HOSTS).chmod(0o644)


def run(*words: str | Path, fine: Collection[int] = (0,)) -> subprocess.CompletedProcess[bytes]:
    """Run a program, which must end with a status in `fine`. Returns what it did."""
    ran = subprocess.run(words, check=False, capture_output=True)
    if ran.returncode not in fine:
        # !a keeps what the program said on one line, whatever a file's name holds.
        err = ran.stderr.decode("utf-8", "surrogateescape").strip()
        why = f" and said {err!a}" if err else ""
        msg = f"`{shlex.join(map(str, words))}` failed with status {ran.returncode}{why}"
        raise ScanUserError(msg)
    return ran


def left_running() -> bool:
    """Whether the user or one of the sandbox's ids has a process. Raises ScanUserError if that
    cannot be found out."""
    return not run("pgrep", "-u", Scan.OWNERS, fine=(0, 1)).returncode


def give_back(reports: str) -> None:
    """Make the caller the owner of what is below `reports`, and close that folder to other users.
    Raises ScanUserError if a file there has a second name."""
    linked = run(
        "sudo", "-n", "find", reports, "!", "-type", "d", "-links", "+1", "-print", "-quit"
    )
    if linked.stdout:
        name = linked.stdout.decode("utf-8", "surrogateescape").rstrip("\n")
        msg = (
            f"{name!a} has a second name (a hard link), so the report was not given back to the "
            f"job's user. {Scan.PRIVATELY}"
        )
        raise ScanUserError(msg)
    run("sudo", "-n", "chown", "-R", "-h", f"{os.getuid()}:{os.getgid()}", "--", reports)
    # The user could change this folder's mode while the folder was its own.
    Path(reports).chmod(0o700)


def sweep() -> None:
    """Kill each process of the user and of the sandbox's ids with one signal for each id, which
    no fork can outrun. Raises ScanUserError if that fails."""
    run("sudo", "-n", "/usr/bin/python3", "-I", "-S", str(Path(__file__).resolve()), "sweep")


def sweep_as_root() -> None:
    """Run as root: for each of the user and the sandbox's ids, a child takes that id and sends
    SIGKILL to -1, which reaches every process of the id but the child itself. Raises ScanUserError
    if a child fails."""
    import pwd

    failed: list[str] = []
    for uid in (pwd.getpwnam(Scan.USER).pw_uid, *FREE_IDS):
        if uid == 0:
            msg = "User id 0 is root's, whose processes the sweep does not kill."
            raise ScanUserError(msg)
        child = os.fork()
        if not child:
            try:
                os.setresuid(uid, uid, uid)
                with suppress(ProcessLookupError):
                    os.kill(-1, signal.SIGKILL)
            except BaseException:
                os._exit(1)
            os._exit(0)
        _, status = os.waitpid(child, os.WUNTRACED)
        if os.WIFSTOPPED(status):
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
        if status:
            failed.append(str(uid))
    if failed:
        msg = f"The kill of the processes of user ids {', '.join(failed)} failed."
        raise ScanUserError(msg)


def kill_until_none_is_left() -> None:
    """Kill each process of the user and of the sandbox's ids, again until a kill passes and none is
    left. Raises ScanUserError if that has not happened after at least a minute, or a look cannot
    find out."""
    failed = None
    for _ in range(Scan.POLLS):
        try:
            sweep()
            failed = None
        except ScanUserError as error:
            failed = error
        if failed is None and not left_running():
            return
        time.sleep(Scan.POLL_S)
    msg = (
        f"A process of the scan's user ({Scan.USER}) or of the sandbox may still run after at "
        f"least {Scan.POLLS * Scan.POLL_S:.0f} seconds of tries to kill what the cancelled scan "
        "left."
    )
    if failed:
        msg += f" The last try: {failed}."
    raise ScanUserError(msg) from failed


def end(reports: str, scan_outcome: str) -> None:
    if scan_outcome == Scan.CANCELLED:
        kill_until_none_is_left()
        return
    for _ in range(Scan.POLLS):
        if not left_running():
            sweep()
            if not left_running():
                give_back(reports)
                return
        time.sleep(Scan.POLL_S)
    sweep()
    msg = (
        f"A process of the scan's user ({Scan.USER}) or of the sandbox was still running "
        f"{Scan.POLLS * Scan.POLL_S:.0f} seconds after the scan's step ended, so it was killed. "
        "The report may not be whole, and it was not given back to the job's user."
    )
    raise ScanUserError(msg)


def not_for_the_input(name: str) -> bool:
    """Whether the input may not name the variable `name`: it holds or mints one of the job's
    tokens, or the launch or sudo sets it."""
    return name in Scan.TOKENS | Scan.SET_ELSEWHERE or name.startswith("SUDO_")


def named_by_the_input() -> list[str]:
    return os.environ.get(Scan.MORE, "").split()


def handed_on() -> dict[str, str]:
    """The caller's variables that both launches write to the file of variables, beside PATH and
    HOME: those that Scan.HANDED_ON, Scan.PREFIXES and, on Amazon Bedrock, Scan.FOR_BEDROCK name,
    and those that $CLAUDE_SECURITY_SCAN_VARIABLES names. Raises ScanUserError for a name that the
    input may not give."""
    more = named_by_the_input()
    if refused := list(filter(not_for_the_input, more)):
        msg = (
            f"The input {Scan.INPUT} names {', '.join(map(repr, refused))}, which the scan cannot "
            "get. Name no variable that holds or mints the job's token, or that the action or sudo "
            "sets itself. Nothing was scanned."
        )
        raise ScanUserError(msg)
    for_bedrock = Scan.FOR_BEDROCK if os.environ.get(Scan.BEDROCK) == "1" else ()
    listed = {*Scan.HANDED_ON, *for_bedrock, *more}
    # Not the input's own text: it may hold a value that a team put there by mistake.
    return {
        name: value
        for name, value in os.environ.items()
        if name != Scan.MORE and (name in listed or name.startswith(Scan.PREFIXES))
    }


def write_variables(given: Mapping[str, str]) -> Path:
    """Write `given` to a new file of variables, in RUNNER_TEMP, that only the caller can open.
    Returns its path."""
    temp = os.environ["RUNNER_TEMP"]
    descriptor, variables = tempfile.mkstemp(prefix=Scan.VARIABLES_FILE_PREFIX, dir=temp)
    with os.fdopen(descriptor, "wb") as file:
        file.write(b"\0".join(os.fsencode(f"{name}={value}") for name, value in given.items()))
    return Path(variables)


def take_variables(variables: Path) -> dict[str, str]:
    """The variables in the file `variables`, which it removes."""
    parts = os.fsdecode(variables.read_bytes()).split("\0")
    variables.unlink()
    return dict(part.split("=", 1) for part in parts)


def launch(verb: str, folder: str, handed: Mapping[str, str], *program: str) -> Launch:
    """The words that, put before what `program` takes, run it as root under `verb`, to start under
    PATH alone. `program` starts with a full path, because root must run nothing that the job's PATH
    finds. Writes `handed`, with PATH and HOME, to the file of variables that the words name."""
    path = os.environ["PATH"]
    variables = write_variables({**handed, "PATH": path, "HOME": os.environ["HOME"]})
    words = (
        *("sudo", "-n", "unshare", "--mount", "--propagation", "private", "--ipc"),
        *("python3", "-I", "-S", str(Path(__file__).resolve()), verb),
        *(folder, str(variables), "--", *program),
    )
    return Launch(words, {"PATH": path})


def start(folder: str) -> Launch:
    """The words that, put before a command, run it as the user."""
    user = Scan.USER
    drop = ("--reuid", user, "--regid", user, "--clear-groups", "--no-new-privs", "--")
    return launch("view", folder, handed_on(), "/usr/bin/setpriv", *drop)


def relay_alone(name: str) -> bool:
    """Whether --env leaves the variable `name` out, unless the input names it."""
    by_prefix = name.startswith(Scan.PREFIXES) and Scan.SECRET.search(name)
    return name.startswith(Scan.RELAY_ALONE) or bool(by_prefix)


def session(folder: str) -> Launch:
    """The words that, put before ARGUMENTS, run sandbox.py as root, to go on as the user."""
    sandbox = str(Path(__file__).resolve().with_name("sandbox.py"))
    given = (Path(folder).parent / Scan.ARGUMENTS).read_text(encoding="utf-8").splitlines()
    named, handed = named_by_the_input(), handed_on()
    passed = (f"--env={name}" for name in handed if name in named or not relay_alone(name))
    files = {name: os.environ[name] for name in CREDENTIAL_FILES if name in os.environ}
    python = ("/usr/bin/python3", "-I", "-S")
    return launch(
        "alone", folder, {**handed, **files}, *python, sandbox, "--user", Scan.USER, *passed, *given
    )


def view(folder: str, variables: str) -> Launch:
    """Take the file of variables and pin the host. Returns what COMMAND starts under: root's own
    variables, and over them the file's."""
    given = take_variables(Path(variables))
    run("mount", "--bind", Path(folder) / Scan.HOSTS, "/etc/hosts")
    return Launch((), {**os.environ, **given})


def ended_otherwise(kind: socket.SocketKind, place: str, port: int) -> str | None:
    """How a try at `place` ended, in words. None if it was refused as by a REJECT, or `place`
    is IPv6 and this machine has no IPv6 at all, or has it switched off."""
    family, level, hops = (
        (socket.AF_INET6, socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS)
        if ":" in place
        else (socket.AF_INET, socket.IPPROTO_IP, socket.IP_TTL)
    )
    refusals = (
        errno.ECONNREFUSED if kind is socket.SOCK_STREAM else errno.EPERM,
        *((errno.EAFNOSUPPORT, errno.EADDRNOTAVAIL) if family is socket.AF_INET6 else ()),
    )
    try:
        with socket.socket(family, kind) as sock:
            sock.settimeout(Scan.TIMEOUT_S)
            sock.setsockopt(level, hops, 1)
            sock.connect((place, port))
            sock.send(b"\0")
    except OSError as error:
        if error.errno in refusals:
            return None
        return f"the try ended otherwise: {error.strerror or error}"
    return "it succeeded"


def reaches(place: str, port: int) -> Iterator[str]:
    """The tries, other than TCP to `place` at `port`, that are not refused, each in a clause."""
    for kind, where, at in (
        (socket.SOCK_STREAM, Scan.TEST_NET, port),
        (socket.SOCK_STREAM, place, 443 if port == 80 else 80),
        (socket.SOCK_DGRAM, place, port),
        (socket.SOCK_DGRAM, Scan.RESOLVER, Scan.DNS_PORT),
        (socket.SOCK_STREAM, Scan.RESOLVER, Scan.DNS_PORT),
        (socket.SOCK_DGRAM, "::1", Scan.DNS_PORT),
    ):
        if how := ended_otherwise(kind, where, at):
            what = "a TCP connection" if kind is socket.SOCK_STREAM else "a UDP datagram"
            yield f"{what} from it to {where} at port {at} is not refused by the firewall ({how})"


def check(target: str) -> None:
    name, port = address(target)
    user = f"the scan's user ({Scan.USER})"
    try:
        socket.create_connection((name, port), Scan.TIMEOUT_S).close()
    except OSError as error:
        msg = (
            f"As {user}, this runner could not connect to {name} at port {port} "
            f"({error.strerror or error}). Nothing was scanned. If model_base_url names that "
            "host, check that this runner can reach it. Then run the job again."
        )
        raise ScanUserError(msg) from error
    if found := list(reaches(socket.gethostbyname(name), port)):
        msg = (
            f"The checks of {user} found that {'; '.join(found)}. Nothing was scanned. "
            f"{Scan.PRIVATELY}"
        )
        raise ScanUserError(msg)


def become(command: list[str], variables: Mapping[str, str]) -> NoReturn:
    """Replace this process with `command`, under `variables`."""
    os.execvpe(command[0], command, variables)


def stay(command: list[str], variables: Mapping[str, str]) -> NoReturn:
    """Lay an empty tmpfs over /run, since no firewall covers a Unix socket. Run `command` under
    `variables` as process 1 of a PID namespace of its own, with that namespace's /proc. End it with
    a TERM if a signal asks this process to end, and exit as it does."""
    from lib.sandbox.kernel import Mount, Namespace, mount, unshare

    quiet = Mount.NO_SETUID | Mount.NO_DEVICES | Mount.NO_EXEC
    mount("tmpfs", "/run", quiet, "mode=755")
    unshare(Namespace.PID)
    child = os.fork()
    if not child:
        os.setsid()
        mount("proc", "/proc", quiet)
        become(command, variables)

    def stop(*_signal: object) -> None:
        with suppress(ProcessLookupError):
            os.kill(child, signal.SIGTERM)

    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, stop)
    code = os.waitstatus_to_exitcode(os.waitpid(child, 0)[1])
    sys.exit(code if code >= 0 else 128 - code)


VERBS: Final[Mapping[str, tuple[Callable[..., Launch | None], Callable[..., NoReturn] | None]]] = {
    "host": (host, None),
    "rules": (rules, None),
    "start": (start, become),
    "session": (session, become),
    "view": (view, become),
    "alone": (view, stay),
    "end": (end, None),
    "sweep": (sweep_as_root, None),
    "check": (check, None),
}


def main(argv: Sequence[str]) -> int:
    dashes = argv.index("--") if "--" in argv else len(argv)
    verb, runs = VERBS[argv[0]]
    try:
        if (command_line := verb(*argv[1:dashes])) and runs:
            runs([*command_line.before, *argv[dashes + 1 :]], command_line.variables)
    except (ScanUserError, HostError, OSError, ValueError) as error:
        sys.stderr.write(f"scan_user.py: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
