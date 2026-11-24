"""A Claude Code session that runs one scan with nobody at its prompt."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from contextlib import suppress
from typing import IO, TYPE_CHECKING, cast

from lib import display, plugin, products, strictjson
from lib.sandbox.plan import BROKEN
from lib.strictjson import JsonMap, is_map

from . import login, report, sandbox
from .scan import Result, Scan, Stage, State
from .stream import HOOKED_TOOLS, Reader

if TYPE_CHECKING:
    from collections.abc import Callable, Collection
    from pathlib import Path

_WITHHELD = (
    *("AskUserQuestion", "WebFetch", "WebSearch", "Artifact", "EnterWorktree", "ExitWorktree"),
    *("CronCreate", "CronDelete", "CronList", "ScheduleWakeup", "RemoteTrigger", "SendMessage"),
)
_VARIABLES = {
    "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_CRON": "1",
    "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": "1",
    "DISABLE_AUTOUPDATER": "1",
}
# Claude Code renews a login in the last five minutes of its life, so a check falls in that time.
_LOGIN_CHECK_SECONDS = 100
_STORE_CHECK_SECONDS = 2
_EXPIRED = re.compile(r"\b401\b|OAuth|/login")
# A tool call waits this long for an answer to its callback. Claude Code's default is ten minutes.
_CALLBACK_SECONDS = 10
_GRACE_SECONDS = 5
_EXIT_SECONDS = 45
_MESSAGE_CHARS = 4000
# Code and bold text in Markdown, which a model can write though it is asked for plain text.
_CODE = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"(?<![\w/*])\*\*(?=\S)([^*\n]*[^*\s])\*\*(?![\w/*])")
# How the recipes' closing offers begin. A model can keep them, or put a name in the place of "I",
# and nobody can answer them here.
_OFFER = re.compile(
    r"Do you want me to suggest fixes for these\?"
    r"|[\w ]{1,40} can also analyze this project's attack surface"
)
_REFUSED = (
    "If Claude Code signs in with a key, a token or a command, check it. If it signs in with a "
    "login, start claude once to renew it; for a long scan, set CLAUDE_CODE_OAUTH_TOKEN to the "
    "token that `claude setup-token` prints. A credential in ANTHROPIC_CUSTOM_HEADERS can go in "
    "place of a key or a login: check it too."
)
_MANAGED_CAUSE = (
    "Your organization's managed settings can be the cause: {}. In the sandbox, Claude Code "
    "reaches the model through a relay and loads the plugin from its folder. To scan with no "
    "sandbox, add --no-sandbox."
)
_NOT_RENEWED = "Your login ends soon and could not be renewed. Start claude once to renew it."
_OTHER_OWNER = (
    "Your login ends soon, and Claude Code is now signed in to another account. Sign in again to "
    "the account that started the scan."
)
_NOT_WRITTEN = "Your login was renewed, but its new token could not be written for the scan: {}."
STOPPED = "The scan was stopped."
# The session can offer to continue the scan, but it ends with the command.
_NO_REPORT = "No report was written. The command cannot continue a scan that stopped."
_NO_AUTO = (
    "Claude Code is not in auto mode, and nobody can approve a command here. Auto mode needs a "
    "model that supports it (see --model) and settings that allow it."
)
_NO_PLUGIN = (
    "Claude Code did not load the plugin, so nothing was scanned. Where managed settings turn the "
    "plugin on, only its installed copy loads: install it, and add --no-sandbox."
)
_LEFT_AUTO = "Claude Code left auto mode during the scan, so the scan can have gaps."
_UNFINISHED = (
    "The session wrote a report but did not finish. Its files can still hold credential values."
)


def _prompt(request: str) -> str:
    """What the session is asked: the plugin's command, the request, and the yes to its cost."""
    return (
        f"/{plugin.NAME}:{plugin.NAME} {request}\n\n"
        "I understand that this scan may take a while and use a significant number of tokens."
    )


