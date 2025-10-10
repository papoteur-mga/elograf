from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class IconState(Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    SUSPENDED = "suspended"


@dataclass
class DictationState:
    dictating: bool = False
    suspended: bool = False
    icon_state: IconState = IconState.IDLE


class DictationStateMachine:
    def __init__(self) -> None:
        self.state = DictationState()
        self.on_state = lambda state: None
        self.on_warning: Callable[[str], None] = lambda message: None

    def set_loading(self) -> None:
        self.state.icon_state = IconState.LOADING
        self.state.dictating = True
        self.state.suspended = False
        self._emit()

    def set_ready(self) -> None:
        self.state.icon_state = IconState.READY
        self.state.dictating = True
        self.state.suspended = False
        self._emit()

    def set_dictating(self) -> None:
        self.set_ready()

    def set_suspended(self) -> None:
        self.state.icon_state = IconState.SUSPENDED
        self.state.dictating = True
        self.state.suspended = True
        self._emit()

    def set_idle(self) -> None:
        self.state.icon_state = IconState.IDLE
        self.state.dictating = False
        self.state.suspended = False
        self._emit()

    def fail(self, message: str) -> None:
        self.on_warning(message)
        self.set_idle()

    def toggle(self) -> str:
        if self.state.suspended:
            return "resume"
        if self.state.dictating:
            return "suspend"
        return "begin"

    def _emit(self) -> None:
        self.on_state(self.state)
