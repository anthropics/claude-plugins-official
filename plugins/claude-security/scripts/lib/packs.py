"""A target's files cut into pieces that one Read call holds, the pieces gathered into packs, and
the packs laid out in the run directory for workflows/scan.js."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypedDict

from . import source, strictjson

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

PACK_BYTES = 195_000
# One reader makes a Read call and gives an answer for each piece.
PACK_PIECES = 80
# What one Read call holds: the tool takes 25,000 tokens and 2,000 lines a call.
PIECE_BYTES = 40_000
PIECE_LINES = 1_500
# A NUL among the first characters marks a binary file, as in git's own test of 8,000 bytes.
BINARY_PROBE = 8_000
# Packs per packs.<n>.json; workflows/scan.js derives the chunk count from the same size.
INDEX_CHUNK = 100
# A larger file is data rather than code, and reading it whole could exhaust the set-up's memory.
FILE_BYTES = 2_000_000


class _Piece(NamedTuple):
    """Lines `first` to `last` of a file, counted from 1, and their bytes."""

    file: str
    first: int
    last: int
    size: int


class _Row(TypedDict):
    """One pack in packs.<k>.json: where it starts, its count of pieces, whether it has halves."""

    file: str
    line: int
    pieces: int
    halves: bool


class _Chunk(TypedDict):
    """One packs.<k>.json: its number, the count of all packs, its packs."""

    chunk: int
    total_packs: int
    packs: list[_Row]


def _text_of(scan_root: str, file: str) -> str | None:
    """The file's text. None where the packs leave the file out: its name is not printable, lies
    outside the Basic Multilingual Plane, holds a backslash or has a blank at an end, it is larger
    than FILE_BYTES, or it is unreadable, binary or blank."""
    if not file.isprintable() or any(ord(char) > 0xFFFF for char in file):
        return None
    if "\\" in file or file != file.strip():
        return None
    try:
        if Path(scan_root, file).stat().st_size > FILE_BYTES:
            return None
    except OSError:
        return None
    text = source.read(scan_root, file)
    return None if text is None or not text.strip() or "\0" in text[:BINARY_PROBE] else text


def _pieces_of(scan_root: str, file: str) -> list[_Piece]:
    """The file's pieces. Empty where the packs leave the file out (_text_of), or one of its lines
    is longer than a piece."""
    text = _text_of(scan_root, file)
    if text is None:
        return []
    sizes = [len(line.encode("utf-8", "surrogateescape")) + 1 for line in text.split("\n")]
    if max(sizes) > PIECE_BYTES:
        return []
    if text.endswith("\n"):
        sizes.pop()
    pieces: list[_Piece] = []
    first, held = 1, 0
    for number, size in enumerate(sizes, 1):
        if held + size > PIECE_BYTES or number - first >= PIECE_LINES:
            pieces.append(_Piece(file, first, number - 1, held))
            first, held = number, 0
        held += size
    return [*pieces, _Piece(file, first, len(sizes), held)]


def _cut(scan_root: str, files: Iterable[str]) -> Iterator[list[_Piece]]:
    """The pieces of `files`, in their order, in packs of at most PACK_BYTES and PACK_PIECES."""
    pack: list[_Piece] = []
    size = 0
    for piece in (piece for file in files for piece in _pieces_of(scan_root, file)):
        if pack and (size + piece.size > PACK_BYTES or len(pack) == PACK_PIECES):
            yield pack
            pack, size = [], 0
        pack.append(piece)
        size += piece.size
    if pack:
        yield pack


def _halves(pack: Sequence[_Piece]) -> tuple[Sequence[_Piece], Sequence[_Piece]] | None:
    """The pack in two parts. None where it is no larger than PIECE_BYTES."""
    if sum(piece.size for piece in pack) <= PIECE_BYTES:
        return None
    middle = len(pack) // 2
    return pack[:middle], pack[middle:]


def _sheet(pieces: Sequence[_Piece]) -> str:
    """What a reader of `pieces` is handed: one numbered line for each Read call."""
    lines = [
        f"{number}. {piece.file} offset {piece.first} limit {piece.last - piece.first + 1}"
        for number, piece in enumerate(pieces, 1)
    ]
    return "\n".join(["Pieces:", *lines, ""])


def write(run_dir: Path, scan_root: str, files: Iterable[str]) -> int:
    """Lay out the packs of `files`, taken in the order of their code points, and return their
    count: pack.<n>.md for each, pack.<n>a.md and pack.<n>b.md for its halves, and packs.<k>.json
    for where each pack starts, how many pieces it holds and whether it has halves."""
    rows: list[_Row] = []
    for number, pack in enumerate(_cut(scan_root, sorted(set(files))), 1):
        parts = _halves(pack)
        for letter, pieces in zip(("", "a", "b"), (pack, *(parts or ()))):
            (run_dir / f"pack.{number}{letter}.md").write_bytes(_sheet(pieces).encode())
        rows.append(
            _Row(file=pack[0].file, line=pack[0].first, pieces=len(pack), halves=bool(parts))
        )
    for number, start in enumerate(range(0, len(rows), INDEX_CHUNK), start=1):
        chunk = _Chunk(chunk=number, total_packs=len(rows), packs=rows[start : start + INDEX_CHUNK])
        (run_dir / f"packs.{number}.json").write_bytes(
            (strictjson.text(chunk, indent=1) + "\n").encode()
        )
    return len(rows)
