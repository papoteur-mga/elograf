# ABOUTME: Settings schema for Gemini Live API engine with UI metadata.
# ABOUTME: Defines GeminiSettings dataclass with field metadata for dynamic UI generation.

from __future__ import annotations

from dataclasses import dataclass, field

from eloGraf.base_settings import EngineSettings


@dataclass
class GeminiSettings(EngineSettings):
    """Settings for Gemini Live API speech-to-text engine."""

    engine_type: str = field(
        default="gemini-live",
        metadata={"hidden": True}
    )

    api_key: str = field(
        default="",
        metadata={
            "label": "API Key",
            "widget": "password",
            "tooltip": (
                "<b>Google AI API Key</b><br>"
                "API key for Gemini Live API.<br><br>"
                "<i>Get your key at:</i> aistudio.google.com/apikey<br>"
                "<i>Note:</i> Different from Google Cloud credentials"
            ),
        }
    )

    model: str = field(
        default="gemini-2.5-flash",
        metadata={
            "label": "Model",
            "widget": "text",
            "tooltip": (
                "<b>Gemini Model</b><br>"
                "Select the Gemini model for transcription.<br><br>"
                "<b>gemini-2.5-flash:</b><br>"
                "- Recommended for real-time<br>"
                "- Fastest response time<br>"
                "<b>gemini-2.5-pro:</b><br>"
                "- Higher accuracy<br>"
                "- More capable with complex audio"
            ),
        }
    )

    language_code: str = field(
        default="en-US",
        metadata={
            "label": "Language Code",
            "widget": "text",
            "tooltip": "BCP-47 language code (e.g. en-US, es-ES, fr-FR)",
        }
    )

    sample_rate: int = field(
        default=16000,
        metadata={
            "label": "Sample Rate",
            "widget": "text",
            "tooltip": "Sample rate in Hz (16000 recommended for Gemini Live API)",
        }
    )

    channels: int = field(
        default=1,
        metadata={
            "label": "Channels",
            "widget": "text",
            "tooltip": "Number of audio channels (must be 1 for Gemini Live API)",
        }
    )

    vad_enabled: bool = field(
        default=True,
        metadata={
            "label": "VAD Enabled",
            "widget": "checkbox",
            "tooltip": "Enable voice activity detection when streaming audio",
        }
    )

    vad_threshold: float = field(
        default=500.0,
        metadata={
            "label": "VAD Threshold",
            "widget": "text",
            "tooltip": "RMS loudness threshold used when VAD is enabled",
        }
    )

    def __post_init__(self):
        """Validate settings."""
        if not 8000 <= self.sample_rate <= 48000:
            raise ValueError(f"Invalid sample rate: {self.sample_rate}")
        if self.channels != 1:
            raise ValueError(f"Gemini Live API requires mono audio (channels=1), got {self.channels}")
