# ABOUTME: Registry mapping engine names to their settings dataclasses.
# ABOUTME: Provides centralized access to engine settings schemas for dynamic UI generation.

from __future__ import annotations

from typing import Type, Dict, Optional
import importlib


# Engine registry with metadata for each speech-to-text engine
ENGINES: Dict[str, Dict[str, str]] = {
    "nerd-dictation": {
        "module": "eloGraf.engines.nerd.settings",
        "class": "NerdSettings",
        "display_name": "Nerd Dictation",
    },
    "whisper-docker": {
        "module": "eloGraf.engines.whisper.settings",
        "class": "WhisperSettings",
        "display_name": "Whisper Docker",
    },
    "google-cloud-speech": {
        "module": "eloGraf.engines.google.settings",
        "class": "GoogleCloudSettings",
        "display_name": "Google Cloud",
    },
    "openai-realtime": {
        "module": "eloGraf.engines.openai.settings",
        "class": "OpenAISettings",
        "display_name": "OpenAI",
    },
    "assemblyai": {
        "module": "eloGraf.engines.assemblyai.settings",
        "class": "AssemblyAISettings",
        "display_name": "AssemblyAI",
    },
    "gemini-live": {
        "module": "eloGraf.engines.gemini.settings",
        "class": "GeminiSettings",
        "display_name": "Gemini Live API",
    },
    "vosk-local": {
        "module": "eloGraf.engines.vosk_local.settings",
        "class": "VoskLocalSettings",
        "display_name": "Vosk (Local)",
    },
}


def get_engine_settings_class(engine_id: str) -> Optional[Type]:
    """Get the settings dataclass for an engine.

    Args:
        engine_id: Engine identifier (e.g., "nerd-dictation")

    Returns:
        Settings dataclass type, or None if not found
    """
    engine = ENGINES.get(engine_id)
    if not engine:
        return None

    module_path = engine.get("module")
    class_name = engine.get("class")

    if not module_path or not class_name:
        return None

    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        return None


def get_all_engine_ids() -> list[str]:
    """Get list of all registered engine identifiers.

    Returns:
        List of engine IDs
    """
    return list(ENGINES.keys())


def get_engine_display_name(engine_id: str) -> str:
    """Get the display name for an engine.

    Args:
        engine_id: Engine identifier

    Returns:
        Human-readable display name
    """
    engine = ENGINES.get(engine_id)
    if engine:
        return engine.get("display_name", engine_id)
    return engine_id


def get_engine_choices() -> list[tuple[str, str]]:
    """Get list of (engine_id, display_name) tuples for dropdown widgets.

    Returns:
        List of tuples: [(engine_id, display_name), ...]
    """
    return [(engine_id, get_engine_display_name(engine_id)) for engine_id in get_all_engine_ids()]
