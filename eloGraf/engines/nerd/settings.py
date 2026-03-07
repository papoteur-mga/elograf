# ABOUTME: Settings schema for nerd-dictation engine with UI metadata.
# ABOUTME: Defines NerdSettings dataclass with field metadata for dynamic UI generation.

from __future__ import annotations

from dataclasses import dataclass, field

from eloGraf.base_settings import EngineSettings
from .ui.dialogs import launch_model_selection_dialog


@dataclass
class NerdSettings(EngineSettings):
    """Settings for nerd-dictation engine."""

    engine_type: str = field(
        default="nerd-dictation",
        metadata={"hidden": True}
    )

    sample_rate: int = field(
        default=44100,
        metadata={
            "label": "Sample rate (Hz)",
            "widget": "text",
            "tooltip": (
                "<b>Audio Sample Rate</b><br>"
                "Sample rate for recording in Hertz.<br><br>"
                "<i>Common values:</i><br>"
                "44100 Hz: CD quality (default)<br>"
                "48000 Hz: Professional audio<br>"
                "16000 Hz: Lower quality, smaller files"
            ),
        }
    )

    timeout: int = field(
        default=0,
        metadata={
            "label": "Timeout (s)",
            "widget": "slider",
            "tooltip": (
                "<b>Recording Timeout</b><br>"
                "Automatically stop recording after silence period.<br><br>"
                "<i>0:</i> Disabled (manual stop required)<br>"
                "<i>2-5:</i> Stop after short silence<br>"
                "<i>Useful for:</i> Hands-free dictation without explicit stop"
            ),
            "range": [0, 100],
            "step": 1,
        }
    )

    idle_time: int = field(
        default=100,
        metadata={
            "label": "Idle time (ms)",
            "widget": "slider",
            "tooltip": (
                "Time to idle between processing audio from the recording.\n"
                "Setting to zero is the most responsive at the cost of high CPU usage.\n"
                "The default value is 0.1 (processing 10 times a second),\n"
                "which is quite responsive in practice"
            ),
            "range": [0, 500],
            "step": 1,
        }
    )

    punctuate_timeout: int = field(
        default=0,
        metadata={
            "label": "Punctuate from previous timeout (s)",
            "widget": "slider",
            "tooltip": (
                "The time-out in seconds for detecting the state of dictation from the previous recording,\n"
                "this can be useful so punctuation it is added before entering the dictation (zero disables)"
            ),
            "range": [0, 100],
            "step": 1,
        }
    )

    full_sentence: bool = field(
        default=False,
        metadata={
            "label": "Full sentence",
            "widget": "checkbox",
            "tooltip": (
                "<b>Full Sentence Formatting</b><br>"
                "Capitalize first letter and add punctuation.<br><br>"
                "<i>Enabled:</i><br>"
                "- Capitalizes first character<br>"
                "- Adds comma/full stop based on pause length<br><br>"
                "<i>Best for:</i> Continuous dictation of full sentences"
            ),
        }
    )

    digits: bool = field(
        default=False,
        metadata={
            "label": "Numbers as digits",
            "widget": "checkbox",
            "tooltip": (
                "<b>Number Format</b><br>"
                "Convert spoken numbers to digits.<br><br>"
                "<i>Example:</i><br>"
                "'twenty five' → '25'<br>"
                "'one hundred' → '100'<br><br>"
                "<i>Best for:</i> Technical content, addresses, phone numbers"
            ),
        }
    )

    use_separator: bool = field(
        default=False,
        metadata={
            "label": "Use separator for numbers",
            "widget": "checkbox",
            "tooltip": "Use a comma separators for numbers",
        }
    )

    free_command: str = field(
        default="",
        metadata={
            "label": "Free option",
            "widget": "text",
            "tooltip": "Add option to add on the comamnd line of the dictation tool",
        }
    )

    model_path: str = field(
        default="",
        metadata={
            "label": "Model Path",
            "widget": "text",
            "readonly": True,
        }
    )

    manage_models_action: str = field(
        default="",
        repr=False,
        metadata={
            "widget": "action_button",
            "button_text": "Manage Models...",
            "on_click": launch_model_selection_dialog,
        }
    )
