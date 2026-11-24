"""Landlock: a second wall round the files, which does not rest on the mounts."""

from __future__ import annotations

import os
import stat
import struct
from enum import IntFlag
from typing import TYPE_CHECKING

from .kernel import Call, syscall

if TYPE_CHECKING:
    from collections.abc import Mapping

_OLDEST = 2
TRUNCATE_SINCE = 3


class Access(IntFlag):
    EXECUTE = 1 << 0
    WRITE_FILE = 1 << 1
    READ_FILE = 1 << 2
    READ_DIR = 1 << 3
    MAKE_CHAR = 1 << 6
    MAKE_BLOCK = 1 << 11
    TRUNCATE = 1 << 14

    READ = EXECUTE | READ_FILE | READ_DIR
    DEVICE = READ_FILE | WRITE_FILE | TRUNCATE
    # Every right up to TRUNCATE but making devices, so reading and running too.
    WRITE = 0x7FFF & ~(MAKE_CHAR | MAKE_BLOCK)


_ON_A_FILE = Access.EXECUTE | Access.DEVICE
_RIGHTS = {2: 14, 3: 15, 4: 15}
_NEWEST_RIGHTS = 16
_SCOPES_SINCE = 6


def version() -> int:
    """The version of Landlock that this kernel offers; 0 for none."""
    ask_version = 1
    try:
        return syscall(Call.LANDLOCK_CREATE_RULESET, None, 0, ask_version)
    except OSError:
        return 0


def restrict(allowed: Mapping[str, Access]) -> None:
    """Hold this thread and what it starts to `allowed`: the access below each path. The caller
    has set no_new_privs, as kernel.drop_capabilities does."""
    have = version()
    if have < _OLDEST:
        found = f"this kernel has {have}" if have else "here it is off or missing"
        msg = f"Landlock version {_OLDEST} (Linux 5.19) or newer is needed; {found}"
        raise OSError(msg)
    handled = (1 << _RIGHTS.get(have, _NEWEST_RIGHTS)) - 1
    scopes = 0b11 if have >= _SCOPES_SINCE else 0
    attributes = struct.pack("3Q", handled, 0, scopes)
    ruleset = syscall(Call.LANDLOCK_CREATE_RULESET, attributes, len(attributes), 0)
    path_beneath = 1
    for path, access in allowed.items():
        place = os.open(path, os.O_PATH)
        fits = handled if stat.S_ISDIR(os.fstat(place).st_mode) else handled & _ON_A_FILE
        rule = struct.pack("=Qi", access & fits, place)
        syscall(Call.LANDLOCK_ADD_RULE, ruleset, path_beneath, rule, 0)
        os.close(place)
    syscall(Call.LANDLOCK_RESTRICT_SELF, ruleset, 0)
    os.close(ruleset)
