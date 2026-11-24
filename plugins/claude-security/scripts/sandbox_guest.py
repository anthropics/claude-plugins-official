#!/usr/bin/env python3
"""The supervisor's part inside a virtual machine. `sandbox.py --image` starts it, as root.

It starts the keeper, and carries the keeper's streams, calls and files over stdin and stdout.
It holds no credential.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from contextlib import suppress
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn, cast

# Under runpy, which starts this program, Python leaves its folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sandbox.keeper import Door, Keeper
from lib.sandbox.plan import BROKEN, MOST_CALLS, SandboxError, parsed_plan
from lib.sandbox.tunnel import CHUNK, FIRST_CALL, REPORT, STDERR, STDIN, STDOUT, Tunnel

if TYPE_CHECKING:
    import socket
    from io import BufferedReader

_FRAMES = {"exit": b"x", "note": b"n", "removed": b"r"}


def _answer(door: socket.socket, tunnel: Tunnel) -> None:
    try:
        for lane in count(FIRST_CALL):
            # A call that waits for the relay would hold up the one stream.
            while len(tunnel.open_calls()) >= MOST_CALLS:
                time.sleep(0.05)
            tunnel.join(lane, door.accept()[0])
    except EOFError:
        return
    except (OSError, RuntimeError, MemoryError) as error:
        with suppress(OSError):
            tunnel.send(b"e", data=f"the machine cannot take calls: {error}".encode())


def _serve(tunnel: Tunnel) -> int:
    frames = tunnel.frames()
    if not (first := next(frames, None)) or first.kind != b"p":
        msg = "the host sent no plan"
        raise SandboxError(msg)
    keeper = Keeper(parsed_plan(first.data.decode()), sudo=False)

    def listen() -> None:
        try:
            with suppress(SandboxError):
                for _ in frames:
                    pass
        finally:
            keeper.stop()

    relay = -1
    outputs: list[threading.Thread] = []
    threading.Thread(target=listen, daemon=True).start()
    for kind, text, files in keeper.messages():
        if kind == "relay":
            relay = files[0]
        elif kind == "streams":
            tunnel.deliver_to(STDIN, os.fdopen(files[0], "wb"))
            tunnel.send(b"s")
            door = Door(fileno=relay)
            threading.Thread(target=_answer, args=(door, tunnel), daemon=True).start()
            outputs = [
                tunnel.carry(lane, os.fdopen(file, "rb", buffering=0))
                for lane, file in ((STDOUT, files[1]), (STDERR, files[2]))
            ]
        elif kind == "file":
            tunnel.send(b"f", data=os.fsencode(text))
            with os.fdopen(files[0], "rb") as report:
                while data := report.read(CHUNK):
                    tunnel.send(b"d", REPORT, data)
            tunnel.send(b"d", REPORT)
        else:
            tunnel.send(_FRAMES.get(kind, b"e"), data=os.fsencode(text))
    for output in outputs:
        output.join()
    return keeper.wait()


def _pass_zeros(source: BufferedReader) -> None:
    while source.peek(1)[:1] == b"\0":
        source.read(1)


def main() -> NoReturn:
    _pass_zeros(cast("BufferedReader", sys.stdin.buffer))
    tunnel = Tunnel(sys.stdin.buffer, sys.stdout.buffer, guest=True)
    try:
        code = _serve(tunnel)
    except (OSError, SandboxError) as error:
        tunnel.send(b"e", data=str(error).encode())
        code = BROKEN
    # A normal exit fails while a daemon thread is blocked in stdin.
    tunnel.exit(code)


if __name__ == "__main__":
    main()
