"""Runs a view of a scan in a Node process of its own."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from contextlib import suppress
from pathlib import Path
from typing import IO, TYPE_CHECKING, cast

from lib import plugin

from . import wire

if TYPE_CHECKING:
    from lib.live.scan import Scan

_VIEWS = plugin.ROOT / "scripts/views"
_LENGTH_BYTES = 4
# A first start of Node on a busy Windows machine can take longer than any later answer.
_START_SECONDS = 60
_ANSWER_SECONDS = 10
# The option of Node's permission model in Node.js 22.13 and later, and in 20 to 22.12. It limits
# the view's file calls to reads in its own folder, and refuses child processes.
_PERMISSION = ("--permission", "--experimental-permission")
# Node's exit code for an option that it does not know.
_UNKNOWN_OPTION = 9
# What Windows, and a version manager's stand-in for node, need to start it.
_KEPT = {
    *("PATH", "PATHEXT", "HOME", "USERPROFILE", "SYSTEMROOT", "LOCALAPPDATA", "XDG_DATA_HOME"),
    *("VOLTA_HOME", "ASDF_DIR", "ASDF_DATA_DIR", "MISE_DATA_DIR", "NODENV_ROOT"),
}


class RendererError(Exception):
    """The view cannot be drawn."""


class Renderer:
    """The view of `scan` that Node draws when it is given these files of the views' folder. Raises
    RendererError where it cannot start."""

    def __init__(self, scan: Scan, entry: str, *rest: str) -> None:
        name = "node.exe" if os.name == "nt" else "node"
        places = (Path(folder, name) for folder in os.get_exec_path() if os.path.isabs(folder))
        node = next((p for p in places if os.path.isfile(p) and os.access(p, os.X_OK)), None)
        if node is None:
            msg = "Node.js is not on PATH"
            raise RendererError(msg)
        self._process: subprocess.Popen[bytes] = _start(node, (entry, *rest))
        self._into: IO[bytes] = cast("IO[bytes]", self._process.stdin)
        self._out: IO[bytes] = cast("IO[bytes]", self._process.stdout)
        self._scan: Scan = scan
        self._since: int = 0
        self._lock: threading.RLock = threading.RLock()
        self._due: float | None = None
        threading.Thread(target=self._watch, daemon=True).start()
        try:
            self.ask(b"A" + wire.atlas(scan.atlas), first=True)
        except RendererError:
            self.close()
            raise

    def ask(self, message: bytes, *, first: bool = False) -> bytes:
        """The view's answer to a message. The first can take longer. Raises RendererError where
        the view stops or is late."""
        with self._lock:
            self._due = time.monotonic() + (_START_SECONDS if first else _ANSWER_SECONDS)
            try:
                self._into.write(len(message).to_bytes(_LENGTH_BYTES, "little") + message)
                self._into.flush()
                return self._take(int.from_bytes(self._take(_LENGTH_BYTES), "little"))
            except (OSError, ValueError, MemoryError) as error:
                with suppress(OSError):
                    self._into.close()
                msg = "the view stopped"
                raise RendererError(msg) from error
            finally:
                self._due = None

    def show(self, message: bytes) -> bytes:
        """The answer to a message, after the view has learned what changed in the scan."""
        with self._lock:
            with self._scan.changed:
                delta, self._since = wire.delta(self._scan, self._since), self._scan.rev
            self.ask(b"D" + delta.encode())
            return self.ask(message)

    def _take(self, size: int) -> bytes:
        taken = self._out.read(size)
        if len(taken) < size:
            raise BrokenPipeError
        return taken

    def _watch(self) -> None:
        while self._process.poll() is None:
            time.sleep(1)
            due = self._due
            if due is not None and time.monotonic() > due:
                self.close()

    def close(self) -> None:
        """End the view's process."""
        if os.name == "nt":
            self._process.kill()
        elif self._process.poll() is None:
            # A stand-in for node can have a child that holds the pipes open.
            with suppress(OSError):
                os.killpg(self._process.pid, signal.SIGKILL)


def _knows(node: Path, option: str, env: dict[str, str]) -> bool:
    tried = subprocess.run(
        [node, option, "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=_VIEWS.anchor,
        env=env,
        timeout=_START_SECONDS,
        check=False,
    )
    if tried.returncode != _UNKNOWN_OPTION:
        tried.check_returncode()
    return tried.returncode == 0


def _start(node: Path, files: tuple[str, ...]) -> subprocess.Popen[bytes]:
    paths = [(_VIEWS / name).resolve() for name in files]
    if "*" in str(paths[0]):
        # Node reads a star in the path of a grant as a pattern, which matches other folders too.
        msg = "the plugin's path holds a *"
        raise RendererError(msg)
    env = {name: os.environ[name] for name in _KEPT & os.environ.keys()}
    try:
        option = next((option for option in _PERMISSION if _knows(node, option, env)), None)
        if option is None and paths[-1].suffix == ".mjs":
            print(
                "This Node.js cannot limit the view's access. Use 22.13 or newer.", file=sys.stderr
            )
        fence = [option, f"--allow-fs-read={paths[0].with_name('*')}"] if option else []
        return subprocess.Popen(
            [node, *fence, "--disallow-code-generation-from-strings", *paths],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=_VIEWS.anchor,
            env=env,
            start_new_session=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        msg = f"{node} does not start"
        raise RendererError(msg) from error
