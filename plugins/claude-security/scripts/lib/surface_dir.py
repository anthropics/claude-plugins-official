"""The output directory of an attack surface analysis: its name, which a change scan's report
directory takes too, where it must lie, and its stages' folders."""

from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING, Final

from . import plugin

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime
    from pathlib import Path

OUTPUT_FORM: Final = f"{plugin.REPORT_DIR_PREFIX}<timestamp>"
# \Z, not $: "$" also matches before a trailing newline, and this name decides what may be removed.
OUTPUT_RE: Final = re.compile(rf"{re.escape(plugin.REPORT_DIR_PREFIX)}[0-9]{{8}}-[0-9]{{6}}\Z")
WORK_DIR_NAME: Final = ".work"


def output_name(moment: datetime) -> str:
    """The name of a report directory for the second of `moment`."""
    return f"{plugin.REPORT_DIR_PREFIX}{moment:%Y%m%d-%H%M%S}"


def in_current_directory(out: Path) -> bool:
    """Whether the output directory `out` lies in the current directory, where `start` makes it."""
    return out.parent.samefile(".")


def paths_in(folder: Path) -> Iterable[Path]:
    """What `folder` holds, or nothing if there is nothing at that path. The call, or iterating over
    the result, raises OSError if the folder cannot be read, or if the path is not a folder."""
    return folder.iterdir() if folder.exists() or folder.is_symlink() else ()


class Stage(Enum):
    """One stage of the analysis. `covers` is what it looks for, in a user's words. `patch_folder`
    is the folder in the stage's directory that holds its patches, or None."""

    ONE = (
        1,
        "stage1-default-attack-surface-reduction",
        "default attack surface reduction",
        "unneeded default features",
        "gates",
    )
    TWO = (
        2,
        "stage2-early-reachability-audit",
        "early reachability audit",
        "code reachable before login",
        None,
    )
    THREE = (
        3,
        "stage3-config-interaction-audit",
        "configuration interaction audit",
        "risky combinations of settings",
        "fixes",
    )

    def __init__(
        self, number: int, folder: str, title: str, covers: str, patch_folder: str | None
    ) -> None:
        self.number = number
        self.folder = folder
        self.title = title
        self.covers = covers
        self.patch_folder = patch_folder

    @property
    def numbers(self) -> range:
        """The numbers of its findings' ids: 101 to 199 for stage 1."""
        return range(100 * self.number + 1, 100 * self.number + 100)

    @property
    def id_range(self) -> str:
        return f"F{self.numbers[0]} to F{self.numbers[-1]}"

    def holds(self, name: str) -> bool:
        """Whether a name is one of this stage's ids, such as F101 for stage 1."""
        return name in {f"F{number}" for number in self.numbers}
