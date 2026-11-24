"""How long a run took, from the start time that the run recorded."""

from __future__ import annotations

from datetime import datetime

from .strictjson import is_str


def elapsed_seconds(started_at: object, now: datetime) -> int | None:
    """Whole seconds from a run's recorded started_at to now, floored at 0.

    None when started_at is absent, unparseable or timezone-naive.
    """
    if not is_str(started_at):
        return None
    try:
        started = datetime.fromisoformat(started_at)
    except ValueError:
        return None
    return max(int((now - started).total_seconds()), 0) if started.tzinfo else None
