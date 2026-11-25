"""The command's options for the views, and the views that they ask for."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, Callable

from lib.live import plain

from . import tui

if TYPE_CHECKING:
    from contextlib import ExitStack

    from lib.live.scan import Scan


class _Options(argparse.Namespace):
    tui: bool = False
    nerd_fonts: bool = False
    light: bool | None = None


def add_options(parser: argparse.ArgumentParser) -> None:
    show = parser.add_argument_group("how to watch it")
    show.add_argument(
        "--tui",
        action="store_true",
        help="show the scan in this terminal; CLAUDE_SECURITY_REDUCED_MOTION=1 shows less motion",
    )
    show.add_argument("--nerd-fonts", action="store_true", help="use a Nerd Font's icons in --tui")
    theme = show.add_mutually_exclusive_group()
    theme.add_argument(
        "--light",
        action="store_true",
        default=None,
        help="use colors for a light background in --tui (default: dark, or as COLORFGBG says)",
    )
    theme.add_argument(
        "--dark",
        action="store_false",
        default=None,
        dest="light",
        help="use colors for a dark background in --tui",
    )


def watcher(args: argparse.Namespace, stack: ExitStack) -> Callable[[Scan], None]:
    """What shows a scan until it ends or the user leaves."""
    options = _Options(**vars(args))

    def watch(scan: Scan) -> None:
        url = ""
        if options.tui and sys.stdin.isatty() and sys.stdout.isatty():
            tui.run(scan, url, nerd_fonts=options.nerd_fonts, light=options.light)
            return
        plain.run(scan)

    return watch
