"""Frames on a pair of byte streams, between a host and its virtual machine."""

from __future__ import annotations

import os
import socket
import struct
import threading
from contextlib import suppress
from typing import IO, TYPE_CHECKING, NamedTuple, NoReturn, cast

from .plan import LARGEST_MESSAGE, SandboxError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from io import RawIOBase

STDIN, STDOUT, STDERR, REPORT, FIRST_CALL = range(5)
CHUNK = 1 << 16
_PATIENCE = struct.pack("ll", 30, 0)
_HEAD = struct.Struct(">cII")
_BROKE = "the virtual machine's stream broke"


class Frame(NamedTuple):
    kind: bytes
    lane: int
    data: bytes


class Tunnel:
    def __init__(self, source: IO[bytes], target: IO[bytes], *, guest: bool = False) -> None:
        self._guest: bool = guest
        self._source: IO[bytes] = source
        self._target: IO[bytes] = target
        self._sending: threading.Lock = threading.Lock()
        self._taken: threading.Event = threading.Event()
        self._files: dict[int, IO[bytes]] = {}
        self._calls: dict[int, socket.socket] = {}

    def send(self, kind: bytes, lane: int = 0, data: bytes = b"") -> None:
        with self._sending:
            self._target.write(_HEAD.pack(kind, lane, len(data)) + data)
            self._target.flush()

    def exit(self, code: int) -> NoReturn:
        """End this process between two frames."""
        self._sending.acquire()
        os._exit(code)

    def frames(self) -> Iterator[Frame]:
        """The frames that the tunnel does not handle by itself."""
        while head := self._source.read(_HEAD.size):
            if len(head) < _HEAD.size:
                raise SandboxError(_BROKE)
            kind, lane, size = cast("tuple[bytes, int, int]", _HEAD.unpack(head))
            if size > LARGEST_MESSAGE or len(data := self._source.read(size)) < size:
                raise SandboxError(_BROKE)
            if kind == b"a":
                self._taken.set()
            elif kind in {b"d", b"k"} and lane >= FIRST_CALL:
                self._to_call(lane, data, socket.SHUT_WR if kind == b"d" else socket.SHUT_RDWR)
            elif kind == b"d" and lane == STDIN:
                # The command can leave its stdin unread, which must not hold up the other lanes.
                threading.Thread(target=self._to_file, args=(lane, data), daemon=True).start()
            elif kind == b"d" and lane != REPORT:
                self._to_file(lane, data)
            else:
                yield Frame(kind, lane, data)

    def _to_file(self, lane: int, data: bytes) -> None:
        with suppress(OSError, KeyError):
            if not data:
                self._files.pop(lane).close()
                return
            self._files[lane].write(data)
            self._files[lane].flush()
            if lane == STDIN:
                self.send(b"a")

    def _to_call(self, lane: int, data: bytes, end: int) -> None:
        if not (call := self._calls.get(lane)):
            return
        if not data:
            with suppress(OSError):
                call.shutdown(end)
            call.close()
            return
        try:
            call.sendall(data)
        except OSError:
            # The relay can answer before it has read the request, and that answer must still pass.
            self._to_call(lane, b"", socket.SHUT_RDWR if self._guest else socket.SHUT_WR)
            if self._guest:
                with suppress(OSError):
                    self.send(b"k", lane)

    def deliver_to(self, lane: int, target: IO[bytes]) -> None:
        """What comes on `lane` goes to `target`."""
        self._files[lane] = target

    def end_files(self) -> None:
        for lane in [*self._files]:
            self._to_file(lane, b"")

    def carry(self, lane: int, source: RawIOBase, last: bytes = b"d") -> threading.Thread:
        """What `source` gives goes out on `lane`, in the background."""

        def run() -> None:
            with suppress(OSError), source:
                # After a failed read, `last` still tells the other side that the lane has ended.
                with suppress(OSError):
                    while data := source.read(CHUNK):
                        self.send(b"d", lane, data)
                        if lane == STDIN:
                            self._taken.wait()
                            self._taken.clear()
                self.send(last, lane)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def open_calls(self) -> set[int]:
        return {lane for lane, call in self._calls.items() if call.fileno() >= 0}

    def join(self, lane: int, call: socket.socket) -> None:
        """Carry a connection both ways: in the guest to the caller, else to the relay, whose end
        ends the call. The socket closes when its file has closed too."""
        # A reader that stalls must not hold up the other lanes for good.
        call.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, _PATIENCE)
        self._calls = {kept: self._calls[kept] for kept in self.open_calls()} | {lane: call}
        if self._guest:
            self.send(b"c", lane)
        self.carry(lane, call.makefile("rb", buffering=0), b"d" if self._guest else b"k")
