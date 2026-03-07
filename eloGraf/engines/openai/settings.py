# ABOUTME: Settings schema for OpenAI Realtime API engine with UI metadata.
# ABOUTME: Defines OpenAISettings dataclass with field metadata for dynamic UI generation.

from __future__ import annotations

from dataclasses import dataclass, field

from eloGraf.base_settings import EngineSettings


@dataclass
class OpenAISettings(EngineSettings):
    """Settings for OpenAI Realtime API engine."""

    engine_type: str = field(
        default="openai-realtime",
        metadata={"hidden": True}
    )

    api_key: str = field(
        default="",
        metadata={
            "label": "API Key",
            "widget": "password",
            "tooltip": (
                "<b>OpenAI API Key</b><br>"
                "API key with access to Realtime API.<br><br>"
                "<i>Get your key at:</i> platform.openai.com/api-keys<br>"
                "<i>Note:</i> Requires billing enabled on your account"
            ),
        }
    )

    model: str = field(
        default="gpt-4o-transcribe",
        metadata={
            "label": "Transcription Model",
            "widget": "dropdown",
            "tooltip": (
                "<b>Transcription Model</b><br>"
                "Select the model for speech recognition.<br><br>"
                "<b>gpt-4o-transcribe:</b><br>"
                "- Higher accuracy<br>"
                "- Better for complex vocabulary<br>"
                "- Higher cost<br><br>"
                "<b>gpt-4o-mini-transcribe:</b><br>"
                "- Faster response<br>"
                "- Lower cost<br>"
                "- Good for general use"
            ),
            "options": ["gpt-4o-transcribe", "gpt-4o-mini-transcribe"],
        }
    )

    api_version: str = field(
        default="2025-08-28",
        metadata={
            "label": "API Version",
            "widget": "text",
            "tooltip": "Realtime API version string appended to the WebSocket URL",
        }
    )

    sample_rate: int = field(
        default=16000,
        metadata={
            "label": "Sample Rate",
            "widget": "text",
            "tooltip": "PCM sample rate used when capturing audio for the websocket stream",
        }
    )

    channels: int = field(
        default=1,
        metadata={
            "label": "Channels",
            "widget": "text",
            "tooltip": "Number of audio channels streamed to OpenAI (mono required)",
        }
    )

    vad_enabled: bool = field(
        default=True,
        metadata={
            "label": "VAD Enabled",
            "widget": "checkbox",
            "tooltip": "Enable server-side voice activity detection to segment speech automatically",
        }
    )

    vad_threshold: float = field(
        default=0.5,
        metadata={
            "label": "VAD Threshold",
            "widget": "text",
            "tooltip": "Energy threshold between 0.0 and 1.0 for server VAD speech detection",
        }
    )

    vad_prefix_padding_ms: int = field(
        default=300,
        metadata={
            "label": "VAD Prefix Padding (ms)",
            "widget": "text",
            "tooltip": "Milliseconds of audio retained before speech start when VAD triggers",
        }
    )

    vad_silence_duration_ms: int = field(
        default=200,
        metadata={
            "label": "VAD Silence Duration (ms)",
            "widget": "text",
            "tooltip": "Silence duration in milliseconds required to finalize a segment",
        }
    )

    language: str = field(
        default="en-US",
        metadata={
            "label": "Language",
            "widget": "text",
            "tooltip": "BCP-47 language code (leave empty to let the model auto-detect)",
        }
    )

    def __post_init__(self):
        """Validate VAD threshold is between 0 and 1."""
        if not 0.0 <= self.vad_threshold <= 1.0:
            raise ValueError(f"VAD threshold must be between 0 and 1, got {self.vad_threshold}")
