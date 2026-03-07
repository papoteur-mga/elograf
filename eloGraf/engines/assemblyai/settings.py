# ABOUTME: Settings schema for AssemblyAI Realtime engine with UI metadata.
# ABOUTME: Defines AssemblyAISettings dataclass with field metadata for dynamic UI generation.

from __future__ import annotations

from dataclasses import dataclass, field

from eloGraf.base_settings import EngineSettings


@dataclass
class AssemblyAISettings(EngineSettings):
    """Settings for AssemblyAI Realtime engine."""

    engine_type: str = field(
        default="assemblyai",
        metadata={"hidden": True}
    )

    api_key: str = field(
        default="",
        metadata={
            "label": "API Key",
            "widget": "password",
            "tooltip": (
                "<b>AssemblyAI API Key</b><br>"
                "API key for AssemblyAI Realtime transcription.<br><br>"
                "<i>Get your key at:</i> www.assemblyai.com<br>"
                "<i>Note:</i> Supports regular API keys or temporary tokens"
            ),
        }
    )

    model: str = field(
        default="universal",
        metadata={
            "label": "Model",
            "widget": "text",
            "tooltip": (
                "<b>Transcription Model</b><br>"
                "AssemblyAI model optimized for different use cases.<br><br>"
                "<b>universal:</b> General purpose (default)<br>"
                "<b>meeting:</b> Multi-speaker conversations<br>"
                "<b>default:</b> Balanced accuracy/speed"
            ),
        }
    )

    language: str = field(
        default="",
        metadata={
            "label": "Language",
            "widget": "text",
            "tooltip": "Optional BCP-47 language code; leave empty for auto-detect",
        }
    )

    sample_rate: int = field(
        default=16000,
        metadata={
            "label": "Sample Rate",
            "widget": "text",
            "tooltip": "Sample rate in Hz used for PCM frames sent to AssemblyAI",
        }
    )

    channels: int = field(
        default=1,
        metadata={
            "label": "Channels",
            "widget": "text",
            "tooltip": "Number of audio channels captured (mono recommended)",
        }
    )

    def __post_init__(self):
        """Validate sample rate is in valid range."""
        if not 8000 <= self.sample_rate <= 48000:
            raise ValueError(f"Invalid sample rate: {self.sample_rate}")
