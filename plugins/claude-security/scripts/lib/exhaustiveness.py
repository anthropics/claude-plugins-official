"""Closing a chain of tests over an enum or a Literal, so the type checker reports a value left
out."""

from __future__ import annotations

from typing import NoReturn


def unreachable(value: NoReturn) -> NoReturn:
    """Refuse a value the type checker has proven cannot occur."""
    raise AssertionError(value)
