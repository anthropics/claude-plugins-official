"""Plugin Lifecycle: the states a discovered plugin moves through as the
Loader processes it, and the only transitions allowed between them.

    DISCOVERED -> MANIFEST_LOADED -> VALIDATED -> REGISTERED -> ACTIVE
         |               |               |            |          |
         v               v               v            v          v
      FAILED          FAILED          FAILED       FAILED    DISABLED

DISABLED is reachable from ACTIVE (an operator can disable a plugin after
it's running) as well as from any earlier state; both FAILED and DISABLED
are terminal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .errors import LifecycleError


class LifecycleState(str, Enum):
    DISCOVERED = "discovered"
    MANIFEST_LOADED = "manifest_loaded"
    VALIDATED = "validated"
    REGISTERED = "registered"
    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"


_ALLOWED_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.DISCOVERED: {
        LifecycleState.MANIFEST_LOADED, LifecycleState.FAILED, LifecycleState.DISABLED,
    },
    LifecycleState.MANIFEST_LOADED: {
        LifecycleState.VALIDATED, LifecycleState.FAILED, LifecycleState.DISABLED,
    },
    LifecycleState.VALIDATED: {
        LifecycleState.REGISTERED, LifecycleState.FAILED, LifecycleState.DISABLED,
    },
    LifecycleState.REGISTERED: {
        LifecycleState.ACTIVE, LifecycleState.FAILED, LifecycleState.DISABLED,
    },
    LifecycleState.ACTIVE: {LifecycleState.DISABLED, LifecycleState.FAILED},
    LifecycleState.FAILED: set(),
    LifecycleState.DISABLED: set(),
}


@dataclass
class LifecycleEvent:
    state: LifecycleState
    at: datetime
    note: str = ""


@dataclass
class PluginLifecycle:
    """Tracks one plugin's journey through the states above, in order."""

    plugin_name: str
    state: LifecycleState = LifecycleState.DISCOVERED
    history: list[LifecycleEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.history:
            self.history.append(LifecycleEvent(self.state, datetime.now(timezone.utc)))

    def transition(self, new_state: LifecycleState, note: str = "") -> None:
        allowed = _ALLOWED_TRANSITIONS[self.state]
        if new_state not in allowed:
            raise LifecycleError(
                f"{self.plugin_name}: illegal lifecycle transition "
                f"{self.state.value} -> {new_state.value}"
            )
        self.state = new_state
        self.history.append(LifecycleEvent(new_state, datetime.now(timezone.utc), note))

    @property
    def is_terminal_failure(self) -> bool:
        return self.state in (LifecycleState.FAILED, LifecycleState.DISABLED)
