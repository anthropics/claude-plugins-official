"""The chain a vote record carries: which verification run wrote it, and what it left pending."""

from __future__ import annotations

from typing import TypedDict

from .strictjson import JsonMap, is_int, is_list, is_map


class Chain(TypedDict):
    """A scan's position after a run: the run, the next free report id, the ranks pending."""

    shard: int
    next_id: int
    pending: list[list[int]]
    retry: list[int]


def _positive(raw: JsonMap, key: str) -> int:
    """A field holding an integer from 1."""
    value = raw.get(key)
    if not is_int(value) or value < 1:
        msg = f"field {key!r} is not a positive integer"
        raise ValueError(msg)
    return value


def _ranks(raw: object, key: str) -> list[int]:
    """A field holding a list of ranks (integers from 1)."""
    if is_list(raw):
        ranks = [n for n in raw if is_int(n) and n >= 1]
        if len(ranks) == len(raw):
            return ranks
    msg = f"field {key!r} is not a list of ranks"
    raise ValueError(msg)


def _span(raw: object) -> list[int]:
    """One `[from, to]` entry of `pending`."""
    span = _ranks(raw, "pending")
    if len(span) != 2 or span[0] > span[1]:
        msg = "field 'pending' is not a list of [from, to] rank ranges"
        raise ValueError(msg)
    return span


def chain_of(raw: object) -> Chain:
    """The chain `raw` spells; ValueError naming the field when it is not one."""
    if not is_map(raw):
        msg = "is not an object"
        raise ValueError(msg)
    pending = raw.get("pending")
    if not is_list(pending):
        msg = "field 'pending' is not a list of [from, to] rank ranges"
        raise ValueError(msg)
    return {
        "shard": _positive(raw, "shard"),
        "next_id": _positive(raw, "next_id"),
        "pending": [_span(entry) for entry in pending],
        "retry": _ranks(raw.get("retry"), "retry"),
    }


def pending_ranks(chain: Chain) -> list[int]:
    """Every rank the chain leaves to the next run, ascending."""
    spanned = {n for start, end in chain["pending"] for n in range(start, end + 1)}
    return sorted(spanned | set(chain["retry"]))
