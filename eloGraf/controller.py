from __future__ import annotations

from typing import Callable, Optional, Sequence, Dict

from eloGraf.dictation import CommandBuildError, build_dictation_command
from eloGraf.state_machine import DictationStateMachine
from eloGraf.nerd_controller import NerdDictationProcessRunner, NerdDictationController, NerdDictationState

CommandHandler = Callable[[], None]


class DictationController:
    def __init__(
        self,
        settings,
        runner: NerdDictationProcessRunner,
        state_machine: DictationStateMachine,
        *,
        on_begin_command: Callable[[Sequence[str], Dict[str, str]], bool],
        on_model_request: Callable[[], bool],
    ) -> None:
        self.settings = settings
        self.runner = runner
        self.state_machine = state_machine
        self.on_begin_command = on_begin_command
        self.on_model_request = on_model_request

    def handle_state(self, state: NerdDictationState) -> None:
        if state in {NerdDictationState.STARTING, NerdDictationState.LOADING}:
            self.state_machine.set_loading()
        elif state in {NerdDictationState.READY, NerdDictationState.DICTATING}:
            self.state_machine.set_ready()
        elif state == NerdDictationState.SUSPENDED:
            self.state_machine.set_suspended()
        else:
            self.state_machine.set_idle()

    def begin(self) -> None:
        model, location = self._ensure_model()
        if not location:
            return
        if self.settings.precommand:
            parts = self.settings.precommand.split()
            if parts:
                self.on_begin_command(parts, {})
        try:
            cmd, env = build_dictation_command(self.settings, location)
        except CommandBuildError as exc:
            self.state_machine.fail(str(exc))
            return
        if self.on_begin_command(cmd, env):
            self.state_machine.set_loading()
        else:
            self.state_machine.set_idle()

    def end(self) -> None:
        self.runner.stop()
        self.state_machine.set_idle()

    def suspend(self) -> None:
        if self.runner.is_running():
            self.runner.suspend()
            self.state_machine.set_suspended()

    def resume(self) -> None:
        if self.runner.is_running():
            self.runner.resume()
            self.state_machine.set_ready()
        else:
            # No running process: behave like begin
            self.begin()

    def toggle(self) -> None:
        action = self.state_machine.toggle()
        getattr(self, action)()

    def _ensure_model(self):
        model, location = self.settings.current_model()
        if model and location:
            return model, location
        if self.on_model_request():
            return self.settings.current_model()
        self.state_machine.fail("No model selected")
        return "", ""