def _system_prompt(reports: Path) -> str:
    """What the session is told of where it runs."""
    return (
        f"The {plugin.NAME} command started this session, to run one scan. Nobody can answer a "
        "question: where a recipe would ask, take its default, and where it has none, stop and "
        "say what is missing. Where a recipe makes or names the report directory, use "
        f"{reports.as_posix()}/{plugin.REPORT_DIR_PREFIX}<ts>, with that whole path in place of "
        "the bare name, and not the recipe's start folder; where its command takes the folder for "
        f"that directory, give {reports.as_posix()}. "
        f"The {plugin.NAME} command then delivers the report. Only your last message reaches the "
        "user. In it, "
        "repeat what still holds of your kickoff message, name the report directory without its "
        "path if a report was written, and write plain text with no Markdown. Leave out the "
        "offers and the question that a recipe ends with: nobody can answer them."
    )


def command(claude: str, run: Path, model: str, *, sandboxed: bool) -> list[str]:
    """The claude command line. If it needs settings, they are written to a file in `run`."""
    settings: dict[str, object] = {}
    installed = "" if sandboxed else sandbox.installed()
    if sandboxed:
        # Claude Code's own sandbox cannot start inside the plugin's.
        settings = {**sandbox.kept_settings(), "env": _VARIABLES, "sandbox": {"enabled": False}}
    elif installed:
        settings = {"enabledPlugins": {installed: True}}
    path = run / "start/settings.json"
    if settings:
        path.write_text(json.dumps(settings), encoding="utf-8")
    reports = run / "reports"
    return [
        *(claude, "-p", "--verbose"),
        *("--input-format", "stream-json", "--output-format", "stream-json"),
        # In the sandbox the user's settings come by --settings.
        *("--setting-sources", "" if sandboxed else "user"),
        *("--permission-mode", "auto", "--strict-mcp-config"),
        *(("--settings", str(path)) if settings else ()),
        *("--add-dir", str(reports)),
        *(() if installed else ("--plugin-dir", str(plugin.ROOT))),
        *(("--model", model) if model else ()),
        *("--disallowedTools", ",".join(_WITHHELD)),
    ]


def popen(argv: list[str], root: Path) -> subprocess.Popen[bytes]:
    """Start `argv` in `root` with no sandbox and the session's variables, in a process group of
    its own, with three pipes."""
    env = {name: value for name, value in os.environ.items() if name != "CLAUDECODE"}
    return subprocess.Popen(
        argv,
        cwd=root,
        env={**env, **_VARIABLES},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )


