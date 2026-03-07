"""Settings for VoskLocal engine."""
import dataclasses
from dataclasses import dataclass
from typing import Optional
from eloGraf.base_settings import EngineSettings


@dataclass
class VoskLocalSettings(EngineSettings):
    """Configuration for VoskLocal STT engine."""
    
    engine_type: str = dataclasses.field(
        default="vosk-local",
        metadata={"hidden": True}
    )
    
    # Required
    model_path: str = dataclasses.field(
        default="",
        metadata={
            "label": "Model Path",
            "widget": "text",
            "readonly": True,
            "tooltip": "Path to the Vosk model directory",
        }
    )

    manage_models_action: str = dataclasses.field(
        default="",
        repr=False,
        metadata={
            "widget": "action_button",
            "button_text": "Manage Models...",
            # We will connect the click handler in dialogs.py
        }
    )
    
    # Audio settings
    sample_rate: int = dataclasses.field(
        default=16000,
        metadata={
            "label": "Sample Rate",
            "widget": "text",
            "tooltip": "Audio sample rate in Hz (typically 16000)",
        }
    )
    
    device: Optional[str] = dataclasses.field(
        default=None,
        metadata={"hidden": True} # Uses global deviceName
    )
    
    # VAD settings
    vad_type: str = dataclasses.field(
        default="silero",
        metadata={
            "label": "VAD Type",
            "widget": "dropdown",
            "options": ["silero", "webrtc", "rms"],
            "tooltip": (
                "1. Silero (Neural): El más preciso, detecta muy bien el habla humana incluso con ruido de fondo, "
                "pero usa más CPU y memoria.\n"
                "2. WebRTC (Algorítmico): Muy rápido y ligero, excelente en entornos silenciosos, "
                "pero puede confundirse con ruidos constantes (ventiladores, etc.).\n"
                "3. RMS (Volumen): El más simple (detecta si el sonido supera un 'volumen'). "
                "Es el que menos falla, pero el que menos distingue entre un golpe en la mesa y una palabra."
            ),
        }
    )
    
    vad_threshold: float = dataclasses.field(
        default=0.5,
        metadata={
            "label": "VAD Threshold",
            "widget": "text",
            "tooltip": "Threshold for speech detection (0.0 to 1.0)",
        }
    )
    
    silence_timeout_ms: int = dataclasses.field(
        default=500,
        metadata={
            "label": "Silence Timeout (ms)",
            "widget": "text",
            "tooltip": "Wait this long after speech ends before transcribing",
        }
    )
    
    # Features
    partial_results: bool = dataclasses.field(
        default=False,
        metadata={
            "label": "Partial Results",
            "widget": "checkbox",
            "tooltip": "Show partial transcriptions while speaking (if supported)",
        }
    )
    
    text_formatting: bool = dataclasses.field(
        default=True,
        metadata={
            "label": "Text Formatting",
            "widget": "checkbox",
            "tooltip": "Apply automatic capitalization and punctuation",
        }
    )
    
    locale: str = dataclasses.field(
        default="en_US",
        metadata={
            "label": "Locale",
            "widget": "text",
            "tooltip": "Locale for text formatting (e.g. en_US, es_ES)",
        }
    )
    
    # Performance
    max_queue_depth: int = dataclasses.field(
        default=3,
        metadata={
            "label": "Max Queue Depth",
            "widget": "text",
            "tooltip": "Maximum number of audio segments to queue for inference",
        }
    )
