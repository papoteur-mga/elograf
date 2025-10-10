from __future__ import annotations

import os

import pytest

from eloGraf.dictation import CommandBuildError, build_dictation_command
from eloGraf.settings import Settings


class DummySettings(Settings):
    """Settings wrapper that avoids touching real QSettings storage."""

    def __init__(self):
        super().__init__(backend=self._create_backend())

    @staticmethod
    def _create_backend():
        from PyQt6.QtCore import QSettings

        return QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Test", "Dictation")


def make_settings() -> Settings:
    settings = DummySettings()
    settings.models = []
    return settings


def test_build_command_basic_includes_required_flags(monkeypatch):
    settings = make_settings()
    cmd, env = build_dictation_command(settings, "/models/en")
    assert cmd[:2] == ["nerd-dictation", "begin"]
    assert "--output=SIMULATE_INPUT" in cmd
    assert "--continuous" in cmd
    assert "--verbose=1" in cmd
    assert env["PATH"] == os.environ["PATH"]


def test_build_command_respects_custom_env(monkeypatch):
    settings = make_settings()
    settings.env = "FOO=bar BAZ=qux"
    cmd, env = build_dictation_command(settings, "/models/en")
    assert env["FOO"] == "bar"
    assert env["BAZ"] == "qux"


def test_build_command_rejects_bad_env():
    settings = make_settings()
    settings.env = "INVALID"  # missing '='
    with pytest.raises(CommandBuildError):
        build_dictation_command(settings, "/models/en")


def test_build_command_default_device_name_omits_flag():
    """When deviceName is 'default', --pulse-device-name should not be added."""
    settings = make_settings()
    settings.deviceName = "default"
    cmd, env = build_dictation_command(settings, "/models/en")
    assert not any("--pulse-device-name" in arg for arg in cmd)


def test_build_command_custom_device_name_adds_flag():
    """When deviceName is set, --pulse-device-name should be added."""
    settings = make_settings()
    settings.deviceName = "alsa_input.pci-0000_00_1b.0.analog-stereo"
    cmd, env = build_dictation_command(settings, "/models/en")
    assert "--pulse-device-name=alsa_input.pci-0000_00_1b.0.analog-stereo" in cmd
