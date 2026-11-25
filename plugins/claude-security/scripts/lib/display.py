"""A text made fit to show: on one line, cut short, or with what does not print written out."""

from __future__ import annotations


def single_line(text: str) -> str:
    """`text` on one line: each run of white space is one space, and none is at either end."""
    return " ".join(text.split())


def capped(text: str, cap: int) -> str:
    """`text` trimmed to `cap` characters, the cut marked with how many were dropped."""
    return text if len(text) <= cap else f"{text[:cap]}...[+{len(text) - cap} chars]"


def counted(number: int, noun: str) -> str:
    """`number` and `noun`, with an s on the noun unless the number is 1."""
    return f"{number} {noun}{'' if number == 1 else 's'}"


def written_out(text: str) -> str:
    """`text` with each character that does not print, other than a tab, written as \\u{hex}."""
    if text.replace("\t", "").isprintable():
        return text
    return "".join(ch if ch.isprintable() or ch == "\t" else f"\\u{{{ord(ch):x}}}" for ch in text)
