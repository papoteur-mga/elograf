from __future__ import annotations

from PyQt6.QtCore import QSettings

from eloGraf.settings import DEFAULT_RATE, Settings


def _make_backend(tmp_path):
    path = tmp_path / "settings.ini"
    backend = QSettings(str(path), QSettings.Format.IniFormat)
    backend.clear()
    backend.sync()
    return backend, path


def test_load_defaults_when_backend_empty(tmp_path):
    backend, _ = _make_backend(tmp_path)
    settings = Settings(backend)

    settings.load()

    assert settings.precommand == ""
    assert settings.postcommand == ""
    assert settings.sampleRate == DEFAULT_RATE
    assert settings.timeout == 0
    assert settings.fullSentence is False
    assert settings.beginShortcut == ""
    assert settings.endShortcut == ""
    assert settings.suspendShortcut == ""
    assert settings.resumeShortcut == ""
    assert settings.models == []


def test_save_persists_custom_values(tmp_path):
    backend, path = _make_backend(tmp_path)
    settings = Settings(backend)
    settings.precommand = "echo start"
    settings.postcommand = "echo stop"
    settings.sampleRate = DEFAULT_RATE + 1
    settings.timeout = 42
    settings.fullSentence = True
    settings.digits = True
    settings.deviceName = "usb-mic"
    settings.freeCommand = "--foo bar"
    settings.beginShortcut = "Ctrl+Alt+B"
    settings.endShortcut = "Ctrl+Alt+E"
    settings.suspendShortcut = "Ctrl+Alt+S"
    settings.resumeShortcut = "Ctrl+Alt+R"

    settings.save()
    backend.sync()

    reloaded = QSettings(str(path), QSettings.Format.IniFormat)
    assert reloaded.value("Precommand") == "echo start"
    assert reloaded.value("Postcommand") == "echo stop"
    assert reloaded.value("SampleRate", type=int) == DEFAULT_RATE + 1
    assert reloaded.value("Timeout", type=int) == 42
    assert reloaded.value("FullSentence", type=int) == 1
    assert reloaded.value("Digits", type=int) == 1
    assert reloaded.value("DeviceName") == "usb-mic"
    assert reloaded.value("FreeCommand") == "--foo bar"
    assert reloaded.value("BeginShortcut") == "Ctrl+Alt+B"
    assert reloaded.value("EndShortcut") == "Ctrl+Alt+E"
    assert reloaded.value("SuspendShortcut") == "Ctrl+Alt+S"
    assert reloaded.value("ResumeShortcut") == "Ctrl+Alt+R"


def test_add_and_remove_model_updates_backend(tmp_path):
    backend, path = _make_backend(tmp_path)
    settings = Settings(backend)
    settings.load()

    settings.add_model("en", "vosk-en", "1.0", "1 GB", "Vosk", "/models/en")
    backend.sync()

    loaded = Settings(QSettings(str(path), QSettings.Format.IniFormat))
    loaded.load()
    assert loaded.models == [
        {
            "language": "en",
            "name": "vosk-en",
            "version": "1.0",
            "size": "1 GB",
            "type": "Vosk",
            "location": "/models/en",
        }
    ]

    settings.remove_model(0)
    backend.sync()

    loaded_again = Settings(QSettings(str(path), QSettings.Format.IniFormat))
    loaded_again.load()
    assert loaded_again.models == []