class Session:
    """Drives `job`, a started claude command, through one scan, and delivers the report.
    `refused` says that the job ended before its first row, and not by a stop, or that it was not
    in auto mode, or in the sandbox had not loaded the plugin, before any workflow or agent
    started."""

    def __init__(
        self,
        job: subprocess.Popen[bytes],
        scan: Scan,
        root: Path,
        reports: Path,
        into: Path,
        earlier: Collection[Path],
    ) -> None:
        self.refused: bool = False
        self._job: subprocess.Popen[bytes] = job
        self._stdin: IO[bytes] = cast("IO[bytes]", job.stdin)
        self._stdout: IO[bytes] = cast("IO[bytes]", job.stdout)
        self._scan: Scan = scan
        self._reports: Path = reports
        self._earlier: Collection[Path] = earlier
        self._into: Path = into
        self._reader: Reader = Reader(scan, root)
        self._errors: deque[bytes] = deque(maxlen=8)
        self._listener: threading.Thread = threading.Thread(
            target=self._errors.extend, args=(job.stderr,), daemon=True
        )
        self._sending: threading.Lock = threading.Lock()
        self._stopped: bool = False
        self._heard: bool = False
        self._answered: bool = False
        self._thread: threading.Thread | None = None

    def start(self, request: str) -> None:
        """Send the request, and follow the session on a thread until it ends."""
        hook = {
            "matcher": "|".join(HOOKED_TOOLS),
            "hookCallbackIds": ["tool"],
            "timeout": _CALLBACK_SECONDS,
        }
        hooks = {"PostToolUse": [hook]}
        told = _system_prompt(self._reports)
        hello = {
            "subtype": "initialize",
            "hooks": hooks,
            "appendSystemPrompt": told,
            "systemPromptSnapshot": False,
        }
        message = {"role": "user", "content": _prompt(request)}
        self._scan.enter(Stage.SETUP)
        self._send({"type": "control_request", "request_id": "hello", "request": hello})
        self._send({"type": "user", "message": message, "parent_tool_use_id": None})
        self._listener.start()
        self._thread = threading.Thread(target=self._follow, daemon=True)
        self._thread.start()

    def keep_signed_in(self, claude: str, held: login.Login, owner: str, folder: int) -> None:
        """Have Claude Code renew the login outside the sandbox, and lay each new token in `folder`
        while login.owner() is `owner`. With an empty `owner` nothing is compared."""
        laying = threading.Lock()
        written = True

        def lay() -> None:
            nonlocal held, written
            with laying, suppress(OSError):
                fresh = login.stored()
                if (
                    self._scan.running
                    and fresh
                    and fresh != held
                    # A key in the store is no renewal, so the old token stays due.
                    and (token := fresh.variables.get(login.TOKEN))
                    and owner in {"", login.owner()}
                ):
                    try:
                        login.lay(token, folder)
                    except OSError as error:
                        written = False
                        self._reader.tell("token", _NOT_WRITTEN.format(error.strerror))
                    else:
                        held, written = fresh, True

        def renew() -> None:
            if held.ending:
                with suppress(OSError):
                    login.signed_in(claude)
                lay()
                if held.ending and written and self._scan.running:
                    switched = owner and login.owner() not in {"", owner}
                    note = _OTHER_OWNER if switched else _NOT_RENEWED
                    self._reader.tell(note, note)

        def repeat(step: Callable[[], None], seconds: float) -> None:
            while self._scan.running:
                step()
                time.sleep(seconds)

        for each in ((lay, _STORE_CHECK_SECONDS), (renew, _LOGIN_CHECK_SECONDS)):
            threading.Thread(target=repeat, args=each, daemon=True).start()

    def stop(self) -> None:
        """End the session if it still runs, and wait until the scan has its result."""
        if self._scan.running:
            self._stopped = True
            self._end(0)
            # Where claude is a .cmd or .bat file, the end reaches cmd.exe alone: close its input.
            self._close_input()
            if self._thread and self._thread.is_alive():
                self._thread.join(_EXIT_SECONDS)
        # A process that left the group can hold its output open, and nothing would end the wait.
        if self._scan.running:
            self._scan.finish(Result(State.FAILED, STOPPED))

    def _send(self, row: JsonMap) -> None:
        with self._sending, suppress(OSError, ValueError):
            self._stdin.write(json.dumps(row).encode() + b"\n")
            self._stdin.flush()

    def _follow(self) -> None:
        try:
            for line in self._stdout:
                self._take(line)
                # A process that left the group can hold its output open after the last result.
                if self._answered or self._unfit:
                    break
            self._end(0 if self._unfit else _EXIT_SECONDS)
            self._finish()
        except Exception as error:
            self._end(0)
            self._scan.finish(Result(State.FAILED, _shown(f"{type(error).__name__}: {error}")))

    def _take(self, line: bytes) -> None:
        try:
            row = strictjson.loads(line.decode("utf-8", "replace"))
        except ValueError:
            return
        if not is_map(row):
            return
        self._heard = True
        if row.get("type") == "control_request":
            answer: JsonMap = {"subtype": "success", "request_id": row.get("request_id")}
            self._send({"type": "control_response", "response": {**answer, "response": {}}})
        try:
            self._reader.row(row)
        # A row that cannot be read must not end the scan.
        except Exception as error:
            said = f"Some progress could not be shown ({type(error).__name__}). The scan goes on."
            self._reader.tell("unread", said)
        if row.get("type") == "result" and not self._reader.busy:
            self._answered = True
            self._close_input()

    def _close_input(self) -> None:
        # A write can wait for a process that left the group, and it holds the lock meanwhile.
        if self._sending.acquire(timeout=_GRACE_SECONDS):
            with suppress(OSError, ValueError):
                self._stdin.close()
            self._sending.release()

    def _end(self, patience: float) -> None:
        with suppress(subprocess.TimeoutExpired):
            self._job.wait(patience)
        for force in (False, True):
            with suppress(OSError):
                if sys.platform == "win32":
                    self._job.kill()
                elif self._scan.target.sandboxed:
                    # The sandbox ends all that runs inside it, also when it is killed.
                    self._job.send_signal(signal.SIGKILL if force else signal.SIGTERM)
                else:
                    os.killpg(self._job.pid, signal.SIGKILL if force else signal.SIGTERM)
            with suppress(subprocess.TimeoutExpired):
                self._job.wait(_GRACE_SECONDS)

    def _finish(self) -> None:
        if self._unfit:
            self._close_input()
            self.refused = True
            self._scan.finish(Result(State.FAILED, _shown(self._unfit)))
            return
        # A sandbox that broke, or was killed during its copy, can leave a part of a report.
        code = self._job.poll()
        broke = self._scan.target.sandboxed and (code is None or code < 0 or code == BROKEN)
        self.refused = not (self._heard or self._stopped)
        whole = self._answered and not self._reader.failed and not broke
        said = _shown(self._closing(whole))
        if self.refused and self._scan.target.sandboxed and not broke:
            names = ", ".join(sandbox.refusing_settings())
            said += f"\n{_MANAGED_CAUSE.format(names)}" if names else ""
        if self._reader.left_auto:
            said = _above(_LEFT_AUTO, said)
        written = report.finished(self._reports, self._earlier)
        if written is None:
            if whole and self._reader.nothing_to_scan:
                self._scan.finish(Result(State.SKIPPED, said))
            else:
                told = _NO_REPORT if whole else ""
                self._scan.finish(Result(State.FAILED, _above(told, said)))
            return
        if not whole:
            said += f"\n{_UNFINISHED}"
        try:
            delivered = report.deliver(written, self._into)
        except OSError as error:
            kept = report.set_aside(written, self._reports.parent)
            told = (
                f"The report could not be written in {self._into}: {error}\n"
                f"It lies here, as the session left it:\n{kept}"
            )
            self._scan.finish(Result(State.FAILED, _above(told, said), str(kept)))
            return
        files = sorted(p.name for p in delivered.iterdir() if p.name != ".gitignore")
        result = Result(State.FAILED, said, str(delivered), files)
        if not whole:
            self._scan.finish(result)
            return
        try:
            stamp = products.Stamp.read(delivered)
            findings = report.findings(delivered, self._scan.atlas, texts=self._reader.redacted)
        except (OSError, ValueError, products.ProductError) as error:
            # The error's own words can hold text that the scan wrote, which no agent redacted.
            result.message = _above(f"The report could not be read: {type(error).__name__}", said)
            self._scan.finish(result)
            return
        if stamp.empty:
            result.state = State.SKIPPED
        else:
            missing = report.missing(stamp, len(findings))
            result.state = State.FAILED if missing or self._reader.left_auto else State.DONE
            result.message, result.verification = _above(missing, said), stamp.status.value
        self._scan.finish(result, findings)

    @property
    def _unfit(self) -> str:
        """Why the session cannot scan, while no workflow or agent has started; else nothing."""
        if self._reader.underway:
            return ""
        if self._reader.unloaded and self._scan.target.sandboxed:
            return "\n".join((_NO_PLUGIN, *self._reader.load_errors))
        return _NO_AUTO if self._reader.left_auto else ""

    def _closing(self, whole: bool) -> str:
        """The session's last words, or why it ended without them."""
        if whole:
            return _plain(self._reader.last_words)
        if self._stopped:
            return STOPPED
        self._listener.join(_GRACE_SECONDS)
        errors = sandbox.holds(b"".join(self._errors).decode("utf-8", "replace"))
        # Words from before the session died say nothing of why it did.
        words = self._reader.last_words if self._reader.failed else ""
        # The relay gives the reason for a refused sign-in on stderr alone.
        told = f"{words}\n{sandbox.own_lines(errors)}" if words else errors
        said = told.strip() or "Claude Code ended before the scan did."
        return f"{said}\n{_REFUSED}" if _EXPIRED.search(said) else said


def _plain(words: str) -> str:
    """The session's closing `words`, less the marks of code and bold text and the offers."""
    lines = _BOLD.sub(r"\1", _CODE.sub(r"\1", words)).splitlines()
    return "\n".join(line for line in lines if not _OFFER.match(line))


def _shown(message: str) -> str:
    """`message` with its lines kept, and what does not print written out."""
    lines = display.capped(strictjson.well_formed(message).strip(), _MESSAGE_CHARS).splitlines()
    return "\n".join(map(display.written_out, lines))


def _above(told: str, said: str) -> str:
    """The command's words `told`, on lines above the words `said` that are already shown."""
    return f"{_shown(told)}\n{said}".strip()
