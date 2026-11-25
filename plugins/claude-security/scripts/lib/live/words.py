"""Plain names for the agents of a scan."""

from __future__ import annotations

import re
from typing import Protocol

_ROLES = {
    "inventory": "Inventory",
    "history": "History",
    "context": "Context",
    "research": "Research",
    "boundary": "Trust boundary",
    "sweep": "Sweep",
    "past-fixes": "Past fixes",
    "pack": "Close reading",
    "half": "Close reading",
    "gap": "Close reading",
    "lead": "Lead",
    "duplicates": "Duplicates",
    "load": "Load",
    "root-flaws": "Root flaws",
    "redactor": "Redaction",
}


class _Agent(Protocol):
    label: str
    role: str
    component: str
    lens: str


def _lens(name: str) -> str:
    """The first word of a lens: "injection-and-input" reads "Injection"."""
    return name.partition("-")[0].capitalize()


def agent(who: _Agent) -> str:
    """An agent's name, as in "Injection · bookings". An unknown role gives its label."""
    narrow = who.role in {"research", "panel"} and who.lens not in {"", "all"}
    what = _lens(who.lens) if narrow else _ROLES.get(who.role, "")
    where = who.component or re.sub(r"\A([a-z-]+):(\d+)\Z", r"\1 \2", who.label.partition(":")[2])
    return " · ".join(filter(None, (what, where))) if what else who.label
