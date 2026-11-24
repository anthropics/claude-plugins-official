"""The effort tiers of a scan, the values of Change Scan Effort, and the word that names each."""

from __future__ import annotations

import argparse
from enum import Enum

from . import plugin


class Effort(Enum):
    """An effort tier, as `--effort` spells it, lowest first."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


class ChangeScanEffort(Enum):
    """A value of Change Scan Effort, as `--change-scan-effort` spells it."""

    LOW = "low"
    HIGH = plugin.CHANGE_SCAN_EFFORT_HIGH


def tier(word: str) -> Effort:
    """The tier a word names, whatever its case or the spaces around it; any other is refused."""
    try:
        return Effort(word.strip().lower())
    except ValueError:
        offered = ", ".join(effort.value for effort in Effort if effort is not Effort.MAX)
        msg = (
            f"{word!r} is not an effort tier; the tiers are {offered}. "
            "Tell the user so and start no scan; do not choose a tier for them"
        )
        raise argparse.ArgumentTypeError(msg) from None
