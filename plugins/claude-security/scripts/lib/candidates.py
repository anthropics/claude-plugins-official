"""The candidate files that a run of the scan workflow loads from the run directory."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from . import plugin, strictjson
from .strictjson import is_int, is_map, is_str

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from pathlib import Path

    from .strictjson import JsonMap

# The most rows in a candidate file: one agent gives a file back in one answer, which has a limit.
CHUNK = 10


def candidate_file(shard: int, number: int) -> str:
    """The name of run `shard`'s candidate file `number`; workflows/scan.js asks for the same."""
    return f"candidates.{shard}.{number}.json"


def candidate_files(
    run_dir: Path, shard: int, rows: Sequence[JsonMap]
) -> Iterator[tuple[str, JsonMap]]:
    """Run `shard`'s candidate files, each as its name and its content: `rows` in their order,
    CHUNK to a file."""
    for number, start in enumerate(range(0, len(rows), CHUNK), start=1):
        yield (
            candidate_file(shard, number),
            {
                "runDir": str(run_dir),
                "shard": shard,
                "chunk": number,
                "candidates": rows[start : start + CHUNK],
            },
        )


class LastReport(TypedDict):
    """The last report: its directory's name, how many findings it has, and how many of them were
    written as the first run's candidate rows."""

    report: str
    findings: int
    held: int


def taken_from(run_dir: Path) -> LastReport | None:
    """What lib/last_report.py wrote of the last report; None if it wrote none. OSError or
    ValueError if the file cannot be read."""
    try:
        taken = strictjson.load(run_dir / plugin.LAST_REPORT_NAME)
    except FileNotFoundError:
        return None
    except ValueError as error:
        msg = f"{plugin.LAST_REPORT_NAME} is not valid JSON: {error}"
        raise ValueError(msg) from error
    if (
        is_map(taken)
        and is_str(report := taken.get("report"))
        and is_int(findings := taken.get("findings"))
        and is_int(held := taken.get("held"))
    ):
        return LastReport(report=report, findings=findings, held=held)
    msg = f"{plugin.LAST_REPORT_NAME} is not what write_scan_meta.py writes"
    raise ValueError(msg)
