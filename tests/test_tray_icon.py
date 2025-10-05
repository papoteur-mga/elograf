from __future__ import annotations

import os

import pytest
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from eloGraf.tray_icon import SystemTrayIcon


class FakeSignal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback):
        self.callback = callback

    def emit(self, value):
        if self.callback:
            self.callback(value)


class FakeIPC:
    def __init__(self) -> None:
        self.command_received = FakeSignal()
        self.cleanup_called = False

    def start_server(self) -> bool:
        return True

    def send_command(self, command: str) -> bool:
        self.last_command = command
        return True

    def supports_global_shortcuts(self) -> bool:
        return False

    def register_global_shortcut(self, action: str, shortcut: str, callback) -> bool:
        return False

    def cleanup(self) -> None:
        self.cleanup_called = True


@pytest.fixture(scope="module")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


@pytest.fixture
def tray(qt_app):
    ipc = FakeIPC()
    icon = QIcon()
    tray = SystemTrayIcon(icon, False, ipc)
    yield tray, ipc


def test_begin_sets_dictating(tray, monkeypatch):
    tray_icon, _ = tray
    monkeypatch.setattr(tray_icon.dictation_runner, "start", lambda *args, **kwargs: True)
    monkeypatch.setattr(tray_icon, "currentModel", lambda: ("dummy", "/tmp/dummy"))
    tray_icon.begin()
    assert tray_icon.dictating is True


def test_ipc_command_routes_to_actions(tray, monkeypatch):
    tray_icon, ipc = tray
    calls = []
    monkeypatch.setattr(tray_icon, "begin", lambda: calls.append("begin"))
    monkeypatch.setattr(tray_icon, "end", lambda: calls.append("end"))
    monkeypatch.setattr(tray_icon, "exit", lambda: calls.append("exit"))
    monkeypatch.setattr(tray_icon, "suspend", lambda: calls.append("suspend"))
    monkeypatch.setattr(tray_icon, "resume", lambda: calls.append("resume"))

    for command in ["begin", "end", "suspend", "resume", "exit"]:
        ipc.command_received.emit(command)

    assert calls == ["begin", "end", "suspend", "resume", "exit"]


def test_suspend_and_resume_toggle(tray, monkeypatch):
    tray_icon, _ = tray
    tray_icon.dictating = True
    monkeypatch.setattr(tray_icon.dictation_runner, "is_running", lambda: True)
    calls = []
    monkeypatch.setattr(tray_icon.dictation_runner, "suspend", lambda: calls.append("suspend"))
    monkeypatch.setattr(tray_icon.dictation_runner, "resume", lambda: calls.append("resume"))

    tray_icon.suspend()
    assert tray_icon.suspended is True
    tray_icon.resume()
    assert tray_icon.suspended is False
    assert calls == ["suspend", "resume"]


def test_commute_toggles(tray, monkeypatch):
    tray_icon, _ = tray
    actions = []
    monkeypatch.setattr(tray_icon, "begin", lambda: actions.append("begin"))
    monkeypatch.setattr(tray_icon, "suspend", lambda: actions.append("suspend"))
    monkeypatch.setattr(tray_icon, "resume", lambda: actions.append("resume"))
    tray_icon.dictating = False
    tray_icon.suspended = False
    tray_icon.commute(QSystemTrayIcon.ActivationReason.Trigger)
    assert actions[-1] == "begin"
    tray_icon.dictating = True
    tray_icon.suspended = False
    tray_icon.commute(QSystemTrayIcon.ActivationReason.Trigger)
    assert actions[-1] == "suspend"
    tray_icon.suspended = True
    tray_icon.commute(QSystemTrayIcon.ActivationReason.Trigger)
    assert actions[-1] == "resume"
    tray_icon.commute(QSystemTrayIcon.ActivationReason.Context)
    assert actions[-1] == "resume"


def test_tooltip_updates_with_model(tray, monkeypatch):
    tray_icon, _ = tray
    monkeypatch.setattr(tray_icon, "currentModel", lambda: ("model-a", "/tmp/a"))
    tray_icon._update_tooltip()
    assert tray_icon.toolTip() == "EloGraf\nModel: model-a"
    monkeypatch.setattr(tray_icon, "currentModel", lambda: ("", ""))
    tray_icon._update_tooltip()
    assert tray_icon.toolTip() == "EloGraf"
