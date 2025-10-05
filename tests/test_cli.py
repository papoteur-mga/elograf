from __future__ import annotations

import argparse

from eloGraf.cli import choose_ipc_command, handle_model_commands
from eloGraf.settings import Settings


class FakeSettings(Settings):
    def __init__(self, models=None, current_name=None):
        super().__init__()
        self.models = models or []
        self._current = current_name

    def load(self):
        pass

    def contains(self, key: str) -> bool:  # noqa: N802
        if key == "Model/name" and self._current is not None:
            return True
        return super().contains(key)

    def value(self, key: str, default=None, type=None):  # noqa: N802
        if key == "Model/name" and self._current is not None:
            return self._current
        return super().value(key, default, type=type)


class DummyArgs(argparse.Namespace):
    def __init__(self, **kwargs):
        defaults = dict(list_models=False, set_model=None, exit=False, end=False, begin=False, resume=False, suspend=False)
        defaults.update(kwargs)
        super().__init__(**defaults)


def test_handle_model_commands_list_empty(tmp_path):
    settings = FakeSettings()
    result = handle_model_commands(DummyArgs(list_models=True, set_model=None), settings)
    assert result is not None and "No models configured" in result.stdout


def test_handle_model_commands_set_model_success(tmp_path):
    settings = FakeSettings(models=[
        {"name": "demo", "language": "en", "version": "1", "size": "1", "type": "custom", "location": "/tmp"}
    ])
    result = handle_model_commands(DummyArgs(list_models=False, set_model="demo"), settings)
    assert result is not None and result.code == 0


def test_handle_model_commands_set_model_failure(tmp_path):
    settings = FakeSettings(models=[
        {"name": "demo", "language": "en", "version": "1", "size": "1", "type": "custom", "location": "/tmp"}
    ])
    result = handle_model_commands(DummyArgs(list_models=False, set_model="missing"), settings)
    assert result is not None and result.code == 1 and "missing" in result.stderr


def test_choose_ipc_command_priority():
    assert choose_ipc_command(DummyArgs(exit=True, end=False, begin=False, resume=False, suspend=False)) == "exit"
    assert choose_ipc_command(DummyArgs(exit=False, end=True, begin=False, resume=False, suspend=False)) == "end"
    assert choose_ipc_command(DummyArgs(exit=False, end=False, begin=True, resume=False, suspend=False)) == "begin"
    assert choose_ipc_command(DummyArgs(exit=False, end=False, begin=False, resume=True, suspend=False)) == "resume"
    assert choose_ipc_command(DummyArgs(exit=False, end=False, begin=False, resume=False, suspend=True)) == "suspend"
