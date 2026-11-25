#!/usr/bin/env python3
"""Try the sandbox's files, network and processes from inside. `sandbox.py --check` starts this
program. It does not try the caps on memory and time, and it cannot look for the credential.

Usage:
  sandbox_walls.py <the user's home folder>

Prints one line for each try. Exits 0 if all hold, 1 if one does not, and 2 on a host not named
claude-security-sandbox, where it tries nothing.
Python 3.9-compatible, stdlib only. Linux only.
"""

from __future__ import annotations

import ctypes
import os
import socket
import sys
from http import HTTPStatus
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from typing import TYPE_CHECKING, cast

# Under -I, which starts this program, Python leaves its folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.sandbox import kernel
from lib.sandbox.plan import HOST_NAME, RELAY

if TYPE_CHECKING:
    from collections.abc import Callable

_DOCUMENTATION_HOST = ("192.0.2.1", 443)
_METADATA_HOST = ("169.254.169.254", 80)
# Not every build of Python names these two.
_AF_ALG, _AF_VSOCK = 38, 40


def _refused(attempt: Callable[[], object]) -> bool:
    try:
        attempt()
    except OSError as error:
        # A call that only ran out of time had a way to go.
        return not isinstance(error, socket.timeout)
    return False


def _hidden(folder: Path) -> bool:
    """Whether `folder` shows nothing but the way to what is mounted below it."""
    mounts = [*map(Path, kernel.mount_points())]
    entries = folder.iterdir() if folder.is_dir() else ()
    return all(any(mount.is_relative_to(entry) for mount in mounts) for entry in entries)


def _relay_refuses(method: str, path: str) -> bool:
    connection = HTTPConnection(*RELAY, timeout=10)
    try:
        connection.request(method, path, body="{}")
        return connection.getresponse().status == HTTPStatus.BAD_REQUEST
    except (OSError, HTTPException):
        return False


def _child_is_cut_off() -> bool:
    if not (child := os.fork()):
        cut_off = False
        try:
            with socket.create_connection(RELAY, timeout=10) as call:
                cut_off = not call.recv(1)
        finally:
            os._exit(not cut_off)
    return os.waitpid(child, 0)[1] == 0


def _traces() -> None:
    trace_me = 0
    if cast("int", ctypes.CDLL(None).ptrace(trace_me, 0, None, None)) < 0:
        raise PermissionError


def main() -> int:
    if socket.gethostname() != HOST_NAME:
        sys.stderr.write(
            "sandbox_walls: this runs only inside the sandbox; start it with sandbox.py --check\n"
        )
        return 2
    home = Path(sys.argv[1])
    writes = ("/", "/usr", "/etc", "/dev")
    walls = {
        "the home folder is hidden": _hidden(home),
        "the host's folders are hidden": all(
            _hidden(Path("/", name)) for name in ("root", "run", "sys", "var", "mnt", "opt")
        ),
        "system folders are read-only": all(
            _refused(Path(folder, "probe").touch) for folder in writes
        )
        and bool(os.statvfs("/proc").f_flag & os.ST_RDONLY),
        "process 1 is closed": _refused(Path("/proc/1/environ").read_bytes),
        "loopback is the only device": kernel.devices_up() == ["lo"],
        "no host can be reached": all(
            _refused(lambda host=host: socket.create_connection(host, timeout=3))
            for host in (_DOCUMENTATION_HOST, _METADATA_HOST)
        ),
        "no name resolves": _refused(lambda: socket.getaddrinfo("example.com", 443)),
        "other socket families are refused": all(
            _refused(lambda kind=kind: socket.socket(*kind))
            for kind in ((_AF_ALG, socket.SOCK_SEQPACKET), (_AF_VSOCK, socket.SOCK_STREAM))
        ),
        "no new namespace": _refused(lambda: kernel.unshare(kernel.Namespace.USER)),
        "no mount": _refused(lambda: kernel.mount("tmpfs", "/tmp", kernel.Mount(0))),  # noqa: S108
        "no tracing": _refused(_traces),
        "no way to root": _refused(lambda: os.setuid(0)),
        "no terminal": _refused(lambda: os.open("/dev/tty", os.O_RDWR)),
        "the command's mem file and streams are closed": all(
            _refused(lambda part=part: os.open(f"/proc/self/{part}", os.O_WRONLY))
            for part in ("mem", "fd/0", "fd/1", "fd/2")
        ),
        "only the command reaches the relay": _child_is_cut_off(),
        "the relay passes model requests alone": all(
            _relay_refuses(method, path)
            for method in ("GET", "POST", "CONNECT")
            for path in ("/v1/models", "/v1/files", "example.com:443")
        ),
    }
    for wall, holds in walls.items():
        print("holds " if holds else "FAILED", wall)
    return 0 if all(walls.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
