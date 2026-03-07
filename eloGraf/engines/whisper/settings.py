# ABOUTME: Settings schema for Whisper Docker engine with UI metadata.
# ABOUTME: Defines WhisperSettings dataclass with field metadata for dynamic UI generation.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from eloGraf.base_settings import EngineSettings


@dataclass
class WhisperSettings(EngineSettings):
    """Settings for Whisper Docker engine."""

    engine_type: str = field(
        default="whisper-docker",
        metadata={"hidden": True}
    )

    model: str = field(
        default="base",
        metadata={
            "label": "Whisper Model",
            "widget": "dropdown",
            "tooltip": (
                "<b>Whisper Model Size</b><br>"
                "Select the model based on accuracy vs speed trade-off:<br><br>"
                "<b>tiny:</b> Fastest, lowest accuracy (~39 MB)<br>"
                "<b>base:</b> Good balance (~74 MB)<br>"
                "<b>small:</b> Better accuracy (~244 MB)<br>"
                "<b>medium:</b> High accuracy (~769 MB)<br>"
                "<b>large-v3:</b> Best accuracy, slowest (~1.5 GB)"
            ),
            "options": ["tiny", "base", "small", "medium", "large-v3"],
        }
    )

    port: int = field(
        default=9000,
        metadata={
            "label": "Whisper Port",
            "widget": "text",
            "tooltip": (
                "<b>API Port</b><br>"
                "Port for the Whisper Docker container REST API.<br><br>"
                "<i>Default:</i> 9000<br>"
                "<i>Range:</i> 1-65535"
            ),
        }
    )

    language: Optional[str] = field(
        default=None,
        metadata={
            "label": "Whisper Language",
            "widget": "text",
            "tooltip": (
                "<b>Language Code</b><br>"
                "ISO 639-1 language code for transcription.<br><br>"
                "<i>Examples:</i> en, es, fr, de, it<br>"
                "<i>Leave empty for auto-detection</i>"
            ),
        }
    )

    chunk_duration: float = field(
        default=5.0,
        metadata={
            "label": "Whisper Chunk Duration (s)",
            "widget": "text",
            "tooltip": (
                "<b>Audio Chunk Duration</b><br>"
                "Length of audio segments sent for transcription.<br><br>"
                "<i>Shorter (2-3s):</i> Lower latency, more requests<br>"
                "<i>Longer (5-10s):</i> Better context, less overhead<br>"
                "<i>Default:</i> 5.0 seconds"
            ),
        }
    )

    sample_rate: int = field(
        default=16000,
        metadata={
            "label": "Sample Rate",
            "widget": "text",
            "tooltip": "PCM sample rate forwarded to the Whisper REST service",
        }
    )

    channels: int = field(
        default=1,
        metadata={
            "label": "Channels",
            "widget": "text",
            "tooltip": "Number of channels to record (Whisper Docker expects mono)",
        }
    )

    vad_enabled: bool = field(
        default=True,
        metadata={
            "label": "VAD Enabled",
            "widget": "checkbox",
            "tooltip": (
                "<b>Voice Activity Detection</b><br>"
                "Skip silent audio chunks to reduce API calls.<br><br>"
                "<i>Enabled:</i> Only send chunks with detected speech<br>"
                "<i>Disabled:</i> Process all audio chunks"
            ),
        }
    )

    vad_threshold: float = field(
        default=500.0,
        metadata={
            "label": "VAD Threshold",
            "widget": "text",
            "tooltip": (
                "<b>VAD Threshold</b><br>"
                "RMS loudness threshold for voice detection.<br><br>"
                "<i>Lower (100-300):</i> Detects quiet speech, more false positives<br>"
                "<i>Medium (400-600):</i> Good for normal environments<br>"
                "<i>Higher (700-1000):</i> Filters noise, may miss quiet speech<br>"
                "<i>Default:</i> 500"
            ),
        }
    )

    auto_reconnect: bool = field(
        default=True,
        metadata={
            "label": "Auto Reconnect",
            "widget": "checkbox",
            "tooltip": "Automatically restart the container when the REST API stops responding",
        }
    )

    def __post_init__(self):
        """Validate port is in valid range."""
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port: {self.port}")
