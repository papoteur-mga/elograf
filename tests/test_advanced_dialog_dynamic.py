# ABOUTME: Tests for AdvancedUI dialog with dynamic tab generation.
# ABOUTME: Verifies that settings tabs are created from engine metadata.

from __future__ import annotations

import os
import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qt_app():
    """Create QApplication for tests that need Qt."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def stub_pulseaudio(monkeypatch):
    monkeypatch.setattr(
        "eloGraf.audio_recorder.get_audio_devices",
        lambda backend="auto": [("default", "Default Device")],
    )


def test_advanced_dialog_creates_dynamic_tabs(qt_app):
    """Test that AdvancedUI creates tabs for all registered engines."""
    from eloGraf.dialogs import AdvancedUI
    from eloGraf.engine_settings_registry import get_all_engine_ids

    dialog = AdvancedUI()

    # Should have General tab plus one tab per engine
    expected_tab_count = 1 + len(get_all_engine_ids())

    assert dialog.ui.tabWidget.count() >= expected_tab_count

    # Check that engine tabs were created
    tab_texts = [
        dialog.ui.tabWidget.tabText(i)
        for i in range(dialog.ui.tabWidget.count())
    ]

    assert "General" in tab_texts
    assert "Nerd Dictation" in tab_texts
    assert "Whisper Docker" in tab_texts
    assert "Google Cloud" in tab_texts
    assert "OpenAI" in tab_texts
    assert "AssemblyAI" in tab_texts


def test_advanced_dialog_stores_engine_tabs(qt_app):
    """Test that AdvancedUI stores references to dynamically created tabs."""
    from eloGraf.dialogs import AdvancedUI

    dialog = AdvancedUI()

    # Should have engine_tabs dict with all engines
    assert hasattr(dialog, 'engine_tabs')
    assert isinstance(dialog.engine_tabs, dict)

    assert "nerd-dictation" in dialog.engine_tabs
    assert "whisper-docker" in dialog.engine_tabs
    assert "google-cloud-speech" in dialog.engine_tabs
    assert "openai-realtime" in dialog.engine_tabs
    assert "assemblyai" in dialog.engine_tabs


def test_engine_tab_switching(qt_app):
    """Test that selecting an engine switches to its tab."""
    from eloGraf.dialogs import AdvancedUI

    dialog = AdvancedUI()

    # Find whisper-docker in dropdown and set it as current
    index = dialog.ui.stt_engine_cb.findData("whisper-docker")
    assert index >= 0, "whisper-docker not found in dropdown"

    dialog.ui.stt_engine_cb.setCurrentIndex(index)
    dialog._on_stt_engine_changed(index)

    # Current tab should be whisper tab
    current_tab = dialog.ui.tabWidget.currentWidget()
    whisper_tab = dialog.engine_tabs["whisper-docker"]

    assert current_tab == whisper_tab


def test_advanced_dialog_populates_settings_instance(qt_app):
    """AdvancedUI should pre-fill dynamic tabs with existing settings values."""
    import dataclasses
    from eloGraf.dialogs import AdvancedUI
    from eloGraf.engine_settings_registry import get_all_engine_ids, get_engine_settings_class

    class DummySettings:
        def __init__(self):
            self._cache = {
                engine_id: get_engine_settings_class(engine_id)()
                for engine_id in get_all_engine_ids()
            }
            self._cache["openai-realtime"].api_key = "secret-key"

        def get_engine_settings(self, engine_type: str):
            cls = get_engine_settings_class(engine_type)
            instance = self._cache.get(engine_type, cls())
            return dataclasses.replace(instance)

    dialog = AdvancedUI(DummySettings())

    openai_tab = dialog.engine_tabs["openai-realtime"]
    api_widget = openai_tab.widgets_map["api_key"]
    assert api_widget.text() == "secret-key"

    api_widget.setText("new-key")
    updated = dialog.get_engine_settings_dataclass("openai-realtime")
    assert updated.api_key == "new-key"


def test_manage_models_action_updates_path(qt_app, monkeypatch, tmp_path):
    """Clicking manage models should refresh the model path field."""
    from PyQt6.QtCore import QSettings
    from eloGraf.dialogs import AdvancedUI
    from eloGraf.settings import Settings

    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    backend.clear()
    app_settings = Settings(backend)
    app_settings.models = [
        {
            "language": "en",
            "name": "model-a",
            "version": "1",
            "size": "10MB",
            "type": "custom",
            "location": "/tmp/a",
        }
    ]
    app_settings.write_models()
    app_settings.load()

    dialog = AdvancedUI(app_settings)
    nerd_tab = dialog.engine_tabs["nerd-dictation"]
    path_widget = nerd_tab.widgets_map["model_path"]
    path_widget.setText("old")

    def fake_launch(parent=None, *_, **__):
        backend.setValue("Model/name", "model-a")
        backend.sync()

    monkeypatch.setattr(
        "eloGraf.dialogs.launch_model_selection_dialog",
        fake_launch,
    )

    dialog._handle_model_selection(nerd_tab)
    assert path_widget.text() == "/tmp/a"


def test_custom_ui_edit_persists_changes(qt_app, tmp_path):
    """Editing an existing model should persist updated metadata."""
    from PyQt6.QtCore import QSettings
    from eloGraf.settings import Settings
    from eloGraf.engines.nerd.ui.dialogs import CustomUI

    backend = QSettings(str(tmp_path / "models.ini"), QSettings.Format.IniFormat)
    backend.clear()
    settings = Settings(backend)
    settings.models = [
        {
            "language": "en",
            "name": "model-a",
            "version": "1",
            "size": "10MB",
            "type": "custom",
            "location": "/tmp/a",
        }
    ]
    settings.write_models()
    settings.load()

    model_dir = tmp_path / "model_dir"
    model_dir.mkdir()

    dialog = CustomUI(0, settings)
    dialog.ui.languageLineEdit.setText("es")
    dialog.ui.nameLineEdit.setText("model-b")
    dialog.ui.versionLineEdit.setText("2")
    dialog.ui.classLineEdit.setText("updated")
    dialog.ui.sizeLineEdit.setText("12MB")
    dialog.ui.filePicker.setText(str(model_dir))

    dialog.accept()

    settings.load()
    assert settings.models[0]["name"] == "model-b"
    assert settings.models[0]["language"] == "es"
    assert settings.models[0]["location"] == str(model_dir)
